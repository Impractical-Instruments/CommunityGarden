/**
 * Music Rhythm Game — grow-in-grid mechanic
 *
 * Grid: N×N (starts 2×2, grows to 4×4 over levels).
 * Each cell = a chromatic note (C4 upward).
 * Gems appear in cells and grow to fill them over beatMs.
 * Tap when gem fills its square → plays note, scores.
 * Miss window: gem grows past 125% unfilled → flash red, shrink, miss.
 * Win: complete the full song sequence.
 */
class RhythmGame {
  static get META() {
    return { id: 'rhythm', title: '🎵 Music Rhythm', cols: 2, rows: 2 };
  }

  static BASE_FREQ = 261.63; // C4 in Hz

  // 4 songs encoded as chromatic semitone offsets from C4 (0–15 = C4–D#5).
  // These fit on the 4×4 (16-note) grid; smaller grids remap proportionally.
  static SONGS = [
    {
      title: 'Seven Nation Army',
      // G G D5 G F D# C# — main riff, transposed to sit in upper half of grid
      notes: [7,7,14,7,5,3,1, 7,7,14,7,5,3,1, 5,3],
    },
    {
      title: 'Smoke on the Water',
      // G A Bb / G A C Bb / G A Bb A G
      notes: [7,9,10, 7,9,12,10, 7,9,10,9,7],
    },
    {
      title: 'Ode to Joy',
      // E E F G  G F E D  C C D E  E D D
      notes: [4,4,5,7, 7,5,4,2, 0,0,2,4, 4,2,2],
    },
    {
      title: 'Imperial March',
      // G G G Eb Bb G Eb Bb G / D5 D5 D5 Eb5 Bb G Eb Bb G
      notes: [7,7,7,3,10,7,3,10,7, 14,14,14,15,10,7,3,10,7],
    },
  ];

  static TUNING = {
    beatMs:       600,   // gem grow time at level 0 (ms)
    beatMsMin:    280,   // fastest
    beatMsStep:    30,   // reduction per level
    beatInterval: 0.85,  // fraction of beatMs between note spawns (< 1 = overlap)
    tolerance:    0.24,  // ±fraction of beatMs counted as valid tap (near progress=1)
    missAt:       1.28,  // gem disappears as miss at this progress
  };

  constructor(grid, hud, onWin, onLose) {
    this.grid       = grid;
    this.hud        = hud;
    this.onWin      = onWin;
    this.onLose     = onLose;
    this.level      = 0;
    this.alive      = false;
    this._destroyed = false;
    this.gems       = [];
    this.onGridResize = null; // wired by main.js

    this._audioCtx = null;
    this._initAudio();
    this._start();
  }

  // ── Derived level params ──────────────────────────────────────────────────────

  _gridDim() {
    return Math.min(4, 2 + Math.floor(this.level / 3));
  }

  _maxSim() {
    return Math.min(3, 1 + Math.floor(this.level / 3));
  }

  _beatMs() {
    return Math.max(RhythmGame.TUNING.beatMsMin,
      RhythmGame.TUNING.beatMs - this.level * RhythmGame.TUNING.beatMsStep);
  }

  _songIdx() { return this.level % RhythmGame.SONGS.length; }

  _semitoneToCell(semitone, gridCells) {
    return Math.round(semitone / 15 * (gridCells - 1));
  }

  // ── Audio ─────────────────────────────────────────────────────────────────────

  _initAudio() {
    try { this._audioCtx = new (window.AudioContext || window.webkitAudioContext)(); } catch (_) {}
  }

  async _playNote(semitone, dur = 0.22) {
    if (!this._audioCtx) return;
    try {
      const ctx  = this._audioCtx;
      if (ctx.state === 'suspended') await ctx.resume();
      const freq = RhythmGame.BASE_FREQ * Math.pow(2, semitone / 12);
      const osc  = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.type = 'triangle';
      osc.frequency.value = freq;
      gain.gain.setValueAtTime(0.4, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + dur);
      osc.start();
      osc.stop(ctx.currentTime + dur);
    } catch (_) {}
  }

