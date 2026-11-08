class_name LevelBuilder
extends Node3D
## Niveau construit depuis un fichier JSON : carte ASCII (1 case = 1 m) + données
## (herses, rencontres, boss, zones, indices, coffres). Voir tools/compose_level1.py et LEVEL_DESIGN.md.
##
## Les murs situés entre la caméra et un sol sont bas, pour ne jamais cacher le héros.

signal zone_changed(zone: Dictionary)
signal hint_requested(text: String)
signal encounter_started(encounter: Encounter)
signal encounter_cleared(encounter: Encounter)
signal checkpoint_reached(brazier: Brazier)
signal boss_started(boss: BossSlime)
signal boss_defeated(boss: BossSlime)
signal chest_opened(reward: String)

const PROPS := preload("res://assets/models/props.glb")
const SLIME := preload("res://scenes/slime.tscn")
const SKELETON := preload("res://scenes/skeleton.tscn")
const BOSS := preload("res://scenes/boss_slime.tscn")
const SUN_DIRECTION := Vector3(0.229, -0.743, -0.629)
const DIRS := [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1)]
const PALETTE := {
	"herbe1": "5fa84a", "herbe2": "63ad4d", "herbe3": "5aa346", "terre1": "9a7650", "terre2": "8f6c48",
	"dalle1": "a7a3a8", "dalle2": "94909a", "dalle3": "9d99a3", "mur1": "8d8a96", "mur2": "85828f",
	"ruine": "a09aa6", "sommet": "6c6875", "mousse": "4e8a3c",
}
const STATIC_AGGRO := 7.0
const ENEMY_HEART_CHANCE := 0.18

@export_file("*.json") var level_path := "res://levels/niveau1.json"

var data: Dictionary
var rows: Array = []
var width := 0
var height := 0
var hero: Hero
var enemies_root: Node3D
var start_position := Vector3.ZERO
var gates := {}
var encounters: Array[Encounter] = []
var boss: BossSlime
var spawn_points := {}
var stats := {}

var _props_root: Node
var _templates := {}
var _mat_cache := {}
var _color_mats := {}
var _sun: DirectionalLight3D
var _sun_tween: Tween
var _torches: Array[OmniLight3D] = []
var _zone_index := -1
var _hints_shown := {}
var _boss_active := false
var _time := 0.0
var _rng := RandomNumberGenerator.new()


# =========================================================================== construction
func setup(the_hero: Hero, enemies: Node3D) -> void:
	hero = the_hero
	enemies_root = enemies
	_rng.seed = 1234
	data = JSON.parse_string(FileAccess.get_file_as_string(level_path))
	rows = data["map"]
	height = rows.size()
	width = String(rows[0]).length()
	_props_root = PROPS.instantiate()
	for c in _props_root.get_children():
		_templates[String(c.name)] = c
	_setup_environment()
	_build_ground()
	_build_walls()
	_build_vegetation()
	_build_cells()
	_build_gates()
	_build_encounters()
	_build_navigation()


# --------------------------------------------------------------------------- navigation (A* sur la grille)
const NAV_SOLID := "#T PprLtocBC"

var astar := AStarGrid2D.new()


func _build_navigation() -> void:
	astar.region = Rect2i(0, 0, width, height)
	astar.cell_size = Vector2.ONE
	astar.diagonal_mode = AStarGrid2D.DIAGONAL_MODE_ONLY_IF_NO_OBSTACLES
	astar.update()
	for z in height:
		for x in width:
			if NAV_SOLID.contains(cell(x, z)):
				astar.set_point_solid(Vector2i(x, z), true)
	for id in gates:
		_update_gate_nav(gates[id])


func _update_gate_nav(g: Gate) -> void:
	for c in g.cells:
		astar.set_point_solid(c, not g.is_open)


func _cell_of(p: Vector3) -> Vector2i:
	return Vector2i(clampi(int(floor(p.x)), 0, width - 1), clampi(int(floor(p.z)), 0, height - 1))


## Prochain point de passage pour aller de `from` à `to` en contournant murs, piliers et herses.
func next_waypoint(from: Vector3, to: Vector3) -> Vector3:
	var a := _cell_of(from)
	var b := _cell_of(to)
	if a == b or astar.is_point_solid(a) or astar.is_point_solid(b):
		return to
	var path := astar.get_id_path(a, b, true)
	if path.size() <= 2:
		return to
	return cell_center(path[1].x, path[1].y)


