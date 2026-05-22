#version 330

uniform vec2 iResolution;
uniform float iTime;
uniform float iIntensity;

out vec4 fragColor;

float hash(vec2 p) {
    return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

float noise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    f = f * f * (3.0 - 2.0 * f);
    return mix(
        mix(hash(i),           hash(i + vec2(1, 0)), f.x),
        mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), f.x),
        f.y
    );
}

float fbm(vec2 p) {
    float v = 0.0, a = 0.5;
    mat2 rot = mat2(0.8660, 0.5, -0.5, 0.8660);  // 30°
    for (int i = 0; i < 6; i++) {
        v += a * noise(p);
        p = rot * p * 2.1;
        a *= 0.5;
    }
    return v;
}

void main() {
    vec2 uv = (gl_FragCoord.xy * 2.0 - iResolution) / iResolution.y;
    vec2 p = uv * 1.4 + iTime * 0.018;

    // Triple-layered domain-warped nebula
    float n1 = fbm(p);
    float n2 = fbm(p + vec2(n1 * 1.8, n1 * 0.9) + iTime * 0.008);
    float n3 = fbm(p * 2.1 + vec2(n2) - iTime * 0.012);

    float nebula = n2 * n3;

    vec3 col = mix(vec3(0.04, 0.0, 0.10), vec3(0.0, 0.25, 0.55), n2);
    col = mix(col, vec3(0.75, 0.88, 1.0), nebula * 0.55);
    col += vec3(0.65, 0.28, 0.02) * n3 * n1 * 0.9;  // warm gas cloud fringe

    // Procedural starfield (UV-stable grid)
    vec2 sUV = gl_FragCoord.xy / iResolution;
    vec2 sCell = floor(sUV * 280.0);
    float s = hash(sCell);
    float twinkle = 0.65 + 0.35 * sin(iTime * (2.5 + s * 5.5) + s * 94.0);
    col += vec3(twinkle) * step(0.984, s) * 1.4;

    col *= 0.4 + iIntensity * 0.6;
    fragColor = vec4(col, 1.0);
}
