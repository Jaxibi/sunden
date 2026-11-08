class_name SpikeTrap
extends Node3D
## Piège à piques : repos, alerte (les pointes tremblent), sortie (blesse), retrait.
## Blesse le héros (sauf pendant la roulade) et les monstres : on peut les y attirer.

const REST := 1.6
const WARN := 0.5
const UP := 0.4
const DOWN := 0.2
const CYCLE := REST + WARN + UP + DOWN
const HIDDEN_Y := -0.36
const HERO_DAMAGE := 15
const ENEMY_DAMAGE := 1

var offset := 0.0
var hero: Hero
var _spikes: Node3D
var _t := 0.0
var _was_up := false
var _hit: Array = []


func setup(model: Node3D, phase_offset: float, the_hero: Hero) -> void:
	add_child(model)
	_spikes = model.find_child("*Pointes", true, false)
	offset = phase_offset
	hero = the_hero


func _process(delta: float) -> void:
	_t = fposmod(_t + delta, CYCLE)
	var t := fposmod(_t + offset, CYCLE)
	var up := false
	if t < REST:
		_spikes.position.y = HIDDEN_Y
	elif t < REST + WARN:
		_spikes.position.y = -0.27 + 0.02 * sin(t * 70.0)          # pointes visibles qui tremblent
	elif t < REST + WARN + UP:
		_spikes.position.y = 0.0
		up = true
	else:
		_spikes.position.y = lerpf(0.0, HIDDEN_Y, (t - REST - WARN - UP) / DOWN)
	if up and not _was_up:
		_hit.clear()
		_play_sound()
	_was_up = up
	if up:
		_damage()


func _inside(p: Vector3) -> bool:
	return absf(p.x - global_position.x) < 0.55 and absf(p.z - global_position.z) < 0.55


func _damage() -> void:
	if is_instance_valid(hero) and not _hit.has(hero) and _inside(hero.global_position):
		_hit.append(hero)
		hero.take_damage(HERO_DAMAGE, global_position)
	for e in get_tree().get_nodes_in_group("enemies"):
		if e is Enemy and not _hit.has(e) and _inside(e.global_position):
			_hit.append(e)
			e.take_hit(ENEMY_DAMAGE, global_position, 3.0)


func _play_sound() -> void:
	if not is_instance_valid(hero):
		return
	var d := hero.global_position.distance_to(global_position)
	if d < 8.0:
		Sound.play("spike_trap", -d * 0.8)
