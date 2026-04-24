/**
 * Upside Down
 *
 * Grid: 4×4
 * Pairs of puzzle pieces are scattered, each showing a flipped half-icon.
 * Tap one piece, then its partner → they animate right-side-up and are "fixed".
 * Fix all pairs before time runs out.
 * Time out → vortex animation and lose.
 */
class UpsideDownGame {
  static get META() {
    return { id: 'upsidedown', title: '🔄 Upside Down', cols: 4, rows: 4 };
  }

  // Pairs: [ [ half-A-emoji, half-B-emoji, description ], ... ]
  static PAIRS = [
    ['🚌', '🚗', 'vehicles'],
    ['🏠', '🏚️', 'houses'],
    ['🌳', '🌲', 'trees'],
    ['⚽', '🏈', 'balls'],
    ['🐶', '🐱', 'pets'],
    ['🍎', '🍊', 'fruits'],
    ['🌙', '⭐', 'sky'],
    ['🔑', '🔒', 'locks'],
  ];

  constructor(grid, hud, onWin, onLose) {
    this.grid   = grid;
    this.hud    = hud;
    this.onWin  = onWin;
    this.onLose = onLose;
    this.alive  = true;
    this.TIME   = 45; // seconds

    this._init();
  }

  _init() {
    this.elapsed   = 0;
    this.selected  = null; // { col, row, pairId, half }
    this.fixed     = new Set(); // "col,row" keys of matched cells
    this.alive     = true;

    const totalCells = this.grid.cols * this.grid.rows;
    const numPairs   = totalCells / 2;

    // Pick pairs
    const shuffledPairs = [...UpsideDownGame.PAIRS].sort(() => Math.random() - .5).slice(0, numPairs);

    // Build cell list
    const cells = [];
    for (let r = 0; r < this.grid.rows; r++)
      for (let c = 0; c < this.grid.cols; c++)
        cells.push({ c, r });

    // Shuffle cells
    cells.sort(() => Math.random() - .5);

    // Assign pairs to shuffled cells
    this.pieces = {}; // "col,row" → { pairId, half (0|1), emoji }
    shuffledPairs.forEach((pair, pi) => {
      const cellA = cells[pi * 2];
      const cellB = cells[pi * 2 + 1];
      this.pieces[`${cellA.c},${cellA.r}`] = { pairId: pi, half: 0, emoji: pair[0] };
      this.pieces[`${cellB.c},${cellB.r}`] = { pairId: pi, half: 1, emoji: pair[1] };
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

  _render() {
    this.grid.clearAll();
    for (let r = 0; r < this.grid.rows; r++) {
      for (let c = 0; c < this.grid.cols; c++) {
        const key = `${c},${r}`;
        const piece = this.pieces[key];
        if (!piece) continue;
        const el = this.grid.cell(c, r);
        const isFixed = this.fixed.has(key);
        const isSel   = this.selected?.col === c && this.selected?.row === r;

        el.innerHTML = `<span style="display:inline-block;transform:${isFixed ? 'none' : 'rotate(180deg)'};font-size:1.6rem">${piece.emoji}</span>`;
        el.className = 'grid-cell' + (isFixed ? ' matched' : isSel ? ' selected-piece' : '');
      }
    }
  }

  _updateHud() {
    const remaining = Math.max(0, this.TIME - this.elapsed);
    const pct = (remaining / this.TIME) * 100;
    const matched = this.fixed.size / 2;
    const total   = Object.keys(this.pieces).length / 2;

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
    `;
  }

  async _vortexAnimation() {
    // Spin all unmatched pieces toward center and hide
    const cells = [];
    for (let r = 0; r < this.grid.rows; r++)
      for (let c = 0; c < this.grid.cols; c++) {
        const key = `${c},${r}`;
        if (!this.fixed.has(key) && this.pieces[key]) cells.push({ c, r });
      }

    // Staggered shrink animation
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
    const key = `${col},${row}`;
    const piece = this.pieces[key];
    if (!piece || this.fixed.has(key)) return;

    if (!this.selected) {
      this.selected = { col, row, pairId: piece.pairId, half: piece.half };
      this._render();
      return;
    }

    // Same cell — deselect
    if (this.selected.col === col && this.selected.row === row) {
      this.selected = null;
      this._render();
      return;
    }

    // Check match
    if (this.selected.pairId === piece.pairId && this.selected.half !== piece.half) {
      // Match!
      const prevCol = this.selected.col, prevRow = this.selected.row;
      const keyA = `${prevCol},${prevRow}`;
      this.fixed.add(keyA);
      this.fixed.add(key);
      this.selected = null;
      this._render();
      this.grid.flash(col, row, 'success', 500);
      this.grid.flash(prevCol, prevRow, 'success', 500);

      // Win check
      if (this.fixed.size === Object.keys(this.pieces).length) {
        this._stop();
        setTimeout(() => this.onWin(), 400);
      }
    } else {
      // Wrong pair
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
    this.TIME = Math.max(20, this.TIME - 8);
    this._init();
  }
}
