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
        float grow = abs((sz.x + sz.y) - (psz.x + psz.y)) / dt;
        target = clamp(speed / SPEED_FULL + grow / SIZE_FULL - MOTION_FLOOR, 0.0, 1.0);
    }
    float tau = target > s.y ? MOTION_RISE_S : MOTION_FALL_S;
    s.y += (target - s.y) * (1.0 - exp(-dt / tau));

    // Stamped: the strike named this id (matched on id, so a reused slot is safe).
    vec4 at = bAttn(B);
    if (abs(at.w - s.x) < 0.5 && at.z < STRIKE_ACK_S) s.w = 1.0;

    // Interest: rises with motion while confirmed; tentative, coasting and lost drain.
    if (confirmed && s.y > MOTION_ON) s.z += dt * INTEREST_GAIN * s.y;
    else                              s.z -= dt * INTEREST_DRAIN;
    s.z = s.w > 0.5 ? 0.0 : clamp(s.z, 0.0, 1.0);
    return s;
}

// ── HEAD ──────────────────────────────────────────────────────────────────────
vec4 headNext(int k, float dt) {
    if (isFresh(k)) return vec4(0.0, 0.0, 0.0, T_CLAMP);
    vec4 h = bHead(B, k);
    h.w = min(h.w + dt, T_CLAMP);
    return h;
}

void mainImage(out vec4 o, in vec2 fc) {
    ivec2 c = ivec2(fc);
    o = vec4(0.0);
    if (c.y > 4) return;
    if (iFrame == 0) { o = initial(c); return; }
    float dt = clamp(iTimeDelta, 1e-3, DT_MAX);

    if (c.x < SLOTS && c.y == 0) o = slotNext(c.x, dt);
    else if (c.x < SLOTS && c.y == 1) o = recBox(BLOBS, c.x);
    else if (c.x < SLOTS && c.y == 2) o = headNext(c.x, dt);
    else o = initial(c);                                     // filled in by later tasks
}
