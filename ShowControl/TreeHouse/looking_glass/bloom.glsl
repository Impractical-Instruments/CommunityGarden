#version 330

uniform vec2 iResolution;
uniform float iTime;
uniform float iIntensity;

out vec4 fragColor;

void main() {
    vec2 uv = (gl_FragCoord.xy * 2.0 - iResolution) / iResolution.y;

    float r = length(uv);
    float a = atan(uv.y, uv.x);

    // Six spiral arms rotating over time
    float spiral = sin(6.0 * a - r * 10.0 + iTime * 1.2);

    // Radial rings pulsing outward
    float rings = sin(r * 14.0 - iTime * 2.0) * 0.5 + 0.5;

    // Fade at dead centre and hard edge
    float vignette = smoothstep(0.0, 0.15, r) * (1.0 - smoothstep(0.5, 0.85, r));

    float brightness = max(0.0, spiral * rings * vignette);
    brightness *= 0.4 + iIntensity * 0.6;

    // Deep green → warm gold driven by brightness
    vec3 col = mix(vec3(0.05, 0.3, 0.05), vec3(0.9, 0.7, 0.1), brightness) * brightness;

    fragColor = vec4(col, 1.0);
}
