class_name Hero
extends CharacterBody3D
## Héros : déplacement relatif à la caméra, combo de 3 coups, esquive en roulade.
## Les poses viennent des animations Blender (blender/rig_hero.py) ; le code gère le rythme,
## la touche, la traînée d'épée et la rotation du coup tournoyant.

signal health_changed(hp: int, max_hp: int)
signal armor_changed(set_name: String)
signal died

enum State { MOVE, ATTACK, DODGE, HURT, DEAD }
enum ArmorSet { TISSU, CUIR, PLATES }

const ARMOR_NODES := ["Equip_Tissu", "Equip_Cuir", "Equip_Plates"]
const ARMOR_NAMES := ["Tenue de Tissu", "Armure de Cuir", "Harnois de Plates"]

## Durées en secondes = images Blender / 30 (préparation, coup actif, récupération).
## trail_from/trail_to : balayage de l'épée en degrés depuis l'avant (positif = vers la gauche).
const ATTACKS := [
	{"anim": "attaque_1", "windup": 0.1, "active": 0.1, "recovery": 0.233,
		"trail_from": -100.0, "trail_to": 95.0,
		"range": 1.8, "arc": 170.0, "damage": 1, "knockback": 6.0, "lunge": 4.0, "stop": 0.05, "shake": 1.0},
	{"anim": "attaque_2", "windup": 0.1, "active": 0.1, "recovery": 0.233,
		"trail_from": 100.0, "trail_to": -100.0,
		"range": 1.8, "arc": 170.0, "damage": 1, "knockback": 6.0, "lunge": 4.0, "stop": 0.05, "shake": 1.0},
	{"anim": "attaque_3", "windup": 0.167, "active": 0.167, "recovery": 0.333, "spin": true,
		"range": 2.1, "arc": 360.0, "damage": 2, "knockback": 11.0, "lunge": 2.0, "stop": 0.09, "shake": 3.0},
]
const LOOPING := ["repos", "course"]
const MASK_NORMAL := 1 | 4        # monde + ennemis
const MASK_DODGE := 1             # la roulade traverse les ennemis

@export var move_speed := 5.0
@export var acceleration := 45.0
@export var dodge_speed := 11.0
@export var dodge_time := 0.26
@export var dodge_cooldown := 0.3
@export var max_hp := 100
@export var invulnerable_after_hit := 0.7
## Cadence des animations (images par seconde). 0 = animation fluide.
## Une cadence basse donne l'aspect « image par image » du pixel art.
@export var anim_fps := 15.0
@export var armor_set: ArmorSet = ArmorSet.PLATES

var hp := 0
var state := State.MOVE
var state_time := 0.0
var facing := Vector3(0.707, 0.0, -0.707)
var combo := 0

var _attack_buffer := 0.0
var _dodge_cd := 0.0
var _dodge_velocity := Vector3.ZERO
var _invulnerable := 0.0
var _has_hit := false
var _step_timer := 0.0
var _dodge_hits: Array = []
## Bottes de rafale (coffre de l'alcôve) : la roulade blesse et repousse.
var dodge_strike := false
## Tests automatiques uniquement : ne prend aucun dégât.
var god_mode := false
var _flash := 0.0
var _flash_on := false
var _mats: Array[ShaderMaterial] = []
var _trails: Array[MeshInstance3D] = []
var _animator: SteppedAnimator

@onready var model: Node3D = $Model


func _ready() -> void:
	hp = max_hp
	add_to_group("hero")
	collision_mask = MASK_NORMAL
	_mats = ToonMaterials.apply(model)
	set_armor_set(armor_set, false)
	_setup_animations()
	_build_trails()
	model.rotation.y = _yaw(facing)


func set_armor_set(new_set: ArmorSet, fx := true) -> void:
	armor_set = new_set
	for i in ARMOR_NODES.size():
		var n := model.find_child(ARMOR_NODES[i], true, false) as Node3D
		if n:
			n.visible = (i == int(armor_set))
	if fx:
		Juice.burst(global_position + Vector3.UP * 0.8, [Color("fff1d6"), Color("e8b83a")], 8, 3.0, 0.08)
		armor_changed.emit(ARMOR_NAMES[int(armor_set)])


func cycle_armor_set() -> void:
	set_armor_set(((int(armor_set) + 1) % ARMOR_NODES.size()) as ArmorSet, true)


