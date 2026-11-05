// Blob debug — the Body plus every blob record (ADR-0022).
// iChannel0 = Body (Buffer A), iChannel1 = blobs.
//   dashed slate = tentative · ink = confirmed · orange, fading = coasting · rust = lost

const int   SLOTS = 8;
const vec3  PAPER = vec3(0.965, 0.945, 0.894), INK = vec3(0.067),
            SLATE = vec3(0.443, 0.604, 0.678), ORANGE = vec3(0.910, 0.525, 0.184),
            RUST  = vec3(0.737, 0.298, 0.149), DEEP = vec3(0.125, 0.463, 0.639);

vec4 blob(int slot, int row) { return texelFetch(iChannel1, ivec2(slot, row), 0); }

// Distance (px) from p to the border of the box lo–hi.
float border(vec2 p, vec2 lo, vec2 hi) {
    vec2 q = abs(p - (lo + hi) * 0.5) - (hi - lo) * 0.5;
    return abs(length(max(q, 0.0)) + min(max(q.x, q.y), 0.0));
}

float segment(vec2 p, vec2 a, vec2 b) {
    vec2 pa = p - a, ba = b - a;
    return length(pa - ba * clamp(dot(pa, ba) / max(dot(ba, ba), 1e-6), 0.0, 1.0));
}

void mainImage(out vec4 o, in vec2 fc) {
    vec2 uv  = fc / iResolution.xy;
    vec3 col = mix(PAPER, vec3(0.82), texture(iChannel0, uv).r);

    for (int s = 0; s < SLOTS; s++) {
        vec4  box = blob(s, 0), mot = blob(s, 1), idn = blob(s, 2);
        float state = idn.y;
        if (state < 0.5) continue;
        vec2 lo = box.xy * iResolution.xy, hi = box.zw * iResolution.xy;
        vec2 cc = mot.xy * iResolution.xy;

        vec3  ink   = state < 1.5 ? SLATE : state < 2.5 ? INK : state < 3.5 ? ORANGE : RUST;
        float alpha = state > 2.5 && state < 3.5 ? 1.0 - 0.6 * clamp(idn.z, 0.0, 1.0) : 1.0;
        float line  = 1.0 - smoothstep(1.0, 2.0, border(fc, lo, hi));
        if (state < 1.5) line *= step(mod(fc.x + fc.y, 10.0), 5.0);
        col = mix(col, ink, line * alpha);

        col = mix(col, DEEP, 1.0 - smoothstep(1.0, 2.0, segment(fc, cc, cc + mot.zw * iResolution.xy * 0.5)));
        col = mix(col, ink, (1.0 - smoothstep(2.5, 3.5, length(fc - cc))) * alpha);
    }
    o = vec4(col, 1.0);
}
