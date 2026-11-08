// Image — rainbow poop. iChannel0 = Body (A), iChannel1 = state (B), iChannel2 = blobs.
// Back to front: paper and clouds → ground puddles → people → splats on people → falling poops.
// Positions: `p` is in screen heights (x 0…aspect, y 0…1); state and Body are in UV.

#define BODY  iChannel0
#define B     iChannel1
#define BLOBS iChannel2

float PX;        // one pixel, in screen heights
float ASPECT;

vec2 uvToP(vec2 uv) { return uv * vec2(ASPECT, 1.0); }
vec2 pToUv(vec2 p)  { return p / vec2(ASPECT, 1.0); }

// Paint `c` over `col` with coverage `a`.
void over(inout vec3 col, vec3 c, float a) { col = mix(col, c, clamp(a, 0.0, 1.0)); }

// ── Sky ───────────────────────────────────────────────────────────────────────
void drawClouds(inout vec3 col, vec2 p) {
    if (p.y < CLOUD_Y - 0.1) return;
    for (int c = 0; c < 3; c++) {
        float fc = float(c);
        float span = ASPECT + 0.6;
        vec2  at = vec2(mod(fc * 0.71 * span + iTime * (0.010 + 0.004 * fc), span) - 0.3,
                        CLOUD_Y + 0.05 * hash11(fc * 4.1));
        vec2  q = p - at;
        if (abs(q.x) > 0.25 || abs(q.y) > 0.12) continue;
        float d = 1e9;
        for (int k = 0; k < 4; k++) {
            float fk = float(k);
            vec2  o = vec2((fk - 1.5) * 0.055, 0.012 * sin(fk * 2.3 + fc));
            d = smin(d, length(q - o) - (0.038 + 0.014 * hash11(fk + fc * 9.0)), 0.02);
        }
        d = max(d, -q.y - 0.015);                           // flat bottom
        over(col, WARM_WHITE, fill(d, PX));
        over(col, INK, pen(abs(d), INK_W_LIGHT, PX));
    }
}

// ── Splats ────────────────────────────────────────────────────────────────────
// A rainbow splat of radius r around the origin: a lumpy blob in concentric bands (red outside,
// violet in the middle), satellite droplets and, if `drips`, drips running down. rgb + coverage.
vec4 splat(vec2 q, float r, float seed, float age, bool drips) {
    float s = smoothstep(0.0, POP_S, age);
    r *= max(s * (1.0 + 0.35 * sin(3.14159 * s)), 1e-3);    // splat in with a little overshoot
    float ang = atan(q.y, q.x);
    float rr = r * (1.0 + SPLAT_LUMP * (0.6 * sin(5.0 * ang + seed * 40.0) + 0.4 * sin(3.0 * ang - seed * 23.0)));
    float d = length(q) - rr;
    vec3  c = rainbow(5 - int(clamp(length(q) / rr, 0.0, 0.999) * 6.0));
    int   shift = int(seed * 6.0);
    for (int i = 0; i < 4; i++) {
        float fi = float(i), h = hash11(seed * 31.0 + fi);
        float a  = seed * 6.2832 + fi * 1.7 + h;
        float ds = length(q - r * (1.35 + 0.35 * h) * vec2(cos(a), sin(a))) - r * (0.12 + 0.12 * h);
        if (ds < d) { d = ds; c = rainbow(shift + i); }
    }
    if (drips) {
        float grow = pow(smoothstep(0.0, DRIP_S, age), 0.6);
        for (int i = 0; i < 3; i++) {
            float fi = float(i), h = hash11(seed * 17.0 + fi * 5.0);
            float x  = r * (-0.55 + 0.55 * fi + 0.2 * (h - 0.5));
            float len = DRIP_LEN * r * (0.4 + 0.6 * h) * grow;
            vec2  a = vec2(x, -0.3 * r), b = a - vec2(0.0, len);
            float dd = min(sdSegment(q, a, b) - 0.15 * r, length(q - b) - 0.21 * r * grow);
            if (dd < d) { d = dd; c = rainbow(shift + 2 * i + 1); }
        }
    }
    float a = fill(d, PX);
    float ink = pen(abs(d), INK_W, PX);
    return vec4(mix(c, INK, ink / max(max(a, ink), 1e-4)), max(a, ink));
}

