/**
 * Upside Down
 *
 * Grid: 4×4
 * Pairs of puzzle pieces are scattered, each showing a flipped half-icon.
 * Tap one piece, then its partner → they animate right-side-up and are "fixed".
 * Fix all pairs before time runs out.
 * Time out → vortex animation and lose.
 *
 * If /api/pairs has photo pairs saved via gallery.html, those are used instead
 * of the default emoji set.
 */
class UpsideDownGame {
  static get META() {
    return { id: 'upsidedown', title: '🔄 Upside Down', cols: 4, rows: 4 };
  }

  // Default emoji pairs used when no photos are configured.
  // Each entry: [ pieceA, pieceB, description ]
  // pieceA/B is either an emoji string or {url, label} for photos.
  static DEFAULT_PAIRS = [
    ['🚌', '🚗', 'vehicles'],
    ['🏠', '🏚️', 'houses'],
    ['🌳', '🌲', 'trees'],
    ['⚽', '🏈', 'balls'],
    ['🐶', '🐱', 'pets'],
    ['🍎', '🍊', 'fruits'],
    ['🌙', '⭐', 'sky'],
    ['🔑', '🔒', 'locks'],
  ];

  static TUNING = {
    initialTime:  45,  // seconds to match all pairs on first round
    timeMin:      20,  // minimum time (seconds) in later rounds
    timePerLevel:  8,  // seconds removed from timer each level
  };

  constructor(grid, hud, onWin, onLose) {
    this.grid   = grid;
    this.hud    = hud;
    this.onWin  = onWin;
    this.onLose = onLose;
    this.alive  = true;
    this.TIME   = UpsideDownGame.TUNING.initialTime;

    // Try to load photo pairs; fall back to emoji if unavailable or empty.
    this._loadPairsAndInit();
  }

  async _loadPairsAndInit() {
    let pairSource = UpsideDownGame.DEFAULT_PAIRS;
    try {
      const res   = await fetch('/api/pairs');
      const data  = await res.json();
      if (Array.isArray(data) && data.length >= 2) {
        // Convert API format [{label, a:{url,label}, b:{url,label}}]
        // to internal format [[pieceA, pieceB, label]]
        pairSource = data.map(p => [
          { url: p.a.url, label: p.a.label },
          { url: p.b.url, label: p.b.label },
          p.label,
        ]);
      }
    } catch (_) { /* no server or no pairs — use default */ }

    this._pairSource = pairSource;
    this._init();
  }

  _init() {
    this.elapsed   = 0;
    this.selected  = null;
    this.fixed     = new Set();
    this.alive     = true;

    const totalCells = this.grid.cols * this.grid.rows;
    const numPairs   = totalCells / 2;

    const shuffledPairs = [...this._pairSource]
      .sort(() => Math.random() - .5)
      .slice(0, numPairs);

    const cells = [];
    for (let r = 0; r < this.grid.rows; r++)
      for (let c = 0; c < this.grid.cols; c++)
        cells.push({ c, r });
    cells.sort(() => Math.random() - .5);

    // pieces[key] = { pairId, half(0|1), piece } where piece is emoji string or {url,label}
    this.pieces = {};
    shuffledPairs.forEach((pair, pi) => {
      const cellA = cells[pi * 2];
      const cellB = cells[pi * 2 + 1];
      this.pieces[`${cellA.c},${cellA.r}`] = { pairId: pi, half: 0, piece: pair[0] };
      this.pieces[`${cellB.c},${cellB.r}`] = { pairId: pi, half: 1, piece: pair[1] };
    });

    this._render();
    this._updateHud();
    this._timerId = setInterval(() => {
      if (!this.alive) return;
      this.elapsed++;
      this._updateHud();
      if (this.elapsed >= this.TIME) {
        this._stop();
        this._vortexAnimation().then(() => this.onLose());
      }
    }, 1000);
  }

  _stop() {
    this.alive = false;
    clearInterval(this._timerId);
  }

  _pieceHTML(piece, isFixed) {
    const transform = isFixed ? 'none' : 'rotate(180deg)';
    if (piece && typeof piece === 'object' && piece.url) {
      // Photo piece
      return `<img src="${piece.url}" alt="${piece.label || ''}"
        style="width:85%;height:85%;object-fit:cover;border-radius:6px;
               display:block;transform:${transform};transition:transform .4s ease">`;
    }
    // Emoji piece
    return `<span style="display:inline-block;transform:${transform};font-size:1.6rem;transition:transform .4s ease">${piece}</span>`;
  }

