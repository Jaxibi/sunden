// Ombrage toon en paliers, mêmes teintes que le rendu Blender d'exemple.
// - Ombre = couleur x teinte violette ; la lumière du soleil ajoute des paliers nets
//   ainsi qu'un 4e palier « point chaud » (spéculaire / rim en palier pour métaux et slime).
// - Les lumières ponctuelles (torches) dessinent un double halo chaud en paliers.
// - ROUGHNESS transporte le masque de contour lu par outline.gdshader :
//   0.0 = sans contour, 0.5 = silhouette seule, 1.0 = silhouette + plis internes.
shader_type spatial;
render_mode specular_disabled, ambient_light_disabled;

uniform vec4 albedo : source_color = vec4(1.0);
// Valeurs linéaires (#6f679e, #b9b3d1 et #fff1d6 en sRGB)
uniform vec3 shadow_tint = vec3(0.159, 0.136, 0.342);
uniform vec3 mid_tint = vec3(0.485, 0.451, 0.637);
uniform vec3 highlight_tint = vec3(1.0, 0.884, 0.672);
uniform float mid_threshold = 0.10;
uniform float lit_threshold = 0.40;
// Point chaud (spéculaire / rim en palier)
uniform float spec_strength = 0.0;
uniform float spec_threshold = 0.74;
uniform float rim_strength = 0.0;
uniform float rim_threshold = 0.65;
// Double halo des lumières ponctuelles (torches)
uniform float point_threshold = 0.12;
uniform float point_inner_threshold = 0.36;
uniform float point_strength = 0.25;
uniform float point_inner_strength = 0.30;
// Masque de contour pour outline.gdshader (0.0, 0.5 ou 1.0)
uniform float outline_mask = 1.0;
// a = intensité du flash d'impact (0 ou 1 pour rester en pixel art)
uniform vec4 flash_color : source_color = vec4(1.0, 1.0, 1.0, 0.0);

void fragment() {
	ALBEDO = albedo.rgb * (1.0 - flash_color.a);
	ROUGHNESS = outline_mask;
	EMISSION = mix(albedo.rgb * shadow_tint, flash_color.rgb, flash_color.a);
}

void light() {
	float ndl = clamp(dot(NORMAL, LIGHT), 0.0, 1.0) * ATTENUATION;
	if (LIGHT_IS_DIRECTIONAL) {
		vec3 band = ndl > lit_threshold ? vec3(1.0) : (ndl > mid_threshold ? mid_tint : shadow_tint);
		vec3 H = normalize(LIGHT + VIEW);
		float ndh = clamp(dot(NORMAL, H), 0.0, 1.0);
		float ndv = clamp(dot(NORMAL, VIEW), 0.0, 1.0);
		float spec = step(spec_threshold, ndh) * step(lit_threshold, ndl) * spec_strength;
		float rim = step(rim_threshold, 1.0 - ndv) * step(mid_threshold, ndl) * rim_strength;
		band += highlight_tint * max(spec, rim);
		DIFFUSE_LIGHT += band - shadow_tint;
	} else {
		float peak = max(max(LIGHT_COLOR.r, LIGHT_COLOR.g), max(LIGHT_COLOR.b, 0.0001));
		vec3 warm = LIGHT_COLOR / peak;
		float halo = step(point_threshold, ndl) * point_strength
			+ step(point_inner_threshold, ndl) * point_inner_strength;
		DIFFUSE_LIGHT += halo * warm;
	}
}
