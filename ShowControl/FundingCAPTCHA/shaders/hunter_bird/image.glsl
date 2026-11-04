// Image — the bird's view. iChannel0 = Body (A), iChannel1 = bird state (B), iChannel2 = blobs.
// Back to front: world (zooms on a strike) → field notes → attention → the eye (screen space).
// Positions: `p` is in screen heights (x 0…aspect, y 0…1); records and Body are in UV.

#define BODY  iChannel0
#define B     iChannel1
#define BLOBS iChannel2

float PX;        // one pixel, in screen heights
float ASPECT;

vec2 uvToP(vec2 uv) { return uv * vec2(ASPECT, 1.0); }
vec2 pToUv(vec2 p)  { return p / vec2(ASPECT, 1.0); }
vec2 anchorX(vec2 q) { return vec2(q.x < 0.0 ? ASPECT + q.x : q.x, q.y); }   // negative x: from the right edge
vec2 anchorR(vec2 q) { return vec2(ASPECT + q.x, q.y); }

// Paint `c` over `col` with coverage `a`.
void over(inout vec3 col, vec3 c, float a) { col = mix(col, c, clamp(a, 0.0, 1.0)); }

// ── World ─────────────────────────────────────────────────────────────────────
float present(vec2 uv) { return step(0.5, texture(BODY, uv).r); }

void drawGround(inout vec3 col, vec2 p) {
    if (p.y > 70.0 / 360.0) return;
    float x = p.x * 360.0;
    vec4 Y = vec4(60.0, 44.0, 22.0, -2.0), A = vec4(2.0, 2.5, 3.0, 3.5);  // mockup rows 300…362, y up
    for (int i = 0; i < 4; i++) {
        float y = (Y[i] - sin(x * 0.035 + (360.0 - Y[i])) * A[i]) / 360.0;
        over(col, SLATE, pen(abs(p.y - y), 1.3 / 360.0, PX));
    }
}

void drawPrints(inout vec3 col, vec2 p) {
    for (int i = 0; i < SLOTS * PRINTS; i++) {
        vec4 pr = texelFetch(B, ivec2(i, 4), 0);
        if (pr.z >= PRINT_LIFE_S) continue;
        vec2 q = p - uvToP(pr.xy);
        if (dot(q, q) > 36.0 / (360.0 * 360.0)) continue;       // early-out: 6 px
        q = rot(q, pr.w) / vec2(4.5 / 360.0, 2.6 / 360.0);
        float d = (length(q) - 1.0) * 2.6 / 360.0;
        over(col, SLATE, 0.85 * (1.0 - pr.z / PRINT_LIFE_S) * (1.0 - smoothstep(-0.5 * PX, 0.5 * PX, d)));
    }
}

void drawPeople(inout vec3 col, vec2 p, vec2 uv) {
    vec4  body = texture(BODY, uv);
    float in_ = step(0.5, body.r);
    // Outline: outside the silhouette, within a heavy pen's width of it.
    float r = max(INK_W_HEAVY, PX);
    float edge = 0.0;
    for (int i = 0; i < 8; i++) {
        float a = float(i) * 0.78539816;
        edge = max(edge, present(pToUv(p + r * vec2(cos(a), sin(a)))));
    }
    if (in_ < 0.5) { over(col, INK, edge); return; }
    col = WARM_WHITE;
    // Hatching on the lower 40% of any tracked box that holds this pixel, denser when near.
    for (int k = 0; k < SLOTS; k++) {
        if (isState(recIdn(BLOBS, k).y, S_EMPTY)) continue;
        vec4 box = recBox(BLOBS, k);
        if (uv.x < box.x || uv.x > box.z || uv.y < box.y || uv.y > box.y + 0.4 * (box.w - box.y)) continue;
        float gap = mix(11.0, 6.0, body.g) / 360.0;
        over(col, SLATE, 0.8 * hatch(p, gap, 1.4 / 360.0, PX));
        break;
    }
}

