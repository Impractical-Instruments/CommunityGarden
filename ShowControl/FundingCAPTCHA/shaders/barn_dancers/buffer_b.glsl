// Buffer B — Dancer state. iChannel0 = this buffer, iChannel1 = blobs.
// Layout: see common.glsl. Each texel reads the previous frame of every other texel.

#define B     iChannel0
#define BLOBS iChannel1

// Slot k's barn still has its visitor: the record carries the id the barn rose
// for and the tracker sees them (or is coasting through a dropped frame).
bool present(int k) {
    vec4 idn = recIdn(BLOBS, k);
    float id = bDancer(B, k).w;
    return id > 0.5 && abs(idn.x - id) < 0.5
        && (isState(idn.y, S_CONFIRMED) || isState(idn.y, S_COASTING));
}
// The barn finishes sinking this frame and frees its slot. DANCER and STAGE
// both ask, on the same inputs, so they agree.
bool gone(int k, float dt) {
    return !present(k) && bStage(B, k).y + dt / EXIT_S >= 1.0;
}

// ── DANCER ────────────────────────────────────────────────────────────────────
vec4 dancerNext(int k, float dt) {
    vec4 d = bDancer(B, k), idn = recIdn(BLOBS, k), mot = recMot(BLOBS, k);
    if (d.w < 0.5)                                         // no barn: one rises for a confirmed visitor
        return isState(idn.y, S_CONFIRMED) ? vec4(mot.x, idn.w, 0.0, idn.x) : vec4(0.0);
    if (gone(k, dt)) return vec4(0.0);

    float target = 0.0;                                    // energy: travel plus how fast the box changes size
    if (present(k)) {
        float ease = 1.0 - exp(-dt / FOLLOW_S);
        d.x += (mot.x - d.x) * ease;
        d.y += (idn.w - d.y) * ease;
        if (isState(idn.y, S_CONFIRMED)) {
            vec4  box = recBox(BLOBS, k), prev = bPrev(B, k);
            vec2  sz = toScreen(box.zw - box.xy), psz = toScreen(prev.zw - prev.xy);
            float grow = abs((sz.x + sz.y) - (psz.x + psz.y)) / BOX_EMA_S;
            target = clamp(length(toScreen(mot.zw)) / SPEED_FULL + grow / SIZE_FULL - MOTION_FLOOR, 0.0, 1.0);
        }
    }
    d.z += (target - d.z) * (1.0 - exp(-dt / (target > d.z ? ENERGY_RISE_S : ENERGY_FALL_S)));
    return d;
}

// ── STAGE ─────────────────────────────────────────────────────────────────────
vec4 stageNext(int k, float dt) {
    if (bDancer(B, k).w < 0.5 || gone(k, dt)) return vec4(0.0);
    vec4 s = bStage(B, k);
    float vx = 0.0;
    if (present(k)) {
        s.x = min(s.x + dt / ENTER_S, 1.0);
        vx  = toScreen(recMot(BLOBS, k).zw).x;
    } else {
        s.y += dt / EXIT_S;
    }
    s.z += (vx - s.z) * (1.0 - exp(-dt / FOLLOW_S));
    return s;
}

// ── PREV ──────────────────────────────────────────────────────────────────────
vec4 prevNext(int k, float dt) {
    vec4 box = recBox(BLOBS, k);
    if (!present(k)) return box;
    vec4 p = bPrev(B, k);
    return p + (box - p) * (1.0 - exp(-dt / BOX_EMA_S));
}

// ── ORDER: slots sorted far to near, so nearer barns are drawn over farther ones ──
float depthKey(int k) { vec4 d = bDancer(B, k); return d.w > 0.5 ? d.y : -1.0; }
vec4 orderNext(int r) {
    for (int j = 0; j < SLOTS; j++) {
        float kj = depthKey(j);
        int rank = 0;
        for (int i = 0; i < SLOTS; i++) {
            float ki = depthKey(i);
            if (ki < kj || (ki == kj && i < j)) rank++;
        }
        if (rank == r) return vec4(float(j), 0.0, 0.0, 0.0);
    }
    return vec4(float(r), 0.0, 0.0, 0.0);
}

// ── BEAT: one phase for the troupe; it runs faster the more anyone moves ──────
vec4 beatNext(float dt) {
    vec4 b = bBeat(B);
    float most = 0.0;
    for (int k = 0; k < SLOTS; k++) most = max(most, bDancer(B, k).z);
    b.y += (most - b.y) * (1.0 - exp(-dt / TEMPO_EASE_S));
    b.x  = fract(b.x + dt * (1.0 + TEMPO_GAIN * b.y) / CYCLE_S);
    return vec4(b.xy, 0.0, 0.0);
}

void mainImage(out vec4 o, in vec2 fragCoord) {
    ivec2 c = ivec2(fragCoord);
    o = vec4(0.0);
    if (iFrame == 0 || c.y > 4 || c.x >= SLOTS) return;
    float dt = min(iTimeDelta, DT_MAX);
    if      (c.y == 0) o = dancerNext(c.x, dt);
    else if (c.y == 1) o = stageNext(c.x, dt);
    else if (c.y == 2) o = prevNext(c.x, dt);
    else if (c.y == 3) o = orderNext(c.x);
    else if (c.x == 0) o = beatNext(dt);
}
