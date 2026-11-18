// Image — paper and its grit, the backdrop, the sun, footprints and each person's tree.  iChannel0 = Buffer B, iChannel1 = Buffer C,
// iChannel2 = blobs. p is in screen heights, origin bottom left, y up; screen-height y and UV y are the same number.
//
// Buffer C grows each person's tree on a grid (see common.glsl, "The tree"): every body cell has a node and a
// parent on the way back to the root; the cells on a seed's path are branches. A pixel draws the branch cells
// within TREE_R of its own: the segment from each node to its parent's, as far as growth has reached, as ink
// wood (all of it one shape, inked once, so forks are seamless), and a sprig or a daisy on each seed. Flowers are small and pale near the
// root, and larger and bolder further along the tree (so later, as growth climbs and slows).

const float TAU = 6.2831853;

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
// The style guide's pale yellow, light blue and orange; and a centre that stands out from each.
vec3 flowerColour(float seed) {
    float h = hash12(vec2(seed, 9.7));
    return h < 0.34 ? PALE : h < 0.67 ? SKY : ORANGE;
}
vec3 heartColour(float seed) { return hash12(vec2(seed, 9.7)) < 0.34 ? ORANGE : YELLOW; }   // stands out from its petals
// A flower colour as drawn: paled toward the paper, keeping its hue, by how low it is (bold 0–1) and how
// young the person's growth is (sat, from SAT_MIN to SAT_MAX as it ripens): pale, never grey.
vec3 tint(vec3 c, float sat, float bold) {
    float ripe = clamp((sat - SAT_MIN) / (SAT_MAX - SAT_MIN), 0.0, 1.0);
    return mix(PAPER, c, bold * mix(BOLD_YOUNG, 1.0, ripe));
}

// iq's vesica: a pointed leaf along y, half-length sqrt(r² − d²), half-width r − d.
float sdVesica(vec2 p, float r, float d) {
    p = abs(p);
    float b = sqrt(r * r - d * d);
    return ((p.y - b) * d > p.x * b) ? length(p - vec2(0.0, b)) : length(p - vec2(-d, 0.0)) - r;
}

vec4 tapB(float x, float y) {                     // B under screen point (x, y); 0 off screen
    float aspect = iResolution.x / iResolution.y;
    if (y < 0.0 || y >= 1.0 || x < 0.0 || x >= aspect) return vec4(0.0);
    return texelFetch(iChannel0, ivec2(vec2(x / aspect, y) * iChannelResolution[0].xy), 0);
}
// Is t on a body (or its held shape)? B's membership has hysteresis, so a flickering edge holds
// still; a softer test on raw presence here would bring the flicker back.
bool onBody(vec4 t) { return bOwner(t) > 0 && bHold(t) > 0.0; }


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

// A daisy at q = 0 of radius fr (its petals' ring; they reach fr × (1 + PETAL_R)), petals swollen e of
// the way out, petals pc and centre hc; seed picks its turn and petal jitter.
void daisy(inout vec4 acc, vec2 q, float fr, float e, vec3 pc, vec3 hc, float seed) {
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
    inked(acc, hc, sd, 1.0);
    float step_  = 0.22 * rad.y;
    float stripe = abs(fract(q.y / step_) - 0.5) * step_;
    over(acc, INK, lineA(stripe, 0.5 * INK_W) * fillA(sd + 0.15 * rad.x) * smoothstep(0.0, -0.4 * rad.x, q.x) * e);
}

// A daisy's pop as it opens (o 0–1): .x its size, easing out past 1 (POP_BACK), .y its stretch along the
// stem (POP_STRETCH): out while it shoots open, squashed while it overshoots, 1 open and closed.
vec2 pop(float o) {
    float u = o - 1.0;
    return vec2(1.0 + (POP_BACK + 1.0) * u * u * u + POP_BACK * u * u, 1.0 + POP_STRETCH * sin(TAU * o));
}
// Where to draw an unstretched shape so it shows stretched st along unit direction d, and 1 / st across.
vec2 stretchQ(vec2 q, vec2 d, float st) {
    float a = dot(q, d);
    return (a / st) * d + (q - a * d) * st;
}

