extends Node
## Scène principale : rendu basse résolution agrandi en entier, déroulement du niveau, contrôles.
##
## Options de lancement (après `--`) :
##   --screenshot=chemin.png   visite du niveau en captures (chemin_1.png, chemin_2.png...) puis quitte
##   --selftest                parcours automatique (objets, 1re salle, boss) avec bilan, puis quitte

## Zoom : la densité (pixels par mètre) ne change jamais ; zoomer change le facteur d'agrandissement
## entier, donc la taille de l'image native et la portion du monde visible.
## Hauteur native entre 180 (le plus proche) et 360 (le plus éloigné) ; la largeur suit l'écran.
## Exemple en 5120x1440 (32:9) : x8 = 640x180, x6 = 854x240 (par défaut), x4 = 1280x360.
const NEAREST_NATIVE_H := 180
const FARTHEST_NATIVE_H := 360
const DEFAULT_NATIVE_H := 240.0
const MAX_ASPECT := 4.0                # au-delà de 4:1, bandes noires sur les côtés
const MARGIN := 1                      # pixels en plus autour de l'image pour le décalage sous-pixel
const RESPAWN_DELAY := 3.0

@onready var display: SubViewportContainer = $Display
@onready var game: SubViewport = $Display/Game
@onready var camera: PixelCamera = $Display/Game/Camera
@onready var hero: Hero = $Display/Game/Hero
@onready var enemies: Node3D = $Display/Game/Enemies
@onready var level: LevelBuilder = $Display/Game/Level
@onready var hud: Hud = $HUD

var pixel_scale := 4
var native := Vector2i(320, 180)
## Hauteur native souhaitée (garde le même zoom quand la fenêtre change de taille).
var zoom_height := DEFAULT_NATIVE_H
var checkpoint := Vector3.ZERO

var _base_pos := Vector2.ZERO
var _respawn_in := -1.0
var _finished := false
var _shot_path := ""


func _ready() -> void:
	_setup_input()
	RenderingServer.set_default_clear_color(Color.BLACK)
	Juice.fx_root = game
	get_tree().root.size_changed.connect(_layout)
	_layout()

	level.setup(hero, enemies)
	hero.global_position = level.start_position
	checkpoint = level.start_position
	camera.snap()

	hero.health_changed.connect(hud.set_health)
	hero.armor_changed.connect(func(set_name: String): hud.announce(set_name, 1.4))
	hero.died.connect(_on_hero_died)
	hud.set_health(hero.hp, hero.max_hp)
	level.zone_changed.connect(func(zone): hud.set_zone(String(zone["name"])))
	level.hint_requested.connect(func(text): hud.hint(text))
	level.encounter_started.connect(_on_encounter_started)
	level.encounter_cleared.connect(_on_encounter_cleared)
	level.checkpoint_reached.connect(_on_checkpoint)
	level.boss_started.connect(_on_boss_started)
	level.boss_defeated.connect(_on_boss_defeated)
	level.chest_opened.connect(_on_chest_opened)
	Sound.play_ambience("forest_ambience")

	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--zoom-height="):          # tests : hauteur native voulue (180 à 360)
			zoom_height = float(arg.get_slice("=", 1))
			_layout()
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--screenshot="):
			_shot_path = arg.get_slice("=", 1)
			_run_tour()
		elif arg == "--selftest":
			_run_selftest()


func _process(delta: float) -> void:
	display.position = _base_pos + camera.subpixel * pixel_scale
	if Input.is_action_just_pressed("toggle_fullscreen"):
		_toggle_fullscreen()
	if Input.is_action_just_pressed("equip_cycle"):
		hero.cycle_armor_set()
	elif Input.is_action_just_pressed("equip_1"):
		hero.set_armor_set(Hero.ArmorSet.TISSU)
	elif Input.is_action_just_pressed("equip_2"):
		hero.set_armor_set(Hero.ArmorSet.CUIR)
	elif Input.is_action_just_pressed("equip_3"):
		hero.set_armor_set(Hero.ArmorSet.PLATES)
	if hero.state == Hero.State.DEAD:
		_respawn_in -= delta
		if _respawn_in <= 0.0 or (_respawn_in < RESPAWN_DELAY - 0.8 and Input.is_action_just_pressed("restart")):
			_respawn()


func _unhandled_input(event: InputEvent) -> void:
	# la molette envoie appui et relâchement dans la même image : on lit l'événement lui-même
	if event.is_action_pressed("zoom_out"):
		_zoom(1)
	elif event.is_action_pressed("zoom_in"):
		_zoom(-1)


## Facteurs d'agrandissement entiers possibles pour cette fenêtre, du plus proche au plus éloigné.
func _zoom_scales() -> Vector2i:
	var h := float(get_tree().root.size.y)
	return Vector2i(maxi(1, int(h / NEAREST_NATIVE_H)), maxi(1, int(ceil(h / FARTHEST_NATIVE_H))))


## `step` > 0 : dézoomer (facteur plus petit, plus de monde visible).
func _zoom(step: int) -> void:
	var r := _zoom_scales()
	var s := clampi(pixel_scale - step, r.y, r.x)
	if s == pixel_scale:
		return
	zoom_height = float(get_tree().root.size.y) / s
	_layout()


