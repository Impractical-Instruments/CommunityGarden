// Common — every tunable for Barn Dancers lives here (edit, save, press R).
// A barn on hairy legs rises out of the field for each visitor, stands at their
// left–right position and dances a kick line on a beat the whole troupe shares.
// The more a visitor moves, the bigger their barn dances and the faster the beat.
//
// Screen lengths are in screen heights. A barn is posed in rig units: 1 = the
// barn's own height, (0, 0) = the ground under its middle, y up.
//
// Dancer state (Buffer B) layout, texel (x, y), k = slot 0–7:
//   (k, 0) DANCER  x (Body UV), nearness 0–1, energy 0–1, id (0 = no barn)
//   (k, 1) STAGE   risen 0–1, leaving 0–1, sideways speed (screen heights/s), 0
//   (k, 2) PREV    this slot's box, low-passed over BOX_EMA_S (Body UV)
//   (k, 3) ORDER   the slot of the k-th farthest barn (drawn back to front)
//   (0, 4) BEAT    phase 0–1 through the dance cycle, troupe energy 0–1

const int   SLOTS  = 8;
const float DT_MAX = 0.25;               // a render hiccup longer than this is treated as this

// ── Stage ─────────────────────────────────────────────────────────────────────
const float BARN_H      = 0.25;          // a barn's height (one rig unit), at the middle distance
const float SIZE_FAR    = 0.8, SIZE_NEAR = 1.2;       // × BARN_H for the farthest / nearest visitor
const float GROUND_FAR  = 0.20, GROUND_NEAR = 0.07;   // where their barns stand, above the bottom edge
const float FOLLOW_S    = 0.35;          // a barn eases to its visitor's position over this
const float ENTER_S     = 0.8;           // rising out of the ground
const float EXIT_S      = 1.5;           // the bow, then sinking back
const float BOW_END     = 0.45;          // fraction of EXIT_S spent bowing
const float SINK_DEPTH  = 1.75;          // rig units a hidden barn sits below the ground
const float POP_HOP     = 0.6;           // rig units of hop per unit the rise overshoots
const float SIL_ALPHA   = 0.22;          // how strongly visitors' silhouettes shade the scene

// ── Energy: how much a visitor moves (as hunter_bird's motion) ─────────────────
const float SPEED_FULL   = 0.39;         // screen heights/s of travel that alone reads as energy 1
const float SIZE_FULL    = 0.61;         // screen heights/s of box (w + h) change that alone reads as 1
const float MOTION_FLOOR = 0.15;         // subtracted: tracker breathing and flicker live below this
const float BOX_EMA_S    = 0.15;         // PREV is the box low-passed over this
const float ENERGY_RISE_S = 0.4, ENERGY_FALL_S = 1.6;

// ── Dance ─────────────────────────────────────────────────────────────────────
// One cycle: squat, kick right, squat, kick left (the artist's 14-frame loop).
const float CYCLE_S     = 1.75;          // at troupe energy 0
const float TEMPO_GAIN  = 0.4;           // the beat runs this much faster at troupe energy 1
const float TEMPO_EASE_S = 1.0;
const float AMP_MIN     = 0.5;           // a still visitor's barn dances this big; 1 at energy 1
const float KICK_THIGH  = 1.08;          // radians the kicking thigh swings up (62°)
const float KICK_CALF   = 2.55;          // radians the calf then snaps out (146°)
const float FOOT_FOLLOW = 0.8;           // the kicking foot turns this much of its calf's turn
const float KICK_LEAN   = 0.16;          // radians the barn leans away from its kick
const float KICK_SHIFT  = 0.07;          // rig units it shifts over its standing leg
const float KICK_HOP    = 0.05;          // … and rises at the top of the kick
const float SQUAT       = 0.10;          // rig units it drops between kicks
const float BOW_LEAN    = 0.45, BOW_SQUAT = 0.2;      // the goodbye bow
const float TRAVEL_LEAN = 0.5, TRAVEL_LEAN_MAX = 0.2; // radians per screen height/s walked, and the most
const float EYE_GLANCE  = 0.016;         // rig units the pupils slide toward the kick
const float LID_TRAVEL  = 0.085;         // rig units an eyelid drops to shut
const float BLINK_EVERY_S = 3.7, BLINK_S = 0.22;

// ── Palette ───────────────────────────────────────────────────────────────────
const vec3 INK       = vec3(0.07, 0.06, 0.06);
const vec3 SKY_TOP   = vec3(0.47, 0.72, 0.90), SKY_LOW = vec3(0.86, 0.93, 0.93);
const vec3 CLOUD     = vec3(1.00, 0.99, 0.96);
const vec3 HILL_FAR  = vec3(0.47, 0.67, 0.45), HILL_NEAR = vec3(0.40, 0.62, 0.36);
const vec3 FIELD     = vec3(0.56, 0.74, 0.36), FIELD_ROW = vec3(0.50, 0.69, 0.33);
const vec3 DIRT      = vec3(0.47, 0.33, 0.22);
const vec3 SHADE     = vec3(0.13, 0.20, 0.24);        // silhouettes and barn shadows
const vec3 BARN_RED  = vec3(0.67, 0.27, 0.26), TRIM = vec3(0.98, 0.97, 0.94), SKIN = vec3(0.98, 0.78, 0.71);
const float INK_W    = 0.004;            // background line weight

