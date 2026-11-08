extends Node
## Autoload « Sound » : effets sonores et musique (direction audio : AUDIO_THEME.md).
##
## Sound.play("sword_hit") joue une variante au hasard parmi assets/audio/sfx/sword_hit_1.wav,
## sword_hit_2.wav... (ou sword_hit.wav), sans répéter deux fois de suite la même, avec une
## légère variation de hauteur et de volume. Un son absent est ignoré (avertissement unique).

const SFX_DIR := "res://assets/audio/sfx/"
const MUSIC_DIR := "res://assets/audio/music/"

## Réglages par son : volume (dB, ajouté au niveau du fichier), variation de hauteur
## (1.06 = ±6 %) et nombre maximal d'occurrences simultanées.
const TUNING := {
	"footstep": {"pitch": 1.12, "polyphony": 2},
	"sword_swing": {"pitch": 1.08},
	"sword_hit": {"pitch": 1.05, "polyphony": 3},
	"spin_attack": {"pitch": 1.03, "polyphony": 1},
	"dodge_roll": {"pitch": 1.06, "polyphony": 1},
	"hero_hurt": {"pitch": 1.04, "polyphony": 1},
	"hero_death": {"pitch": 1.0, "polyphony": 1},
	"wave_start": {"pitch": 1.0, "polyphony": 1},
	"slime_hit": {"volume": -2.0},
	"skeleton_hit": {"volume": -2.0},
	"slime_windup": {"volume": -3.0},
	"skeleton_windup": {"volume": -3.0},
	"skeleton_spawn": {"volume": -4.0},
	"spike_trap": {"polyphony": 2},
	"gate_move": {"pitch": 1.03, "polyphony": 2},
	"brazier_light": {"pitch": 1.0, "polyphony": 1},
	"chest_open": {"pitch": 1.0, "polyphony": 1},
	"victory": {"pitch": 1.0, "polyphony": 1},
	"boss_roar": {"pitch": 1.03, "polyphony": 1},
	"boss_slam": {"pitch": 1.04, "polyphony": 2},
	"heart_pickup": {"pitch": 1.04},
}
const DEFAULT_PITCH := 1.06
const DEFAULT_POLYPHONY := 4

var _players := {}
var _missing := {}
var _music: AudioStreamPlayer
var _ambience: AudioStreamPlayer
var _quitting := false


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	_music = _loop_player("Music")
	_ambience = _loop_player("Ambience")
	# fermeture : on coupe le son et on laisse au serveur audio le temps de libérer les flux
	get_tree().set_auto_accept_quit(false)


func _notification(what: int) -> void:
	if what == NOTIFICATION_WM_CLOSE_REQUEST:
		quit_cleanly()


## Quitte le jeu après avoir arrêté tous les sons (à utiliser à la place de get_tree().quit()).
func quit_cleanly() -> void:
	_quitting = true
	for p in get_children():
		if p is AudioStreamPlayer:
			p.stop()
			p.stream = null
	_players.clear()
	await get_tree().create_timer(0.15, true, false, true).timeout
	get_tree().quit()


# --------------------------------------------------------------------------- effets
## `pitch` < 1 rend le son plus grave (le Roi Gluant réutilise les sons du slime).
func play(sound_name: String, volume_db := 0.0, pitch := 1.0) -> void:
	if _quitting:
		return
	var p := _player(sound_name)
	if p == null:
		return
	var tuning: Dictionary = TUNING.get(sound_name, {})
	p.volume_db = float(tuning.get("volume", 0.0)) + volume_db
	p.pitch_scale = pitch
	p.play()


func _player(sound_name: String) -> AudioStreamPlayer:
	if _players.has(sound_name):
		return _players[sound_name]
	if _missing.has(sound_name):
		return null
	var streams := _load_variants(sound_name)
	if streams.is_empty():
		_missing[sound_name] = true
		push_warning("Son introuvable : %s (relancer tools/generate_audio.py)" % sound_name)
		return null
	var tuning: Dictionary = TUNING.get(sound_name, {})
	var rnd := AudioStreamRandomizer.new()
	rnd.playback_mode = AudioStreamRandomizer.PLAYBACK_RANDOM_NO_REPEATS if streams.size() > 1 \
		else AudioStreamRandomizer.PLAYBACK_RANDOM
	rnd.random_pitch = float(tuning.get("pitch", DEFAULT_PITCH))
	rnd.random_volume_offset_db = 1.2
	for s in streams:
		rnd.add_stream(-1, s)
	var p := AudioStreamPlayer.new()
	p.name = sound_name
	p.stream = rnd
	p.bus = &"SFX"
	p.max_polyphony = int(tuning.get("polyphony", DEFAULT_POLYPHONY))
	add_child(p)
	_players[sound_name] = p
	return p


func _load_variants(sound_name: String) -> Array:
	var out := []
	var single := SFX_DIR + sound_name + ".wav"
	if ResourceLoader.exists(single):
		out.append(load(single))
	var i := 1
	while ResourceLoader.exists(SFX_DIR + "%s_%d.wav" % [sound_name, i]):
		out.append(load(SFX_DIR + "%s_%d.wav" % [sound_name, i]))
		i += 1
	return out


# --------------------------------------------------------------------------- musique
## Lance une piste en boucle sur le bus Music (ne la relance pas si elle joue déjà).
func play_music(track: String, fade := 1.5) -> void:
	_start_loop(_music, track, fade)


func stop_music(fade := 2.0) -> void:
	_fade(_music, -60.0, fade, true)


func play_ambience(track: String, fade := 3.0) -> void:
	_start_loop(_ambience, track, fade)


func _start_loop(player: AudioStreamPlayer, track: String, fade: float) -> void:
	var path := MUSIC_DIR + track + ".mp3"
	if not ResourceLoader.exists(path):
		if not _missing.has(path):
			_missing[path] = true
			push_warning("Musique introuvable : %s" % path)
		return
	var stream := load(path) as AudioStreamMP3
	stream.loop = true
	if player.stream != stream or not player.playing:
		player.stream = stream
		player.volume_db = -60.0
		player.play()
	_fade(player, 0.0, fade, false)


func _fade(player: AudioStreamPlayer, to_db: float, seconds: float, stop_after: bool) -> void:
	if not player.playing:
		return
	var tw := create_tween()
	tw.tween_property(player, "volume_db", to_db, seconds)
	if stop_after:
		tw.tween_callback(player.stop)


func _loop_player(bus: StringName) -> AudioStreamPlayer:
	var p := AudioStreamPlayer.new()
	p.name = String(bus)
	p.bus = bus
	add_child(p)
	return p
