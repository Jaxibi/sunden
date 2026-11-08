extends Node3D
## Niveau importé de Blender : matériaux toon, lumière, collisions et torches ajoutées au chargement.

const HALF_SIZE := 14.0
# Direction du soleil, identique à la scène Blender (repère Godot : Y en haut)
const SUN_DIRECTION := Vector3(0.229, -0.743, -0.629)
const SOLID_PREFIXES := ["Pilier", "Mur", "Rocher", "Caisse", "Torche"]
const NOT_SOLID := ["Mousse", "Flamme", "Coeur", "Cerclage", "Coupe", "Chapiteau"]

var _torches: Array[OmniLight3D] = []
var _time := 0.0


func _ready() -> void:
	var model := $Model
	ToonMaterials.apply(model)
	_setup_environment()
	for node in model.find_children("*", "MeshInstance3D", true, false):
		var mi := node as MeshInstance3D
		var n := String(mi.name)
		if n.ends_with("_Flamme"):
			_add_torch_light(mi.global_position + Vector3.UP * 0.3)
		if n == "Sol" or n.begins_with("Touffe"):
			mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		if _is_solid(n):
			mi.create_convex_collision(true, false)
	_add_ground_and_walls()


func _process(delta: float) -> void:
	_time += delta
	for i in _torches.size():
		_torches[i].light_energy = 2.2 + 0.25 * sin(_time * 11.0 + i * 2.0) + 0.15 * sin(_time * 23.0 + i)


func _is_solid(n: String) -> bool:
	if n.begins_with("Arbre"):
		return n.ends_with("_Tronc")
	for bad in NOT_SOLID:
		if n.contains(bad):
			return false
	for p in SOLID_PREFIXES:
		if n.begins_with(p):
			return true
	return false


func _setup_environment() -> void:
	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color("3c4a72")
	env.ambient_light_source = Environment.AMBIENT_SOURCE_DISABLED
	env.reflected_light_source = Environment.REFLECTION_SOURCE_DISABLED
	env.tonemap_mode = Environment.TONE_MAPPER_LINEAR
	var world_env := WorldEnvironment.new()
	world_env.environment = env
	add_child(world_env)

	var sun := DirectionalLight3D.new()
	sun.name = "Soleil"
	sun.shadow_enabled = true
	sun.directional_shadow_mode = DirectionalLight3D.SHADOW_ORTHOGONAL
	sun.directional_shadow_max_distance = 45.0
	add_child(sun)
	sun.look_at(sun.global_position + SUN_DIRECTION.normalized(), Vector3.UP)


func _add_torch_light(pos: Vector3) -> void:
	var light := OmniLight3D.new()
	light.light_color = Color(1.0, 0.62, 0.3)
	light.omni_range = 3.5
	light.shadow_enabled = false
	add_child(light)
	light.global_position = pos
	_torches.append(light)


func _add_ground_and_walls() -> void:
	var body := StaticBody3D.new()
	body.name = "Limites"
	add_child(body)
	_add_box(body, Vector3(HALF_SIZE * 2.0, 1.0, HALF_SIZE * 2.0), Vector3(0.0, -0.5, 0.0))
	var edge := HALF_SIZE - 1.5
	for side in [-1.0, 1.0]:
		_add_box(body, Vector3(1.0, 4.0, HALF_SIZE * 2.0), Vector3(edge * side, 2.0, 0.0))
		_add_box(body, Vector3(HALF_SIZE * 2.0, 4.0, 1.0), Vector3(0.0, 2.0, edge * side))


func _add_box(body: StaticBody3D, box_size: Vector3, pos: Vector3) -> void:
	var shape := BoxShape3D.new()
	shape.size = box_size
	var col := CollisionShape3D.new()
	col.shape = shape
	col.position = pos
	body.add_child(col)
