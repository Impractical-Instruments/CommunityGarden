/**
 * FundingCAPTCHA — orchestrator
 * Wires together the lobby, grid, and pluggable game modules.
 */

const GAMES = {
  keepaway:   KeepawayGame,
  rhythm:     RhythmGame,
  upsidedown: UpsideDownGame,
};

let activeGame = null;
let grid       = null;

const lobby      = document.getElementById('lobby');
const gameScreen = document.getElementById('game-screen');
const gridCont   = document.getElementById('grid-container');
const gameHud    = document.getElementById('game-hud');
const gameTitle  = document.getElementById('game-title');
const gameStatus = document.getElementById('game-status');
const msgOverlay = document.getElementById('game-message');

// --- Lobby ---
document.querySelectorAll('.game-card .play-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    const card = btn.closest('.game-card');
    startGame(card.dataset.game);
  });
});

document.getElementById('back-btn').addEventListener('click', () => {
  stopGame();
  showLobby();
});

function showLobby() {
  lobby.classList.remove('hidden');
  gameScreen.classList.add('hidden');
  msgOverlay.classList.add('hidden');
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

  grid = new Grid(gridCont, meta.cols, meta.rows, (col, row, el) => {
    activeGame?.onTap(col, row);
  });

  activeGame = new GameClass(
    grid,
    gameHud,
    () => handleWin(id),
    () => handleLose(id)
  );
}

function stopGame() {
  activeGame?.destroy();
  activeGame = null;
  grid = null;
  gridCont.innerHTML = '';
  gameHud.innerHTML  = '';
}

function handleWin(id) {
  showMessage(
    '🎉 You did it!',
    'Challenge complete. You\'ve proven you\'re human (or at least have human-like skills).',
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
        ${btn2Text ? `<button id="msg-btn2" style="background:var(--surface); border:1px solid var(--border)">${btn2Text}</button>` : ''}
      </div>
    </div>`;
  msgOverlay.classList.remove('hidden');
  document.getElementById('msg-btn1')?.addEventListener('click', btn1Fn);
  document.getElementById('msg-btn2')?.addEventListener('click', btn2Fn);
}
