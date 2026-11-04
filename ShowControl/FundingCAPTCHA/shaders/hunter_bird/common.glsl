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