// ── The tree ─────────────────────────────────────────────────────────────────

// A cell's node, in screen heights, swaying a little more the further it is along the tree (u 0–1).
vec2 nodeOf(ivec2 cell, vec4 t, float u) {
    vec2 j = vec2(hash12(vec2(cell) + 5.1), hash12(vec2(cell) + 8.3)) - 0.5;   // a fixed jitter: no grid shows
    vec2 n = (vec2(cell) + 0.5 + treeOffset(t) + TREE_JITTER * j) * TREE_CELL;
    n.x += SWAY_AMP * u * sin(TAU * SWAY_HZ * iTime + 3.0 * n.y + float(treeOwner(t)));
    return n;
}
// Wood along A → B (path distances sA < sB, radii rA, rB), as far as the growth front has reached.
float woodSeg(vec2 p, vec2 A, vec2 B, float sA, float sB, float rA, float rB, float front) {
    if (front <= sA) return 1e3;
    float f = clamp((front - sA) / max(sB - sA, 1e-4), 0.0, 1.0);
    return sdTaper(p, A, mix(A, B, f), rA, mix(rA, rB, f));
}
float branchW(float seeds) { return clamp(TREE_W_K * sqrt(max(seeds, 1.0)), STEM_TIP_W, TREE_ROOT_W); }

