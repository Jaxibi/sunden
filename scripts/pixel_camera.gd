class_name PixelCamera
extends Camera3D
## Caméra orthographique de hack & slash, alignée sur la grille de pixels.
## - la position est arrondie au pixel près : le décor ne scintille pas quand on bouge ;
## - l'écart de moins d'un pixel est exposé dans `subpixel` : Main décale l'image agrandie
##   d'autant, ce qui garde un défilement fluide ;
## - les tremblements d'écran se font en pixels entiers.

const OUTLINE_SHADER := preload("res://shaders/outline.gdshader")

@export var target_path: NodePath
@export var pitch_degrees := -35.0
@export var yaw_degrees := 45.0
@export var distance := 20.0
@export var pixels_per_meter := 320.0 / 11.0
@export var follow_speed := 8.0
@export var look_height := 0.6
@export var outline_enabled := true

## Décalage sous-pixel (en pixels natifs) à appliquer à l'image agrandie.
var subpixel := Vector2.ZERO

var _target: Node3D
var _follow := Vector3.ZERO
var _shake := 0.0


func _ready() -> void:
	projection = PROJECTION_ORTHOGONAL
	rotation_degrees = Vector3(pitch_degrees, yaw_degrees, 0.0)
	near = 0.1
	far = 100.0
	_target = get_node_or_null(target_path) as Node3D
	if _target:
		_follow = _target.global_position
	Juice.camera = self
	if outline_enabled:
		_add_outline()


func shake(pixels: float) -> void:
	_shake = maxf(_shake, pixels)


func _process(delta: float) -> void:
	var vp_height := float(get_viewport().size.y)
	size = vp_height / pixels_per_meter
	var texel := 1.0 / pixels_per_meter

	if is_instance_valid(_target):
		_follow = _follow.lerp(_target.global_position, 1.0 - exp(-follow_speed * delta))
	var desired := _follow + Vector3.UP * look_height + global_basis.z * distance

	var local := global_basis.inverse() * desired
	var snapped_local := Vector3(snappedf(local.x, texel), snappedf(local.y, texel), local.z)
	var err := (local - snapped_local) / texel
	subpixel = Vector2(-err.x, err.y)

	if _shake > 0.0:
		snapped_local.x += roundf(randf_range(-_shake, _shake)) * texel
		snapped_local.y += roundf(randf_range(-_shake, _shake)) * texel
		_shake = move_toward(_shake, 0.0, delta * 40.0)

	global_position = global_basis * snapped_local


func _add_outline() -> void:
	var mat := ShaderMaterial.new()
	mat.shader = OUTLINE_SHADER
	var quad := QuadMesh.new()
	quad.size = Vector2(2.0, 2.0)
	quad.material = mat
	var mi := MeshInstance3D.new()
	mi.name = "OutlinePass"
	mi.mesh = quad
	mi.extra_cull_margin = 16384.0
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(mi)
	mi.position = Vector3(0.0, 0.0, -1.0)
