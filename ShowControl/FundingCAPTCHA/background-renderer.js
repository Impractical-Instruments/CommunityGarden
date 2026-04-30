/**
 * Background shader renderer — a WebGL canvas that sits behind the DOM game grid.
 * Each game gets its own ambient GLSL fragment shader that reacts to game state.
 *
 * Usage (automatically instantiated at bottom of this file):
 *   backgroundRenderer.update({ game, event, score, winScore, timerFraction });
 *
 * `event` can be 'tap', 'win', or 'lose' — triggers a brightness spike that decays.
 */

// ── GLSL shaders ──────────────────────────────────────────────────────────────

const _VERT = `
attribute vec2 aPos;
varying vec2 vUv;
void main() {
  vUv = aPos * 0.5 + 0.5;
  gl_Position = vec4(aPos, 0.0, 1.0);
}`;

// Lobby — soft flowing violet gradient
const _FRAG_LOBBY = `
precision mediump float;
varying vec2 vUv;
uniform float uTime;
uniform float uEvent;
uniform float uIntensity;
void main() {
  float t = uTime * 0.25;
  vec3 col = vec3(0.03, 0.02, 0.08);
  col += vec3(0.05, 0.02, 0.13) * (sin(vUv.x * 3.14159 + t)       * 0.5 + 0.5);
  col += vec3(0.03, 0.04, 0.10) * (cos(vUv.y * 2.0    + t * 0.73) * 0.5 + 0.5);
  col += vec3(0.18, 0.07, 0.35) * uEvent * 0.7;
  gl_FragColor = vec4(col, 1.0);
}`;

// Keepaway — football field with ripple ring on events
const _FRAG_KEEPAWAY = `
precision mediump float;
varying vec2 vUv;
uniform float uTime;
uniform float uEvent;
uniform float uIntensity;
void main() {
  // Alternating grass stripes
  float stripe = mod(floor(vUv.y * 7.0), 2.0);
  vec3 col = mix(vec3(0.07, 0.21, 0.06), vec3(0.06, 0.18, 0.05), stripe);
  // Subtle yard-line marks
  float mark = smoothstep(0.025, 0.0, abs(fract(vUv.y * 7.0) - 0.5));
  col = mix(col, vec3(0.9, 0.9, 0.9), mark * 0.12);
  // Expanding ring on tap/win
  float dist = length(vUv - 0.5);
  float ring = smoothstep(0.018, 0.0, abs(dist - mod(uTime * 1.1, 0.75))) * uEvent;
  col += vec3(1.0, 0.82, 0.15) * ring * 0.9;
  col *= 0.52 + uIntensity * 0.18;
  gl_FragColor = vec4(col, 1.0);
}`;

// Rhythm — four column bands with scrolling audio waveform
const _FRAG_RHYTHM = `
precision mediump float;
varying vec2 vUv;
uniform float uTime;
uniform float uEvent;
uniform float uIntensity;
void main() {
  float colIdx = floor(vUv.x * 4.0);
  float colFrac = fract(vUv.x * 4.0);
  float phase = colIdx * 1.5708;
  // Vertical wave
  float wave = sin(vUv.y * 22.0 - uTime * 5.0 + phase) * 0.5 + 0.5;
  wave *= 0.14;
  // Column separator
  float sep = smoothstep(0.06, 0.0, min(colFrac, 1.0 - colFrac));
  vec3 col = vec3(0.02, 0.04, 0.13);
  col += vec3(0.0, 0.09, 0.28) * wave;
  col += vec3(0.06, 0.0, 0.12) * sep;
  col += col * uIntensity * 0.65;
  col += vec3(0.12, 0.42, 1.0) * uEvent * 0.45;
  gl_FragColor = vec4(col, 1.0);
}`;

// Upside Down — slow purple vortex; urgency increases as timer runs low
const _FRAG_UPSIDEDOWN = `
precision mediump float;
varying vec2 vUv;
uniform float uTime;
uniform float uEvent;
uniform float uIntensity;
void main() {
  vec2 uv = vUv - 0.5;
  float angle  = atan(uv.y, uv.x);
  float radius = length(uv);
  float spiral = sin(angle * 4.0 - uTime * 1.6 - radius * 10.0) * 0.5 + 0.5;
  vec3 inner = vec3(0.04, 0.0, 0.10);
  vec3 outer = vec3(0.13, 0.03, 0.30);
  vec3 col = mix(inner, outer, radius * 1.8) * (0.48 + spiral * 0.52);
  // Red urgency as timer drains
  col = mix(col, vec3(0.28, 0.0, 0.38), uIntensity * 0.55);
  col += vec3(0.45, 0.0, 0.65) * uEvent * 0.55;
  gl_FragColor = vec4(col, 1.0);
}`;

// ── Renderer class ─────────────────────────────────────────────────────────────

