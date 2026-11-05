// Buffer B — Bird state. iChannel0 = this buffer, iChannel1 = blobs.
// Layout: see common.glsl. Each texel reads the previous frame of every other texel.

#define B     iChannel0
#define BLOBS iChannel1

// The starting value of every texel: "seconds since" counters start long ago.
vec4 initial(ivec2 c) {
    if (c.y == 2 && c.x < SLOTS)  return vec4(0.0, 0.0, 0.0, T_CLAMP);           // HEAD
    if (c.y == 3 && c.x == 0)     return vec4(0.0, 0.0, T_CLAMP, 0.0);           // ATTN
    if (c.y == 3 && c.x == 1)     return vec4(0.5, 0.5, RET_R_WANDER, 0.0);      // RETICLE
    if (c.y == 3 && c.x == 2)     return vec4(LID_DROWSY, 0.0, 0.5, 0.5);        // MOOD
    if (c.y == 3 && c.x == 3)     return vec4(T_CLAMP, IDLE_BLINK_MIN, 0.0, 0.0);// BLINK
    if (c.y == 3 && c.x == 4)     return vec4(0.5, 0.5, 0.0, 0.0);               // STAMP
    if (c.y == 4 && c.x < SLOTS * PRINTS) return vec4(0.0, 0.0, T_CLAMP, 0.0);   // PRINT
    return vec4(0.0);
}

// The record in slot k carries a different person than SLOT k remembers (or none).
bool isFresh(int k) {
    vec4 idn = recIdn(BLOBS, k);
    return isState(idn.y, S_EMPTY) || abs(idn.x - bSlot(B, k).x) > 0.5;
}

// ── SLOT ──────────────────────────────────────────────────────────────────────
vec4 slotNext(int k, float dt) {
    vec4 idn = recIdn(BLOBS, k);
    if (isFresh(k)) return vec4(isState(idn.y, S_EMPTY) ? 0.0 : idn.x, 0.0, 0.0, 0.0);

    vec4 s = bSlot(B, k);
    bool confirmed = isState(idn.y, S_CONFIRMED);

    // Motion: speed plus how fast the box's size changes, minus the noise floor.
    float target = 0.0;
    if (confirmed) {
        vec4  box = recBox(BLOBS, k), prev = bPrev(B, k);
        float speed = length(toScreen(recMot(BLOBS, k).zw));
        vec2  sz = toScreen(box.zw - box.xy), psz = toScreen(prev.zw - prev.xy);
        float grow = abs((sz.x + sz.y) - (psz.x + psz.y)) / BOX_EMA_S;   // d/dt of the low-passed size
        target = clamp(min(speed / SPEED_FULL, SPEED_CAP) + grow / SIZE_FULL - MOTION_FLOOR, 0.0, 1.0);
    }
    float tau = target > s.y ? MOTION_RISE_S : MOTION_FALL_S;
    s.y += (target - s.y) * (1.0 - exp(-dt / tau));

    // Stamped: the strike named this id (matched on id, so a reused slot is safe).
    vec4 at = bAttn(B);
    if (abs(at.w - s.x) < 0.5 && at.z < STRIKE_ACK_S) s.w = 1.0;

    // Interest: rises with motion while confirmed; tentative, coasting and lost drain.
    // It settles at the motion level, so whoever moves most can win the bird.
    if (confirmed && s.y > MOTION_ON) s.z = min(s.z + dt * INTEREST_GAIN * s.y, max(s.z - dt * INTEREST_DRAIN, s.y));
    else                              s.z -= dt * INTEREST_DRAIN;
    s.z = s.w > 0.5 ? 0.0 : clamp(s.z, 0.0, 1.0);
    return s;
}

