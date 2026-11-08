// Buffer B — flock, poops and splats. iChannel0 = Body (A), iChannel1 = this buffer, iChannel2 = blobs.
// Layout: see common.glsl. Each texel reads the previous frame of every other texel; texels that
// depend on the same event (an assignment, a release, a hit) recompute it from the same inputs.
// Positions are worked in screen heights (sh) and stored as UV.

#define BODY  iChannel0
#define B     iChannel1
#define BLOBS iChannel2

float ASPECT;
float DITHER;    // 0–1, per texel per frame: stochastic rounding for tick()

// x + dt, kept in multiples of AGE_Q (see common.glsl) and clamped at T_CLAMP.
float tick(float x, float dt) { return min(x + floor(dt / AGE_Q + DITHER) * AGE_Q, T_CLAMP); }
float quant(float x) { return floor(x / AGE_Q + 0.5) * AGE_Q; }

// ── Who is there ──────────────────────────────────────────────────────────────
// The record in slot k carries a different person than SLOT k remembers (or none).
bool isFresh(int k) {
    vec4 idn = recIdn(BLOBS, k);
    return isState(idn.y, S_EMPTY) || abs(idn.x - sSlot(B, k).x) > 0.5;
}
int planSlot(vec4 plan) { return int(abs(plan.z) + 0.5) - 1; }
// The person a dive is aimed at is still in their slot.
bool targetValid(vec4 plan) {
    int k = planSlot(plan);
    if (k < 0) return false;
    vec4 idn = recIdn(BLOBS, k);
    return abs(idn.x - plan.w) < 0.5 && isHere(idn.y);
}

// ── Flock ─────────────────────────────────────────────────────────────────────
// Bird i's idle orbit point (sh): a slow loop around a centre that wanders across the sky.
vec2 orbitGoal(int i) {
    float fi = float(i);
    float cx = ASPECT * (0.5 + 0.36 * vnoise(iTime * ORBIT_DRIFT + fi * 7.3));
    float cy = ORBIT_Y + 0.04 * vnoise(iTime * ORBIT_DRIFT * 1.7 + fi * 3.1 + 50.0);
    float a  = (i % 2 == 0 ? 1.0 : -1.0) * iTime * ORBIT_W + fi * 1.9;
    return vec2(cx, cy) + ORBIT_R * vec2(1.6 * cos(a), sin(a));
}

vec4 initial(ivec2 c) {
    if (c.y == 0 && c.x < SLOTS)          return vec4(0.0, FIRST_BOMB_S, 0.0, 0.0);           // SLOT
    if (c.y == 2 && c.x < BIRDS)          return vec4(toUv(orbitGoal(c.x)), 0.0, 0.0);        // BIRD
    if (c.y == 7 && c.x < SLOTS * SPLATS) return vec4(0.0, 0.0, T_CLAMP, 0.0);                // SPLAT
    if (c.y == 8 && c.x < GROUNDS)        return vec4(0.0, 0.0, T_CLAMP, 0.0);                // GROUND
    return vec4(0.0);
}

// ── Assignment: which idle bird goes for which overdue person this frame ────
bool targeted(int k) {
    for (int i = 0; i < BIRDS; i++) {
        vec4 plan = sPlan(B, i);
        if (isState(plan.x, 1.0) && planSlot(plan) == k) return true;
    }
    return false;
}
// (bird, slot), or (-1, -1). At most one per frame: the most overdue person, the nearest idle bird.
ivec2 assignNext() {
    int bk = -1; float bt = 0.0;
    for (int k = 0; k < SLOTS; k++) {
        float due = sSlot(B, k).y;
        if (due > 0.0 || isFresh(k) || !isState(recIdn(BLOBS, k).y, S_CONFIRMED) || targeted(k)) continue;
        if (bk < 0 || due < bt) { bk = k; bt = due; }
    }
    if (bk < 0) return ivec2(-1);
    vec2 tp = toScreen(recMot(BLOBS, bk).xy);
    int bi = -1; float bd = 1e9;
    for (int i = 0; i < BIRDS; i++) {
        if (sPlan(B, i).x > 0.5) continue;
        float d = length(toScreen(sBird(B, i).xy) - tp);
        if (d < bd) { bi = i; bd = d; }
    }
    return bi < 0 ? ivec2(-1) : ivec2(bi, bk);
}

