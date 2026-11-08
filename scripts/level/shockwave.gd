class_name Shockwave
extends Node3D
## Onde de choc du Roi Gluant : anneau qui s'élargit au sol. Impossible à fuir à temps :
## il faut la traverser en roulade (invulnérable).

const MAX_RADIUS := 7.0
const DURATION := 0.85
const BAND := 0.45
const DAMAGE := 15

var hero: Hero
var _t := 0.0
var _hit := false
var _ring := MeshInstance3D.new()
var _mat := StandardMaterial3D.new()


func setup(the_hero: Hero) -> void:
	hero = the_hero
	_mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	_mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	_mat.cull_mode = BaseMaterial3D.CULL_DISABLED
	_mat.depth_draw_mode = BaseMaterial3D.DEPTH_DRAW_DISABLED
	_mat.render_priority = 1
	_mat.albedo_color = Color(0.85, 0.65, 1.0, 0.85)
	_ring.mesh = _annulus(1.0, 1.0 - 0.09, 40)
	_ring.material_override = _mat
	_ring.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_ring.position.y = 0.06
	add_child(_ring)


func _process(delta: float) -> void:
	_t += delta
	var k := _t / DURATION
	if k >= 1.0:
		queue_free()
		return
	var r := lerpf(0.6, MAX_RADIUS, k)
	_ring.scale = Vector3(r, 1.0, r)
	_mat.albedo_color.a = 0.9 * (1.0 - k * k)
	if _hit or not is_instance_valid(hero):
		return
	var d := hero.global_position - global_position
	d.y = 0.0
	if absf(d.length() - r) < BAND:
		_hit = true
		hero.take_damage(DAMAGE, global_position)     # sans effet pendant la roulade


static func _annulus(outer: float, inner: float, segments: int) -> ArrayMesh:
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	for i in segments:
		var a0 := TAU * i / segments
		var a1 := TAU * (i + 1) / segments
		var o0 := Vector3(cos(a0), 0, sin(a0)) * outer
		var o1 := Vector3(cos(a1), 0, sin(a1)) * outer
		var i0 := Vector3(cos(a0), 0, sin(a0)) * inner
		var i1 := Vector3(cos(a1), 0, sin(a1)) * inner
		for v in [o0, o1, i1, o0, i1, i0]:
			st.set_normal(Vector3.UP)
			st.add_vertex(v)
	return st.commit()