func _exit_tree() -> void:
	if is_instance_valid(_props_root):
		_props_root.free()


func cell(x: int, z: int) -> String:
	if z < 0 or z >= height or x < 0 or x >= width:
		return " "
	return String(rows[z])[x]


## Rendu au-delà de la carte (écrans larges) : on prolonge le bord, forêt ou roche.
## Pas de collision ici : ces cases sont hors d'atteinte.
const BORDER := 26                     # assez pour le zoom le plus éloigné en 32:9 (~44 m de large)


func _render_cell(x: int, z: int) -> String:
	if x >= 0 and x < width and z >= 0 and z < height:
		return cell(x, z)
	var edge := cell(clampi(x, 0, width - 1), clampi(z, 0, height - 1))
	return "#" if edge == "#" else "T"


func cell_center(x: int, z: int) -> Vector3:
	return Vector3(x + 0.5, 0.0, z + 0.5)


func _is_open(c: String) -> bool:
	return not (c == "#" or c == "T" or c == " ")


func _hash(x: int, z: int) -> int:
	return absi((x * 73856093) ^ (z * 19349663) ^ 0x5bd1e995)


# --------------------------------------------------------------------------- matériaux
func _color_mat(key: String) -> ShaderMaterial:
	if not _color_mats.has(key):
		var m := ShaderMaterial.new()
		m.shader = ToonMaterials.TOON_SHADER
		m.set_shader_parameter("albedo", Color(PALETTE[key]))
		_color_mats[key] = m
	return _color_mats[key]


## Matériau toon partagé par tous les décors qui utilisent le même matériau importé.
func _toon(src: Material, node_name: String) -> Material:
	if src == null:
		return null
	var key := "%d:%s" % [src.get_instance_id(), node_name.begins_with("P_Touffe")]
	if not _mat_cache.has(key):
		_mat_cache[key] = ToonMaterials._convert(src, node_name)
	return _mat_cache[key]


func prop(template: String) -> Node3D:
	var n: Node3D = _templates[template].duplicate()
	for mi in n.find_children("*", "MeshInstance3D", true, false):
		for s in mi.mesh.get_surface_count():
			mi.set_surface_override_material(s, _toon(mi.get_active_material(s), String(mi.name)))
	return n


# --------------------------------------------------------------------------- sols
func _ground_kind(x: int, z: int, depth := 0) -> String:
	var c := _render_cell(x, z)
	if c == "." or c == "T":
		return "herbe"
	if c == ",":
		return "terre"
	if c == "_" or c == "^" or c == "#":
		return "dalle"
	if depth < 2:
		for d in DIRS:
			var n := cell(x + d.x, z + d.y)
			if n in [".", ",", "_"]:
				return _ground_kind(x + d.x, z + d.y, depth + 1)
	return "dalle"


func _build_ground() -> void:
	var tools := {}
	for z in range(-BORDER, height + BORDER):
		for x in range(-BORDER, width + BORDER):
			var c := _render_cell(x, z)
			if c == "#" or c == " ":
				continue
			var kind := _ground_kind(x, z)
			var h := _hash(x, z)
			var key := ""
			match kind:
				"herbe":
					key = ["herbe1", "herbe2", "herbe3", "herbe1"][h % 4]
				"terre":
					key = "terre1" if h % 3 else "terre2"
				_:
					key = "dalle1" if (x + z) % 2 == 0 else ("dalle2" if h % 3 else "dalle3")
			if not tools.has(key):
				var st := SurfaceTool.new()
				st.begin(Mesh.PRIMITIVE_TRIANGLES)
				tools[key] = st
			_quad(tools[key], Vector3(x, 0, z), Vector3(x + 1, 0, z), Vector3(x + 1, 0, z + 1),
				Vector3(x, 0, z + 1), Vector3.UP)
	_commit_mesh("Sol", tools, false)
	# un seul grand sol physique
	var body := StaticBody3D.new()
	body.name = "SolPhysique"
	add_child(body)
	_add_box(body, Vector3(width, 1.0, height), Vector3(width * 0.5, -0.5, height * 0.5))