// Every tree near p, over transparent, premultiplied: the wood, then sprigs, then flowers.
vec4 tree(vec2 fc) {
    vec2  p = fc / iResolution.y;
    vec4  acc = vec4(0.0);
    if (!cNear(iChannel1, p, iResolution.xy)) return acc;            // nothing near: paper, one fetch
    float aspect = iResolution.x / iResolution.y;
    ivec2 c0 = ivec2(floor(p / TREE_CELL));
    float wood = 1e3;
    float slack = 2.5 * TREE_CELL + REACH * POP_REACH + INK_W;   // a node's drawing reaches at most this far
    int   nt = 0;
    vec4  tipA[MAX_TIPS], tipB[MAX_TIPS];                              // pos, dir · tips: scale, u, open, sat
    float tipS[MAX_TIPS];                                              // seed
    for (int dy = -TREE_R; dy <= TREE_R; dy++)
        for (int dx = -TREE_R; dx <= TREE_R; dx++) {
            ivec2 cell = c0 + ivec2(dx, dy);
            vec4  t = cTree(iChannel1, cell, iResolution.xy);
            int   own = treeOwner(t);
            if (own == 0 || own > SLOTS || t.x >= TREE_FAR || t.y < 0.5) continue;   // no branch here
            vec4  tp = cTreeP(iChannel1, own - 1);
            if (tp.x <= 0.0) continue;
            float u  = clamp(t.x / tp.x, 0.0, 1.0);
            vec2  P  = nodeOf(cell, t, u);
            if (length(p - P) > slack) continue;
            vec4  bt = tapB(P.x, P.y);
            float front = tp.z * tp.x * (bt.r >= BODY_ON ? 1.0 : bHold(bt));   // growth × the farthest
            // The branch runs P → parent Q → grandparent R. Corners are cut: this cell draws the curve from
            // the middle of R–Q round Q to the middle of Q–P (its children's curves carry on from there), and
            // a tip the straight half on to P. Path distance s along the way says how far the growth reaches.
            vec2  Q, R;
            float dQ, dR, sQ, sR;
            vec4  b = cBase(iChannel1, own - 1);
            vec2  root = tp.w > 0.0 ? tp.wy : vec2(b.x * aspect, b.y);
            int   pa = treeParent(t);
            if (pa == 0) { Q = root; dQ = 0.0; sQ = t.y; R = root; dR = 0.0; sR = t.y; }
            else {
                ivec2 c2 = cell + TREE_DIRS[pa - 1];
                vec4  t2 = cTree(iChannel1, c2, iResolution.xy);
                if (treeOwner(t2) != own || t2.x >= TREE_FAR) continue;   // its parent just left the body: re-settling
                Q = nodeOf(c2, t2, clamp(t2.x / tp.x, 0.0, 1.0)); dQ = t2.x; sQ = t2.y;
                int pa2 = treeParent(t2);
                if (pa2 == 0) { R = root; dR = 0.0; sR = sQ; }
                else {
                    ivec2 c3 = c2 + TREE_DIRS[pa2 - 1];
                    vec4  t3 = cTree(iChannel1, c3, iResolution.xy);
                    if (treeOwner(t3) != own || t3.x >= TREE_FAR) { R = Q; dR = dQ; sR = sQ; }   // as above: no corner
                    else { R = nodeOf(c3, t3, clamp(t3.x / tp.x, 0.0, 1.0)); dR = t3.x; sR = t3.y; }
                }
            }
            if (dQ >= front && pa != 0) continue;                      // the growth hasn't reached this branch
            float rP = 0.5 * branchW(t.y), rQ = 0.5 * branchW(sQ), rR = 0.5 * branchW(sR);
            vec2  M1 = 0.5 * (P + Q), M2 = 0.5 * (Q + R), C = 0.25 * M2 + 0.5 * Q + 0.25 * M1;
            float s1 = 0.5 * (t.x + dQ), s2 = 0.5 * (dQ + dR);
            if (pa == 0) wood = smin(wood, woodSeg(p, root, P, 0.0, t.x, rQ * 1.2, rP, front), TREE_FILLET);
            else {
                wood = smin(wood, woodSeg(p, M2, C, s2, dQ, 0.5 * (rQ + rR), rQ, front), TREE_FILLET);
                wood = smin(wood, woodSeg(p, C, M1, dQ, s1, rQ, 0.5 * (rP + rQ), front), TREE_FILLET);
            }
            bool tip = t.y - (treeSeed(cell) ? 1.0 : 0.0) < 0.5;     // no seed above: the branch ends here
            if (tip && pa != 0) wood = smin(wood, woodSeg(p, M1, P, s1, t.x, 0.5 * (rP + rQ), rP, front), TREE_FILLET);
            float k = smoothstep(t.x - TREE_CELL, t.x + 0.5 * TREE_CELL, front);   // a seed's sprig grows in as growth reaches it
            if (treeSeed(cell) && k > 0.0 && nt < MAX_TIPS && length(p - P) < REACH * POP_REACH + SPRIG_LEN + INK_W) {
                tipA[nt] = vec4(P, normalize(P - Q + vec2(0.0, 1e-4)));
                tipB[nt] = vec4(k, u, smoothstep(0.0, TREE_OPEN_D, front - t.x), mix(SAT_MIN, SAT_MAX, tp.z));
                tipS[nt] = hash12(vec2(cell) + 0.37);
                nt++;
            }
        }
    if (wood < INK_W + 2.0 * AA) inked(acc, PAPER, wood, 1.0);         // unfilled: ink on paper, as the art
    for (int n = 0; n < MAX_TIPS; n++) {                               // sprigs, on the nodes without a flower
        if (n >= nt) break;
        if (tipS[n] < TWIG_FLOWER_FRAC && tipB[n].z > 0.0) continue;
        sprig(acc, p, tipA[n].xy, tipA[n].zw, tipB[n].x, tipS[n] * 97.0, PAPER);
    }
    for (int n = 0; n < MAX_TIPS; n++) {                               // flowers on top
        if (n >= nt) break;
        if (tipS[n] >= TWIG_FLOWER_FRAC || tipB[n].z <= 0.0) continue;
        float u  = tipB[n].y, open = tipB[n].z;
        vec2  pp = pop(open);
        float fr = mix(TWIG_FLOWER_R_MIN, FLOWER_R, u * u) * pp.x;
        vec2  q  = p - tipA[n].xy;
        if (length(q) > fr * (1.0 + PETAL_R) * max(pp.y, 1.0 / pp.y) + INK_W + 2.0 * AA) continue;
        q = stretchQ(q, tipA[n].zw, pp.y);
        float bold = mix(BOLD_MIN, 1.0, u * u), seed = tipS[n] * 97.0;
        daisy(acc, q, fr, smoothstep(0.0, 0.4, open), tint(flowerColour(seed), tipB[n].w, bold),
              tint(heartColour(seed), tipB[n].w, bold), seed);
    }
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
    // The stems pop up as the daisies do (and, fading, swell a little before they sink away): height eases out
    // past full and back, tall and thin while they shoot up, short and stout while they overshoot.
    vec2  pp = pop(g);
    for (int s = 0; s < FOOT_SPROUTS; s++) {                          // the wood: stems and twigs, one shape
        float h  = hash12(vec2(seed, float(s) + 0.5));
        float x  = at.x + FOOT_SPREAD * (2.0 * (float(s) + 0.5) / float(FOOT_SPROUTS) - 1.0 + 0.4 * (h - 0.5));
        float ht = FOOT_H * (0.6 + 0.4 * hash12(vec2(seed, float(s) + 3.5))) * pp.x * pp.y;
        float lean = FOOT_LEAN * (2.0 * hash12(vec2(seed, float(s) + 6.5)) - 1.0);
        vec2  o  = vec2(x, at.y);
        tips[s]  = o + vec2(lean * ht, ht);
        float tw = 0.5 * STEM_W * min(1.0, 3.0 * g) / pp.y, tip = 0.5 * STEM_TIP_W * g / pp.y, thin = (1.0 - min(1.0, 3.0 * g)) * 2.0 * INK_W;
        wd = smin(wd, sdTaper(p, o, tips[s], tw, tip) + thin, WOOD_FILLET);
        // One twig, halfway up, on alternating sides.
        float side = mod(float(s), 2.0) < 0.5 ? 1.0 : -1.0;
        vec2  n  = mix(o, tips[s], 0.5);
        dirs[s]  = vec2(side * cos(TWIG_RISE), sin(TWIG_RISE));
        ks[s]    = smoothstep(0.3, 0.7, g);
        twigs[s] = n + dirs[s] * TWIG_LEN * 0.7 * ks[s];
        wd = smin(wd, sdTaper(p, n, twigs[s], 0.5 * TWIG_W * ks[s], tip) + (1.0 - min(1.0, 3.0 * ks[s])) * 2.0 * INK_W, WOOD_FILLET);
    }
    if (wd < INK_W + 2.0 * AA) inked(acc, PAPER, wd, 1.0);
    for (int s = 0; s < FOOT_SPROUTS; s++) {                          // then sprigs, and the middle one's daisy
        float sd = seed * 17.0 + float(s);
        if (ks[s] > 0.0) sprig(acc, p, twigs[s], dirs[s], ks[s], sd, PAPER);
        if (s == FOOT_SPROUTS / 2) {
            float open = smoothstep(FOOT_FLOWER_FROM, 1.0, g);
            vec2  pp   = pop(open);
            if (open > 0.0 && length(p - tips[s]) < FOOT_FLOWER_R * (1.0 + PETAL_R) * POP_REACH + INK_W + 2.0 * AA)
                daisy(acc, stretchQ(p - tips[s], vec2(0.0, 1.0), pp.y), FOOT_FLOWER_R * pp.x, smoothstep(0.0, 0.25, open),
                      tint(flowerColour(seed), sat, 1.0), tint(heartColour(seed), sat, 1.0), sd);
        } else sprig(acc, p, tips[s], vec2(0.0, 1.0), g, sd + 0.5, PAPER);
    }
}

