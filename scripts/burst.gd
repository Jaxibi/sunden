class_name Burst
extends Node3D
## Éclats carrés projetés puis retombant : impacts, morts, poussière d'esquive.

var _parts: Array = []   # [MeshInstance3D, Vector3 vitesse]
var _life := 0.4


static func spawn(parent: Node, pos: Vector3, colors: Array, count := 8, speed := 4.0, size := 0.09) -> void:
	var b := Burst.new()
	parent.add_child(b)
	b.global_position = pos
	for i in count:
		var mat := StandardMaterial3D.new()
		mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		mat.depth_draw_mode = BaseMaterial3D.DEPTH_DRAW_DISABLED
		mat.render_priority = 2
		mat.albedo_color = colors.pick_random()
		var mesh := BoxMesh.new()
		var s := size * randf_range(0.7, 1.3)
		mesh.size = Vector3(s, s, s)
		mesh.material = mat
		var mi := MeshInstance3D.new()
		mi.mesh = mesh
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		b.add_child(mi)
		var dir := Vector3(randf_range(-1.0, 1.0), randf_range(0.3, 1.4), randf_range(-1.0, 1.0)).normalized()
		b._parts.append([mi, dir * speed * randf_range(0.6, 1.2)])


func _process(delta: float) -> void:
	_life -= delta
	for p in _parts:
		p[1].y -= 16.0 * delta
		p[0].position += p[1] * delta
	if _life <= 0.0:
		queue_free()
