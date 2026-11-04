// Common — every tunable for the hunter bird lives here (edit, save, press R).
// Lengths are in screen heights unless noted; mockup px / 360 = screen heights.
// Spec: docs/superpowers/specs/2026-11-04-hunter-bird-design.md
//
// Bird state (Buffer B) layout, texel (x, y), k = slot 0–7:
//   (k, 0) SLOT     id, motion 0–1, interest 0–1, stamped 0/1
//   (k, 1) PREV     this slot's box last frame (Body UV)
//   (k, 2) HEAD     last print x, y, side 0/1, seconds since last print
//   (0, 3) ATTN     target slot + 1 (0 none), lock 0–1, seconds since strike, id struck last
//   (1, 3) RETICLE  x, y (screen UV), radius (screen heights), alpha
//   (2, 3) MOOD     lid openness, shiver 0–1, wander anchor x, y
//   (3, 3) BLINK    seconds since blink start (negative = scheduled), idle countdown s,
//                   seconds everyone present has been stamped
//   (4, 3) STAMP    x, y (screen UV)
//   (k·PRINTS + j, 4) PRINT  x, y (Body UV), age s, angle — j = 0 newest

const int   SLOTS = 8, PRINTS = 12;
const float T_CLAMP = 99.0;              // every "seconds since" counter clamps here
const float DT_MAX  = 0.25;              // a render hiccup longer than this is treated as this
// motion (per confirmed slot)
const float SPEED_FULL    = 0.39;        // screen heights/s of speed that alone reads as motion 1
const float SIZE_FULL     = 0.61;        // screen heights/s of (w + h) change that alone reads as motion 1
const float MOTION_FLOOR  = 0.15;        // subtracted: eased-box breathing and flicker live below this
const float MOTION_RISE_S = 0.15, MOTION_FALL_S = 0.3;
// interest, target, lock
const float MOTION_ON      = 0.2;        // above: interest rises; below: drains
const float INTEREST_GAIN  = 0.9;        // per second, × motion
const float INTEREST_DRAIN = 0.45;       // per second
const float TARGET_MIN     = 0.25, TARGET_SWITCH = 0.2, SWITCH_KEEP = 0.3;
const float LOCK_RATE      = 0.45;       // per second, × motion²
const float LOCK_DRAIN     = 0.3;
const float STRIKE_ACK_S   = 0.2;        // window in which a SLOT accepts the strike for its id
// reticle
const float RET_R_LOOSE = 58.0/360.0, RET_R_LOCKED = 20.0/360.0, RET_R_WANDER = 66.0/360.0;
const float RET_K_MIN = 3.0, RET_K_GAIN = 6.0, RET_K_WANDER = 1.2;   // spring rates, 1/s
const float RET_K_RADIUS = 5.0, RET_K_ALPHA = 3.0;                    // 1/s
const float WANDER_X = 90.0/360.0, WANDER_Y = 40.0/360.0, WANDER_RATE = 0.6;
// mood (lid openness 0–1) and blinks
const float LID_DROWSY = 0.42, LID_DROOP = 0.05, LID_SQUINT = 0.7, LID_WIDE = 0.96, LID_STRIKE = 1.0, LID_SMUG = 0.58;
const float LID_OPEN_RATE = 9.0, LID_CLOSE_RATE = 3.0;
const float STRIKE_WIDE_S = 0.9, STRIKE_SMUG_S = 3.2, ALL_STAMPED_DROWSY_S = 6.0;
const float SHIVER_DECAY = 1.5;          // per second
const float BLINK_S = 0.32, BLINK_NEW_DELAY = 0.15, BLINK_STRIKE_DELAY = 2.3, IDLE_BLINK_MIN = 6.0, IDLE_BLINK_SPAN = 4.0;
// strike sequence
const float PUNCH_ZOOM = 0.38, PUNCH_RISE_S = 0.12, PUNCH_HOLD_S = 0.9, PUNCH_END_S = 1.7;
const float STAMP_SLAM_S = 0.12, STAMP_FADE_START_S = 2.6, STAMP_END_S = 3.2;
// footprints
const float PRINT_EVERY_S = 0.33, PRINT_MIN_SPEED = 25.0/360.0, PRINT_LIFE_S = 4.0;
// eye
const float IRIS_R_OPEN = 345.0/360.0, IRIS_R_LOCKED = 250.0/360.0, IRIS_R_STRIKE = 380.0/360.0, IRIS_BAND = 34.0/360.0;
// line weights
const float INK_W = 2.2/360.0, INK_W_HEAVY = 2.6/360.0, INK_W_LIGHT = 1.6/360.0;

