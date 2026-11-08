// Common — every tunable for rainbow poop lives here (edit, save, press R).
// Lengths are in screen heights ("sh") unless noted. Spec: docs/superpowers/specs/2026-11-08-rainbow-poop-design.md
//
// State (Buffer B) layout, texel (x, y); k = person slot 0–7, i = bird 0–3:
//   (k, 0) SLOT    id, seconds until this person's next bomb, presence 0–1 (fades splats on loss), 0
//   (k, 1) ANCHOR  box top-centre x, y (Body UV) and box height (sh), low-passed over ANCHOR_EMA_S; 0
//   (i, 2) BIRD    position x, y (UV), velocity x, y (sh/s)
//   (i, 3) PLAN    mode (0 orbit, 1 dive, 2 climb), seconds in mode, ±(target slot + 1) (sign = flight
//                  direction), target id
//   (i, 4) PATH    dive start x, y (UV), release point x, y (UV; frozen once released)
//   (i, 5) POOP    position x, y (UV), velocity x, y (sh/s)
//   (i, 6) DROP    target slot + 1 (0 = nothing falling), floor y (UV), 0, seconds falling
//   (k·SPLATS + j, 7) SPLAT   centre in the person's frame x, y (box heights from the box top-centre),
//                             age s, seed 0–1 — j = 0 newest
//   (j, 8) GROUND  x, y (UV), age s, seed 0–1 — j = 0 newest

const int   SLOTS = 8, BIRDS = 4, SPLATS = 8, GROUNDS = 8;
const float T_CLAMP = 99.0;              // every "seconds since" counter clamps here
const float DT_MAX  = 0.25;              // a render hiccup longer than this is treated as this
// Ages and countdowns are kept in multiples of this, which a half float holds exactly up to 64 s;
// each frame's step is rounded to it stochastically, so the expected rate is exact at any fps.
// (Plain f16 adds of 1/30 above 8 s drift by ~6%.)
const float AGE_Q   = 1.0 / 32.0;

// ── Bombing cadence (per person) ──────────────────────────────────────────────
const float FIRST_BOMB_S  = 1.2;         // s after a person appears before a bird is sent …
const float FIRST_JITTER  = 0.8;         // … plus up to this
const float BOMB_EVERY_S  = 5.0;         // then one bird every this many seconds …
const float BOMB_JITTER_S = 1.0;         // … ± this

// ── Flock (idle orbits) ───────────────────────────────────────────────────────
const float ORBIT_Y     = 0.80;          // orbit centres' height
const float ORBIT_R     = 0.09;          // orbit radius
const float ORBIT_W     = 0.8;           // rad/s
const float ORBIT_DRIFT = 0.04;          // how fast orbit centres wander across the sky (noise rate)
const float CRUISE      = 0.55;          // top speed toward the orbit point, sh/s
const float ORBIT_GAIN  = 2.0;           // 1/s: speed toward the orbit point per sh of distance
const float STEER_K     = 3.0;           // 1/s: how fast velocity turns to the desired one

// ── Dive (a fixed-time swoop to the release point, then a climb away) ─────────
const float DIVE_S      = 1.4;
const float CLIMB_S     = 1.4;
const float APPROACH    = 0.35;          // sh: arrives flying level from this far to the side
const float DROP_ABOVE  = 0.20;          // sh above the target's head to release
const float SKY_MAX     = 0.94;          // the release point is never higher than this
const float CLIMB_TO_Y  = 0.84;
const float LEAD_MAX    = 0.5;           // sh: the bird leads a moving target by at most this
const float AIM_SPREAD  = 0.5;           // aim within ± this × half the box width of its centre

// ── Poop ──────────────────────────────────────────────────────────────────────
const float GRAVITY     = 1.6;           // sh/s²
const int   FALL_STEPS  = 3;             // body hit tests per frame along the fall
const float POOP_R      = 0.012;         // in-flight drop radius

