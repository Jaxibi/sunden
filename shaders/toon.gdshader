// Ombrage toon en paliers, mêmes teintes que le rendu Blender d'exemple.
// Ombre = couleur x teinte violette ; la lumière du soleil ajoute des paliers nets,
// les lumières ponctuelles (torches) ajoutent une flaque de couleur chaude.
shader_type spatial;
render_mode specular_disabled, ambient_light_disabled;

uniform vec4 albedo : source_color = vec4(1.0);
// Valeurs linéaires (#6f679e et #b9b3d1 en sRGB)
uniform vec3 shadow_tint = vec3(0.159, 0.136, 0.342);
uniform vec3 mid_tint = vec3(0.485, 0.451, 0.637);
uniform float mid_threshold = 0.10;
uniform float lit_threshold = 0.40;
uniform float point_threshold = 0.15;
uniform float point_strength = 0.35;
// a = intensité du flash d'impact (0 ou 1 pour rester en pixel art)
uniform vec4 flash_color : source_color = vec4(1.0, 1.0, 1.0, 0.0);

void fragment() {
	ALBEDO = albedo.rgb * (1.0 - flash_color.a);
	ROUGHNESS = 1.0;
	EMISSION = mix(albedo.rgb * shadow_tint, flash_color.rgb, flash_color.a);
}

void light() {
	float ndl = clamp(dot(NORMAL, LIGHT), 0.0, 1.0) * ATTENUATION;
	if (LIGHT_IS_DIRECTIONAL) {
		vec3 band = ndl > lit_threshold ? vec3(1.0) : (ndl > mid_threshold ? mid_tint : shadow_tint);
		DIFFUSE_LIGHT += band - shadow_tint;
	} else {
		float peak = max(max(LIGHT_COLOR.r, LIGHT_COLOR.g), max(LIGHT_COLOR.b, 0.0001));
		DIFFUSE_LIGHT += step(point_threshold, ndl) * (LIGHT_COLOR / peak) * point_strength;
	}
}
