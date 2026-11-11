// Image — the field, visitors' faint silhouettes, and the barns.
// iChannel0 = Body (Buffer A), iChannel1 = dancer state (Buffer B),
// iChannel2 = the sprite sheet ("image"; unbound → barns are drawn in code).

#define BODY  iChannel0
#define B     iChannel1
#define SHEET iChannel2

// Everything is composited premultiplied: `src` over `dst`.
vec4 over(vec4 dst, vec4 src) { return src + dst * (1.0 - src.a); }

// ── Barn parts ────────────────────────────────────────────────────────────────
// Part i at q (rig units, standing pose) from the sprite sheet. `lod` picks
// between the sheet's full-, half- and quarter-size copies.
vec4 sheetPart(int i, vec2 q, float lod) {
    vec4 box = PART_BOX[i];
    if (any(lessThan(q, box.xy)) || any(greaterThan(q, box.zw))) return vec4(0.0);
    vec2 uv = mix(PART_UV[i].xy, PART_UV[i].zw, (q - box.xy) / (box.zw - box.xy));
    int  l0 = int(lod), l1 = min(l0 + 1, LODS - 1);
    return mix(textureLod(SHEET, LOD_RECT[l0].xy + uv * LOD_RECT[l0].zw, 0.0),
               textureLod(SHEET, LOD_RECT[l1].xy + uv * LOD_RECT[l1].zw, 0.0), fract(lod));
}

// The same parts drawn in code, for when there's no sprite sheet: flat fill, ink outline.
vec4 inked(float d, vec3 fill, float px) {
    float w = 0.022;
    return vec4(mix(fill, INK, smoothstep(-w - px, -w, d)), 1.0) * (1.0 - smoothstep(-px, 0.0, d));
}
float sdBox(vec2 p, vec2 c, vec2 half_) {
    vec2 q = abs(p - c) - half_;
    return length(max(q, 0.0)) + min(max(q.x, q.y), 0.0);
}
vec4 drawnPart(int i, vec2 q, float px) {
    if (i == P_BARN) {
        // Walls below, a round roof above; two square holes for the eyes.
        float d = min(sdBox(q, vec2(0.0, BODY_Y + 0.21), vec2(0.52, 0.21)),
                      max(length((q - vec2(0.0, BODY_Y + 0.42)) * vec2(1.0, 0.92)) - 0.55, BODY_Y + 0.40 - q.y));
        float eyes = min(sdBox(q, vec2(-0.241, 1.072), vec2(0.03)), sdBox(q, vec2(0.251, 1.066), vec2(0.03)));
        vec4  c = inked(d, BARN_RED, px);
        c.rgb = mix(c.rgb, TRIM * c.a, pen(abs(q.y - BODY_Y - 0.42), 0.02, px) * step(abs(q.x), 0.56));
        c.rgb = mix(c.rgb, TRIM * c.a, pen(abs(eyes - 0.012), 0.02, px));
        return c * smoothstep(0.0, px, eyes);
    }
    if (i == P_EYE_L || i == P_EYE_R) {                    // a white disc with a tall pupil
        vec2 c = i == P_EYE_L ? vec2(-0.241, 1.072) : vec2(0.251, 1.066);
        float pupil = length((q - c) * vec2(2.4, 1.0)) - 0.04;
        return vec4(mix(INK, TRIM, smoothstep(0.0, px, pupil)), 1.0) * (1.0 - smoothstep(-px, 0.0, length(q - c) - 0.09));
    }
    if (i == P_EYELID_L || i == P_EYELID_R) {              // a wall-coloured shutter, parked above its window
        vec2 c = i == P_EYELID_L ? vec2(-0.241, 1.166) : vec2(0.251, 1.160);
        return vec4(BARN_RED, 1.0) * (1.0 - smoothstep(-px, 0.0, sdBox(q, c, vec2(0.045, 0.05))));
    }
    int  leg = i >= P_THIGH_R ? 1 : 0, bone = i - (leg == 1 ? P_THIGH_R : P_THIGH_L);   // 0 thigh, 1 foot, 2 calf
    float side = leg == 1 ? 1.0 : -1.0;
    if (bone == 0) return inked(sdSegment(q, HIP[leg], KNEE[leg]) - 0.095, SKIN, px);
    if (bone == 2) return inked(sdSegment(q, KNEE[leg], ANKLE[leg]) - 0.07, SKIN, px);
    return inked(sdSegment(q, ANKLE[leg] - vec2(0.0, 0.07), ANKLE[leg] + vec2(-side * 0.14, -0.1)) - 0.05, SKIN, px);
}

