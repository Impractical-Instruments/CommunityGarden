// Common — every tunable for the watering can lives here (edit, save, press R).
// Lengths are in screen heights unless noted; mockup px / 360 = screen heights.
// Spec: docs/superpowers/specs/2026-11-06-watering-can-design.md
//
// Body memory (Buffer B, per pixel):
//   .r presence 0–1 (soft, hole-filled, eased)   .g run bottom y (UV)   .b run top y (UV)
//   .a owner + 0.9 * hold   (owner = slot + 1, 0 none; hold 0–1, 1 while the body is present)
// Garden state (Buffer C), texel (x, y), k = slot 0–7:
//   (k, 0) PERSON  id (0 none), growth 0–1, planted spot x, y (UV)
//   (k, 1) BASE    base x, base y (UV, smoothed), seconds since last walking step (negative: re-planting,
//                  -seconds to go), record state last frame
//   (k, 2) GHOST   spot x, y, growth at loss, seconds since loss (T_CLAMP = no ghost)
//   (0, 3) SUN     sun level 0–1 (eased), raw total growth, next footprint f (the ring's head), —
//   (1 + f, 3) FOOT footprint f = 0–FOOTPRINTS-1: x, y (UV), seconds since dropped (T_CLAMP none), seed
//   (TREE_P_X + k, 3) TREE PERSON  farthest path distance on k's body (eased), root y, growth 0–1, root x
//                  (screen heights; the root is the middle of their lowest cells, eased)
//   (i, 4 + j) TREE  grid cell (i, j) = screen [i, i + 1] × [j, j + 1] · TREE_CELL (screen heights):
//                    on a body: path distance to its person's root, seeds whose paths run through it (0: no
//                    branch here), owner + parent / 16 (parent 0 the root, 1–8 TREE_DIRS), node offset in the
//                    cell (qx * 16 + qy, q 0–15);
//                    off a body: -1, 1 if a body or a footprint's plants are near else 0, 0, 0. See cTree().

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
const float LEAVE_S          = 2.0;      // a lost person's plants rewind away over this
const float HOLD_Q           = 1.0/128.0; // 0.9 * hold is stored in multiples of this, so it is exact in a half float for any owner
// Garden
const float GROW_S = 20.0, REWIND_S = 20.0;           // empty → full bloom, full bloom → empty
const float GROW_EARLY = 0.3, GROW_EARLY_S = 2.0;     // growth starts fast, reaching GROW_EARLY in GROW_EARLY_S,
                                                      // then slows to reach full bloom at GROW_S
const float GROW_Q = 1.0/2048.0;        // growth is stored in multiples of this (a half float's step just below 1)
const float BASE_BAND = 0.04;           // screen heights above the lowest body row that count as feet
const int   BASE_TAPS = 16;
const float BASE_EASE_S = 0.3;
const float BASE_WIN = 0.14;            // feet count only this far either side of the last base (screen heights; about
                                        // a stance), so a neighbour the tracker merges into the box can't pull it
const float BASE_FEET = 1.0;            // the box bottom is this person's feet if their window finds this much presence
                                        // there (in taps' worth); else it is a merged neighbour's (nearer the camera)
const int   BASE_ITERS = 3;             // the window re-centres on the feet it finds this many times a frame, so it
                                        // keeps up with a walk (each pass reaches BASE_WIN further)
const float BASE_UP  = 0.1;             // the window finds the lowest body row from the legs this far above the last
                                        // base (screen heights): more than the eased base lags a step up the image
const float REPLANT_S = 0.5;            // for this long after a neighbour within SPLIT_GAP changes tracker state (a
                                        // merge or a split), a person re-plants where they stand instead of stepping
const float WALK_DIST   = 0.04;         // screen heights the base must move from the spot to count as a step
const float WALK_HOLD_S = 0.4;          // walking lasts this long after the last step
const float INHERIT_S = 3.0, INHERIT_DIST = 0.15;     // ghost lifetime; how near a new track must appear (screen heights)
const float SPLIT_GAP = 0.03;            // a new track this close to a live one (box gap, screen heights) is a split of it and
                                        // inherits its growth: the tracker merges touching people, so a gap this small means a split
