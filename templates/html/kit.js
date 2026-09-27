// Product film kit for the HTML engine. Every function here is pure in `t`
// (seconds since the first frame), except boot(), which wires the page up.
// The Remotion engine has TypeScript twins of the maths in templates/remotion/kit/.

// ---------- time ----------
export const clamp01 = v => Math.min(1, Math.max(0, v))
/** 0 before `start`, 1 after `start + length`, linear between. */
export const progress = (t, start, length) => length <= 0 ? (t >= start ? 1 : 0) : clamp01((t - start) / length)
export const mix = (a, b, p) => a + (b - a) * p

/** Seconds at a bar and beat of a measured grid (beats.py). `fraction` is a share of one beat. */
export function at(grid, bar, beat = 1, fraction = 0) {
  const index = (grid.pickupBeats ?? 0) + (bar - 1) * (grid.beatsPerBar ?? 4) + (beat - 1) + fraction
  return grid.firstBeat + index * 60 / grid.bpm
}

// ---------- easing ----------
/** CSS cubic-bezier as a function of 0..1 (Newton on x, then y). */
export function bezier(x1, y1, x2, y2) {
  const cx = 3 * x1, bx = 3 * (x2 - x1) - cx, ax = 1 - cx - bx
  const cy = 3 * y1, by = 3 * (y2 - y1) - cy, ay = 1 - cy - by
  const x = s => ((ax * s + bx) * s + cx) * s, y = s => ((ay * s + by) * s + cy) * s
  const dx = s => (3 * ax * s + 2 * bx) * s + cx
  return p => {
    if (p <= 0) return 0
    if (p >= 1) return 1
    let s = p
    for (let i = 0; i < 8; i++) { const d = dx(s); if (Math.abs(d) < 1e-6) break; s -= (x(s) - p) / d }
    return y(clamp01(s))
  }
}
/** The default landing curve for words and UI: fast out, soft landing. */
export const easeOut = bezier(0.22, 1, 0.36, 1)
/** Eased 0..1 over a window: ease(t, start, length). */
export const ease = (t, start, length, curve = easeOut) => curve(progress(t, start, length))

// ---------- springs ----------
/** Closed-form step response of a damped spring let go at t = 0, moving from 0 toward 1. */
export function step(t, { stiffness, damping, mass = 1 }) {
  if (t <= 0) return 0
  const w = Math.sqrt(stiffness / mass), z = damping / (2 * Math.sqrt(stiffness * mass))
  if (z < 1) { const d = w * Math.sqrt(1 - z * z); return 1 - Math.exp(-z * w * t) * (Math.cos(d * t) + (z * w / d) * Math.sin(d * t)) }
  if (z === 1) return 1 - Math.exp(-w * t) * (1 + w * t)
  const d = w * Math.sqrt(z * z - 1)
  return 1 - Math.exp(-z * w * t) * (Math.cosh(d * t) + (z * w / d) * Math.sinh(d * t))
}
/** A value that retargets at each [time, value, config?] key (keys sorted by time): one spring per change.
 *  A key's own config (third item) overrides the default, so one track can snap, whip and creep. */
export function track(t, keys, config) {
  let value = keys[0][1]
  for (let i = 1; i < keys.length; i++) value += (keys[i][1] - keys[i - 1][1]) * step(t - keys[i][0], keys[i][2] ?? config)
  return value
}
export const glide = { stiffness: 150, damping: 20 }
export const heavy = { stiffness: 120, damping: 30, mass: 1.2 }
/** Camera move vocabulary: snap (a punch, ~0.25 s), whip (line to line, ~0.4 s), creep (a slow build, seconds). */
export const snap = { stiffness: 420, damping: 34 }
export const whip = { stiffness: 300, damping: 30 }
export const creep = { stiffness: 14, damping: 9 }

// ---------- magic moves ----------
/** A rect travelling from `from` to `to`, starting at `start`, on a spring. */
export function move(t, start, from, to, config = glide) {
  const u = step(t - start, config)
  return { x: mix(from.x, to.x, u), y: mix(from.y, to.y, u), w: mix(from.w, to.w, u), h: mix(from.h, to.h, u) }
}
/** Content arriving after a move lands and leaving just before the next: a short blur swap. */
export function swapIn(t, from, to = Infinity, delay = 0.18, out = 0.1) {
  const v = clamp01((t - from - delay) / 0.18) * (1 - (to === Infinity ? 0 : clamp01((t - (to - out)) / out)))
  return { op: v, blur: (1 - v) * 10, vis: v > 0 }
}

