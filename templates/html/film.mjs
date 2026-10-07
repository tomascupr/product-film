// The HTML engine's harness: serve the film, take stills, measure targets, render.
//
//   node film.mjs serve [--port 4173]                 preview at /#play, one frame at /#t=12.4
//   node film.mjs stills <dir> <seconds>... [--cues]  PNG per time, plus sheet.png (sheet-N.png past 16 frames)
//   node film.mjs measure <seconds>                   JSON boxes of every [data-target]
//   node film.mjs check <seconds>... [--cues] [--cold] [--view 390] [--min 10]
//                                                     text too small at the viewing width, covered, overlapping
//                                                     or off frame; out/check/<t>.png at that width to look at.
//                                                     --cold: a frame that changes with what was drawn before it
//   node film.mjs render <name> [--blur [N]] [--segments [s]] [--scale 0.5] [--from s] [--to s] [--webm] [--poster s] [--muted] [--workers 4]
//                                                     -> out/<name>/<name>.mp4 (+ -muted.mp4, .webm, -poster.jpg,
//                                                        -cover-300.png: frame 0 at thumbnail size, with its text checked)
//
// --cues on stills or check adds the film's own moments to the times given: frame 0, every film.json cue,
// and the middle and last word of every voice line.
// --size 1080x1920 on stills, measure, check or render draws the same film at another size (film.json size
// by default), so each format of one timeline renders from one folder, in parallel under its own name.
//
// render: headless Chrome steps window.render(t) frame by frame and pipes PNGs into
// ffmpeg. --blur renders N subframes per frame (4 by default) and averages them: motion blur, N times slower.
// Colors: screenshots are sRGB; ffmpeg converts once to BT.709 limited range and tags it,
// so dark backgrounds do not come back lifted. Muxes audio/mix.wav when it exists.
// --segments renders s seconds of film at a time in fresh browsers (10 when bare) and joins the pieces: a
// long blurred render can stall in a browser that runs too long. A finished render replaces the one before
// it; a failed one leaves it alone.
import { chromium } from 'playwright-core'
import { spawn } from 'node:child_process'
import { createServer } from 'node:http'
import { existsSync, mkdirSync, readFileSync, renameSync, rmSync, statSync, writeFileSync } from 'node:fs'
import { extname, join, resolve } from 'node:path'

const [cmd, ...rest] = process.argv.slice(2)
const flags = {}, args = [], SWITCHES = ['cues', 'cold', 'webm', 'muted'] // these take no value, so a time after one stays a time
for (let i = 0; i < rest.length; i++) {
  if (!rest[i].startsWith('--')) { args.push(rest[i]); continue }
  const name = rest[i].slice(2), next = rest[i + 1]
  flags[name] = SWITCHES.includes(name) || next === undefined || next.startsWith('--') ? true : (i++, next)
}
const root = process.cwd()
const film = JSON.parse(readFileSync(join(root, 'film.json'), 'utf8'))
const [W, H] = flags.size?.split('x').map(Number) ?? film.size ?? [1920, 1080]
const FPS = film.fps ?? 60

const types = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.json': 'application/json', '.css': 'text/css', '.svg': 'image/svg+xml', '.png': 'image/png', '.jpg': 'image/jpeg', '.webp': 'image/webp', '.woff2': 'font/woff2', '.woff': 'font/woff', '.ttf': 'font/ttf', '.otf': 'font/otf', '.mp3': 'audio/mpeg', '.wav': 'audio/wav', '.mp4': 'video/mp4' }
function serve(port = 0) {
  const server = createServer((req, res) => {
    const path = resolve(root, '.' + decodeURIComponent(new URL(req.url, 'http://x').pathname).replace(/\/$/, '/index.html'))
    if (!path.startsWith(root) || !existsSync(path) || statSync(path).isDirectory()) { res.writeHead(404).end(); return }
    res.writeHead(200, { 'content-type': types[extname(path)] ?? 'application/octet-stream', 'cache-control': 'no-store' }).end(readFileSync(path))
  })
  return new Promise(ok => server.listen(port, '127.0.0.1', () => ok(server)))
}

