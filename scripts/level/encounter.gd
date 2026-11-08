class_name Encounter
extends Node
## Rencontre en salle fermée : le héros entre → herses fermées → vagues → herses rouvertes.
## Configuration (niveau1.json) : rect déclencheur, herses, vagues {"slime": n, "skeleton": n}.

signal started(encounter: Encounter)
signal cleared(encounter: Encounter)

enum Phase { IDLE, ACTIVE, CLEARED }

const WAVE_DELAY := 1.2         # répit entre deux vagues
const SPAWN_STAGGER := 0.35     # apparitions échelonnées : on lit chaque arrivée

var config: Dictionary
var level: LevelBuilder
var phase := Phase.IDLE
var wave := -1
var _alive: Array = []
var _pending := 0
var _next_wave_in := -1.0
var _generation := 0


func setup(cfg: Dictionary, lvl: LevelBuilder) -> void:
	config = cfg
	level = lvl
	name = "Rencontre_" + String(cfg.get("id", "?"))


func display_name() -> String:
	return String(config.get("name", ""))


func _process(delta: float) -> void:
	match phase:
		Phase.IDLE:
			if level.hero_alive() and level.hero_in_rect(config["rect"]):
				_start()
		Phase.ACTIVE:
			_alive = _alive.filter(func(e): return is_instance_valid(e) and e.state != Enemy.State.DEAD)
			if _pending > 0 or not _alive.is_empty():
				return
			if wave + 1 < config["waves"].size():
				if _next_wave_in < 0.0:
					_next_wave_in = WAVE_DELAY
				_next_wave_in -= delta
				if _next_wave_in <= 0.0:
					_spawn_wave(wave + 1)
			else:
				_clear()


func _start() -> void:
	phase = Phase.ACTIVE
	level.set_gates(config["gates"], false)
	started.emit(self)
	_spawn_wave(0)


func _spawn_wave(index: int) -> void:
	wave = index
	_next_wave_in = -1.0
	var kinds: Array[String] = []
	var spec: Dictionary = config["waves"][index]
	for kind in spec:
		for i in int(spec[kind]):
			kinds.append(kind)
	kinds.shuffle()
	# points d'apparition les plus éloignés du héros d'abord : pas d'apparition sous ses pieds
	var points: Array = level.spawn_points.get(String(config["marker"]), []).duplicate()
	var hero_pos := level.hero.global_position
	points.sort_custom(func(a, b): return a.distance_to(hero_pos) > b.distance_to(hero_pos))
	_pending = kinds.size()
	for i in kinds.size():
		var pos: Vector3 = points[i % points.size()]
		_spawn_later(kinds[i], pos, i * SPAWN_STAGGER, _generation)


func _spawn_later(kind: String, pos: Vector3, delay: float, generation: int) -> void:
	if delay > 0.0:
		await get_tree().create_timer(delay, false).timeout
	if phase != Phase.ACTIVE or generation != _generation:      # rencontre réinitialisée entre-temps
		return
	_alive.append(level.spawn_enemy(kind, pos, INF))
	_pending -= 1


func _clear() -> void:
	phase = Phase.CLEARED
	level.set_gates(config["gates"], true)
	level.set_gates(config.get("open_on_clear", []), true)
	cleared.emit(self)


## Le héros est tombé pendant la rencontre : on efface les monstres et on rouvre la salle.
func reset() -> void:
	if phase != Phase.ACTIVE:
		return
	for e in _alive:
		if is_instance_valid(e):
			e.queue_free()
	_alive.clear()
	_pending = 0
	_generation += 1
	wave = -1
	phase = Phase.IDLE
	level.set_gates(config["gates"], true)
