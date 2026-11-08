class_name Brazier
extends StaticBody3D
## Brasero : l'allumer (en s'approchant) soigne complètement et devient le point de retour.

signal lit(brazier: Brazier)

var is_lit := false
var respawn_point := Vector3.ZERO
var hero: Hero
var _flames: Array[Node3D] = []
var _light := OmniLight3D.new()
var _t := 0.0


func setup(model: Node3D, the_hero: Hero, respawn: Vector3) -> void:
	hero = the_hero
	respawn_point = respawn
	add_child(model)
	for n in model.find_children("*", "", true, false):
		if n.name.ends_with("_Flamme") or n.name.ends_with("_Coeur"):
			_flames.append(n)
			n.visible = false
	var shape := CollisionShape3D.new()
	var cyl := CylinderShape3D.new()
	cyl.radius = 0.4
	cyl.height = 0.8
	shape.shape = cyl
	shape.position.y = 0.4
	add_child(shape)
	_light.light_color = Color(1.0, 0.6, 0.28)
	_light.omni_range = 4.5
	_light.position.y = 1.1
	_light.visible = false
	add_child(_light)


func _process(delta: float) -> void:
	_t += delta
	if is_lit:
		_light.light_energy = 2.6 + 0.3 * sin(_t * 9.0) + 0.2 * sin(_t * 21.0)
	elif is_instance_valid(hero) and hero.state != Hero.State.DEAD \
			and hero.global_position.distance_to(global_position) < 1.5:
		light()


func light() -> void:
	is_lit = true
	for f in _flames:
		f.visible = true
	_light.visible = true
	Sound.play("brazier_light")
	Juice.burst(global_position + Vector3.UP * 0.9, [Color("ff8a2a"), Color("fff27a")], 12, 3.0, 0.08)
	hero.heal(hero.max_hp)
	lit.emit(self)