// ── Footprints: HEAD and PRINT ────────────────────────────────────────────────
// HEAD and every PRINT texel of slot k evaluate this on the same inputs, so they agree.
// Here, not in Common: toScreen needs iResolution, which Shadertoy's Common can't see.
bool emitsPrint(vec4 head, vec4 idn, vec4 mot, float dt) {
    return isState(idn.y, S_CONFIRMED)
        && length(toScreen(mot.zw)) >= PRINT_MIN_SPEED
        && head.w + dt >= PRINT_EVERY_S;
}
bool emits(int k, float dt) {
    return !isFresh(k) && emitsPrint(bHead(B, k), recIdn(BLOBS, k), recMot(BLOBS, k), dt);
}

vec4 headNext(int k, float dt) {
    if (isFresh(k)) return vec4(0.0, 0.0, 0.0, T_CLAMP);
    vec4 h = bHead(B, k);
    if (emits(k, dt)) {
        vec4 box = recBox(BLOBS, k);
        return vec4((box.x + box.z) * 0.5, box.y, 1.0 - h.z, 0.0);
    }
    h.w = min(h.w + dt, T_CLAMP);
    return h;
}

vec4 printNext(int k, int j, float dt) {
    if (emits(k, dt)) {
        if (j > 0) {
            vec4 p = bPrint(B, k, j - 1);
            p.z = min(p.z + dt, T_CLAMP);
            return p;
        }
        vec4  box = recBox(BLOBS, k);
        vec2  v = toScreen(recMot(BLOBS, k).zw);
        float side = 1.0 - bHead(B, k).z;                    // the side HEAD takes this frame
        vec2  perp = normalize(vec2(-v.y, v.x)) * (side > 0.5 ? 3.0 : -3.0) / 360.0;
        vec2  at = vec2((box.x + box.z) * 0.5, box.y - 3.0 / 360.0)
                 + perp * vec2(iResolution.y / iResolution.x, 1.0);   // screen heights → UV
        return vec4(at, 0.0, atan(v.y, v.x));
    }
    vec4 p = bPrint(B, k, j);
    p.z = min(p.z + dt, T_CLAMP);
    return p;
}

// ── Who is there (all from the previous frame's SLOTs and this frame's records) ──
// Can slot k be the bird's target? Confirmed, unstamped, interesting, and the
// SLOT still holds this record's person.
bool candidate(int k) {
    vec4 s = bSlot(B, k), idn = recIdn(BLOBS, k);
    return isState(idn.y, S_CONFIRMED) && abs(idn.x - s.x) < 0.5 && s.w < 0.5 && s.z > TARGET_MIN;
}
// The current target's blob was missed for a camera frame or two: keep it, so
// mask flicker doesn't hand the bird to a rival (and halve the lock twice).
bool heldTarget(int k) {
    vec4 s = bSlot(B, k), idn = recIdn(BLOBS, k);
    return isState(idn.y, S_COASTING) && abs(idn.x - s.x) < 0.5 && s.w < 0.5;
}
bool present(int k) {
    float st = recIdn(BLOBS, k).y;
    return isState(st, S_TENTATIVE) || isState(st, S_CONFIRMED) || isState(st, S_COASTING);
}
// Present and not yet stamped (a new id in a slot is never stamped).
bool unstampedPresent(int k) {
    return present(k) && (isFresh(k) || bSlot(B, k).w < 0.5);
}
bool anyPresent()   { for (int k = 0; k < SLOTS; k++) if (present(k)) return true; return false; }
bool anyUnstamped() { for (int k = 0; k < SLOTS; k++) if (unstampedPresent(k)) return true; return false; }
// A record carries an id no SLOT holds yet.
bool newId() {
    for (int k = 0; k < SLOTS; k++)
        if (!isState(recIdn(BLOBS, k).y, S_EMPTY) && isFresh(k)) return true;
    return false;
}

