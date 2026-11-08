extends Node
## Scène principale : rendu basse résolution agrandi en entier, vagues d'ennemis, contrôles.
##
## Options de lancement (après `--`) :
##   --screenshot=chemin.png   capture une image pendant un coup d'épée puis quitte
##   --selftest                attaque en boucle 14 s, affiche le bilan puis quitte

const NATIVE := Vector2i(320, 180)
const MARGIN := 1                      # pixels en plus autour de l'image pour le décalage sous-pixel
const ARENA_LIMIT := 11.0
const SLIME := preload("res://scenes/slime.tscn")
const SKELETON := preload("res://scenes/skeleton.tscn")

@onready var display: SubViewportContainer = $Display
@onready var game: SubViewport = $Display/Game
@onready var camera: PixelCamera = $Display/Game/Camera
@onready var hero: Hero = $Display/Game/Hero
@onready var enemies: Node3D = $Display/Game/Enemies
@onready var hud: Hud = $HUD

var pixel_scale := 4
var wave := 0
var kills := 0

var _base_pos := Vector2.ZERO
var _next_wave_in := 1.0
var _shot_path := ""
var _selftest := false
var _start_msec := 0


func _ready() -> void:
	_setup_input()
	RenderingServer.set_default_clear_color(Color.BLACK)
	Juice.fx_root = game
	get_tree().root.size_changed.connect(_layout)
	_layout()
	hero.health_changed.connect(hud.set_health)
	hero.died.connect(_on_hero_died)
	hud.set_health(hero.hp, hero.max_hp)
	hud.set_wave(wave, kills)
	Sound.play_music("combat_theme")
	Sound.play_ambience("forest_ambience")
	_start_msec = Time.get_ticks_msec()
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--screenshot="):
			_shot_path = arg.get_slice("=", 1)
			_run_screenshot()
		elif arg == "--selftest":
			_selftest = true
			_run_selftest()


func _process(delta: float) -> void:
	display.position = _base_pos + camera.subpixel * pixel_scale
	if hero.state != Hero.State.DEAD and get_tree().get_nodes_in_group("enemies").is_empty():
		_next_wave_in -= delta
		if _next_wave_in <= 0.0:
			_spawn_wave()
			_next_wave_in = 2.0
	if hero.state == Hero.State.DEAD and Input.is_action_just_pressed("restart"):
		Engine.time_scale = 1.0
		get_tree().reload_current_scene()


## Facteur d'agrandissement entier le plus grand qui tient dans la fenêtre.
func _layout() -> void:
	var win := Vector2(get_tree().root.size)
	pixel_scale = maxi(1, int(minf(win.x / NATIVE.x, win.y / NATIVE.y)))
	display.stretch_shrink = pixel_scale
	display.size = Vector2(NATIVE + Vector2i(MARGIN, MARGIN) * 2) * pixel_scale
	var origin := ((win - Vector2(NATIVE) * pixel_scale) * 0.5).floor()
	_base_pos = origin - Vector2(MARGIN, MARGIN) * pixel_scale
	hud.set_pixel_scale(pixel_scale, origin)


# --------------------------------------------------------------------------- vagues
func _spawn_wave() -> void:
	wave += 1
	for i in 2 + wave:
		_spawn(SLIME, _random_spawn_point())
	for i in wave / 2:
		_spawn(SKELETON, _random_spawn_point())
	hud.announce("Vague %d" % wave)
	hud.set_wave(wave, kills)
	Sound.play("wave_start")


func _random_spawn_point() -> Vector3:
	var ang := randf() * TAU
	var r := randf_range(5.5, 8.0)
	var p := hero.global_position + Vector3(cos(ang) * r, 0.0, sin(ang) * r)
	return Vector3(clampf(p.x, -ARENA_LIMIT, ARENA_LIMIT), 0.0, clampf(p.z, -ARENA_LIMIT, ARENA_LIMIT))


func _spawn(scene: PackedScene, pos: Vector3) -> Enemy:
	var e: Enemy = scene.instantiate()
	e.position = pos
	e.target = hero
	e.died.connect(_on_enemy_died)
	enemies.add_child(e)
	return e


func _on_enemy_died(_e: Enemy) -> void:
	kills += 1
	hud.set_wave(wave, kills)


func _on_hero_died() -> void:
	hud.announce("Tu es tombe  -  R pour recommencer", 0.0)
	Sound.stop_music(1.2)
	Sound.play("hero_death")


