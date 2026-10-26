// Image — shade the wave height as a lit liquid.  iChannel0 = Body, iChannel1 = Buffer B

vec3 palette(float t) {
    return 0.5 + 0.5 * cos(6.2831 * (vec3(0.0, 0.33, 0.67) + t));
}

void mainImage(out vec4 o, in vec2 fc) {
    vec2 px = 1.0 / iResolution.xy;
    vec2 uv = fc * px;
    float hx = texture(iChannel1, uv + vec2(px.x, 0.0)).r - texture(iChannel1, uv - vec2(px.x, 0.0)).r;
    float hy = texture(iChannel1, uv + vec2(0.0, px.y)).r - texture(iChannel1, uv - vec2(0.0, px.y)).r;
    vec3 n = normalize(vec3(-hx, -hy, 0.08));

    vec3 light = normalize(vec3(0.4, 0.6, 1.0));
    float spec = pow(max(dot(reflect(-light, n), vec3(0.0, 0.0, 1.0)), 0.0), 24.0);
    vec3 base  = palette(0.08 * iTime + 0.3 * uv.x) * 0.25;
    vec3 col   = base * (0.4 + 0.6 * dot(n, light)) + spec;

    // Faint rim so visitors can find themselves.
    vec4 body = texture(iChannel0, uv);
    col += body.r * (0.05 + 0.15 * body.g) * palette(0.08 * iTime + 0.5);

    o = vec4(col, 1.0);
}