  // ── Lifecycle ─────────────────────────────────────────────────────────────────

  _start() {
    const dim = this._gridDim();
    if (dim !== this.grid.cols || dim !== this.grid.rows) {
      this.grid.resize(dim, dim);
      this.onGridResize?.(dim, dim);
    }
    this._initRound();
  }

  _initRound() {
    this._clearGems();

    const song        = RhythmGame.SONGS[this._songIdx()];
    this.song         = song.notes;
    this.songTitle    = song.title;
    this.beatMs       = this._beatMs();
    this.gridDim      = this._gridDim();
    this.maxSim       = this._maxSim();
    this.beatInterval = this.beatMs * RhythmGame.TUNING.beatInterval / this.maxSim;
    this.songPos      = 0;
    this.nextNoteAt   = 0;     // ms from songStart
    this.songStart    = null;  // set on first RAF tick
    this.score        = 0;
    this.misses       = 0;
    this.alive        = true;

    this._renderCells();
    this._updateHud();
    this._startLoop();
  }

  _renderCells() {
    const { grid, gridDim } = this;
    const noteNames = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B'];
    const cells = gridDim * gridDim;
    for (let r = 0; r < gridDim; r++) {
      for (let c = 0; c < gridDim; c++) {
        const idx      = r * gridDim + c;
        const semitone = Math.round(idx / Math.max(1, cells - 1) * 15);
        const octave   = semitone >= 12 ? '5' : '4';
        const label    = noteNames[semitone % 12] + octave;
        const el = grid.cell(c, r);
        if (!el) continue;
        el.innerHTML  = `<span style="font-size:.6rem;color:var(--muted);position:absolute;bottom:3px;right:4px">${label}</span>`;
        el.className  = 'grid-cell';
      }
    }
  }

  _clearGems() {
    this.gems.forEach(g => g.el?.remove());
    this.gems = [];
  }

  _startLoop() {
    let last = performance.now();
    const loop = (now) => {
      if (!this.alive) return;
      if (this.songStart === null) this.songStart = now;
      last = now;

      const elapsed = now - this.songStart;

      // Spawn notes on schedule
      while (this.songPos < this.song.length && elapsed >= this.nextNoteAt) {
        const semitone = this.song[this.songPos++];
        const cell     = this._semitoneToCell(semitone, this.gridDim * this.gridDim);
        this._spawnGem(cell, semitone, now);
        this.nextNoteAt += this.beatInterval;
      }

      // Update gems
      let hudDirty = false;
      this.gems.forEach(g => {
        if (g.hit || g.missed) return;
        const progress = (now - g.spawnTime) / this.beatMs;

        if (progress >= RhythmGame.TUNING.missAt) {
          g.missed = true;
          this.misses++;
          hudDirty = true;
          this._animateMiss(g);
          return;
        }

        const scale = Math.min(1, progress);
        const hue   = 190 - progress * 30;
        const alpha = 0.15 + progress * 0.85;
        g.el.style.transform  = `scale(${scale.toFixed(3)})`;
        g.el.style.background = `hsla(${hue},75%,58%,${alpha.toFixed(2)})`;
        if (progress > 0.7) {
          const glow = Math.round((progress - 0.7) / 0.3 * 18);
          g.el.style.boxShadow = `0 0 ${glow}px 2px rgba(6,182,212,0.7)`;
        }
      });

      if (hudDirty) this._updateHud();

      // Song complete: all notes spawned and no pending gems
      if (this.songPos >= this.song.length) {
        const pending = this.gems.filter(g => !g.hit && !g.missed).length;
        if (pending === 0) {
          this._stop();
          setTimeout(() => this.onWin(), 400);
          return;
        }
      }

      this._rafId = requestAnimationFrame(loop);
    };

    this._rafId = requestAnimationFrame(loop);
  }