void drawBranch(inout vec3 col, vec2 p, vec2 a, vec2 b, vec2 c, float w) {
    float d = sdBezier(p, a, b, c);
    if (d > w) return;
    over(col, INK, pen(d, w + BR_RIM, PX));
    over(col, PAPER, pen(d, w, PX));
    for (int i = 0; i < 13; i++) {                           // short bark strokes along it
        vec2 q = bezier(a, b, c, 0.05 + 0.07 * float(i));
        over(col, INK, pen(sdSegment(p, q + vec2(-0.25, 0.15) * w, q + vec2(0.15, -0.25) * w), 1.2 / 360.0, PX));
    }
}

void drawLeaf(inout vec3 col, vec2 p, int i, float shiver) {
    vec4 l = LEAF[i]; vec3 k = LEAF_K[i];
    vec2 at = k.z > 0.5 ? anchorR(l.xy) : l.xy;
    float L = l.w;
    if (length(p - at) > L + 3.0 * PX) return;
    float fi = float(i);
    float a = l.z + LEAF_SWAY * sin(iTime * 0.9 + fi * 1.7) + shiver * LEAF_SHIVER * sin(iTime * 28.0 + fi);
    vec2 q = rot(p - at, a);
    float d = sdLeaf(q, L);
    float fill = 1.0 - smoothstep(-0.5 * PX, 0.5 * PX, d);
    over(col, leafFill(k.x), fill);
    if (k.y > 0.5) over(col, SLATE, fill * hatch(p, 10.0 / 360.0, 1.4 / 360.0, PX));
    over(col, INK, pen(abs(d), 1.8 / 360.0, PX));
    // midrib and two pairs of veins
    float v = sdSegment(q, vec2(0.0), vec2(0.85 * L, 0.0));
    for (int j = 0; j < 2; j++) {
        float u = j == 0 ? 0.35 : 0.6;
        v = min(v, sdSegment(q, vec2(u * L, 0.0), vec2((u + 0.14) * L, -0.16 * L)));
        v = min(v, sdSegment(q, vec2(u * L, 0.0), vec2((u + 0.14) * L,  0.16 * L)));
    }
    over(col, INK, fill * pen(v, 1.0 / 360.0, PX));
}

void drawCanopy(inout vec3 col, vec2 p, float shiver) {
    bool band   = p.y > CANOPY_BAND;
    bool corner = p.y > CORNER_Y && (p.x < CORNER_W || p.x > ASPECT - CORNER_W);
    bool perch  = p.x < PERCH_BOX.x && p.y < PERCH_BOX.y;
    if (!band && !corner && !perch) return;                  // early-out: most of the screen
    if (band) {
        drawBranch(col, p, BR_L0, BR_L1, BR_L2, BR_W_L);
        drawBranch(col, p, anchorR(BR_R0), anchorR(BR_R1), anchorR(BR_R2), BR_W_R);
    }
    if (perch) drawBranch(col, p, PERCH0, PERCH1, PERCH2, PERCH_W);
    for (int i = 0; i < LEAVES; i++) drawLeaf(col, p, i, shiver);
}

vec3 world(vec2 p, float shiver) {
    vec2 uv = pToUv(p);
    vec3 col = PAPER;
    drawGround(col, p);
    drawPrints(col, p);
    drawPeople(col, p, uv);
    drawCanopy(col, p, shiver);
    return col;
}


// ── Field notes (world space, over the canopy) ────────────────────────────────
const float G = 1.0 / 360.0;             // one glyph-space unit (mockup px), in screen heights

// Glyph space at `origin`: mockup pixels, y down.
vec2 glyph(vec2 p, vec2 origin) { return (p - origin) * vec2(360.0, -360.0); }