// Every live footprint near p, over transparent, premultiplied.
vec4 footprints(vec2 fc) {
    vec2  p = fc / iResolution.y;
    vec4  acc = vec4(0.0);
    if (!cNear(iChannel1, p, iResolution.xy)) return acc;             // the tree grid's near flag counts footprints too
    float aspect = iResolution.x / iResolution.y;
    for (int f = 0; f < FOOTPRINTS; f++) {
        vec4 ft = cFoot(iChannel1, f);
        float g = footGrowth(ft.z);
        if (g > 0.0) footprint(acc, p, vec2(ft.x * aspect, ft.y), g, ft.w);
    }
    return acc;
}

// ── The backdrop ──────────────────────────────────────────────────────────────

// A hill's height above the horizon at x: a smooth bump, 0 off it. hill = HILL_A or HILL_B.
float hillY(vec3 hill, float x, float aspect) {
    float u = (x / aspect - hill.x) / hill.y;
    return abs(u) < 1.0 ? hill.z * 0.5 * (1.0 + cos(0.5 * TAU * u)) : 0.0;
}
// A row of two hills standing on a wandering line at height y0, b behind a: p's distance from its ink. The
// line is drawn where no hill stands, a's outline whole, and b's where it rises above a.
float hillRow(vec2 p, float y0, vec3 a, vec3 b, float aspect) {
    float base = y0 + HORIZON_WOBBLE * (2.0 * noise(vec2(p.x * HORIZON_FREQ, 40.0 * y0)) - 1.0);
    float ha = hillY(a, p.x, aspect), hb = hillY(b, p.x, aspect);
    float d = ha > 0.0 ? abs(p.y - base - ha) : hb > 0.0 ? 1e3 : abs(p.y - base);
    return hb > ha ? min(d, abs(p.y - base - hb)) : d;
}
// Ink coverage of the backdrop at p: the horizon and its hills, the nearer row, the grass.
float backdrop(vec2 p) {
    float top = HORIZON_Y + HORIZON_WOBBLE + max(HILL_A.z, HILL_B.z), pad = INK_W + 2.0 * AA;
    if (p.y > top + pad || p.y < min(GRASS_Y0, NEAR_Y - HORIZON_WOBBLE) - pad) return 0.0;   // most of the page: one compare
    float aspect = iResolution.x / iResolution.y;
    float a = lineA(min(hillRow(p, HORIZON_Y, HILL_A, HILL_B, aspect), hillRow(p, NEAR_Y, NEAR_A, NEAR_B, aspect)), INK_W);
    for (int i = 0; i < GRASS_TUFTS; i++) {
        float fi = float(i);
        vec2  c = vec2(aspect * (fi + 0.5 + 0.7 * (hash12(vec2(fi, 1.3)) - 0.5)) / float(GRASS_TUFTS),
                       mix(GRASS_Y0, GRASS_Y1, hash12(vec2(fi, 4.7))));
        vec2  q = p - c;
        if (abs(q.x) > GRASS_H + pad || q.y < -pad || q.y > GRASS_H + pad) continue;
        for (int b = 0; b < 3; b++) {                                  // blades fanned from one point
            float fb = float(b), h = hash12(vec2(fi, fb + 7.1));
            vec2  tip = GRASS_H * (0.6 + 0.4 * h) * rot(vec2(0.0, 1.0), 0.45 * (1.0 - fb) + 0.3 * (h - 0.5));
            a = max(a, lineA(sdTaper(q, vec2(0.0), tip, 0.0, 0.0), INK_W));
        }
    }
    return a;
}