// ---------- camera ----------
// The frame the camera films: film.size (or a --size override), set by boot(). fit(), inside() and
// worldTransform() default to it, so one film renders every format.
let W = 1920, H = 1080
/** Camera keys [t, x, y, zoom, spring?] in world units; zoom springs in log space. Each key can
 *  carry its own spring (snap, whip, creep) so a move's character matches its moment. */
export function camera(t, keys, config = heavy) {
  return {
    x: track(t, keys.map(k => [k[0], k[1], k[4]]), config),
    y: track(t, keys.map(k => [k[0], k[2], k[4]]), config),
    zoom: Math.exp(track(t, keys.map(k => [k[0], Math.log(k[3]), k[4]]), config)),
  }
}
/** A camera hold [x, y, zoom] that shows the whole box {x, y, w, h} (world units) with `margin`
 *  px clear of every edge on a w x h frame, zoomed in no further than `cap`. Use it for every hold
 *  on text being read: framing from the text's box never crops a line. Spread into a key:
 *  [t, ...fit(box), whip]. */
export const fit = (box, { w = W, h = H, margin = 70, cap = 3 } = {}) =>
  [box.x + box.w / 2, box.y + box.h / 2, Math.min(cap, (w - 2 * margin) / box.w, (h - 2 * margin) / box.h)]
/** Keep a hold [x, y, zoom] on the content: on each axis, center on `bounds` when the frame is
 *  larger than it, otherwise slide the frame only as far as the bounds' edge. A hold from fit() on
 *  a box inside `bounds` still shows the whole box, but a line near the bottom of the content no
 *  longer drags empty space into the frame. Spread into a key: [t, ...inside(fit(box), bounds), whip]. */
export function inside([x, y, zoom], bounds, { w = W, h = H } = {}) {
  const axis = (v, lo, size, frame) => {
    const half = frame / 2 / zoom
    return size <= 2 * half ? lo + size / 2 : Math.min(lo + size - half, Math.max(lo + half, v))
  }
  return [axis(x, bounds.x, bounds.w, w), axis(y, bounds.y, bounds.h, h), zoom]
}
/** The world-space box of an element's glyphs (trailing spaces and padding excluded). Call at boot:
 *  it clears the world layer's transform while it measures. */
export function textBox(el, world) {
  const saved = world.style.transform
  world.style.transform = 'none'
  const origin = world.getBoundingClientRect(), range = document.createRange()
  range.selectNodeContents(el)
  const rects = [...range.getClientRects()].filter(r => r.width > 0)
  world.style.transform = saved
  const x0 = Math.min(...rects.map(r => r.left)), x1 = Math.max(...rects.map(r => r.right))
  const y0 = Math.min(...rects.map(r => r.top)), y1 = Math.max(...rects.map(r => r.bottom))
  return { x: x0 - origin.left, y: y0 - origin.top, w: x1 - x0, h: y1 - y0 }
}
/** Impact shake at `at`: an offset {x, y} that decays to nothing in about 0.4 s. Add it to the camera. */
export function shake(t, at, { amp = 7, decay = 8 } = {}) {
  if (t < at) return { x: 0, y: 0 }
  const k = amp * Math.exp(-decay * (t - at))
  return { x: k * Math.sin(t * 90), y: 0.7 * k * Math.cos(t * 77) }
}
/** A zoom multiplier that kicks on every beat of the grid between `from` and `to`, so holds never sit dead. */
export function beatKick(t, grid, from, to, { amount = 0.012, decay = 9 } = {}) {
  if (t < from || t >= to) return 1
  const beat = 60 / grid.bpm, since = (t - grid.firstBeat) % beat
  return 1 + amount * Math.exp(-decay * since)
}
/** CSS transform for a world layer (transform-origin 0 0). Never put will-change on it. */
export const worldTransform = (view, w = W, h = H) =>
  `translate(${w / 2}px,${h / 2}px) scale(${view.zoom}) translate(${-view.x}px,${-view.y}px)`

