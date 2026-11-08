class_name ToonMaterials
## Convertit les matériaux importés depuis Blender (glTF) en shader toon pixel art.
## Les matériaux émissifs (flammes, effets) deviennent des matériaux non éclairés.

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
		for s in mi.mesh.get_surface_count():
			var src := mi.get_active_material(s)
			if src == null:
				continue
			if not cache.has(src):
				cache[src] = _convert(src)
				if cache[src] is ShaderMaterial:
					result.append(cache[src])
			mi.set_surface_override_material(s, cache[src])
	return result


static func _convert(src: Material) -> Material:
	var base := src as BaseMaterial3D
	if base == null:
		return src
	if base.emission_enabled:
		var unlit := StandardMaterial3D.new()
		unlit.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		unlit.albedo_color = base.albedo_color
		return unlit
	var toon := ShaderMaterial.new()
	toon.shader = TOON_SHADER
	toon.set_shader_parameter("albedo", base.albedo_color)
	return toon