// ── Dive ──────────────────────────────────────────────────────────────────────
float releaseSpeed() { return 2.0 * APPROACH / DIVE_S; }   // the approach curve's end speed (level)

// Where to release (sh) over slot k's person, flying `dir`, with `left` s of dive to go:
// above their head, leading them by the time until the poop lands.
vec2 releasePoint(int k, float dir, float left, float aim) {
    vec4  box = recBox(BLOBS, k);
    float top = box.w;                                      // UV y is sh
    float ry  = min(top + DROP_ABOVE, SKY_MAX);
    float fall = sqrt(2.0 * max(ry - top, 0.01) / GRAVITY);
    vec2  c = toScreen(vec2((box.x + box.z) * 0.5, top));
    float halfw = 0.5 * toScreen(vec2(box.z - box.x, 0.0)).x;
    float lead = clamp(toScreen(recMot(BLOBS, k).zw).x * (left + fall), -LEAD_MAX, LEAD_MAX);
    return vec2(c.x + aim * AIM_SPREAD * halfw + lead - dir * releaseSpeed() * fall, ry);
}
// A per-dive aim offset, −1…1, fixed by the dive's start point.
float aimOf(int i, vec4 plan, vec4 path) {
    return 2.0 * hash11(plan.w * 3.7 + float(i) * 11.0 + floor(path.x * 997.0) + floor(path.y * 613.0)) - 1.0;
}

struct Bird { vec4 bird; vec4 plan; vec4 path; bool released; };

Bird birdStep(int i, float dt) {
    Bird o;
    o.bird = sBird(B, i); o.plan = sPlan(B, i); o.path = sPath(B, i); o.released = false;
    vec2 pos = toScreen(o.bird.xy), vel = o.bird.zw;

    if (o.plan.x < 0.5) {                                   // orbiting
        ivec2 a = assignNext();
        if (a.x == i) {                                     // sent: start the dive from here
            int   k   = a.y;
            float dir = toScreen(recMot(BLOBS, k).xy).x >= pos.x ? 1.0 : -1.0;
            o.plan = vec4(1.0, 0.0, dir * float(k + 1), recIdn(BLOBS, k).x);
            o.path = vec4(o.bird.xy, 0.0, 0.0);
            o.path.zw = toUv(releasePoint(k, dir, DIVE_S, aimOf(i, o.plan, o.path)));
            return o;
        }
        vec2 want = (orbitGoal(i) - pos) * ORBIT_GAIN;
        if (length(want) > CRUISE) want *= CRUISE / length(want);
        vel += (want - vel) * (1.0 - exp(-dt * STEER_K));
        pos += vel * dt;
        o.bird = vec4(toUv(pos), vel);
        return o;
    }

    float t = o.plan.y + dt, dir = sign(o.plan.z);
    if (o.plan.x < 1.5) {                                   // diving: the release point follows the target
        vec2 R = targetValid(o.plan)
               ? releasePoint(planSlot(o.plan), dir, max(DIVE_S - t, 0.0), aimOf(i, o.plan, o.path))
               : toScreen(o.path.zw);
        o.path.zw = toUv(R);
        if (t >= DIVE_S) { o.released = true; o.plan.x = 2.0; t -= DIVE_S; }
        else {
            vec2 S = toScreen(o.path.xy), C = vec2(R.x - dir * APPROACH, R.y);
            float u = t / DIVE_S;
            pos = bezier(S, C, R, u); vel = bezierD(S, C, R, u) / DIVE_S;
        }
    }
    if (o.plan.x > 1.5) {                                   // climbing away from the frozen release point
        vec2 R = toScreen(o.path.zw);
        vec2 C = vec2(R.x + dir * APPROACH, R.y), E = vec2(R.x + 2.0 * dir * APPROACH, CLIMB_TO_Y);
        float u = min(t / CLIMB_S, 1.0);
        pos = bezier(R, C, E, u); vel = bezierD(R, C, E, u) / CLIMB_S;
        if (t >= CLIMB_S) { o.plan = vec4(0.0); t = 0.0; }
    }
    o.plan.y = min(t, T_CLAMP);
    o.bird = vec4(toUv(pos), vel);
    return o;
}

// ── Poop ──────────────────────────────────────────────────────────────────────
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

