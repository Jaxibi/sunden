class_name HeartPickup
extends Node3D
## Cœur : +25 PV. Attiré vers le héros quand il est proche, mais seulement s'il est blessé
## (sinon il reste au sol : on peut revenir le chercher plus tard).

const HEAL := 25

var hero: Hero
var _model: Node3D
var _t := 0.0


func setup(model: Node3D, the_hero: Hero) -> void:
	hero = the_hero
	_model = model
	add_child(model)
	_t = randf() * TAU
	# petit saut d'apparition
	_model.position.y = 0.6
	var tw := create_tween()
	tw.tween_property(_model, "position:y", 0.25, 0.35).set_trans(Tween.TRANS_BOUNCE).set_ease(Tween.EASE_OUT)


func _process(delta: float) -> void:
	_t += delta
	_model.rotation.y += delta * 2.0
	if _t > 0.4:
		_model.position.y = 0.25 + sin(_t * 3.0) * 0.06
	if not is_instance_valid(hero) or hero.state == Hero.State.DEAD or hero.hp >= hero.max_hp:
		return
	var d := hero.global_position - global_position
	d.y = 0.0
	var dist := d.length()
	if dist < 1.8:
		global_position += d.normalized() * minf(dist, delta * 7.0)
	if dist < 0.6:
		hero.heal(HEAL)
		Sound.play("heart_pickup")
		Juice.burst(global_position + Vector3.UP * 0.4, [Color("e8434f"), Color("ffb3b8"), Color("ffffff")], 8, 2.5, 0.07)
		queue_free()
