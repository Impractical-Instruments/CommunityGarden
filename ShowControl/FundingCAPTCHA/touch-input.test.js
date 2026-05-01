// node --test touch-input.test.js

const { test, describe } = require('node:test');
const assert = require('node:assert/strict');
const { TouchInput } = require('./touch-input.js');

const RECT = { x0: 0, x1: 100, z0: 0, z1: 100 };

function make(overrides = {}) {
  const taps = [];
  const ti = new TouchInput({
    cols: 5,
    rows: 5,
    screenRect: RECT,
    dwellFrames: 3,
    onTap: (col, row) => taps.push({ col, row }),
    ...overrides,
  });
  return { ti, taps };
}

// ── Cell mapping ──────────────────────────────────────────────────────────────

describe('_toCell', () => {
  test('left edge → col 0', () => {
    const { ti } = make();
    assert.equal(ti._toCell(0, 50).col, 0);
  });

  test('right edge → last col', () => {
    const { ti } = make();
    assert.equal(ti._toCell(100, 50).col, 4);
  });

  test('top of screen (high Z) → row 0', () => {
    const { ti } = make();
    assert.equal(ti._toCell(50, 100).row, 0);
  });

  test('bottom of screen (low Z) → last row', () => {
    const { ti } = make();
    assert.equal(ti._toCell(50, 0).row, 4);
  });

  test('centre maps to centre cell', () => {
    const { ti } = make();
    const { col, row } = ti._toCell(50, 50);
    assert.equal(col, 2);
    assert.equal(row, 2);
  });

  test('clamps blobs outside rect to boundary cells', () => {
    const { ti } = make();
    const { col, row } = ti._toCell(-50, 150);
    assert.equal(col, 0);
    assert.equal(row, 0);
  });
});

// ── Dwell debounce ────────────────────────────────────────────────────────────

describe('dwell', () => {
  test('does not fire before threshold', () => {
    const { ti, taps } = make({ dwellFrames: 3 });
    ti.update([{ id: 1, x: 10, y: 0, z: 90 }]);
    ti.update([{ id: 1, x: 10, y: 0, z: 90 }]);
    assert.equal(taps.length, 0);
  });

  test('fires exactly at threshold', () => {
    const { ti, taps } = make({ dwellFrames: 3 });
    ti.update([{ id: 1, x: 10, y: 0, z: 90 }]);
    ti.update([{ id: 1, x: 10, y: 0, z: 90 }]);
    ti.update([{ id: 1, x: 10, y: 0, z: 90 }]);
    assert.equal(taps.length, 1);
  });

  test('fires only once per dwell — not on subsequent frames', () => {
    const { ti, taps } = make({ dwellFrames: 3 });
    for (let i = 0; i < 6; i++) ti.update([{ id: 1, x: 10, y: 0, z: 90 }]);
    assert.equal(taps.length, 1);
  });

  test('resets dwell counter when blob moves to a new cell', () => {
    const { ti, taps } = make({ dwellFrames: 3 });
    ti.update([{ id: 1, x: 5, y: 0, z: 95 }]);  // cell (0,0)
    ti.update([{ id: 1, x: 5, y: 0, z: 95 }]);
    ti.update([{ id: 1, x: 55, y: 0, z: 45 }]); // different cell — resets
    ti.update([{ id: 1, x: 55, y: 0, z: 45 }]);
    assert.equal(taps.length, 0);
    ti.update([{ id: 1, x: 55, y: 0, z: 45 }]);
    assert.equal(taps.length, 1);
  });

  test('fires tap at the correct cell coords', () => {
    const { ti, taps } = make({ dwellFrames: 1 });
    ti.update([{ id: 1, x: 25, y: 0, z: 75 }]); // 25% from left, 25% from top
    assert.deepEqual(taps[0], { col: 1, row: 1 });
  });
});

// ── Multi-blob ────────────────────────────────────────────────────────────────

describe('multi-blob', () => {
  test('tracks two blobs independently', () => {
    const { ti, taps } = make({ dwellFrames: 2 });
    for (let i = 0; i < 2; i++) {
      ti.update([
        { id: 1, x: 10, y: 0, z: 90 }, // col 0, row 0
        { id: 2, x: 90, y: 0, z: 10 }, // col 4, row 4
      ]);
    }
    assert.equal(taps.length, 2);
    assert.deepEqual(taps[0], { col: 0, row: 0 });
    assert.deepEqual(taps[1], { col: 4, row: 4 });
  });

  test('evicts stale blobs so dwell restarts on reappearance', () => {
    const { ti, taps } = make({ dwellFrames: 3 });
    ti.update([{ id: 1, x: 10, y: 0, z: 90 }]);
    ti.update([{ id: 1, x: 10, y: 0, z: 90 }]);
    ti.update([]);                                // blob disappears
    ti.update([{ id: 1, x: 10, y: 0, z: 90 }]); // reappears — dwell restarts
    ti.update([{ id: 1, x: 10, y: 0, z: 90 }]);
    assert.equal(taps.length, 0);
    ti.update([{ id: 1, x: 10, y: 0, z: 90 }]);
    assert.equal(taps.length, 1);
  });
});

// ── resize ────────────────────────────────────────────────────────────────────

describe('resize', () => {
  test('clears dwell state so threshold restarts from zero', () => {
    const { ti, taps } = make({ dwellFrames: 3 });
    ti.update([{ id: 1, x: 25, y: 0, z: 75 }]);
    ti.update([{ id: 1, x: 25, y: 0, z: 75 }]);
    ti.resize(10, 10); // clears dwell — the 2 frames above are discarded
    ti.update([{ id: 1, x: 25, y: 0, z: 75 }]);
    ti.update([{ id: 1, x: 25, y: 0, z: 75 }]);
    assert.equal(taps.length, 0);
    ti.update([{ id: 1, x: 25, y: 0, z: 75 }]);
    assert.equal(taps.length, 1);
  });

  test('remaps blobs to new grid dimensions after resize', () => {
    const { ti, taps } = make({ dwellFrames: 1 });
    ti.resize(10, 10);
    // x=25, z=75 on 10×10 grid: col=2, row=2
    ti.update([{ id: 1, x: 25, y: 0, z: 75 }]);
    assert.deepEqual(taps[0], { col: 2, row: 2 });
  });
});