# --------------------------------------------------------------------------- boucle
func _physics_process(delta: float) -> void:
	state_time += delta
	_attack_buffer = maxf(_attack_buffer - delta, 0.0)
	_dodge_cd = maxf(_dodge_cd - delta, 0.0)
	_invulnerable = maxf(_invulnerable - delta, 0.0)
	if state != State.DEAD and Input.is_action_just_pressed("attack"):
		_attack_buffer = 0.2

	var input_dir := _input_direction()
	var hv := Vector3(velocity.x, 0.0, velocity.z)

	match state:
		State.MOVE:
			hv = hv.move_toward(input_dir * move_speed, acceleration * delta)
			if input_dir != Vector3.ZERO:
				facing = input_dir.normalized()
			if _attack_buffer > 0.0:
				_start_attack(0, input_dir)
			elif Input.is_action_just_pressed("dodge") and _dodge_cd <= 0.0:
				hv = _start_dodge(input_dir)
			else:
				var running := hv.length() > 0.6
				_play("course" if running else "repos")
				# deux pas par cycle de course (16 images à 30 i/s)
				_step_timer = _step_timer - delta if running else 0.05
				if running and _step_timer <= 0.0:
					_step_timer = 0.267
					Sound.play("footstep")
		State.ATTACK:
			hv = _update_attack(delta, hv, input_dir)
		State.DODGE:
			hv = _dodge_velocity
			if dodge_strike:
				_dodge_strike_hits()
			if state_time >= dodge_time:
				collision_mask = MASK_NORMAL
				hv *= 0.35
				_set_state(State.MOVE)
		State.HURT:
			hv = hv.move_toward(Vector3.ZERO, 30.0 * delta)
			if state_time >= 0.25:
				_set_state(State.MOVE)
		State.DEAD:
			hv = hv.move_toward(Vector3.ZERO, 30.0 * delta)

	velocity.x = hv.x
	velocity.z = hv.z
	velocity.y = 0.0 if is_on_floor() else velocity.y - 25.0 * delta
	move_and_slide()
	_update_visuals(delta)


func _process(delta: float) -> void:
	_animator.update(delta)


func _input_direction() -> Vector3:
	if state == State.DEAD:
		return Vector3.ZERO
	var v := Input.get_vector("move_left", "move_right", "move_up", "move_down")
	if v == Vector2.ZERO:
		return Vector3.ZERO
	var right := Vector3.RIGHT
	var forward := Vector3.FORWARD
	var cam := get_viewport().get_camera_3d()
	if cam:
		right = Vector3(cam.global_basis.x.x, 0.0, cam.global_basis.x.z).normalized()
		forward = Vector3(-cam.global_basis.z.x, 0.0, -cam.global_basis.z.z).normalized()
	var dir := right * v.x - forward * v.y
	return dir.normalized() * minf(v.length(), 1.0)


# --------------------------------------------------------------------------- attaque
func _start_attack(index: int, input_dir: Vector3) -> void:
	combo = index
	_attack_buffer = 0.0
	_has_hit = false
	if input_dir != Vector3.ZERO:
		facing = input_dir.normalized()
	else:
		var e := _nearest_enemy(3.5)
		if e:
			var to := e.global_position - global_position
			to.y = 0.0
			if to.length() > 0.01:
				facing = to.normalized()
	model.rotation.y = _yaw(facing)
	_hide_trails()
	_set_state(State.ATTACK)
	_play(ATTACKS[index]["anim"], true)


func _update_attack(delta: float, hv: Vector3, input_dir: Vector3) -> Vector3:
	var a: Dictionary = ATTACKS[combo]
	var windup: float = a["windup"]
	var active: float = a["active"]
	var recovery: float = a["recovery"]
	var t := state_time

	if t < windup:
		return hv.move_toward(Vector3.ZERO, 40.0 * delta)

	if t < windup + active:
		var k := (t - windup) / active
		if a.get("spin", false):
			model.rotation.y = _yaw(facing) + TAU * k
		if not _trails[combo].visible:
			Sound.play("spin_attack" if a.get("spin", false) else "sword_swing")
		_trails[combo].visible = true
		if not _has_hit and k >= 0.3:
			_has_hit = true
			_do_hit(a)
		return facing * float(a["lunge"])

	if t > windup + active + 0.07:
		_trails[combo].visible = false
	# Fenêtre d'enchaînement : coup suivant ou esquive pendant la récupération
	if combo < ATTACKS.size() - 1 and _attack_buffer > 0.0:
		_start_attack(combo + 1, input_dir)
		return hv
	if Input.is_action_just_pressed("dodge") and _dodge_cd <= 0.0:
		return _start_dodge(input_dir)
	if t >= windup + active + recovery:
		_hide_trails()
		combo = 0
		_set_state(State.MOVE)
	return hv.move_toward(Vector3.ZERO, 40.0 * delta)


