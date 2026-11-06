// Common — every tunable for the watering can lives here (edit, save, press R).
// Lengths are in screen heights unless noted; mockup px / 360 = screen heights.
// Spec: docs/superpowers/specs/2026-11-06-watering-can-design.md
//
// Body memory (Buffer B, per pixel):
//   .r presence 0–1 (soft, hole-filled, eased)   .g run bottom y (UV)   .b run top y (UV)
//   .a owner + 0.9 * hold   (owner = slot + 1, 0 none; hold 0–1, 1 while the body is present)
// Garden state (Buffer C), texel (x, y), k = slot 0–7:
//   (k, 0) PERSON  id (0 none), growth 0–1, planted spot x, y (UV)
//   (k, 1) BASE    base x, base y (UV, smoothed), seconds since last walking step, record state last frame
//   (k, 2) GHOST   spot x, y, growth at loss, seconds since loss (T_CLAMP = no ghost)
//   (0, 3) SUN     sun level 0–1 (eased), raw total growth, —, —
//   (i, 4 + j) NEAR  1 if body (or a held shape) lies within NEAR_PAD of grid cell (i, j), else 0;
//                    cell (i, j) is screen [i, i + 1] × [j, j + 1] · NEAR_CELL (screen heights). See cNear().

const int   SLOTS = 8;
const float T_CLAMP = 99.0;              // every "seconds since" counter clamps here
// Body memory
const float BODY_BLUR_TEXELS = 1.5, HOLE_FILL_TEXELS = 2.5;   // as endless_sunset
const float PRESENCE_EASE_S  = 0.12;     // eases presence so 1-px edge flicker averages out
const float BODY_ON          = 0.5;      // presence above this is body
const float BODY_OFF         = 0.3;      // ... and a texel stays body until below this, so a flickering edge holds still
const int   RUN_STEPS        = 64;       // max march taps each way
const float RUN_STEP_H       = 1.0/64.0; // march step, screen heights: RUN_STEPS of them cover a full screen height
const int   RUN_REFINE       = 6;        // bisections of the last march step, down to the edge texel (to 1080p), so a run's texels agree
const float RUN_EASE_S       = 0.15;     // eases run extents; snaps when they jump more than RUN_SNAP
const float RUN_SNAP         = 0.08;     // screen heights
const float LEAVE_S          = 2.0;      // a lost person's plants rewind away over this
const float HOLD_Q           = 1.0/128.0; // 0.9 * hold is stored in multiples of this, so it is exact in a half float for any owner
// Garden
const float GROW_S = 20.0, REWIND_S = 20.0;           // empty → full bloom, full bloom → empty
const float GROW_Q = 1.0/2048.0;        // growth is stored in multiples of this (a half float's step just below 1)
const float BASE_BAND = 0.04;           // screen heights above the box bottom that count as feet
const int   BASE_TAPS = 16;
const float BASE_EASE_S = 0.3;
const float WALK_DIST   = 0.04;         // screen heights the base must move from the spot to count as a step
const float WALK_HOLD_S = 0.4;          // walking lasts this long after the last step
const float INHERIT_S = 3.0, INHERIT_DIST = 0.15;     // ghost lifetime; how near a new track must appear (screen heights)
const float SPLIT_GAP = 0.03;            // a new track this close to a live one (box gap, screen heights) is a split of it and
                                        // inherits its growth: the tracker merges touching people, so a gap this small means a split
const float SUN_FULL = 1.0, SUN_EASE_S = 1.5;         // total growth that fully lights the sun
// Plants
const float VINE_SPACING = 4.5/360.0;   // ~30 vines across an adult, as the mockup's Dense panel
const int   VINE_NEIGHBOURS = 4;        // vines evaluated each side of a pixel. Was 2: a leaf or flower reaches
                                        // ~4.5 vines sideways (wobble + sway + its size), and at 2 they were cut off
                                        // in visible straight lines. Lower it first if the Pi falls short of frame rate.
const float VINE_WOBBLE = 5.0/360.0, SWAY_AMP = 2.0/360.0, SWAY_HZ = 0.25;
const float STEM_W = 2.2/360.0, INK_W = 1.2/360.0;
const float LEAF_STEP = 18.0/360.0, LEAF_LEN = 9.0/360.0, LEAF_WID = 3.8/360.0;
const float FLOWER_FROM = 0.6, FLOWER_FULL = 0.9;     // growth at which buds start, and are fully open
const float FLOWER_R = 8.0/360.0, BUD_R = 2.5/360.0;
const float SAT_MIN = 0.1, SAT_MAX = 0.95;
const float WOBBLE_FREQ = 21.6;         // radians per screen height up a vine (the mockup's 0.06 / px)
const float LEAF_DROOP = 0.8, LEAF_DROOP_VAR = 0.3;   // leaf angle below horizontal, and its random spread (radians)
const float SPROUT_H = 18.0/360.0;      // a stem fades in, and a leaf or bud grows in, over this much vine below it
const float PETAL_R = 0.8, HEART_R = 0.45;            // petal and yellow-centre radius, as fractions of the flower radius
const float PEN_MIN = 1.5;              // thinnest line, render pixels: thinner ones are drawn this wide but fainter
const float REACH = FLOWER_R * (1.0 + PETAL_R);   // a flower's outer radius (FLOWER_R is its petals' ring, as the mockup's r);
                                        // the Image taps B at ±REACH and ±REACH / 2 above and below each pixel