// ---------- cursor ----------
/** A smooth path through timed stops {t, x, y} (Hermite). Stops whose t is in `hold` rest there. */
export function pathAt(stops, t, hold = []) {
  if (t <= stops[0].t) return { x: stops[0].x, y: stops[0].y }
  const last = stops[stops.length - 1]
  if (t >= last.t) return { x: last.x, y: last.y }
  const i = stops.findIndex((s, k) => t >= s.t && t < stops[k + 1].t)
  const p0 = stops[i], p1 = stops[i + 1], span = p1.t - p0.t, u = (t - p0.t) / span
  const vel = (k, a) => hold.includes(stops[k].t) ? 0 : (stops[Math.min(stops.length - 1, k + 1)][a] - stops[Math.max(0, k - 1)][a]) / (stops[Math.min(stops.length - 1, k + 1)].t - stops[Math.max(0, k - 1)].t)
  const h00 = 2 * u ** 3 - 3 * u ** 2 + 1, h10 = u ** 3 - 2 * u ** 2 + u, h01 = -2 * u ** 3 + 3 * u ** 2, h11 = u ** 3 - u ** 2
  const along = a => h00 * p0[a] + h10 * span * vel(i, a) + h01 * p1[a] + h11 * span * vel(i + 1, a)
  return { x: along('x'), y: along('y') }
}
/** Click squash for a cursor: 1 normally, dips to ~0.85 for 0.12 s at each click time. */
export const squash = (t, clicks) => 1 - 0.15 * Math.max(0, ...clicks.map(c => Math.sin(Math.PI * progress(t, c, 0.12)) * (t >= c && t <= c + 0.12)))

// ---------- dither ----------
export const BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]].map(r => r.map(v => (v + 0.5) / 16))
/** Ordered-dither reveal as an SVG path of lit cells (use as clip-path: path("...")). */
export function bayerPath({ width, height, cell, progress: p, sweep = 'up', band = 0.45, x = 0, y = 0 }) {
  if (p <= 0) return ''
  const cols = Math.ceil(width / cell), rows = Math.ceil(height / cell)
  if (p >= 1) return `M${x} ${y}h${cols * cell}v${rows * cell}h${-cols * cell}z`
  const front = p * (1 + band)
  let d = ''
  for (let r = 0; r < rows; r++) for (let c = 0; c < cols; c++) {
    const u = (c + 0.5) / cols, v = (r + 0.5) / rows, radial = Math.min(1, Math.hypot(u - 0.5, v - 0.5) * Math.SQRT2)
    const pos = { up: 1 - v, down: v, left: 1 - u, right: u, out: radial, in: 1 - radial }[sweep]
    if (BAYER[r & 3][c & 3] < clamp01((front - pos) / band)) d += `M${x + c * cell} ${y + r * cell}h${cell}v${cell}h${-cell}z`
  }
  return d
}

// ---------- voice ----------
const plain = s => s.toLowerCase().replace(/[^\p{L}\p{N}]/gu, '')
/**
 * Film seconds at which a voice line says a word: wordAt(film, 'v2', 'SAP').
 * `nth` picks a repeat; `edge` 'start' or 'end'. Throws if the word is not in the line,
 * so a script edit that drops a cue word fails loudly instead of drifting.
 */
export function wordAt(film, id, word, { nth = 1, edge = 'start' } = {}) {
  const line = film.voice.lines.find(l => l.id === id)
  const hits = (line?.words ?? []).filter(w => plain(w.w) === plain(word))
  if (!hits[nth - 1]) throw new Error(`"${word}" (#${nth}) not in voice line ${id}`)
  return line.at + hits[nth - 1][edge]
}
/** Start and end of a whole voice line in film seconds. */
export function lineSpan(film, id) {
  const line = film.voice.lines.find(l => l.id === id)
  return { start: line.at, end: line.at + (line.words?.at(-1)?.end ?? 0) }
}

// ---------- color ----------
const rgb = h => [1, 3, 5].map(i => parseInt(h.slice(i, i + 2), 16))
/** A color between two hex tokens, for anything that animates color (CSS color-mix cannot tween). */
export const mixHex = (a, b, p) => `rgb(${rgb(a).map((v, i) => Math.round(mix(v, rgb(b)[i], clamp01(p)))).join(',')})`

