// Image — the logo on black, leaning into its motion. Drawn in screen heights on both
// axes, so it stays round whatever the screen's aspect.
// iChannel0 = Buffer B, iChannel1 = image (the logo; images/logo.png).

#define B    iChannel0
#define LOGO iChannel1

// Procedural stand-in for when images/ is empty: a white disc, black ring, yellow bulb.
vec4 standIn(vec2 q) {                          // q: logo-local, -1 … 1
    float r = length(q);
    if (r > 1.0) return vec4(0.0);
    vec3 col = r > 0.68 ? vec3(1.0) : vec3(0.0);
    if (length(q - vec2(0.0, 0.12)) < 0.2) col = vec3(1.0, 0.94, 0.0);
    return vec4(col, 1.0 - smoothstep(0.98, 1.0, r));
}

vec4 logoAt(vec2 q) {                           // q: logo-local, -1 … 1
    if (iChannelResolution[1].x == 0.0) return standIn(q);
    vec2 uv = q * 0.5 + 0.5;
    if (any(lessThan(uv, vec2(0.0))) || any(greaterThan(uv, vec2(1.0)))) return vec4(0.0);
    return texture(LOGO, uv);
}

mat2 rot(float a) { float c = cos(a), s = sin(a); return mat2(c, s, -s, c); }

void mainImage(out vec4 o, in vec2 fc) {
    vec2  p   = fc / iResolution.y;             // screen heights
    vec4  g   = bLogo(B);
    vec2  at  = g.xy + vec2(0.0, BOB * sin(iTime * 1.3));
    float ang = clamp(-g.z * TILT, -TILT_MAX, TILT_MAX);
    mat2  R   = rot(-ang);

    vec3 col = BG;

    // The logo, 4 taps per pixel so its lettering doesn't shimmer when small.
    float px = 1.0 / (iResolution.y * RADIUS);  // one pixel in logo-local units
    vec4 lg = vec4(0.0);
    for (int i = 0; i < 4; i++) {
        vec2 off = (vec2(i & 1, i >> 1) - 0.5) * 0.5 * px;
        vec4 t = logoAt(R * ((p - at) / RADIUS) + off);
        lg += vec4(t.rgb * t.a, t.a);
    }
    lg *= 0.25;
    col = col * (1.0 - lg.a) + lg.rgb;
    o = vec4(col, 1.0);
}
