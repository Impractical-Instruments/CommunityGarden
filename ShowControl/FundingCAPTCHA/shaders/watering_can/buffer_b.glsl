// Buffer B — Body memory.  iChannel0 = Buffer A (Body), iChannel1 = Buffer B (itself), iChannel2 = blobs
// .r presence · .g run bottom y (UV) · .b run top y (UV) · .a owner + 0.9 * hold
// A run is the vertical stretch of body through a pixel; a raised arm's run starts at its own lowest point.

float softPresence(vec2 uv) {
    vec2 t = BODY_BLUR_TEXELS / max(iChannelResolution[0].xy, vec2(1.0));
    float s = 0.0;
    for (int y = -1; y <= 1; y++)
        for (int x = -1; x <= 1; x++)
            s += texture(iChannel0, uv + vec2(x, y) * t).r;
    s /= 9.0;
    // Fill depth-dropout holes: a pixel ringed by body counts as body.
    vec2  h = HOLE_FILL_TEXELS / max(iChannelResolution[0].xy, vec2(1.0));
    float ring = 0.0;
    for (int k = 0; k < 8; k++) {
        float a = 0.7853982 * float(k);
        ring += texture(iChannel0, uv + vec2(cos(a), sin(a)) * h).r;
    }
    return max(s, smoothstep(0.45, 0.7, ring / 8.0));
}

// The slot whose live-or-not (non-empty) box contains uv; nearest centre wins. 0 = none.
int ownerAt(vec2 uv) {
    int best = 0;
    float bestD = 1e9;
    for (int k = 0; k < SLOTS; k++) {
        if (isState(recIdn(iChannel2, k).y, S_EMPTY)) continue;
        vec4 b = recBox(iChannel2, k);
        if (uv.x < b.x || uv.x > b.z || uv.y < b.y || uv.y > b.w) continue;
        float d = length(uv - 0.5 * (b.xy + b.zw));
        if (d < bestD) { bestD = d; best = k + 1; }
    }
    return best;
}

// Is this texel body this frame? Decided from last frame's stored texel t alone, so the march below,
// probing its neighbours, judges each exactly as that texel judges itself: every texel of a run then
// finds the same ends, even while the body moves (a rule using this frame's presence can't be
// evaluated at a neighbour, and the two disagreed wherever the body had just arrived or left, tearing
// the plants into rows). The cost is a frame of latency. From BODY_ON, and once body, until below
// BODY_OFF: hysteresis, so a flickering edge holds still. (A held, fading texel isn't body.)
bool fullHold(vec4 t) { return fract(t.a) > floor(0.9 / HOLD_Q) * HOLD_Q - 0.5 * HOLD_Q; }
bool member(vec4 t) {
    bool run = t.g > 0.0 || t.b > 0.0;
    return t.r >= BODY_ON || (fullHold(t) && run && t.r >= BODY_OFF);
}
bool bodyAt(float x, float y) {
    return member(texelFetch(iChannel1, ivec2(min(vec2(x, y) * iResolution.xy, iResolution.xy - 1.0)), 0));
}

// How far the run extends from uv in direction dir (±1, in UV y) while last frame's body continues.
// Every texel of a run must agree on its ends, or the plants tear into rows: the march steps on a
// grid fixed to the screen, so the texels of a run all probe the same points along a ragged edge,
// then bisects the last step to find the edge texel itself.
float march(vec2 uv, float dir) {
    float y = uv.y, off = clamp(uv.y + dir * float(RUN_STEPS + 1) * RUN_STEP_H, 0.0, 1.0);
    float k0 = dir > 0.0 ? floor(uv.y / RUN_STEP_H) : ceil(uv.y / RUN_STEP_H);
    for (int i = 1; i <= RUN_STEPS; i++) {
        float ny = (k0 + dir * float(i)) * RUN_STEP_H;
        if (ny < 0.0 || ny > 1.0) { off = clamp(ny, 0.0, 1.0); break; }
        if (!bodyAt(uv.x, ny)) { off = ny; break; }
        y = ny;
    }
    for (int i = 0; i < RUN_REFINE; i++) {
        float m = 0.5 * (y + off);
        if (bodyAt(uv.x, m)) y = m; else off = m;
    }
    return y;
}

void mainImage(out vec4 o, in vec2 fc) {
    vec2 uv = fc / iResolution.xy;
    vec4 prev = iFrame == 0 ? vec4(0.0) : texelFetch(iChannel1, ivec2(fc), 0);

    float target = softPresence(uv);
    float pres = iFrame == 0 ? target : mix(prev.r, target, 1.0 - exp(-iTimeDelta / PRESENCE_EASE_S));

    float g = 0.0, b = 0.0, a = 0.0;
    // The body has gone from under a person whose track is missing: every texel of theirs lets go this
    // frame, not as its eased presence crosses BODY_OFF (sooner at the edges), so their hold fades in step.
    int   po = bOwner(prev);
    float pst = po > 0 ? recIdn(iChannel2, po - 1).y : S_EMPTY;
    bool  leaving = po > 0 && target < BODY_OFF && !isState(pst, S_TENTATIVE) && !isState(pst, S_CONFIRMED);
    if (!leaving && iFrame > 0 && member(prev)) {
        // Not eased: an eased end has a history per texel, and texels that joined the run at different
        // times would disagree. The hysteresis above already holds a flickering edge still.
        g = march(uv, -1.0);
        b = march(uv, 1.0);
        a = float(ownerAt(uv)) + floor(0.9 / HOLD_Q) * HOLD_Q;
    } else {
        float ph = bHold(prev);
        if (po > 0 && ph > 0.0) {
            // A missing body coasts first: keep its plants until the track is lost, then rewind them away.
            if (!isState(pst, S_TENTATIVE) && !isState(pst, S_CONFIRMED)) {
                // The step is below a half float's resolution at high render rates, so round it
                // stochastically to HOLD_Q: the expected fade is exact at any rate. The offset depends on
                // the frame only, so every texel of a person steps together and their vines don't tear
                // into rows; a golden-ratio sequence, not a hash, so the count of steps stays near exact.
                float f = fract(prev.a);
                float d = 0.9 * iTimeDelta / LEAVE_S;
                f -= floor(d / HOLD_Q + fract(float(iFrame % 4096) * 0.618034)) * HOLD_Q;
                if (f > 0.5 * HOLD_Q) { g = prev.g; b = prev.b; a = float(po) + f; }
            }
        }
    }
    o = vec4(pres, g, b, a);
}