async function open(browser, url, scale = 1) {
  const page = await browser.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: scale })
  page.on('pageerror', e => { pageError ??= e })
  page.on('console', m => m.type() === 'error' && console.error('console:', m.text(), m.location()?.url ?? ''))
  // An error while the page loads (a bad import, a missing file) would otherwise surface as a silent
  // 30 s timeout; race it so the run stops at once with the page's own message.
  const failed = new Promise((_, fail) => page.once('pageerror', e => fail(new Error(`page error while loading: ${e.message}`))))
  await page.goto(url)
  await Promise.race([page.waitForFunction(() => window.ready), failed])
  await page.evaluate(() => window.ready)
  if (pageError) throw new Error(`page error: ${pageError.message}`)
  return page
}

function ffmpeg(list) {
  const p = spawn(process.env.FFMPEG ?? 'ffmpeg', ['-v', 'error', '-y', ...list], { stdio: ['pipe', 'inherit', 'inherit'] })
  const done = new Promise((ok, fail) => p.on('close', c => c ? fail(new Error(`ffmpeg exited ${c}`)) : ok()))
  // A write after ffmpeg has gone is not the error; `done` carries the reason to whoever awaits it.
  done.catch(() => {}); p.stdin.on('error', () => {})
  return { stdin: p.stdin, done, kill: () => p.kill('SIGKILL') }
}

// An error inside the page (a missing cue word, a typo) stops the run with its own message.
let pageError
async function draw(page, t) {
  const threw = await page.evaluate(async t => { try { await window.render(t) } catch (e) { return e?.stack ?? String(e) } }, t)
  if (threw) pageError ??= new Error(`render(${t}): ${threw}`)
  if (pageError) throw new Error(`page error: ${pageError.message}`)
}

// --cues: the film's own moments, so every look and check covers the same set.
function moments() {
  const found = new Map([[0, ['frame 0, the cover']]])
  const add = (t, why) => { t = +t.toFixed(2); if (t >= 0 && t < film.duration) found.set(t, [...(found.get(t) ?? []), why]) }
  for (const [name, t] of Object.entries(film.cues ?? {})) if (typeof t === 'number') add(t, `cue ${name}`)
  for (const line of film.voice?.lines ?? []) {
    const file = join(root, 'audio', 'vo', `${line.id}.json`)
    const last = existsSync(file) ? JSON.parse(readFileSync(file, 'utf8')).words?.at(-1) : null
    // "said" is inside the last word: at its end the next line may already be starting
    if (last) { add(line.at + last.end / 2, `${line.id} halfway`); add(line.at + (last.start + last.end) / 2, `${line.id} said: ${line.text}`) }
  }
  return [...found].sort((a, b) => a[0] - b[0]).map(([t, why]) => ({ t, why: why.join(' · ') }))
}
// The times a command looks at: the ones given, in their order, then with --cues the film's moments.
const timesOf = given => [...given.map(t => ({ t: +t, why: '' })), ...(flags.cues ? moments().filter(m => !given.some(g => +g === m.t)) : [])]

// How far two screenshots of one frame are apart: the share of the frame off by more than 24 levels (something
// moved, showed or hid), the share off by more than 4 (a faint layer), and the box around those.
const differ = (page, a, b) => page.evaluate(async ({ a, b }) => {
  const pixels = async s => {
    const img = await createImageBitmap(new Blob([Uint8Array.from(atob(s), c => c.charCodeAt(0))], { type: 'image/png' }))
    const g = new OffscreenCanvas(img.width, img.height).getContext('2d')
    g.drawImage(img, 0, 0)
    return g.getImageData(0, 0, img.width, img.height)
  }
  const [A, B] = [await pixels(a), await pixels(b)], w = A.width
  let strong = 0, faint = 0, x0 = w, y0 = A.height, x1 = 0, y1 = 0
  for (let i = 0; i < A.data.length; i += 4) {
    const d = Math.max(Math.abs(A.data[i] - B.data[i]), Math.abs(A.data[i + 1] - B.data[i + 1]), Math.abs(A.data[i + 2] - B.data[i + 2]))
    if (d <= 4) continue
    const x = (i / 4) % w, y = Math.floor(i / 4 / w)
    faint++; strong += d > 24; x0 = Math.min(x0, x); x1 = Math.max(x1, x); y0 = Math.min(y0, y); y1 = Math.max(y1, y)
  }
  return { strong: strong / (w * A.height), faint: faint / (w * A.height), box: `x ${x0}-${x1}, y ${y0}-${y1}` }
}, { a: a.toString('base64'), b: b.toString('base64') })

