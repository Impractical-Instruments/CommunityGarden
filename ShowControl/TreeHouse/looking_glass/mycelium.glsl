#version 330

uniform vec2 iResolution;
uniform float iTime;
uniform float iIntensity;

out vec4 fragColor;

float hash(vec2 p) {
    p = fract(p * vec2(127.1, 311.7));
    p += dot(p, p + 19.19);
    return fract(p.x * p.y);
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
    for (int i = 0; i < 5; i++) {
        v += a * noise(p);
        p = p * 2.1 + vec2(0.7, 1.3);
        a *= 0.5;
    }
    return v;
}

void main() {
    vec2 p = gl_FragCoord.xy / iResolution * 4.0;

    // Domain warp -> organic drape
    vec2 warp = vec2(
        fbm(p + iTime * 0.04),
        fbm(p + vec2(5.2, 1.3) + iTime * 0.04)
    );
    vec2 pw = p + 1.4 * warp;

    // Cellular veins via Voronoi distance
    vec2 ip = floor(pw);
    vec2 fp = fract(pw);
    float minDist = 1e6;

    for (int x = -1; x <= 1; x++) {
        for (int y = -1; y <= 1; y++) {
            vec2 off = vec2(x, y);
            float h1 = hash(ip + off);
            float h2 = hash(ip + off + 37.3);
            vec2 center = off + vec2(h1, h2);
            center += 0.25 * vec2(
                sin(iTime * 0.35 + h1 * 6.28),
                cos(iTime * 0.35 + h2 * 6.28)
            );
            minDist = min(minDist, length(fp - center));
        }
    }

    float vein = 1.0 - smoothstep(0.02, 0.09, minDist);
    vein += 0.25 * (1.0 - smoothstep(0.09, 0.22, minDist))
                 * (0.5 + 0.5 * sin(iTime * 0.6));

    float brightness = vein * (0.4 + iIntensity * 0.6);
    vec3 col = mix(vec3(0.02, 0.12, 0.04), vec3(0.55, 0.95, 0.25), vein) * brightness;
    fragColor = vec4(col, 1.0);
}