// ── Palette ───────────────────────────────────────────────────────────────────
const vec3 PAPER      = vec3(0.965, 0.945, 0.894);   // #f6f1e4
const vec3 INK        = vec3(0.067);                 // #111111
const vec3 SLATE      = vec3(0.443, 0.604, 0.678);   // #719aad
const vec3 DEEP       = vec3(0.125, 0.463, 0.639);   // #2076a3
const vec3 RUST       = vec3(0.737, 0.298, 0.149);   // #bc4c26
const vec3 YELLOW     = vec3(1.000, 0.949, 0.000);   // #fff200
const vec3 ORANGE     = vec3(0.910, 0.525, 0.184);   // #e8862f
const vec3 VIOLET     = vec3(0.420, 0.357, 0.584);   // #6b5b95
const vec3 WARM_WHITE = vec3(1.000, 0.980, 0.941);   // #fffaf0

// ── Blob records (ADR-0022) ───────────────────────────────────────────────────
const float S_EMPTY = 0., S_TENTATIVE = 1., S_CONFIRMED = 2., S_COASTING = 3., S_LOST = 4.;

vec4 recBox(sampler2D b, int k) { return texelFetch(b, ivec2(k, 0), 0); }   // x0, y0, x1, y1  Body UV
vec4 recMot(sampler2D b, int k) { return texelFetch(b, ivec2(k, 1), 0); }   // cx, cy, vx, vy  UV, UV/s
vec4 recIdn(sampler2D b, int k) { return texelFetch(b, ivec2(k, 2), 0); }   // id, state, age_s, near
bool isState(float s, float want) { return abs(s - want) < 0.5; }

// ── Bird state accessors ──────────────────────────────────────────────────────
vec4 bSlot   (sampler2D s, int k) { return texelFetch(s, ivec2(k, 0), 0); }
vec4 bPrev   (sampler2D s, int k) { return texelFetch(s, ivec2(k, 1), 0); }
vec4 bHead   (sampler2D s, int k) { return texelFetch(s, ivec2(k, 2), 0); }
vec4 bAttn   (sampler2D s)        { return texelFetch(s, ivec2(0, 3), 0); }
vec4 bReticle(sampler2D s)        { return texelFetch(s, ivec2(1, 3), 0); }
vec4 bMood   (sampler2D s)        { return texelFetch(s, ivec2(2, 3), 0); }
vec4 bBlink  (sampler2D s)        { return texelFetch(s, ivec2(3, 3), 0); }
vec4 bStamp  (sampler2D s)        { return texelFetch(s, ivec2(4, 3), 0); }
vec4 bPrint  (sampler2D s, int k, int j) { return texelFetch(s, ivec2(k * PRINTS + j, 4), 0); }

// UV → screen-height units. A macro: Shadertoy's Common tab can't see iResolution.
#define toScreen(uv) ((uv) * iResolution.xy / iResolution.y)

// ── Noise ─────────────────────────────────────────────────────────────────────
float hash11(float n) { return fract(sin(n * 127.1 + 311.7) * 43758.5453); }
float vnoise(float x) {                  // value noise, −1…1
    float i = floor(x), f = fract(x);
    return mix(hash11(i), hash11(i + 1.0), f * f * (3.0 - 2.0 * f)) * 2.0 - 1.0;
}

// ── Drawing helpers (lengths in screen heights) ───────────────────────────────
float sdSegment(vec2 p, vec2 a, vec2 b) {
    vec2 pa = p - a, ba = b - a;
    return length(pa - ba * clamp(dot(pa, ba) / max(dot(ba, ba), 1e-9), 0.0, 1.0));
}
// Coverage of a pen stroke `w` wide at distance `d`, antialiased over one pixel `px`.
float pen(float d, float w, float px) {
    w = max(w, px);
    return 1.0 - smoothstep(0.5 * (w - px), 0.5 * (w + px), d);
}
vec2 rot(vec2 p, float a) { float c = cos(a), s = sin(a); return vec2(c * p.x + s * p.y, -s * p.x + c * p.y); }
vec2 bezier(vec2 a, vec2 b, vec2 c, float u) { return mix(mix(a, b, u), mix(b, c, u), u); }
// Distance to a quadratic Bézier, via 12 chords (good to well under a pixel here).
float sdBezier(vec2 p, vec2 a, vec2 b, vec2 c) {
    float d = 1e9; vec2 q = a;
    for (int i = 1; i <= 12; i++) {
        vec2 r = bezier(a, b, c, float(i) / 12.0);
        d = min(d, sdSegment(p, q, r)); q = r;
    }
    return d;
}
// Diagonal hatch lines `gap` apart, `w` wide; 1 on a line.
float hatch(vec2 p, float gap, float w, float px) {
    float d = (p.x - p.y) * 0.70710678;               // "/" lines, as the mockup
    return pen(abs(fract(d / gap) - 0.5) * gap, w, px);
}
// A leaf: a lens from two quadratics (0,0)→(L/2, ±0.42L)→(L,0), in leaf space. Signed distance.
float sdLeaf(vec2 q, float L) {
    float t = q.x / L;
    if (t <= 0.0) return length(q);
    if (t >= 1.0) return length(q - vec2(L, 0.0));
    float half_ = 0.84 * L * t * (1.0 - t), slope = 0.84 * (1.0 - 2.0 * t);
    return (abs(q.y) - half_) / sqrt(1.0 + slope * slope);
}