func _do_hit(a: Dictionary) -> void:
	var hits := 0
	var reach: float = a["range"]
	var arc: float = a["arc"]
	# monstres, boss, jarres et caisses : tout ce qui a take_hit() et un rayon
	for node in get_tree().get_nodes_in_group("hittable"):
		var e := node as Node3D
		var to := e.global_position - global_position
		to.y = 0.0
		var dist := to.length()
		if dist > reach + float(e.get("radius")):
			continue
		if arc < 360.0 and dist > 0.3 and rad_to_deg(facing.angle_to(to)) > arc * 0.5:
			continue
		if e.take_hit(a["damage"], global_position, a["knockback"]):
			hits += 1
	if hits > 0:
		Juice.hitstop(a["stop"])
		Juice.shake(a["shake"])
		Sound.play("sword_hit", 2.0 if a.get("spin", false) else 0.0)


func _nearest_enemy(max_dist: float) -> Node3D:
	var best: Node3D = null
	var best_d := max_dist
	for e in get_tree().get_nodes_in_group("enemies"):
		var d := global_position.distance_to(e.global_position)
		if d < best_d:
			best_d = d
			best = e
	return best


# --------------------------------------------------------------------------- esquive et dégâts
func _start_dodge(input_dir: Vector3) -> Vector3:
	var dir := input_dir.normalized() if input_dir != Vector3.ZERO else facing
	facing = dir
	model.rotation.y = _yaw(facing)
	_dodge_velocity = dir * dodge_speed
	_dodge_cd = dodge_time + dodge_cooldown
	_invulnerable = maxf(_invulnerable, dodge_time + 0.05)
	_dodge_hits.clear()
	collision_mask = MASK_DODGE
	_hide_trails()
	Juice.burst(global_position + Vector3.UP * 0.1, [Color("d8d2c0"), Color("aaa290")], 5, 2.0, 0.08)
	_set_state(State.DODGE)
	_play("esquive", true)
	Sound.play("dodge_roll")
	return _dodge_velocity


## Bottes de rafale : chaque monstre touché pendant la roulade prend 1 et est repoussé.
func _dodge_strike_hits() -> void:
	for node in get_tree().get_nodes_in_group("enemies"):
		var e := node as Node3D
		if _dodge_hits.has(e) or not e.has_method("take_hit"):
			continue
		var d := e.global_position - global_position
		d.y = 0.0
		if d.length() <= 0.9 + float(e.get("radius")):
			_dodge_hits.append(e)
			if e.take_hit(1, global_position, 7.0):
				Juice.hitstop(0.03)
				Sound.play("sword_hit", -4.0, 1.2)


func heal(amount: int) -> void:
	if state == State.DEAD:
		return
	hp = mini(hp + amount, max_hp)
	health_changed.emit(hp, max_hp)


## Retour au brasero après une chute : PV pleins, debout.
func respawn(pos: Vector3) -> void:
	global_position = pos
	velocity = Vector3.ZERO
	hp = max_hp
	_invulnerable = 1.0
	collision_mask = MASK_NORMAL
	model.rotation = Vector3(0.0, _yaw(facing), 0.0)
	model.visible = true
	_hide_trails()
	_set_state(State.MOVE)
	_play("repos", true)
	health_changed.emit(hp, max_hp)


