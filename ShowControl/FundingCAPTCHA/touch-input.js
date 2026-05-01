/**
 * TouchInput — maps world-space blob positions to grid tap events.
 *
 * Pure processor: feed it blob arrays via update(), get onTap() callbacks.
 * No WebSocket, no DOM.
 *
 * Coordinate convention: X=right, Z=up (height on vertical screen).
 * Row 0 is the top of the screen (high Z); row (rows-1) is the bottom (low Z).
 */
class TouchInput {
  /**
   * @param {object} opts
   * @param {number} opts.cols
   * @param {number} opts.rows
   * @param {{ x0: number, x1: number, z0: number, z1: number }} opts.screenRect
   *   World-space bounding box (cm) of the screen surface.
   *   x0/x1 = left/right edges; z0/z1 = bottom/top edges.
   * @param {number} [opts.dwellFrames=3]  Frames a blob must stay in a cell before tap fires.
   * @param {(col: number, row: number) => void} opts.onTap
   */
  constructor({ cols, rows, screenRect, dwellFrames = 3, onTap }) {
    this._cols        = cols;
    this._rows        = rows;
    this._screenRect  = screenRect;
    this._dwellFrames = dwellFrames;
    this._onTap       = onTap;
    this._dwell       = new Map(); // blobId → { col, row, frames }
  }

  /** Update screenRect and/or dwellFrames without recreating the instance. */
  configure({ screenRect, dwellFrames } = {}) {
    if (screenRect  !== undefined) this._screenRect  = screenRect;
    if (dwellFrames !== undefined) this._dwellFrames = dwellFrames;
  }

  /** Change grid dimensions and clear all in-progress dwell state. */
  resize(cols, rows) {
    this._cols = cols;
    this._rows = rows;
    this._dwell.clear();
  }

  /**
   * Process one frame of blobs.
   * @param {{ id: number, x: number, y: number, z: number }[]} blobs
   *   World-space positions in cm. y (depth) is ignored for grid mapping.
   */
  update(blobs) {
    const liveIds = new Set(blobs.map(b => b.id));

    for (const id of this._dwell.keys()) {
      if (!liveIds.has(id)) this._dwell.delete(id);
    }

    for (const b of blobs) {
      const { col, row } = this._toCell(b.x, b.z);
      const prev = this._dwell.get(b.id);

      if (!prev || prev.col !== col || prev.row !== row) {
        this._dwell.set(b.id, { col, row, frames: 1 });
      } else {
        prev.frames++;
      }
      if (this._dwell.get(b.id).frames === this._dwellFrames) {
        this._onTap(col, row);
      }
    }
  }

  /**
   * Convert world-space (x, z) to (col, row).
   * X increases rightward → col increases.
   * Z increases upward → row *decreases* (row 0 = top of screen).
   */
  _toCell(x, z) {
    const { x0, x1, z0, z1 } = this._screenRect;
    const col = Math.floor((x  - x0) / (x1 - x0) * this._cols);
    const row = Math.floor((z1 - z)  / (z1 - z0) * this._rows);
    return {
      col: Math.max(0, Math.min(this._cols - 1, col)),
      row: Math.max(0, Math.min(this._rows - 1, row)),
    };
  }
}

if (typeof module !== 'undefined') module.exports = { TouchInput };
