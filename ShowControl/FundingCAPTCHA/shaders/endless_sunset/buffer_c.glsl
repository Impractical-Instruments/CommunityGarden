// Buffer C — State, in texel (0,0) only.  iChannel0 = Buffer B (Body memory), iChannel1 = Buffer C (itself)
// .r awake 0–1 · .g flail 0–1 · .b clock whole seconds [0, LOOP_S) · .a clock fraction [0, 1)
// The clock is split because buffers are 16-bit float: one channel would lose the fraction.

float ease(float from, float to, float riseS, float fallS) {
    float tau = to > from ? riseS : fallS;
    return mix(from, to, 1.0 - exp(-iTimeDelta / tau));
}

void mainImage(out vec4 o, in vec2 fc) {
    if (any(greaterThan(ivec2(fc), ivec2(0)))) { o = vec4(0.0); return; }
    vec4 prev = iFrame == 0 ? vec4(0.0) : readState(iChannel1);

    float present = 0.0, moving = 0.0;
    for (int y = 0; y < 18; y++)
        for (int x = 0; x < 32; x++) {
            vec4 b = texture(iChannel0, (vec2(x, y) + 0.5) / vec2(32.0, 18.0));
            present += step(0.5, b.r);
            moving  += b.g;
        }
    present /= 576.0;
    moving  /= 576.0;

    float awakeTarget = clamp(present / AWAKE_COVERAGE, 0.0, 1.0);
    float flailTarget = clamp(moving / FLAIL_FULL, 0.0, 1.0) * awakeTarget;
    float awake = ease(prev.r, awakeTarget, AWAKE_RISE_S, AWAKE_FALL_S);
    float flail = ease(prev.g, flailTarget, FLAIL_RISE_S, FLAIL_FALL_S);

    float rate  = mix(RATE_EMPTY, RATE_AWAKE, awake) + RATE_FLAIL_BONUS * flail;
    float frac  = prev.a + iTimeDelta * rate;
    float whole = mod(prev.b + floor(frac), LOOP_S);

    o = vec4(awake, flail, whole, fract(frac));
}