// ── Splats ────────────────────────────────────────────────────────────────────
const float SPLAT_LIFE_S  = 20.0;
const float SPLAT_FADE_S  = 3.0;         // the last part of the life
const float LEAVE_FADE_S  = 0.6;         // splats fade this fast when their person's track is lost
const float ANCHOR_EMA_S  = 0.15;
const float SPLAT_R       = 0.075;       // × box height
const float SPLAT_R_MIN   = 0.02;        // sh
const float SPLAT_SINK    = 0.04;        // × box height: the splat centre sits this far below the impact …
const float SINK_SPREAD   = 0.10;        // … plus up to this, so splats spread down over head and shoulders
const float SPLAT_LUMP    = 0.22;        // edge lumpiness, × radius
const float POP_S         = 0.18;        // splat-in time
const float DRIP_LEN      = 2.6;         // longest drip, × splat radius
const float DRIP_S        = 4.0;         // drips reach full length after this
const float GROUND_LIFE_S = 8.0;
const float GROUND_FADE_S = 2.0;
const float GROUND_SQUASH = 2.6;         // puddles are this many times wider than tall

// ── Look ──────────────────────────────────────────────────────────────────────
const float BIRD_S   = 0.045;            // bird body half-length
const float FLAP_HZ  = 2.2, FLAP_CLIMB_HZ = 4.0;
const float CLOUD_Y  = 0.86;
const float INK_W = 2.2 / 360.0, INK_W_HEAVY = 2.6 / 360.0, INK_W_LIGHT = 1.6 / 360.0;

// ── Palette ───────────────────────────────────────────────────────────────────
const vec3 PAPER      = vec3(0.965, 0.945, 0.894);   // #f6f1e4
const vec3 INK        = vec3(0.067);                 // #111111
const vec3 WARM_WHITE = vec3(1.000, 0.980, 0.941);   // #fffaf0
const vec3 SLATE      = vec3(0.443, 0.604, 0.678);   // #719aad
const vec3 DEEP       = vec3(0.125, 0.463, 0.639);   // #2076a3
const vec3 VIOLET     = vec3(0.420, 0.357, 0.584);   // #6b5b95
const vec3 RUST       = vec3(0.737, 0.298, 0.149);   // #bc4c26
const vec3 ORANGE     = vec3(0.910, 0.525, 0.184);   // #e8862f
const vec3 YELLOW     = vec3(1.000, 0.949, 0.000);   // #fff200
// The rainbow, outside in: red, orange, yellow, green, blue, violet.
const vec3 RAINBOW[6] = vec3[6](vec3(0.878, 0.271, 0.227), ORANGE, YELLOW,
                                vec3(0.384, 0.698, 0.341), DEEP, VIOLET);
vec3 rainbow(int i) { return RAINBOW[((i % 6) + 6) % 6]; }

// ── Blob records (ADR-0022) ───────────────────────────────────────────────────
const float S_EMPTY = 0., S_TENTATIVE = 1., S_CONFIRMED = 2., S_COASTING = 3., S_LOST = 4.;

vec4 recBox(sampler2D b, int k) { return texelFetch(b, ivec2(k, 0), 0); }   // x0, y0, x1, y1  Body UV
vec4 recMot(sampler2D b, int k) { return texelFetch(b, ivec2(k, 1), 0); }   // cx, cy, vx, vy  UV, UV/s
vec4 recIdn(sampler2D b, int k) { return texelFetch(b, ivec2(k, 2), 0); }   // id, state, age_s, near
bool isState(float s, float want) { return abs(s - want) < 0.5; }
bool isHere(float s) { return isState(s, S_TENTATIVE) || isState(s, S_CONFIRMED) || isState(s, S_COASTING); }

