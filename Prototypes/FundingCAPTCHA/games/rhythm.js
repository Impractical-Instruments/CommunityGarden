/**
 * Music Rhythm Game
 *
 * Grid: 4 columns (notes C D E G) × 5 rows.
 * Notes fall from the top; tap the correct column when the indicator
 * hits the bottom trigger row. Correct = points, wrong = penalty.
 * Score ≥ WIN_SCORE wins; hitting 0 resets the song.
 *
 * If photos are uploaded via upload.html, each column gets one kid's face.
 * Falling notes show a circular crop of that face; the closer to the
 * trigger row, the brighter the glow ring.
 */
class RhythmGame {
  static get META() {
    return { id: 'rhythm', title: '🎵 Music Rhythm', cols: 4, rows: 5 };
  }

  static NOTES  = [261.6, 293.7, 329.6, 392.0]; // C D E G
  static LABELS = ['C', 'D', 'E', 'G'];
  static EMOJIS = ['🎹', '🥁', '🎸', '🎺'];

  constructor(grid, hud, onWin, onLose) {
    this.grid         = grid;
    this.hud          = hud;
    this.onWin        = onWin;
    this.onLose       = onLose;
    this.alive        = false; // set true after async init
    this.columnPhotos = null;  // array of 4 urls, or null
    this._destroyed   = false;

    this._audioCtx = null;
    this._initAudio();
    this._loadPhotosAndInit();
  }

  async _loadPhotosAndInit() {
    try {
      const res    = await fetch('/api/photos');
      const photos = await res.json();
      if (Array.isArray(photos) && photos.length > 0) {
        const shuffled = [...photos].sort(() => Math.random() - .5);
        // Assign one photo per column, cycling if fewer than 4 uploaded
        this.columnPhotos = Array.from({ length: this.grid.cols },
          (_, i) => shuffled[i % shuffled.length].url);
      }
    } catch (_) { /* no server / no photos — emoji fallback */ }
    if (!this._destroyed) this._start();
  }

  _start() {
    this.alive = true;
    this._initSong();
    this._startLoop();
    this._renderStatic();
    this._updateHud();
  }

