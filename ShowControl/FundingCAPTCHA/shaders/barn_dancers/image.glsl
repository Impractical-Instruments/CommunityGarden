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
// Ridge lines waver like a line drawn by hand.
float wobble(float x)     { return 0.007 * (vnoise2(vec2(x * 14.0, 3.0)) - 0.5) + 0.003 * (vnoise2(vec2(x * 47.0, 9.0)) - 0.5); }
float ridgeFar(float x)   { return 0.50 + 0.045 * sin(x * 2.1 + 1.0) + 0.018 * sin(x * 5.3 + 0.4) + wobble(x); }
float ridgeNear(float x)  { return 0.41 + 0.035 * sin(x * 1.3 + 4.0) + 0.012 * sin(x * 4.1 + 2.0) + wobble(x + 5.0); }
float ridgeField(float x) { return 0.33 + 0.010 * sin(x * 3.0 + 0.7) + wobble(x + 11.0); }
// A hand-inked line at distance d: its weight swells and thins along x.
float inkLine(float d, float x, float px) { return pen(abs(d), INK_W * (0.6 + 0.8 * vnoise2(vec2(x * 9.0, 1.0))), px); }

// Short scratchy dashes, one in some cells of a staggered grid, like the barn's siding. 1 on a dash.
float dashes(vec2 p, vec2 cell, float density, float px) {
    vec2 g = p / cell;
    g.x += hash11(floor(g.y)) * 7.0;
    vec2 id = floor(g), f = fract(g) * cell;
    if (hash21(id) > density) return 0.0;
    float len = mix(0.25, 0.85, hash21(id + 3.1)), x0 = hash21(id + 7.7) * (1.0 - len);
    float y0 = 0.3 + 0.4 * hash21(id + 1.9), y1 = y0 + 0.2 * (hash21(id + 5.3) - 0.5);
    return pen(sdSegment(f, vec2(x0, y0) * cell, vec2(x0 + len, y1) * cell), cell.y * 0.2, px);
}
// Stray curls, like the hairs on the legs. 1 on a hair.
float curls(vec2 p, float cell, float density, float px) {
    vec2 id = floor(p / cell);
    if (hash21(id + 11.0) > density) return 0.0;
    vec2  v = p - (id + 0.3 + 0.4 * vec2(hash21(id + 1.3), hash21(id + 2.9))) * cell;
    float a = hash21(id + 9.1) * 6.2832;
    float gap = dot(v / max(length(v), 1e-6), vec2(cos(a), sin(a)));           // the ring is open on one side
    return pen(abs(length(v) - cell * mix(0.1, 0.2, hash21(id + 5.5))), cell * 0.04, px) * smoothstep(-0.3, 0.0, gap);
}

float cloud(vec2 p, vec2 c, float s) {
    p = (p - c) / s;
    float d = length(p * vec2(1.0, 1.6)) - 0.5;
    d = min(d, length(p - vec2(0.42, -0.06)) - 0.3);
    d = min(d, length(p - vec2(-0.45, -0.08)) - 0.26);
    return (max(d, -0.22 - p.y) + 0.05 * (vnoise2(p * 6.0 + c * 31.0) - 0.5)) * s;   // flat underside, lumpy edge
}
// A puddle at c, radii r: signed distance, with a ragged edge.
float puddle(vec2 p, vec2 c, vec2 r) {
    vec2 q = (p - c) / r;
    float k = length(q);
    return (k - 1.0 - 0.3 * (vnoise2(q * 2.0 + c * 17.0) - 0.5)) * k / max(length(q / r), 1e-6);
}

