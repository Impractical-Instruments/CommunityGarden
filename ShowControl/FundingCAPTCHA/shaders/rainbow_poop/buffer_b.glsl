// Buffer B — poops and splats. iChannel0 = Body (A), iChannel1 = this buffer, iChannel2 = blobs.
// Layout: see common.glsl. Each texel reads the previous frame of every other texel; texels that
// depend on the same event (a drop, a hit) recompute it from the same inputs.
// Positions are worked in screen heights (sh) and stored as UV.

#define BODY  iChannel0
#define B     iChannel1
#define BLOBS iChannel2

// 0–1, per frame: the rounding offset for tick(). A golden-ratio (Weyl) sequence, not a random
// hash: its running sum stays within about one AGE_Q of exact, where independent random
// offsets wander (≈ ±0.17 s over 15 s at 30 fps).
float DITHER;

// x + dt, kept in multiples of AGE_Q (see common.glsl) and clamped at T_CLAMP.
float tick(float x, float dt) { return min(x + floor(dt / AGE_Q + DITHER) * AGE_Q, T_CLAMP); }
float quant(float x) { return floor(x / AGE_Q + 0.5) * AGE_Q; }

// ── Who is there ──────────────────────────────────────────────────────────────
// The record in slot k carries a different person than SLOT k remembers (or none).
bool isFresh(int k) {
    vec4 idn = recIdn(BLOBS, k);
    return isState(idn.y, S_EMPTY) || abs(idn.x - sSlot(B, k).x) > 0.5;
}

vec4 initial(ivec2 c) {
    if (c.y == 0 && c.x < SLOTS)          return vec4(0.0, FIRST_BOMB_S, 0.0, 0.0);   // SLOT
    if (c.y == 4 && c.x < SLOTS * SPLATS) return vec4(0.0, 0.0, T_CLAMP, 0.0);        // SPLAT
    if (c.y == 5 && c.x < GROUNDS)        return vec4(0.0, 0.0, T_CLAMP, 0.0);        // GROUND
    return vec4(0.0);
}

// ── Dropping ──────────────────────────────────────────────────────────────────
// Slot k's person is due a poop this frame: confirmed, overdue, and theirs isn't still falling.
bool drops(int k) {
    return !isFresh(k) && isState(recIdn(BLOBS, k).y, S_CONFIRMED)
        && sSlot(B, k).y <= 0.0 && sDrop(B, k).x < 0.5;
}

// Where to drop it (UV x): over their head, ahead of them by the time it takes to fall there.
float dropX(int k) {
    vec4  box = recBox(BLOBS, k);
    float fall = max(SPAWN_Y - box.w, 0.0) / FALL_SPEED;
    float cx = toScreen(vec2((box.x + box.z) * 0.5, 0.0)).x;
    float halfw = 0.5 * toScreen(vec2(box.z - box.x, 0.0)).x;
    float lead = clamp(toScreen(recMot(BLOBS, k).zw).x * fall, -LEAD_MAX, LEAD_MAX);
    float aim = 2.0 * hash11(recIdn(BLOBS, k).x * 3.7 + iTime * 1.3) - 1.0;
    return clamp(toUv(vec2(cx + aim * AIM_SPREAD * halfw + lead, 0.0)).x, 0.02, 0.98);   // always seen falling
}

// The falling poop's position (sh): a steady fall with a sway about its sway centre.
vec2 poopAt(vec4 poop, float age) {
    vec2 c = toScreen(poop.xy);
    return vec2(c.x + SWAY * sin(age * SWAY_W + poop.z), c.y);
}

// The tracked person whose box holds `uv`, preferring `prefer`; −1 if none.
int slotAt(vec2 uv, int prefer) {
    const float M = 0.02;                                   // boxes ease; allow a little slack
    int found = -1;
    for (int k = 0; k < SLOTS; k++) {
        if (!isHere(recIdn(BLOBS, k).y)) continue;
        vec4 b = recBox(BLOBS, k);
        if (uv.x < b.x - M || uv.x > b.z + M || uv.y < b.y - M || uv.y > b.w + M) continue;
        if (k == prefer) return k;
        if (found < 0) found = k;
    }
    return found;
}

struct Poop { vec4 poop; vec4 drop; int hitSlot; bool ground; vec2 at; };

