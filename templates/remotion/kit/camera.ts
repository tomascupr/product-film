import { track, type SpringConfig } from "./spring";

/** The frame the camera films. Change for 9:16 or other sizes. */
export const FRAME = { width: 1920, height: 1080 } as const;

/** Camera keys in world units: the world point at the frame's center, and the zoom. */
export type CameraKey = readonly [time: number, x: number, y: number, zoom: number, spring?: SpringConfig];
export type Camera = { x: number; y: number; zoom: number };

/** Slow, heavy, no overshoot: a camera that feels held, not thrown. */
export const cameraSpring: SpringConfig = { damping: 30, mass: 1.2, stiffness: 120 };
/** Move vocabulary: snap (a punch, ~0.25 s), whip (line to line, ~0.4 s), creep (a slow build, seconds). */
export const snap: SpringConfig = { stiffness: 420, damping: 34 };
export const whip: SpringConfig = { stiffness: 300, damping: 30 };
export const creep: SpringConfig = { stiffness: 14, damping: 9 };

/** The camera at time t. Zoom springs in log space, so a push reads the same at any scale. */
export function camera(t: number, keys: readonly CameraKey[], config: SpringConfig = cameraSpring): Camera {
  return {
    x: track(t, keys.map(([time, x, , , s]) => [time, x, s] as const), config),
    y: track(t, keys.map(([time, , y, , s]) => [time, y, s] as const), config),
    zoom: Math.exp(track(t, keys.map(([time, , , zoom, s]) => [time, Math.log(zoom), s] as const), config)),
  };
}

/** A hold [x, y, zoom] that shows the whole box (world units) `margin` px clear of every edge,
 *  zoomed no further than `cap`. Use it for every hold on text being read, so no line is cropped. */
export function fit(box: { x: number; y: number; w: number; h: number }, { margin = 70, cap = 3 } = {}) {
  return [box.x + box.w / 2, box.y + box.h / 2,
    Math.min(cap, (FRAME.width - 2 * margin) / box.w, (FRAME.height - 2 * margin) / box.h)] as const;
}

/** Keep a hold on the content: per axis, center on `bounds` when the frame is larger, else slide
 *  only as far as the bounds' edge. A fitted box inside `bounds` stays whole. */
export function inside([x, y, zoom]: readonly [number, number, number], bounds: { x: number; y: number; w: number; h: number }) {
  const axis = (v: number, lo: number, size: number, frame: number) => {
    const half = frame / 2 / zoom;
    return size <= 2 * half ? lo + size / 2 : Math.min(lo + size - half, Math.max(lo + half, v));
  };
  return [axis(x, bounds.x, bounds.w, FRAME.width), axis(y, bounds.y, bounds.h, FRAME.height), zoom] as const;
}

/** Impact shake at `at`: an offset that decays to nothing in about 0.4 s. Add it to the camera. */
export function shake(t: number, at: number, { amp = 7, decay = 8 } = {}) {
  if (t < at) return { x: 0, y: 0 };
  const k = amp * Math.exp(-decay * (t - at));
  return { x: k * Math.sin(t * 90), y: 0.7 * k * Math.cos(t * 77) };
}

/** A zoom multiplier that kicks on every beat between `from` and `to`, so holds never sit dead. */
export function beatKick(t: number, grid: { bpm: number; firstBeat: number }, from: number, to: number, { amount = 0.012, decay = 9 } = {}) {
  if (t < from || t >= to) return 1;
  const since = (t - grid.firstBeat) % (60 / grid.bpm);
  return 1 + amount * Math.exp(-decay * since);
}

/** Screen position of a world point. */
export function project(view: Camera, x: number, y: number) {
  return { x: FRAME.width / 2 + (x - view.x) * view.zoom, y: FRAME.height / 2 + (y - view.y) * view.zoom };
}

/** CSS transform for a world layer (transform-origin 0 0). Never add will-change to it. */
export function worldTransform(view: Camera) {
  return `translate(${FRAME.width / 2}px, ${FRAME.height / 2}px) scale(${view.zoom}) translate(${-view.x}px, ${-view.y}px)`;
}