## Facteur entier tiré du zoom choisi, puis image native qui remplit toute la fenêtre.
func _layout() -> void:
	var win := Vector2(get_tree().root.size)
	var r := _zoom_scales()
	pixel_scale = clampi(roundi(win.y / zoom_height), r.y, r.x)
	var nh := int(ceil(win.y / pixel_scale))
	native = Vector2i(mini(int(ceil(win.x / pixel_scale)), int(nh * MAX_ASPECT)), nh)
	display.stretch_shrink = pixel_scale
	display.size = Vector2(native + Vector2i(MARGIN, MARGIN) * 2) * pixel_scale
	var origin := ((win - Vector2(native) * pixel_scale) * 0.5).floor()
	_base_pos = origin - Vector2(MARGIN, MARGIN) * pixel_scale
	hud.set_layout(pixel_scale, origin, native)


func _toggle_fullscreen() -> void:
	var fs := DisplayServer.window_get_mode() in [DisplayServer.WINDOW_MODE_FULLSCREEN,
		DisplayServer.WINDOW_MODE_EXCLUSIVE_FULLSCREEN]
	DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_WINDOWED if fs else DisplayServer.WINDOW_MODE_FULLSCREEN)


# --------------------------------------------------------------------------- déroulement
func _on_encounter_started(enc: Encounter) -> void:
	hud.announce(enc.display_name(), 1.6)
	var tip := String(enc.config.get("hint", ""))
	if tip != "":
		hud.hint(tip, 7.0)
	Sound.play("wave_start")
	Sound.play_music("combat_theme", 0.8)


func _on_encounter_cleared(enc: Encounter) -> void:
	hud.announce(String(enc.config.get("clear_message", "Salle libérée")), 2.2)
	Sound.stop_music(3.0)


func _on_checkpoint(b: Brazier) -> void:
	checkpoint = b.respawn_point
	hud.announce("Feu ravivé", 1.8)
	hud.hint("Tes forces reviennent. Si tu tombes, tu repartiras d'ici.", 5.0)


func _on_boss_started(b: BossSlime) -> void:
	hud.show_boss(b.display_name)
	hud.announce(b.display_name, 2.2)
	if not b.health_changed.is_connected(hud.set_boss):
		b.health_changed.connect(hud.set_boss)
		b.phase_changed.connect(_on_boss_phase)
	Sound.play_music("boss_theme", 0.5)


func _on_boss_phase(phase: int) -> void:
	match phase:
		2:
			hud.hint("Son onde de choc ne se fuit pas : traverse-la en roulade !", 7.0)
		3:
			hud.announce("Le Roi enrage !", 1.6)
			hud.hint("Trois écrasements de suite... puis il s'effondre : frappe !", 7.0)


func _on_boss_defeated(_b: BossSlime) -> void:
	hud.hide_boss()
	hud.announce("Le Roi Gluant est vaincu !", 3.5)
	hud.hint("Sa salle du trésor s'est ouverte.", 6.0)
	Sound.stop_music(1.0)
	Sound.play("victory")


func _on_chest_opened(reward: String) -> void:
	match reward:
		"bottes":
			hero.dodge_strike = true
			hud.announce("Bottes de rafale !", 2.5)
			hud.hint("Ta roulade frappe et repousse désormais les monstres.", 8.0)
		"fin":
			_finished = true
			hud.announce("Fin du niveau 1 - merci d'avoir joué !", 0.0)
			Sound.play("victory")


func _on_hero_died() -> void:
	hud.announce("Tu es tombé...", RESPAWN_DELAY)
	hud.hide_boss()
	Sound.stop_music(1.2)
	Sound.play("hero_death")
	_respawn_in = RESPAWN_DELAY


func _respawn() -> void:
	Engine.time_scale = 1.0
	level.on_hero_respawn()
	hero.respawn(checkpoint)
	camera.snap()
	hud.announce("", 0.1)


# --------------------------------------------------------------------------- contrôles
func _setup_input() -> void:
	# touches physiques : ZQSD sur AZERTY et WASD sur QWERTY tombent au même endroit
	var keys := {
		"move_left": [KEY_A, KEY_LEFT], "move_right": [KEY_D, KEY_RIGHT],
		"move_up": [KEY_W, KEY_UP], "move_down": [KEY_S, KEY_DOWN],
		"attack": [KEY_J], "dodge": [KEY_SPACE, KEY_K], "restart": [KEY_R],
		"equip_cycle": [KEY_TAB], "equip_1": [KEY_1], "equip_2": [KEY_2], "equip_3": [KEY_3],
		"toggle_fullscreen": [KEY_F11],
		"zoom_in": [KEY_EQUAL, KEY_KP_ADD], "zoom_out": [KEY_MINUS, KEY_KP_SUBTRACT],
	}
	for action in keys:
		if InputMap.has_action(action):
			continue
		InputMap.add_action(action, 0.2)
		for k in keys[action]:
			var ev := InputEventKey.new()
			ev.physical_keycode = k
			InputMap.action_add_event(action, ev)
	for wheel in [[MOUSE_BUTTON_WHEEL_UP, "zoom_in"], [MOUSE_BUTTON_WHEEL_DOWN, "zoom_out"]]:
		var ev := InputEventMouseButton.new()
		ev.button_index = wheel[0]
		InputMap.action_add_event(wheel[1], ev)
	var alt_enter := InputEventKey.new()               # Alt+Entrée : plein écran, comme F11
	alt_enter.physical_keycode = KEY_ENTER
	alt_enter.alt_pressed = true
	InputMap.action_add_event("toggle_fullscreen", alt_enter)
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


