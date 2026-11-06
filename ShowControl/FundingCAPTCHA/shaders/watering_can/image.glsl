// Image — paper and plants (the sun is Task 4).  iChannel0 = Buffer B, iChannel1 = Buffer C, iChannel2 = blobs
// p is in screen heights, origin bottom left, y up; screen-height y and UV y are the same number.
//
// Vine i stands at screen x i * VINE_SPACING. Where it crosses a run of body (B), it grows from
// the run's bottom g toward its top b: stem, leaves on alternating sides, and a bud at the tip
// that opens into a flower late. The drawing derives from B and the owner's growth every frame,
// so the plants ride along on the body.
//
// Each pixel looks at VINE_NEIGHBOURS vines each side and taps B on the vine's own x: at the
// pixel's height, and a flower's reach above and below, so leaves and flowers hanging past the
// edge of the body still find their run; halfway between too, so a run thinner than a flower
// (an outstretched arm, a hand) is found from every row its plants cover. The taps don't follow the
// wobble: a vine's runs must be the same from one pixel row to the next, or its leaves and
// flowers would be cut into strips (B's runs agree along a column for the same reason). One more
// tap, at the pixel, keeps stems inside the body, and a leaf taps B at its node, only on the
// pixels it covers, so leaves grow only from nodes on the body.

const float TAU = 6.2831853;
const int   NV  = 2 * VINE_NEIGHBOURS + 1;
const int   TAPS = 5;                             // offsets 0, ±REACH, ±REACH/2 (see plants())
const float SAME_RUN = 0.5 * RUN_STEP_H;          // two taps whose extents agree this closely found the same run

float AA;                                         // one render pixel, in screen heights

float fillA(float sd) { return 1.0 - smoothstep(-0.6 * AA, 0.6 * AA, sd); }
float lineA(float sd, float w) {                  // a line of width w along sd = 0
    float wf = max(w, PEN_MIN * AA);              // never thinner than the pen: fainter instead
    return (w / wf) * (1.0 - smoothstep(0.5 * wf - 0.6 * AA, 0.5 * wf + 0.6 * AA, abs(sd)));
}

// Premultiplied "over": lay colour c at coverage a on top of what's drawn so far.
void over(inout vec4 acc, vec3 c, float a) { acc = vec4(c * a, a) + acc * (1.0 - a); }
// A flat fill with an ink outline; k fades a shape in as it grows from nothing.
void inked(inout vec4 acc, vec3 c, float sd, float k) {
    over(acc, c, fillA(sd) * k);
    over(acc, INK, lineA(sd, INK_W) * k);
}

vec3 hsl(float h, float s, float l) {             // h in degrees
    vec3 k = mod(vec3(0.0, 8.0, 4.0) + h / 30.0, 12.0);
    return l - s * min(l, 1.0 - l) * clamp(min(k - 3.0, 9.0 - k), -1.0, 1.0);
}
vec3 desaturate(vec3 c, float sat) { return mix(vec3(dot(c, vec3(0.299, 0.587, 0.114))), c, sat / SAT_MAX); }
vec3 stemColour(float sat) { return hsl(105.0, sat, 0.28); }
vec3 leafColour(float sat) { return hsl(110.0, sat, 0.44); }
vec3 flowerColour(int i) {
    float h = hash12(vec2(float(i), 9.7));
    return h < 0.25 ? PINK : h < 0.5 ? ORANGE : h < 0.75 ? VIOLET : RUST;
}

// iq's vesica: a pointed leaf along y, half-length sqrt(r² − d²), half-width r − d.
float sdVesica(vec2 p, float r, float d) {
    p = abs(p);
    float b = sqrt(r * r - d * d);
    return ((p.y - b) * d > p.x * b) ? length(p - vec2(0.0, b)) : length(p - vec2(-d, 0.0)) - r;
}

// ── Body memory and growth ────────────────────────────────────────────────────

vec4 tapB(float x, float y) {                     // B under screen point (x, y); 0 off screen
    float aspect = iResolution.x / iResolution.y;
    if (y < 0.0 || y >= 1.0 || x < 0.0 || x >= aspect) return vec4(0.0);
    return texelFetch(iChannel0, ivec2(vec2(x / aspect, y) * iChannelResolution[0].xy), 0);
}
// Is t on a body (or its held shape)? B's membership has hysteresis, so a flickering edge holds
// still; a softer test on raw presence here would bring the flicker back.
bool onBody(vec4 t) { return bOwner(t) > 0 && bHold(t) > 0.0; }

// Growth for owner slot k (R7): the live person's, or while their plants rewind away, their ghost's.
float growthOf(int k) {
    vec4 pr = cPerson(iChannel1, k);
    if (abs(pr.x) > 0.5) return pr.y;
    vec4 gh = cGhost(iChannel1, k);
    return gh.w < LEAVE_S ? gh.z : 0.0;
}

