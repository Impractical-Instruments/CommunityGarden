#version 330

uniform vec2 iResolution;
uniform float iTime;
uniform float iIntensity;

out vec4 fragColor;

void main() {
    vec2 uv = (gl_FragCoord.xy * 2.0 - iResolution) / iResolution.y;
    vec2 p = uv * 2.5;

    float brightness = 0.0;
    float scale = 1.0;

    for (int i = 0; i < 7; i++) {
        // Mirror-fold both axes
        p = abs(p) - 1.0;
        // Slow rotation per iteration
        float a = iTime * 0.07 + float(i) * 0.45;
        float ca = cos(a), sa = sin(a);
        p = vec2(ca * p.x - sa * p.y, sa * p.x + ca * p.y);
        // Scale toward attractor
        float s = 1.65 + 0.15 * sin(iTime * 0.25);
        p = p * s - vec2(0.45);
        scale *= s;
        brightness += exp(-dot(p, p) / (scale * scale) * 6.0)
                      * (0.4 + 0.6 * sin(float(i) * 1.1 + iTime * 0.4));
    }

    brightness = clamp(brightness, 0.0, 1.0);
    brightness *= 0.4 + iIntensity * 0.6;
    vec3 col = mix(vec3(0.05, 0.3, 0.05), vec3(0.9, 0.7, 0.1), brightness) * brightness;
    fragColor = vec4(col, 1.0);
}
