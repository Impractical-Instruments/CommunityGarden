/**
 * Music Rhythm Game
 *
 * Grid: 4 columns (notes C D E G) × 4 rows (octaves/instruments, only top row used as trigger lane).
 * A short melody scrolls as beat indicators. Player taps the correct column when the beat
 * indicator is in the trigger row. Correct = points, wrong = penalty.
 * Score ≥ WIN_SCORE wins; score ≤ 0 loses and resets.
 *
 * Uses the Web Audio API for sound.
 */
class RhythmGame {
  static get META() {
    return { id: 'rhythm', title: '🎵 Music Rhythm', cols: 4, rows: 5 };
  }

  constructor(grid, hud, onWin, onLose) {
    this.grid   = grid;
    this.hud    = hud;
    this.onWin  = onWin;
    this.onLose = onLose;
    this.alive  = true;

    this._audioCtx = null;
    this._initAudio();
    this._initSong();
    this._startLoop();
    this._renderStatic();
    this._updateHud();
  }

  _initAudio() {
    try {
      this._audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    } catch (e) { /* no audio */ }
  }

  _playNote(freq, dur = 0.18) {
    if (!this._audioCtx) return;
    try {
      const ctx = this._audioCtx;
      if (ctx.state === 'suspended') ctx.resume();
      const osc  = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.type = 'triangle';
      osc.frequency.value = freq;
      gain.gain.setValueAtTime(0.35, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + dur);
      osc.start();
      osc.stop(ctx.currentTime + dur);
    } catch (e) {}
  }

  // Column → note frequency mapping (C D E G)
  static NOTES  = [261.6, 293.7, 329.6, 392.0];
  static LABELS = ['C', 'D', 'E', 'G'];
  static EMOJIS = ['🎹', '🥁', '🎸', '🎺'];

  _initSong() {
    // Simple melody: each entry is column index (0-3) or -1 for rest
    // "Mary Had a Little Lamb" fragment in C D E G
    this.song = [
      2,1,0,1, 2,2,2,-1, 1,1,1,-1, 2,3,3,-1,
      2,1,0,1, 2,2,2, 2, 1,1,2,1,  0,-1,-1,-1,
    ];
    this.songPos    = 0;
    this.beatMs     = 420;
    this.tolerance  = 0.38; // fraction of beatMs for timing window
    this.score      = 0;
    this.WIN_SCORE  = 18;
    this.noteQueue  = []; // falling beats: { col, row, born }

    // Spawn initial queue
    for (let i = 0; i < 3; i++) this._spawnNext();
  }

  _spawnNext() {
    if (this.songPos >= this.song.length) return;
    const col = this.song[this.songPos++];
    this.noteQueue.push({ col, row: -1, born: performance.now(), advance: 0, rest: col < 0 });
  }

  _startLoop() {
    let last = performance.now();
    const ROWS = this.grid.rows;
    const TRIGGER_ROW = ROWS - 1;

    const tick = (now) => {
      if (!this.alive) return;
      const dt = now - last;
      last = now;

      // Advance notes
      this.noteQueue.forEach(n => { n.advance += dt; });

      // How far each note has traveled (0 → 1 over beatMs * rows)
      const rowTravelMs = this.beatMs * 0.85;
      this.noteQueue.forEach(n => {
        n.row = Math.floor((n.advance / rowTravelMs) * ROWS);
      });

      // Remove notes that passed the trigger row un-hit
      const toRemove = this.noteQueue.filter(n => n.row > TRIGGER_ROW && !n.hit);
      toRemove.forEach(n => {
        if (!n.rest && !n.penalised) {
          n.penalised = true;
          this.score = Math.max(0, this.score - 2);
          this._flashMiss(n.col);
        }
      });
      this.noteQueue = this.noteQueue.filter(n => n.row <= TRIGGER_ROW + 1);

      // Spawn next note when last one is far enough
      const last_note = this.noteQueue[this.noteQueue.length - 1];
      if (!last_note || last_note.advance > this.beatMs * 0.7) {
        this._spawnNext();
        if (this.songPos > this.song.length && this.noteQueue.length === 0) {
          // Song complete — check win
          if (this.score >= this.WIN_SCORE) {
            this._stop(); this.onWin(); return;
          } else {
            // Loop song
            this.songPos = 0;
            this._spawnNext();
          }
        }
      }

      this._renderNotes();
      this._updateHud();
      this._rafId = requestAnimationFrame(tick);
    };

    this._rafId = requestAnimationFrame(tick);
  }