// Text on the current frame that is too small at the viewing width, covered, overlapping or off frame.
async function inspect(page, view, min) {
  await page.addStyleTag({ content: '* { pointer-events: auto !important }' }) // elementsFromPoint skips pointer-events: none
  return page.evaluate(({ W, H, k, min }) => {
    const alpha = el => { let a = 1; for (let e = el; e; e = e.parentElement) a *= +getComputedStyle(e).opacity; return a }
    const shown = el => el.checkVisibility({ visibilityProperty: true }) && alpha(el) > 0.1
    const paints = el => { const c = getComputedStyle(el)
      return el instanceof SVGElement || /^(IMG|CANVAS|VIDEO)$/.test(el.tagName) || !/rgba\(.*,\s*0\)|transparent/.test(c.backgroundColor) || c.backgroundImage !== 'none' }
    const label = el => el.id ? '#' + el.id : el.tagName.toLowerCase()
    // what an ancestor with overflow clipping lets through
    const clip = (el, r) => { let [l, t, rr, b] = [r.left, r.top, r.right, r.bottom]
      for (let e = el.parentElement; e; e = e.parentElement) if (getComputedStyle(e).overflow !== 'visible') {
        const c = e.getBoundingClientRect(); l = Math.max(l, c.left); t = Math.max(t, c.top); rr = Math.min(rr, c.right); b = Math.min(b, c.bottom) }
      return rr - l > 1 && b - t > 1 ? { left: l, top: t, right: rr, bottom: b, width: rr - l, height: b - t } : null }
    // per sample point: 'clear', or the painted elements on top of the text
    const grid = r => { const n = Math.min(24, Math.max(3, Math.ceil(r.width / (r.height * .4))))
      return [.3, .7].flatMap(fy => Array.from({ length: n }, (_, i) => [(i + .5) / n, fy])) }
    const probe = (el, r) => grid(r).map(([fx, fy]) => {
      const x = r.left + r.width * fx, y = r.top + r.height * fy
      if (x < 0 || y < 0 || x >= W || y >= H) return null
      const over = []
      for (const e of document.elementsFromPoint(x, y)) {
        if (e === el || el.contains(e) || e.contains(el)) return over.length ? over : 'clear'
        if (paints(e) && shown(e)) over.push(label(e))
      }
      return null })
    const texts = [], out = { small: [], covered: [], frame: [], overlap: [] }
    const walk = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT)
    for (let n; (n = walk.nextNode());) {
      const el = n.parentElement, text = n.textContent.trim()
      if (!text || !el || !shown(el)) continue
      const range = document.createRange(); range.selectNodeContents(n)
      const raw = [...range.getClientRects()].filter(r => r.width > 0)
      const rects = raw.map(r => clip(el, r)).filter(Boolean)
      const probes = rects.flatMap(r => probe(el, r))
      if (!probes.includes('clear')) continue // hidden: clipped away or under another layer
      const scale = el.offsetWidth ? el.getBoundingClientRect().width / el.offsetWidth : 1
      const x = { el, text: `"${text.slice(0, 40)}"`, rects, px: parseFloat(getComputedStyle(el).fontSize) * scale * k }
      texts.push(x)
      if (x.px < min) out.small.push(`${x.text} ${x.px.toFixed(1)} px`)
      const over = [...new Set(probes.filter(Array.isArray).flat())]
      if (over.length) out.covered.push(`${x.text} under ${over.join(', ')}`)
      // cropped by the frame edge: test the unclipped glyph boxes (the stage's overflow would hide the crop)
      if (raw.some(r => r.left < -1 || r.top < -1 || r.right > W + 1 || r.bottom > H + 1)) out.frame.push(x.text)
    }
    for (let i = 0; i < texts.length; i++) for (let j = i + 1; j < texts.length; j++) {
      const a = texts[i], b = texts[j]
      if (a.el.contains(b.el) || b.el.contains(a.el)) continue
      // line boxes carry ascent and descent room; compare roughly the glyphs (the middle 60%)
      const g = r => ({ ...r, top: r.top + r.height * .2, bottom: r.bottom - r.height * .2 })
      if (a.rects.map(g).some(p => b.rects.map(g).some(q => {
        const w = Math.min(p.right, q.right) - Math.max(p.left, q.left), h = Math.min(p.bottom, q.bottom) - Math.max(p.top, q.top)
        return w > 0 && h > 0 && w * h > 0.2 * Math.min(p.width * p.height, q.width * q.height)
      }))) out.overlap.push(`${a.text} and ${b.text}`)
    }
    return out
  }, { W, H, k: view / W, min })
}