func _teleport(cell: Vector2i) -> void:
	hero.global_position = level.cell_center(cell.x, cell.y)
	camera.snap()


func _shot(index: int) -> void:
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png(_shot_path.get_basename() + "_%d.png" % index)


## Visite en captures : départ, passage piégé, 1re salle, hall, piques, ossuaire, boss.
func _run_tour() -> void:
	hero.god_mode = true
	var stops := [Vector2i(50, 57), Vector2i(41, 56), Vector2i(37, 47), Vector2i(31, 38),
		Vector2i(27, 25), Vector2i(10, 24), Vector2i(9, 9), Vector2i(6, 37)]
	await _wait_real(1.0)
	for i in stops.size():
		_teleport(stops[i])
		await _wait_real(1.6)
		for k in 2:
			_press("attack")
			await _wait_real(0.12)
		await _shot(i + 1)
	# boss : directement en phase 2 pour voir l'onde de choc et les mini-slimes
	level.boss.hp = 22.0
	level.boss.phase = 2
	_teleport(Vector2i(46, 18))
	var t := 0.0
	while level.boss.state != BossSlime.State.AIR and t < 8.0:
		await _wait_real(0.1)
		t += 0.1
	await _wait_real(0.45)
	await _shot(stops.size() + 1)
	while level.boss.state != BossSlime.State.LANDED and t < 12.0:
		await _wait_real(0.05)
		t += 0.05
	await _wait_real(0.2)
	await _shot(stops.size() + 2)
	await _wait_real(0.6)
	await _shot(stops.size() + 3)
	print("SCREENSHOT ", _shot_path)
	Sound.quit_cleanly()


## Parcours automatique (héros invincible) : objets, première salle, boss. Affiche un bilan.
func _run_selftest() -> void:
	hero.god_mode = true
	var report := {"stats": level.stats, "herses": level.gates.size(), "rencontres": level.encounters.size(),
		"apparitions": level.spawn_points.keys(), "boss": level.boss != null}
	print("SELFTEST niveau ", JSON.stringify(report))
	# 1) jarres du chemin
	var before := get_tree().get_nodes_in_group("hittable").size()
	_teleport(Vector2i(45, 55))
	for i in 4:
		await _press("attack")
		await _wait_real(0.3)
	print("SELFTEST jarres cassées : %d" % (before - get_tree().get_nodes_in_group("hittable").size()))
	# 2) première salle
	_teleport(Vector2i(30, 37))
	var enc: Encounter = level.encounters[0]
	var t0 := Time.get_ticks_msec()
	var next_dbg := 0
	while enc.phase != Encounter.Phase.CLEARED and Time.get_ticks_msec() - t0 < 45000:
		await _press("attack")
		await _wait_real(0.2)
		if Time.get_ticks_msec() - t0 > next_dbg:
			next_dbg += 5000
			var info := []
			for e in enc._alive:
				if is_instance_valid(e):
					info.append("%s pv%d %s d=%.1f" % [e.name, e.hp, Enemy.State.keys()[e.state],
						e.global_position.distance_to(hero.global_position)])
			print("SELFTEST salle 1 vague=%d attente=%d vivants=%s héros=%s" % [enc.wave, enc._pending, info,
				hero.global_position])
	print("SELFTEST salle 1 : %s en %.1f s, herses ouvertes : %s" % [
		Encounter.Phase.keys()[enc.phase], (Time.get_ticks_msec() - t0) / 1000.0,
		level.gates["e1_out"].is_open])
	# 3) boss
	level.set_gates(["boss"], true)
	_teleport(Vector2i(46, 18))
	t0 = Time.get_ticks_msec()
	var last_print := 0
	while level.boss.state != BossSlime.State.DEAD and Time.get_ticks_msec() - t0 < 150000:
		await _press("attack")
		await _wait_real(0.18)
		var s := (Time.get_ticks_msec() - t0) / 1000
		if s >= last_print + 15:
			last_print = s
			print("SELFTEST boss t=%ds pv=%.1f phase=%d état=%s" % [s, level.boss.hp, level.boss.phase,
				BossSlime.State.keys()[level.boss.state]])
	var duration := (Time.get_ticks_msec() - t0) / 1000.0
	await _wait_real(1.5)                     # la sortie s'ouvre après l'animation de mort
	print("SELFTEST boss : %s en %.1f s, sortie ouverte : %s" % [BossSlime.State.keys()[level.boss.state],
		duration, level.gates["exit"].is_open])
	Sound.quit_cleanly()
