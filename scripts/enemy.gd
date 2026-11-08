class_name Enemy
extends CharacterBody3D
## Ennemi générique : poursuite, attaque annoncée (télégraphe lisible), recul quand on le frappe.
## Les poses viennent des animations Blender (blender/rig_enemies.py) ; les animations de
## préparation, d'attaque, de recul et d'apparition sont recalées sur les durées ci-dessous.

signal died(enemy: Enemy)

enum Kind { SLIME, SKELETON }
enum State { SPAWN, CHASE, WINDUP, ATTACK, RECOVER, STAGGER, DEAD }

const SPAWN_TIME := 0.45
const STAGGER_TIME := 0.35

@export var kind: Kind = Kind.SLIME
@export var max_hp := 3
@export var move_speed := 2.0
@export var attack_range := 2.2
@export var windup_time := 0.5
@export var attack_time := 0.35
@export var recover_time := 0.7
@export var damage := 10
@export var lunge_speed := 8.0
@export var radius := 0.45
@export var knockback_scale := 1.0
## Animation de déplacement (« saut » pour le slime, « marche » pour le squelette).
@export var move_anim := "saut"
## Cadence des animations (images par seconde). 0 = animation fluide.
@export var anim_fps := 15.0
## Distance à laquelle un ennemi posé dans le décor remarque le héros (INF = toujours).
## Un coup reçu le réveille aussi.
@export var aggro_range := INF
## Échelle du modèle (mini-slimes du boss).
@export var size_scale := 1.0

var target: Hero
## Niveau qui fournit le chemin (next_waypoint) ; sans lui, l'ennemi va tout droit.
var nav: Node
var _provoked := false
var _waypoint := Vector3.ZERO
var _repath_in := 0.0
var hp := 0
var state := State.SPAWN
var state_time := 0.0

var _mats: Array[ShaderMaterial] = []
var _flash := 0.0
var _flash_on := false
var _has_hit := false
var _attack_dir := Vector3.FORWARD
var _animator: SteppedAnimator

@onready var model: Node3D = $Model


func _ready() -> void:
	hp = max_hp
	radius *= size_scale
	add_to_group("enemies")
	add_to_group("hittable")
	_mats = ToonMaterials.apply(model)
	_animator = SteppedAnimator.new(model, anim_fps, ["repos", move_anim])
	_set_state(State.SPAWN)


# --------------------------------------------------------------------------- comportement
func _physics_process(delta: float) -> void:
	state_time += delta
	var hv := Vector3(velocity.x, 0.0, velocity.z)
	var to_target := Vector3.ZERO
	var dist := INF
	var target_ok := is_instance_valid(target) and target.state != Hero.State.DEAD
	if target_ok:
		to_target = target.global_position - global_position
		to_target.y = 0.0
		dist = to_target.length()

	match state:
		State.SPAWN:
			hv = Vector3.ZERO
			if target_ok:
				_face(to_target, delta)
			if state_time >= SPAWN_TIME:
				_set_state(State.CHASE)
		State.CHASE:
			var desired := Vector3.ZERO
			if target_ok and not _provoked and dist <= aggro_range:
				_provoked = true
			if target_ok and _provoked:
				desired = _chase_direction(delta) * move_speed + _separation()
				_face(to_target, delta)
				_animator.play(move_anim)
				if dist <= attack_range:
					_attack_dir = to_target.normalized()
					_set_state(State.WINDUP)
			else:
				_animator.play("repos")
			hv = hv.move_toward(desired, 18.0 * delta)
		State.WINDUP:
			hv = hv.move_toward(Vector3.ZERO, 20.0 * delta)
			# suit le héros, puis verrouille sa direction juste avant de frapper
			if target_ok and state_time < windup_time * 0.7 and dist > 0.01:
				_attack_dir = to_target.normalized()
			_face(_attack_dir, delta)
			if state_time >= windup_time:
				_has_hit = false
				_set_state(State.ATTACK)
		State.ATTACK:
			var k := state_time / attack_time
			if kind == Kind.SLIME:
				hv = _attack_dir * lunge_speed * (1.0 - k)
				if not _has_hit and target_ok and dist <= radius + 0.55:
					_has_hit = true
					target.take_damage(damage, global_position)
			else:
				hv = _attack_dir * 2.5 * (1.0 - k)
				if not _has_hit and k >= 0.35:
					_has_hit = true
					_sfx("attack")
					if target_ok and dist <= attack_range + 0.4 \
							and rad_to_deg(_attack_dir.angle_to(to_target)) < 70.0:
						target.take_damage(damage, global_position)
			if state_time >= attack_time:
				_set_state(State.RECOVER)
		State.RECOVER:
			hv = hv.move_toward(Vector3.ZERO, 12.0 * delta)
			if state_time >= recover_time:
				_set_state(State.CHASE)
		State.STAGGER:
			hv = hv.move_toward(Vector3.ZERO, 14.0 * delta)
			if state_time >= STAGGER_TIME:
				_set_state(State.CHASE)
		State.DEAD:
			hv = Vector3.ZERO

	velocity.x = hv.x
	velocity.z = hv.z
	velocity.y = 0.0 if is_on_floor() else velocity.y - 25.0 * delta
	move_and_slide()