const float SUN_FULL = 1.0, SUN_EASE_S = 1.5;         // total growth that fully lights the sun
// Plants
const float VINE_SPACING = 8.0/360.0;   // ~17 branches across an adult; their twigs fill between
const int   VINE_NEIGHBOURS = 4;        // vines evaluated each side of a pixel. Was 2: a twig or flower reaches
                                        // ~4 vines sideways (wobble + sway + its size), and at 2 they were cut off
                                        // in visible straight lines. Lower it first if the Pi falls short of frame rate.
const float VINE_WOBBLE = 2.5/360.0, SWAY_AMP = 2.0/360.0, SWAY_HZ = 0.25;
const float WOBBLE_FREQ = 21.6;         // radians per screen height up a branch (the mockup's 0.06 / px)
const float KINK_AMP = 0.5, KINK_FREQ = 2.7;          // a second, faster wobble (× VINE_WOBBLE, × WOBBLE_FREQ): gnarled, not wavy
const float INK_W = 0.8/360.0;
// Branches are drawn as the concept art's: a filled, ink-outlined trunk that tapers to its tip, with
// twigs forking off it (blended into it, so the outline runs round the fork) that end in sprigs of petals.
const float STEM_W = 4.0/360.0, STEM_TIP_W = 1.2/360.0;   // trunk width at its base and at its tip
const float STEM_TAPER_H = 60.0/360.0;  // the trunk tapers over this much branch below its tip
const float BARK_HATCH = 0.2, BARK_FREQ = 90.0;       // a broken ink stroke down the trunk's shaded side: offset (× width), dash rate
const float TWIG_STEP = 18.5/360.0;     // twigs fork off every this much trunk, on alternating sides
const float TWIG_LEN = 11.0/360.0, TWIG_W = 1.8/360.0; // twig length, and width where it leaves the trunk
const float TWIG_RISE = 0.6, TWIG_RISE_VAR = 0.35;    // twig angle above horizontal, and its random spread (radians)
const float TWIG_FORK = 0.45;           // the fraction of twigs that fork once more, partway along...
const float FORK_AT = 0.55, FORK_LEN = 0.5, FORK_ANG = 0.75;   // ... at this fraction of the twig, this × as long, turned up this far
const float WOOD_FILLET = 1.5/360.0;    // the trunk and its twigs blend over this, so a fork reads as one piece of wood
const float PAIR_H = 50.0/360.0;        // branches rise in pairs from one root, parting over about this much branch
const float SPRIG_LEN = 7.5/360.0, SPRIG_WID = 1.5/360.0;     // a sprig's petals: length, half-width
const float SPRIG_FAN = 0.85, SPRIG_LIFT = 0.6;       // petals fan ± this (radians) round the twig, turned up by this much
const float FLOWER_FROM = 0.6, FLOWER_FULL = 0.9;     // growth at which buds start, and are fully open
const float FLOWER_R = 8.0/360.0, BUD_R = 2.5/360.0;
const float SAT_MIN = 0.1, SAT_MAX = 0.95;
const float SPROUT_H = 18.0/360.0;      // a trunk fades in, and a twig or bud grows in, over this much branch below it
// The flower is a daisy: DAISY_N long petals round an oval centre, hatched in ink near their roots.
const float PETAL_R = 0.8, HEART_R = 0.7;            // petals reach FLOWER_R × (1 + PETAL_R); centre radius, × FLOWER_R
const int   DAISY_N = 12;
const float DAISY_FRAC = 0.5;            // the fraction of branch tips that open into a daisy; the rest end in a sprig
// Flowers bloom all through the growth: TWIG_FLOWER_FRAC of twigs end in a daisy instead of a sprig, opening
// once the growing tip has climbed TWIG_FLOWER_OPEN_H past it. Low on a run they are small and pale; higher
// (so later, as growth climbs and slows) larger and bolder. The tips' late daisies are the largest and boldest.
const float TWIG_FLOWER_FRAC = 0.5;
const float TWIG_FLOWER_OPEN_H = 30.0/360.0;
const float TWIG_FLOWER_R_MIN = 2.5/360.0, TWIG_FLOWER_R_MAX = 6.5/360.0;   // radius (petals' ring) at a run's bottom, top
const float BOLD_MIN = 0.35;            // how much colour a flower at a run's bottom has (the rest is paper); 1 at its top
const float BOLD_YOUNG = 0.6;           // ... times this while the person's growth is young, rising to 1 at full bloom
const float DAISY_PETAL_W = 0.3;        // a petal's half-width at its tip, × the flower radius
const float PEN_MIN = 1.5;              // thinnest line, render pixels: thinner ones are drawn this wide but fainter
const float REACH = FLOWER_R * (1.0 + PETAL_R);   // a flower's outer radius (FLOWER_R is its petals' ring, as the mockup's r);
                                        // the Image taps B at ±REACH and ±REACH / 2 above and below each pixel
