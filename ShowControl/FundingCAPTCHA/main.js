/**
 * FundingCAPTCHA — orchestrator
 * Wires together the lobby, grid, pluggable game modules, background renderer,
 * and the WebSocket blob-input client (for camera-driven installs).
 */

const GAMES = {
  keepaway:   KeepawayGame,
  rhythm:     RhythmGame,
  upsidedown: UpsideDownGame,
};

let activeGame    = null;
let grid          = null;
let currentGameId = null;

const lobby      = document.getElementById('lobby');
const gameScreen = document.getElementById('game-screen');
const gridCont   = document.getElementById('grid-container');
const gameHud    = document.getElementById('game-hud');
const gameTitle  = document.getElementById('game-title');
const gameStatus = document.getElementById('game-status');
const msgOverlay = document.getElementById('game-message');

// ── Lobby ──────────────────────────────────────────────────────────────────────
document.querySelectorAll('.game-card .play-btn').forEach(btn => {
  btn.addEventListener('click', () => startGame(btn.closest('.game-card').dataset.game));
});

document.getElementById('back-btn').addEventListener('click', () => {
  stopGame();
  showLobby();
});

function showLobby() {
  lobby.classList.remove('hidden');
  gameScreen.classList.add('hidden');
  msgOverlay.classList.add('hidden');
  currentGameId = null;
  backgroundRenderer?.update({ game: null });
}

function startGame(id) {
  const GameClass = GAMES[id];
  if (!GameClass) return;

  stopGame();
  lobby.classList.add('hidden');
  gameScreen.classList.remove('hidden');
  msgOverlay.classList.add('hidden');

  const meta = GameClass.META;
  gameTitle.textContent = meta.title;
  gameStatus.textContent = '';
  currentGameId = id;

  grid = new Grid(gridCont, meta.cols, meta.rows, (col, row) => {
    activeGame?.onTap(col, row);
    backgroundRenderer?.update({ game: currentGameId, event: 'tap' });
  });

  activeGame = new GameClass(
    grid,
    gameHud,
    () => handleWin(id),
    () => handleLose(id)
  );

  backgroundRenderer?.update({ game: id });
}

function stopGame() {
  activeGame?.destroy();
  activeGame    = null;
  grid          = null;
  gridCont.innerHTML = '';
  gameHud.innerHTML  = '';
}

function handleWin(id) {
  backgroundRenderer?.update({ game: id, event: 'win' });
  showMessage(
    '🎉 You did it!',
    "Challenge complete. You've proven you're human (or at least have human-like skills).",
    'Play Again',
    () => {
      if (activeGame) {
        msgOverlay.classList.add('hidden');
        activeGame.nextLevel?.();
      } else {
        startGame(id);
      }
    },
    'Back to Menu',
    () => { stopGame(); showLobby(); }
  );
}

function handleLose(id) {
  backgroundRenderer?.update({ game: id, event: 'lose' });
  showMessage(
    '💀 Game Over',
    'The defenders got the ball. Try again!',
    'Try Again',
    () => startGame(id),
    'Back to Menu',
    () => { stopGame(); showLobby(); }
  );
}

function showMessage(title, body, btn1Text, btn1Fn, btn2Text, btn2Fn) {
  msgOverlay.innerHTML = `
    <div class="msg-box">
      <h2>${title}</h2>
      <p>${body}</p>
      <div style="display:flex; gap:12px; justify-content:center; flex-wrap:wrap">
        <button id="msg-btn1">${btn1Text}</button>
        ${btn2Text ? `<button id="msg-btn2" style="background:var(--surface);border:1px solid var(--border)">${btn2Text}</button>` : ''}
      </div>
    </div>`;
  msgOverlay.classList.remove('hidden');
  document.getElementById('msg-btn1')?.addEventListener('click', btn1Fn);
  document.getElementById('msg-btn2')?.addEventListener('click', btn2Fn);
}

// ── WebSocket blob input ───────────────────────────────────────────────────────
// When the server runs with --camera or --mock-camera it pushes
// { blobs: [{id, x, y}] } in world-space centimetres each frame.
// We normalise these to grid (col, row) using the floor rect from captcha-settings.json.

let floorRect       = { x0: -150, y0: 100, x1: 150, y1: 400 };
let blobDwellFrames = 3; // frames a blob must dwell in a cell before triggering a tap

// Map { blobId → { col, row, frames } }
const _blobDwell = new Map();

(async function loadSettings() {
  try {
    const res = await fetch('/api/captcha-settings');
    const s   = await res.json();
    if (s.floor_rect)        floorRect       = s.floor_rect;
    if (s.blob_dwell_frames) blobDwellFrames = s.blob_dwell_frames;
  } catch (_) { /* use defaults — server may not be FastAPI yet */ }
})();

function _blobToCell(x, y, cols, rows) {
  const { x0, y0, x1, y1 } = floorRect;
  const col = Math.floor((x - x0) / (x1 - x0) * cols);
  const row = Math.floor((y - y0) / (y1 - y0) * rows);
  return {
    col: Math.max(0, Math.min(cols - 1, col)),
    row: Math.max(0, Math.min(rows - 1, row)),
  };
}

function _connectWS() {
  const proto = location.protocol === 'https:' ? 'wss' : 'ws';
  const ws    = new WebSocket(`${proto}://${location.host}/ws`);

  ws.onmessage = (ev) => {
    let msg;
    try { msg = JSON.parse(ev.data); } catch (_) { return; }
    const blobs = msg.blobs;
    if (!Array.isArray(blobs) || !activeGame || !grid) return;

    const cols = grid.cols, rows = grid.rows;
    const liveIds = new Set(blobs.map(b => b.id));

    // Evict stale blob tracks
    for (const id of _blobDwell.keys()) {
      if (!liveIds.has(id)) _blobDwell.delete(id);
    }

    // Process each blob: dwell-debounce → virtual tap
    blobs.forEach(b => {
      const { col, row } = _blobToCell(b.x, b.y, cols, rows);
      const prev = _blobDwell.get(b.id);
      if (!prev || prev.col !== col || prev.row !== row) {
        _blobDwell.set(b.id, { col, row, frames: 1 });
      } else {
        prev.frames++;
        if (prev.frames === blobDwellFrames) {
          // Dwell threshold reached — fire exactly once until blob moves
          activeGame.onTap(col, row);
          backgroundRenderer?.update({ game: currentGameId, event: 'tap' });
        }
      }
    });

    backgroundRenderer?.update({ game: currentGameId, blobCount: blobs.length });
  };

  ws.onclose = () => setTimeout(_connectWS, 2000);
  ws.onerror = () => ws.close();
}

_connectWS();
