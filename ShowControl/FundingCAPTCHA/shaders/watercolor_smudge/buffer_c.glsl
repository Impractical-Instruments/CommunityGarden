// Buffer C — motion. iChannel0 = A (Body), iChannel1 = C (itself, last frame).
// r = eased soft Body, g = last frame's eased Body, b = extremity weight (thin parts 1, torso 0)
// measured on last frame's eased Body,
// a at texel (0,0) = seconds the room has been empty (clamped at EMPTY_CLAMP_S), 0 elsewhere.

// The Body averaged over a small disc: a soft edge about 2 × BODY_SOFT wide.
float softBody(vec2 uv, float A) {
    float s = texture(iChannel0, uv).r;
    for (int i = 0; i < 8; i++) {
        float a = float(i) * 0.7853982;
        vec2 d = vec2(cos(a), sin(a)) / vec2(A, 1.0) * BODY_SOFT;
        s += texture(iChannel0, uv + d * 0.5).r + texture(iChannel0, uv + d).r;
    }
    return s / 17.0;
}

void mainImage(out vec4 o, in vec2 f) {
    vec2 uv  = f / iResolution.xy;
    float A  = iResolution.x / iResolution.y;
    float raw = softBody(uv, A);
    vec4 prev = texelFetch(iChannel1, ivec2(f), 0);
    float k   = 1.0 - exp(-iTimeDelta / BODY_EASE_S);
    float body = iFrame == 0 ? raw : mix(prev.r, raw, k);
    float last = iFrame == 0 ? raw : prev.r;
    float t = 0.0;
    if (ivec2(f) == ivec2(0)) {
        t = iMouse.z > 0.0 ? 0.0 : min(EMPTY_CLAMP_S, prev.a + iTimeDelta);
    }
    o = vec4(body, last, extremity(iChannel1, uv, A), t);
}
