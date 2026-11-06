// Image — paper, the crayon sun and plants.  iChannel0 = Buffer B, iChannel1 = Buffer C, iChannel2 = blobs
// p is in screen heights, origin bottom left, y up; screen-height y and UV y are the same number.
//
// Vine i stands at screen x i * VINE_SPACING. Where it crosses a run of body (B), it grows from
// the run's bottom g toward its top b, drawn as the concept art's branches: a trunk tapering to its
// tip, twigs forking up off it on alternating sides with sprigs of petals at their ends, and at the
// tip a sprig, or on some branches a bud that opens into a daisy late. Branches rise in pairs from
// one root, and all the wood near a pixel is one inked shape, so they merge and fork as the art's.
// The drawing derives from B and the owner's growth every frame, so the plants ride along on the body.
//
// Each pixel looks at VINE_NEIGHBOURS vines each side and taps B on the vine's own x: at the
// pixel's height, and a flower's reach above and below, so twigs and flowers reaching past the
// edge of the body still find their run; halfway between too, so a run thinner than a flower
// (an outstretched arm, a hand) is found from every row its plants cover. The taps don't follow the
// wobble: a vine's runs must be the same from one pixel row to the next, or its twigs and
// flowers would be cut into strips (B's runs agree along a column for the same reason). A twig
// taps B at its node, only on the pixels it covers, so twigs grow only from nodes on the body.

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
vec3 stemColour(float sat) { return hsl(95.0, sat, 0.34); }
vec3 leafColour(float sat) { return hsl(100.0, sat, 0.58); }
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

// ── Branches ──────────────────────────────────────────────────────────────────

float vineHash(int i) { return hash12(vec2(float(i), 1.7)); }
float wobbleX(int i, float y) {                   // a slow wave and a faster kink: gnarled wood
    float ph = TAU * vineHash(i);
    return float(i) * VINE_SPACING
         + VINE_WOBBLE * (sin(y * WOBBLE_FREQ + ph) + KINK_AMP * sin(y * WOBBLE_FREQ * KINK_FREQ + 2.0 * ph));
}
float wobbleSlope(int i, float y) {
    float ph = TAU * vineHash(i);
    return VINE_WOBBLE * WOBBLE_FREQ * (cos(y * WOBBLE_FREQ + ph) + KINK_AMP * KINK_FREQ * cos(y * WOBBLE_FREQ * KINK_FREQ + 2.0 * ph));
}
float swayX(int i, float y, Run r) {              // grows up the run
    float up = clamp((y - r.g) / max(r.b - r.g, 1e-3), 0.0, 1.0);
    return SWAY_AMP * up * sin(TAU * SWAY_HZ * iTime - 3.0 * float(i) * VINE_SPACING + vineHash(i));
}
// Branches come up in pairs from one root: at the run's bottom both lean to their pair's middle,
// and part over PAIR_H, so the wood forks in a Y as the art's.
float pairX(int i, float y, Run r) {
    float pr = floor(float(i) / 2.0);
    float h  = PAIR_H * (0.6 + 0.8 * hash12(vec2(pr, 4.4)));
    return (2.0 * pr + 0.5 - float(i)) * VINE_SPACING * (1.0 - smoothstep(0.0, h, y - r.g));
}
float vineX(int i, float y, Run r) { return wobbleX(i, y) + pairX(i, y, r) + swayX(i, y, r); }

float sprout(float len) { return smoothstep(0.0, SPROUT_H, len); }

float smin(float a, float b, float k) {           // polynomial smooth min: the fillet where a twig leaves the trunk
    float h = clamp(0.5 + 0.5 * (b - a) / k, 0.0, 1.0);
    return mix(b, a, h) - k * h * (1.0 - h);
}
// A segment a → b, radius ra at a tapering to rb at b.
float sdTaper(vec2 p, vec2 a, vec2 b, float ra, float rb) {
    vec2  pa = p - a, ba = b - a;
    float h  = clamp(dot(pa, ba) / max(dot(ba, ba), 1e-10), 0.0, 1.0);
    return length(pa - ba * h) - mix(ra, rb, h);
}
vec2 rot(vec2 v, float a) { float c = cos(a), s = sin(a); return vec2(c * v.x - s * v.y, s * v.x + c * v.y); }