const float SHORT_BLOOM_FROM = 0.5, SHORT_BLOOM_FULL = 0.75;   // a run shorter than these × REACH keeps a bud, not a flower
                                        // (the taps are REACH / 2 apart: they don't find it from every row a flower covers)
// Footprints: a walker leaves plants behind on the floor where they step (Buffer C row 3, a ring).
const int   FOOTPRINTS = 32;            // live at once; when all are, walkers leave none until the oldest has gone
const float FOOT_GAP = 0.12;            // a walker drops a footprint where their feet are this far (screen heights)
                                        // from every live one
const float FOOT_GROW_S = 1.5, FOOT_HOLD_S = 4.0, FOOT_FADE_S = 2.0;   // grows in fast, holds, rewinds away
const float FOOT_LIFE = FOOT_GROW_S + FOOT_HOLD_S + FOOT_FADE_S;
const int   FOOT_SPROUTS = 3;           // little branches in a footprint's clump
const float FOOT_H = 0.08;              // the tallest stands this high (screen heights)
const float FOOT_SPREAD = 0.025;        // they stand across this either side of the footprint
const float FOOT_LEAN = 0.35;           // and lean up to this far sideways per unit height
const float FOOT_FLOWER_FROM = 0.5, FOOT_FLOWER_R = 5.0/360.0;   // the middle one's daisy opens from this growth; its size
// How far a footprint's plants reach from it: sideways, below, above (for the near grid and the Image's bounds).
const float FOOT_REACH_X = FOOT_SPREAD * 1.2 + FOOT_LEAN * FOOT_H + 0.7 * TWIG_LEN + SPRIG_LEN + INK_W;
const float FOOT_REACH_DOWN = SPRIG_LEN + INK_W;
const float FOOT_REACH_UP = FOOT_H + max(SPRIG_LEN, FOOT_FLOWER_R * (1.0 + PETAL_R)) + INK_W;
// The tree (Buffer C rows 4+). Each person's plants are one tree, rooted on the floor at their base (feet).
// Every body cell's parent is its neighbour on the cheapest path back to the root through that person's body;
// paths cost more near the silhouette's edge, so they run up the middle of the legs, torso and arms. A cell is
// grown once its path distance is within growth × the farthest on the body: growth climbs from the root, up
// the legs, then out along the arms and up the neck, and never starts a new root. Only the paths of a
// scattering of seed cells (TREE_SEED_FRAC) are branches, so the tree is sparse; a branch's width comes from how
// many seeds lie above it (thick at the root, thin at the tips), and every seed carries a sprig or a daisy.
// The branches don't depend on growth, so growth runs along them: tips extend, nothing pops in. An arm's path through the shoulder
// doesn't change as it waves, so waving keeps its growth.
const float TREE_CELL = 1.0/48.0;       // cell size; 4 + 1/TREE_CELL rows of C must fit the render height (52 ≤ 72 at test size)
const int   TREE_ROWS = 48;             // = 1 / TREE_CELL
const int   TREE_COLS_MAX = 96;         // widest grid (aspect ≤ 2)
const float TREE_FILL = 0.25;           // a cell is body when this much of it is (of 16 samples); stays until half that
const float TREE_EDGE_COST = 8.0;       // a step costs 1 + this × (1 − how much of a ring round it is body): stay central
const float TREE_EDGE_R = 1.6;          // the rings' radii: this and twice this, in cells
const float TREE_ROOT_BAND = 1.5 * TREE_CELL;   // cells this close above the base are the root's (they join it on the floor)
const float TREE_ROOT_WIN = 0.35;       // ... if within this of it sideways (screen heights): both feet, however wide
const float TREE_FAR = 50.0;            // the path distance of a body cell no path reaches
const float TREE_ROOT_EASE_S = 1.0;     // the root point eases over this
const float TREE_WIDTH_EASE_S = 1.0;    // branch widths (seed counts) ease over this
const float TREE_PARENT_HYST = 0.05;    // a cell changes its way back to the root only for one this much cheaper
const float TREE_MAX_EASE_S = 1.0;      // the farthest path distance eases over this (so a raised arm doesn't jolt the front)
const int   TREE_P_X = 34;              // TREE PERSON texels: row 3, from x = this (after the footprints)
const float TREE_SEED_FRAC = 0.35;     // the share of body cells that are seeds: a branch runs from each to the root
const float TREE_ROOT_W = 7.0/360.0, TREE_W_K = 1.1/360.0;   // branch width: TREE_W_K × sqrt(seeds above), up to TREE_ROOT_W
const float TREE_JITTER = 0.5;          // nodes are jittered this much (cells) so the grid doesn't show
const float TREE_FILLET = 4.0/360.0;     // the tree's branches blend over this where they meet (closes slits between near paths)
const int   TREE_R = 3;                 // the Image draws the cells within this many of a pixel's
const int   MAX_TIPS = 12;              // sprigs and flowers a pixel can see at once
const float TREE_OPEN_D = 3.0 * TREE_CELL;   // a flower opens as the growth front passes this far beyond it
const ivec2 TREE_DIRS[8] = ivec2[8](ivec2(-1, -1), ivec2(0, -1), ivec2(1, -1), ivec2(-1, 0),
                                    ivec2(1, 0), ivec2(-1, 1), ivec2(0, 1), ivec2(1, 1));
