class_name BossSlime
extends CharacterBody3D
## Le Roi Gluant (voir LEVEL_DESIGN.md §6).
## P1 : bonds + écrasement télégraphié, puis étourdi (fenêtre de punition).
## P2 : l'écrasement libère une onde de choc (à traverser en roulade) et des mini-slimes.
## P3 : trois écrasements enchaînés, puis long étourdissement.
## Hors étourdissement, ses PV ne baissent que de moitié : lire, esquiver, puis punir.

signal health_changed(ratio: float)
signal phase_changed(phase: int)
signal defeated(boss: BossSlime)

enum State { DORMANT, INTRO, IDLE, HOP, PREP, AIR, LANDED, DAZED, ROAR, DEAD }

const MAX_HP := 36.0
const PHASE_HP := [24.0, 12.0]
const MODEL_SCALE := 2.4
const TINT := Color("b36ae0")
const SLAM_RADIUS := 2.0
const SLAM_DAMAGE := 20
const HOP_DAMAGE := 10
const MAX_MINIONS := 4
const LEASH := 7.5                       # distance max à son point de départ (reste dans l'arène)

var display_name := "Le Roi Gluant"
var target: Hero
var crown: Node3D
var minion_spawner: Callable
var hp := MAX_HP
var phase := 1
var state := State.DORMANT
var state_time := 0.0
var radius := 1.1

var _home := Vector3.ZERO
var _jump_from := Vector3.ZERO
var _jump_to := Vector3.ZERO
var _jump_time := 0.5
var _jump_height := 1.0
var _hops_left := 2
var _slams_left := 0
var _minions: Array = []
var _mats: Array[ShaderMaterial] = []
var _animator: SteppedAnimator
var _flash := 0.0
var _flash_on := false
var _telegraph := MeshInstance3D.new()
var _tele_mat := StandardMaterial3D.new()
var _stars := Node3D.new()

@onready var model: Node3D = $Model


func _ready() -> void:
	_home = global_position
	add_to_group("hittable")
	add_to_group("enemies")
	model.scale = Vector3.ONE * MODEL_SCALE
	_mats = ToonMaterials.apply(model)
	for m in _mats:
		var c: Color = m.get_shader_parameter("albedo")
		if c.g > c.r and c.g > c.b:                        # le corps (pas les yeux) : violet royal
			m.set_shader_parameter("albedo", TINT)
	_attach_crown()
	_animator = SteppedAnimator.new(model, 15.0, ["repos", "saut"])
	_build_telegraph()
	_build_stars()
	_set_state(State.DORMANT)


func _attach_crown() -> void:
	if crown == null:
		return
	var skels := model.find_children("*", "Skeleton3D", true, false)
	if skels.is_empty():
		model.add_child(crown)
		crown.position.y = 0.66
		return
	var att := BoneAttachment3D.new()
	att.bone_name = "haut"
	skels[0].add_child(att)
	att.add_child(crown)
	crown.position = Vector3(0.0, 0.3, 0.0)
	crown.scale = Vector3.ONE * 0.55


func _build_telegraph() -> void:
	var disc := CylinderMesh.new()
	disc.top_radius = 1.0
	disc.bottom_radius = 1.0
	disc.height = 0.02
	disc.radial_segments = 32
	_tele_mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	_tele_mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	_tele_mat.depth_draw_mode = BaseMaterial3D.DEPTH_DRAW_DISABLED
	_tele_mat.render_priority = 1
	_tele_mat.albedo_color = Color(0.9, 0.15, 0.25, 0.4)
	_telegraph.mesh = disc
	_telegraph.material_override = _tele_mat
	_telegraph.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_telegraph.top_level = true
	_telegraph.visible = false
	add_child(_telegraph)


func _build_stars() -> void:
	var mat := StandardMaterial3D.new()
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.albedo_color = Color("fff27a")
	for i in 4:
		var s := MeshInstance3D.new()
		var b := BoxMesh.new()
		b.size = Vector3(0.14, 0.14, 0.14)
		b.material = mat
		s.mesh = b
		s.position = Vector3(cos(i * TAU / 4) * 0.8, 0.0, sin(i * TAU / 4) * 0.8)
		s.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		_stars.add_child(s)
	_stars.position.y = 2.2
	_stars.visible = false
	add_child(_stars)


# =========================================================================== combat
func awaken() -> void:
	_set_state(State.INTRO)
	Sound.play("boss_roar")
	Juice.shake(5.0)


