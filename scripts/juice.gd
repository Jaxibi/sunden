extends Node
## Autoload « Juice » : la sensation des coups (arrêt sur image, tremblement, éclats).

var camera: PixelCamera
var fx_root: Node

var _resume_at_msec := 0


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS


## Fige presque le jeu pendant `seconds` (temps réel) : donne du poids à l'impact.
func hitstop(seconds: float) -> void:
	_resume_at_msec = maxi(_resume_at_msec, Time.get_ticks_msec() + int(seconds * 1000.0))
	Engine.time_scale = 0.02


## Tremblement d'écran, en pixels entiers.
func shake(pixels: float) -> void:
	if is_instance_valid(camera):
		camera.shake(pixels)


func burst(pos: Vector3, colors: Array, count := 8, speed := 4.0, size := 0.09) -> void:
	if is_instance_valid(fx_root):
		Burst.spawn(fx_root, pos, colors, count, speed, size)


func _process(_delta: float) -> void:
	if Engine.time_scale < 1.0 and Time.get_ticks_msec() >= _resume_at_msec:
		Engine.time_scale = 1.0