struct Run { float g, b, tip, f, sat; };          // bottom, top, tip (y), reach fraction G·hold, saturation

// The run under screen point (x, y), if anything has grown on it.
bool tapRun(float x, float y, out Run r) {
    r = Run(0.0, 0.0, 0.0, 0.0, 0.0);
    vec4 t = tapB(x, y);
    int own = bOwner(t);
    if (own <= 0 || own > SLOTS || t.b < t.g) return false;
    float h = t.r >= BODY_ON ? 1.0 : bHold(t);    // present body is fully held (its stored hold is ≈ 0.998)
    if (h <= 0.0) return false;
    float G = growthOf(own - 1);
    r = Run(t.g, t.b, 0.0, G * h, mix(SAT_MIN, SAT_MAX, G));
    r.tip = mix(r.g, r.b, r.f);
    return r.tip > r.g;
}

// ── Vines ─────────────────────────────────────────────────────────────────────

float vineHash(int i) { return hash12(vec2(float(i), 1.7)); }
float wobbleX(int i, float y) {
    return float(i) * VINE_SPACING + VINE_WOBBLE * sin(y * WOBBLE_FREQ + TAU * vineHash(i));
}
float swayX(int i, float y, Run r) {              // grows up the run
    float up = clamp((y - r.g) / max(r.b - r.g, 1e-3), 0.0, 1.0);
    return SWAY_AMP * up * sin(TAU * SWAY_HZ * iTime - 3.0 * float(i) * VINE_SPACING + vineHash(i));
}
float vineX(int i, float y, Run r) { return wobbleX(i, y) + swayX(i, y, r); }

float sprout(float len) { return smoothstep(0.0, SPROUT_H, len); }

void stem(inout vec4 acc, vec2 p, int i, Run r) {
    float y  = clamp(p.y, r.g, r.tip);
    float s  = VINE_WOBBLE * WOBBLE_FREQ * cos(y * WOBBLE_FREQ + TAU * vineHash(i));   // slope of the wobble
    float dx = (p.x - vineX(i, y, r)) / sqrt(1.0 + s * s);
    over(acc, stemColour(r.sat), lineA(length(vec2(dx, p.y - y)), STEM_W) * sprout(r.tip - r.g));
}

void leaves(inout vec4 acc, vec2 p, int i, Run r) {
    float off  = 0.5 + 0.5 * hash12(vec2(float(i), 3.1));            // the first leaf, in steps above g
    float flip = step(0.5, hash12(vec2(float(i), 5.3)));
    float down = 2.0 * LEAF_LEN + LEAF_WID;                           // a leaf hangs at most this far below its node
    int   j0   = max(int(ceil((p.y - LEAF_WID - r.g) / LEAF_STEP - off)), 0);
    float rr   = 0.5 * (LEAF_LEN * LEAF_LEN / LEAF_WID + LEAF_WID); // vesica of half-length LEAF_LEN, half-width LEAF_WID
    float dd   = rr - LEAF_WID;
    for (int n = 2; n >= 0; n--) {                                    // top leaf first, so lower leaves overlap it
        int   j  = j0 + n;
        float yj = r.g + (float(j) + off) * LEAF_STEP;
        if (yj > p.y + down || yj >= r.tip) continue;
        float k  = sprout(r.tip - yj);                                // grows in as the tip passes
        float side = mod(float(j) + flip, 2.0) < 0.5 ? 1.0 : -1.0;
        float a  = LEAF_DROOP + LEAF_DROOP_VAR * (2.0 * hash12(vec2(float(i), float(j) + 0.5)) - 1.0);
        vec2  dir = vec2(side * cos(a), -sin(a));
        vec2  q   = p - (vec2(vineX(i, yj, r), yj) + dir * LEAF_LEN * k);
        vec2  lq  = vec2(dot(q, vec2(-dir.y, dir.x)), dot(q, dir));   // across, along
        float sd  = sdVesica(lq / max(k, 1e-3), rr, dd) * k;
        if (sd > INK_W + 2.0 * AA) continue;
        if (!onBody(tapB(wobbleX(i, yj), yj))) continue;              // leaves grow from nodes on the body
        float o  = min(1.0, 3.0 * k);                                 // solid long before it's full size: flat, not a wash
        inked(acc, leafColour(r.sat), sd, o);
        float rib = length(vec2(lq.x, max(abs(lq.y) - 0.6 * LEAF_LEN, 0.0)));
        over(acc, INK, lineA(rib, 0.6 * INK_W) * fillA(sd) * o);       // midrib
    }
}

