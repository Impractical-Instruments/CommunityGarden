/**
 * Upside Down
 *
 * Grid: 4×4
 * Pairs of pieces are scattered upside-down. Tap matching pairs to fix them.
 * Fix all pairs before time runs out.
 *
 * Background image (uploaded via upload.html → /api/background) bleeds through
 * the grid, with opacity increasing each level so pairs camouflage harder.
 * 10 levels: timer decreases and background gets more opaque.
 */
class UpsideDownGame {
  static get META() {
    return { id: 'upsidedown', title: '🔄 Upside Down', cols: 4, rows: 4 };
  }

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

  // Per-level config: timeLimit (seconds) and bgOpacity (0 = invisible, 1 = full).
  static LEVELS = [
    { timeLimit: 60, bgOpacity: 0.00 },
    { timeLimit: 55, bgOpacity: 0.10 },
    { timeLimit: 50, bgOpacity: 0.20 },
    { timeLimit: 45, bgOpacity: 0.32 },
    { timeLimit: 40, bgOpacity: 0.44 },
    { timeLimit: 35, bgOpacity: 0.55 },
    { timeLimit: 30, bgOpacity: 0.65 },
    { timeLimit: 25, bgOpacity: 0.75 },
    { timeLimit: 20, bgOpacity: 0.87 },
    { timeLimit: 15, bgOpacity: 1.00 },
  ];

  constructor(grid, hud, onWin, onLose) {
    this.grid     = grid;
    this.hud      = hud;
    this.onWin    = onWin;
    this.onLose   = onLose;
    this.levelIdx   = 0;
    this.alive      = true;
    this._bgUrl     = null;
    this._destroyed = false;

    this._loadAll();
  }

  get hasNextLevel() { return this.levelIdx < UpsideDownGame.LEVELS.length - 1; }

  async _loadAll() {
    const [pairSource, bgUrl] = await Promise.all([
      this._fetchPairs(),
      this._fetchBackground(),
    ]);
    this._pairSource = pairSource;
    this._bgUrl      = bgUrl;
    if (!this._destroyed) this._init();
  }

  async _fetchPairs() {
    try {
      const res  = await fetch('/api/pairs');
      const data = await res.json();
      if (Array.isArray(data) && data.length >= 2) {
        return data.map(p => [
          { url: p.a.url, label: p.a.label },
          { url: p.b.url, label: p.b.label },
          p.label,
        ]);
      }
    } catch (_) {}
    return UpsideDownGame.DEFAULT_PAIRS;
  }

  async _fetchBackground() {
    try {
      const res = await fetch('/api/background');
      if (res.ok) return '/api/background';
    } catch (_) {}
    return null;
  }