// Sun
const vec2  SUN_POS = vec2(-0.16, 0.84);   // x from the right edge (screen heights), y as a fraction of height
const float SUN_R = 0.09, RAY_LEN = 0.07;
const int   SUN_RAYS = 12;               // crayon rays at full level
const float SUN_MUTE = 0.8;              // paper mixed into the yellow at level 0 (0 = full yellow)
const float SUN_EDGE_WOBBLE = 0.07;      // the disc's edge is broken by noise: ± this fraction of SUN_R
const float SUN_GRAIN = 45.0;            // crayon grain scale, cycles per screen height
const float SUN_COVER = 0.4;             // grain threshold: higher = more paper shows through the fill
const float SUN_RAY_W = 0.011;           // ray half-width (screen heights), tapering to a point
const float SUN_RAY_FROM = 1.2;          // rays start this many SUN_R from the centre
const float SUN_WOBBLE_RATE = 0.3;       // the wobble's clock: noise offsets move this fast per second
const float SUN_DRIFT = 0.02;            // rays turn this many ray-widths per wobble-second (slow drift)
const float SUN_EDGE_SCALE = 25.0;       // scale of the noise that breaks the disc's edge, cycles per screen height
const float SUN_RIM_FROM = 0.75, SUN_RIM_WEIGHT = 0.25;   // the pressed stroke starts at this fraction of the edge; extra grain it adds
const float SUN_FILL_SOFT = 0.03;        // softness of the fill's grain threshold
const float SUN_GRAIN_A = 0.6;           // weight of the round grain; the stretched (hatching) grain gets the rest
const vec2  SUN_HATCH = vec2(0.2, 1.3);  // the hatching grain's scale along and across the stroke, × SUN_GRAIN
const float SUN_RAY_MIN = 0.003;         // rays shorter than this (screen heights) aren't drawn
const float SUN_RAY_LEN_JITTER = 0.2;    // each ray's length varies by up to this fraction below full
const float SUN_RAY_SKEW = 0.1;          // each ray's angle varies by ± half this many ray spacings
const float SUN_RAY_TAPER = 0.6;         // a ray's width shrinks by this fraction toward its tip
const float SUN_RAY_W_JITTER = 0.3;      // width varies by ± half this fraction, along the ray (noise rate SUN_RAY_W_RATE)
const float SUN_RAY_W_RATE = 6.0;
const float SUN_RAY_GRAIN = 0.7, SUN_RAY_FADE = 0.25, SUN_RAY_BIAS = 0.3;   // ray grain weight; extra fill near the root; base fill
const float SUN_RAY_SOFT = 0.1;          // softness of the ray grain threshold

