class_name ToonMaterials
## Convertit les matériaux importés depuis Blender (glTF) en shader toon pixel art.
## - Les matériaux émissifs (flammes, effets) sont rendus après la passe de contour (sans liseré noir).
## - Les touffes d'herbe désactivent le contour (outline_mask = 0.0, comme SansContour dans Blender).
## - Le slime n'a qu'un contour de silhouette sans pli interne (outline_mask = 0.5) et un éclat humide.
## - Les métaux (Acier, Or) reçoivent un 4e palier spéculaire/rim net.

const TOON_SHADER := preload("res://shaders/toon.gdshader")


## Remplace les matériaux de tous les MeshInstance3D sous `root`.
## Chaque appel crée ses propres copies : on peut donc faire clignoter un ennemi sans toucher aux autres.
## Renvoie les ShaderMaterial créés (utile pour le flash d'impact).
static func apply(root: Node) -> Array[ShaderMaterial]:
	var cache := {}
	var result: Array[ShaderMaterial] = []
	for node in root.find_children("*", "MeshInstance3D", true, false):
		var mi := node as MeshInstance3D
		if mi.mesh == null:
			continue
		var node_name := String(mi.name)
		for s in mi.mesh.get_surface_count():
			var src := mi.get_active_material(s)
			if src == null:
				continue
			var key := "%d:%s" % [src.get_instance_id(), "touffe" if node_name.begins_with("Touffe") else ""]
			if not cache.has(key):
				cache[key] = _convert(src, node_name)
				if cache[key] is ShaderMaterial:
					result.append(cache[key])
			mi.set_surface_override_material(s, cache[key])
	return result


static func _convert(src: Material, node_name := "") -> Material:
	var base := src as BaseMaterial3D
	if base == null:
		return src
	var mat_name := base.resource_name
	if base.emission_enabled:
		var unlit := StandardMaterial3D.new()
		unlit.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		unlit.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		unlit.depth_draw_mode = BaseMaterial3D.DEPTH_DRAW_DISABLED
		# Le coeur de flamme est dessiné par-dessus la flamme externe, tous deux après OutlinePass
		unlit.render_priority = 2 if (mat_name == "FlammeCoeur" or node_name.ends_with("_Coeur")) else 1
		unlit.albedo_color = base.albedo_color
		return unlit
	var toon := ShaderMaterial.new()
	toon.shader = TOON_SHADER
	toon.set_shader_parameter("albedo", base.albedo_color)
	if mat_name == "TouffeHerbe" or node_name.begins_with("Touffe"):
		toon.set_shader_parameter("outline_mask", 0.0)
	elif mat_name == "Slime":
		toon.set_shader_parameter("outline_mask", 0.5)
		toon.set_shader_parameter("spec_strength", 0.35)
		toon.set_shader_parameter("spec_threshold", 0.86)
		toon.set_shader_parameter("rim_strength", 0.22)
		toon.set_shader_parameter("rim_threshold", 0.72)
	elif mat_name in ["Acier", "AcierSombre", "Or"]:
		toon.set_shader_parameter("outline_mask", 0.5)
		toon.set_shader_parameter("spec_strength", 0.50)
		toon.set_shader_parameter("spec_threshold", 0.76)
		toon.set_shader_parameter("rim_strength", 0.22)
		toon.set_shader_parameter("rim_threshold", 0.70)
	elif mat_name in ["Peau", "Cheveux", "Tunique", "TissuClair", "Cape", "CapeVerte", "Pantalon", "Os"]:
		# Silhouette externe nette sans plis noirs internes sur le visage, les os et les étoffes
		toon.set_shader_parameter("outline_mask", 0.5)
		toon.set_shader_parameter("rim_strength", 0.15)
		toon.set_shader_parameter("rim_threshold", 0.72)
	elif mat_name in ["Cuir", "CuirClair", "BoisSombre", "Rouille"]:
		toon.set_shader_parameter("outline_mask", 0.5)
		toon.set_shader_parameter("spec_strength", 0.22)
		toon.set_shader_parameter("spec_threshold", 0.78)
	return toon
