class_name SteppedAnimator
extends RefCounted
## Joue les animations importées de Blender par paliers (aspect « image par image » du pixel art)
## et peut recaler une animation sur une durée de jeu (préparation, coup, recul...).

var player: AnimationPlayer
var fps := 15.0
var current := ""
var _accum := 0.0


## `looping` : animations à lire en boucle. `frames_per_second` <= 0 : lecture fluide.
func _init(model: Node, frames_per_second: float, looping: Array) -> void:
	fps = frames_per_second
	player = model.find_child("AnimationPlayer", true, false) as AnimationPlayer
	if player == null:
		push_warning("%s : aucune animation importée" % model.name)
		return
	for n in looping:
		if player.has_animation(n):
			player.get_animation(n).loop_mode = Animation.LOOP_LINEAR
	if fps > 0.0:
		player.callback_mode_process = AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_MANUAL


func has(anim_name: String) -> bool:
	return player != null and player.has_animation(anim_name)


func length(anim_name: String) -> float:
	return player.get_animation(anim_name).length if has(anim_name) else 0.0


## `duration` > 0 : la lecture est accélérée ou ralentie pour durer exactement `duration` secondes.
func play(anim_name: String, restart := false, duration := 0.0) -> void:
	if not has(anim_name):
		return
	if anim_name == current and not restart:
		return
	current = anim_name
	var speed := 1.0
	if duration > 0.0:
		speed = player.get_animation(anim_name).length / duration
	player.play(anim_name, -1.0, speed)
	player.seek(0.0, true)
	_accum = 0.0


## À appeler dans _process.
func update(delta: float) -> void:
	if player == null or fps <= 0.0:
		return
	_accum += delta
	var step := 1.0 / fps
	if _accum >= step:
		var n := floorf(_accum / step)
		player.advance(n * step)
		_accum -= n * step
