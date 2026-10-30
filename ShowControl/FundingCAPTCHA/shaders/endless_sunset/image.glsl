// Image — the endless sunset.  iChannel0 = Buffer B (Body memory), iChannel1 = Buffer C (State)
// p is in screen heights, origin at the sun's centre on the horizon, y up.

const float HORIZON_Y = 0.34;           // screen heights from the bottom
const float SUN_R     = 40.0 / 360.0;
const float RING_R0   = 56.0 / 360.0;
const float RAY_R0    = 48.0 / 360.0;
const float N_RAYS    = 17.0;
const float PI        = 3.14159265;

float AA;                               // one render pixel, in screen heights

float fillA(float sd)          { return 1.0 - smoothstep(-AA, AA, sd); }
float lineA(float sd, float w) { return 1.0 - smoothstep(0.5 * w - AA, 0.5 * w + AA, abs(sd)); }

vec3 ringColor(float i) {
    return i < 0.5 ? YELLOW : i < 1.5 ? ORANGE : i < 2.5 ? PINK : i < 3.5 ? RUST : i < 4.5 ? VIOLET : SLATE;
}

// Rings: endless half-annuli growing out of the sun, biggest drawn first.
vec3 rings(vec3 col, vec2 p, float t, float ripple) {
    float r = length(p), th = atan(p.y, p.x);
    float base = t / T_RINGS;
    float f = fract(base * N_LAYERS), shift = floor(base * N_LAYERS);
    for (float k = N_LAYERS - 1.0; k >= 0.0; k--) {
        float ph = (k + f) / N_LAYERS;                      // = layerPhase(t, T_RINGS, i), in descending order
        float i  = mod(k - shift, N_LAYERS);                // which layer this is, so its colour sticks
        float a  = layerAlpha(ph);
        float R  = RING_R0 * layerScale(ph) * (1.0 + 0.05 * sin(9.0 * th + loopWave(t, 74.0) + i)) + ripple;
        float sd = r - R;
        col = mix(col, ringColor(i), fillA(sd) * 0.75 * a);
        col = mix(col, INK, lineA(sd, INK_W) * a);
    }
    return col;
}

// Rays: sine-wiggled segments streaming outward, warm white / pale yellow, no outline.
vec3 rays(vec3 col, vec2 p, float t, float ripple) {
    float th = atan(p.y, p.x);
    float k0 = clamp(floor(th / (PI / N_RAYS)), 0.0, N_RAYS - 1.0);
    for (float dk = -1.0; dk <= 1.0; dk++) {
        float k = k0 + dk;
        if (k < 0.0 || k > N_RAYS - 1.0) continue;
        float a  = PI * (k + 0.5) / N_RAYS;
        vec2  d  = vec2(cos(a), sin(a));
        float along = dot(p, d);
        float perp  = d.x * p.y - d.y * p.x;
        float wob   = sin(along * 43.2 - loopWave(t, 172.0)) * (4.0 / 360.0 + 0.03 * along) + 1.3 * ripple;
        float odd   = mod(k, 2.0);
        for (float i = 0.0; i < N_LAYERS; i++) {
            float ph = layerPhase(t, T_RAYS, i + 0.5 * odd);
            float rA = RAY_R0 * layerScale(ph), rB = 1.35 * rA;
            float w  = (3.0 + 2.0 * ph) / 360.0;
            float sd = length(vec2(max(rA - along, 0.0) + max(along - rB, 0.0), perp - wob)) - 0.5 * w;
            vec3  c  = mod(k + i, 3.0) < 0.5 ? PALE : WARM_WHITE;
            col = mix(col, c, fillA(sd) * layerAlpha(ph));
        }
    }
    return col;
}

// Water: hatched ripple lines below the horizon, with the sun's orange reflection.
vec3 water(vec3 col, vec2 p, float t) {
    float depth = -p.y;
    for (float j = 1.0; j < 9.0; j++) {
        float y   = (j * j * 1.6 + 4.0) / 360.0;
        float wig = sin(p.x * 18.0 + loopWave(t, 115.0) + j) * 1.6 / 360.0;
        col = mix(col, mod(j, 2.0) > 0.5 ? DEEP : INK, lineA(depth - y - wig, 1.4 / 360.0));
        float half_ = SUN_R * (1.0 - j / 10.0);
        float x  = p.x - sin(loopWave(t, 115.0) + j) * 4.0 / 360.0;
        float sd = length(vec2(max(abs(x) - half_, 0.0), depth - y));
        col = mix(col, ORANGE, lineA(sd, 3.0 / 360.0));
    }
    return col;
}

vec3 sunset(vec2 p, float t, float ripple) {
    vec3 col = PAPER;
    if (p.y > 0.0) {
        col = rings(col, p, t, ripple);
        col = rays(col, p, t, ripple);
        float sd = length(p) - SUN_R;
        col = mix(col, YELLOW, fillA(sd));
        col = mix(col, INK, lineA(sd, 2.5 / 360.0));
    } else {
        col = water(col, p, t);
    }
    return mix(col, INK, lineA(p.y, 2.5 / 360.0));         // horizon
}

void mainImage(out vec4 o, in vec2 fc) {
    AA = 1.0 / iResolution.y;
    vec2 p = (fc - vec2(0.5 * iResolution.x, HORIZON_Y * iResolution.y)) / iResolution.y;
    vec4 s = readState(iChannel1);

    vec3 col = sunset(p, stateClock(s), 0.0);
    col = mix(col, DIM_WASH, DIM_EMPTY * (1.0 - s.r));
    o = vec4(col, 1.0);
}