// ── Sprite sheet ──────────────────────────────────────────────────────────────
// Written by pack_atlas.py from source/barn.psd — rerun it instead of editing.
// ATLAS:BEGIN
const int   PARTS = 11, LODS = 3;
const int   P_EYE_L = 0, P_EYE_R = 1, P_EYELID_L = 2, P_EYELID_R = 3, P_BARN = 4, P_THIGH_L = 5, P_FOOT_L = 6, P_CALF_L = 7, P_THIGH_R = 8, P_FOOT_R = 9, P_CALF_R = 10;
// Each part's rectangle in the standing pose (rig units: x0, y0, x1, y1) …
const vec4  PART_BOX[PARTS] = vec4[PARTS](
    vec4(-0.3391, 0.9681, -0.1263, 1.1795),
    vec4(0.1556, 0.9654, 0.3604, 1.1676),
    vec4(-0.3059, 1.0971, -0.1835, 1.2394),
    vec4(0.1928, 1.0878, 0.3152, 1.2287),
    vec4(-0.5678, 0.5359, 0.5665, 1.5572),
    vec4(-0.7234, 0.3604, -0.3178, 0.7527),
    vec4(-0.7074, -0.0080, -0.4189, 0.1981),
    vec4(-0.7168, 0.0957, -0.4574, 0.4960),
    vec4(0.2753, 0.3271, 0.6902, 0.7114),
    vec4(0.3098, -0.0120, 0.5891, 0.2128),
    vec4(0.3551, 0.1184, 0.6729, 0.4681));
// … and in the full-size copy (fractions of it: u0, v0, u1, v1).
const vec4  PART_UV[PARTS] = vec4[PARTS](
    vec4(0.00625, 0.00629, 0.13125, 0.13208),
    vec4(0.32500, 0.01258, 0.44531, 0.13208),
    vec4(0.45781, 0.04717, 0.52969, 0.13208),
    vec4(0.54219, 0.04874, 0.61406, 0.13208),
    vec4(0.00625, 0.38994, 0.67188, 0.99371),
    vec4(0.00625, 0.14465, 0.24375, 0.37736),
    vec4(0.14375, 0.00943, 0.31250, 0.13208),
    vec4(0.68437, 0.75786, 0.83750, 0.99371),
    vec4(0.25625, 0.15094, 0.50000, 0.37736),
    vec4(0.71250, 0.24528, 0.87656, 0.37736),
    vec4(0.51250, 0.16981, 0.70000, 0.37736));
// Where each copy sits in the sheet (UV origin, UV size): full, half, quarter.
const vec4  LOD_RECT[LODS] = vec4[LODS](vec4(0.00000, 0.00000, 0.66667, 1.00000), vec4(0.66667, 0.50000, 0.33333, 0.50000), vec4(0.66667, 0.25000, 0.16667, 0.25000));
const float SHEET_UNIT = 0.59119;   // one rig unit at full size, as a fraction of the sheet's height
// Leg joints, standing: [0] left leg, [1] right leg.
const vec2  HIP[2] = vec2[2](vec2(-0.4149, 0.6463), vec2(0.3697, 0.6024));
const vec2  KNEE[2] = vec2[2](vec2(-0.6410, 0.4428), vec2(0.6117, 0.4136));
const vec2  ANKLE[2] = vec2[2](vec2(-0.4973, 0.1343), vec2(0.3830, 0.1543));
const float BODY_Y = 0.5465;   // the barn's bottom edge above the ground, standing
// ATLAS:END

// ── Blob records (ADR-0022) ───────────────────────────────────────────────────
const float S_EMPTY = 0., S_TENTATIVE = 1., S_CONFIRMED = 2., S_COASTING = 3., S_LOST = 4.;

vec4 recBox(sampler2D b, int k) { return texelFetch(b, ivec2(k, 0), 0); }   // x0, y0, x1, y1  Body UV
vec4 recMot(sampler2D b, int k) { return texelFetch(b, ivec2(k, 1), 0); }   // cx, cy, vx, vy  UV, UV/s
vec4 recIdn(sampler2D b, int k) { return texelFetch(b, ivec2(k, 2), 0); }   // id, state, age_s, near
bool isState(float s, float want) { return abs(s - want) < 0.5; }

// ── Dancer state accessors ────────────────────────────────────────────────────
vec4  bDancer(sampler2D s, int k) { return texelFetch(s, ivec2(k, 0), 0); }
vec4  bStage (sampler2D s, int k) { return texelFetch(s, ivec2(k, 1), 0); }
vec4  bPrev  (sampler2D s, int k) { return texelFetch(s, ivec2(k, 2), 0); }
int   bOrder (sampler2D s, int k) { return int(texelFetch(s, ivec2(k, 3), 0).x + 0.5); }
vec4  bBeat  (sampler2D s)        { return texelFetch(s, ivec2(0, 4), 0); }