# --------------------------------------------------------------------------- murs
func _wall_height(x: int, z: int) -> float:
	if _render_cell(x, z) != "#":
		return 0.0
	# mur court s'il se trouve devant un sol (entre ce sol et la caméra, qui regarde vers -X -Z)
	for d in [Vector2i(-1, 0), Vector2i(0, -1), Vector2i(-1, -1)]:
		if _is_open(cell(x + d.x, z + d.y)):
			return 0.5
	var base := 1.15 if _zone_music(clampi(x, 0, width - 1), clampi(z, 0, height - 1)) == "forest" else 1.9
	return base + float(_hash(x, z) % 4) * 0.08


func _build_walls() -> void:
	var tools := {}
	for z in range(-BORDER, height + BORDER):
		for x in range(-BORDER, width + BORDER):
			if _render_cell(x, z) != "#":
				continue
			var h := _wall_height(x, z)
			var hs := _hash(x, z)
			var forest := _zone_music(clampi(x, 0, width - 1), clampi(z, 0, height - 1)) == "forest"
			var top := "mousse" if hs % 9 == 0 else ("ruine" if forest else "sommet")
			var side := "ruine" if forest else ("mur1" if hs % 2 else "mur2")
			_quad(_tool(tools, top), Vector3(x, h, z), Vector3(x + 1, h, z), Vector3(x + 1, h, z + 1),
				Vector3(x, h, z + 1), Vector3.UP)
			for d in DIRS:
				var nh := _wall_height(x + d.x, z + d.y)
				if nh >= h:
					continue
				var n := Vector3(d.x, 0, d.y)
				var a := Vector3(x, 0, z)            # côté -Z par défaut
				var b := Vector3(x + 1, 0, z)
				if d.x == 1:
					a = Vector3(x + 1, 0, z)
					b = Vector3(x + 1, 0, z + 1)
				elif d.x == -1:
					a = Vector3(x, 0, z + 1)
					b = Vector3(x, 0, z)
				elif d.y == 1:
					a = Vector3(x + 1, 0, z + 1)
					b = Vector3(x, 0, z + 1)
				_quad(_tool(tools, side), a + Vector3.UP * nh, b + Vector3.UP * nh, b + Vector3.UP * h,
					a + Vector3.UP * h, n)
	_commit_mesh("Murs", tools, true)
	# collisions : bandes horizontales de cases pleines (murs et forêt dense)
	var body := StaticBody3D.new()
	body.name = "MursPhysiques"
	add_child(body)
	for z in height:
		var x := 0
		while x < width:
			if cell(x, z) in ["#", "T"]:
				var x0 := x
				while x < width and cell(x, z) in ["#", "T"]:
					x += 1
				_add_box(body, Vector3(x - x0, 3.0, 1.0), Vector3((x0 + x) * 0.5, 1.5, z + 0.5))
			else:
				x += 1


func _tool(tools: Dictionary, key: String) -> SurfaceTool:
	if not tools.has(key):
		var st := SurfaceTool.new()
		st.begin(Mesh.PRIMITIVE_TRIANGLES)
		tools[key] = st
	return tools[key]


## Quad a-b-c-d ; l'ordre des sommets est corrigé pour que la face regarde `normal`.
func _quad(st: SurfaceTool, a: Vector3, b: Vector3, c: Vector3, d: Vector3, normal: Vector3) -> void:
	for tri in [[a, b, c], [a, c, d]]:
		var p0: Vector3 = tri[0]
		var p1: Vector3 = tri[1]
		var p2: Vector3 = tri[2]
		if (p1 - p0).cross(p2 - p0).dot(normal) > 0.0:     # Godot : faces avant dans le sens horaire
			var tmp := p1
			p1 = p2
			p2 = tmp
		for p in [p0, p1, p2]:
			st.set_normal(normal)
			st.add_vertex(p)


func _commit_mesh(mesh_name: String, tools: Dictionary, shadows: bool) -> void:
	var mesh := ArrayMesh.new()
	for key in tools:
		var st: SurfaceTool = tools[key]
		st.commit(mesh)
		mesh.surface_set_material(mesh.get_surface_count() - 1, _color_mat(key))
	var mi := MeshInstance3D.new()
	mi.name = mesh_name
	mi.mesh = mesh
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON if shadows \
		else GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(mi)


