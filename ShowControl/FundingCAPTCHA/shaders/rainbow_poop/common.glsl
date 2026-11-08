// Common — every tunable for rainbow poop lives here (edit, save, press R).
// Lengths are in screen heights ("sh") unless noted. Spec: docs/superpowers/specs/2026-11-08-rainbow-poop-design.md
//
// State (Buffer B) layout, texel (x, y); k = person slot 0–7:
//   (k, 0) SLOT    id, seconds until this person's next poop, presence 0–1 (fades splats on loss), 0
//   (k, 1) ANCHOR  the person's silhouette: centre of mass x, y (Body UV) and size (sh, ≈ their height;
//                  see SIZE_K), measured from this frame's Body, low-passed over ANCHOR_EMA_S; 0
//   (k, 2) POOP    the poop dropped on this person: sway centre x, y (UV), sway phase, aim offset (sizes)
//   (k, 3) DROP    falling 0/1, floor y (UV), target id, seconds falling
//   (k·SPLATS + j, 4) SPLAT   centre in the person's frame x, y (sizes from their centre of mass),
//                             age s, seed 0–1 — j = 0 newest
//   (j, 5) GROUND  x, y (UV), age s, seed 0–1 — j = 0 newest

const int   SLOTS = 8, SPLATS = 8, GROUNDS = 8;
const float T_CLAMP = 99.0;              // every "seconds since" counter clamps here
const float DT_MAX  = 0.25;              // a render hiccup longer than this is treated as this
// Ages and countdowns are kept in multiples of this, which a half float holds exactly up to 64 s;
// each frame's step is rounded to it with a golden-ratio offset, so the running error stays
// within about one step at any fps. (Plain f16 adds of 1/30 above 8 s drift by ~6%.)
const float AGE_Q   = 1.0 / 32.0;

// ── Cadence (per person) ──────────────────────────────────────────────────────
const float FIRST_BOMB_S  = 1.2;         // s after a person is confirmed before their first poop drops …
const float FIRST_JITTER  = 0.8;         // … plus up to this
const float BOMB_EVERY_S  = 5.0;         // then one every this many seconds …
const float BOMB_JITTER_S = 1.0;         // … ± this, counted from the drop

// ── The fall ──────────────────────────────────────────────────────────────────
// A poop appears just above the top of the screen, over where its person will be when it
// reaches their head, and drifts down at a steady, visible speed with a gentle sway.
const float SPAWN_Y     = 1.04;          // UV y the poop starts at (just off the top)
const float FALL_SPEED  = 0.2;           // sh/s
const float SWAY        = 0.02;          // sh, sideways sway amplitude
const float SWAY_W      = 3.0;           // rad/s
const float LEAD_MAX    = 0.5;           // sh: drop ahead of a moving person by at most this
const float AIM_SPREAD  = 0.05;          // aim within ± this × their size of their centre of mass
// While it falls, the poop drifts toward its person's centre of mass: quick enough to find someone
// standing or swaying, too slow to catch someone who walks or turns away (a walk is ~0.3 sh/s).
const float HOMING_GAIN = 3.0;           // 1/s: sideways speed per sh off target …
const float HOMING_MAX  = 0.18;          // … up to this, sh/s
const int   FALL_STEPS  = 2;             // body hit tests per frame along the fall
const float POOP_R      = 0.022;         // falling drop radius

// ── Splats ────────────────────────────────────────────────────────────────────
const float SPLAT_LIFE_S  = 20.0;
const float SPLAT_FADE_S  = 3.0;         // the last part of the life
const float LEAVE_FADE_S  = 0.6;         // splats fade this fast when their person's track is lost
// Splats ride on the silhouette's centre of mass, scaled by its size: SIZE_K × √(area), about an
// upright adult's height. Both are measured from the Body each frame inside the tracker's box, so
// raised arms, strides and box jitter barely move them, and they don't lag the silhouette.
const float SIZE_K        = 2.1;
const int   ANCHOR_NX = 16, ANCHOR_NY = 24;   // Body samples across and up the box
const float ANCHOR_MARGIN = 0.03;        // UV: the box is widened by this (records ease behind the Body)
const float ANCHOR_EMA_S  = 0.04;        // just enough to soften sampling noise
const float SPLAT_R       = 0.15;        // × size
const float SPLAT_R_MIN   = 0.04;        // sh
const float SPLAT_SINK    = 0.06;        // × size: the splat centre sits this far below the impact …
const float SINK_SPREAD   = 0.12;        // … plus up to this, so splats spread down over head and shoulders
const float SPLAT_LUMP    = 0.22;        // edge lumpiness, × radius
const float POP_S         = 0.18;        // splat-in time
const float DRIP_LEN      = 2.6;         // longest drip, × splat radius
const float DRIP_S        = 4.0;         // drips reach full length after this
const float GROUND_R      = 0.10;        // sh, puddle radius before squashing
const float GROUND_LIFE_S = 8.0;
const float GROUND_FADE_S = 2.0;
const float GROUND_SQUASH = 2.6;         // puddles are this many times wider than tall

// ── Look ──────────────────────────────────────────────────────────────────────
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
vec4 sPoop  (sampler2D s, int k) { return texelFetch(s, ivec2(k, 2), 0); }
vec4 sDrop  (sampler2D s, int k) { return texelFetch(s, ivec2(k, 3), 0); }
vec4 sSplat (sampler2D s, int k, int j) { return texelFetch(s, ivec2(k * SPLATS + j, 4), 0); }
vec4 sGround(sampler2D s, int j) { return texelFetch(s, ivec2(j, 5), 0); }

// UV ↔ screen heights. Macros: Shadertoy's Common tab can't see iResolution.
#define toScreen(uv) ((uv) * iResolution.xy / iResolution.y)
#define toUv(sh)     ((sh) * iResolution.y / iResolution.xy)

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
// Coverage of the inside of a signed distance `d`.
float fill(float d, float px) { return 1.0 - smoothstep(-0.5 * px, 0.5 * px, d); }
float smin(float a, float b, float k) {
    float h = clamp(0.5 + 0.5 * (b - a) / k, 0.0, 1.0);
    return mix(b, a, h) - k * h * (1.0 - h);
}
