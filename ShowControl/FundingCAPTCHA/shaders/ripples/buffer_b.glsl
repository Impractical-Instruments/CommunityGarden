// Buffer B — wave simulation.  iChannel0 = Buffer A (Body), iChannel1 = Buffer B (itself)
// .r = height now, .g = height last frame.

const float DAMPING = 0.985;

void mainImage(out vec4 o, in vec2 fc) {
    vec2 px = 1.0 / iResolution.xy;
    vec2 uv = fc * px;
    vec2 here = texture(iChannel1, uv).rg;
    float n = texture(iChannel1, uv + vec2(0.0,  px.y)).r;
    float s = texture(iChannel1, uv - vec2(0.0,  px.y)).r;
    float e = texture(iChannel1, uv + vec2(px.x, 0.0)).r;
    float w = texture(iChannel1, uv - vec2(px.x, 0.0)).r;

    float h = ((n + s + e + w) * 0.5 - here.g) * DAMPING;

    // Bodies press the surface down; closer bodies press harder.
    vec4 body = texture(iChannel0, uv);
    h = mix(h, -0.6 - body.g, body.r * 0.5);

    o = vec4(h, here.r, 0.0, 1.0);
}