func reset_fight() -> void:
	_pop_minions()
	hp = MAX_HP
	phase = 1
	_hops_left = 2
	_slams_left = 0
	global_position = _home
	model.position = Vector3.ZERO
	model.scale = Vector3.ONE * MODEL_SCALE
	_telegraph.visible = false
	_set_collision(true)
	_set_state(State.DORMANT)
	health_changed.emit(1.0)


func _physics_process(delta: float) -> void:
	state_time += delta
	var to := Vector3.ZERO
	var dist := INF
	var ok := is_instance_valid(target) and target.state != Hero.State.DEAD
	if ok:
		to = target.global_position - global_position
		to.y = 0.0
		dist = to.length()

	match state:
		State.INTRO, State.ROAR:
			if state_time >= 1.4:
				_set_state(State.IDLE)
		State.IDLE:
			_face(to, delta)
			if ok and state_time >= (0.3 if phase == 3 else 0.55):
				_next_attack()
		State.HOP:
			_update_jump()
			if state_time >= _jump_time:
				_land_hop(dist)
		State.PREP:
			_face(to, delta)
			if state_time >= 0.35:
				_launch_slam()
		State.AIR:
			_update_jump()
			var pulse := 0.3 + 0.25 * absf(sin(state_time * 14.0))
			_tele_mat.albedo_color.a = pulse
			if state_time >= _jump_time:
				_land_slam()
		State.LANDED:
			if state_time >= 0.3:
				if _slams_left > 0:
					_start_slam()
				else:
					_set_state(State.DAZED)
		State.DAZED:
			if state_time >= (2.2 if phase == 3 else 1.4):
				_set_state(State.IDLE)


func _next_attack() -> void:
	if phase == 3:
		_slams_left = 3
		_start_slam()
	elif _hops_left > 0:
		_hops_left -= 1
		_start_hop()
	else:
		_hops_left = 2
		_slams_left = 1
		_start_slam()


func _start_hop() -> void:
	var to := target.global_position - global_position
	to.y = 0.0
	var step := clampf(to.length() - 1.2, 0.0, 2.6)
	_jump(_clamp_to_arena(global_position + to.normalized() * step), 0.55, 0.9)
	_set_state(State.HOP)
	Sound.play("slime_jump", 3.0, 0.6)


func _land_hop(dist: float) -> void:
	model.position.y = 0.0
	Juice.shake(1.5)
	Sound.play("boss_slam", -10.0)
	if dist <= radius + 0.7:
		target.take_damage(HOP_DAMAGE, global_position)
	_set_state(State.IDLE)


func _start_slam() -> void:
	_slams_left -= 1
	_set_state(State.PREP)
	Sound.play("slime_windup", 2.0, 0.6)


func _launch_slam() -> void:
	var t := 0.6 if phase == 3 else 0.9
	var aim := _clamp_to_arena(target.global_position)
	_telegraph.global_position = Vector3(aim.x, 0.04, aim.z)
	_telegraph.scale = Vector3(SLAM_RADIUS, 1.0, SLAM_RADIUS)
	_telegraph.visible = true
	_jump(aim, t, 4.0)
	_set_collision(false)
	_set_state(State.AIR)
	Sound.play("slime_jump", 4.0, 0.5)


func _land_slam() -> void:
	global_position = _jump_to
	model.position.y = 0.0
	_telegraph.visible = false
	_set_collision(true)
	Juice.shake(5.0)
	Juice.hitstop(0.06)
	Sound.play("boss_slam")
	Juice.burst(global_position + Vector3.UP * 0.3, [TINT, Color("e0b8ff"), Color("ffffff")], 18, 6.0, 0.14)
	if is_instance_valid(target):
		var d := target.global_position - global_position
		d.y = 0.0
		if d.length() <= SLAM_RADIUS:
			target.take_damage(SLAM_DAMAGE, global_position)
	if phase >= 2:
		var wave := Shockwave.new()
		get_parent().add_child(wave)
		wave.global_position = global_position
		wave.setup(target)
	if phase == 2:
		_spawn_minions()
	_set_state(State.LANDED)


func _spawn_minions() -> void:
	_minions = _minions.filter(func(m): return is_instance_valid(m) and m.state != Enemy.State.DEAD)
	if not minion_spawner.is_valid():
		return
	for i in 2:
		if _minions.size() >= MAX_MINIONS:
			return
		var ang := randf() * TAU
		var p := _clamp_to_arena(global_position + Vector3(cos(ang), 0, sin(ang)) * 2.2)
		_minions.append(minion_spawner.call(p))


func _pop_minions() -> void:
	for m in _minions:
		if is_instance_valid(m) and m.state != Enemy.State.DEAD:
			m.take_hit(99, global_position, 4.0)
	_minions.clear()