Poop poopStep(int i, float dt) {
    Poop o;
    o.poop = sPoop(B, i); o.drop = sDrop(B, i); o.hitSlot = -1; o.ground = false; o.at = vec2(0.0);
    Bird b = birdStep(i, dt);
    if (b.released) {                                       // dropped this frame, from the release point
        bool valid = targetValid(b.plan);
        float floorY = valid ? recBox(BLOBS, planSlot(b.plan)).y : 0.02;
        o.poop = vec4(b.path.zw, sign(b.plan.z) * releaseSpeed(), 0.0);
        o.drop = vec4(float(planSlot(b.plan) + 1), floorY, 0.0, 0.0);
        return o;
    }
    if (o.drop.x < 0.5) return o;                           // nothing falling

    vec2  pos = toScreen(o.poop.xy), vel = o.poop.zw;
    float h = dt / float(FALL_STEPS);
    for (int s = 0; s < FALL_STEPS; s++) {
        vel.y -= GRAVITY * h;
        pos += vel * h;
        vec2 uv = toUv(pos);
        bool onScreen = uv.x > 0.0 && uv.x < 1.0 && uv.y > 0.0 && uv.y < 1.0;
        if (onScreen && texture(BODY, uv).r > 0.5) {
            int k = slotAt(uv, int(o.drop.x + 0.5) - 1);
            if (k >= 0) { o.hitSlot = k; o.at = uv; o.poop = vec4(0.0); o.drop = vec4(0.0); return o; }
        }
        if (uv.y <= o.drop.y) {
            o.ground = uv.x > -0.05 && uv.x < 1.05;
            o.at = vec2(uv.x, o.drop.y); o.poop = vec4(0.0); o.drop = vec4(0.0); return o;
        }
        if (uv.x < -0.3 || uv.x > 1.3) { o.poop = vec4(0.0); o.drop = vec4(0.0); return o; }
    }
    o.poop = vec4(toUv(pos), vel);
    o.drop.w = min(o.drop.w + dt, T_CLAMP);
    return o;
}

// ── Per person ────────────────────────────────────────────────────────────────
vec4 slotNext(int k, float dt) {
    vec4 idn = recIdn(BLOBS, k);
    float here = isHere(idn.y) ? 1.0 : 0.0;
    if (isFresh(k))
        return vec4(isState(idn.y, S_EMPTY) ? 0.0 : idn.x, quant(FIRST_BOMB_S + FIRST_JITTER * hash11(idn.x * 1.37)), here, 0.0);
    vec4 s = sSlot(B, k);
    if (isState(idn.y, S_CONFIRMED)) s.y = max(-tick(-s.y, dt), -10.0);
    if (assignNext().y == k) s.y = quant(BOMB_EVERY_S + BOMB_JITTER_S * (2.0 * hash11(iTime * 7.7 + float(k)) - 1.0));
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
    for (int i = 0; i < BIRDS; i++) {
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
    for (int i = 0; i < BIRDS; i++) {
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
    if (c.y > 8) return;
    ASPECT = iResolution.x / iResolution.y;
    if (iFrame == 0) { o = initial(c); return; }
    float dt = clamp(iTimeDelta, 1e-3, DT_MAX);
    uint hx = uint(iFrame) * 747796405u + uint(c.x) * 2891336453u + uint(c.y) * 277803737u;   // PCG-style
    hx = ((hx >> ((hx >> 28u) + 4u)) ^ hx) * 277803737u;
    DITHER = float((hx >> 22u) ^ hx) / 4294967296.0;

    if      (c.y == 0 && c.x < SLOTS) o = slotNext(c.x, dt);
    else if (c.y == 1 && c.x < SLOTS) o = anchorNext(c.x, dt);
    else if (c.y >= 2 && c.y <= 4 && c.x < BIRDS) {
        Bird b = birdStep(c.x, dt);
        o = c.y == 2 ? b.bird : c.y == 3 ? b.plan : b.path;
    }
    else if (c.y >= 5 && c.y <= 6 && c.x < BIRDS) {
        Poop p = poopStep(c.x, dt);
        o = c.y == 5 ? p.poop : p.drop;
    }
    else if (c.y == 7 && c.x < SLOTS * SPLATS) o = splatNext(c.x / SPLATS, c.x % SPLATS, dt);
    else if (c.y == 8 && c.x < GROUNDS)        o = groundNext(c.x, dt);
}
