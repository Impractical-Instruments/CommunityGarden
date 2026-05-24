#version 330

uniform vec2 iResolution;
uniform float iTime;
uniform float iIntensity;

out vec4 fragColor;

void main() {
    vec2 uv = (gl_FragCoord.xy * 2.0 - iResolution) / iResolution;

    float r = length(uv);
    float a = atan(uv.y, uv.x);

    // Six spiral arms rotating over time
    float spiral = sin(6.0 * a - r * 10.0 + iTime * 1.2);

    // Radial rings pulsing outward
    float rings = sin(r * 14.0 - iTime * 2.0) * 0.5 + 0.5;

    // Fade at dead centre only; outer edge beyond screen corners (~1.41)
    float vignette = smoothstep(0.0, 0.15, r) * (1.0 - smoothstep(1.3, 1.6, r));

    float brightness = max(0.0, spiral * rings * vignette);
    brightness *= 0.4 + iIntensity * 0.6;

    // Bright gold background, warm highlights on animation
    vec3 col = mix(vec3(0.85, 0.65, 0.0), vec3(0.9, 0.0, 0.8), brightness);

    fragColor = vec4(col, 1.0);
}
