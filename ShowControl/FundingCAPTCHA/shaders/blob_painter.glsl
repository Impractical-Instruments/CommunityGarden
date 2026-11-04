// Blob painter — Shadertoy stand-in for the "blobs" source. Do not edit per Setup.
//
// Paste into a spare buffer tab (D unless your Setup uses it) and bind that
// buffer wherever your Setup reads blobs. Don't copy this tab into the Setup
// folder: in setup.json write "blobs" where Shadertoy has that buffer.
//
//   This buffer's channels:  iChannel0 = this buffer,  iChannel1 = Keyboard
//
// It tracks the people body_painter.glsl draws, using the same controls: the
// person under the held mouse is slot 0; each Space press parks a person into
// the next free slot 1–7; C sends everyone to lost. On the show Pi the real
// tracker fills these records instead (ADR-0022).
//
// Records — read with texelFetch(iChannelN, ivec2(slot, row), 0), slot 0–7:
//   row 0  x0, y0, x1, y1          bounding box, Body UV (0–1, y up)
//   row 1  cx, cy, vx, vy          centroid (UV), velocity (UV per second)
//   row 2  id, state, age_s, near  id 1–999 · state 0 empty, 1 tentative,
//                                  2 confirmed, 3 coasting, 4 lost · seconds
//                                  in this state · nearness 0 far … 1 near
// Rows 3+ and columns 8+ are this painter's own state.

const int   SLOTS     = 8;
const float EMPTY     = 0.0, TENTATIVE = 1.0, CONFIRMED = 2.0, COASTING = 3.0, LOST = 4.0;
const float CONFIRM_S = 0.4;     // roughly the Pi's defaults at 10 fps
const float COAST_S   = 0.8;
const float LOST_S    = 1.0;

const int KEY_SHIFT = 16;
const int KEY_SPACE = 32;
const int KEY_C     = 67;

float key(int code, int row) { return texelFetch(iChannel1, ivec2(code, row), 0).x; }
vec4  rec(int slot, int row) { return texelFetch(iChannel0, ivec2(slot, row), 0); }

// Box of body_painter.glsl's person at `at` (pixels), in UV.
vec4 personBox(vec2 at, float near) {
    float s  = mix(0.75, 1.4, near) * iResolution.y;
    vec2  lo = at + vec2(-0.075, -0.375) * s;
    vec2  hi = at + vec2( 0.075,  0.285) * s;
    return clamp(vec4(lo, hi) / iResolution.xyxy, 0.0, 1.0);
}

void mainImage(out vec4 o, in vec2 fc) {
    ivec2 c = ivec2(fc);
    o = vec4(0.0);
    if (iFrame == 0 || c.y > 3 || c.x > SLOTS) return;

    bool  down  = iMouse.z > 0.0;
    bool  clear = key(KEY_C, 1) > 0.5;
    float near  = key(KEY_SHIFT, 0) > 0.5 ? 1.0 : 0.35;

    // Births this frame: the live person (new press, or held with an empty
    // slot 0), then a parked one into the first empty slot.
    bool liveBirth = down && !clear && (iMouse.w > 0.0 || rec(0, 2).y == EMPTY);
    int  parkSlot  = -1;
    if (key(KEY_SPACE, 1) > 0.5 && !clear)
        for (int k = 1; k < SLOTS; k++)
            if (rec(k, 2).y == EMPTY) { parkSlot = k; break; }
    float nextId = rec(SLOTS, 0).x;
    float liveId = nextId;
    float parkId = nextId + (liveBirth ? 1.0 : 0.0);

    if (c.x == SLOTS) {                 // id counter
        if (c.y == 0) o.x = nextId + (liveBirth ? 1.0 : 0.0) + (parkSlot >= 0 ? 1.0 : 0.0);
        return;
    }

    int   slot  = c.x;
    vec4  box   = rec(slot, 0), mot = rec(slot, 1), idn = rec(slot, 2);
    float state = idn.y, t0 = rec(slot, 3).x;
    float dt    = max(iTimeDelta, 1e-3);

    bool born = (slot == 0 && liveBirth) || slot == parkSlot;
    if (born) {
        box   = personBox(iMouse.xy, near);
        mot   = vec4((box.xy + box.zw) * 0.5, 0.0, 0.0);
        idn   = vec4(mod(slot == 0 ? liveId : parkId, 999.0) + 1.0, TENTATIVE, 0.0, near);
        state = TENTATIVE;
        t0    = iTime;
    } else if (slot == 0 && down && (state == TENTATIVE || state == CONFIRMED)) {
        box     = personBox(iMouse.xy, near);
        vec2 cc = (box.xy + box.zw) * 0.5;
        mot     = vec4(cc, mix(mot.zw, (cc - mot.xy) / dt, 0.3));
        idn.w   = near;
    } else if (slot == 0 && !down && state == TENTATIVE) {
        state = EMPTY;                  // never confirmed: gone without a trace
    } else if (slot == 0 && !down && state == CONFIRMED) {
        state = COASTING; t0 = iTime;
    }

    if (state == COASTING) {            // drift on the last velocity, slowing down
        box    += mot.zwzw * dt;
        mot.xy += mot.zw * dt;
        mot.zw *= exp(-2.0 * dt);
    }
    if (!born && clear && (state == CONFIRMED || state == COASTING)) { state = LOST; t0 = iTime; }
    if (!born && clear && state == TENTATIVE) state = EMPTY;

    float age = iTime - t0;
    if (state == TENTATIVE && age >= CONFIRM_S) { state = CONFIRMED; t0 = iTime; }
    if (state == COASTING  && age >= COAST_S)   { state = LOST;      t0 = iTime; mot.zw = vec2(0.0); }
    if (state == LOST      && age >= LOST_S)      state = EMPTY;
    if (state == EMPTY) return;

    idn.y = state;
    idn.z = iTime - t0;
    o = c.y == 0 ? box : c.y == 1 ? mot : c.y == 2 ? idn : vec4(t0, 0.0, 0.0, 0.0);
}
