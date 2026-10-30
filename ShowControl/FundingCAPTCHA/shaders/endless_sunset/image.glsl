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
float lineA(float sd, float w) {
    w = max(w, 2.5 * AA);               // never thinner than a pen stroke, at any render size
    return 1.0 - smoothstep(0.5 * w - AA, 0.5 * w + AA, abs(sd));
}

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

// How big is the blob under this pixel? Local *solid* body coverage, 0 = a lone speck … 1 = a person.
// Counting only solid taps keeps dense loose grain (depth noise) from passing as a person.
float blobSize(vec2 uv) {
    vec2  r = BLOB_REACH * vec2(iResolution.y / iResolution.x, 1.0);
    float c = 0.0;
    for (int k = 0; k < 8; k++) {
        float a = 0.7853982 * float(k);
        vec2  d = vec2(cos(a), sin(a));
        c += step(BLOB_SOLID, texture(iChannel0, uv + d * r * 0.4).r)
           + step(BLOB_SOLID, texture(iChannel0, uv + d * r).r);
    }
    return smoothstep(BLOB_SMALL, BLOB_LARGE, c / 16.0);
}

// The person: fill and ink outline that squiggles with local movement. Small blobs (camera
// noise) get a tinted, see-through fill and no outline; full-size people are opaque warm white.
// The squiggle shifts where the Body is sampled, so it works at any amplitude.
vec3 person(vec3 col, vec2 fc, vec4 b) {
    if (b.b < 0.01) return col;                             // nobody near: skip the taps
    vec2  q   = fc / iResolution.y;
    float amp = WIGGLE_MIN + (WIGGLE_MAX - WIGGLE_MIN) * b.g;
    vec2  off = amp * vec2(sin(q.y * 28.8 - iTime * 7.0), sin(q.x * 32.4 + iTime * 9.0));
    vec2  px  = 1.0 / iResolution.xy;
    vec2  uv  = fc * px + off * iResolution.y * px;
    float size  = blobSize(uv);
    float level = mix(BLOB_MIN_LEVEL, 0.5, size);
    float soft  = texture(iChannel0, uv).r;
    vec2 g = vec2(texture(iChannel0, uv + vec2(px.x, 0.0)).r - texture(iChannel0, uv - vec2(px.x, 0.0)).r,
                  texture(iChannel0, uv + vec2(0.0, px.y)).r - texture(iChannel0, uv - vec2(0.0, px.y)).r)
             / (2.0 * AA);
    float d = (level - soft) / max(length(g), 1e-3);       // ≈ signed distance to the edge, screen heights

    vec3  fill  = size < 0.5 ? mix(BLOB_SMALL_COL, BLOB_MID_COL, size * 2.0)
                             : mix(BLOB_MID_COL, WARM_WHITE, size * 2.0 - 1.0);
    float alpha = mix(BLOB_MIN_ALPHA, BLOB_MAX_ALPHA, size);
    float ink   = smoothstep(BLOB_INK_FROM, 1.0, size);   // specks: no outline, and no inset for one
    col = mix(col, fill, fillA(d + 0.75 * INK_W * ink) * alpha);
    return mix(col, INK, lineA(d, 1.5 * INK_W) * ink);
}

// The ripple field around people, averaged over a wide patch: .x field, .yz its gradient.
// Ripples and stir both read this, so the push changes smoothly (a sharp change folds the picture).
vec3 fieldAround(vec2 fc) {
    vec2  px = 1.0 / iResolution.xy, uv = fc * px, h = LIQUID_SMOOTH * iResolution.y * px;
    float e = texture(iChannel0, uv + vec2(h.x, 0.0)).b, w = texture(iChannel0, uv - vec2(h.x, 0.0)).b;
    float n = texture(iChannel0, uv + vec2(0.0, h.y)).b, s = texture(iChannel0, uv - vec2(0.0, h.y)).b;
    return vec3(0.2 * (e + w + n + s + texture(iChannel0, uv).b), e - w, n - s);
}

// Liquid stir: push the background sideways around people (a swirl) and a little in and out.
vec2 stir(vec3 f, float dist, float strength) {
    float gl = length(f.yz);
    vec2  n  = f.yz / max(gl, 1e-5) * smoothstep(0.0, 0.02, gl);   // toward the person; 0 where flat
    vec2  tg = vec2(-n.y, n.x);
    float w  = dist * LIQUID_WAVES;
    return LIQUID_AMP * strength * f.x
         * (tg * sin(w - iTime * LIQUID_SPEED) + n * 0.5 * cos(0.7 * w + 0.6 * iTime * LIQUID_SPEED));
}

void mainImage(out vec4 o, in vec2 fc) {
    AA = 1.0 / iResolution.y;
    vec2 p = (fc - vec2(0.5 * iResolution.x, HORIZON_Y * iResolution.y)) / iResolution.y;
    vec4 s = readState(iChannel1);
    vec4 b = texture(iChannel0, fc / iResolution.xy);

    // Ripples travel outward from people: faint when they stand, full when they flail.
    vec3  f        = fieldAround(fc);
    float dist     = -RIPPLE_FALLOFF * log(max(f.x, 1e-3));
    float strength = s.r * mix(RIPPLE_STANDING, 1.0, s.g);
    float ripple   = strength * RIPPLE_AMP * f.x * sin(dist * RIPPLE_WAVES - iTime * 9.0);

    vec2 warp = stir(f, dist, s.r * mix(LIQUID_STANDING, 1.0, s.g));

    vec3 col = sunset(p + warp, stateClock(s), ripple);
    col = person(col, fc, b);
    col = mix(col, DIM_WASH, DIM_EMPTY * (1.0 - s.r));
    o = vec4(col, 1.0);
}
