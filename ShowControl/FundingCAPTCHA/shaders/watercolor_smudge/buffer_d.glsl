// Buffer D — the canvas: rgb = paint, a = wetness 0–1.
// iChannel0 = D (itself), iChannel1 = B (original, this frame), iChannel2 = C (motion, this frame).
// Thin, moving Body edges push paint the way they move (semi-Lagrangian advection), in finger
// streaks, mixing like pigment. Heals toward the original once the room has been empty a while.

vec2 bodyPair(vec2 uv) { return texture(iChannel2, uv).rg; }

// 0 when nearby Body change balances (something moved), 1 when it's one-sided (appeared,
// vanished, flickered). Sampled on the extremity rings, so it spans a limb and its travel.
float imbalance(vec2 uv, float A) {
    vec4 m = texture(iChannel2, uv);
    float net = m.r - m.g, total = abs(net);
    for (int i = 0; i < 12; i++) {
        float a = float(i) * 0.5235988;
        vec2 d = vec2(cos(a), sin(a)) / vec2(A, 1.0);
        vec4 m1 = texture(iChannel2, uv + d * RING_R1), m2 = texture(iChannel2, uv + d * RING_R2);
        net   += (m1.r - m1.g) + (m2.r - m2.g);
        total += abs(m1.r - m1.g) + abs(m2.r - m2.g);
    }
    return abs(net) / (total + 1e-4);
}

void mainImage(out vec4 o, in vec2 f) {
    // Paint never goes below PAINT_FLOOR, so an exactly-zero centre means "buffer cleared" (a
    // Shadertoy resize), never black paint.
    vec3 ctr = texelFetch(iChannel0, ivec2(iResolution.xy * 0.5), 0).rgb;
    if (iFrame == 0 || ctr == vec3(0.0)) {
        o = vec4(max(texelFetch(iChannel1, ivec2(f), 0).rgb, vec3(PAINT_FLOOR)), 0.0);
        return;
    }
    vec2 uv = f / iResolution.xy;
    float A = iResolution.x / iResolution.y;
    float dt = max(iTimeDelta, 1e-3);

    // Normal flow from this and last frame's eased Body, in screen heights per second.
    vec2 ox = vec2(FLOW_TAP / A, 0.0), oy = vec2(0.0, FLOW_TAP);
    vec2 px1 = bodyPair(uv + ox), px0 = bodyPair(uv - ox), py1 = bodyPair(uv + oy), py0 = bodyPair(uv - oy);
    vec2 g = vec2((px1.x + px1.y) - (px0.x + px0.y), (py1.x + py1.y) - (py0.x + py0.y)) / (4.0 * FLOW_TAP);
    vec4 m = texture(iChannel2, uv);
    vec2 v = -(m.r - m.g) / dt * g / (dot(g, g) + FLOW_EPS);
    float sp = length(v);
    if (sp > FLOW_MAX) v *= FLOW_MAX / sp;
    v *= smoothstep(MIN_FLOW, 2.0 * MIN_FLOW, sp);       // dead zone: creep isn't movement
    if (sp > 0.0) v *= 1.0 - smoothstep(BALANCE_LO, BALANCE_HI, imbalance(uv, A));

    // Only thin parts smear, and never on or out of the paper border.
    vec4 orig = texture(iChannel1, uv);
    float upstream = texture(iChannel1, uv - v * 0.08 / vec2(A, 1.0)).a;
    vec2 vel = v * m.b * orig.a * upstream;
    float vs = length(vel);
    vec2 perp = vs > 1e-4 ? vec2(-vel.y, vel.x) / vs : vec2(1.0, 0.0);
    float streak = STREAK_BASE + STREAK_AMP * vn(vec2(dot(uv * vec2(A, 1.0), perp) * STREAK_FREQ, 3.0));
    vec2 src = uv - vel * streak * SMEAR_STRENGTH * dt / vec2(A, 1.0);
    vec4 c = texture(iChannel0, src);

    // Pigment-like mixing: geometric mean of neighbours, where moving or still wet.
    float mv = smoothstep(0.02, 0.3, vs);
    vec2 mx = vec2(MIX_TAP / A, 0.0), my = vec2(0.0, MIX_TAP);
    vec3 L = log(max(texture(iChannel0, src + mx).rgb, 0.02)) + log(max(texture(iChannel0, src - mx).rgb, 0.02))
           + log(max(texture(iChannel0, src + my).rgb, 0.02)) + log(max(texture(iChannel0, src - my).rgb, 0.02));
    c.rgb = mix(c.rgb, exp(L * 0.25), clamp(mv * MIX_MOVE + c.a * MIX_WET, 0.0, 0.6) * orig.a);

    float wet = max(c.a * exp(-dt * WET_DECAY), mv);

    float empty = texelFetch(iChannel2, ivec2(0), 0).a;
    if (empty > HEAL_DELAY_S) {
        vec3 d = orig.rgb - c.rgb;                       // exp ease, with a linear floor for 16-bit
        vec3 step = max(abs(d) * (1.0 - exp(-dt * 3.0 / HEAL_TIME_S)), vec3(HEAL_FLOOR * dt));
        c.rgb += sign(d) * min(abs(d), step);
    } else {
        c.rgb = mix(c.rgb, orig.rgb, 1.0 - exp(-dt * PRESENT_HEAL));
    }
    o = vec4(max(c.rgb, vec3(PAINT_FLOOR)), wet);
}
