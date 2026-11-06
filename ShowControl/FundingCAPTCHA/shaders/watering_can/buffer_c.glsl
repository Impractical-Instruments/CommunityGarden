// Buffer C — Garden state.  iChannel0 = Buffer B, iChannel1 = Buffer C (itself), iChannel2 = blobs
// Layout: see common.glsl (rows 0–3 garden state and footprints, rows 4+ the near-body grid). Each texel reads the
// previous frame of every other texel; texels that need the same derived value (PERSON and BASE
// both need this frame's base) compute it from the same inputs.

#define BB    iChannel0
#define C     iChannel1
#define BLOBS iChannel2

// The starting value of every texel: "seconds since" counters start long ago.
vec4 initial(ivec2 c) {
    if (c.y == 1) return vec4(0.0, 0.0, T_CLAMP, S_EMPTY);       // BASE
    if (c.y == 2) return vec4(0.0, 0.0, 0.0, T_CLAMP);           // GHOST
    if (c.y == 3 && c.x > 0) return vec4(0.0, 0.0, T_CLAMP, 0.0); // FOOT: none
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

// A new track's feet: presence-weighted mean x of B across the box, just above its bottom; y = the box bottom.
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

// Presence-weighted mean x of B over [x0, x1], BASE_BAND / 2 above row y (.y: the total weight, in taps).
vec2 feetBand(float x0, float x1, float y) {
    float w = 0.0, wx = 0.0;
    for (int i = 0; i < BASE_TAPS; i++) {
        float x = mix(x0, x1, (float(i) + 0.5) / float(BASE_TAPS));
        float p = texture(BB, vec2(x, y + 0.5 * BASE_BAND)).r;
        w += p; wx += p * x;
    }
    return vec2(w > 1e-3 ? wx / w : 0.5 * (x0 + x1), w);
}

// A tracked person's feet, measured near their last base so that only their own feet count: in a
// window BASE_WIN either side of it (and inside the box), the presence-weighted mean x of the feet
// band. The window then re-centres on that x and measures again (mean shift), so it keeps up with a
// walk but stays on the feet it started on: when the tracker merges a neighbour in, the box swells but
// this doesn't move. y is the box bottom while the window finds feet there; if it doesn't, the bottom
// is a merged neighbour's (nearer the camera), and y is this person's lowest body row in the window:
// the bottom of B's runs through their legs BASE_UP above the last base. The whole box if no body is
// near (they have moved off it faster than the window follows: that's a step).
vec2 baseNear(vec4 box, vec2 last) {
    float hw = BASE_WIN * iResolution.y / iResolution.x;         // screen heights → UV x
    vec2  bRes = iChannelResolution[0].xy;
    float up = min(last.y + BASE_UP, 1.0);
    vec2  base = last;
    for (int n = 0; n < BASE_ITERS; n++) {
        float x0 = max(box.x, base.x - hw), x1 = min(box.z, base.x + hw);
        if (x1 <= x0) return n == 0 ? baseTarget(box) : base;
        vec2 f = feetBand(x0, x1, box.y);
        if (f.y >= BASE_FEET) { base = vec2(f.x, box.y); continue; }
        float lo = 2.0;
        for (int i = 0; i < BASE_TAPS; i++) {
            float x = mix(x0, x1, (float(i) + 0.5) / float(BASE_TAPS));
            vec4  t = texelFetch(BB, ivec2(min(vec2(x, up) * bRes, bRes - 1.0)), 0);
            if (t.r >= BODY_ON && t.b > 0.0) lo = min(lo, t.g);
        }
        if (lo > 1.0) return n == 0 ? baseTarget(box) : base;
        base = vec2(feetBand(x0, x1, lo).x, lo);
    }
    return base;
}

// A neighbour within SPLIT_GAP changed tracker state this frame (it appeared, coasted, came back or
// was lost): the tracker is merging them into slot k's person or splitting them off, and slot k's box
// swells or shrinks with it. That isn't a step: slot k's person re-plants for REPLANT_S.
bool contactChange(int k) {
    vec4 box = recBox(BLOBS, k);
    for (int j = 0; j < SLOTS; j++) {
        vec4 idn = recIdn(BLOBS, j);
        if (j == k || isState(idn.y, S_EMPTY)) continue;
        bool changed = fresh(j) || !isState(cBase(C, j).w, idn.y);
        if (changed && boxGap(box, recBox(BLOBS, j)) <= SPLIT_GAP) return true;
    }
    return false;
}
// BASE .z, seconds since the last step, is negative while re-planting: -(seconds still to go).
bool replanting(int k)   { return contactChange(k) || cBase(C, k).z < 0.0; }
bool walking(float since) { return since >= 0.0 && since < WALK_HOLD_S; }

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
// This frame's BASE for slot k: eased base, seconds since the last step (negative: re-planting),
// record state (for GHOST, and to see a neighbour's state change).
vec4 baseNext(int k, float dt) {
    vec4 idn = recIdn(BLOBS, k);
    if (isState(idn.y, S_EMPTY)) return vec4(0.0, 0.0, T_CLAMP, S_EMPTY);
    if (fresh(k)) return vec4(baseTarget(recBox(BLOBS, k)), T_CLAMP, idn.y);
    vec4 b = cBase(C, k);
    bool rp = replanting(k);
    if (contactChange(k)) b.z = -REPLANT_S;
    // A coasting or lost box drifts without a body under it: hold the base, so a dropped
    // camera frame can't read as a step. Re-planting, the base snaps to the feet (and the spot with it).
    if (seen(idn.y)) {
        vec2 t = baseNear(recBox(BLOBS, k), b.xy);
        b.xy = rp ? t : mix(b.xy, t, 1.0 - exp(-dt / BASE_EASE_S));
    }
    if (rp) b.z = b.z + dt < 0.0 ? b.z + dt : WALK_HOLD_S;      // planted again: not walking
    else    b.z = length(toScreen(b.xy - cPerson(C, k).zw)) > WALK_DIST ? 0.0 : min(b.z + dt, T_CLAMP);
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
    if (b.z == 0.0 || replanting(k)) p.zw = b.xy;                // a step or a re-plant: the new spot is here
    // Tentative and coasting hold their level, but a coasting track the tracker has merged into a
    // neighbour's blob shares that neighbour's walking or not, so merged people grow (or rewind) together.
    float since = b.z;                                           // seconds since the last step
    bool  moves = isState(idn.y, S_CONFIRMED);
    if (isState(idn.y, S_COASTING)) {
        vec4 box = recBox(BLOBS, k);
        since = T_CLAMP;
        for (int j = 0; j < SLOTS; j++) {
            if (j == k || fresh(j) || !isState(recIdn(BLOBS, j).y, S_CONFIRMED)) continue;
            if (boxGap(box, recBox(BLOBS, j)) <= SPLIT_GAP) { moves = true; since = min(since, cBase(C, j).z); }
        }
    }
    if (moves) {
        float grow = p.y < GROW_EARLY ? GROW_EARLY / GROW_EARLY_S : (1.0 - GROW_EARLY) / (GROW_S - GROW_EARLY_S);
        float rate = walking(since) ? -1.0 / REWIND_S : grow;
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
    // must not wipe a ghost someone may still come back to. Replace a ghost only once it can
    // no longer be inherited, or with one at least as grown.
    bool  stronger = g.w >= INHERIT_S || p.y >= g.z;
    if (p.x > 0.5 && gone && stronger) return vec4(p.zw, p.y, 0.0);
    g.w = min(g.w + dt, T_CLAMP);
    return g;
}

// ── FOOT ──────────────────────────────────────────────────────────────────────
// The slot of the walker who drops a footprint this frame, or -1. A seen person who is walking drops one
// where their feet are once they're FOOT_GAP from every live footprint: the first such slot, one a frame
// (another stepping the same frame drops next frame). Only into the ring's head, and only once the
// footprint there has gone, so a live one never pops. The SUN texel (which keeps the head) and every
// FOOT texel compute this from the same last frame, so they agree.
int footDropper() {
    if (cFoot(C, int(cSun(C).z)).z < FOOT_LIFE) return -1;
    for (int k = 0; k < SLOTS; k++) {
        if (!seen(recIdn(BLOBS, k).y) || fresh(k)) continue;
        vec4 b = cBase(C, k);
        if (!walking(b.z)) continue;
        bool clear = true;
        for (int f = 0; f < FOOTPRINTS; f++) {
            vec4 ft = cFoot(C, f);
            if (ft.z < FOOT_LIFE && length(toScreen(ft.xy - b.xy)) < FOOT_GAP) { clear = false; break; }
        }
        if (clear) return k;
    }
    return -1;
}

vec4 footNext(int f, float dt) {
    int k = footDropper();
    if (k >= 0 && f == int(cSun(C).z)) {
        vec2 at = cBase(C, k).xy;
        return vec4(at, 0.0, fract(hash12(at * 1000.0 + float(iFrame % 997)) * 0.999) * 8.0);
    }
    vec4 ft = cFoot(C, f);
    ft.z = min(ft.z + dt, T_CLAMP);
    return ft;
}

// ── NEAR ──────────────────────────────────────────────────────────────────────
// Is there body (or a held shape: anything a vine could grow on) within NEAR_PAD of cell (i, j)?
// Reads this frame's B, so the grid never lags the plants.
float nearNext(ivec2 cell) {
    float aspect = iResolution.x / iResolution.y;
    vec2  lo = vec2(cell) * NEAR_CELL - NEAR_PAD;
    vec2  bRes = iChannelResolution[0].xy;
    for (int y = 0; y < NEAR_TAPS; y++) {
        float sy = lo.y + float(y) * NEAR_STEP;
        if (sy < 0.0 || sy >= 1.0) continue;
        for (int x = 0; x < NEAR_TAPS; x++) {
            float sx = lo.x + float(x) * NEAR_STEP;
            if (sx < 0.0 || sx >= aspect) continue;
            vec4 t = texelFetch(BB, ivec2(vec2(sx / aspect, sy) * bRes), 0);
            if (bOwner(t) > 0 && bHold(t) > 0.0) return 1.0;
        }
    }
    // A footprint's plants reach into the cell (last frame's footprints: a new one starts bare).
    vec2 c0 = vec2(cell) * NEAR_CELL, c1 = c0 + NEAR_CELL;
    for (int f = 0; f < FOOTPRINTS; f++) {
        vec4 ft = cFoot(C, f);
        if (ft.z >= FOOT_LIFE) continue;
        vec2 at = vec2(ft.x * aspect, ft.y);
        if (at.x + FOOT_REACH_X >= c0.x && at.x - FOOT_REACH_X <= c1.x
            && at.y + FOOT_REACH_UP >= c0.y && at.y - FOOT_REACH_DOWN <= c1.y) return 1.0;
    }
    return 0.0;
}

// ── SUN ───────────────────────────────────────────────────────────────────────
vec4 sunNext(float dt, vec2 fc) {
    float raw = 0.0;
    for (int k = 0; k < SLOTS; k++) {
        if (live(recIdn(BLOBS, k).y) && !fresh(k)) raw += cPerson(C, k).y;
        vec4 g = cGhost(C, k);
        raw += g.z * max(0.0, 1.0 - g.w / LEAVE_S);
    }
    float lvl = cSun(C).x;
    float step = (clamp(raw / SUN_FULL, 0.0, 1.0) - lvl) * (1.0 - exp(-dt / SUN_EASE_S));
    // Near the target the step is below a half float's resolution and the easing would stall short of
    // full: round it stochastically to GROW_Q, as growth is, so the expected easing is exact.
    float h = hash12(fc + vec2(113.0, 57.0) * float(iFrame % 997));
    lvl = clamp(lvl + sign(step) * floor(abs(step) / GROW_Q + h) * GROW_Q, 0.0, 1.0);
    float head = cSun(C).z;                                     // the footprint ring's head moves on past a drop
    if (footDropper() >= 0) head = mod(head + 1.0, float(FOOTPRINTS));
    return vec4(lvl, raw, head, 0.0);
}

void mainImage(out vec4 o, in vec2 fc) {
    ivec2 c = ivec2(fc);
    o = vec4(0.0);
    if (c.y >= 4) {                                              // the near-body grid
        if (c.y < 4 + NEAR_ROWS && float(c.x) * NEAR_CELL < iResolution.x / iResolution.y) o.x = nearNext(c - ivec2(0, 4));
        return;
    }
    if (c.y == 3 ? c.x > FOOTPRINTS : c.x >= SLOTS) return;
    if (iFrame == 0) { o = initial(c); return; }
    float dt = clamp(iTimeDelta, 0.0, T_CLAMP);

    if      (c.y == 0) o = personNext(c.x, dt, fc);
    else if (c.y == 1) o = baseNext(c.x, dt);
    else if (c.y == 2) o = ghostNext(c.x, dt);
    else if (c.x == 0) o = sunNext(dt, fc);
    else               o = footNext(c.x - 1, dt);
}