# --------------------------------------------------------------------------- végétation (MultiMesh)
func _build_vegetation() -> void:
	var trees := {"P_Arbre": [], "P_Arbre2": []}
	var tufts: Array = []
	for z in range(-BORDER, height + BORDER):
		for x in range(-BORDER, width + BORDER):
			var c := _render_cell(x, z)
			if c == "T":
				# lisière pleine près des chemins, forêt un peu plus clairsemée au loin
				var dist := _distance_to_open(x, z, 3)
				if dist > 3 and _hash(x, z) % 7 == 0:
					continue
				var t := Transform3D(Basis(Vector3.UP, _rng.randf() * TAU).scaled(Vector3.ONE * _rng.randf_range(0.85, 1.3)),
					cell_center(x, z) + Vector3(_rng.randf_range(-0.2, 0.2), 0, _rng.randf_range(-0.2, 0.2)))
				trees["P_Arbre" if _hash(x, z) % 3 else "P_Arbre2"].append(t)
			elif c == "." and _hash(x, z) % 4 == 0:
				tufts.append(Transform3D(Basis(Vector3.UP, _rng.randf() * TAU),
					cell_center(x, z) + Vector3(_rng.randf_range(-0.35, 0.35), 0, _rng.randf_range(-0.35, 0.35))))
	for tpl in trees:
		_multimesh(tpl, trees[tpl], true)
	_multimesh("P_Touffe", tufts, false)
	stats["arbres"] = trees["P_Arbre"].size() + trees["P_Arbre2"].size()


func _distance_to_open(x: int, z: int, max_d: int) -> int:
	for d in range(1, max_d + 1):
		for dz in range(-d, d + 1):
			for dx in range(-d, d + 1):
				if maxi(absi(dx), absi(dz)) == d and _is_open(cell(x + dx, z + dz)):
					return d
	return max_d + 1


func _multimesh(template: String, transforms: Array, shadows: bool) -> void:
	if transforms.is_empty():
		return
	var tpl: Node3D = _templates[template]
	for mi in tpl.find_children("*", "MeshInstance3D", true, false):
		var local := _local_transform(mi, tpl)
		var mm := MultiMesh.new()
		mm.transform_format = MultiMesh.TRANSFORM_3D
		mm.mesh = mi.mesh
		mm.instance_count = transforms.size()
		for i in transforms.size():
			mm.set_instance_transform(i, transforms[i] * local)
		var mmi := MultiMeshInstance3D.new()
		mmi.name = String(mi.name) + "_x%d" % transforms.size()
		mmi.multimesh = mm
		mmi.material_override = _toon(mi.get_active_material(0), String(mi.name))
		mmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON if shadows \
			else GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		add_child(mmi)


func _local_transform(node: Node3D, root: Node3D) -> Transform3D:
	var t := node.transform
	var p := node.get_parent()
	while p != root and p is Node3D:
		t = (p as Node3D).transform * t
		p = p.get_parent()
	return t


# --------------------------------------------------------------------------- objets case par case
func _build_cells() -> void:
	for z in height:
		for x in width:
			var c := cell(x, z)
			var pos := cell_center(x, z)
			match c:
				"S":
					start_position = pos
				"P":
					_static_prop("P_Pilier", pos, 0.42, 2.6, _rng.randi_range(0, 3) * PI * 0.5)
				"p":
					_static_prop("P_PilierBrise", pos, 0.45, 1.0, _rng.randf() * TAU)
				"r":
					_static_prop("P_Rocher", pos, 0.45, 0.7, _rng.randf() * TAU)
				"L":
					_static_prop("P_Stele", pos, 0.35, 1.0, PI)
				"t":
					_static_prop("P_Torche", pos, 0.15, 1.4, 0.0)
					_add_torch_light(pos + Vector3.UP * 1.65)
				"%":
					var bones := prop("P_Ossements")
					add_child(bones)
					bones.position = pos
					bones.rotation.y = _rng.randf() * TAU
				"o", "c":
					var b := Breakable.new()
					b.setup(prop("P_Jarre" if c == "o" else "P_Caisse"), "jarre" if c == "o" else "caisse")
					add_child(b)
					b.position = pos
					b.rotation.y = _rng.randf() * TAU
					b.broken.connect(_on_breakable_broken)
					_count("objets cassables")
				"B":
					var br := Brazier.new()
					br.setup(prop("P_Brasero"), hero, _respawn_near(x, z))
					add_child(br)
					br.position = pos
					br.lit.connect(func(b2): checkpoint_reached.emit(b2))
					_count("braseros")
				"C":
					var ch := Chest.new()
					ch.setup(prop("P_Coffre"), String(data["chests"].get("%d,%d" % [x, z], "")), hero)
					add_child(ch)
					ch.position = pos
					ch.rotation.y = PI
					ch.opened.connect(func(c2): chest_opened.emit(c2.reward))
					_count("coffres")
				"^":
					var trap := SpikeTrap.new()
					trap.setup(prop("P_Piques"), float(z % 2) * SpikeTrap.CYCLE * 0.5, hero)
					add_child(trap)
					trap.position = pos
					_count("piques")
				"s", "k":
					spawn_enemy("slime" if c == "s" else "skeleton", pos, STATIC_AGGRO)
					_count("ennemis placés")
				"K":
					boss = BOSS.instantiate()
					boss.position = pos
					boss.target = hero
					boss.crown = prop("P_Couronne")
					boss.minion_spawner = func(p: Vector3): return spawn_enemy("slime", p, INF, 2, 0.7)
					add_child(boss)
					boss.defeated.connect(_on_boss_defeated)
				_:
					if c >= "1" and c <= "9":
						if not spawn_points.has(c):
							spawn_points[c] = []
						spawn_points[c].append(pos)


