/**
 * Football Keepaway
 *
 * Grid: 5×5
 * Offense taps ball-carrier → selects, taps open receiver → passes.
 * Defenders (canvas overlay, smooth continuous motion) chase ball.
 * Win: survive TARGET_TIME seconds. 10 levels, per-level config.
 */
class KeepawayGame {
  static get META() {
    return { id: 'keepaway', title: '🏈 Football Keepaway', cols: 5, rows: 5 };
  }

  // Edit this array to tune each level: defenders, tick speed, survival time.
  static LEVELS = [
    { defenders: 1, tickMs: 1600, targetTime:  8 },
    { defenders: 1, tickMs: 1300, targetTime: 12 },
    { defenders: 2, tickMs: 1100, targetTime: 14 },
    { defenders: 2, tickMs:  900, targetTime: 16 },
    { defenders: 2, tickMs:  750, targetTime: 18 },
    { defenders: 3, tickMs:  620, targetTime: 20 },
    { defenders: 3, tickMs:  500, targetTime: 22 },
    { defenders: 3, tickMs:  420, targetTime: 24 },
    { defenders: 4, tickMs:  360, targetTime: 26 },
    { defenders: 4, tickMs:  300, targetTime: 30 },
  ];

  static TUNING = {
    easeInFactor: 1.8,  // defenders start this many times slower at round start
  };

  constructor(grid, hud, onWin, onLose) {
    this.grid         = grid;
    this.hud          = hud;
    this.onWin        = onWin;
    this.onLose       = onLose;
    this.levelIdx     = 0;
    this.playerPhotos = null;
    this._destroyed   = false;
    this._canvas      = null;
    this._ctx         = null;
    this._rafId       = null;

    this._loadPhotosAndInit();
  }

  get hasNextLevel() { return this.levelIdx < KeepawayGame.LEVELS.length - 1; }

  async _loadPhotosAndInit() {
    try {
      const res    = await fetch('/api/photos');
      const photos = await res.json();
      if (Array.isArray(photos) && photos.length > 0) {
        this.playerPhotos = [...photos].sort(() => Math.random() - .5).map(p => p.url);
      }
    } catch (_) {}
    if (!this._destroyed) this._init();
  }

  _init() {
    this.phase    = 'select';
    this.selected = null;
    this.elapsed  = 0;
    this.alive    = true;

    const level  = KeepawayGame.LEVELS[this.levelIdx];
    const numDef = level.defenders;

    this.offense = [
      { c: 1, r: 1 }, { c: 3, r: 1 },
      { c: 0, r: 3 }, { c: 2, r: 3 }, { c: 4, r: 3 },
    ];
    this.ballIdx = 0;

    const defStarts = [
      { c: 4, r: 0 }, { c: 0, r: 4 }, { c: 4, r: 4 }, { c: 2, r: 2 },
    ];
    this.defense = defStarts.slice(0, numDef).map(d => ({
      c: d.c, r: d.r, vx: d.c, vy: d.r,
    }));

    this._baseTickMs = level.tickMs;
    this._tickMs     = this._baseTickMs * KeepawayGame.TUNING.easeInFactor;
    this._targetTime = level.targetTime;
    this._tickId     = null;
    this._timerId    = null;

    this._setupCanvas();
    this._startTimers();
    this._startRAF();
    this._render();
    this._updateHud();
  }

  _setupCanvas() {
    const cont = this.grid.container;
    if (!this._canvas) {
      this._canvas = document.createElement('canvas');
      this._canvas.style.cssText = 'position:absolute;inset:0;pointer-events:none;z-index:10;';
      this._ctx = this._canvas.getContext('2d');
    }
    if (this._canvas.parentNode !== cont) cont.appendChild(this._canvas);
    const px  = this.grid._cellPx;
    const gap = 4;
    this._canvas.width  = px * this.grid.cols + gap * (this.grid.cols - 1);
    this._canvas.height = px * this.grid.rows + gap * (this.grid.rows - 1);
  }

  _startRAF() {
    let last = performance.now();
    const loop = (now) => {
      if (!this.alive) return;
      const dt = now - last;
      last = now;
      this._updateVisuals(dt);
      this._drawCanvas();
      this._rafId = requestAnimationFrame(loop);
    };
    this._rafId = requestAnimationFrame(loop);
  }

