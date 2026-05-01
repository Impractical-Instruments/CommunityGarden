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

  touchInput.resize(meta.cols, meta.rows);

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

// ── Camera blob input ──────────────────────────────────────────────────────────
// TouchInput maps world-space blob positions (x=right, z=up) to grid cells.
// BlobWS receives {blobs:[{id,x,y,z}]} frames from the server WebSocket.
// Settings (screenRect, dwellFrames) are loaded from /api/captcha-settings.

const touchInput = new TouchInput({
  cols: 1, rows: 1, // placeholder — resized in startGame()
  screenRect:  { x0: -150, x1: 150, z0: 50, z1: 200 },
  dwellFrames: 3,
  onTap: (col, row) => {
    activeGame?.onTap(col, row);
    backgroundRenderer?.update({ game: currentGameId, event: 'tap' });
  },
});

(async function loadSettings() {
  try {
    const res = await fetch('/api/captcha-settings');
    const s   = await res.json();
    touchInput.configure({
      screenRect:  s.screen_rect        || undefined,
      dwellFrames: s.blob_dwell_frames  || undefined,
    });
  } catch (_) { /* use defaults — server may not be FastAPI yet */ }
})();

new BlobWS({
  url: BlobWS.wsUrl(),
  onBlobs: blobs => {
    touchInput.update(blobs);
    backgroundRenderer?.update({ game: currentGameId, blobCount: blobs.length });
  },
});