// ── State accessors ───────────────────────────────────────────────────────────
vec4 sSlot  (sampler2D s, int k) { return texelFetch(s, ivec2(k, 0), 0); }
vec4 sAnchor(sampler2D s, int k) { return texelFetch(s, ivec2(k, 1), 0); }
vec4 sBird  (sampler2D s, int i) { return texelFetch(s, ivec2(i, 2), 0); }
vec4 sPlan  (sampler2D s, int i) { return texelFetch(s, ivec2(i, 3), 0); }
vec4 sPath  (sampler2D s, int i) { return texelFetch(s, ivec2(i, 4), 0); }
vec4 sPoop  (sampler2D s, int i) { return texelFetch(s, ivec2(i, 5), 0); }
vec4 sDrop  (sampler2D s, int i) { return texelFetch(s, ivec2(i, 6), 0); }
vec4 sSplat (sampler2D s, int k, int j) { return texelFetch(s, ivec2(k * SPLATS + j, 7), 0); }
vec4 sGround(sampler2D s, int j) { return texelFetch(s, ivec2(j, 8), 0); }

// UV ↔ screen heights. Macros: Shadertoy's Common tab can't see iResolution.
#define toScreen(uv) ((uv) * iResolution.xy / iResolution.y)
#define toUv(sh)     ((sh) * iResolution.y / iResolution.xy)

// ── Noise ─────────────────────────────────────────────────────────────────────
float hash11(float n) { return fract(sin(n * 127.1 + 311.7) * 43758.5453); }
float vnoise(float x) {                  // value noise, −1…1
    float i = floor(x), f = fract(x);
    return mix(hash11(i), hash11(i + 1.0), f * f * (3.0 - 2.0 * f)) * 2.0 - 1.0;
}

// ── Paths ─────────────────────────────────────────────────────────────────────
vec2 bezier(vec2 a, vec2 b, vec2 c, float u)  { return mix(mix(a, b, u), mix(b, c, u), u); }
vec2 bezierD(vec2 a, vec2 b, vec2 c, float u) { return 2.0 * mix(b - a, c - b, u); }   // d/du

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
// Coverage of the inside of a signed distance `d`.
float fill(float d, float px) { return 1.0 - smoothstep(-0.5 * px, 0.5 * px, d); }
vec2 rot(vec2 p, float a) { float c = cos(a), s = sin(a); return vec2(c * p.x + s * p.y, -s * p.x + c * p.y); }
float smin(float a, float b, float k) {
    float h = clamp(0.5 + 0.5 * (b - a) / k, 0.0, 1.0);
    return mix(b, a, h) - k * h * (1.0 - h);
}
// A leaf/wing: a lens from two quadratics (0,0)→(L/2, ±0.42L)→(L,0). Signed distance.
float sdLeaf(vec2 q, float L) {
    float t = q.x / L;
    if (t <= 0.0) return length(q);
    if (t >= 1.0) return length(q - vec2(L, 0.0));
    float half_ = 0.84 * L * t * (1.0 - t), slope = 0.84 * (1.0 - 2.0 * t);
    return (abs(q.y) - half_) / sqrt(1.0 + slope * slope);
}
float sdTriangle(vec2 p, vec2 a, vec2 b, vec2 c) {
    vec2 e0 = b - a, e1 = c - b, e2 = a - c, v0 = p - a, v1 = p - b, v2 = p - c;
    vec2 pq0 = v0 - e0 * clamp(dot(v0, e0) / dot(e0, e0), 0.0, 1.0);
    vec2 pq1 = v1 - e1 * clamp(dot(v1, e1) / dot(e1, e1), 0.0, 1.0);
    vec2 pq2 = v2 - e2 * clamp(dot(v2, e2) / dot(e2, e2), 0.0, 1.0);
    float s = sign(e0.x * e2.y - e0.y * e2.x);
    vec2 d = min(min(vec2(dot(pq0, pq0), s * (v0.x * e0.y - v0.y * e0.x)),
                     vec2(dot(pq1, pq1), s * (v1.x * e1.y - v1.y * e1.x))),
                     vec2(dot(pq2, pq2), s * (v2.x * e2.y - v2.y * e2.x)));
    return -sqrt(d.x) * sign(d.y);
}