func _jump(to: Vector3, duration: float, height: float) -> void:
	_jump_from = global_position
	_jump_to = Vector3(to.x, _jump_from.y, to.z)
	_jump_time = duration
	_jump_height = height


func _update_jump() -> void:
	var k := clampf(state_time / _jump_time, 0.0, 1.0)
	global_position = _jump_from.lerp(_jump_to, k)
	model.position.y = sin(PI * k) * _jump_height


func _clamp_to_arena(p: Vector3) -> Vector3:
	var off := p - _home
	off.y = 0.0
	if off.length() > LEASH:
		off = off.normalized() * LEASH
	return _home + off


func _set_collision(on: bool) -> void:
	collision_layer = 4 if on else 0


func _face(dir: Vector3, delta: float) -> void:
	if dir.length() > 0.01:
		model.rotation.y = lerp_angle(model.rotation.y, atan2(-dir.x, -dir.z), 1.0 - exp(-6.0 * delta))


# =========================================================================== coups reçus
## Appelé par le héros (groupe « hittable »). Étourdi : dégâts pleins ; sinon moitié.
func take_hit(amount: int, _from_pos: Vector3, _knockback: float) -> bool:
	if state in [State.DORMANT, State.INTRO, State.ROAR, State.DEAD, State.AIR]:
		return false
	hp = maxf(hp - float(amount) * (1.0 if state == State.DAZED else 0.5), 0.0)
	_flash = 0.1
	health_changed.emit(hp / MAX_HP)
	Juice.burst(global_position + Vector3.UP * 1.2, [TINT, Color("e0b8ff"), Color("ffffff")], 8, 4.5, 0.1)
	Sound.play("slime_hit", 2.0, 0.7)
	if hp <= 0.0:
		_die()
		return true
	var new_phase := 1 if hp > PHASE_HP[0] else (2 if hp > PHASE_HP[1] else 3)
	if new_phase != phase:
		phase = new_phase
		_roar()
		phase_changed.emit(phase)
	return true


func _roar() -> void:
	_pop_minions()
	_telegraph.visible = false
	model.position.y = 0.0
	_set_collision(true)
	_hops_left = 2
	_set_state(State.ROAR)
	Sound.play("boss_roar")
	Juice.shake(6.0)
	Juice.hitstop(0.1)


func _die() -> void:
	_pop_minions()
	_telegraph.visible = false
	_set_collision(false)
	_set_state(State.DEAD)
	Sound.play("boss_slam")
	Juice.shake(8.0)
	Juice.hitstop(0.2)
	for i in 3:
		Juice.burst(global_position + Vector3.UP * (0.6 + i * 0.6), [TINT, Color("e0b8ff"), Color("fff27a")], 20, 7.0, 0.16)
	if crown:                                   # la couronne roule à terre
		var keep := crown.global_transform
		crown.get_parent().remove_child(crown)
		get_parent().add_child(crown)
		crown.global_transform = keep
		var land := global_position + Vector3(1.2, 0.0, 1.2)
		var tw := crown.create_tween()
		tw.tween_property(crown, "global_position", keep.origin + Vector3(0.6, 1.5, 0.6), 0.35)
		tw.tween_property(crown, "global_position", land, 0.4).set_trans(Tween.TRANS_BOUNCE).set_ease(Tween.EASE_OUT)
	var tw2 := create_tween()
	tw2.tween_property(model, "scale", Vector3(MODEL_SCALE * 1.5, 0.15, MODEL_SCALE * 1.5), 0.5)
	tw2.tween_callback(func(): model.visible = false)
	tw2.tween_interval(0.4)
	tw2.tween_callback(func(): defeated.emit(self))


# =========================================================================== visuel
func _set_state(s: State) -> void:
	state = s
	state_time = 0.0
	_stars.visible = s == State.DAZED
	match s:
		State.DORMANT, State.IDLE, State.DAZED:
			_animator.play("repos")
		State.INTRO, State.ROAR:
			_animator.play("preparation", true, 1.2)
		State.HOP:
			_animator.play("attaque", true, _jump_time)
		State.PREP:
			_animator.play("preparation", true, 0.35)
		State.AIR:
			_animator.play("attaque", true, _jump_time)
		State.LANDED:
			_animator.play("touche", true, 0.3)


func _process(delta: float) -> void:
	_animator.update(delta)
	_stars.rotation.y += delta * 4.0
	var on := _flash > 0.0
	_flash -= delta
	if on != _flash_on:
		_flash_on = on
		for m in _mats:
			m.set_shader_parameter("flash_color", Color(1, 1, 1, 1.0 if on else 0.0))
