// Buffer C — motion. iChannel0 = A (Body), iChannel1 = C (itself, last frame).
// r = eased Body, g = last frame's eased Body, b = extremity weight (thin parts 1, torso 0),
// a at texel (0,0) = seconds the room has been empty (clamped at EMPTY_CLAMP_S), 0 elsewhere.

void mainImage(out vec4 o, in vec2 f) {
    vec2 uv  = f / iResolution.xy;
    float A  = iResolution.x / iResolution.y;
    float raw = texture(iChannel0, uv).r;
    vec4 prev = texelFetch(iChannel1, ivec2(f), 0);
    float k   = 1.0 - exp(-iTimeDelta / BODY_EASE_S);
    float body = iFrame == 0 ? raw : mix(prev.r, raw, k);
    float last = iFrame == 0 ? raw : prev.r;
    float t = 0.0;
    if (ivec2(f) == ivec2(0)) {
        t = iMouse.z > 0.0 ? 0.0 : min(EMPTY_CLAMP_S, prev.a + iTimeDelta);
    }
    o = vec4(body, last, extremity(iChannel0, iChannel1, uv, A), t);
}
