class_name Hud
extends CanvasLayer
## Interface dessinée en 320x180 puis agrandie du même facteur que le jeu : pixels nets.

var _font: Font
var _hp_fill: ColorRect
var _info: Label
var _banner: Label
var _help: Label
var _banner_time := 0.0
var _help_time := 7.0


func _ready() -> void:
	_font = ThemeDB.fallback_font
	if _font is FontFile:
		var f := (_font as FontFile).duplicate() as FontFile
		f.antialiasing = TextServer.FONT_ANTIALIASING_NONE
		f.hinting = TextServer.HINTING_NONE
		f.subpixel_positioning = TextServer.SUBPIXEL_POSITIONING_DISABLED
		_font = f
	_rect(Vector2(5, 5), Vector2(62, 7), Color("1f1830"))
	_rect(Vector2(6, 6), Vector2(60, 5), Color("4a2434"))
	_hp_fill = _rect(Vector2(6, 6), Vector2(60, 5), Color("e04a4a"))
	_info = _label(Vector2(6, 13), Vector2(200, 12), 8, HORIZONTAL_ALIGNMENT_LEFT)
	_banner = _label(Vector2(0, 58), Vector2(320, 24), 16, HORIZONTAL_ALIGNMENT_CENTER)
	_help = _label(Vector2(0, 166), Vector2(320, 12), 8, HORIZONTAL_ALIGNMENT_CENTER)
	_help.text = "ZQSD/WASD bouger   J/clic attaquer   Espace esquiver"


func set_pixel_scale(pixel_scale: int, origin: Vector2) -> void:
	transform = Transform2D(0.0, Vector2(pixel_scale, pixel_scale), 0.0, origin)


func set_health(hp: int, max_hp: int) -> void:
	_hp_fill.size.x = roundf(60.0 * hp / max_hp)


func set_wave(wave: int, kills: int) -> void:
	_info.text = "Vague %d   Vaincus %d" % [wave, kills]


## duration <= 0 : le message reste affiché.
func announce(text: String, duration := 1.6) -> void:
	_banner.text = text
	_banner_time = duration if duration > 0.0 else INF


func _process(delta: float) -> void:
	if _banner_time > 0.0:
		_banner_time -= delta
		if _banner_time <= 0.0:
			_banner.text = ""
	if _help_time > 0.0:
		_help_time -= delta
		if _help_time <= 0.0:
			_help.text = ""


func _rect(pos: Vector2, rect_size: Vector2, color: Color) -> ColorRect:
	var r := ColorRect.new()
	r.position = pos
	r.size = rect_size
	r.color = color
	r.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(r)
	return r


func _label(pos: Vector2, rect_size: Vector2, font_size: int, align: HorizontalAlignment) -> Label:
	var l := Label.new()
	l.position = pos
	l.size = rect_size
	l.horizontal_alignment = align
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	l.add_theme_font_override("font", _font)
	l.add_theme_font_size_override("font_size", font_size)
	l.add_theme_color_override("font_color", Color("fff1d6"))
	l.add_theme_color_override("font_outline_color", Color("1f1830"))
	l.add_theme_constant_override("outline_size", 2)
	add_child(l)
	return l