// Twig j of vine i: where it leaves the trunk (o), its tip (e), and its fork's tip (f; f == m when
// it doesn't fork, m being where the fork leaves the twig). k is how far it has grown in, 0–1.
struct Twig { vec2 o, e, m, f, dir; float k; bool fork; };

Twig twigOf(int i, int j, Run r, float off, float flip) {
    Twig t;
    float yj   = r.g + (float(j) + off) * TWIG_STEP;
    t.k        = sprout(r.tip - yj);                                  // grows in as the tip passes
    float side = mod(float(j) + flip, 2.0) < 0.5 ? 1.0 : -1.0;
    float a    = TWIG_RISE + TWIG_RISE_VAR * (2.0 * hash12(vec2(float(i), float(j) + 0.5)) - 1.0);
    t.dir  = vec2(side * cos(a), sin(a));
    t.o    = vec2(vineX(i, yj, r), yj);
    t.e    = t.o + t.dir * TWIG_LEN * t.k;
    t.m    = mix(t.o, t.e, FORK_AT);
    t.fork = hash12(vec2(float(i), float(j) + 7.3)) < TWIG_FORK;
    t.f    = t.fork ? t.m + rot(t.dir, side * FORK_ANG) * TWIG_LEN * FORK_LEN * t.k : t.m;
    return t;
}

// A sprig: SPRIG petals fanned round direction d from point s, at scale k, with an ink vein each.
void sprig(inout vec4 acc, vec2 p, vec2 s, vec2 d, float k, float seed, vec3 col) {
    if (length(p - s) > SPRIG_LEN * k + INK_W + 2.0 * AA) return;
    d = normalize(d + vec2(0.0, SPRIG_LIFT));                         // sprigs turn to the light
    float half_len = 0.5 * SPRIG_LEN * k, wid = SPRIG_WID * k;
    float rr = 0.5 * (half_len * half_len / max(wid, 1e-6) + wid);    // vesica of half-length half_len, half-width wid
    float dd = rr - wid;
    int   n  = 3 + int(2.0 * hash12(vec2(seed, 2.9)));                // 3 or 4 petals
    float o  = min(1.0, 3.0 * k);                                     // solid long before it's full size: flat, not a wash
    for (int m = 0; m < 4; m++) {
        if (m >= n) break;
        float a  = SPRIG_FAN * (2.0 * float(m) / float(n - 1) - 1.0) + 0.25 * (hash12(vec2(seed, float(m))) - 0.5);
        vec2  u  = rot(d, a);
        vec2  q  = p - (s + u * half_len);
        vec2  lq = vec2(dot(q, vec2(-u.y, u.x)), dot(q, u));          // across, along
        float sd = sdVesica(lq, rr, dd);
        if (sd > INK_W + 2.0 * AA) continue;
        inked(acc, col, sd, o);
        float vein = length(vec2(lq.x, max(abs(lq.y + 0.15 * half_len) - 0.45 * half_len, 0.0)));
        over(acc, INK, lineA(vein, 0.6 * INK_W) * fillA(sd) * o);
    }
}