// ---------- third-party animation, driven by t ----------
/** A Lottie file (After Effects via Bodymovin, or LottieFiles) as a clip on the film's clock.
 *  Pass the `lottie` global from lottie-web's build/player/lottie_svg.min.js. It seeks by frame, not
 *  time: lottie-web's time argument is in milliseconds whatever its docs say, and frames leave no
 *  doubt. Add `clip.ready` to boot's wait list so frame 0 is never drawn before the file loads.
 *  clip.at(t, start, speed) shows the frame for film time t; before `start` it holds frame 0. */
export function lottieClip(lottie, container, path) {
  const anim = lottie.loadAnimation({ container, path, renderer: 'svg', loop: false, autoplay: false })
  const ready = new Promise((ok, fail) => { anim.addEventListener('DOMLoaded', ok); anim.addEventListener('data_failed', () => fail(new Error(`lottie: could not load ${path}`))) })
  return {
    anim, ready,
    at(t, start = 0, speed = 1) {
      const last = anim.totalFrames - 1
      anim.goToAndStop(Math.min(last, Math.max(0, (t - start) * speed * anim.frameRate)), true)
    },
  }
}
/** A GSAP timeline on the film's clock. Build it once, paused (gsap.timeline({ paused: true })), then
 *  call this from render(t). seek() sets every tweened value for that moment and fires no callbacks,
 *  so a frame drawn cold matches one drawn in sequence. Loose gsap.to() tweens run on GSAP's own
 *  ticker: put every tween on a paused timeline. */
export const gsapAt = (timeline, t, start = 0) => timeline.seek(Math.max(0, t - start), true)

// ---------- DOM ----------
export const $ = id => document.getElementById(id)
/** Set transform, opacity, blur and visibility on an element (or id) in one call. */
export function set(el, o) {
  const s = (typeof el === 'string' ? $(el) : el).style
  const tr = []
  if (o.x != null || o.y != null) tr.push(`translate(${o.x ?? 0}px,${o.y ?? 0}px)`)
  if (o.s != null) tr.push(`scale(${o.s})`)
  if (o.r != null) tr.push(`rotate(${o.r}deg)`)
  if (o.tr) tr.push(o.tr)
  if (tr.length) s.transform = tr.join(' ')
  if (o.op != null) s.opacity = o.op
  if (o.blur != null) s.filter = o.blur > 0.05 ? `blur(${o.blur}px)` : 'none'
  if (o.vis != null) s.visibility = o.vis ? 'visible' : 'hidden'
}

/**
 * Load film.json (and the voice word timings eleven.py wrote), then expose
 * window.render(t) and window.ready for film.mjs. Hash modes for the browser:
 *   #play       live preview with audio/mix.wav if it exists
 *   #t=12.4     hold one frame
 */
export async function boot(render, { wait = [] } = {}) {
  const film = await (await fetch('film.json', { cache: 'no-store' })).json()
  // film.mjs passes its size (--size 1080x1920, or film.json's); in the browser, /?size=1080x1920#play
  ;[W, H] = film.size = new URLSearchParams(location.search).get('size')?.split('x').map(Number) ?? film.size ?? [W, H]
  document.documentElement.style.setProperty('--w', `${W}px`)
  document.documentElement.style.setProperty('--h', `${H}px`)
  for (const line of film.voice?.lines ?? []) {
    const r = await fetch(`audio/vo/${line.id}.json`, { cache: 'no-store' })
    if (r.ok) line.words = (await r.json()).words
  }
  const draw = t => render(t, film)
  window.film = film
  window.render = draw
  // `wait`: anything else frame 0 depends on, such as lottieClip(...).ready
  window.ready = Promise.all([document.fonts.ready, ...[...document.images].map(i => i.decode().catch(() => {})), ...wait])
  await window.ready
  const hold = location.hash.match(/^#t=([\d.]+)/)
  if (location.hash === '#play') {
    const audio = new Audio('audio/mix.wav')
    let t0 = performance.now(), withAudio = false
    audio.addEventListener('canplaythrough', () => { withAudio = true; audio.loop = !!film.loop; audio.play().catch(() => { withAudio = false }) }, { once: true })
    addEventListener('click', () => { t0 = performance.now(); audio.currentTime = 0; audio.play().then(() => { withAudio = true }).catch(() => {}) })
    const loop = () => {
      const t = withAudio ? audio.currentTime : (performance.now() - t0) / 1000
      draw(film.loop ? t % film.duration : Math.min(t, film.duration))
      requestAnimationFrame(loop)
    }
    loop()
  } else draw(hold ? +hold[1] : 0)
  return film
}