// ── ATTN: target, lock, strike ────────────────────────────────────────────────
// Every texel that depends on this frame's attention calls this; same inputs, same answer.
vec4 attnNext(float dt) {
    vec4 at = bAttn(B);
    int cur = int(at.x + 0.5) - 1;

    int best = -1; float bestI = 0.0;
    for (int k = 0; k < SLOTS; k++)
        if (candidate(k) && bSlot(B, k).z > bestI) { best = k; bestI = bSlot(B, k).z; }

    int tgt = best;
    if (cur >= 0 && candidate(cur) && !(best != cur && bestI > bSlot(B, cur).z + TARGET_SWITCH))
        tgt = cur;                                           // keep: no rival beats it by enough
    if (cur >= 0 && heldTarget(cur)) tgt = cur;              // keep through a dropped frame
    float lock = at.y;
    if (tgt >= 0 && tgt != cur && cur >= 0) lock *= SWITCH_KEEP;

    // Lock builds on motion in place: a coasting target and a walker don't add to it.
    float m = tgt >= 0 && !heldTarget(tgt) ? bSlot(B, tgt).y : 0.0;
    m *= tgt >= 0 ? 1.0 - smoothstep(DRIFT_STILL, DRIFT_WALK, length(bDrift(B, tgt).xy)) : 0.0;
    if (tgt >= 0 && m > LOCK_ON) lock += dt * LOCK_RATE * m * m;
    else                           lock -= dt * LOCK_DRAIN;
    lock = clamp(lock, 0.0, 1.0);

    at.z = min(at.z + dt, T_CLAMP);
    if (tgt >= 0 && lock >= 1.0) {                           // strike
        at.z = 0.0;
        at.w = recIdn(BLOBS, tgt).x;
        lock = 0.0;
    }
    return vec4(float(tgt + 1), lock, at.z, at.w);
}
bool struck(vec4 at) { return at.z == 0.0; }
int  target(vec4 at) { return int(at.x + 0.5) - 1; }

// ── STAMP ─────────────────────────────────────────────────────────────────────
vec4 stampNext(vec4 at) {
    vec4 st = bStamp(B);
    for (int k = 0; k < SLOTS; k++) {                        // follow that id's box while it lives
        vec4 idn = recIdn(BLOBS, k);
        if (!isState(idn.y, S_EMPTY) && abs(idn.x - at.w) < 0.5 && at.w > 0.5) {
            vec4 box = recBox(BLOBS, k);
            st.xy = (box.xy + box.zw) * 0.5;
        }
    }
    return st;
}

// ── RETICLE ───────────────────────────────────────────────────────────────────
vec4 reticleNext(vec4 at, float dt) {
    vec4 r = bReticle(B);
    int  tgt = target(at), cur = target(bAttn(B));
    vec2 goal = r.xy; float rad = RET_R_WANDER, alpha = 0.0, k = RET_K_WANDER;
    if (tgt >= 0) {
        vec4 box = recBox(BLOBS, tgt);
        goal  = vec2((box.x + box.z) * 0.5, box.w - 0.3 * (box.w - box.y));
        k     = RET_K_MIN + RET_K_GAIN * bSlot(B, tgt).z;
        rad   = mix(RET_R_LOOSE, RET_R_LOCKED, at.y);
        alpha = 1.0;
    } else if (anyUnstamped()) {
        vec2 anchor = cur >= 0 ? r.xy : bMood(B).zw;          // the anchor is set where the target was lost
        float aspect = iResolution.x / iResolution.y;
        goal = anchor + vec2(vnoise(iTime * WANDER_RATE) * WANDER_X / aspect,
                             vnoise(iTime * WANDER_RATE + 40.0) * WANDER_Y);
        goal = clamp(goal, vec2(60.0 / 360.0 / aspect, 80.0 / 360.0),
                           vec2(1.0 - 60.0 / 360.0 / aspect, 1.0 - 60.0 / 360.0));
        alpha = 0.55;
    }
    r.xy += (goal - r.xy) * (1.0 - exp(-dt * k));
    r.z  += (rad - r.z)   * (1.0 - exp(-dt * RET_K_RADIUS));
    r.w  += (alpha - r.w) * (1.0 - exp(-dt * RET_K_ALPHA));
    return r;
}