  _init() {
    this.elapsed  = 0;
    this.selected = null;
    this.fixed    = new Set();
    this.alive    = true;

    const level = UpsideDownGame.LEVELS[this.levelIdx];
    this.TIME   = level.timeLimit;

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

    this.pieces = {};
    shuffledPairs.forEach((pair, pi) => {
      const cellA = cells[pi * 2];
      const cellB = cells[pi * 2 + 1];
      this.pieces[`${cellA.c},${cellA.r}`] = { pairId: pi, half: 0, piece: pair[0] };
      this.pieces[`${cellB.c},${cellB.r}`] = { pairId: pi, half: 1, piece: pair[1] };
    });

    this._applyBackground(level.bgOpacity);
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

  _applyBackground(opacity) {
    const cont = this.grid.container;
    if (this._bgUrl && opacity > 0) {
      cont.style.backgroundImage    = `url('${this._bgUrl}')`;
      cont.style.backgroundSize     = 'cover';
      cont.style.backgroundPosition = 'center';
      // Make cells semi-transparent so background bleeds through.
      // At opacity=0: cells are mostly opaque. At opacity=1: cells are mostly clear.
      const cellBg = `rgba(20,20,30,${(0.9 - opacity * 0.78).toFixed(2)})`;
      this._injectCellStyle(cellBg);
    } else {
      cont.style.backgroundImage = '';
      this._injectCellStyle(null);
    }
  }

  _injectCellStyle(bgValue) {
    let el = document.getElementById('_usd_style');
    if (!el) {
      el = document.createElement('style');
      el.id = '_usd_style';
      document.head.appendChild(el);
    }
    el.textContent = bgValue
      ? `#grid-container .grid-cell { background: ${bgValue} !important; }`
      : '';
  }

  _stop() {
    this.alive = false;
    clearInterval(this._timerId);
  }

  _pieceHTML(piece, isFixed) {
    const transform = isFixed ? 'none' : 'rotate(180deg)';
    if (piece && typeof piece === 'object' && piece.url) {
      return `<img src="${piece.url}" alt="${piece.label || ''}"
        style="width:85%;height:85%;object-fit:cover;border-radius:6px;
               display:block;transform:${transform};transition:transform .4s ease">`;
    }
    return `<span style="display:inline-block;transform:${transform};font-size:1.6rem;transition:transform .4s ease">${piece}</span>`;
  }

  _render() {
    this.grid.clearAll();
    for (let r = 0; r < this.grid.rows; r++) {
      for (let c = 0; c < this.grid.cols; c++) {
        const key  = `${c},${r}`;
        const slot = this.pieces[key];
        if (!slot) continue;
        const el      = this.grid.cell(c, r);
        const isFixed = this.fixed.has(key);
        const isSel   = this.selected?.col === c && this.selected?.row === r;

        el.innerHTML = this._pieceHTML(slot.piece, isFixed);
        el.className = 'grid-cell' + (isFixed ? ' matched' : isSel ? ' selected-piece' : '');
      }
    }
  }

  _updateHud() {
    const remaining   = Math.max(0, this.TIME - this.elapsed);
    const pct         = (remaining / this.TIME) * 100;
    const matched     = this.fixed.size / 2;
    const total       = Object.keys(this.pieces).length / 2;
    const usingPhotos = this._pairSource !== UpsideDownGame.DEFAULT_PAIRS;
    const level       = UpsideDownGame.LEVELS[this.levelIdx];
    const bgPct       = Math.round(level.bgOpacity * 100);

    this.hud.innerHTML = `
      <div class="hud-box">
        <div class="hud-label">Time Left</div>
        <div class="hud-value ${remaining <= 10 ? 'bad' : 'good'}">${remaining}s</div>
        <div class="progress-bar">
          <div class="progress-bar-fill" style="width:${pct}%;background:${remaining <= 10 ? 'var(--danger)' : 'var(--accent2)'}"></div>
        </div>
      </div>
      <div class="hud-box">
        <div class="hud-label">Pairs Fixed</div>
        <div class="hud-value">${matched} / ${total}</div>
      </div>
      <div class="hud-box">
        <div class="hud-label">Level</div>
        <div class="hud-value">${this.levelIdx + 1} / ${UpsideDownGame.LEVELS.length}</div>
      </div>
      ${bgPct > 0 ? `
      <div class="hud-box">
        <div class="hud-label">Camouflage</div>
        <div class="hud-value warn">${bgPct}%</div>
      </div>` : ''}
      <div class="hud-box">
        <div class="hud-label">How to Play</div>
        <div style="font-size:.8rem;color:var(--muted);margin-top:4px;line-height:1.5">
          Tap two pieces<br>that belong<br>together
        </div>
      </div>
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
    const key  = `${col},${row}`;
    const slot = this.pieces[key];
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

  destroy() {
    this._destroyed = true;
    this._stop();
    this.grid.container.style.backgroundImage = '';
    this._injectCellStyle(null);
  }

  nextLevel() {
    if (!this.hasNextLevel) return false;
    this.levelIdx++;
    this._init();
    return true;
  }
}
