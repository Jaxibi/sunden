class_name Gate
extends StaticBody3D
## Herse : barreaux qui descendent dans le sol pour ouvrir le passage.

const DROP := 1.85

var gate_id := ""
var is_open := true
var cells: Array[Vector2i] = []
var _bars := Node3D.new()
var _shape := CollisionShape3D.new()


## `cells` : cases (Vector2i) alignées sur une ligne ou une colonne. `make_bar` crée une herse d'une case.
func setup(id: String, gate_cells: Array, make_bar: Callable, open: bool) -> void:
	gate_id = id
	for c in gate_cells:
		cells.append(c)
	name = "Herse_" + id
	add_child(_bars)
	var lo := Vector2(INF, INF)
	var hi := Vector2(-INF, -INF)
	for c in cells:
		lo = Vector2(minf(lo.x, c.x), minf(lo.y, c.y))
		hi = Vector2(maxf(hi.x, c.x), maxf(hi.y, c.y))
	var along_x := hi.y == lo.y
	for c in cells:
		var bar: Node3D = make_bar.call()
		_bars.add_child(bar)
		bar.position = Vector3(c.x + 0.5, 0.0, c.y + 0.5)
		if not along_x:
			bar.rotation.y = PI * 0.5
	var box := BoxShape3D.new()
	box.size = Vector3(hi.x - lo.x + 1.0, 2.4, 0.4) if along_x else Vector3(0.4, 2.4, hi.y - lo.y + 1.0)
	_shape.shape = box
	_shape.position = Vector3((lo.x + hi.x) * 0.5 + 0.5, 1.2, (lo.y + hi.y) * 0.5 + 0.5)
	add_child(_shape)
	is_open = not open                      # force l'état initial sans animation ni son
	_apply(open, false)


func open() -> void:
	_apply(true, true)


func close() -> void:
	_apply(false, true)


func _apply(open: bool, animate: bool) -> void:
	if open == is_open:
		return
	is_open = open
	_shape.set_deferred("disabled", open)
	var y := -DROP if open else 0.0
	if animate:
		var tw := create_tween()
		tw.tween_property(_bars, "position:y", y, 0.5 if open else 0.25) \
			.set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN_OUT)
		Sound.play("gate_move")
		Juice.shake(1.0)
	else:
		_bars.position.y = y