// ── The sun ───────────────────────────────────────────────────────────────────

// The sun, over transparent, premultiplied: drawn as a flower is, a flat yellow disc in an ink outline, hatched on
// the side away from the light, with rays as inked petals. Its centre is just inside the top-right corner, so a
// third of the disc shows. Level 0 has no rays; at level 1 they are full length.
vec4 sun(vec2 fc) {
    vec4 acc = vec4(0.0);
    vec2 d = fc / iResolution.y - (vec2(iResolution.x / iResolution.y, 1.0) - SUN_PEEK * SUN_R);
    float r = length(d);
    if (r > SUN_REACH + 2.0 * AA) return acc;
    float lv = clamp(cSun(iChannel1).x, 0.0, 1.0);
    float t = iTime * SUN_WOBBLE_RATE;                                // a slow wobble; nothing is stored
    // The rays, under the disc. Only the nearest can cover p: they're far apart for their width.
    float len = RAY_LEN * lv, r0 = SUN_R * SUN_RAY_FROM;
    if (len > SUN_RAY_MIN && r > r0 - SUN_RAY_W - SUN_INK_W) {
        float a  = atan(d.y, d.x) / TAU * float(SUN_RAYS) + SUN_DRIFT * t;
        float k  = floor(a + 0.5);
        float id = mod(k, float(SUN_RAYS));                           // atan's branch cut splits one ray in two: wrap its id
        float ang = (k - SUN_RAY_SKEW * (hash12(vec2(id, 7.7)) - 0.5) - SUN_DRIFT * t) * TAU / float(SUN_RAYS);
        vec2  u  = vec2(cos(ang), sin(ang));
        float rl = (SUN_R + len - r0) * (1.0 - SUN_RAY_LEN_JITTER + SUN_RAY_LEN_JITTER * hash12(vec2(id, 3.1)));
        float w  = SUN_RAY_W * min(1.0, 2.0 * lv);                    // thin while short, as a petal opens
        inked(acc, SUN_COL, sdTaper(d, u * r0, u * (r0 + rl), w, w * (1.0 - SUN_RAY_TAPER)), 1.0);
    }
    // The disc: its rim wanders a little, by hand.
    float edge = SUN_R * (1.0 + SUN_EDGE_WOBBLE * (2.0 * noise(d * SUN_EDGE_SCALE + t) - 1.0));
    float sd = r - edge;
    if (sd < SUN_INK_W + 2.0 * AA) {
        over(acc, SUN_COL, fillA(sd));
        // Shading, as on a daisy's centre: ink hatching in a crescent along the rim away from the light (up and to
        // the right), parallel to the light. Each line reaches its own way in, so the inner edge is ragged.
        vec2  L = vec2(0.70710678);
        float across = dot(d, vec2(-L.y, L.x)), line = floor(across / SUN_HATCH_STEP);
        float away = dot(d / max(r, 1e-6), -L);                       // 1 facing straight away from the light
        float reach = SUN_SHADE_W * SUN_R * smoothstep(-0.2, 0.9, away) * (1.0 - SUN_HATCH_JITTER * hash12(vec2(line, 5.3)));
        float stripe = abs(fract(across / SUN_HATCH_STEP) - 0.5) * SUN_HATCH_STEP;
        over(acc, INK, lineA(stripe, 0.5 * INK_W) * fillA(sd + 0.4 * SUN_INK_W) * fillA(-sd - reach));
        over(acc, INK, lineA(sd, SUN_INK_W));
    }
    return acc;
}