// Vine i's wood near p: its trunk and the twigs near p, blended into one
// shape, as a signed distance. Out: bark, the ink of the trunk's bark stroke at p; sat, the wood's
// saturation; nodes, a bit per twig j0 + n (n = 0–2) near p, for sprigs(); j0.
float wood(vec2 p, int i, Run r, out float bark, out int nodes, out int j0) {
    float o    = sprout(r.tip - r.g);
    float y    = clamp(p.y, r.g, r.tip);
    float dx   = (p.x - vineX(i, y, r)) / sqrt(1.0 + pow(wobbleSlope(i, y), 2.0));
    float w    = mix(STEM_TIP_W, STEM_W, clamp((r.tip - y) / STEM_TAPER_H, 0.0, 1.0));
    // A sprouting trunk is thinned past nothing, so its outline doesn't draw a line where it hasn't grown.
    float trunk = length(vec2(dx, p.y - y)) - 0.5 * w + (1.0 - o) * 2.0 * INK_W;
    float dash = smoothstep(0.45, 0.55, noise(vec2(y * BARK_FREQ, float(i) * 7.1)));
    bark = lineA(dx - BARK_HATCH * w, 0.5 * INK_W) * fillA(trunk) * dash;
    float sd   = trunk;

    float off  = 0.5 + 0.5 * hash12(vec2(float(i), 3.1));            // the first twig, in steps above g
    float flip = step(0.5, hash12(vec2(float(i), 5.3)));
    float up   = (1.0 + FORK_LEN) * TWIG_LEN + SPRIG_LEN;             // a twig reaches at most this far above its node
    float down = SPRIG_LEN;                                           // ... and this far below
    j0    = max(int(ceil((p.y - up - r.g) / TWIG_STEP - off)), 0);
    nodes = 0;
    for (int n = 0; n < 3; n++) {
        int j = j0 + n;
        float yj = r.g + (float(j) + off) * TWIG_STEP;
        if (yj > p.y + down || yj >= r.tip || abs(p.x - vineX(i, yj, r)) > up) continue;
        if (!onBody(tapB(wobbleX(i, yj), yj))) continue;              // twigs grow from nodes on the body
        nodes |= 1 << n;
        Twig t = twigOf(i, j, r, off, flip);
        float tw = 0.5 * TWIG_W * t.k, tip = 0.5 * STEM_TIP_W * t.k, thin = (1.0 - min(1.0, 3.0 * t.k)) * 2.0 * INK_W;
        sd = smin(sd, sdTaper(p, t.o, t.e, tw, tip) + thin, WOOD_FILLET);
        if (t.fork) sd = smin(sd, sdTaper(p, t.m, t.f, mix(tw, tip, FORK_AT), tip) + thin, WOOD_FILLET);
    }
    return sd;
}

// The sprigs on vine i's twigs near p (as wood() found them), top twig first, so lower ones overlap it.
void sprigs(inout vec4 acc, vec2 p, int i, Run r, int nodes, int j0) {
    float off  = 0.5 + 0.5 * hash12(vec2(float(i), 3.1));
    float flip = step(0.5, hash12(vec2(float(i), 5.3)));
    vec3  col  = leafColour(r.sat);
    for (int n = 2; n >= 0; n--) {
        if ((nodes & (1 << n)) == 0) continue;
        int  j = j0 + n;
        Twig t = twigOf(i, j, r, off, flip);
        float seed = float(i) * 31.0 + float(j);
        sprig(acc, p, t.e, t.dir, t.k, seed, col);
        if (t.fork) sprig(acc, p, t.f, normalize(t.f - t.m + 1e-6), 0.8 * t.k, seed + 0.5, col);
    }
}