// Slot k's poop, one frame on: dropped, falling, landed on someone, or landed on the floor.
Poop poopStep(int k, float dt) {
    Poop o;
    o.poop = sPoop(B, k); o.drop = sDrop(B, k); o.hitSlot = -1; o.ground = false; o.at = vec2(0.0);
    if (drops(k)) {
        o.poop = vec4(dropX(k), SPAWN_Y, 6.2832 * hash11(iTime * 2.9 + float(k)), 0.0);
        o.drop = vec4(1.0, recBox(BLOBS, k).y, 0.0, 0.0);
        return o;
    }
    if (o.drop.x < 0.5) return o;                           // nothing falling

    float h = dt / float(FALL_STEPS), age = o.drop.w;
    for (int s = 0; s < FALL_STEPS; s++) {
        o.poop.y -= FALL_SPEED * h;                         // UV y is sh
        age += h;
        vec2 uv = toUv(poopAt(o.poop, age));
        bool onScreen = uv.x > 0.0 && uv.x < 1.0 && uv.y > 0.0 && uv.y < 1.0;
        if (onScreen && texture(BODY, uv).r > 0.5) {
            int m = slotAt(uv, k);
            if (m >= 0) { o.hitSlot = m; o.at = uv; o.poop = vec4(0.0); o.drop = vec4(0.0); return o; }
        }
        if (uv.y <= o.drop.y) {
            o.ground = uv.x > -0.05 && uv.x < 1.05;
            o.at = vec2(uv.x, o.drop.y); o.poop = vec4(0.0); o.drop = vec4(0.0); return o;
        }
    }
    o.drop.w = min(age, T_CLAMP);
    return o;
}

// ── Per person ────────────────────────────────────────────────────────────────
vec4 slotNext(int k, float dt) {
    vec4 idn = recIdn(BLOBS, k);
    float here = isHere(idn.y) ? 1.0 : 0.0;
    if (isFresh(k))
        return vec4(isState(idn.y, S_EMPTY) ? 0.0 : idn.x, quant(FIRST_BOMB_S + FIRST_JITTER * hash11(idn.x * 1.37)), here, 0.0);
    vec4 s = sSlot(B, k);
    if (drops(k)) s.y = quant(BOMB_EVERY_S + BOMB_JITTER_S * (2.0 * hash11(iTime * 7.7 + float(k)) - 1.0));
    else if (isState(idn.y, S_CONFIRMED)) s.y = max(-tick(-s.y, dt), -10.0);
    s.z = here > 0.5 ? 1.0 : max(s.z - dt / LEAVE_FADE_S, 0.0);
    return s;
}

// Box top-centre (UV) and height (sh), low-passed so splats ride smoothly.
vec4 anchorNext(int k, float dt) {
    vec4 box = recBox(BLOBS, k);
    vec4 want = vec4((box.x + box.z) * 0.5, box.w, box.w - box.y, 0.0);
    if (isFresh(k)) return want;
    if (!isHere(recIdn(BLOBS, k).y)) return sAnchor(B, k);  // lost: hold where they were
    return mix(sAnchor(B, k), want, 1.0 - exp(-dt / ANCHOR_EMA_S));
}

vec4 splatNext(int k, int j, float dt) {
    const vec4 DEAD = vec4(0.0, 0.0, T_CLAMP, 0.0);
    bool fresh = isFresh(k);
    for (int i = 0; i < SLOTS; i++) {                       // any person's poop can land on k
        Poop p = poopStep(i, dt);
        if (p.hitSlot != k) continue;
        if (j > 0) {                                        // shift the ring down
            if (fresh) return DEAD;
            vec4 s = sSplat(B, k, j - 1);
            s.z = tick(s.z, dt);
            return s;
        }
        vec4 an = anchorNext(k, dt);
        vec2 q  = (toScreen(p.at) - toScreen(an.xy)) / max(an.z, 0.05);
        float seed = hash11(iTime * 13.7 + float(k) * 3.1 + float(i));
        return vec4(q.x, q.y - SPLAT_SINK - SINK_SPREAD * hash11(seed * 91.0), 0.0, seed);
    }
    if (fresh) return DEAD;
    vec4 s = sSplat(B, k, j);
    s.z = tick(s.z, dt);
    return s;
}

vec4 groundNext(int j, float dt) {
    for (int i = 0; i < SLOTS; i++) {
        Poop p = poopStep(i, dt);
        if (!p.ground) continue;
        if (j == 0) return vec4(p.at, 0.0, hash11(iTime * 5.3 + float(i)));
        vec4 g = sGround(B, j - 1);
        g.z = tick(g.z, dt);
        return g;
    }
    vec4 g = sGround(B, j);
    g.z = tick(g.z, dt);
    return g;
}

void mainImage(out vec4 o, in vec2 fc) {
    ivec2 c = ivec2(fc);
    o = vec4(0.0);
    if (c.y > 5) return;
    if (iFrame == 0) { o = initial(c); return; }
    float dt = clamp(iTimeDelta, 1e-3, DT_MAX);
    DITHER = float((uint(iFrame) * 2654435769u) >> 8u) / 16777216.0;   // fract(iFrame · φ), exact in integers

    if      (c.y == 0 && c.x < SLOTS) o = slotNext(c.x, dt);
    else if (c.y == 1 && c.x < SLOTS) o = anchorNext(c.x, dt);
    else if (c.y >= 2 && c.y <= 3 && c.x < SLOTS) {
        Poop p = poopStep(c.x, dt);
        o = c.y == 2 ? p.poop : p.drop;
    }
    else if (c.y == 4 && c.x < SLOTS * SPLATS) o = splatNext(c.x / SPLATS, c.x % SPLATS, dt);
    else if (c.y == 5 && c.x < GROUNDS)        o = groundNext(c.x, dt);
}