  _updateVisuals(dt) {
    const speed = 1000 / (this._baseTickMs * 0.55); // cells per second
    this.defense.forEach(d => {
      const dx = d.c - d.vx, dy = d.r - d.vy;
      const dist = Math.hypot(dx, dy);
      if (dist < 0.005) { d.vx = d.c; d.vy = d.r; return; }
      const step = Math.min(dist, speed * dt / 1000);
      d.vx += (dx / dist) * step;
      d.vy += (dy / dist) * step;
    });
  }

  _drawCanvas() {
    const { _canvas: cv, _ctx: ctx, grid } = this;
    ctx.clearRect(0, 0, cv.width, cv.height);

    const px = grid._cellPx;
    const gap = 4;
    const r = px * 0.36;

    this.defense.forEach(d => {
      const x = d.vx * (px + gap) + px / 2;
      const y = d.vy * (px + gap) + px / 2;

      // Glow
      const grd = ctx.createRadialGradient(x, y, 0, x, y, r * 1.7);
      grd.addColorStop(0, 'rgba(239,68,68,0.45)');
      grd.addColorStop(1, 'rgba(239,68,68,0)');
      ctx.beginPath();
      ctx.arc(x, y, r * 1.7, 0, Math.PI * 2);
      ctx.fillStyle = grd;
      ctx.fill();

      // Body
      ctx.beginPath();
      ctx.arc(x, y, r, 0, Math.PI * 2);
      ctx.fillStyle = '#ef4444';
      ctx.fill();
      ctx.strokeStyle = 'rgba(255,255,255,0.85)';
      ctx.lineWidth = 2;
      ctx.stroke();

      // Inner highlight
      ctx.beginPath();
      ctx.arc(x - r * 0.28, y - r * 0.28, r * 0.32, 0, Math.PI * 2);
      ctx.fillStyle = 'rgba(255,255,255,0.35)';
      ctx.fill();
    });
  }

  _startTimers() {
    this._tickId  = setInterval(() => this._tick(), this._tickMs);
    this._timerId = setInterval(() => {
      if (!this.alive) return;
      this.elapsed++;
      this._updateTickSpeed();
      this._updateHud();
      if (this.elapsed >= this._targetTime) { this._stop(); this.onWin(); }
    }, 1000);
  }

  _updateTickSpeed() {
    const { easeInFactor } = KeepawayGame.TUNING;
    const progress = Math.min(this.elapsed / this._targetTime, 1);
    const factor   = easeInFactor - (easeInFactor - 1) * progress;
    const newMs    = Math.round(this._baseTickMs * factor);
    if (newMs !== this._tickMs) {
      this._tickMs = newMs;
      clearInterval(this._tickId);
      this._tickId = setInterval(() => this._tick(), this._tickMs);
    }
  }

  _stop() {
    clearInterval(this._tickId);
    clearInterval(this._timerId);
    cancelAnimationFrame(this._rafId);
    this._rafId = null;
    this.alive  = false;
    if (this._ctx) this._ctx.clearRect(0, 0, this._canvas.width, this._canvas.height);
  }

  _tick() {
    if (!this.alive) return;
    this._moveDefenders();
    this._checkCatch();
    this._render();
  }

  _moveDefenders() {
    const ballCell = this.offense[this.ballIdx];
    this.defense.forEach((def, di) => {
      let target = ballCell;
      if (di % 2 === 1) {
        let best = null, bestDist = -1;
        this.offense.forEach((o, oi) => {
          if (oi === this.ballIdx) return;
          const d = Math.abs(o.c - ballCell.c) + Math.abs(o.r - ballCell.r);
          if (d > bestDist) { bestDist = d; best = o; }
        });
        if (best) target = best;
      }
      const dc = Math.sign(target.c - def.c);
      const dr = Math.sign(target.r - def.r);
      const candidates = [];
      if (dc !== 0) candidates.push({ c: def.c + dc, r: def.r });
      if (dr !== 0) candidates.push({ c: def.c, r: def.r + dr });
      if (dc !== 0 && dr !== 0) candidates.push({ c: def.c + dc, r: def.r + dr });
      candidates.push({ c: def.c, r: def.r });

      const occupied = new Set(
        this.defense.filter((_, i) => i !== di).map(d => `${d.c},${d.r}`)
      );
      for (const cand of candidates) {
        if (cand.c < 0 || cand.c >= this.grid.cols) continue;
        if (cand.r < 0 || cand.r >= this.grid.rows) continue;
        if (!occupied.has(`${cand.c},${cand.r}`)) { def.c = cand.c; def.r = cand.r; break; }
      }
    });
  }