  _stop() {
    this.alive = false;
    cancelAnimationFrame(this._rafId);
  }

  _flashMiss(col) {
    if (col < 0) return;
    this.grid.flash(col, this.grid.rows - 1, 'note-miss', 300);
  }

  _renderStatic() {
    // Label bottom row buttons
    for (let c = 0; c < this.grid.cols; c++) {
      this.grid.setContent(c, this.grid.rows - 1,
        `<span style="font-size:1.4rem">${RhythmGame.EMOJIS[c]}</span><span class="cell-label">${RhythmGame.LABELS[c]}</span>`
      );
      this.grid.addClass(c, this.grid.rows - 1, 'highlight');
    }
  }

  _renderNotes() {
    const ROWS = this.grid.rows;
    const TRIGGER_ROW = ROWS - 1;

    // Clear non-trigger rows
    for (let r = 0; r < TRIGGER_ROW; r++)
      for (let c = 0; c < this.grid.cols; c++) {
        this.grid.cell(c, r).innerHTML = '';
        this.grid.setClass(c, r, '');
      }

    // Draw falling notes
    this.noteQueue.forEach(n => {
      if (n.col < 0 || n.hit) return;
      const r = Math.max(0, Math.min(TRIGGER_ROW - 1, n.row));
      const nearTrigger = n.row >= TRIGGER_ROW - 1;
      const icon = nearTrigger ? '🟡' : '⚪';
      this.grid.setContent(n.col, r, icon);
      this.grid.addClass(n.col, r, nearTrigger ? 'warn' : 'dim');
    });
  }

  _updateHud() {
    const pct = Math.min(100, (this.score / this.WIN_SCORE) * 100);
    this.hud.innerHTML = `
      <div class="hud-box">
        <div class="hud-label">Score</div>
        <div class="hud-value ${this.score <= 2 ? 'bad' : this.score >= this.WIN_SCORE * .7 ? 'good' : ''}">${this.score}</div>
        <div class="progress-bar">
          <div class="progress-bar-fill" style="width:${pct}%; background:var(--accent2)"></div>
        </div>
      </div>
      <div class="hud-box">
        <div class="hud-label">Goal</div>
        <div class="hud-value">${this.WIN_SCORE}</div>
      </div>
      <div class="hud-box">
        <div class="hud-label">How to play</div>
        <div style="font-size:.8rem; color:var(--muted); margin-top:4px; line-height:1.5">
          Tap the column<br>when 🟡 reaches<br>the bottom row
        </div>
      </div>
    `;
  }

  onTap(col, row) {
    if (!this.alive) return;
    const TRIGGER_ROW = this.grid.rows - 1;

    // Only trigger-row taps count as note plays
    if (row !== TRIGGER_ROW) return;

    // Play the sound regardless
    this._playNote(RhythmGame.NOTES[col]);

    // Find the nearest note in this column that's in the tolerance window
    const rowTravelMs = this.grid.rows * this.grid.rows * 10; // same formula
    let best = null, bestDist = Infinity;

    this.noteQueue.forEach(n => {
      if (n.col !== col || n.hit || n.rest) return;
      const rowFrac = n.advance / (this.beatMs * 0.85);
      const distFromTrigger = Math.abs(rowFrac - 1.0);
      if (distFromTrigger < bestDist) { bestDist = distFromTrigger; best = n; }
    });

    if (best && bestDist < this.tolerance) {
      best.hit = true;
      this.score++;
      this.grid.flash(col, TRIGGER_ROW, 'note-hit', 350);
      if (this.score >= this.WIN_SCORE) {
        this._stop(); this.onWin(); return;
      }
    } else {
      this.score = Math.max(0, this.score - 1);
      this.grid.flash(col, TRIGGER_ROW, 'note-miss', 300);
      if (this.score === 0) {
        // reset song
        this.noteQueue = [];
        this.songPos = 0;
        this._spawnNext();
      }
    }
    this._updateHud();
  }

  destroy() { this._stop(); }

  nextLevel() {
    this.beatMs = Math.max(260, this.beatMs - 40);
    this.WIN_SCORE += 6;
    this.score = 0;
    this.noteQueue = [];
    this.songPos = 0;
    this._spawnNext();
    this.alive = true;
    this._startLoop();
    this._renderStatic();
    this._updateHud();
  }
}
