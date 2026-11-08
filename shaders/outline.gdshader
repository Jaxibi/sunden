// Contour d'un pixel en post-process (quad plein écran enfant de la caméra).
// - silhouette : un voisin nettement plus loin -> trait sombre
// - pli : normale différente du voisin de droite ou du bas -> pixel assombri (1 px, un seul côté)
// - masque dans normal_tex.w (alimenté par ROUGHNESS dans toon.gdshader) :
//     < 0.25 : aucun contour ni pli (touffes d'herbe)
//     0.25..0.75 : silhouette seule, sans pli interne (slime, formes organiques)
//     >= 0.75 : silhouette + plis internes (architecture, personnages en blocs)
// Nécessite le moteur Forward+ (textures de profondeur et de normales).
shader_type spatial;
render_mode unshaded, fog_disabled, depth_draw_never, depth_test_disabled, cull_disabled, shadows_disabled;

uniform sampler2D screen_tex : hint_screen_texture, filter_nearest;
uniform sampler2D depth_tex : hint_depth_texture, filter_nearest;
uniform sampler2D normal_tex : hint_normal_roughness_texture, filter_nearest;

uniform vec3 line_color = vec3(0.0137, 0.0091, 0.0284); // #1f1830 en linéaire
uniform float depth_threshold = 0.3;
uniform float normal_threshold = 0.55;
uniform float crease_darken = 0.7;

void vertex() {
	POSITION = vec4(VERTEX.xy, 1.0, 1.0);
}

float view_depth(vec2 uv, mat4 inv_proj) {
	float d = texture(depth_tex, uv).r;
	vec4 v = inv_proj * vec4(uv * 2.0 - 1.0, d, 1.0);
	return -v.z / v.w;
}

vec3 decode_normal(vec4 nr) {
	return normalize(nr.xyz * 2.0 - 1.0);
}

void fragment() {
	vec2 px = 1.0 / VIEWPORT_SIZE;
	vec2 uv = SCREEN_UV;
	vec4 nr = texture(normal_tex, uv);
	float mask = nr.w;
	vec3 col = texture(screen_tex, uv).rgb;

	if (mask >= 0.25) {
		float d = view_depth(uv, INV_PROJECTION_MATRIX);

		float far_r = view_depth(uv + vec2(px.x, 0.0), INV_PROJECTION_MATRIX);
		float far_l = view_depth(uv - vec2(px.x, 0.0), INV_PROJECTION_MATRIX);
		float far_d = view_depth(uv + vec2(0.0, px.y), INV_PROJECTION_MATRIX);
		float far_u = view_depth(uv - vec2(0.0, px.y), INV_PROJECTION_MATRIX);
		float silhouette = max(max(far_r - d, far_l - d), max(far_d - d, far_u - d));

		float crease = 0.0;
		if (mask >= 0.75) {
			vec3 n = decode_normal(nr);
			vec4 nr_r = texture(normal_tex, uv + vec2(px.x, 0.0));
			vec4 nr_d = texture(normal_tex, uv + vec2(0.0, px.y));
			if (nr_r.w >= 0.75 && abs(far_r - d) < depth_threshold) {
				crease = max(crease, 1.0 - dot(n, decode_normal(nr_r)));
			}
			if (nr_d.w >= 0.75 && abs(far_d - d) < depth_threshold) {
				crease = max(crease, 1.0 - dot(n, decode_normal(nr_d)));
			}
		}

		if (silhouette > depth_threshold) {
			col = line_color;
		} else if (crease > normal_threshold) {
			col *= crease_darken;
		}
	}
	ALBEDO = col;
}
