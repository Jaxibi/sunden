class_name Breakable
extends StaticBody3D
## Jarre ou caisse : se brise au premier coup et peut libérer un cœur.

signal broken(breakable: Breakable)

var kind := "jarre"
var heart_chance := 0.35
var radius := 0.35


func setup(model: Node3D, what: String) -> void:
	kind = what
	heart_chance = 0.35 if kind == "jarre" else 0.6
	add_child(model)
	var shape := CollisionShape3D.new()
	if kind == "jarre":
		var cyl := CylinderShape3D.new()
		cyl.radius = 0.25
		cyl.height = 0.6
		shape.shape = cyl
		shape.position.y = 0.3
	else:
		var box := BoxShape3D.new()
		box.size = Vector3(0.6, 0.6, 0.6)
		shape.shape = box
		shape.position.y = 0.3
	add_child(shape)
	add_to_group("hittable")


## Même interface que les ennemis (appelée par le héros).
func take_hit(_amount: int, _from_pos: Vector3, _knockback: float) -> bool:
	var colors := [Color("c4703f"), Color("8f4a2a"), Color("e8a070")] if kind == "jarre" \
		else [Color("a0703f"), Color("6e4a2b"), Color("d8b080")]
	Juice.burst(global_position + Vector3.UP * 0.3, colors, 10, 4.0, 0.09)
	Sound.play("pot_break" if kind == "jarre" else "crate_break")
	broken.emit(self)
	queue_free()
	return true
