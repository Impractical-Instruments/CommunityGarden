// Watercolor smudge — shared tunables and helpers.
// Spec: docs/superpowers/specs/2026-11-07-watercolor-smudge-design.md
// Approved sketch: docs/superpowers/specs/2026-11-07-watercolor-smudge-mockup.html
//
// Sizes are in screen heights: q = uv * vec2(aspect, 1). Times are seconds.
// Retune on site and press R to reload.

// ── Smear ────────────────────────────────────────────────────────────────────
const float SMEAR_STRENGTH = 1.5;    // paint speed / edge speed (sketch was 0.63). Second to FLOW_EPS in effect
const float THIN           = 0.5;    // what counts as an extremity: 0 only the thinnest … 1 almost all
const float RING_R1        = 0.045;  // extremity rings: how much of these is Body decides thin vs. broad
const float RING_R2        = 0.08;
const float STREAK_BASE    = 0.7;    // finger streaks across a stroke: base + amp × noise
const float STREAK_AMP     = 0.6;
const float STREAK_FREQ    = 45.0;   // streaks per screen height
const float MIX_MOVE       = 0.5;    // pigment mixing where paint is moving
const float MIX_WET        = 0.04;   // ... and where it's still wet

// ── Motion (normal flow from the eased Body changing between frames) ─────────
const float BODY_SOFT      = 0.04;   // softens the Body edge (screen heights). The camera's 10 Hz frames move a
                                     // limb ~0.07 per frame; a soft edge wider than that makes the cross-fade
                                     // between frames read as a sliding edge, which carries paint along
const float BODY_EASE_S    = 0.12;   // eases the 10 Hz Body so flow is smooth and 1-px flicker averages out
const float FLOW_TAP       = 0.006;  // gradient half-step, screen heights
const float FLOW_EPS       = 0.25;   // regularises v = −dB/dt · ∇B / (|∇B|² + eps). The biggest smear knob: 4.0 swamped
                                     // |∇B|² and underestimated limb speed several-fold; lower = stronger smear
const float FLOW_MAX       = 2.5;    // screen heights per second
const float MIN_FLOW       = 0.1;    // edge motion slower than this (screen heights/s) is ignored: 1-camera-px jitter is ~0.05, limbs 0.5–1.5
const float BALANCE_LO     = 0.35;   // movement gains Body ahead and loses it behind in equal measure;
const float BALANCE_HI     = 0.7;    // appearing, vanishing and flicker only gain or only lose. |gain−loss|/(gain+loss)
                                     // above BALANCE_LO starts suppressing the smear, fully by BALANCE_HI.
                                     // Known cost: an arm reaching along its own axis only gains, so it doesn't
                                     // smear; raise BALANCE_LO/HI at the rig if reaching matters more than flicker
const float MIX_TAP        = 0.0045; // pigment-mixing neighbourhood, screen heights

// ── Wet look ─────────────────────────────────────────────────────────────────
const float WET_DECAY      = 0.2;    // per second; smears look wet for ~5 s
const float WET_DARKEN     = 0.15;   // wet paint reads this much darker

// ── Heal ─────────────────────────────────────────────────────────────────────
const float HEAL_DELAY_S   = 2.0;    // room empty this long before healing starts
const float HEAL_TIME_S    = 10.0;   // then ~95 % healed after this long
const float PRESENT_HEAL   = 0.004;  // per second while anyone is present (keeps drift bounded)
const float HEAL_FLOOR     = 0.05;   // min heal speed (colour/s) while healing: 16-bit can't do the exp tail
const float EMPTY_CLAMP_S  = 10.0;   // empty-room timer clamp; 16-bit can't count 1/30 s steps near 99

// ── Display ──────────────────────────────────────────────────────────────────
const float DISTURB_LO     = 0.01;   // |canvas − original| below this shows the image untouched
const float DISTURB_HI     = 0.04;   // ... above this shows the canvas

const float T_CLAMP        = 99.0;   // every "seconds since" counter clamps here
const float PAINT_FLOOR    = 1.0 / 512.0;  // canvas paint floor: keeps black paint distinct from a cleared buffer
const vec3  PAPER          = vec3(0.965, 0.94, 0.885);

// ── Noise ────────────────────────────────────────────────────────────────────
float hash(vec2 p) { p = fract(p * vec2(123.34, 456.21)); p += dot(p, p + 45.32); return fract(p.x * p.y); }
float vn(vec2 p) {
    vec2 i = floor(p), f = fract(p);
    f = f * f * (3.0 - 2.0 * f);
    return mix(mix(hash(i), hash(i + vec2(1, 0)), f.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), f.x), f.y);
}
float fbm(vec2 p) { float s = 0.0, a = 0.5; for (int i = 0; i < 5; i++) { s += a * vn(p); p = p * 2.03 + 17.1; a *= 0.5; } return s; }
float lum(vec3 c) { return dot(c, vec3(0.3, 0.55, 0.15)); }
vec3  glaze(vec3 c, vec3 g, float k) { return c * mix(vec3(1.0), g, k); }

float paperGrain(vec2 q) {
    float fib = vn(q * vec2(420.0, 140.0)) * 0.5 + vn(q * vec2(150.0, 520.0)) * 0.5;
    return 0.955 + 0.045 * fib;
}

// How thin the Body is around uv: 1 for limbs and head, 0 for the torso.
// Coverage of two rings of Body samples; a thin part leaves most of each ring empty.
// Measured on the same eased, softened Body (.r) that drives the flow, so a broad part's
// lagging trailing edge still reads as broad.
float extremity(sampler2D body, vec2 uv, float A) {
    float s = 0.0;
    for (int i = 0; i < 12; i++) {
        float a = float(i) * 0.5235988;
        vec2 d = vec2(cos(a), sin(a)) / vec2(A, 1.0);
        s += texture(body, uv + d * RING_R1).r + texture(body, uv + d * RING_R2).r;
    }
    float t = mix(0.18, 0.45, THIN);
    return 1.0 - smoothstep(t - 0.08, t + 0.08, s / 24.0);
}