  _render() {
    this.grid.clearAll();
    for (let r = 0; r < this.grid.rows; r++) {
      for (let c = 0; c < this.grid.cols; c++) {
        const key   = `${c},${r}`;
        const slot  = this.pieces[key];
        if (!slot) continue;
        const el      = this.grid.cell(c, r);
        const isFixed = this.fixed.has(key);
        const isSel   = this.selected?.col === c && this.selected?.row === r;

        el.innerHTML  = this._pieceHTML(slot.piece, isFixed);
        el.className  = 'grid-cell' + (isFixed ? ' matched' : isSel ? ' selected-piece' : '');
      }
    }
  }

  _updateHud() {
    const remaining = Math.max(0, this.TIME - this.elapsed);
    const pct       = (remaining / this.TIME) * 100;
    const matched   = this.fixed.size / 2;
    const total     = Object.keys(this.pieces).length / 2;
    const usingPhotos = this._pairSource !== UpsideDownGame.DEFAULT_PAIRS;

    this.hud.innerHTML = `
      <div class="hud-box">
        <div class="hud-label">Time Left</div>
        <div class="hud-value ${remaining <= 10 ? 'bad' : 'good'}">${remaining}s</div>
        <div class="progress-bar">
          <div class="progress-bar-fill" style="width:${pct}%; background:${remaining <= 10 ? 'var(--danger)' : 'var(--accent2)'}"></div>
        </div>
      </div>
      <div class="hud-box">
        <div class="hud-label">Pairs Fixed</div>
        <div class="hud-value">${matched} / ${total}</div>
      </div>
      <div class="hud-box">
        <div class="hud-label">How to play</div>
        <div style="font-size:.8rem; color:var(--muted); margin-top:4px; line-height:1.5">
          Tap two pieces<br>that belong<br>together
        </div>
      </div>
      ${usingPhotos ? `<div class="hud-box"><div class="hud-label">Content</div><div style="font-size:.75rem;color:var(--accent2);margin-top:4px">📸 Using your photos!</div></div>` : ''}
    `;
  }

  async _vortexAnimation() {
    const cells = [];
    for (let r = 0; r < this.grid.rows; r++)
      for (let c = 0; c < this.grid.cols; c++) {
        const key = `${c},${r}`;
        if (!this.fixed.has(key) && this.pieces[key]) cells.push({ c, r });
      }

    return new Promise(resolve => {
      cells.forEach(({ c, r }, i) => {
        setTimeout(() => {
          const el = this.grid.cell(c, r);
          if (el) {
            el.style.transition = 'transform .5s ease-in, opacity .5s';
            el.style.transform  = 'scale(0) rotate(360deg)';
            el.style.opacity    = '0';
          }
        }, i * 80);
      });
      setTimeout(resolve, cells.length * 80 + 600);
    });
  }

  onTap(col, row) {
    if (!this.alive) return;
    const key   = `${col},${row}`;
    const slot  = this.pieces[key];
    if (!slot || this.fixed.has(key)) return;

    if (!this.selected) {
      this.selected = { col, row, pairId: slot.pairId, half: slot.half };
      this._render();
      return;
    }

    if (this.selected.col === col && this.selected.row === row) {
      this.selected = null;
      this._render();
      return;
    }

    if (this.selected.pairId === slot.pairId && this.selected.half !== slot.half) {
      // Match!
      const prevCol = this.selected.col, prevRow = this.selected.row;
      this.fixed.add(`${prevCol},${prevRow}`);
      this.fixed.add(key);
      this.selected = null;
      this._render();
      this.grid.flash(col, row, 'success', 500);
      this.grid.flash(prevCol, prevRow, 'success', 500);

      if (this.fixed.size === Object.keys(this.pieces).length) {
        this._stop();
        setTimeout(() => this.onWin(), 400);
      }
    } else {
      const prevCol = this.selected.col, prevRow = this.selected.row;
      this.selected = null;
      this.grid.flash(col, row, 'wrong', 400);
      this.grid.flash(prevCol, prevRow, 'wrong', 400);
      setTimeout(() => this._render(), 420);
    }
    this._updateHud();
  }

  destroy() { this._stop(); }

  nextLevel() {
    this.TIME = Math.max(UpsideDownGame.TUNING.timeMin, this.TIME - UpsideDownGame.TUNING.timePerLevel);
    this._init();
  }
}
