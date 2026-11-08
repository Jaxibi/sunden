class_name Chest
extends StaticBody3D
## Coffre : s'ouvre quand on s'en approche et donne sa récompense.

signal opened(chest: Chest)

var reward := ""
var is_open := false
var hero: Hero
var _lid: Node3D


func setup(model: Node3D, what: String, the_hero: Hero) -> void:
	reward = what
	hero = the_hero
	add_child(model)
	_lid = model.find_child("*Couvercle", true, false)
	var shape := CollisionShape3D.new()
	var box := BoxShape3D.new()
	box.size = Vector3(0.8, 0.6, 0.5)
	shape.shape = box
	shape.position.y = 0.3
	add_child(shape)


func _process(_delta: float) -> void:
	if not is_open and is_instance_valid(hero) and hero.state != Hero.State.DEAD \
			and hero.global_position.distance_to(global_position) < 1.2:
		open()


func open() -> void:
	is_open = true
	if _lid:
		var tw := create_tween()
		tw.tween_property(_lid, "rotation:x", 1.9, 0.45).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	Sound.play("chest_open")
	Juice.burst(global_position + Vector3.UP * 0.6, [Color("e8b83a"), Color("fff27a"), Color("ffffff")], 18, 3.5, 0.08)
	opened.emit(self)