vec3 field(vec2 p, float aspect, float px) {
    // Sky: overcast and stained, with dirty clouds.
    vec3 col = mix(SKY_LOW, SKY_TOP, smoothstep(0.45, 1.0, p.y));
    col = mix(col, SKY_STAIN, 0.55 * smoothstep(0.45, 0.8, vnoise2(p * vec2(1.7, 3.5) + 2.0)));
    col = mix(col, SKY_TOP * 0.85, 0.5 * dashes(p, vec2(0.11, 0.016), 0.22, px));
    float span = aspect + 1.2, drift = iTime * 0.012;      // clouds wrap just off screen
    for (int i = 0; i < 3; i++) {
        vec3  k  = i == 0 ? vec3(0.3, 0.83, 0.26) : i == 1 ? vec3(1.2, 0.70, 0.18) : vec3(2.0, 0.90, 0.21);
        vec2  c  = vec2(mod(k.x + drift * (0.7 + 0.3 * float(i)), span) - 0.6, k.y);
        float cl = cloud(p, c, k.z);
        vec3  fill = mix(CLOUD_SHADE, CLOUD, smoothstep(-0.08, 0.06, (p.y - c.y) / k.z));
        fill = mix(fill, CLOUD_SHADE * 0.8, 0.6 * dashes(p - c, vec2(0.06, 0.012), 0.3, px));
        col = mix(col, fill, 1.0 - smoothstep(-px, px, cl));
        col = mix(col, INK, inkLine(cl, p.x + float(i), px));
    }

    // Hills: scrubby, scratched.
    float far = p.y - ridgeFar(p.x), near = p.y - ridgeNear(p.x), fld = p.y - ridgeField(p.x);
    vec3  hill = mix(HILL_FAR, SCRUB, 0.5 * dashes(p, vec2(0.07, 0.012), 0.35, px));
    col = mix(col, hill, 1.0 - smoothstep(-px, px, far));
    col = mix(col, INK, inkLine(far, p.x, px));
    hill = mix(HILL_NEAR, SCRUB, 0.6 * dashes(p + 3.0, vec2(0.09, 0.014), 0.45, px));
    hill = mix(hill, INK, 0.8 * curls(p, 0.035, 0.12, px));
    col = mix(col, hill, 1.0 - smoothstep(-px, px, near));
    col = mix(col, INK, inkLine(near, p.x + 3.0, px));

    // The yard: churned mud, puddles, ruts and stray hairs.
    vec3 mud = mix(MUD, MUD_DARK, smoothstep(0.35, 0.75, vnoise2(p * vec2(3.0, 9.0))));
    mud = mix(mud, MUD_LIGHT, 0.4 * smoothstep(0.05, 0.33, p.y));
    mud = mix(mud, MUD_DARK * 0.75, 0.8 * dashes(p, vec2(0.10, 0.014), 0.5, px));
    mud = mix(mud, MUD_LIGHT, 0.7 * dashes(p + 7.0, vec2(0.08, 0.011), 0.3, px));
    for (int i = 0; i < 4; i++) {
        vec4  k = i == 0 ? vec4(0.17, 0.105, 0.17, 0.022) : i == 1 ? vec4(0.63, 0.040, 0.21, 0.020)
                : i == 2 ? vec4(0.87, 0.175, 0.11, 0.013) : vec4(0.41, 0.235, 0.08, 0.009);
        vec2  c = vec2(k.x * aspect, k.y);
        float d = puddle(p, c, k.zw);
        vec3  water = mix(PUDDLE, PUDDLE_SHINE, pen(sdSegment(p, c + k.zw * vec2(-0.5, 0.25), c + k.zw * vec2(0.15, 0.3)), k.w * 0.22, px));
        mud = mix(mud, water, 1.0 - smoothstep(-px, px, d));
        mud = mix(mud, INK, 0.9 * inkLine(d * 1.4, p.x * 3.0 + float(i), px));
    }
    mud = mix(mud, INK, 0.85 * curls(p, 0.045, 0.3, px));
    mud = mix(mud, SCRUB, curls(p + 0.5, 0.03, 0.12, px));
    col = mix(col, mud, 1.0 - smoothstep(-px, px, fld));
    col = mix(col, INK, inkLine(fld, p.x + 7.0, px));

    // A crooked fence along the yard's far edge.
    float gx = p.x / 0.19, id = floor(gx);
    float cx = (id + 0.4 + 0.2 * hash11(id)) * 0.19, base = ridgeField(cx) - 0.012;
    vec2  top = vec2(cx + 0.03 * (hash11(id + 4.0) - 0.5), base + 0.055 + 0.02 * hash11(id + 8.0));
    float wire = p.y - ridgeField(p.x) - 0.034 + 0.009 * sin(3.14159 * fract(gx + 0.5)) ;
    col = mix(col, INK, pen(abs(wire), 0.003, px));
    float post = sdSegment(p, vec2(cx, base), top) - 0.010;
    col = mix(col, mix(POST, INK, smoothstep(-0.005 - px, -0.005, post)), 1.0 - smoothstep(-px, 0.0, post));

    // Grit over everything.
    col *= 1.0 - 0.10 * step(0.965, hash21(floor(p / 0.004)));
    return col * (0.93 + 0.14 * vnoise2(p * 5.0 + 40.0));
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
        col = mix(col, SHADE, 0.5 * up * (1.0 - smoothstep(0.7, 1.0, length(q))));
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