// ── Canopy layout (mockup px / 360, y up) ─────────────────────────────────────
// Branches: quadratic Bézier start, control, end, and width. A negative x is
// measured from the right edge, so the right branch hugs it at any aspect.
const vec2  BR_L0 = vec2(-20.0, 338.0) / 360.0, BR_L1 = vec2(120.0, 330.0) / 360.0, BR_L2 = vec2(270.0, 354.0) / 360.0;
const vec2  BR_R0 = vec2( 20.0, 326.0) / 360.0, BR_R1 = vec2(-100.0, 330.0) / 360.0, BR_R2 = vec2(-220.0, 356.0) / 360.0;
const vec2  PERCH0 = vec2(-30.0, -18.0) / 360.0, PERCH1 = vec2(130.0, 30.0) / 360.0, PERCH2 = vec2(310.0, 8.0) / 360.0;
const float BR_W_L = 8.0 / 360.0, BR_W_R = 7.0 / 360.0, PERCH_W = 17.0 / 360.0, BR_RIM = 5.0 / 360.0;
const float CANOPY_BAND = 1.0 - 80.0 / 360.0;       // leaves and branches above this y …
const float CORNER_W = 70.0 / 360.0, CORNER_Y = 1.0 - 180.0 / 360.0;   // … in the corner columns above this …
const vec2  PERCH_BOX = vec2(340.0, 66.0) / 360.0;   // … and in the perch box at the bottom left
const float LEAF_SWAY = 0.07, LEAF_SHIVER = 0.16;

const int LEAVES = 29;
// x, y (screen heights; x is from the right edge when LEAF_K.z = 1), angle, length.
// Generated from the mockup's layout with its hash, side leaves thinned to three per side.
const vec4 LEAF[LEAVES] = vec4[LEAVES](
    vec4(0.0233, 1.0129, -1.3093, 0.0980), vec4(0.0836, 0.9815, -2.2006, 0.0903),
    vec4(0.2222, 1.0012, -2.1594, 0.0864), vec4(0.3128, 0.9821, -2.3154, 0.0691),
    vec4(0.4210, 0.9880, -0.8551, 0.0975), vec4(0.5090, 0.9696, -0.8890, 0.0658),
    vec4(0.6323, 0.9761, -1.9491, 0.0934), vec4(0.7288, 0.9895, -2.2288, 0.0679),
    vec4(0.8235, 1.0063, -1.8559, 0.0637), vec4(0.9305, 0.9787, -0.8539, 0.0979),
    vec4(1.0194, 1.0180, -1.9458, 0.0689), vec4(1.1139, 0.9887, -1.5588, 0.0894),
    vec4(1.1892, 1.0210, -1.2196, 0.0653), vec4(1.3298, 0.9991, -1.9469, 0.0764),
    vec4(1.3845, 0.9527, -2.2598, 0.0942), vec4(1.5239, 1.0080, -1.7574, 0.0700),
    vec4(1.5874, 1.0171, -1.1023, 0.0818), vec4(1.6815, 0.9902, -2.0489, 0.0838),
    vec4(1.8303, 0.9914, -1.6160, 0.0802),
    vec4(0.0097, 0.8889, -0.4041, 0.0824), vec4(0.0147, 0.7944, 0.3367, 0.0852),
    vec4(0.0221, 0.7000, 0.5565, 0.0768),
    vec4(-0.0211, 0.9167, -2.5672, 0.0884), vec4(-0.0313, 0.8222, -3.1907, 0.0608),
    vec4(-0.0123, 0.7278, -3.3886, 0.0561),
    vec4(0.0690, 0.0614, 1.5462, 0.0606), vec4(0.1828, 0.0362, 1.0376, 0.0501),
    vec4(0.3173, 0.0674, 1.0927, 0.0652), vec4(0.4428, 0.0626, 2.1848, 0.0709));
// fill (0 paper, 1 slate, 2 deep, 3 violet), hatched, anchored to the right edge
const vec3 LEAF_K[LEAVES] = vec3[LEAVES](
    vec3(2, 0, 0), vec3(3, 0, 0), vec3(0, 0, 0), vec3(1, 1, 0), vec3(2, 0, 0), vec3(0, 0, 0),
    vec3(2, 1, 0), vec3(0, 0, 0), vec3(0, 0, 0), vec3(1, 0, 0), vec3(0, 1, 0), vec3(0, 0, 0),
    vec3(1, 0, 0), vec3(1, 0, 0), vec3(0, 0, 0), vec3(1, 1, 0), vec3(0, 1, 0), vec3(0, 1, 0),
    vec3(0, 0, 0), vec3(0, 1, 0), vec3(0, 1, 0), vec3(0, 0, 0),
    vec3(3, 0, 1), vec3(1, 0, 1), vec3(0, 1, 1),
    vec3(2, 0, 0), vec3(0, 0, 0), vec3(0, 0, 0), vec3(0, 0, 0));
vec3 leafFill(float k) { return k < 0.5 ? PAPER : k < 1.5 ? SLATE : k < 2.5 ? DEEP : VIOLET; }