const float SHORT_BLOOM_FROM = 0.5, SHORT_BLOOM_FULL = 0.75;   // a run shorter than these × REACH keeps a bud, not a flower
                                        // (the taps are REACH / 2 apart: they don't find it from every row a flower covers)
// Near-body grid (Buffer C rows 4+): the Image skips cells with no body near, so empty paper costs one fetch.
const float NEAR_CELL = 1.0/32.0;       // cell size; 4 + 1/NEAR_CELL rows of C must fit the render height (36 ≤ 72 at test size)
const float NEAR_STEP = 0.01;           // B is sampled this far apart across a padded cell: finer than the thinnest body
// Furthest a pixel's B taps reach from it: sideways to its outermost vine, up and down to ±REACH. A pixel whose
// taps find no grown run draws nothing, so a cell whose padded box holds no body is paper. Plus a step of slack.
const float NEAR_PAD = max((float(VINE_NEIGHBOURS) + 0.5) * VINE_SPACING, REACH) + NEAR_STEP;
const int   NEAR_ROWS = int(ceil(1.0 / NEAR_CELL));
const int   NEAR_TAPS = int(ceil((NEAR_CELL + 2.0 * NEAR_PAD) / NEAR_STEP)) + 1;   // B samples per side of a padded cell
// Sun
const vec2  SUN_POS = vec2(-0.16, 0.84);   // x from the right edge (screen heights), y as a fraction of height
const float SUN_R = 0.09, RAY_LEN = 0.07;

// ── Palette ───────────────────────────────────────────────────────────────────
const vec3 PAPER  = vec3(0.965, 0.945, 0.894);   // #f6f1e4
const vec3 INK    = vec3(0.067);                 // #111111
const vec3 YELLOW = vec3(1.000, 0.949, 0.000);   // #fff200
const vec3 ORANGE = vec3(0.910, 0.525, 0.184);   // #e8862f
const vec3 PINK   = vec3(0.910, 0.584, 0.498);   // #e8957f
const vec3 VIOLET = vec3(0.420, 0.357, 0.584);   // #6b5b95
const vec3 RUST   = vec3(0.737, 0.298, 0.149);   // #bc4c26

// ── Blob records (ADR-0022) ───────────────────────────────────────────────────
const float S_EMPTY = 0., S_TENTATIVE = 1., S_CONFIRMED = 2., S_COASTING = 3., S_LOST = 4.;

vec4 recBox(sampler2D b, int k) { return texelFetch(b, ivec2(k, 0), 0); }   // x0, y0, x1, y1  Body UV
vec4 recMot(sampler2D b, int k) { return texelFetch(b, ivec2(k, 1), 0); }   // cx, cy, vx, vy  UV, UV/s
vec4 recIdn(sampler2D b, int k) { return texelFetch(b, ivec2(k, 2), 0); }   // id, state, age_s, near
bool isState(float s, float want) { return abs(s - want) < 0.5; }

// ── Garden state accessors (Buffer C) ─────────────────────────────────────────
vec4 cPerson(sampler2D c, int k) { return texelFetch(c, ivec2(k, 0), 0); }
vec4 cBase  (sampler2D c, int k) { return texelFetch(c, ivec2(k, 1), 0); }
vec4 cGhost (sampler2D c, int k) { return texelFetch(c, ivec2(k, 2), 0); }
vec4 cSun   (sampler2D c)        { return texelFetch(c, ivec2(0, 3), 0); }
bool cNear  (sampler2D c, vec2 screenPos) {      // screenPos in screen heights; is any body near?
    return texelFetch(c, ivec2(floor(screenPos / NEAR_CELL)) + ivec2(0, 4), 0).x > 0.5;
}

// ── Body memory accessors (Buffer B .a = owner + 0.9 * hold) ──────────────────
int   bOwner(vec4 b) { return int(floor(b.a)); }
float bHold (vec4 b) { return clamp(fract(b.a) / 0.9, 0.0, 1.0); }

// UV → screen-height units. A macro: Shadertoy's Common tab can't see iResolution.
#define toScreen(uv) ((uv) * iResolution.xy / iResolution.y)

// ── Noise ─────────────────────────────────────────────────────────────────────
float hash12(vec2 p) {
    vec3 p3 = fract(vec3(p.xyx) * 0.1031);
    p3 += dot(p3, p3.yzx + 33.33);
    return fract((p3.x + p3.y) * p3.z);
}
float noise(vec2 p) {                    // value noise, 0…1
    vec2 i = floor(p), f = fract(p);
    f = f * f * (3.0 - 2.0 * f);
    return mix(mix(hash12(i), hash12(i + vec2(1, 0)), f.x),
               mix(hash12(i + vec2(0, 1)), hash12(i + vec2(1, 1)), f.x), f.y);
}