// A daisy at q = 0 of radius fr (its petals' ring; they reach fr × (1 + PETAL_R)), petals swollen e of
// the way out, in petal colour pc; seed picks its turn and petal jitter.
void daisy(inout vec4 acc, vec2 q, float fr, float e, vec3 pc, float sat, float seed) {
    float a0 = TAU * hash12(vec2(seed, 11.3));
    float da = TAU / float(DAISY_N);
    float r0 = 0.55 * fr, r1 = mix(r0, fr * (1.0 + PETAL_R), e), pw = DAISY_PETAL_W * fr * e;
    // Only the three petals nearest q's angle can cover it (the centre hides where more overlap).
    // Even petals lie under odd ones, the same at every pixel, so the overlaps agree.
    int nn = int(floor((atan(q.y, q.x) - a0) / da + 0.5));
    for (int pass = 0; pass < 2; pass++)
        for (int m = nn - 1; m <= nn + 1; m++) {
            float id = mod(float(m), float(DAISY_N));
            if (int(mod(id, 2.0)) != pass) continue;
            float a  = a0 + da * float(m) + 0.15 * (hash12(vec2(seed, id)) - 0.5);
            vec2  u  = vec2(cos(a), sin(a));
            vec2  lq = vec2(dot(q, vec2(-u.y, u.x)), dot(q, u));      // across, along
            float sd = sdTaper(lq, vec2(0.0, r0), vec2(0.0, r1 - pw), 0.7 * pw, pw);
            if (sd > INK_W + 2.0 * AA) continue;
            inked(acc, pc, sd, 1.0);
            float root = 1.0 - smoothstep(r0, mix(r0, r1, 0.55), lq.y); // hatched in ink near the centre
            over(acc, INK, lineA(abs(lq.x) - 0.4 * pw, 0.5 * INK_W) * fillA(sd) * root * e);
        }
    // The centre: an oval, hatched on its shaded side.
    vec2  rad = HEART_R * fr * e * vec2(0.8, 1.05);
    float sd  = (length(q / rad) - 1.0) * min(rad.x, rad.y);
    inked(acc, desaturate(YELLOW, sat), sd, 1.0);
    float step_  = 0.22 * rad.y;
    float stripe = abs(fract(q.y / step_) - 0.5) * step_;
    over(acc, INK, lineA(stripe, 0.5 * INK_W) * fillA(sd + 0.15 * rad.x) * smoothstep(0.0, -0.4 * rad.x, q.x) * e);
}

// The trunk's tip: a sprig, or on DAISY_FRAC of branches a bud, which late in growth opens into a daisy.
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
    if (hash12(vec2(float(i), 13.9)) >= DAISY_FRAC) {              // no daisy: the branch ends in a sprig
        sprig(acc, p, tip, vec2(0.0, 1.0), k, float(i) * 31.0 - 7.0, leafColour(r.sat));
        return;
    }
    inked(acc, leafColour(r.sat), length(p - mix(tip, c, open)) - BUD_R * k, k);   // the bud, later the calyx
    if (open <= 0.0) return;
    float fr = mix(BUD_R, FLOWER_R, open);
    daisy(acc, p - c, fr, smoothstep(0.0, 0.25, open), desaturate(flowerColour(i), r.sat), r.sat, float(i));
}

// The plants over transparent, premultiplied. Branches vine by vine, then buds and flowers on top.
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
    // All the wood near p is one shape, inked once: branches that meet merge, as the art's forks.
    float wd = 1e3, bark = 0.0, sat = SAT_MIN;
    int   nodes[NV * TAPS], j0s[NV * TAPS];
    for (int v = 0; v < NV; v++)
        for (int t = 0; t < TAPS; t++) {
            int s = v * TAPS + t;
            nodes[s] = 0;
            if (!has[s]) continue;
            float bk;
            float d = wood(p, i0 + v - VINE_NEIGHBOURS, runs[s], bk, nodes[s], j0s[s]);
            if (d < wd) sat = runs[s].sat;
            wd = smin(wd, d, WOOD_FILLET);
            bark = max(bark, bk);
        }
    if (wd < INK_W + 2.0 * AA) {
        inked(acc, stemColour(sat), wd, 1.0);
        over(acc, INK, bark * fillA(wd));
    }
    for (int v = 0; v < NV; v++)
        for (int t = 0; t < TAPS; t++) {
            int s = v * TAPS + t;
            if (nodes[s] != 0) sprigs(acc, p, i0 + v - VINE_NEIGHBOURS, runs[s], nodes[s], j0s[s]);
        }
    for (int v = 0; v < NV; v++)
        for (int t = 0; t < TAPS; t++)
            if (has[v * TAPS + t]) bloom(acc, p, i0 + v - VINE_NEIGHBOURS, runs[v * TAPS + t]);
    return acc;
}