  _spawnGem(cellIdx, semitone, now) {
    const c = cellIdx % this.gridDim;
    const r = Math.floor(cellIdx / this.gridDim);
    const cellEl = this.grid.cell(c, r);
    if (!cellEl) return;

    const el = document.createElement('div');
    el.style.cssText = [
      'position:absolute',
      'inset:10%',
      'border-radius:50%',
      'background:rgba(6,182,212,0.15)',
      'transform:scale(0)',
      'pointer-events:none',
      'transition:box-shadow .08s',
    ].join(';');
    cellEl.appendChild(el);

    this.gems.push({ cellIdx, semitone, c, r, spawnTime: now, el, hit: false, missed: false });
  }

  _animateMiss(g) {
    const { el } = g;
    if (!el) return;
    el.style.transition = 'transform .35s ease-in, background .35s, opacity .35s';
    el.style.background = 'rgba(239,68,68,0.75)';
    el.style.transform  = 'scale(0)';
    el.style.opacity    = '0';
    this.grid.flash(g.c, g.r, 'note-miss', 400);
    setTimeout(() => el.remove(), 400);
  }

  _stop() {
    this.alive = false;
    cancelAnimationFrame(this._rafId);
    this._rafId = null;
  }

  _updateHud() {
    const total = this.song?.length ?? 0;
    const done  = this.score + this.misses;
    const pct   = total > 0 ? Math.round(done / total * 100) : 0;

    this.hud.innerHTML = `
      <div class="hud-box">
        <div class="hud-label">Song</div>
        <div style="font-size:.85rem;font-weight:600;margin-top:4px;line-height:1.3">${this.songTitle ?? ''}</div>
      </div>
      <div class="hud-box">
        <div class="hud-label">Notes</div>
        <div class="hud-value good">${this.score}</div>
        <div style="font-size:.75rem;color:var(--muted);margin-top:2px">${this.misses} missed</div>
        <div class="progress-bar" style="margin-top:6px">
          <div class="progress-bar-fill" style="width:${pct}%;background:var(--accent2)"></div>
        </div>
      </div>
      <div class="hud-box">
        <div class="hud-label">Level</div>
        <div class="hud-value">${this.level + 1}</div>
      </div>
      <div class="hud-box">
        <div class="hud-label">How to Play</div>
        <div style="font-size:.8rem;color:var(--muted);margin-top:4px;line-height:1.6">
          Tap when the<br>circle fills<br>the square!
        </div>
      </div>
    `;
  }

  onTap(col, row) {
    if (!this.alive) return;

    // Find active gem in this cell closest to progress = 1.0
    const now = performance.now();
    let best = null, bestDist = Infinity;
    this.gems.forEach(g => {
      if (g.c !== col || g.r !== row || g.hit || g.missed) return;
      const progress = (now - g.spawnTime) / this.beatMs;
      const dist = Math.abs(progress - 1.0);
      if (dist < bestDist) { bestDist = dist; best = g; }
    });

    if (best && bestDist < RhythmGame.TUNING.tolerance) {
      best.hit = true;
      this.score++;
      this._playNote(best.semitone);
      // Animate hit
      best.el.style.transition = 'transform .18s ease-out, background .18s, opacity .25s';
      best.el.style.background = 'rgba(34,197,94,0.75)';
      best.el.style.transform  = 'scale(1.08)';
      best.el.style.boxShadow  = '0 0 20px 4px rgba(34,197,94,0.6)';
      setTimeout(() => {
        best.el.style.transform = 'scale(0)';
        best.el.style.opacity   = '0';
        setTimeout(() => best.el?.remove(), 250);
      }, 180);
      this.grid.flash(col, row, 'note-hit', 380);
    } else {
      // Play the cell's note anyway for feedback
      const cellIdx   = row * this.gridDim + col;
      const semitone  = Math.round(cellIdx / Math.max(1, this.gridDim * this.gridDim - 1) * 15);
      this._playNote(semitone, 0.1);
      this.grid.flash(col, row, 'note-miss', 280);
    }

    this._updateHud();
  }

  destroy() {
    this._destroyed = true;
    this._stop();
    this._clearGems();
  }

  nextLevel() {
    this.level++;
    this._start();
  }
}
