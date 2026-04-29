/**
 * Grid — pluggable tap-grid engine.
 * Supports arbitrary rows×cols with optional irregular cell sizes.
 */
class Grid {
  /**
   * @param {HTMLElement} container  - #grid-container
   * @param {number} cols
   * @param {number} rows
   * @param {function} onTap        - called with (col, row, cellEl)
   */
  constructor(container, cols, rows, onTap) {
    this.container = container;
    this.cols = cols;
    this.rows = rows;
    this.onTap = onTap;
    this.cells = []; // cells[row][col]
    this._build();
  }

  _build() {
    const { container, cols, rows } = this;
    container.innerHTML = '';
    container.style.gridTemplateColumns = `repeat(${cols}, 1fr)`;
    container.style.gridTemplateRows = `repeat(${rows}, 1fr)`;

    // Compute cell size so grid fits nicely in viewport.
    // On mobile the HUD stacks below the grid, so don't subtract its width.
    const isMobile = window.innerWidth <= 600;
    const maxW = isMobile ? window.innerWidth - 32 : Math.min(window.innerWidth - 240, 620);
    const maxH = isMobile ? Math.round(window.innerHeight * 0.55) : window.innerHeight - 180;
    const cellPx = Math.floor(Math.min(maxW / cols, maxH / rows, 110));
    container.style.width = `${cellPx * cols + 4 * (cols - 1)}px`;

    this.cells = [];
    for (let r = 0; r < rows; r++) {
      this.cells[r] = [];
      for (let c = 0; c < cols; c++) {
        const el = document.createElement('div');
        el.className = 'grid-cell';
        el.style.width = el.style.height = `${cellPx}px`;
        el.dataset.col = c;
        el.dataset.row = r;
        el.addEventListener('pointerdown', (e) => {
          e.preventDefault();
          this.onTap(c, r, el);
        });
        container.appendChild(el);
        this.cells[r][c] = el;
      }
    }
  }

  cell(col, row) { return this.cells[row]?.[col]; }

  setContent(col, row, html) {
    const el = this.cell(col, row);
    if (el) el.innerHTML = html;
  }

  setClass(col, row, cls) {
    const el = this.cell(col, row);
    if (!el) return;
    el.className = 'grid-cell ' + (cls || '');
  }

  addClass(col, row, cls) {
    this.cell(col, row)?.classList.add(cls);
  }

  removeClass(col, row, cls) {
    this.cell(col, row)?.classList.remove(cls);
  }

  clearAll() {
    for (let r = 0; r < this.rows; r++)
      for (let c = 0; c < this.cols; c++)
        this.setClass(c, r, '');
  }

  flash(col, row, cls, ms = 300) {
    this.addClass(col, row, cls);
    setTimeout(() => this.removeClass(col, row, cls), ms);
  }

  /** Iterate all cells */
  forEach(fn) {
    for (let r = 0; r < this.rows; r++)
      for (let c = 0; c < this.cols; c++)
        fn(c, r, this.cells[r][c]);
  }

  resize(cols, rows) {
    this.cols = cols;
    this.rows = rows;
    this._build();
  }
}