// ── A barn ────────────────────────────────────────────────────────────────────
// The barn at p (rig units) in pose P, premultiplied. `px` is one pixel in rig units.
vec4 barn(vec2 p, Pose P, float px, float lod, bool sheet, vec3 tint) {
    vec4 c = vec4(0.0);
    #define PART(i, q) c = over(c, sheet ? sheetPart(i, q, lod) : drawnPart(i, q, px))
    // Behind the walls: eyes, then eyelids, seen through the window holes.
    vec2 qb = vec2(0.0, BODY_Y) + rot2(p - P.body, -P.lean);
    PART(P_EYE_L, qb - P.eye);
    PART(P_EYE_R, qb - P.eye);
    PART(P_EYELID_L, qb + vec2(0.0, LID_TRAVEL * P.lid));
    PART(P_EYELID_R, qb + vec2(0.0, LID_TRAVEL * P.lid));
    PART(P_BARN, qb);
    c.rgb *= tint;
    // In front: each leg's thigh, foot, then calf.
    for (int i = 0; i < 2; i++) {
        int t = i == 0 ? P_THIGH_L : P_THIGH_R;
        PART(t,     HIP[i]   + rot2(p - P.hip[i],   -P.thigh[i]));
        PART(t + 1, ANKLE[i] + rot2(p - P.ankle[i], -P.foot[i]));
        PART(t + 2, KNEE[i]  + rot2(p - P.knee[i],  -P.calf[i]));
    }
    #undef PART
    return c;
}

// ── The field ─────────────────────────────────────────────────────────────────
float ridgeFar(float x)  { return 0.50 + 0.045 * sin(x * 2.1 + 1.0) + 0.018 * sin(x * 5.3 + 0.4); }
float ridgeNear(float x) { return 0.41 + 0.035 * sin(x * 1.3 + 4.0) + 0.012 * sin(x * 4.1 + 2.0); }
float ridgeField(float x) { return 0.33 + 0.010 * sin(x * 3.0 + 0.7); }

float cloud(vec2 p, vec2 c, float s) {
    p = (p - c) / s;
    float d = length(p * vec2(1.0, 1.6)) - 0.5;
    d = min(d, length(p - vec2(0.42, -0.06)) - 0.3);
    d = min(d, length(p - vec2(-0.45, -0.08)) - 0.26);
    return max(d, -0.22 - p.y) * s;                        // flat underside
}

vec3 field(vec2 p, float aspect, float px) {
    vec3 col = mix(SKY_LOW, SKY_TOP, smoothstep(0.45, 1.0, p.y));
    float span = aspect + 1.2, drift = iTime * 0.012;      // clouds wrap just off screen
    float cl = min(cloud(p, vec2(mod(0.3 + drift, span) - 0.6, 0.83), 0.26),
               min(cloud(p, vec2(mod(1.2 + drift * 0.7, span) - 0.6, 0.70), 0.18),
                   cloud(p, vec2(mod(2.0 + drift * 1.3, span) - 0.6, 0.90), 0.21)));
    col = mix(col, CLOUD, 1.0 - smoothstep(-px, px, cl));

    float far = p.y - ridgeFar(p.x), near = p.y - ridgeNear(p.x), fld = p.y - ridgeField(p.x);
    col = mix(col, HILL_FAR, 1.0 - smoothstep(-px, px, far));
    col = mix(col, INK, pen(abs(far), INK_W, px));
    col = mix(col, HILL_NEAR, 1.0 - smoothstep(-px, px, near));
    col = mix(col, INK, pen(abs(near), INK_W, px));
    // Crop rows fanning out from the horizon.
    float row = (p.x - aspect * 0.5) / (0.62 - p.y);
    vec3  ground = mix(FIELD, FIELD_ROW, smoothstep(0.35, 0.65, abs(fract(row * 3.0) - 0.5) * 2.0));
    col = mix(col, ground, 1.0 - smoothstep(-px, px, fld));
    col = mix(col, INK, pen(abs(fld), INK_W, px));
    return col;
}