# --------------------------------------------------------------------------- contrôles
func _setup_input() -> void:
	# touches physiques : ZQSD sur AZERTY et WASD sur QWERTY tombent au même endroit
	var keys := {
		"move_left": [KEY_A, KEY_LEFT], "move_right": [KEY_D, KEY_RIGHT],
		"move_up": [KEY_W, KEY_UP], "move_down": [KEY_S, KEY_DOWN],
		"attack": [KEY_J], "dodge": [KEY_SPACE, KEY_K], "restart": [KEY_R],
	}
	for action in keys:
		if InputMap.has_action(action):
			continue
		InputMap.add_action(action, 0.2)
		for k in keys[action]:
			var ev := InputEventKey.new()
			ev.physical_keycode = k
			InputMap.action_add_event(action, ev)
	_add_axis("move_left", JOY_AXIS_LEFT_X, -1.0)
	_add_axis("move_right", JOY_AXIS_LEFT_X, 1.0)
	_add_axis("move_up", JOY_AXIS_LEFT_Y, -1.0)
	_add_axis("move_down", JOY_AXIS_LEFT_Y, 1.0)
	_add_button("attack", JOY_BUTTON_X)
	_add_button("dodge", JOY_BUTTON_A)
	_add_button("restart", JOY_BUTTON_START)
	var click := InputEventMouseButton.new()
	click.button_index = MOUSE_BUTTON_LEFT
	InputMap.action_add_event("attack", click)
	var right_click := InputEventMouseButton.new()
	right_click.button_index = MOUSE_BUTTON_RIGHT
	InputMap.action_add_event("dodge", right_click)


func _add_axis(action: String, axis: JoyAxis, value: float) -> void:
	var ev := InputEventJoypadMotion.new()
	ev.axis = axis
	ev.axis_value = value
	InputMap.action_add_event(action, ev)


func _add_button(action: String, button: JoyButton) -> void:
	var ev := InputEventJoypadButton.new()
	ev.button_index = button
	InputMap.action_add_event(action, ev)


# --------------------------------------------------------------------------- outils de test
func _wait_real(seconds: float) -> void:
	await get_tree().create_timer(seconds, true, false, true).timeout


func _press(action: String) -> void:
	Input.action_press(action)
	await _wait_real(0.05)
	Input.action_release(action)


func _run_screenshot() -> void:
	_next_wave_in = INF
	wave = 1
	var f := hero.facing
	var side := Vector3(-f.z, 0.0, f.x)
	_spawn(SLIME, hero.global_position + f * 1.5 + side * 0.3)
	_spawn(SLIME, hero.global_position + f * 3.0 - side * 1.6)
	_spawn(SKELETON, hero.global_position - f * 2.2 + side * 2.2)
	_spawn(SKELETON, hero.global_position + f * 3.2 + side * 2.5)
	hud.set_wave(wave, kills)
	# enregistre aussi ce que joue le bus Master (contrôle du sound design)
	var rec := AudioEffectRecord.new()
	AudioServer.add_bus_effect(0, rec)
	rec.set_recording_active(true)
	await _wait_real(0.9)
	# Série d'images pendant le combo : chemin.png, chemin_1.png, chemin_2.png...
	for i in 16:
		if i == 0 or i == 4 or i == 7:
			_press("attack")
		await _wait_real(0.07 if i < 10 else 0.2)
		await RenderingServer.frame_post_draw
		var path := _shot_path if i == 0 else _shot_path.get_basename() + "_%d.png" % i
		get_viewport().get_texture().get_image().save_png(path)
	await _wait_real(2.0)
	rec.set_recording_active(false)
	var audio := rec.get_recording()
	if audio:
		audio.save_to_wav(_shot_path.get_basename() + "_audio.wav")
	audio = null
	AudioServer.remove_bus_effect(0, AudioServer.get_bus_effect_count(0) - 1)
	print("SCREENSHOT ", _shot_path)
	Sound.quit_cleanly()


func _run_selftest() -> void:
	for scene in [load("res://scenes/hero.tscn"), SLIME, SKELETON]:
		var inst: Node = scene.instantiate()
		var player := inst.find_child("AnimationPlayer", true, false) as AnimationPlayer
		print("SELFTEST %s animations=%s" % [inst.name, player.get_animation_list() if player else "AUCUNE"])
		inst.free()
	var end := Time.get_ticks_msec() + 14000
	while Time.get_ticks_msec() < end and hero.state != Hero.State.DEAD:
		await _press("attack")
		await _wait_real(0.25)
	print("SELFTEST wave=%d kills=%d hero_hp=%d enemies_alive=%d" % [
		wave, kills, hero.hp, get_tree().get_nodes_in_group("enemies").size()])
	Sound.quit_cleanly()
