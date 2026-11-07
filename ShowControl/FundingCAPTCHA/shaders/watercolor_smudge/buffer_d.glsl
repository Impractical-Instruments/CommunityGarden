// Buffer D — the canvas: rgb = paint, a = wetness 0–1.
// iChannel0 = D (itself), iChannel1 = B (original, this frame), iChannel2 = C (motion, this frame).

void mainImage(out vec4 o, in vec2 f) {
    vec3 ctr = texelFetch(iChannel0, ivec2(iResolution.xy * 0.5), 0).rgb;
    if (iFrame == 0 || ctr == vec3(0.0)) {
        o = vec4(texelFetch(iChannel1, ivec2(f), 0).rgb, 0.0);
        return;
    }
    o = texelFetch(iChannel0, ivec2(f), 0);
}