  _checkCatch() {
    const ball = this.offense[this.ballIdx];
    for (const def of this.defense) {
      if (def.c === ball.c && def.r === ball.r) {
        this._stop();
        this.grid.flash(ball.c, ball.r, 'danger', 800);
        setTimeout(() => this.onLose(), 800);
        return;
      }
    }
  }

  _isDefended(oc, or_) {
    return this.defense.some(d => d.c === oc && d.r === or_);
  }

  _playerHTML(playerIdx, badge, dimmed) {
    if (!this.playerPhotos?.length) return null;
    const url    = this.playerPhotos[playerIdx % this.playerPhotos.length];
    const filter = dimmed ? 'filter:grayscale(55%) brightness(0.55)' : '';
    return `<div style="position:relative;width:100%;height:100%;display:flex;align-items:center;justify-content:center">
      <img src="${url}" style="width:78%;height:78%;object-fit:cover;border-radius:50%;${filter}">
      ${badge ? `<span style="position:absolute;bottom:3px;right:3px;font-size:.9rem;line-height:1">${badge}</span>` : ''}
    </div>`;
  }

  _render() {
    const { grid, offense, ballIdx, selected } = this;
    grid.clearAll();
    grid.forEach((c, r, el) => { el.innerHTML = ''; });

    offense.forEach((o, i) => {
      const isBall = i === ballIdx;
      const isSel  = selected === i;
      const isOpen = !this._isDefended(o.c, o.r);

      const html = this._playerHTML(i, isBall ? '🏈' : null, !isOpen && !isBall);
      if (html) {
        grid.setContent(o.c, o.r, html);
      } else {
        grid.setContent(o.c, o.r, isBall ? '🏈' : (isOpen ? '🔵' : '🟤'));
      }

      if (isBall)       grid.addClass(o.c, o.r, isSel ? 'selected' : 'warn');
      else if (isOpen)  grid.addClass(o.c, o.r, isSel ? 'selected' : 'highlight');
    });
  }

  _updateHud() {
    const remaining = Math.max(0, this._targetTime - this.elapsed);
    const pct       = (remaining / this._targetTime) * 100;
    const hasPhotos = !!this.playerPhotos?.length;
    const passHint  = hasPhotos ? 'Tap an open teammate' : 'Tap 🔵 open receiver';
    const level     = KeepawayGame.LEVELS[this.levelIdx];

    this.hud.innerHTML = `
      <div class="hud-box">
        <div class="hud-label">Survive</div>
        <div class="hud-value ${remaining <= 3 ? 'bad' : 'good'}">${remaining}s</div>
        <div class="progress-bar">
          <div class="progress-bar-fill" style="width:${pct}%;background:${remaining <= 3 ? 'var(--danger)' : 'var(--success)'}"></div>
        </div>
      </div>
      <div class="hud-box">
        <div class="hud-label">Level</div>
        <div class="hud-value">${this.levelIdx + 1} / ${KeepawayGame.LEVELS.length}</div>
      </div>
      <div class="hud-box">
        <div class="hud-label">Defenders</div>
        <div class="hud-value">${level.defenders}</div>
      </div>
      <div class="hud-box">
        <div class="hud-label">Instruction</div>
        <div style="font-size:.82rem;color:var(--muted);margin-top:4px;line-height:1.5">
          ${this.phase === 'select' ? 'Tap 🏈 to select<br>the ball carrier' : `${passHint}<br>to pass`}
        </div>
      </div>
    `;
  }

  onTap(col, row) {
    if (!this.alive) return;

    const offIdx = this.offense.findIndex(o => o.c === col && o.r === row);
    const isBall = offIdx === this.ballIdx;

    if (this.phase === 'select') {
      if (isBall) {
        this.selected = offIdx;
        this.phase    = 'pass';
        this._render();
        this._updateHud();
      }
      return;
    }

    if (offIdx !== -1 && offIdx !== this.ballIdx) {
      const receiver = this.offense[offIdx];
      if (this._isDefended(receiver.c, receiver.r)) {
        this.grid.flash(col, row, 'danger', 300);
        return;
      }
      this.ballIdx  = offIdx;
      this.selected = null;
      this.phase    = 'select';
      this.grid.flash(col, row, 'success', 400);
      this._render();
      this._updateHud();
    } else if (isBall) {
      this.selected = null;
      this.phase    = 'select';
      this._render();
      this._updateHud();
    }
  }

  destroy() {
    this._destroyed = true;
    this._stop();
    this._canvas?.remove();
    this._canvas = null;
  }

  nextLevel() {
    if (!this.hasNextLevel) return false;
    this.levelIdx++;
    this._init();
    return true;
  }
}
