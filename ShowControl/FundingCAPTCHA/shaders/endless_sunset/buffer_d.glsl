// Buffer D — Depth inside people.  iChannel0 = Buffer B (Body memory), iChannel1 = Buffer D (itself)
// .r distance in from the silhouette's edge, screen heights (0 outside), smoothed over a
//    few px — the concentric fill lines follow it, and their wiggle follows its slope
// .g the raw distance, but 1 (far) outside: what the depth grows from, so a pixel that was
//    outside last frame can't hold its neighbours down
// Grown from the edge inward: each pixel takes the smallest "neighbour's distance + step"
// around it. That settles to a true distance field and follows a moving body smoothly (no
// popping when the body changes shape). A value can only rise one step per frame, so deep
// inside only long steps are used.

// Last frame's .g at an integer offset: exact steps (no blending with "far" across the edge),
// so every "neighbour + step" really is at least the distance.
float grown(ivec2 at, vec2 off, float AA) {
    ivec2 o = ivec2(round(off));
    ivec2 p = clamp(at + o, ivec2(0), ivec2(iResolution.xy) - 1);
    return texelFetch(iChannel1, p, 0).g + length(vec2(o)) * AA;
}

void mainImage(out vec4 o, in vec2 fc) {
    vec2  px = 1.0 / iResolution.xy;
    vec2  uv = fc * px;
    ivec2 at = ivec2(fc);
    float AA = 1.0 / iResolution.y;

    // Presence smoothed over a small disc, so depth-dropout holes the hole fill misses don't
    // become edges (each would grow its own little ring of lines). The same taps give the
    // presence slope: for a ramp, sum(s_k * dir_k) = 4 * h * slope.
    float h = DEPTH_SMOOTH_PX;
    float soft = texture(iChannel0, uv).r, lo = soft;
    vec2  g = vec2(0.0);
    for (int k = 0; k < 8; k++) {
        vec2  dir = vec2(cos(0.7853982 * float(k)), sin(0.7853982 * float(k)));
        float s   = texture(iChannel0, uv + dir * h * px).r;
        soft += s;
        g    += s * dir;
        lo    = min(lo, s);
    }
    soft /= 9.0;
    g /= 4.0 * h * AA;                                      // per screen height
    if (soft < 0.5 || iFrame == 0) { o = vec4(0.0, 1.0, 0.0, 0.0); return; }

    // On the edge's ramp: read the distance straight off the slope (sub-pixel smooth). Only
    // where real outside is in reach: a dropout dimple has a slope too, but no outside.
    float gl = length(g);
    float d  = lo < 0.4 && gl * h * AA > 0.15 ? min((soft - 0.5) / gl, 2.0 * h * AA) : 1.0;

    // Further in, the nearest edge lies through some neighbour. Long steps in 16 directions
    // (round contours, within 2% of a circle) carry depth DEPTH_LEAP_PX per frame, so a body
    // that just arrived fills in within a camera frame or two.
    float leap = DEPTH_LEAP_PX * AA;
    for (int k = 0; k < 16; k++) {
        float a = 0.3926991 * float(k);
        d = min(d, grown(at, vec2(cos(a), sin(a)) * DEPTH_LEAP_PX, AA));
    }
    // Within a long step of the edge, short steps place the first lines precisely. Not
    // deeper: there they would hold stale low values back to one short step per frame.
    for (int k = 0; k < 12; k++) {
        float a = 0.5235988 * float(k);
        float c = grown(at, vec2(cos(a), sin(a)) * DEPTH_STEP_PX, AA);
        if (c < leap) d = min(d, c);
    }
    d = min(d, 1.0);

    // The raw distance jitters by a fraction of a px from texel to texel (the steps round to
    // whole texels); its slope would make the wiggle scratchy. Relax it toward its
    // neighbours' last smoothed values: over frames that's a small blur that stays put.
    // Only among neighbours that already had a depth: blending in a just-arrived arm's
    // blanks would stipple it.
    float nb = 0.0, known = 1.0;
    for (int k = 0; k < 4; k++) {
        ivec2 e = ivec2(k == 0 ? 2 : k == 1 ? -2 : 0, k == 2 ? 2 : k == 3 ? -2 : 0);
        vec2  v = texelFetch(iChannel1, clamp(at + e, ivec2(0), ivec2(iResolution.xy) - 1), 0).rg;
        nb += v.x;
        known *= step(v.y, 0.999);
    }
    float shown = d > 0.999 ? 0.0                           // the depth hasn't reached here yet: no lines
                            : mix(d, 0.25 * nb, DEPTH_RELAX * known);
    o = vec4(shown, d, 0.0, 0.0);
}
