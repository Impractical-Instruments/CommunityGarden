// Buffer B — logo state. iChannel0 = this buffer, iChannel1 = blobs.
// Layout: see common.glsl.

#define B     iChannel0
#define BLOBS iChannel1

vec4 rec(int k, int row) { return texelFetch(BLOBS, ivec2(k, row), 0); }

bool counts(float state) { return isState(state, S_CONFIRMED) || isState(state, S_COASTING); }

// LIFE for slot k this frame: reset when the slot empties or holds someone new.
vec4 lifeNext(int k, float dt) {
    vec4 idn = rec(k, 2), l = bLife(B, k);
    if (isState(idn.y, S_EMPTY)) return vec4(0.0);
    if (iFrame == 0 || abs(idn.x - l.x) > 0.5) l = vec4(idn.x, 0.0, 0.0, 0.0);
    if (counts(idn.y)) l.y = min(l.y + dt, LIFE_CAP);
    return l;
}

vec4 logoNext(float dt) {
    float aspect = iResolution.x / iResolution.y;
    vec2  home   = vec2(0.5 * aspect, 0.5);
    vec4  g      = bLogo(B);
    if (iFrame == 0) return vec4(home, 0.0, 0.0);

    // Everyone present, weighted by how long they've been here.
    float w = 0.0;
    vec2  sum = vec2(0.0);
    for (int k = 0; k < SLOTS; k++) {
        vec4 idn = rec(k, 2);
        if (!counts(idn.y)) continue;
        float wk = lifeNext(k, dt).y;
        sum += wk * rec(k, 1).xy * vec2(aspect, 1.0);   // centroid, Body UV → heights
        w   += wk;
    }
    vec2 target = home;
    if (w > 0.0) target = mix(home, sum / w, REACH * w / (w + PULL_HALF));
    float m = RADIUS * EDGE_IN;
    target = clamp(target, vec2(m), vec2(aspect - m, 1.0 - m));

    vec2 acc = SPRING * (target - g.xy) - DAMPING * g.zw;
    g.zw += acc * dt;
    float s = length(g.zw);
    if (s > SPEED_MAX) g.zw *= SPEED_MAX / s;
    g.xy += g.zw * dt;
    return g;
}

void mainImage(out vec4 o, in vec2 fc) {
    ivec2 c  = ivec2(fc);
    float dt = clamp(iTimeDelta, 0.0, DT_MAX);
    if      (c.y == 0 && c.x < SLOTS) o = lifeNext(c.x, dt);
    else if (c.y == 1 && c.x == 0)    o = logoNext(dt);
    else                              o = vec4(0.0);
}