// ── Grit ──────────────────────────────────────────────────────────────────────

// The paper's tooth: ink coverage of sparse short flecks and dots, one per cell at most, static. A fleck is shorter
// than a cell, so only the 3 × 3 cells round p can reach it.
float grit(vec2 p) {
    vec2  g = floor(p / GRIT_CELL);
    float a = 0.0;
    for (int dy = -1; dy <= 1; dy++)
        for (int dx = -1; dx <= 1; dx++) {
            vec2 c = g + vec2(dx, dy);
            if (hash12(c + 0.71) > GRIT_FRAC) continue;
            vec2  m  = (c + vec2(hash12(c + 3.3), hash12(c + 6.1))) * GRIT_CELL;
            float an = TAU * hash12(c + 9.4), h = hash12(c + 12.2);
            vec2  u  = 0.5 * GRIT_LEN * h * h * vec2(cos(an), sin(an));    // mostly short: dots and specks
            a = max(a, lineA(sdTaper(p, m - u, m + u, 0.0, 0.0), GRIT_W) * (0.5 + 0.5 * hash12(c + 15.8)));
        }
    return a;
}

void mainImage(out vec4 o, in vec2 fc) {
    AA = 1.0 / iResolution.y;
    vec2 p = fc / iResolution.y;
    vec3 col = mix(PAPER, INK, GRIT_INK * grit(p));                   // the page, with its grit
    col = mix(col, INK, BACKDROP_INK * backdrop(p));                  // the backdrop
    vec4 sn  = sun(fc);                                               // the sun, under the plants
    col = sn.rgb + col * (1.0 - sn.a);
    vec4 fp  = footprints(fc);                                        // behind the people
    col = fp.rgb + col * (1.0 - fp.a);
    vec4 pl  = tree(fc);
    o = vec4(pl.rgb + col * (1.0 - pl.a), 1.0);
}