  _initAudio() {
    try {
      this._audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    } catch (e) {}
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

  _initSong() {
    // "Mary Had a Little Lamb" in columns 0-3 (C D E G), -1 = rest
    this.song = [
      2,1,0,1, 2,2,2,-1, 1,1,1,-1, 2,3,3,-1,
      2,1,0,1, 2,2,2, 2, 1,1,2,1,  0,-1,-1,-1,
    ];
    this.songPos   = 0;
    this.beatMs    = 420;
    this.tolerance = 0.38;
    this.score     = 0;
    this.WIN_SCORE = 18;
    this.noteQueue = [];
    for (let i = 0; i < 3; i++) this._spawnNext();
  }

  _spawnNext() {
    if (this.songPos >= this.song.length) return;
    const col = this.song[this.songPos++];
    this.noteQueue.push({ col, row: -1, advance: 0, rest: col < 0 });
  }

  _startLoop() {
    let last = performance.now();
    const ROWS        = this.grid.rows;
    const TRIGGER_ROW = ROWS - 1;

    const tick = (now) => {
      if (!this.alive) return;
      const dt = now - last;
      last = now;

      this.noteQueue.forEach(n => { n.advance += dt; });

      const rowTravelMs = this.beatMs * 0.85;
      this.noteQueue.forEach(n => {
        n.row = Math.floor((n.advance / rowTravelMs) * ROWS);
      });

      const toRemove = this.noteQueue.filter(n => n.row > TRIGGER_ROW && !n.hit);
      toRemove.forEach(n => {
        if (!n.rest && !n.penalised) {
          n.penalised = true;
          this.score = Math.max(0, this.score - 2);
          this._flashMiss(n.col);
        }
      });
      this.noteQueue = this.noteQueue.filter(n => n.row <= TRIGGER_ROW + 1);

      const lastNote = this.noteQueue[this.noteQueue.length - 1];
      if (!lastNote || lastNote.advance > this.beatMs * 0.7) {
        this._spawnNext();
        if (this.songPos > this.song.length && this.noteQueue.length === 0) {
          if (this.score >= this.WIN_SCORE) { this._stop(); this.onWin(); return; }
          else { this.songPos = 0; this._spawnNext(); }
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

  // Build the HTML for one column's icon in the trigger row
  _columnIconHTML(col) {
    const photo = this.columnPhotos?.[col];
    if (photo) {
      return `<img src="${photo}" style="width:76%;height:76%;object-fit:cover;border-radius:50%;">
              <span class="cell-label">${RhythmGame.LABELS[col]}</span>`;
    }
    return `<span style="font-size:1.4rem">${RhythmGame.EMOJIS[col]}</span>
            <span class="cell-label">${RhythmGame.LABELS[col]}</span>`;
  }

  // Build the HTML for a falling note in a given column
  _noteHTML(col, nearTrigger) {
    const photo = this.columnPhotos?.[col];
    if (photo) {
      const ring = nearTrigger
        ? '3px solid #f59e0b'
        : '2px solid rgba(255,255,255,0.25)';
      const glow = nearTrigger
        ? 'filter:drop-shadow(0 0 6px #f59e0b);'
        : '';
      return `<img src="${photo}"
        style="width:62%;height:62%;object-fit:cover;border-radius:50%;border:${ring};${glow}">`;
    }
    return nearTrigger ? '🟡' : '⚪';
  }

  _renderStatic() {
    for (let c = 0; c < this.grid.cols; c++) {
      this.grid.setContent(c, this.grid.rows - 1, this._columnIconHTML(c));
      this.grid.addClass(c, this.grid.rows - 1, 'highlight');
    }
  }

  _renderNotes() {
    const ROWS        = this.grid.rows;
    const TRIGGER_ROW = ROWS - 1;

    for (let r = 0; r < TRIGGER_ROW; r++)
      for (let c = 0; c < this.grid.cols; c++) {
        this.grid.cell(c, r).innerHTML = '';
        this.grid.setClass(c, r, '');
      }

    this.noteQueue.forEach(n => {
      if (n.col < 0 || n.hit) return;
      const r           = Math.max(0, Math.min(TRIGGER_ROW - 1, n.row));
      const nearTrigger = n.row >= TRIGGER_ROW - 1;
      this.grid.setContent(n.col, r, this._noteHTML(n.col, nearTrigger));
      this.grid.addClass(n.col, r, nearTrigger ? 'warn' : 'dim');
    });
  }

  _updateHud() {
    const pct        = Math.min(100, (this.score / this.WIN_SCORE) * 100);
    const hasPhotos  = !!this.columnPhotos;
    const tapHint    = hasPhotos ? 'Tap the face when<br>it reaches the bottom' : 'Tap the column<br>when 🟡 reaches<br>the bottom row';

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
        <div style="font-size:.8rem; color:var(--muted); margin-top:4px; line-height:1.6">${tapHint}</div>
      </div>
      ${hasPhotos ? `<div class="hud-box"><div class="hud-label">Stars</div><div style="font-size:.75rem;color:var(--accent2);margin-top:4px">📸 Your faces!</div></div>` : ''}
    `;
  }

  onTap(col, row) {
    if (!this.alive) return;
    const TRIGGER_ROW = this.grid.rows - 1;
    if (row !== TRIGGER_ROW) return;

    this._playNote(RhythmGame.NOTES[col]);

    let best = null, bestDist = Infinity;
    this.noteQueue.forEach(n => {
      if (n.col !== col || n.hit || n.rest) return;
      const rowFrac        = n.advance / (this.beatMs * 0.85);
      const distFromTrigger = Math.abs(rowFrac - 1.0);
      if (distFromTrigger < bestDist) { bestDist = distFromTrigger; best = n; }
    });

    if (best && bestDist < this.tolerance) {
      best.hit = true;
      this.score++;
      this.grid.flash(col, TRIGGER_ROW, 'note-hit', 350);
      if (this.score >= this.WIN_SCORE) { this._stop(); this.onWin(); return; }
    } else {
      this.score = Math.max(0, this.score - 1);
      this.grid.flash(col, TRIGGER_ROW, 'note-miss', 300);
      if (this.score === 0) { this.noteQueue = []; this.songPos = 0; this._spawnNext(); }
    }
    this._updateHud();
  }

  destroy() { this._destroyed = true; this._stop(); }

  nextLevel() {
    this.beatMs    = Math.max(260, this.beatMs - 40);
    this.WIN_SCORE += 6;
    this.score     = 0;
    this.noteQueue = [];
    this.songPos   = 0;
    this._spawnNext();
    this.alive = true;
    this._startLoop();
    this._renderStatic();
    this._updateHud();
  }
}