void drawSplats(inout vec3 col, vec2 p, vec2 uv) {
    float clip = smoothstep(0.45, 0.55, texture(BODY, uv).r);   // the people fill's own edge (0.5)
    if (clip <= 0.0) return;                                 // splats live on people only
    for (int k = 0; k < SLOTS; k++) {
        float presence = sSlot(B, k).z;
        if (presence <= 0.0) continue;
        vec4  an = sAnchor(B, k);
        float h = an.z, r = max(SPLAT_R * h, SPLAT_R_MIN);
        vec2  a = uvToP(an.xy);
        float reach = r * (DRIP_LEN + 2.0);
        for (int j = SPLATS - 1; j >= 0; j--) {              // newest on top
            vec4 s = sSplat(B, k, j);
            if (s.z >= SPLAT_LIFE_S) continue;
            vec2 q = p - (a + s.xy * h);
            if (dot(q, q) > reach * reach) continue;
            float alpha = presence * (1.0 - smoothstep(SPLAT_LIFE_S - SPLAT_FADE_S, SPLAT_LIFE_S, s.z));
            vec4 sp = splat(q, r, s.w, s.z, true);
            over(col, sp.rgb, sp.a * alpha * clip);
        }
    }
}

void drawGround(inout vec3 col, vec2 p) {
    const float R = GROUND_R;
    for (int j = GROUNDS - 1; j >= 0; j--) {
        vec4 g = sGround(B, j);
        if (g.z >= GROUND_LIFE_S) continue;
        vec2 q = p - uvToP(g.xy);
        if (abs(q.x) > 2.5 * R || abs(q.y) > R) continue;
        q.y *= GROUND_SQUASH;
        vec4 sp = splat(q, R, g.w, g.z, false);
        over(col, sp.rgb, sp.a * (1.0 - smoothstep(GROUND_LIFE_S - GROUND_FADE_S, GROUND_LIFE_S, g.z)));
    }
}

// ── People ────────────────────────────────────────────────────────────────────
float present(vec2 uv) { return step(0.5, texture(BODY, uv).r); }

void drawPeople(inout vec3 col, vec2 p, vec2 uv) {
    float r = max(INK_W_HEAVY, PX);
    if (present(uv) > 0.5) { col = WARM_WHITE; return; }
    float edge = 0.0;                                        // outline: outside, within a heavy pen
    for (int i = 0; i < 8; i++) {
        float a = float(i) * 0.78539816;
        edge = max(edge, present(pToUv(p + r * vec2(cos(a), sin(a)))));
    }
    over(col, INK, edge);
}

// ── Falling poops ─────────────────────────────────────────────────────────────
void drawPoops(inout vec3 col, vec2 p) {
    for (int k = 0; k < SLOTS; k++) {
        vec4 dr = sDrop(B, k);
        if (dr.x < 0.5) continue;
        vec4  pp = sPoop(B, k);
        float c = toScreen(pp.xy).x;
        vec2  at = vec2(c + SWAY * sin(dr.w * SWAY_W + pp.z), pp.y);   // as Buffer B's poopAt()
        vec2  q = p - at;
        if (dot(q, q) > 9.0 * POOP_R * POOP_R) continue;
        // A drop falling straight down, leaning into its sway: the round end leads, the point trails.
        vec2  fwd = normalize(vec2(SWAY * SWAY_W * cos(dr.w * SWAY_W + pp.z), -FALL_SPEED));
        float y = dot(q, -fwd), x = dot(q, vec2(-fwd.y, fwd.x));
        float d = y > 0.0 ? length(vec2(x, y * 0.45)) - POOP_R : length(q) - POOP_R;
        over(col, rainbow(int(clamp((y / POOP_R + 1.0) * 1.5, 0.0, 5.0))), fill(d, PX));
        over(col, INK, pen(abs(d), INK_W, PX));
    }
}

void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    ASPECT = iResolution.x / iResolution.y;
    PX = 1.0 / iResolution.y;
    vec2 uv = fragCoord / iResolution.xy;
    vec2 p = uvToP(uv);

    vec3 col = PAPER;
    drawClouds(col, p);
    drawGround(col, p);
    drawPeople(col, p, uv);
    drawSplats(col, p, uv);
    drawPoops(col, p);
    fragColor = vec4(col, 1.0);
}