// ── Palette ───────────────────────────────────────────────────────────────────
const vec3 PAPER  = vec3(0.965, 0.945, 0.894);   // #f6f1e4
const vec3 INK    = vec3(0.067);                 // #111111
const vec3 YELLOW = vec3(1.000, 0.949, 0.000);   // #fff200
const vec3 ORANGE = vec3(0.910, 0.525, 0.184);   // #e8862f
const vec3 PALE   = vec3(0.984, 0.914, 0.627);   // #fbe9a0  pale yellow
const vec3 SKY    = vec3(0.443, 0.604, 0.678);   // #719aad  light blue: the site's band, the concept art's sky

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
vec4 cFoot  (sampler2D c, int f) { return texelFetch(c, ivec2(1 + f, 3), 0); }
// A footprint's growth at `age` seconds: fast in (easing out), holding, then rewinding away; 0 when gone.
float footGrowth(float age) {
    if (age >= FOOT_LIFE) return 0.0;
    if (age < FOOT_GROW_S) { float u = 1.0 - age / FOOT_GROW_S; return 1.0 - u * u; }
    return clamp((FOOT_LIFE - age) / FOOT_FADE_S, 0.0, 1.0);
}
vec4 cTreeP (sampler2D c, int k) { return texelFetch(c, ivec2(TREE_P_X + k, 3), 0); }
int  treeCols(vec2 res) { return min(int(ceil(res.x / res.y / TREE_CELL)), TREE_COLS_MAX); }
vec4 cTree  (sampler2D c, ivec2 cell, vec2 res) {   // a cell off the grid is empty, far from anything
    if (cell.x < 0 || cell.y < 0 || cell.x >= treeCols(res) || cell.y >= TREE_ROWS) return vec4(-1.0, 0.0, 0.0, 0.0);
    return texelFetch(c, cell + ivec2(0, 4), 0);
}
int  treeOwner (vec4 t) { return t.x < 0.0 ? 0 : int(floor(t.z)); }
int  treeParent(vec4 t) { return int(floor(fract(t.z) * 16.0 + 0.5)); }
vec2 treeOffset(vec4 t) { return (vec2(floor(t.w / 16.0), mod(t.w, 16.0)) + 0.5) / 16.0 - 0.5; }   // in cells
bool cNear(sampler2D c, vec2 screenPos, vec2 res) {   // is a body, or a footprint's plants, near?
    vec4 t = cTree(c, ivec2(floor(screenPos / TREE_CELL)), res);
    return t.x >= 0.0 || t.y > 0.5;
}
// Growth for owner slot k: the live person's, or while their plants rewind away, their ghost's.
float growthOf(sampler2D c, int k) {
    vec4 pr = cPerson(c, k);
    if (abs(pr.x) > 0.5) return pr.y;
    vec4 gh = cGhost(c, k);
    return gh.w < LEAVE_S ? gh.z : 0.0;
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
// Is tree cell `cell` a seed (a branch runs from it to the root, and it carries a sprig or a daisy)?
bool treeSeed(ivec2 cell) { return hash12(vec2(cell) * 1.618 + 0.37) < TREE_SEED_FRAC; }
float noise(vec2 p) {                    // value noise, 0…1
    vec2 i = floor(p), f = fract(p);
    f = f * f * (3.0 - 2.0 * f);
    return mix(mix(hash12(i), hash12(i + vec2(1, 0)), f.x),
               mix(hash12(i + vec2(0, 1)), hash12(i + vec2(1, 1)), f.x), f.y);
}
