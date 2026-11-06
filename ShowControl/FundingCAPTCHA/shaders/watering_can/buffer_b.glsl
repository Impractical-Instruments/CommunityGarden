// Buffer B — Body memory.  iChannel0 = Buffer A (Body), iChannel1 = Buffer B (itself), iChannel2 = blobs
// .r presence · .g run bottom y (UV) · .b run top y (UV) · .a owner + 0.9 * hold
// A run is the vertical stretch of body through a pixel; a raised arm's run starts at its own lowest point.

float softPresence(vec2 uv) {
    vec2 t = BODY_BLUR_TEXELS / max(iChannelResolution[0].xy, vec2(1.0));
    float s = 0.0;
    for (int y = -1; y <= 1; y++)
        for (int x = -1; x <= 1; x++)
            s += texture(iChannel0, uv + vec2(x, y) * t).r;
    s /= 9.0;
    // Fill depth-dropout holes: a pixel ringed by body counts as body.
    vec2  h = HOLE_FILL_TEXELS / max(iChannelResolution[0].xy, vec2(1.0));
    float ring = 0.0;
    for (int k = 0; k < 8; k++) {
        float a = 0.7853982 * float(k);
        ring += texture(iChannel0, uv + vec2(cos(a), sin(a)) * h).r;
    }
    return max(s, smoothstep(0.45, 0.7, ring / 8.0));
}

// The slot whose live-or-not (non-empty) box contains uv; nearest centre wins. 0 = none.
int ownerAt(vec2 uv) {
    int best = 0;
    float bestD = 1e9;
    for (int k = 0; k < SLOTS; k++) {
        if (isState(recIdn(iChannel2, k).y, S_EMPTY)) continue;
        vec4 b = recBox(iChannel2, k);
        if (uv.x < b.x || uv.x > b.z || uv.y < b.y || uv.y > b.w) continue;
        float d = length(uv - 0.5 * (b.xy + b.zw));
        if (d < bestD) { bestD = d; best = k + 1; }
    }
    return best;
}

// How far the run extends from uv in direction dir (±1, in UV y) while previous presence stays on body.
float march(vec2 uv, float dir) {
    float y = uv.y;
    for (int i = 1; i <= RUN_STEPS; i++) {
        float ny = uv.y + dir * float(i) * RUN_STEP_H;
        if (ny < 0.0 || ny > 1.0) break;
        if (texture(iChannel1, vec2(uv.x, ny)).r < BODY_ON) break;
        y = ny;
    }
    return y;
}

void mainImage(out vec4 o, in vec2 fc) {
    vec2 uv = fc / iResolution.xy;
    vec4 prev = iFrame == 0 ? vec4(0.0) : texelFetch(iChannel1, ivec2(fc), 0);

    float target = softPresence(uv);
    float pres = iFrame == 0 ? target : mix(prev.r, target, 1.0 - exp(-iTimeDelta / PRESENCE_EASE_S));

    float g = 0.0, b = 0.0, a = 0.0;
    if (pres >= BODY_ON) {
        int own = ownerAt(uv);
        float lo = march(uv, -1.0), hi = march(uv, 1.0);
        bool had = prev.g > 0.0 || prev.b > 0.0;
        float ease = 1.0 - exp(-iTimeDelta / RUN_EASE_S);
        g = (!had || abs(lo - prev.g) > RUN_SNAP) ? lo : mix(prev.g, lo, ease);
        b = (!had || abs(hi - prev.b) > RUN_SNAP) ? hi : mix(prev.b, hi, ease);
        a = float(own) + 0.9;
    } else {
        int po = bOwner(prev);
        float ph = bHold(prev);
        if (po > 0 && ph > 0.0) {
            float st = recIdn(iChannel2, po - 1).y;
            // A missing body coasts first: keep its plants until the track is lost, then rewind them away.
            if (!isState(st, S_TENTATIVE) && !isState(st, S_CONFIRMED)) {
                float h = ph - iTimeDelta / LEAVE_S;
                if (h > 0.0) { g = prev.g; b = prev.b; a = float(po) + 0.9 * h; }
            }
        }
    }
    o = vec4(pres, g, b, a);
}