## Direction de poursuite : prochain point du chemin A* (contourne piliers et murs).
func _chase_direction(delta: float) -> Vector3:
	_repath_in -= delta
	if nav == null:
		_waypoint = target.global_position
	elif _repath_in <= 0.0:
		_repath_in = 0.25
		_waypoint = nav.next_waypoint(global_position, target.global_position)
	var d := _waypoint - global_position
	d.y = 0.0
	if d.length() < 0.15:
		_repath_in = 0.0
		d = target.global_position - global_position
		d.y = 0.0
	return d.normalized()


func _separation() -> Vector3:
	var push := Vector3.ZERO
	for e in get_tree().get_nodes_in_group("enemies"):
		if e == self:
			continue
		var d: Vector3 = global_position - e.global_position
		d.y = 0.0
		var l := d.length()
		if l > 0.001 and l < 1.2:
			push += d / l * (1.2 - l) * 2.5
	return push


func _face(dir: Vector3, delta: float) -> void:
	if dir.length() > 0.01:
		model.rotation.y = lerp_angle(model.rotation.y, atan2(-dir.x, -dir.z), 1.0 - exp(-10.0 * delta))


func _set_state(s: State) -> void:
	state = s
	state_time = 0.0
	match s:
		State.SPAWN:
			if _animator.has("apparition"):
				_animator.play("apparition", true, SPAWN_TIME)
				_sfx("spawn")
			else:
				_animator.play("repos", true)
				model.scale = Vector3.ONE * 0.05      # apparition par le code (slime)
		State.CHASE:
			model.scale = Vector3.ONE * size_scale
			_animator.play(move_anim)
		State.WINDUP:
			_animator.play("preparation", true, windup_time)
			_sfx("windup")
		State.ATTACK:
			_animator.play("attaque", true, attack_time)
			if kind == Kind.SLIME:
				_sfx("jump")
		State.RECOVER:
			_animator.play("repos", true)
		State.STAGGER:
			_animator.play("touche", true, STAGGER_TIME)
		State.DEAD:
			if _animator.has("mort"):
				_animator.play("mort", true)


# --------------------------------------------------------------------------- coups reçus
## Renvoie true si le coup a porté.
func take_hit(amount: int, from_pos: Vector3, knockback: float) -> bool:
	if state == State.DEAD or state == State.SPAWN:
		return false
	hp -= amount
	_provoked = true
	_flash = 0.1
	var away := global_position - from_pos
	away.y = 0.0
	away = away.normalized() if away.length() > 0.01 else Vector3.FORWARD
	velocity.x = away.x * knockback * knockback_scale
	velocity.z = away.z * knockback * knockback_scale
	Juice.burst(global_position + Vector3.UP * 0.5, _colors(), 7, 4.5, 0.09)
	if hp <= 0:
		_die()
	else:
		_sfx("hit")
		_set_state(State.STAGGER)
	return true


func _die() -> void:
	remove_from_group("enemies")
	remove_from_group("hittable")
	collision_layer = 0
	collision_mask = 1
	died.emit(self)
	_sfx("death")
	Juice.burst(global_position + Vector3.UP * 0.5, _colors(), 14, 6.0, 0.12)
	var tw := create_tween()
	if _animator.has("mort"):
		# le squelette s'effondre, reste un instant au sol, puis disparaît
		_flash = 0.1
		_set_state(State.DEAD)
		tw.tween_interval(_animator.length("mort") + 0.4)
		tw.tween_property(model, "scale", Vector3(1.2, 0.05, 1.2) * size_scale, 0.1)
	else:
		# le slime éclate
		_flash = 10.0
		_set_state(State.DEAD)
		tw.tween_property(model, "scale", Vector3(1.4, 0.1, 1.4) * size_scale, 0.12)
	tw.tween_callback(queue_free)


## Son propre à l'ennemi : slime_hit, skeleton_windup...
func _sfx(event: String) -> void:
	Sound.play(("slime_" if kind == Kind.SLIME else "skeleton_") + event)


func _colors() -> Array:
	if kind == Kind.SLIME:
		return [Color("7fd35a"), Color("b6f08c"), Color("ffffff")]
	return [Color("e6dfc8"), Color("c9c1a8"), Color("ffffff")]


# --------------------------------------------------------------------------- visuel
func _process(delta: float) -> void:
	_animator.update(delta)

	var on := _flash > 0.0
	_flash -= delta
	if on != _flash_on:
		_flash_on = on
		for m in _mats:
			m.set_shader_parameter("flash_color", Color(1, 1, 1, 1.0 if on else 0.0))

	if state == State.SPAWN and not _animator.has("apparition"):
		var s := clampf(state_time / 0.4, 0.05, 1.0)
		model.scale = Vector3.ONE * (s + sin(s * PI) * 0.25) * size_scale
