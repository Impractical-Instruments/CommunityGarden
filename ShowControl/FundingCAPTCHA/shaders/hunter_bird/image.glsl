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
    drawPeople(col, p, uv);
    drawCanopy(col, p, shiver);
    return col;
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

    vec3 col = world(wp, mood.y);
    o = vec4(col, 1.0);
}