// Distance along a box's border, for dashes: runs round the rim.
float rimCoord(vec2 p, vec2 lo, vec2 hi) {
    vec2 c = (lo + hi) * 0.5, h = (hi - lo) * 0.5, q = p - c;
    return abs(q.x) / h.x > abs(q.y) / h.y ? (q.x > 0.0 ? h.x * 2.0 + (h.y - q.y) : h.x * 4.0 + h.y * 2.0 + (q.y + h.y))
                                           : (q.y > 0.0 ? q.x + h.x : h.x * 2.0 + h.y * 2.0 + (h.x - q.x));
}
float sdRim(vec2 p, vec2 lo, vec2 hi) {
    vec2 q = abs(p - (lo + hi) * 0.5) - (hi - lo) * 0.5;
    return abs(length(max(q, 0.0)) + min(max(q.x, q.y), 0.0));
}

// The eight arms of the corner brackets, wobbling.
float sdBrackets(vec2 p, vec2 lo, vec2 hi, float id) {
    vec2  sz = hi - lo;
    float L = clamp(0.22 * min(sz.x, sz.y), 10.0 * G, 24.0 * G);
    float d = 1e9;
    for (int k = 0; k < 4; k++) {
        vec2 c = vec2(k % 2 == 0 ? lo.x : hi.x, k < 2 ? hi.y : lo.y);
        vec2 s = vec2(k % 2 == 0 ? 1.0 : -1.0, k < 2 ? -1.0 : 1.0);
        float sd = id * 31.0 + float(k) * 7.0;
        d = min(d, sdWobble(p, c, c + vec2(s.x * L, 0.0), sd, 1.2 * G, iTime));
        d = min(d, sdWobble(p, c, c + vec2(0.0, s.y * L), sd + 3.0, 1.2 * G, iTime));
    }
    return d;
}

void drawQuestion(inout vec3 col, vec2 p, vec2 foot, float scale, vec3 ink, float alpha) {
    vec2 q = glyph(p, foot) / scale;
    if (dot(q, q) > 400.0) return;
    over(col, ink, alpha * pen(sdQuestion(q) * scale * G, 1.9 * scale * G, PX));
}

void drawTag(inout vec3 col, vec2 p, vec2 corner, vec4 mot, float id, bool isTarget, bool stamped) {
    float sw = clamp(-mot.z * ASPECT * 360.0 * 0.003, -0.5, 0.5) + sin(iTime * 2.6 + id) * 0.08;
    vec2  q  = rot(glyph(p, corner + vec2(-2.0, -4.0) * G), -sw);   // y down: canvas rotate(sw)
    float n  = id >= 100.0 ? 3.0 : id >= 10.0 ? 2.0 : 1.0;
    float tw = 12.0 + 9.0 * n;
    if (q.x < -4.0 || q.x > tw + 26.0 || q.y < -4.0 || q.y > 34.0) return;
    // string
    over(col, INK, pen(sdBezier(q, vec2(0.0), vec2(4.0, 8.0), vec2(8.0, 12.0)) * G, 1.2 * G, PX));
    vec2 t = q - vec2(8.0, 12.0);
    // body: a pentagon (0,0) (tw,0) (tw,17) (5,17) (0,12)
    float e = max(max(-t.x, t.x - tw), max(-t.y, t.y - 17.0));
    e = max(e, (t.x * -0.7071 + (t.y - 12.0) * 0.7071) - 3.5355 * 0.0);   // the clipped corner
    float edge = min(min(sdSegment(t, vec2(0.0), vec2(tw, 0.0)), sdSegment(t, vec2(tw, 0.0), vec2(tw, 17.0))),
                 min(min(sdSegment(t, vec2(tw, 17.0), vec2(5.0, 17.0)), sdSegment(t, vec2(5.0, 17.0), vec2(0.0, 12.0))),
                     sdSegment(t, vec2(0.0, 12.0), vec2(0.0))));
    float inside = step(e, 0.0);
    over(col, isTarget ? YELLOW : PAPER, inside);
    over(col, INK, pen(edge * G, 1.6 * G, PX));
    over(col, INK, pen(abs(length(t - vec2(4.0)) - 1.6) * G, 1.0 * G, PX));      // the hole
    over(col, INK, pen(sdNumber(t - vec2(9.0, 3.5), id, iTime) * G, 1.8 * G, PX));
    if (stamped) over(col, RUST, pen(sdTick((t - vec2(tw + 8.0, 9.0)) * 2.4) / 2.4 * G, 2.6 * G, PX));
}

