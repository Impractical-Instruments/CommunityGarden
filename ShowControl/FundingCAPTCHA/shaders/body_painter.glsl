// Body painter — paste into Shadertoy's Buffer A tab. Do not edit per Setup.
//
// Buffer A is the Body. On the show Pi this pass is replaced by the Orbbec
// depth silhouette; here the mouse stands in for a visitor.
//
//   Buffer A channels:  iChannel0 = Buffer A,  iChannel1 = Keyboard
//
// Output every Setup may read (sample with texture(), never texelFetch —
// on the Pi the Body is camera resolution, not screen resolution):
//   .r  presence  1 inside a person, 0 outside
//   .g  nearness  0 far … 1 close to the camera (0 where .r is 0)
//   .b .a reserved — painter state here, meaningless on the Pi
//
// Controls:
//   hold left mouse   a person stands at the cursor
//   hold Shift        that person steps close to the camera
//   Space             leave a person standing at the cursor (stays put)
//   C                 clear everyone

const int KEY_SHIFT = 16;
const int KEY_SPACE = 32;
const int KEY_C     = 67;

float key(int code, int row) { return texelFetch(iChannel1, ivec2(code, row), 0).x; }

// Front-on silhouette: a torso capsule plus a head, scaled by nearness.
float person(vec2 fc, vec2 at, float near) {
    vec2  p = (fc - at) / iResolution.y / mix(0.75, 1.4, near);
    vec2  a = vec2(0.0, -0.30), b = vec2(0.0, 0.10);
    float h = clamp(dot(p - a, b - a) / dot(b - a, b - a), 0.0, 1.0);
    float torso = length(p - a - h * (b - a)) - 0.075;
    float head  = length(p - vec2(0.0, 0.24)) - 0.06;
    return step(min(torso, head), 0.0);
}

void mainImage(out vec4 o, in vec2 fc) {
    vec4 prev = texture(iChannel0, fc / iResolution.xy);
    if (iFrame == 0 || key(KEY_C, 1) > 0.5) prev = vec4(0.0);

    float near = key(KEY_SHIFT, 0) > 0.5 ? 1.0 : 0.35;
    float live = iMouse.z > 0.0 ? person(fc, iMouse.xy, near) : 0.0;

    // Parked people live in .b (presence) and .a (nearness).
    vec2 parked = prev.ba;
    if (key(KEY_SPACE, 1) > 0.5 && person(fc, iMouse.xy, near) > 0.5)
        parked = vec2(1.0, near);

    float presence = max(live, parked.x);
    float nearness = max(live * near, parked.x * parked.y);
    o = vec4(presence, nearness, parked);
}
