// Buffer B — the original painting the canvas heals toward.
// iChannel0 = B (itself), iChannel1 = "image" (unbound → resolution 0 → procedural sunset).
// rgb = painting, a = smearable (1) vs. unpainted paper border (0).

void mainImage(out vec4 o, in vec2 f) {
    vec2 uv = f / iResolution.xy;
    if (iChannelResolution[1].x > 0.0) {
        o = vec4(texture(iChannel1, coverUV(uv, iResolution.xy, iChannelResolution[1].xy)).rgb, 1.0);
        return;
    }
    // Paint once; repaint if the buffer was reallocated (a Shadertoy resize clears it).
    vec3 ctr = texelFetch(iChannel0, ivec2(iResolution.xy * 0.5), 0).rgb;
    if (iFrame == 0 || ctr == vec3(0.0)) {
        o = vec4(paintSunset(uv, iResolution.xy), paintMask(uv, iResolution.xy));
    } else {
        o = texelFetch(iChannel0, ivec2(f), 0);
    }
}