// ── MOOD: lids, shiver, wander anchor ─────────────────────────────────────────
vec4 moodNext(vec4 at, float dt) {
    vec4 m = bMood(B);
    float lid;
    if      (at.z < STRIKE_WIDE_S) lid = LID_STRIKE;
    else if (at.z < STRIKE_SMUG_S) lid = LID_SMUG;
    else if (target(at) >= 0)      lid = LID_WIDE;
    else if (anyUnstamped())       lid = LID_SQUINT;
    else if (anyPresent() && bBlink(B).z < ALL_STAMPED_DROWSY_S) lid = LID_SMUG;
    else                           lid = LID_DROWSY + LID_DROOP * sin(iTime * 0.6);
    m.x += (lid - m.x) * (1.0 - exp(-dt * (lid > m.x ? LID_OPEN_RATE : LID_CLOSE_RATE)));

    m.y = newId() ? 1.0 : max(0.0, m.y - dt * SHIVER_DECAY);
    if (target(bAttn(B)) >= 0 && target(at) < 0) m.zw = bReticle(B).xy;
    return m;
}

// ── BLINK ─────────────────────────────────────────────────────────────────────
vec4 blinkNext(vec4 at, float dt) {
    vec4 b = bBlink(B);
    b.x = min(b.x + dt, T_CLAMP);
    if (newId())   b.x = -BLINK_NEW_DELAY;
    if (struck(at)) b.x = -BLINK_STRIKE_DELAY;
    b.y -= dt;
    if (b.y <= 0.0) {
        if (b.x > BLINK_S) b.x = 0.0;                        // idle blink, unless one is due
        b.y = IDLE_BLINK_MIN + IDLE_BLINK_SPAN * hash11(floor(iTime * 10.0));
    }
    b.y = clamp(b.y, 0.0, T_CLAMP);
    b.z = anyPresent() && !anyUnstamped() ? min(b.z + dt, T_CLAMP) : 0.0;
    return b;
}

void mainImage(out vec4 o, in vec2 fc) {
    ivec2 c = ivec2(fc);
    o = vec4(0.0);
    if (c.y > 5) return;
    if (iFrame == 0) { o = initial(c); return; }
    float dt = clamp(iTimeDelta, 1e-3, DT_MAX);

    if (c.x < SLOTS && c.y == 0) o = slotNext(c.x, dt);
    else if (c.x < SLOTS && c.y == 1) {                      // PREV: the box, low-passed
        vec4 box = recBox(BLOBS, c.x);
        o = isFresh(c.x) ? box : mix(bPrev(B, c.x), box, 1.0 - exp(-dt / BOX_EMA_S));
    }
    else if (c.x < SLOTS && c.y == 2) o = headNext(c.x, dt);
    else if (c.y == 3 && c.x < 5) {
        vec4 at = attnNext(dt);
        if      (c.x == 0) o = at;
        else if (c.x == 1) o = reticleNext(at, dt);
        else if (c.x == 2) o = moodNext(at, dt);
        else if (c.x == 3) o = blinkNext(at, dt);
        else               o = stampNext(at);
    }
    else if (c.y == 4 && c.x < SLOTS * PRINTS) o = printNext(c.x / PRINTS, c.x % PRINTS, dt);
    else if (c.x < SLOTS && c.y == 5) {                      // DRIFT: the velocity, low-passed
        vec2 v = isState(recIdn(BLOBS, c.x).y, S_CONFIRMED) ? toScreen(recMot(BLOBS, c.x).zw) : vec2(0.0);
        o = isFresh(c.x) ? vec4(0.0) : vec4(mix(bDrift(B, c.x).xy, v, 1.0 - exp(-dt / DRIFT_S)), 0.0, 0.0);
    }
}
