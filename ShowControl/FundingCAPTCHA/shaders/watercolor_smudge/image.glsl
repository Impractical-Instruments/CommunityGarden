// Image — the painting as seen. iChannel0 = D (canvas), iChannel1 = B (original), iChannel2 = "image".
// With an image bound, untouched areas sample it directly (no second resample through the canvas);
// smeared areas show the canvas with fresh paper grain and a wet sheen.

void mainImage(out vec4 o, in vec2 f) {
    vec2 uv = f / iResolution.xy;
    vec2 q  = uv * vec2(iResolution.x / iResolution.y, 1.0);
    vec4 cv = texture(iChannel0, uv);
    vec3 og = texture(iChannel1, uv).rgb;
    vec3 d  = abs(cv.rgb - og);
    float disturbed = max(smoothstep(DISTURB_LO, DISTURB_HI, max(d.r, max(d.g, d.b))), cv.a);
    vec3 smeared = cv.rgb * (1.0 - WET_DARKEN * cv.a) * paperGrain(q);
    vec3 col;
    if (iChannelResolution[2].x > 0.0) {
        vec3 im = texture(iChannel2, coverUV(uv, iResolution.xy, iChannelResolution[2].xy)).rgb;
        col = mix(im, smeared, disturbed);
    } else {
        col = smeared;                                    // procedural: grain everywhere, as the sketch
    }
    o = vec4(col, 1.0);
}