// Cover-fit: uv 0–1 on screen → image uv, aspect kept, overflow cropped, centred.
vec2 coverUV(vec2 uv, vec2 screen, vec2 img) {
    float sa = screen.x / screen.y, ia = img.x / img.y;
    if (sa > ia) uv.y = (uv.y - 0.5) * ia / sa + 0.5;
    else         uv.x = (uv.x - 0.5) * sa / ia + 0.5;
    return uv;
}

// ── Procedural stand-in painting: a watercolor sunset ────────────────────────
// Distance into the painted area from its ragged edge, in screen heights.
float paperEdge(vec2 uv, vec2 res) {
    float A = res.x / res.y; vec2 q = uv * vec2(A, 1.0);
    vec2 e = min(uv, 1.0 - uv) * vec2(A, 1.0);
    return min(e.x, e.y) + 0.03 * (fbm(q * 7.0) - 0.5);
}

// 1 where paint may smear, 0 on the unpainted border.
float paintMask(vec2 uv, vec2 res) { return smoothstep(0.06, 0.09, paperEdge(uv, res)); }

vec3 sunsetSky(float t) {
    vec3 c0 = vec3(1.0, 0.87, 0.55), c1 = vec3(0.99, 0.63, 0.36), c2 = vec3(0.93, 0.42, 0.48),
         c3 = vec3(0.60, 0.38, 0.62), c4 = vec3(0.27, 0.31, 0.55);
    vec3 c = mix(c0, c1, smoothstep(0.0, 0.2, t));
    c = mix(c, c2, smoothstep(0.15, 0.42, t));
    c = mix(c, c3, smoothstep(0.38, 0.7, t));
    return mix(c, c4, smoothstep(0.65, 1.0, t));
}

vec3 paintSunset(vec2 uv, vec2 res) {
    float A = res.x / res.y; vec2 q = uv * vec2(A, 1.0);
    float warp = fbm(q * vec2(1.5, 4.0) + 3.0) - 0.5;
    float h = 0.36 + 0.012 * (fbm(vec2(q.x * 3.0, 1.0)) - 0.5);       // horizon
    vec2 sc = vec2(A * 0.58, h + 0.12);                                 // sun centre
    vec3 col;
    if (uv.y > h) {
        float t = (uv.y - h) / (1.0 - h) + 0.08 * warp;
        col = sunsetSky(clamp(t, 0.0, 1.0));
        float fb = fract(t * 4.5 + 0.3 * warp);
        col *= 1.0 - 0.08 * smoothstep(0.8, 1.0, fb);                   // pooled lower edge of each wash
        float cl = fbm(vec2(q.x * 1.1, uv.y * 8.0) + vec2(warp * 2.5, 0.0));
        float cm = smoothstep(0.54, 0.68, cl) * smoothstep(h + 0.1, h + 0.22, uv.y) * smoothstep(0.97, 0.62, uv.y);
        col = glaze(col, mix(vec3(0.86, 0.55, 0.72), vec3(0.62, 0.52, 0.80), clamp(t, 0.0, 1.0)), cm * 0.75);
        col *= 1.0 - 0.10 * cm * smoothstep(0.62, 0.68, cl) * (1.0 - smoothstep(0.68, 0.74, cl));
        float d = length(q - sc) + 0.014 * (fbm(q * 11.0) - 0.5);
        col = mix(col, vec3(1.0, 0.84, 0.55), smoothstep(0.34, 0.0, d) * 0.35);    // glow
        col = mix(col, vec3(1.0, 0.95, 0.74), smoothstep(0.088, 0.078, d) * 0.92);  // lifted sun
        col *= 1.0 - 0.13 * smoothstep(0.012, 0.0, abs(d - 0.083));                // pooled rim
        float hill = h + 0.012 + 0.075 * (fbm(vec2(q.x * 1.6, 7.0)) - 0.25) * smoothstep(A * 0.9, A * 0.15, q.x)
                   + 0.006 * (vn(q * 40.0) - 0.5);
        float hm = smoothstep(0.004, -0.004, uv.y - hill);
        col = mix(col, glaze(col, vec3(0.52, 0.36, 0.55), 0.85) * (1.0 - 0.12 * smoothstep(0.014, 0.0, hill - uv.y)), hm);
    } else {
        float s = (h - uv.y) / h;
        float st = fbm(vec2(q.x * 2.2, uv.y * 38.0));
        vec3 w = mix(vec3(0.86, 0.52, 0.52), vec3(0.29, 0.27, 0.50), smoothstep(-0.05, 1.0, s + 0.12 * warp));
        float refl = smoothstep(0.07 + 0.16 * s, 0.0, abs(q.x - sc.x) + 0.09 * (st - 0.5)) * smoothstep(0.42, 0.58, st);
        w = mix(w, vec3(1.0, 0.83, 0.55), refl * 0.85);
        w *= 1.0 - 0.09 * smoothstep(0.58, 0.72, st) * (1.0 - refl);
        col = w;
    }
    float gran = vn(q * 170.0) * vn(q * 63.0 + 5.0);
    col *= 1.0 - 0.14 * gran * (1.0 - lum(col));                        // granulation in darker washes
    float ed = paperEdge(uv, res);
    col = mix(PAPER, col, smoothstep(0.025, 0.05, ed));                 // ragged unpainted border
    col *= 1.0 - 0.06 * smoothstep(0.04, 0.05, ed) * (1.0 - smoothstep(0.05, 0.065, ed));  // dried rim
    return col;
}
