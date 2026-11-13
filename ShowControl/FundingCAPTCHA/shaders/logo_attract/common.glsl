// Common — every tunable for the logo attract lives here (edit, save, press R).
// Lengths are in screen heights (x runs 0 … aspect, y 0 … 1, origin bottom-left).
//
// The logo rests at the centre. Each tracked visitor pulls it toward their
// centroid with weight = how long they've been tracked (capped), so the pull
// is a weighted average of everyone present, and newcomers ease in.
//
// Buffer B layout, texel (x, y), k = blob slot 0–7:
//   (k, 0) LIFE   id, seconds tracked (confirmed or coasting), 0, 0
//   (0, 1) LOGO   centre x, y (screen heights), velocity x, y (heights/s)

const int   SLOTS = 8;
const float S_EMPTY = 0.0, S_TENTATIVE = 1.0, S_CONFIRMED = 2.0, S_COASTING = 3.0, S_LOST = 4.0;
const float DT_MAX   = 0.1;              // a render hiccup longer than this is treated as this
// pull
const float LIFE_CAP = 20.0;             // s; a visitor's weight stops growing here
const float PULL_HALF = 2.0;             // s of total weight at which the logo goes halfway to the crowd
const float REACH    = 0.9;              // fraction of the way to the crowd the logo goes at full pull
// spring (toward the target)
const float SPRING   = 7.0;              // 1/s²
const float DAMPING  = 3.2;              // 1/s; below 2·sqrt(SPRING) it overshoots a little
const float SPEED_MAX = 1.5;             // heights/s
// look
const float RADIUS   = 0.3;              // logo radius
const float EDGE_IN  = 0.85;             // the logo's centre stays this many radii inside the screen
const float TILT     = 0.35;             // rad of lean per height/s of sideways speed
const float TILT_MAX = 0.3;              // rad
const float BOB      = 0.012;            // idle bob amplitude
const vec3  BG       = vec3(0.0);

bool isState(float s, float v) { return abs(s - v) < 0.5; }
vec4 bLife(sampler2D b, int k) { return texelFetch(b, ivec2(k, 0), 0); }
vec4 bLogo(sampler2D b)        { return texelFetch(b, ivec2(0, 1), 0); }
