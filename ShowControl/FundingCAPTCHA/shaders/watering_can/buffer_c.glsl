// Buffer C — Garden state.  iChannel0 = Buffer B, iChannel1 = Buffer C (itself), iChannel2 = blobs
// Layout: see common.glsl. Each texel reads the previous frame of every other texel; texels that
// need the same derived value (PERSON and BASE both need this frame's base) compute it from the same inputs.

#define BB    iChannel0
#define C     iChannel1
#define BLOBS iChannel2

// The starting value of every texel: "seconds since" counters start long ago.
vec4 initial(ivec2 c) {
    if (c.y == 1) return vec4(0.0, 0.0, T_CLAMP, S_EMPTY);       // BASE
    if (c.y == 2) return vec4(0.0, 0.0, 0.0, T_CLAMP);           // GHOST
    return vec4(0.0);
}

// The record in slot k carries a different person than PERSON k remembers (or none).
bool fresh(int k) {
    vec4 idn = recIdn(BLOBS, k);
    return isState(idn.y, S_EMPTY) || abs(idn.x - cPerson(C, k).x) > 0.5;
}
bool live(float st) { return isState(st, S_TENTATIVE) || isState(st, S_CONFIRMED) || isState(st, S_COASTING); }
// The box follows a real detection (a coasting or lost box only drifts on its last velocity).
bool seen(float st) { return isState(st, S_TENTATIVE) || isState(st, S_CONFIRMED); }

// The feet: presence-weighted mean x of B across the box, just above its bottom; y = the box bottom.
vec2 baseTarget(vec4 box) {
    float y = box.y + 0.5 * BASE_BAND;                           // screen heights = UV in y
    float w = 0.0, wx = 0.0;
    for (int i = 0; i < BASE_TAPS; i++) {
        float x = mix(box.x, box.z, (float(i) + 0.5) / float(BASE_TAPS));
        float p = texture(BB, vec2(x, y)).r;
        w += p; wx += p * x;
    }
    return vec2(w > 1e-3 ? wx / w : 0.5 * (box.x + box.z), box.y);
}

// Gap between two boxes, in screen heights (0 when they overlap).
float boxGap(vec4 a, vec4 b) {
    vec2 d = max(vec2(0.0), max(a.xy - b.zw, b.xy - a.zw));
    return length(toScreen(d));
}

// Growth a new track at `base` starts from: a recent ghost standing there, or a live
// neighbour its box overlaps or all but touches (a split, a merge, or a part of a planted
// person). A newcomer further away starts bare, so nobody pops into bloom on arrival.
float inherit(int k, vec2 base) {
    vec4 box = recBox(BLOBS, k);
    float g = 0.0;
    for (int j = 0; j < SLOTS; j++) {
        vec4 gh = cGhost(C, j);
        if (gh.w < INHERIT_S && length(toScreen(gh.xy - base)) < INHERIT_DIST) g = max(g, gh.z);
        if (j == k || fresh(j) || !live(recIdn(BLOBS, j).y)) continue;
        if (boxGap(box, recBox(BLOBS, j)) <= SPLIT_GAP) g = max(g, cPerson(C, j).y);
    }
    return g;
}

// ── BASE ──────────────────────────────────────────────────────────────────────
// This frame's BASE for slot k: eased base, seconds since the last step, record state (for GHOST).
vec4 baseNext(int k, float dt) {
    vec4 idn = recIdn(BLOBS, k);
    if (isState(idn.y, S_EMPTY)) return vec4(0.0, 0.0, T_CLAMP, S_EMPTY);
    if (fresh(k)) return vec4(baseTarget(recBox(BLOBS, k)), T_CLAMP, idn.y);
    vec4 b = cBase(C, k);
    // A coasting or lost box drifts without a body under it: hold the base, so a dropped
    // camera frame can't read as a step.
    if (seen(idn.y)) b.xy = mix(b.xy, baseTarget(recBox(BLOBS, k)), 1.0 - exp(-dt / BASE_EASE_S));
    bool step = length(toScreen(b.xy - cPerson(C, k).zw)) > WALK_DIST;
    b.z = step ? 0.0 : min(b.z + dt, T_CLAMP);
    b.w = idn.y;
    return b;
}

// ── PERSON ────────────────────────────────────────────────────────────────────
vec4 personNext(int k, float dt, vec2 fc) {
    vec4 idn = recIdn(BLOBS, k);
    if (isState(idn.y, S_EMPTY)) return vec4(0.0);
    vec4 b = baseNext(k, dt);
    if (fresh(k)) return vec4(idn.x, inherit(k, b.xy), b.xy);
    vec4 p = cPerson(C, k);
    if (b.z == 0.0) p.zw = b.xy;                                 // a step: the new spot is here
    if (isState(idn.y, S_CONFIRMED)) {                           // tentative and coasting hold their level
        float rate = b.z < WALK_HOLD_S ? -1.0 / REWIND_S : 1.0 / GROW_S;
        // The step is a few half-float ulps: round it stochastically to GROW_Q, so the
        // expected growth is exact at any render rate.
        float h = hash12(fc + vec2(113.0, 57.0) * float(iFrame % 997));
        p.y += sign(rate) * floor(abs(rate) * dt / GROW_Q + h) * GROW_Q;
        p.y = clamp(p.y, 0.0, 1.0);
    }
    return p;
}

// ── GHOST ─────────────────────────────────────────────────────────────────────
// Written once when slot k's person goes: their track is lost, or the slot holds someone else.
vec4 ghostNext(int k, float dt) {
    vec4  p = cPerson(C, k);
    float st = recIdn(BLOBS, k).y, was = cBase(C, k).w;          // was = the record state last frame
    bool  fr = fresh(k);
    bool  gone = !isState(was, S_LOST) && (fr || isState(st, S_LOST));
    vec4  g = cGhost(C, k);
    // The slot is reused as soon as a lost record frees it: a short-lived fragment leaving
    // must not wipe a ghost someone may still come back to. Replace a stale ghost, or one
    // worth less than the leaver (strictly, so a bare fragment never wins).
    bool  stronger = g.w >= INHERIT_S || p.y > g.z * max(0.0, 1.0 - g.w / LEAVE_S);
    if (p.x > 0.5 && gone && stronger) return vec4(p.zw, p.y, 0.0);
    g.w = min(g.w + dt, T_CLAMP);
    return g;
}

// ── SUN ───────────────────────────────────────────────────────────────────────
vec4 sunNext(float dt) {
    float raw = 0.0;
    for (int k = 0; k < SLOTS; k++) {
        if (live(recIdn(BLOBS, k).y) && !fresh(k)) raw += cPerson(C, k).y;
        vec4 g = cGhost(C, k);
        raw += g.z * max(0.0, 1.0 - g.w / LEAVE_S);
    }
    float lvl = cSun(C).x;
    lvl = mix(lvl, clamp(raw / SUN_FULL, 0.0, 1.0), 1.0 - exp(-dt / SUN_EASE_S));
    return vec4(lvl, raw, 0.0, 0.0);
}

void mainImage(out vec4 o, in vec2 fc) {
    ivec2 c = ivec2(fc);
    o = vec4(0.0);
    if (c.y > 3 || c.x >= SLOTS || (c.y == 3 && c.x > 0)) return;
    if (iFrame == 0) { o = initial(c); return; }
    float dt = clamp(iTimeDelta, 0.0, T_CLAMP);

    if      (c.y == 0) o = personNext(c.x, dt, fc);
    else if (c.y == 1) o = baseNext(c.x, dt);
    else if (c.y == 2) o = ghostNext(c.x, dt);
    else               o = sunNext(dt);
}