// ── Dancers ───────────────────────────────────────────────────────────────────
// Where slot k's barn stands and how big it is: xy = the ground under it
// (screen heights), z = one rig unit in screen heights.
vec3 standing(vec4 d, float aspect) {
    return vec3(d.x * aspect, mix(GROUND_FAR, GROUND_NEAR, d.y), BARN_H * mix(SIZE_FAR, SIZE_NEAR, d.y));
}
// How far out of the ground the barn is, 0 (hidden) to 1 (and a little over, as it pops).
float risen(vec4 s) {
    return easeOutBack(s.x) * (1.0 - smoothstep(BOW_END, 1.0, s.y));
}

void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    float aspect = iResolution.x / iResolution.y, px = 1.0 / iResolution.y;
    vec2  p = fragCoord * px;
    vec3  col = field(p, aspect, px);

    // Visitors: a faint shade over the scene, behind the barns.
    float body = smoothstep(0.35, 0.65, texture(BODY, fragCoord / iResolution.xy).r);
    col = mix(col, SHADE, SIL_ALPHA * body);

    // Shadows on the ground, under every barn.
    for (int k = 0; k < SLOTS; k++) {
        vec4 d = bDancer(B, k);
        if (d.w < 0.5) continue;
        vec3  at = standing(d, aspect);
        float up = clamp(risen(bStage(B, k)), 0.0, 1.0);
        vec2  q  = (p - at.xy - vec2(0.0, 0.035 * at.z)) / (at.z * vec2(0.62, 0.06));
        col = mix(col, SHADE, 0.3 * up * (1.0 - smoothstep(0.7, 1.0, length(q))));
    }

    bool  sheet = iChannelResolution[2].x > 0.0;
    float phase = bBeat(B).x;
    for (int r = 0; r < SLOTS; r++) {
        int  k = bOrder(B, r);
        vec4 d = bDancer(B, k);
        if (d.w < 0.5) continue;
        vec4  s  = bStage(B, k);
        vec3  at = standing(d, aspect);
        vec2  q  = (p - at.xy) / at.z;                     // rig units; the ground is y = 0
        if (abs(q.x) > 1.5 || q.y < -0.12 || q.y > 1.8) continue;

        float up   = risen(s);
        float seed = hash11(d.w);
        float qpx  = px / at.z;
        if (q.y > 0.0 && up > 0.0) {                       // below the ground line the field hides it
            float flip   = seed < 0.5 ? 1.0 : -1.0;        // half the troupe is mirrored: they kick the other way
            float bow    = smoothstep(0.0, BOW_END * 0.7, s.y);
            float travel = clamp(-s.z * TRAVEL_LEAN, -TRAVEL_LEAN_MAX, TRAVEL_LEAN_MAX) * flip;
            float blink  = 1.0 - smoothstep(0.0, BLINK_S * 0.5, abs(mod(iTime + seed * 9.0, BLINK_EVERY_S + seed) - BLINK_S * 0.5));
            Pose  P = dancePose(phase, mix(AMP_MIN, 1.0, d.z) * clamp(s.x * 2.0 - 1.0, 0.0, 1.0), bow, travel, blink);
            float lod = sheet ? clamp(log2(SHEET_UNIT * iChannelResolution[2].y * qpx), 0.0, float(LODS - 1)) : 0.0;
            vec3  tint = mix(vec3(1.0), 0.9 + 0.2 * vec3(hash11(seed + 1.0), hash11(seed + 2.0), hash11(seed + 3.0)), 0.6);
            float sunk = up < 1.0 ? (1.0 - up) * SINK_DEPTH : (1.0 - up) * POP_HOP;   // past 1 it hops clear of the ground
            vec4  c = barn(vec2(q.x * flip, q.y + sunk), P, qpx, lod, sheet, tint);
            col = col * (1.0 - c.a) + c.rgb;
        }
        // Dirt it pushes up while breaking through, in front of it.
        float digging = sin(3.14159 * clamp(up, 0.0, 1.0));
        if (digging > 0.01) {
            float m = length(q / vec2(0.62, 0.11) / mix(0.6, 1.0, digging)) - 1.0;
            vec4  c = inked(m * 0.11, DIRT, qpx) * step(-0.02, q.y);
            col = col * (1.0 - c.a) + c.rgb;
        }
    }
    fragColor = vec4(col, 1.0);
}