// ── Footprints ────────────────────────────────────────────────────────────────
// Where a walker steps, Buffer C leaves a footprint: a clump of FOOT_SPROUTS little branches grows up
// off the floor there, each with a twig and a sprig, the middle one ending in a small daisy. It grows
// fast, holds, then rewinds away (footGrowth). Drawn as the body's plants are, but stands on its own.

void footprint(inout vec4 acc, vec2 p, vec2 at, float g, float seed) {
    if (abs(p.x - at.x) > FOOT_REACH_X || p.y < at.y - FOOT_REACH_DOWN || p.y > at.y + FOOT_REACH_UP) return;
    float sat  = mix(SAT_MIN, SAT_MAX, g);
    float wd   = 1e3;
    vec2  tips[FOOT_SPROUTS], twigs[FOOT_SPROUTS], dirs[FOOT_SPROUTS];
    float ks[FOOT_SPROUTS];
    for (int s = 0; s < FOOT_SPROUTS; s++) {                          // the wood: stems and twigs, one shape
        float h  = hash12(vec2(seed, float(s) + 0.5));
        float x  = at.x + FOOT_SPREAD * (2.0 * (float(s) + 0.5) / float(FOOT_SPROUTS) - 1.0 + 0.4 * (h - 0.5));
        float ht = FOOT_H * (0.6 + 0.4 * hash12(vec2(seed, float(s) + 3.5))) * g;
        float lean = FOOT_LEAN * (2.0 * hash12(vec2(seed, float(s) + 6.5)) - 1.0);
        vec2  o  = vec2(x, at.y);
        tips[s]  = o + vec2(lean * ht, ht);
        float tw = 0.5 * STEM_W * min(1.0, 3.0 * g), tip = 0.5 * STEM_TIP_W * g, thin = (1.0 - min(1.0, 3.0 * g)) * 2.0 * INK_W;
        wd = smin(wd, sdTaper(p, o, tips[s], tw, tip) + thin, WOOD_FILLET);
        // One twig, halfway up, on alternating sides.
        float side = mod(float(s), 2.0) < 0.5 ? 1.0 : -1.0;
        vec2  n  = mix(o, tips[s], 0.5);
        dirs[s]  = vec2(side * cos(TWIG_RISE), sin(TWIG_RISE));
        ks[s]    = smoothstep(0.3, 0.7, g);
        twigs[s] = n + dirs[s] * TWIG_LEN * 0.7 * ks[s];
        wd = smin(wd, sdTaper(p, n, twigs[s], 0.5 * TWIG_W * ks[s], tip) + (1.0 - min(1.0, 3.0 * ks[s])) * 2.0 * INK_W, WOOD_FILLET);
    }
    if (wd < INK_W + 2.0 * AA) inked(acc, stemColour(sat), wd, 1.0);
    for (int s = 0; s < FOOT_SPROUTS; s++) {                          // then sprigs, and the middle one's daisy
        float sd = seed * 17.0 + float(s);
        if (ks[s] > 0.0) sprig(acc, p, twigs[s], dirs[s], ks[s], sd, leafColour(sat));
        if (s == FOOT_SPROUTS / 2) {
            float open = smoothstep(FOOT_FLOWER_FROM, 1.0, g);
            if (open > 0.0 && length(p - tips[s]) < FOOT_FLOWER_R * (1.0 + PETAL_R) + INK_W + 2.0 * AA)
                daisy(acc, p - tips[s], FOOT_FLOWER_R * open, smoothstep(0.0, 0.25, open),
                      desaturate(flowerColour(int(seed * 97.0)), sat), sat, sd);
        } else sprig(acc, p, tips[s], vec2(0.0, 1.0), g, sd + 0.5, leafColour(sat));
    }
}

// Every live footprint near p, over transparent, premultiplied.
vec4 footprints(vec2 fc) {
    vec2  p = fc / iResolution.y;
    vec4  acc = vec4(0.0);
    if (!cNear(iChannel1, p)) return acc;                             // the near grid counts footprints too
    float aspect = iResolution.x / iResolution.y;
    for (int f = 0; f < FOOTPRINTS; f++) {
        vec4 ft = cFoot(iChannel1, f);
        float g = footGrowth(ft.z);
        if (g > 0.0) footprint(acc, p, vec2(ft.x * aspect, ft.y), g, ft.w);
    }
    return acc;
}

