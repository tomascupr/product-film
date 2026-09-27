// The kit's camera and color maths. Run: node --test tests/
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { camera, fit, inside, shake, beatKick, mixHex, snap, creep } from '../templates/html/kit.js'

test('fit frames the whole box inside the margin, capped', () => {
  const [x, y, zoom] = fit({ x: 100, y: 200, w: 500, h: 80 }, { w: 1080, h: 1080, margin: 70, cap: 3 })
  assert.deepEqual([x, y], [350, 240])
  assert.equal(zoom, 940 / 500)
  assert.equal(fit({ x: 0, y: 0, w: 10, h: 10 }, { w: 1080, h: 1080, cap: 2 })[2], 2)
})

test('camera keys carry their own spring', () => {
  const keys = [[0, 0, 0, 1], [1, 100, 0, 2, snap], [3, 100, 0, 1, creep]]
  const settled = camera(2.5, keys)
  assert.ok(Math.abs(settled.x - 100) < 0.5 && Math.abs(settled.zoom - 2) < 0.02)
  // 0.3 s after their keys, a snap has nearly arrived and a creep has not
  const share = (v, from, to) => (v - from) / (to - from)
  assert.ok(share(camera(1.3, keys).x, 0, 100) > 0.9)
  assert.ok(share(Math.log(camera(3.3, keys).zoom), Math.log(2), 0) < 0.6)
})

test('shake decays to nothing and starts at its hit', () => {
  assert.deepEqual(shake(0.5, 1), { x: 0, y: 0 })
  assert.ok(Math.abs(shake(2, 1).x) < 0.01)
})

test('beatKick peaks on each beat inside its window only', () => {
  const grid = { bpm: 120, firstBeat: 0 }
  assert.ok(beatKick(1.001, grid, 0, 4) > 1.01)
  assert.ok(beatKick(1.4, grid, 0, 4) < 1.001)
  assert.equal(beatKick(5, grid, 0, 4), 1)
})

test('mixHex blends hex tokens and clamps', () => {
  assert.equal(mixHex('#000000', '#ffffff', 0.5), 'rgb(128,128,128)')
  assert.equal(mixHex('#000000', '#ffffff', 2), 'rgb(255,255,255)')
})

test('inside centers small content and keeps a fitted box whole near the edge', () => {
  const bounds = { x: 0, y: 200, w: 1080, h: 660 }, frame = { w: 1080, h: 1080 }
  // the frame is taller than the content: center on it, whatever line was fitted
  assert.equal(inside([540, 700, 1.05], bounds, frame)[1], 530)
  // the frame is shorter: a low line slides the frame up to the content's bottom edge, not past it
  const box = { x: 100, y: 780, w: 400, h: 72 }
  const [, y, zoom] = inside(fit(box, { ...frame, cap: 2.5 }), bounds, frame)
  const top = y - 540 / zoom, bottom = y + 540 / zoom
  assert.equal(bottom, 860)
  assert.ok(box.y >= top && box.y + box.h <= bottom)
})
