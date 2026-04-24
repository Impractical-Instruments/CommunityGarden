/**
 * Football Keepaway
 *
 * Grid: 5×5
 * Offensive team (blue): one has the ball 🏈.
 * Player taps: (1) cell with ball-carrier → selects them
 *              (2) cell with an open receiver → pass
 * Defenders 🔴 move each tick, trying to reach the ball or cover receivers.
 * Win: survive TARGET_TIME seconds (increases each attempt).
 * Lose: a defender lands on the ball-carrier's cell.
 */
class KeepawayGame {
  static get META() {
    return {
      id: 'keepaway',
      title: '🏈 Football Keepaway',
      cols: 5, rows: 5,
    };
  }

  constructor(grid, hud, onWin, onLose) {
    this.grid    = grid;
    this.hud     = hud;
    this.onWin   = onWin;
    this.onLose  = onLose;

    this.difficulty  = 1;
    this.targetTime  = 12; // seconds to survive
    this._init();
  }

  _init() {
    this.phase    = 'select';   // 'select' | 'pass'
    this.selected = null;
    this.elapsed  = 0;
    this.alive    = true;

    const cols = this.grid.cols, rows = this.grid.rows;

    // Offensive players: 4 receivers + 1 ball carrier
    this.offense = [
      { c: 1, r: 1 }, { c: 3, r: 1 },
      { c: 0, r: 3 }, { c: 2, r: 3 }, { c: 4, r: 3 },
    ];
    // ball index into offense array
    this.ballIdx = 0;

    // Defenders: start far from ball
    this.defense = [
      { c: 4, r: 0 }, { c: 0, r: 4 }, { c: 4, r: 4 }, { c: 2, r: 2 },
    ];

    this._tickMs  = Math.max(600 - this.difficulty * 60, 250);
    this._tickId  = null;
    this._timerId = null;

    this._startTimers();
    this._render();
    this._updateHud();
  }

  _startTimers() {
    this._tickId  = setInterval(() => this._tick(), this._tickMs);
    this._timerId = setInterval(() => {
      if (!this.alive) return;
      this.elapsed++;
      this._updateHud();
      if (this.elapsed >= this.targetTime) {
        this._stop();
        this.onWin();
      }
    }, 1000);
  }

  _stop() {
    clearInterval(this._tickId);
    clearInterval(this._timerId);
    this.alive = false;
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
      // Half the defenders chase the ball, half cover nearest receiver
      let target = ballCell;
      if (di % 2 === 1) {
        // find furthest-from-ball offense player
        let best = null, bestDist = -1;
        this.offense.forEach((o, oi) => {
          if (oi === this.ballIdx) return;
          const d = Math.abs(o.c - ballCell.c) + Math.abs(o.r - ballCell.r);
          if (d > bestDist) { bestDist = d; best = o; }
        });
        if (best) target = best;
      }

      // Step one cell toward target; avoid occupied cells
      const dc = Math.sign(target.c - def.c);
      const dr = Math.sign(target.r - def.r);
      const candidates = [];
      if (dc !== 0) candidates.push({ c: def.c + dc, r: def.r });
      if (dr !== 0) candidates.push({ c: def.c, r: def.r + dr });
      if (dc !== 0 && dr !== 0) candidates.push({ c: def.c + dc, r: def.r + dr });
      candidates.push({ c: def.c, r: def.r }); // stay put fallback

      const occupied = new Set(
        this.defense.filter((_, i) => i !== di).map(d => `${d.c},${d.r}`)
      );

      for (const cand of candidates) {
        if (cand.c < 0 || cand.c >= this.grid.cols) continue;
        if (cand.r < 0 || cand.r >= this.grid.rows) continue;
        if (!occupied.has(`${cand.c},${cand.r}`)) {
          def.c = cand.c; def.r = cand.r;
          break;
        }
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

  _render() {
    const { grid, offense, defense, ballIdx, phase, selected } = this;
    grid.clearAll();
    grid.forEach((c, r, el) => { el.innerHTML = ''; });

    // Defenders
    defense.forEach(d => {
      grid.setContent(d.c, d.r, '🔴');
      grid.addClass(d.c, d.r, 'danger');
    });

    // Offense
    offense.forEach((o, i) => {
      const isBall  = i === ballIdx;
      const isSel   = selected === i;
      const isOpen  = !this._isDefended(o.c, o.r);
      const icon    = isBall ? '🏈' : (isOpen ? '🔵' : '🟤');
      grid.setContent(o.c, o.r, icon);
      if (isBall) {
        grid.addClass(o.c, o.r, isSel ? 'selected' : 'warn');
      } else if (isOpen) {
        grid.addClass(o.c, o.r, isSel ? 'selected' : 'highlight');
      }
    });
  }

  _updateHud() {
    const remaining = Math.max(0, this.targetTime - this.elapsed);
    const pct = (remaining / this.targetTime) * 100;
    this.hud.innerHTML = `
      <div class="hud-box">
        <div class="hud-label">Survive</div>
        <div class="hud-value ${remaining <= 3 ? 'bad' : 'good'}">${remaining}s</div>
        <div class="progress-bar">
          <div class="progress-bar-fill" style="width:${pct}%; background:${remaining <= 3 ? 'var(--danger)' : 'var(--success)'}"></div>
        </div>
      </div>
      <div class="hud-box">
        <div class="hud-label">Difficulty</div>
        <div class="hud-value">${this.difficulty}</div>
      </div>
      <div class="hud-box">
        <div class="hud-label">Instruction</div>
        <div style="font-size:.85rem; color:var(--muted); margin-top:4px;">
          ${this.phase === 'select' ? 'Tap 🏈 to select ball carrier' : 'Tap 🔵 open receiver to pass'}
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
        this.phase = 'pass';
        this._render();
        this._updateHud();
      }
      return;
    }

    // pass phase
    if (offIdx !== -1 && offIdx !== this.ballIdx) {
      const receiver = this.offense[offIdx];
      if (this._isDefended(receiver.c, receiver.r)) {
        // Can't pass to covered receiver
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
      // deselect
      this.selected = null;
      this.phase    = 'select';
      this._render();
      this._updateHud();
    }
  }

  destroy() { this._stop(); }

  nextLevel() {
    this.difficulty++;
    this.targetTime += 5;
    this._init();
  }
}