func take_damage(amount: int, from_pos: Vector3) -> void:
	if state == State.DEAD or _invulnerable > 0.0 or god_mode:
		return
	hp = maxi(hp - amount, 0)
	health_changed.emit(hp, max_hp)
	_invulnerable = invulnerable_after_hit
	_flash = 0.1
	var away := global_position - from_pos
	away.y = 0.0
	away = away.normalized() if away.length() > 0.01 else -facing
	velocity.x = away.x * 7.0
	velocity.z = away.z * 7.0
	collision_mask = MASK_NORMAL
	_hide_trails()
	Juice.hitstop(0.07)
	Juice.shake(3.0)
	Juice.burst(global_position + Vector3.UP * 0.8, [Color("e04a4a"), Color("ffffff")], 6, 3.5, 0.08)
	if hp <= 0:
		_set_state(State.DEAD)
		_play("mort", true)
		Sound.play("hero_hurt")
		died.emit()
	else:
		_set_state(State.HURT)
		_play("touche", true)
		Sound.play("hero_hurt")


func _set_state(s: State) -> void:
	state = s
	state_time = 0.0


# --------------------------------------------------------------------------- animation
func _setup_animations() -> void:
	_animator = SteppedAnimator.new(model, anim_fps, LOOPING)
	_play("repos")


func _play(anim_name: String, restart := false) -> void:
	_animator.play(anim_name, restart)


# --------------------------------------------------------------------------- visuel
func _update_visuals(delta: float) -> void:
	var spinning := false
	if state == State.ATTACK:
		var a: Dictionary = ATTACKS[combo]
		var windup: float = a["windup"]
		var active: float = a["active"]
		spinning = a.get("spin", false) and state_time >= windup and state_time < windup + active
	if not spinning and state != State.DEAD:
		model.rotation.y = lerp_angle(model.rotation.y, _yaw(facing), 1.0 - exp(-18.0 * delta))

	# clignotement pendant l'invulnérabilité qui suit un coup reçu
	model.visible = state in [State.DEAD, State.DODGE] or _invulnerable <= 0.0 \
		or int(_invulnerable * 20.0) % 2 == 0

	_flash -= delta
	var on := _flash > 0.0
	if on != _flash_on:
		_flash_on = on
		for m in _mats:
			m.set_shader_parameter("flash_color", Color(1, 1, 1, 1.0 if on else 0.0))


func _yaw(dir: Vector3) -> float:
	return atan2(-dir.x, -dir.z)


func _hide_trails() -> void:
	for t in _trails:
		t.visible = false


func _build_trails() -> void:
	var mat := StandardMaterial3D.new()
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.cull_mode = BaseMaterial3D.CULL_DISABLED
	mat.vertex_color_use_as_albedo = true
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mat.depth_draw_mode = BaseMaterial3D.DEPTH_DRAW_DISABLED
	mat.render_priority = 1
	for a in ATTACKS:
		var mi := MeshInstance3D.new()
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		mi.visible = false
		if a.get("spin", false):
			mi.mesh = _make_arc(0.0, 359.0, 2.0, 0.38, 0.7, mat, false)
			add_child(mi)              # ne tourne pas avec le modèle
		else:
			mi.mesh = _make_arc(a["trail_from"], a["trail_to"], 1.55, 0.52, 0.9, mat, true)
			model.add_child(mi)
		_trails.append(mi)


## Ruban en arc de cercle à deux bandes (bord d'attaque blanc vif, sillage bleu glacier), sans contour noir.
func _make_arc(from_deg: float, to_deg: float, r_out: float, width: float, height: float,
		mat: Material, tapered: bool) -> ArrayMesh:
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var n := 16
	var inner: Array[Vector3] = []
	var mid: Array[Vector3] = []
	var outer: Array[Vector3] = []
	var col_edge := Color("ffffff")
	var col_wake := Color("7ce8ff")
	for i in n + 1:
		var k := float(i) / n
		var ang := deg_to_rad(lerpf(from_deg, to_deg, k))
		var w := width * pow(k, 1.3) + 0.10 if tapered else width
		var dir := Vector3(-sin(ang), 0.0, -cos(ang))
		inner.append(dir * (r_out - w) + Vector3.UP * height)
		mid.append(dir * (r_out - w * 0.42) + Vector3.UP * height)
		outer.append(dir * r_out + Vector3.UP * height)
	for i in n:
		st.set_color(col_wake)
		for v in [inner[i], mid[i], mid[i + 1], inner[i], mid[i + 1], inner[i + 1]]:
			st.add_vertex(v)
		st.set_color(col_edge)
		for v in [mid[i], outer[i], outer[i + 1], mid[i], outer[i + 1], mid[i + 1]]:
			st.add_vertex(v)
	st.set_material(mat)
	return st.commit()