// UV → screen-height units. A macro: Shadertoy's Common tab can't see iResolution.
#define toScreen(uv) ((uv) * iResolution.xy / iResolution.y)

// ── Helpers ───────────────────────────────────────────────────────────────────
float hash11(float n) { return fract(sin(n * 127.1 + 311.7) * 43758.5453); }
vec2  rot2(vec2 p, float a) { float c = cos(a), s = sin(a); return vec2(c * p.x - s * p.y, s * p.x + c * p.y); }   // counter-clockwise
float angleOf(vec2 v) { return atan(v.y, v.x); }
float sdSegment(vec2 p, vec2 a, vec2 b) {
    vec2 pa = p - a, ba = b - a;
    return length(pa - ba * clamp(dot(pa, ba) / max(dot(ba, ba), 1e-9), 0.0, 1.0));
}
// Coverage of a pen stroke `w` wide at distance `d`, antialiased over one pixel `px`.
float pen(float d, float w, float px) {
    w = max(w, px);
    return 1.0 - smoothstep(0.5 * (w - px), 0.5 * (w + px), d);
}
// Overshoots 1 a little before settling: a pop.
float easeOutBack(float x) { float c = 1.70158, y = x - 1.0; return 1.0 + (c + 1.0) * y * y * y + c * y * y; }

// ── Pose ──────────────────────────────────────────────────────────────────────
// Legs: [0] the barn's left on screen, [1] its right. Angles are radians from standing.
struct Pose {
    vec2  body;                          // the barn's bottom-centre
    float lean;                          // counter-clockwise
    vec2  hip[2], knee[2], ankle[2];
    float thigh[2], calf[2], foot[2];
    vec2  eye;                           // the pupils' shift
    float lid;                           // 0 open … 1 shut
};

// Bend leg i from `hip` to reach `target`: the knee points outward, and a
// target beyond reach pulls the foot off the ground along the same line.
void reach(inout Pose P, int i, vec2 target) {
    float l1 = length(KNEE[i] - HIP[i]), l2 = length(ANKLE[i] - KNEE[i]);
    vec2  to = target - P.hip[i];
    float d  = clamp(length(to), abs(l1 - l2) + 1e-3, l1 + l2 - 1e-3);
    vec2  n  = to / max(length(to), 1e-6);
    float a  = (l1 * l1 - l2 * l2 + d * d) / (2.0 * d);
    float h  = sqrt(max(l1 * l1 - a * a, 0.0));
    P.knee[i]  = P.hip[i] + n * a + vec2(-n.y, n.x) * h * (i == 1 ? 1.0 : -1.0);
    P.ankle[i] = P.hip[i] + n * d;
    P.thigh[i] = angleOf(P.knee[i] - P.hip[i])   - angleOf(KNEE[i] - HIP[i]);
    P.calf[i]  = angleOf(P.ankle[i] - P.knee[i]) - angleOf(ANKLE[i] - KNEE[i]);
}

// The dance at `phase` (0–1 through the cycle), `amp` big (0–1). `bow` 0–1
// folds it into the goodbye bow, `travel` leans it (radians), `blink` shuts the eyes.
Pose dancePose(float phase, float amp, float bow, float travel, float blink) {
    Pose P;
    float h    = fract(phase * 2.0);                       // through this half: squat, then one kick
    int   kick = fract(phase) < 0.5 ? 1 : 0;               // right leg first
    float dir  = kick == 1 ? 1.0 : -1.0;
    amp *= 1.0 - bow;
    // The kick: the knee comes up with the calf hanging (lift), then the calf snaps out (snap).
    float lift = smoothstep(0.14, 0.40, h) * (1.0 - smoothstep(0.76, 0.98, h));
    float snap = smoothstep(0.36, 0.56, h) * (1.0 - smoothstep(0.66, 0.90, h));
    float land = abs(fract(h + 0.54) - 0.5) / 0.1;         // 0 on the landing between kicks
    float dip  = SQUAT * amp * exp(-land * land);

    P.body = vec2(-dir * KICK_SHIFT * amp * lift,
                  BODY_Y - dip + KICK_HOP * amp * snap - BOW_SQUAT * bow);
    P.lean = dir * KICK_LEAN * amp * lift + BOW_LEAN * bow + travel;
    P.eye  = vec2(dir * EYE_GLANCE * lift * step(0.01, amp), 0.0);
    P.lid  = max(blink, bow);

    for (int i = 0; i < 2; i++) {
        P.hip[i] = P.body + rot2(HIP[i] - vec2(0.0, BODY_Y), P.lean);
        vec2  target = ANKLE[i];                           // planted
        float up = 0.0;
        if (i == kick) {
            float th = dir * KICK_THIGH * amp * lift, ca = dir * KICK_CALF * amp * snap;
            vec2  knee = P.hip[i] + rot2(KNEE[i] - HIP[i], th);
            up     = smoothstep(0.0, 0.5, lift);
            target = mix(target, knee + rot2(ANKLE[i] - KNEE[i], ca), up);
        }
        reach(P, i, target);
        P.foot[i] = up * FOOT_FOLLOW * P.calf[i];
    }
    return P;
}