void drawArrow(inout vec3 col, vec2 p, vec2 from, vec2 vel, float id) {
    vec2 to = from + vel * ARROW_S;
    vec2 dir = normalize(vel);
    float d = sdWobble(p, from, to, id * 13.0, 0.8 * G, iTime);
    vec2 a1 = to + 8.0 * G * rot(dir, -2.6), a2 = to + 8.0 * G * rot(dir, 2.6);
    d = min(d, min(sdSegment(p, to, a1), sdSegment(p, to, a2)));
    over(col, DEEP, pen(d, 2.0 * G, PX));
}

void drawNotes(inout vec3 col, vec2 p, int tgt) {
    for (int k = 0; k < SLOTS; k++) {
        vec4 idn = recIdn(BLOBS, k);
        float st = idn.y;
        if (isState(st, S_EMPTY)) continue;
        vec4 box = recBox(BLOBS, k), mot = recMot(BLOBS, k);
        vec2 lo = uvToP(box.xy), hi = uvToP(box.zw);
        vec2 vel = uvToP(mot.zw);
        float reach = NOTE_REACH + length(vel) * ARROW_S;
        if (any(lessThan(p, lo - reach)) || any(greaterThan(p, hi + reach))) continue;   // early-out
        float age = idn.z;

        if (isState(st, S_TENTATIVE)) {
            float dash = step(mod(rimCoord(p, lo, hi) + iTime * DASH_CRAWL, DASH_ON + DASH_OFF), DASH_ON);
            over(col, SLATE, dash * pen(sdRim(p, lo, hi), INK_W_LIGHT, PX));
            drawQuestion(col, p, vec2(hi.x - 2.0 * G, hi.y + 4.0 * G), 1.0, SLATE, 1.0);
            continue;
        }
        bool coasting = isState(st, S_COASTING), lost = isState(st, S_LOST), isT = k == tgt;
        float alpha = coasting ? clamp(1.0 - age / COAST_FADE, 0.15, 1.0)
                    : lost     ? clamp(1.0 - (age - LOST_FADE_START) / LOST_FADE_S, 0.0, 1.0) : 1.0;
        if (alpha <= 0.0) continue;
        float w = isT ? INK_W_HEAVY : INK_W_LIGHT;
        float a = alpha * (isT || coasting ? 1.0 : 0.75);
        float br = pen(sdBrackets(p, lo, hi, idn.x), w, PX);
        if (coasting) br *= step(mod(rimCoord(p, lo, hi), 7.0 * G), 3.0 * G);
        over(col, INK, a * br);

        if (!lost && length(vel) > ARROW_MIN_SPEED) drawArrow(col, p, uvToP(mot.xy), vel, idn.x);
        vec3 before = col;
        drawTag(col, p, hi, mot, idn.x, isT, bSlot(B, k).w > 0.5 && abs(bSlot(B, k).x - idn.x) < 0.5);
        col = mix(before, col, alpha);
        if (coasting) drawQuestion(col, p, vec2(hi.x + 8.0 * G, hi.y - 14.0 * G), 1.1, INK, alpha);
        if (lost) {                                              // scribbled through, drawn over 0.25 s
            float u = clamp(age / SCRIBBLE_S, 0.0, 1.0), h = hi.y - lo.y, d = 1e9;
            vec2 prev = vec2(lo.x, hi.y - 0.1 * h);
            for (int i = 1; i <= 7; i++) {
                if (float(i) > floor(7.0 * u)) break;
                vec2 nxt = vec2(i % 2 == 1 ? hi.x : lo.x, hi.y - h * (0.1 + 0.8 * float(i) / 7.0));
                d = min(d, sdSegment(p, prev, nxt)); prev = nxt;
            }
            over(col, INK, alpha * pen(d, INK_W, PX));
        }
    }
}