func _count(what: String) -> void:
	stats[what] = int(stats.get(what, 0)) + 1


func _static_prop(template: String, pos: Vector3, radius: float, h: float, rot: float) -> void:
	var body := StaticBody3D.new()
	body.add_child(prop(template))
	var shape := CollisionShape3D.new()
	var cyl := CylinderShape3D.new()
	cyl.radius = radius
	cyl.height = h
	shape.shape = cyl
	shape.position.y = h * 0.5
	body.add_child(shape)
	add_child(body)
	body.position = pos
	body.rotation.y = rot


func _add_torch_light(pos: Vector3) -> void:
	var light := OmniLight3D.new()
	light.light_color = Color(1.0, 0.62, 0.3)
	light.omni_range = 3.5
	light.shadow_enabled = false
	add_child(light)
	light.position = pos
	_torches.append(light)


func _respawn_near(x: int, z: int) -> Vector3:
	for d in [Vector2i(1, 0), Vector2i(0, 1), Vector2i(-1, 0), Vector2i(0, -1), Vector2i(1, 1)]:
		if cell(x + d.x, z + d.y) in [".", ",", "_"]:
			return cell_center(x + d.x, z + d.y)
	return cell_center(x, z) + Vector3(1, 0, 0)


func _build_gates() -> void:
	for id in data["gates"]:
		var g := Gate.new()
		var cells: Array = []
		for c in data["gates"][id]["cells"]:
			cells.append(Vector2i(int(c[0]), int(c[1])))
		g.setup(id, cells, func(): return prop("P_Herse"), bool(data["gates"][id]["open"]))
		add_child(g)
		gates[id] = g


func _build_encounters() -> void:
	for cfg in data["encounters"]:
		var e := Encounter.new()
		e.setup(cfg, self)
		add_child(e)
		e.started.connect(func(enc): encounter_started.emit(enc))
		e.cleared.connect(func(enc): encounter_cleared.emit(enc))
		encounters.append(e)


# =========================================================================== monde vivant
func spawn_enemy(kind: String, pos: Vector3, aggro := INF, hp_override := 0, size := 1.0) -> Enemy:
	var e: Enemy = (SLIME if kind == "slime" else SKELETON).instantiate()
	e.position = pos
	e.target = hero
	e.nav = self
	e.aggro_range = aggro
	e.size_scale = size
	if hp_override > 0:
		e.max_hp = hp_override
	e.died.connect(_on_enemy_died)
	enemies_root.add_child(e)
	return e


func spawn_heart(pos: Vector3) -> void:
	var h := HeartPickup.new()
	add_child(h)
	h.position = Vector3(pos.x, 0.0, pos.z)
	h.setup(prop("P_Coeur"), hero)


func _on_enemy_died(e: Enemy) -> void:
	if randf() < ENEMY_HEART_CHANCE:
		spawn_heart(e.global_position)