class BackgroundRenderer {
  constructor(canvas) {
    this._canvas = canvas;
    this._gl = canvas.getContext('webgl');
    if (!this._gl) {
      console.warn('BackgroundRenderer: WebGL not available, background disabled');
      this._dead = true;
      return;
    }
    this._dead       = false;
    this._uTime      = 0;
    this._uEvent     = 0;    // decays to 0
    this._intensity  = 0.3;
    this._progId     = 'lobby';
    this._lastTs     = 0;

    this._progs = {};
    this._quadBuf = null;
    this._initGL();
    this._resize();

    this._rafId = requestAnimationFrame(ts => this._tick(ts));
    window.addEventListener('resize', () => this._resize());
  }

  _initGL() {
    const gl = this._gl;

    // Fullscreen quad (2 triangles)
    const verts = new Float32Array([-1,-1, 1,-1, -1,1, -1,1, 1,-1, 1,1]);
    this._quadBuf = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, this._quadBuf);
    gl.bufferData(gl.ARRAY_BUFFER, verts, gl.STATIC_DRAW);

    const pairs = [
      ['lobby',      _FRAG_LOBBY],
      ['keepaway',   _FRAG_KEEPAWAY],
      ['rhythm',     _FRAG_RHYTHM],
      ['upsidedown', _FRAG_UPSIDEDOWN],
    ];
    for (const [id, frag] of pairs) {
      this._progs[id] = this._compile(gl, _VERT, frag);
    }
  }

  _compile(gl, vsrc, fsrc) {
    const compile = (type, src) => {
      const sh = gl.createShader(type);
      gl.shaderSource(sh, src);
      gl.compileShader(sh);
      if (!gl.getShaderParameter(sh, gl.COMPILE_STATUS)) {
        console.error('Shader error:', gl.getShaderInfoLog(sh));
        return null;
      }
      return sh;
    };
    const vs = compile(gl.VERTEX_SHADER,   vsrc);
    const fs = compile(gl.FRAGMENT_SHADER, fsrc);
    if (!vs || !fs) return null;

    const prog = gl.createProgram();
    gl.attachShader(prog, vs);
    gl.attachShader(prog, fs);
    gl.linkProgram(prog);
    gl.deleteShader(vs);
    gl.deleteShader(fs);
    if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) {
      console.error('Link error:', gl.getProgramInfoLog(prog));
      return null;
    }
    return {
      prog,
      aPos:       gl.getAttribLocation(prog,  'aPos'),
      uTime:      gl.getUniformLocation(prog,  'uTime'),
      uEvent:     gl.getUniformLocation(prog,  'uEvent'),
      uIntensity: gl.getUniformLocation(prog,  'uIntensity'),
    };
  }

  _resize() {
    const w = window.innerWidth, h = window.innerHeight;
    this._canvas.width  = w;
    this._canvas.height = h;
    if (!this._dead) this._gl.viewport(0, 0, w, h);
  }

  _tick(ts) {
    if (this._dead) return;
    const dt = this._lastTs ? (ts - this._lastTs) / 1000 : 0;
    this._lastTs = ts;
    this._uTime += dt;
    this._uEvent = Math.max(0, this._uEvent - dt * 2.2); // ~0.45s decay

    const p = this._progs[this._progId] || this._progs['lobby'];
    if (p) {
      const gl = this._gl;
      gl.useProgram(p.prog);
      gl.bindBuffer(gl.ARRAY_BUFFER, this._quadBuf);
      gl.enableVertexAttribArray(p.aPos);
      gl.vertexAttribPointer(p.aPos, 2, gl.FLOAT, false, 0, 0);
      gl.uniform1f(p.uTime,      this._uTime);
      gl.uniform1f(p.uEvent,     this._uEvent);
      gl.uniform1f(p.uIntensity, this._intensity);
      gl.drawArrays(gl.TRIANGLES, 0, 6);
    }

    this._rafId = requestAnimationFrame(ts => this._tick(ts));
  }

  /**
   * Called from main.js whenever game state changes.
   * @param {object} opts
   * @param {string}  opts.game          'keepaway'|'rhythm'|'upsidedown'|null (lobby)
   * @param {string}  opts.event         'tap'|'win'|'lose'|null
   * @param {number}  opts.score         current score (rhythm)
   * @param {number}  opts.winScore      target score (rhythm)
   * @param {number}  opts.timerFraction remaining time 0→1 (upsidedown)
   */
  update({ game = null, event = null, score = 0, winScore = 1, timerFraction = 1 } = {}) {
    if (this._dead) return;
    this._progId = game || 'lobby';

    if (event === 'win')  this._uEvent = 1.0;
    else if (event === 'lose') this._uEvent = 0.8;
    else if (event === 'tap')  this._uEvent = Math.min(1.0, this._uEvent + 0.6);

    if (game === 'rhythm') {
      this._intensity = winScore > 0 ? Math.min(1, score / winScore) : 0;
    } else if (game === 'upsidedown') {
      this._intensity = 1.0 - Math.max(0, Math.min(1, timerFraction));
    } else {
      this._intensity = 0.3;
    }
  }

  destroy() {
    this._dead = true;
    cancelAnimationFrame(this._rafId);
  }
}

// Auto-instantiate — canvas is added to index.html before this script loads
const backgroundRenderer = new BackgroundRenderer(
  document.getElementById('bg-canvas')
);
