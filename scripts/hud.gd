class_name Hud
extends CanvasLayer
## Interface dessinée en 320x180 puis agrandie du même facteur que le jeu : pixels nets.
## Vie, nom de la zone, annonces au centre, indices en bas, barre du boss.

const BOSS_BAR_W := 160.0

var _font: Font
var _hp_fill: ColorRect
var _zone: Label
var _banner: Label
var _hint: Label
var _boss_root: Control
var _boss_name: Label
var _boss_fill: ColorRect
var _boss_ghost: ColorRect
var _banner_time := 0.0
var _hint_time := 0.0
var _zone_time := 0.0


func _ready() -> void:
	_font = ThemeDB.fallback_font
	if _font is FontFile:
		var f := (_font as FontFile).duplicate() as FontFile
		f.antialiasing = TextServer.FONT_ANTIALIASING_NONE
		f.hinting = TextServer.HINTING_NONE
		f.subpixel_positioning = TextServer.SUBPIXEL_POSITIONING_DISABLED
		_font = f
	_rect(self, Vector2(5, 5), Vector2(62, 7), Color("1f1830"))
	_rect(self, Vector2(6, 6), Vector2(60, 5), Color("4a2434"))
	_hp_fill = _rect(self, Vector2(6, 6), Vector2(60, 5), Color("e04a4a"))
	_zone = _label(self, Vector2(6, 13), Vector2(200, 12), 8, HORIZONTAL_ALIGNMENT_LEFT)
	_banner = _label(self, Vector2(0, 56), Vector2(320, 24), 16, HORIZONTAL_ALIGNMENT_CENTER)
	_hint = _label(self, Vector2(4, 164), Vector2(312, 12), 8, HORIZONTAL_ALIGNMENT_CENTER)
	# barre du boss (bas de l'écran, au-dessus des indices)
	_boss_root = Control.new()
	_boss_root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_boss_root.visible = false
	add_child(_boss_root)
	var x0 := (320.0 - BOSS_BAR_W) * 0.5
	_boss_name = _label(_boss_root, Vector2(0, 140), Vector2(320, 12), 8, HORIZONTAL_ALIGNMENT_CENTER)
	_rect(_boss_root, Vector2(x0 - 1, 152), Vector2(BOSS_BAR_W + 2, 7), Color("1f1830"))
	_rect(_boss_root, Vector2(x0, 153), Vector2(BOSS_BAR_W, 5), Color("3a2050"))
	_boss_ghost = _rect(_boss_root, Vector2(x0, 153), Vector2(BOSS_BAR_W, 5), Color("fff1d6"))
	_boss_fill = _rect(_boss_root, Vector2(x0, 153), Vector2(BOSS_BAR_W, 5), Color("b36ae0"))


## Échelle et largeur native (320 en 16:9, 640 en 32:9) : les éléments centrés suivent la largeur.
func set_layout(pixel_scale: int, origin: Vector2, native: Vector2i) -> void:
	transform = Transform2D(0.0, Vector2(pixel_scale, pixel_scale), 0.0, origin)
	var w := float(native.x)
	var h := float(native.y)
	_banner.size.x = w
	_banner.position.y = roundf(h * 0.31)
	_hint.size.x = w - 8.0
	_hint.position.y = h - 16.0
	# barre conçue pour une image de 320x180 : centrée et collée en bas
	_boss_root.position = Vector2(roundf((w - 320.0) * 0.5), h - 180.0)


func set_health(hp: int, max_hp: int) -> void:
	_hp_fill.size.x = roundf(60.0 * hp / max_hp)


## Nom de la zone : affiché en grand un instant, puis en petit en haut à gauche.
func set_zone(zone_name: String) -> void:
	_zone.text = zone_name
	announce(zone_name, 1.8)


## duration <= 0 : le message reste affiché.
func announce(text: String, duration := 1.6) -> void:
	_banner.text = text
	_banner_time = duration if duration > 0.0 else INF


func hint(text: String, duration := 6.0) -> void:
	_hint.text = text
	_hint_time = duration


func show_boss(boss_name: String) -> void:
	_boss_name.text = boss_name
	_boss_root.visible = true
	set_boss(1.0)


func set_boss(ratio: float) -> void:
	_boss_fill.size.x = roundf(BOSS_BAR_W * clampf(ratio, 0.0, 1.0))


func hide_boss() -> void:
	_boss_root.visible = false


func _process(delta: float) -> void:
	if _banner_time > 0.0:
		_banner_time -= delta
		if _banner_time <= 0.0:
			_banner.text = ""
	if _hint_time > 0.0:
		_hint_time -= delta
		if _hint_time <= 0.0:
			_hint.text = ""
	# la partie claire de la barre du boss rattrape lentement les dégâts : on lit le coup porté
	if _boss_root.visible:
		_boss_ghost.size.x = move_toward(_boss_ghost.size.x, _boss_fill.size.x, delta * 30.0)


func _rect(parent: Node, pos: Vector2, rect_size: Vector2, color: Color) -> ColorRect:
	var r := ColorRect.new()
	r.position = pos
	r.size = rect_size
	r.color = color
	r.mouse_filter = Control.MOUSE_FILTER_IGNORE
	parent.add_child(r)
	return r


func _label(parent: Node, pos: Vector2, rect_size: Vector2, font_size: int, align: HorizontalAlignment) -> Label:
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
	parent.add_child(l)
	return l
