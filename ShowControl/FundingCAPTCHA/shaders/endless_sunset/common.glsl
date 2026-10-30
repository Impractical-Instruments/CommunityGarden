// Common — every tunable for the endless sunset lives here (edit, save, press R).
// Lengths are in screen heights unless noted; mockup px / 360 = screen heights.

// ── Endless motion ────────────────────────────────────────────────────────────
const float LOOP_S           = 360.0;   // clock wraps here: every clock-driven motion must do a whole number of cycles per LOOP_S
const float N_LAYERS         = 6.0;
const float T_RAYS           = 9.0;     // s per layer cycle at rate 1  (40 per loop)
const float T_RINGS          = 11.25;   // s per layer cycle at rate 1  (32 per loop)
const float LAYER_GROWTH     = 8.0;

// ── States ────────────────────────────────────────────────────────────────────
const float RATE_EMPTY       = 0.35;
const float RATE_AWAKE       = 1.0;
const float RATE_FLAIL_BONUS = 0.6;
const float DIM_EMPTY        = 0.5;     // wash strength when empty
const float AWAKE_COVERAGE   = 0.004;   // fraction of state samples present that counts as fully awake
const float AWAKE_RISE_S     = 1.5;
const float AWAKE_FALL_S     = 2.5;

// ── Movement (camera noise vs flailing) ───────────────────────────────────────
const float BODY_BLUR_TEXELS = 1.5;     // soft-presence tap spacing, in camera texels
const float MOTION_FLOOR     = 0.3;     // distance from the running average below this is camera noise
const float MOTION_AVG_S     = 0.5;     // running-average window that movement is measured against
const float MOTION_DECAY_S   = 0.6;     // movement trail time constant
const float FLAIL_FULL       = 0.05;    // mean trail over samples that counts as full flail
const float FLAIL_RISE_S     = 0.3;
const float FLAIL_FALL_S     = 1.0;

// ── Ripples and squiggles ─────────────────────────────────────────────────────
const float RIPPLE_FALLOFF   = 45.0 / 360.0;
const float RIPPLE_STEP_PX   = 4.0;     // ripple field spreads this many render px per frame
const float RIPPLE_AMP       = 9.0 / 360.0;
const float RIPPLE_WAVES     = 30.0;    // radians per screen height; keep RIPPLE_AMP * RIPPLE_WAVES < 1 or the picture folds over
const float RIPPLE_STANDING  = 0.12;    // ripple strength when present but still
const float WIGGLE_MIN       = 1.2 / 360.0;
const float WIGGLE_MAX       = 7.0 / 360.0;
const float INK_W            = 2.2 / 360.0;

// ── Palette ───────────────────────────────────────────────────────────────────
const vec3 PAPER      = vec3(246, 241, 228) / 255.0;
const vec3 INK        = vec3( 17,  17,  17) / 255.0;
const vec3 SLATE      = vec3(113, 154, 173) / 255.0;
const vec3 DEEP       = vec3( 32, 118, 163) / 255.0;
const vec3 RUST       = vec3(188,  76,  38) / 255.0;
const vec3 YELLOW     = vec3(255, 242,   0) / 255.0;
const vec3 PALE       = vec3(251, 233, 160) / 255.0;
const vec3 WARM_WHITE = vec3(255, 250, 240) / 255.0;
const vec3 ORANGE     = vec3(232, 134,  47) / 255.0;
const vec3 PINK       = vec3(232, 149, 127) / 255.0;
const vec3 VIOLET     = vec3(107,  91, 149) / 255.0;
const vec3 DIM_WASH   = vec3( 29,  53,  80) / 255.0;

// ── Helpers ───────────────────────────────────────────────────────────────────
// The only way clock-driven code may build a sine argument, so the wrap is seamless.
float loopWave(float t, float cyclesPerLoop) { return 6.2831853 * cyclesPerLoop * t / LOOP_S; }

float layerPhase(float t, float periodS, float i) { return fract(t / periodS + i / N_LAYERS); }
float layerScale(float p) { return pow(LAYER_GROWTH, p); }
float layerAlpha(float p) { float s = sin(3.14159265 * p); return s * s; }

// State buffer texel (0,0): .r awake, .g flail, .b clock whole s, .a clock fraction.
vec4  readState(sampler2D stateBuf) { return texelFetch(stateBuf, ivec2(0), 0); }
float stateClock(vec4 s) { return s.b + s.a; }