const launch = (args = []) => chromium.launch({ ...(process.env.CHROME_PATH ? { executablePath: process.env.CHROME_PATH } : { channel: 'chrome' }), args })

if (cmd === 'serve') {
  const server = await serve(+(flags.port ?? 4173))
  console.log(`http://127.0.0.1:${server.address().port}/#play   (one frame: /#t=12.4)`)
} else if (['stills', 'measure', 'check', 'render'].includes(cmd)) {
  const server = await serve()
  const url = `http://127.0.0.1:${server.address().port}/?size=${W}x${H}` // the page draws at the viewport's size
  const browser = await launch()
  try {
    if (cmd === 'stills') {
      const [dir, ...given] = args, times = timesOf(given)
      if (!dir || !times.length) throw new Error('usage: node film.mjs stills <dir> <seconds>... [--cues]')
      mkdirSync(dir, { recursive: true })
      const page = await open(browser, url)
      for (const [i, { t, why }] of times.entries()) {
        await draw(page, t)
        const file = join(dir, `${String(i).padStart(3, '0')}.png`)
        await page.screenshot({ path: file })
        console.log(`${file}  t=${t}${why && '  ' + why}`)
      }
      if (times.length > 1) {
        // 16 frames a sheet at most, so each stays big enough to read
        const many = times.length > 16, cols = Math.min(4, times.length), rows = many ? 4 : Math.ceil(times.length / cols)
        const sheet = ffmpeg(['-framerate', '1', '-i', join(dir, '%03d.png'), '-vf', `scale=480:-1,tile=${cols}x${rows}:padding=4:color=0x333333`,
          ...(many ? ['-fps_mode', 'passthrough', join(dir, 'sheet-%d.png')] : ['-frames:v', '1', join(dir, 'sheet.png')])])
        sheet.stdin.end(); await sheet.done
        if (many) for (let k = 0; k < times.length; k += 16) console.log(`${join(dir, `sheet-${k / 16 + 1}.png`)}  t=${times[k].t} to ${times[Math.min(k + 15, times.length - 1)].t}, row by row`)
        else console.log(join(dir, 'sheet.png'))
      }
    } else if (cmd === 'measure') {
      const page = await open(browser, url)
      await draw(page, +(args[0] ?? 0))
      const boxes = await page.evaluate(() => {
        return Object.fromEntries([...document.querySelectorAll('[data-target]')].map(el => {
          const r = el.getBoundingClientRect()
          return [el.dataset.target, { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) }]
        }))
      })
      console.log(JSON.stringify(boxes, null, 1))
    } else if (cmd === 'check') {
      const times = timesOf(args)
      if (!times.length) throw new Error('usage: node film.mjs check <seconds>... [--cues] [--cold] [--view 390] [--min 10]')
      // --view: the width the film is watched at in CSS px (a phone feed is about 390). --min: smallest readable text there.
      const view = +(flags.view ?? 390), min = +(flags.min ?? 10), dir = join(root, 'out', 'check')
      mkdirSync(dir, { recursive: true })
      const page = await open(browser, url), shot = { scale: 'css', clip: { x: 0, y: 0, width: W, height: H } }
      let total = 0
      for (const { t, why } of times) {
        await draw(page, t)
        const issues = await inspect(page, view, min)
        const file = join(dir, `${t.toFixed(2)}.png`)
        await page.screenshot({ path: file, ...shot })
        const small = ffmpeg(['-i', file, '-vf', `scale=${view}:-1:flags=area`, file.replace('.png', '-view.png')]); small.stdin.end(); await small.done
        if (flags.cold) {
          // The frame in a fresh page against the same frame in this one, which has drawn others: after the time
          // before it in the list, after the frame before it, and after one from the far side of the film.
          // They differ when render(t) leans on what an earlier frame left behind, and then renders disagree too.
          const fresh = await open(browser, url)
          await draw(fresh, t)
          const cold = await fresh.screenshot(shot)
          let warm = readFileSync(file)
          for (const before of [null, Math.max(0, t - 1 / FPS), (t + film.duration / 2) % film.duration]) {
            if (before !== null) { await draw(page, before); await draw(page, t); warm = await page.screenshot(shot) }
            const d = await differ(fresh, cold, warm)
            // Raster dust stays under both marks: over a 48 s film with camera zooms on text, the worst frame
            // had 0.03% of its pixels past 4 levels and none past 24.
            if (d.strong < 0.0002 && d.faint < 0.005) continue
            writeFileSync(file.replace('.png', '-cold.png'), cold); writeFileSync(file.replace('.png', '-warm.png'), warm)
            issues.cold = [`${(d.faint * 100).toFixed(2)}% of the frame differs at ${d.box}: compare ${file.replace('.png', '-cold.png')} with -warm.png`]
            break
          }
          await fresh.close()
        }
        const count = Object.values(issues).flat().length
        console.log(`t=${t}  ${count ? count + ' issue(s)' : 'clean'}  ${file.replace('.png', '-view.png')}${why && '  ' + why}`)
        for (const [kind, list] of Object.entries(issues)) if (list.length)
          console.log(`  ${kind} (${list.length}): ${list.slice(0, 6).join(' · ')}${list.length > 6 ? ` · +${list.length - 6} more` : ''}`)
        total += count
      }
      if (total) process.exitCode = 1
    } else {
      const [name] = args
      if (!name) throw new Error('usage: node film.mjs render <name> [--blur [N]] [--segments [s]] [--scale 0.5] [--from s] [--to s] [--webm] [--poster s]')
      const sub = flags.blur === true ? 4 : Math.max(1, Math.round(+(flags.blur ?? 1)) || 1), scale = +(flags.scale ?? 1), workers = +(flags.workers ?? 4)
      const from = +(flags.from ?? 0), to = +(flags.to ?? film.duration)
      const f0 = Math.round(from * FPS), f1 = Math.round(to * FPS)
      if (!(f1 > f0)) throw new Error(`nothing to render from ${from} to ${to} s`)
      // Parts are whole frames, so each frame's subframes stay in one part and the join shows no seam.
      const span = flags.segments ? Math.max(1, Math.round((flags.segments === true ? 10 : +flags.segments) * FPS)) : f1 - f0
      const bounds = []
      for (let a = f0; a < f1; a += span) bounds.push([a, Math.min(f1, a + span)])
      const outDir = join(root, 'out', name), tmp = join(outDir, '.parts')
      rmSync(tmp, { recursive: true, force: true }); mkdirSync(tmp, { recursive: true })
      const file = join(outDir, `${name}.mp4`), partName = k => `${String(k).padStart(3, '0')}.mp4`
      const mixWav = join(root, 'audio', 'mix.wav')
      const audio = existsSync(mixWav) && !flags.muted
      const blur = sub > 1 ? `tmix=frames=${sub},select='not(mod(n+1\\,${sub}))',setpts=N/(${FPS}*TB),` : ''
      const wait = () => new Promise(r => setTimeout(r, 5))
      const started = Date.now()
      // Chrome's fast PNG: the same pixels as page.screenshot, about four times quicker at 1080p. It comes
      // through a CDP session of our own, which a browser among several sometimes served at its window's shape
      // rather than the viewport. A clip hides that as wrong pixels; unclipped it shows as a wrong size, which
      // fails the part (ffmpeg would drop frames without a word) and is probed for before a browser renders.
      // Unclipped it also ignores --scale, so a scaled draft keeps Playwright's screenshot.
      const fast = scale === 1
      const shot = async ({ page, cdp }, i) => {
        if (!fast) return page.screenshot({ type: 'png' })
        const png = Buffer.from((await cdp.send('Page.captureScreenshot', { format: 'png', optimizeForSpeed: true })).data, 'base64')
        const got = [png.readUInt32BE(16), png.readUInt32BE(20)]
        if (got[0] !== W || got[1] !== H) throw new Error(`frame ${i} came back ${got.join('x')}, not ${W}x${H}`)
        return png
      }
      // Frames a to b of the film into a video-only file, each worker in a browser of its own:
      // pages in one browser share its compositor, and four of them barely beat one.
      const part = async (out, a, b) => {
        const own = []
        try {
          // Open the pages first: a page error then stops the run before ffmpeg starts. A browser whose first
          // capture comes back the wrong size is swapped for a new one, up to three times.
          // allSettled: every browser is in `own` before a failure reaches `finally`, so none is left running.
          const opened = await Promise.allSettled(Array.from({ length: workers }, async () => {
            for (let tries = 0; ; tries++) {
              const browser = await launch(); own.push(browser)
              const page = await open(browser, url, scale), cdp = await page.context().newCDPSession(page), worker = { page, cdp }
              try { if (fast) await shot(worker, 'probe'); return worker } catch (e) { if (tries === 2) throw e; console.log(`${e.message}; a new browser`) }
              await browser.close(); own.splice(own.indexOf(browser), 1)
            }
          }))
          const stuck = opened.find(o => o.status === 'rejected')
          if (stuck) throw stuck.reason
          const pages = opened.map(o => o.value)
          const enc = ffmpeg([
            '-f', 'image2pipe', '-framerate', String(FPS * sub), '-i', '-',
            // setparams tags primaries and transfer too; output flags alone leave them 'unknown'.
            '-vf', `${blur}scale=out_color_matrix=bt709:out_range=tv:flags=lanczos,format=yuv420p,setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709:range=tv`,
            '-r', String(FPS), '-c:v', 'libx264', '-preset', 'slow', '-crf', '16',
            '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709', '-color_range', 'tv', '-an', out,
          ])
          // Workers render interleaved frames; the writer drains them in order.
          // ponytail: frames buffer in memory up to AHEAD per worker; lower it if RAM is tight at 4K.
          const AHEAD = 24, done = new Map(), n1 = b * sub
          let next = a * sub, failed = false
          try { await Promise.all(pages.map(async (worker, k) => {
            for (let i = a * sub + k; i < n1 && !failed; i += workers) {
              while (i - next > AHEAD * workers && !failed) await wait()
              await draw(worker.page, i / (FPS * sub))
              done.set(i, await shot(worker, i))
              while (done.has(next)) {
                const buf = done.get(next); done.delete(next); next++
                // Wait for ffmpeg to take it, or to die: its exit is then the error, not a drain that never comes.
                if (!enc.stdin.write(buf)) await Promise.race([new Promise(r => enc.stdin.once('drain', r)), enc.done])
                if ((next - f0 * sub) % (FPS * sub * 5) === 0) console.log(`${((next - f0 * sub) / (FPS * sub)).toFixed(0)} s rendered, ${((Date.now() - started) / 1000).toFixed(0)} s elapsed`)
              }
            }
          })) } catch (e) { failed = true; enc.kill(); throw e }
          enc.stdin.end(); await enc.done
        } finally { await Promise.all(own.map(browser => browser.close())) }
      }
      try {
        for (const [k, [a, b]] of bounds.entries()) {
          for (let tries = 0; ; tries++) {
            try { await part(join(tmp, partName(k)), a, b); break } catch (e) {
              // A stalled or crashed browser is worth one more go in a new one; the film's own error is not.
              if (tries || pageError) throw e
              console.log(`${(a / FPS).toFixed(1)} to ${(b / FPS).toFixed(1)} s failed (${e.message.split('\n')[0]}); once more in a fresh browser`)
            }
          }
        }
        writeFileSync(join(tmp, 'list.txt'), bounds.map((_, k) => `file '${partName(k)}'\n`).join(''))
        const joined = join(tmp, 'joined.mp4')
        const mux = ffmpeg([
          ...(bounds.length > 1 ? ['-f', 'concat', '-i', join(tmp, 'list.txt')] : ['-i', join(tmp, partName(0))]),
          ...(audio ? ['-ss', String(from), '-t', String(to - from), '-i', mixWav] : []), '-c:v', 'copy',
          ...(audio ? ['-c:a', 'aac', '-b:a', '256k', '-shortest'] : ['-an']), '-movflags', '+faststart', joined,
        ])
        mux.stdin.end(); await mux.done
        renameSync(joined, file)
      } finally { rmSync(tmp, { recursive: true, force: true }) }
      const outputs = [file]
      if (audio) {
        const muted = join(outDir, `${name}-muted.mp4`)
        const m = ffmpeg(['-i', file, '-c', 'copy', '-an', '-movflags', '+faststart', muted]); m.stdin.end(); await m.done
        outputs.push(muted)
      }
      if (flags.webm) {
        const webm = join(outDir, `${name}.webm`)
        const v = ffmpeg(['-i', file, '-c:v', 'libvpx-vp9', '-b:v', '0', '-crf', '32', '-row-mt', '1', '-pix_fmt', 'yuv420p', '-an', webm]); v.stdin.end(); await v.done
        outputs.push(webm)
      }
      const page = from === 0 || flags.poster ? await open(browser, url, scale) : null
      if (from === 0) {
        // Frame 0 is the cover in many players and feeds. Save it at thumbnail size and check its text.
        await draw(page, 0)
        const full = join(outDir, `${name}-cover.png`)
        await page.screenshot({ path: full })
        const small = ffmpeg(['-i', full, '-vf', 'scale=300:-1:flags=area', full.replace('.png', '-300.png')]); small.stdin.end(); await small.done
        const issues = Object.entries(await inspect(page, 390, 10)).filter(([, list]) => list.length)
        console.log(`cover (frame 0): ${full.replace('.png', '-300.png')}  ${issues.length ? 'CHECK: ' + issues.map(([k, l]) => `${k} ${l.slice(0, 3).join(' · ')}`).join(' | ') : 'text clean'}`)
        console.log('  look at it: would someone click this? The subject whole and readable, nothing half-cropped or mid-move.')
      }
      if (flags.poster) {
        await draw(page, +flags.poster)
        const poster = join(outDir, `${name}-poster.jpg`)
        await page.screenshot({ path: poster, type: 'jpeg', quality: 90 })
        outputs.push(poster)
      }
      for (const f of outputs) console.log(`${f}  ${(statSync(f).size / 1e6).toFixed(1)} MB`)
    }
  } catch (e) {
    // The last line says how the run ended, also when its output is piped or tailed.
    console.error(e.stack ?? e)
    console.error(`FAILED: ${String(e.message ?? e).split('\n')[0]}`)
    process.exitCode = 1
  } finally {
    await browser.close()
    server.close()
  }
} else {
  console.log(readFileSync(new URL(import.meta.url), 'utf8').split('\n').slice(0, 15).join('\n'))
}