// ── Attention (world space) ───────────────────────────────────────────────────
void drawReticle(inout vec3 col, vec2 p, vec4 ret, float lock, bool hasTarget) {
    if (ret.w < 0.02) return;
    float tremble = lock * 1.4 * G;
    vec2  c = uvToP(ret.xy) + vec2(sin(iTime * 41.0), cos(iTime * 37.0)) * tremble;
    float r = ret.z;
    vec2  q = p - c;
    float len = length(q);
    if (len > r + 16.0 * G) return;
    float ang = atan(q.y, q.x);
    float ring = abs(len - (r + vnoise(ang / 6.2831853 * 48.0 * 0.7 + iTime * 1.5) * 1.4 * G));
    float d = ring;
    for (int k = 0; k < 4; k++) {
        vec2 dir = rot(vec2(1.0, 0.0), -(float(k) * 1.5707963 + 0.7853982));
        d = min(d, sdWobble(p, c + dir * (r - 6.0 * G), c + dir * (r + 9.0 * G), float(k) * 5.0, 0.6 * G, iTime));
    }
    float a = pen(d, INK_W, PX);
    // lock arc, clockwise from 12 o'clock
    float cw = mod(atan(q.x, q.y), 6.2831853);
    if (lock > 0.01 && cw < lock * 6.2831853) a = max(a, pen(abs(len - (r + 7.0 * G)), 5.0 * G, PX));
    over(col, RUST, ret.w * a);
    if (!hasTarget) drawQuestion(col, p, c + vec2(0.0, -9.0 * G), 2.0, RUST, ret.w);
}

void drawStamp(inout vec3 col, vec2 p, vec2 at, float since) {
    if (since >= STAMP_END_S) return;
    float s = since < STAMP_SLAM_S ? 2.4 - 1.4 * since / STAMP_SLAM_S : 1.0;
    float alpha = 0.92 * (since < STAMP_FADE_START_S ? 1.0 : 1.0 - (since - STAMP_FADE_START_S) / (STAMP_END_S - STAMP_FADE_START_S));
    vec2 q = rot(glyph(p, at), 0.22) / s;                    // y down: canvas rotate(−0.22)
    float len = length(q);
    if (len > 56.0) return;
    float k = s * G;                                         // glyph units → screen heights
    float a = pen(abs(len - 36.0) * k, 4.5 * k, PX);
    a = max(a, pen(abs(len - 28.0) * k, 1.6 * k, PX));
    float an = atan(q.y, q.x), sector = 6.2831853 / 12.0;
    float ra = (floor(an / sector + 0.5)) * sector;
    vec2 dir = vec2(cos(ra), sin(ra));
    a = max(a, pen(sdSegment(q, dir * 42.0, dir * 50.0) * k, 1.6 * k, PX));
    a = max(a, pen(sdTick(q) * k, 7.0 * k, PX));
    over(col, RUST, alpha * a);
}

// ── Strike punch-in ───────────────────────────────────────────────────────────
float punch(float since) {
    if (since < PUNCH_RISE_S) return smoothstep(0.0, 1.0, since / PUNCH_RISE_S);
    if (since < PUNCH_HOLD_S) return 1.0;
    return 1.0 - smoothstep(0.0, 1.0, (since - PUNCH_HOLD_S) / (PUNCH_END_S - PUNCH_HOLD_S));
}

void mainImage(out vec4 o, in vec2 fc) {
    PX = 1.0 / iResolution.y;
    ASPECT = iResolution.x / iResolution.y;
    vec2 p = fc / iResolution.y;
    vec4 at = bAttn(B), mood = bMood(B);

    vec2  sp   = uvToP(bStamp(B).xy);
    float zoom = 1.0 + PUNCH_ZOOM * punch(at.z);
    vec2  wp   = sp + (p - sp) / zoom;                       // world point under this pixel
    PX /= zoom;

    int  tgt = int(at.x + 0.5) - 1;
    vec3 col = world(wp, mood.y);
    drawNotes(col, wp, tgt);
    drawReticle(col, wp, bReticle(B), at.y, tgt >= 0);
    drawStamp(col, wp, sp, at.z);
    o = vec4(col, 1.0);
}
