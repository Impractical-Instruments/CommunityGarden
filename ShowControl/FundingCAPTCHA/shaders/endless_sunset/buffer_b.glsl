// Buffer B — Body memory.  iChannel0 = Buffer A (Body), iChannel1 = Buffer B (itself)
// .r soft presence · .g movement trail · .b ripple field (1 inside, ~exp(-dist/RIPPLE_FALLOFF) out)
// .a running average of soft presence (what "still" looks like, for movement)

float softPresence(vec2 uv) {
    vec2 t = BODY_BLUR_TEXELS / max(iChannelResolution[0].xy, vec2(1.0));
    float s = 0.0;
    for (int y = -1; y <= 1; y++)
        for (int x = -1; x <= 1; x++)
            s += texture(iChannel0, uv + vec2(x, y) * t).r;
    s /= 9.0;

    // Fill depth-dropout holes: a pixel ringed by body counts as body. Lone specks and real
    // edges aren't ringed, so they keep their shape.
    vec2  h = HOLE_FILL_TEXELS / max(iChannelResolution[0].xy, vec2(1.0));
    float ring = 0.0;
    for (int k = 0; k < 8; k++) {
        float a = 0.7853982 * float(k);
        ring += texture(iChannel0, uv + vec2(cos(a), sin(a)) * h).r;
    }
    return max(s, smoothstep(0.45, 0.7, ring / 8.0));
}

void mainImage(out vec4 o, in vec2 fc) {
    vec2 px = 1.0 / iResolution.xy;
    vec2 uv = fc * px;
    vec4 prev = iFrame == 0 ? vec4(0.0) : texture(iChannel1, uv);

    float soft = softPresence(uv);
    float diff = abs(soft - prev.a);

    // Compared against a short running average, not the last frame: edge flicker toggles
    // around the average, real movement walks away from it.
    float motion = max(diff - MOTION_FLOOR, 0.0) / (1.0 - MOTION_FLOOR);
    float trail  = max(prev.g * exp(-iTimeDelta / MOTION_DECAY_S), motion);
    float avg    = iFrame == 0 ? soft : mix(prev.a, soft, 1.0 - exp(-iTimeDelta / MOTION_AVG_S));

    // Spread the ripple field outward a few px per frame. Max (not average) makes it a true
    // distance: .b = exp(-dist / RIPPLE_FALLOFF). Averaging leaks and decays ~10x faster.
    // The image pass smooths it before using it.
    float stepH = RIPPLE_STEP_PX / iResolution.y;
    float keep  = exp(-stepH / RIPPLE_FALLOFF);
    float near  = 0.0;
    for (int k = 0; k < 8; k++) {
        float a = 0.7853982 * float(k);
        near = max(near, texture(iChannel1, uv + vec2(cos(a), sin(a)) * RIPPLE_STEP_PX * px).b);
    }
    float field = iFrame == 0 ? soft : max(soft, near * keep);

    o = vec4(soft, trail, field, avg);
}