void bloom(inout vec4 acc, vec2 p, int i, Run r) {
    float open = clamp((r.f - FLOWER_FROM) / (FLOWER_FULL - FLOWER_FROM), 0.0, 1.0);
    // The taps are REACH / 2 apart, so a run shorter than that isn't found from every row an open
    // flower covers: on one (a ragged edge, a fragment) the flower stays a bud. Only the bloom.
    open *= smoothstep(SHORT_BLOOM_FROM * REACH, SHORT_BLOOM_FULL * REACH, r.b - r.g);
    // The bud sits on the stem's tip. Opening, the flower drifts to the vine's own x (on the body),
    // so the wobble can't carry it further past the edge than its own size.
    vec2  tip = vec2(vineX(i, r.tip, r), r.tip);
    vec2  c   = vec2(mix(tip.x, float(i) * VINE_SPACING + swayX(i, r.tip, r), open), r.tip);
    if (length(p - c) > REACH + INK_W + 2.0 * AA && length(p - tip) > BUD_R + INK_W + 2.0 * AA) return;
    float k = sprout(r.tip - r.g);
    inked(acc, leafColour(r.sat), length(p - mix(tip, c, open)) - BUD_R * k, k);   // the bud, later the calyx
    if (open <= 0.0) return;
    vec2  q  = p - c;
    float fr = mix(BUD_R, FLOWER_R, open);
    float e  = smoothstep(0.0, 0.25, open);                           // petals swell out of the bud
    vec3  pc = desaturate(flowerColour(i), r.sat);
    float a0 = TAU * hash12(vec2(float(i), 11.3));
    for (int n = 0; n < 5; n++) {
        float a = a0 + TAU * float(n) / 5.0;
        inked(acc, pc, length(q - fr * vec2(cos(a), sin(a))) - PETAL_R * fr * e, 1.0);
    }
    inked(acc, desaturate(YELLOW, r.sat), length(q) - HEART_R * fr * e, 1.0);
}

// The plants over transparent, premultiplied. Stems and leaves vine by vine, then buds and flowers on top.
vec4 plants(vec2 fc) {
    vec2 p  = fc / iResolution.y;
    if (!cNear(iChannel1, p)) return vec4(0.0);                       // no body near (Buffer C's grid): paper, one fetch
    int  i0 = int(floor(p.x / VINE_SPACING + 0.5));
    Run  runs[NV * TAPS];
    bool has[NV * TAPS];
    bool found = false;
    for (int v = 0; v < NV; v++) {
        float x = float(i0 + v - VINE_NEIGHBOURS) * VINE_SPACING;
        for (int t = 0; t < TAPS; t++) {
            int s = v * TAPS + t;
            has[s] = false;
            // The halfway taps only matter when the outer two aren't on one run: if they are, so is
            // everything between (a run is unbroken), and the halfway taps would find it again.
            if (t >= 3 && has[v * TAPS + 1] && has[v * TAPS + 2]
                && abs(runs[v * TAPS + 1].g - runs[v * TAPS + 2].g) < SAME_RUN
                && abs(runs[v * TAPS + 1].b - runs[v * TAPS + 2].b) < SAME_RUN) continue;
            float dy = t == 0 ? 0.0 : t == 1 ? REACH : t == 2 ? -REACH : t == 3 ? 0.5 * REACH : -0.5 * REACH;
            has[s] = tapRun(x, p.y + dy, runs[s]);
            for (int u = 0; u < t; u++) {                             // taps on the same run draw it once
                int o = v * TAPS + u;
                if (has[s] && has[o] && abs(runs[s].g - runs[o].g) < SAME_RUN && abs(runs[s].b - runs[o].b) < SAME_RUN)
                    has[s] = false;
            }
            found = found || has[s];
        }
    }
    vec4 acc = vec4(0.0);
    if (!found) return acc;                                           // nothing grows near: paper
    bool inside = onBody(tapB(p.x, p.y));                             // stems stay inside the body
    for (int v = 0; v < NV; v++) {
        int i = i0 + v - VINE_NEIGHBOURS;
        for (int t = 0; t < TAPS; t++) {
            if (!has[v * TAPS + t]) continue;
            if (inside) stem(acc, p, i, runs[v * TAPS + t]);
            leaves(acc, p, i, runs[v * TAPS + t]);
        }
    }
    for (int v = 0; v < NV; v++)
        for (int t = 0; t < TAPS; t++)
            if (has[v * TAPS + t]) bloom(acc, p, i0 + v - VINE_NEIGHBOURS, runs[v * TAPS + t]);
    return acc;
}

void mainImage(out vec4 o, in vec2 fc) {
    AA = 1.0 / iResolution.y;
    vec3 col = PAPER;                                                 // Task 4: the sun goes here, under the plants
    vec4 pl  = plants(fc);
    o = vec4(pl.rgb + col * (1.0 - pl.a), 1.0);
}