func _on_breakable_broken(b: Breakable) -> void:
	astar.set_point_solid(_cell_of(b.global_position), false)
	if randf() < b.heart_chance:
		spawn_heart(b.global_position)


func set_gates(ids: Array, open: bool) -> void:
	for id in ids:
		if gates.has(id):
			if open:
				gates[id].open()
			else:
				gates[id].close()
			_update_gate_nav(gates[id])


func hero_alive() -> bool:
	return is_instance_valid(hero) and hero.state != Hero.State.DEAD


func hero_in_rect(r: Array) -> bool:
	var p := hero.global_position
	return p.x >= float(r[0]) and p.x < float(r[2]) + 1.0 and p.z >= float(r[1]) and p.z < float(r[3]) + 1.0


func _process(delta: float) -> void:
	_time += delta
	for i in _torches.size():
		_torches[i].light_energy = 2.2 + 0.25 * sin(_time * 11.0 + i * 2.0) + 0.15 * sin(_time * 23.0 + i)
	if not hero_alive():
		return
	_update_zone()
	for i in data["hints"].size():
		if not _hints_shown.has(i) and hero_in_rect(data["hints"][i]["rect"]):
			_hints_shown[i] = true
			hint_requested.emit(String(data["hints"][i]["text"]))
	if boss and not _boss_active and boss.state == BossSlime.State.DORMANT and hero_in_rect(data["boss"]["rect"]):
		_boss_active = true
		set_gates(data["boss"]["gates"], false)
		boss.awaken()
		boss_started.emit(boss)


func _on_boss_defeated(b: BossSlime) -> void:
	_boss_active = false
	set_gates(data["boss"]["open_on_victory"], true)
	boss_defeated.emit(b)


## Le héros revient au brasero : la salle en cours et le boss sont réinitialisés.
func on_hero_respawn() -> void:
	for e in encounters:
		e.reset()
	if boss and _boss_active and boss.state != BossSlime.State.DEAD:
		boss.reset_fight()
		_boss_active = false
		set_gates(data["boss"]["gates"], true)


# --------------------------------------------------------------------------- zones et lumière
func _zone_music(x: int, z: int) -> String:
	for zone in data["zones"]:
		var r: Array = zone["rect"]
		if x >= r[0] and x <= r[2] and z >= r[1] and z <= r[3]:
			return String(zone["music"])
	return ""


func _update_zone() -> void:
	var p := hero.global_position
	var idx := -1
	for i in data["zones"].size():
		var r: Array = data["zones"][i]["rect"]
		if p.x >= r[0] and p.x < r[2] + 1 and p.z >= r[1] and p.z < r[3] + 1:
			idx = i
			break
	if idx == _zone_index or idx < 0:
		return
	var previous := _zone_index
	_zone_index = idx
	var zone: Dictionary = data["zones"][idx]
	if _sun_tween:
		_sun_tween.kill()
	_sun_tween = create_tween()
	_sun_tween.tween_property(_sun, "light_energy", float(zone["sun"]), 1.5 if previous >= 0 else 0.01)
	if previous < 0 or String(data["zones"][previous]["name"]) != String(zone["name"]):
		zone_changed.emit(zone)


func _setup_environment() -> void:
	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color("1c1a28")
	env.ambient_light_source = Environment.AMBIENT_SOURCE_DISABLED
	env.reflected_light_source = Environment.REFLECTION_SOURCE_DISABLED
	env.tonemap_mode = Environment.TONE_MAPPER_LINEAR
	var world_env := WorldEnvironment.new()
	world_env.environment = env
	add_child(world_env)
	_sun = DirectionalLight3D.new()
	_sun.name = "Soleil"
	_sun.shadow_enabled = true
	_sun.directional_shadow_mode = DirectionalLight3D.SHADOW_ORTHOGONAL
	_sun.directional_shadow_max_distance = 18.0
	_sun.shadow_bias = 0.02
	_sun.shadow_normal_bias = 1.0
	add_child(_sun)
	_sun.look_at(_sun.global_position + SUN_DIRECTION.normalized(), Vector3.UP)


func _add_box(body: StaticBody3D, box_size: Vector3, pos: Vector3) -> void:
	var shape := BoxShape3D.new()
	shape.size = box_size
	var col := CollisionShape3D.new()
	col.shape = shape
	col.position = pos
	body.add_child(col)