// The crayon sun: a waxy, grain-filled disc with a noise-broken edge, and rays in the same hand.
// Level 0 is a muted, paper-mixed yellow with no rays; level 1 is full yellow with its rays out.
vec3 sunColour(vec2 fc) {
    vec2 d = fc / iResolution.y - vec2(iResolution.x / iResolution.y + SUN_POS.x, SUN_POS.y);
    float r = length(d);
    if (r > SUN_R * (1.0 + SUN_EDGE_WOBBLE) + RAY_LEN) return PAPER;
    float lv = clamp(cSun(iChannel1).x, 0.0, 1.0);
    float t = iTime * SUN_WOBBLE_RATE;                                             // a slow wobble; nothing is stored
    float grain = SUN_GRAIN_A * noise(d * SUN_GRAIN + t) + (1.0 - SUN_GRAIN_A) * noise(vec2(d.x + d.y, d.x - d.y) * SUN_GRAIN * SUN_HATCH);
    float cov = 0.0;
    float edge = SUN_R * (1.0 + SUN_EDGE_WOBBLE * (2.0 * noise(d * SUN_EDGE_SCALE + t) - 1.0));
    if (r < edge) {
        float rim = smoothstep(SUN_RIM_FROM, 1.0, r / edge);                   // the stroke round the edge is pressed harder
        cov = smoothstep(SUN_COVER - SUN_FILL_SOFT, SUN_COVER + SUN_FILL_SOFT, grain + SUN_RIM_WEIGHT * rim);
    }
    float len = RAY_LEN * lv;
    float r0 = SUN_R * SUN_RAY_FROM;
    if (len > SUN_RAY_MIN && r > r0 && r < SUN_R + len) {
        float a = atan(d.y, d.x) / TAU * float(SUN_RAYS) + SUN_DRIFT * t;
        float id = mod(floor(a + 0.5), float(SUN_RAYS));   // atan's branch cut splits one ray in two: wrap its id
        float rl = (SUN_R + len - r0) * (1.0 - SUN_RAY_LEN_JITTER + SUN_RAY_LEN_JITTER * hash12(vec2(id, 3.1)));
        float u = (r - r0) / rl;                                       // 0 at the root, 1 at the tip
        float perp = (a - floor(a + 0.5) + SUN_RAY_SKEW * (hash12(vec2(id, 7.7)) - 0.5)) * TAU * r / float(SUN_RAYS);
        float w = SUN_RAY_W * (1.0 - SUN_RAY_TAPER * u) * (1.0 - 0.5 * SUN_RAY_W_JITTER + SUN_RAY_W_JITTER * noise(vec2(u * SUN_RAY_W_RATE, id)));
        if (u < 1.0 && abs(perp) < w) {
            float rg = smoothstep(SUN_COVER - 2.0 * SUN_RAY_SOFT, SUN_COVER - SUN_RAY_SOFT, SUN_RAY_GRAIN * noise(d * SUN_GRAIN + 9.0) + SUN_RAY_FADE * (1.0 - u) + SUN_RAY_BIAS);
            cov = max(cov, rg);
        }
    }
    vec3 c = mix(mix(YELLOW, PAPER, SUN_MUTE), YELLOW, lv);
    return mix(PAPER, c, cov);
}

void mainImage(out vec4 o, in vec2 fc) {
    AA = 1.0 / iResolution.y;
    vec3 col = sunColour(fc);                                         // the sun, under the plants
    vec4 fp  = footprints(fc);                                        // behind the people
    col = fp.rgb + col * (1.0 - fp.a);
    vec4 pl  = plants(fc);
    o = vec4(pl.rgb + col * (1.0 - pl.a), 1.0);
}
