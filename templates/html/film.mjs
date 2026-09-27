// The HTML engine's harness: serve the film, take stills, measure targets, render.
//
//   node film.mjs serve [--port 4173]                 preview at /#play, one frame at /#t=12.4
//   node film.mjs stills <dir> <seconds>...           PNG per time, plus sheet.png
//   node film.mjs measure <seconds>                   JSON boxes of every [data-target]
//   node film.mjs check <seconds>... [--view 390] [--min 10]
//                                                     text too small at the viewing width, covered, overlapping
//                                                     or off frame; out/check/<t>.png at that width to look at
//   node film.mjs render <name> [--blur] [--scale 0.5] [--from s] [--to s] [--webm] [--poster s] [--muted] [--workers 4]
//                                                     -> out/<name>/<name>.mp4 (+ -muted.mp4, .webm, -poster.jpg,
//                                                        -cover-300.png: frame 0 at thumbnail size, with its text checked)
//
// --size 1080x1920 on stills, measure, check or render draws the same film at another size (film.json size
// by default), so each format of one timeline renders from one folder, in parallel under its own name.
//
// render: headless Chrome steps window.render(t) frame by frame and pipes PNGs into
// ffmpeg. --blur renders 4 subframes per frame and averages them (motion blur, 4x slower).
// Colors: screenshots are sRGB; ffmpeg converts once to BT.709 limited range and tags it,
// so dark backgrounds do not come back lifted. Muxes audio/mix.wav when it exists.
import { chromium } from 'playwright-core'
import { spawn } from 'node:child_process'
import { createServer } from 'node:http'
import { existsSync, mkdirSync, readFileSync, statSync } from 'node:fs'
import { extname, join, resolve } from 'node:path'

const [cmd, ...rest] = process.argv.slice(2)
const flags = {}, args = []
for (let i = 0; i < rest.length; i++) {
  if (!rest[i].startsWith('--')) { args.push(rest[i]); continue }
  const next = rest[i + 1]
  flags[rest[i].slice(2)] = next === undefined || next.startsWith('--') ? true : (i++, next)
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
  return { stdin: p.stdin, done, kill: () => p.kill('SIGKILL') }
}

// An error inside the page (a missing cue word, a typo) stops the run with its own message.
let pageError
async function draw(page, t) {
  await page.evaluate(t => window.render(t), t)
  if (pageError) throw new Error(`page error: ${pageError.message}`)
}

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

const launch = () => chromium.launch(process.env.CHROME_PATH ? { executablePath: process.env.CHROME_PATH } : { channel: 'chrome' })

if (cmd === 'serve') {
  const server = await serve(+(flags.port ?? 4173))
  console.log(`http://127.0.0.1:${server.address().port}/#play   (one frame: /#t=12.4)`)
} else if (['stills', 'measure', 'check', 'render'].includes(cmd)) {
  const server = await serve()
  const url = `http://127.0.0.1:${server.address().port}/?size=${W}x${H}` // the page draws at the viewport's size
  const browser = await launch()
  try {
    if (cmd === 'stills') {
      const [dir, ...times] = args
      if (!dir || !times.length) throw new Error('usage: node film.mjs stills <dir> <seconds>...')
      mkdirSync(dir, { recursive: true })
      const page = await open(browser, url)
      for (const [i, t] of times.entries()) {
        await draw(page, +t)
        const file = join(dir, `${String(i).padStart(3, '0')}.png`)
        await page.screenshot({ path: file })
        console.log(`${file}  t=${t}`)
      }
      if (times.length > 1) {
        const cols = Math.min(4, times.length)
        const sheet = ffmpeg(['-framerate', '1', '-i', join(dir, '%03d.png'), '-vf', `scale=480:-1,tile=${cols}x${Math.ceil(times.length / cols)}:padding=4:color=0x333333`, '-frames:v', '1', join(dir, 'sheet.png')])
        sheet.stdin.end(); await sheet.done
        console.log(join(dir, 'sheet.png'))
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
      if (!args.length) throw new Error('usage: node film.mjs check <seconds>... [--view 390] [--min 10]')
      // --view: the width the film is watched at in CSS px (a phone feed is about 390). --min: smallest readable text there.
      const view = +(flags.view ?? 390), min = +(flags.min ?? 10), dir = join(root, 'out', 'check')
      mkdirSync(dir, { recursive: true })
      const page = await open(browser, url)
      let total = 0
      for (const t of args) {
        await draw(page, +t)
        const issues = await inspect(page, view, min)
        const file = join(dir, `${(+t).toFixed(2)}.png`)
        await page.screenshot({ path: file, scale: 'css', clip: { x: 0, y: 0, width: W, height: H } })
        const small = ffmpeg(['-i', file, '-vf', `scale=${view}:-1:flags=area`, file.replace('.png', '-view.png')]); small.stdin.end(); await small.done
        const count = Object.values(issues).flat().length
        console.log(`t=${t}  ${count ? count + ' issue(s)' : 'clean'}  ${file.replace('.png', '-view.png')}`)
        for (const [kind, list] of Object.entries(issues)) if (list.length)
          console.log(`  ${kind} (${list.length}): ${list.slice(0, 6).join(' · ')}${list.length > 6 ? ` · +${list.length - 6} more` : ''}`)
        total += count
      }
      if (total) process.exitCode = 1
    } else {
      const [name] = args
      if (!name) throw new Error('usage: node film.mjs render <name> [--blur] [--scale 0.5] [--from s] [--to s] [--webm] [--poster s]')
      const sub = flags.blur ? 4 : 1, scale = +(flags.scale ?? 1), workers = +(flags.workers ?? 4)
      const from = +(flags.from ?? 0), to = +(flags.to ?? film.duration)
      const n0 = Math.round(from * FPS * sub), n1 = Math.round(to * FPS * sub)
      const outDir = join(root, 'out', name); mkdirSync(outDir, { recursive: true })
      const file = join(outDir, `${name}.mp4`)
      const mixWav = join(root, 'audio', 'mix.wav')
      const audio = existsSync(mixWav) && !flags.muted
      // Open the pages first: a page error then stops the run before ffmpeg starts.
      const pages = await Promise.all(Array.from({ length: workers }, () => open(browser, url, scale)))
      const blur = sub > 1 ? `tmix=frames=${sub},select='not(mod(n+1\\,${sub}))',setpts=N/(${FPS}*TB),` : ''
      const enc = ffmpeg([
        '-f', 'image2pipe', '-framerate', String(FPS * sub), '-i', '-',
        ...(audio ? ['-ss', String(from), '-t', String(to - from), '-i', mixWav] : []),
        // setparams tags primaries and transfer too; output flags alone leave them 'unknown'.
        '-vf', `${blur}scale=out_color_matrix=bt709:out_range=tv:flags=lanczos,format=yuv420p,setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709:range=tv`,
        '-r', String(FPS), '-c:v', 'libx264', '-preset', 'slow', '-crf', '16',
        '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709', '-color_range', 'tv',
        ...(audio ? ['-c:a', 'aac', '-b:a', '256k', '-shortest'] : ['-an']), '-movflags', '+faststart', file,
      ])
      // Workers render interleaved frames; the writer drains them in order.
      // ponytail: frames buffer in memory up to AHEAD per worker; lower it if RAM is tight at 4K.
      const AHEAD = 24, done = new Map()
      let next = n0
      const wait = () => new Promise(r => setTimeout(r, 5))
      const started = Date.now()
      try { await Promise.all(pages.map(async (page, k) => {
        for (let i = n0 + k; i < n1; i += workers) {
          while (i - next > AHEAD * workers) await wait()
          await draw(page, i / (FPS * sub))
          done.set(i, await page.screenshot({ type: 'png' }))
          while (done.has(next)) {
            const buf = done.get(next); done.delete(next); next++
            if (!enc.stdin.write(buf)) await new Promise(r => enc.stdin.once('drain', r))
            if ((next - n0) % (FPS * sub * 5) === 0) console.log(`${((next - n0) / (FPS * sub)).toFixed(0)} s rendered, ${((Date.now() - started) / 1000).toFixed(0)} s elapsed`)
          }
        }
      })) } catch (e) { enc.kill(); throw e }
      enc.stdin.end(); await enc.done
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
      if (from === 0) {
        // Frame 0 is the cover in many players and feeds. Save it at thumbnail size and check its text.
        const page = pages[0]
        await draw(page, 0)
        const full = join(outDir, `${name}-cover.png`)
        await page.screenshot({ path: full })
        const small = ffmpeg(['-i', full, '-vf', 'scale=300:-1:flags=area', full.replace('.png', '-300.png')]); small.stdin.end(); await small.done
        const issues = Object.entries(await inspect(page, 390, 10)).filter(([, list]) => list.length)
        console.log(`cover (frame 0): ${full.replace('.png', '-300.png')}  ${issues.length ? 'CHECK: ' + issues.map(([k, l]) => `${k} ${l.slice(0, 3).join(' · ')}`).join(' | ') : 'text clean'}`)
        console.log('  look at it: would someone click this? The subject whole and readable, nothing half-cropped or mid-move.')
      }
      if (flags.poster) {
        const page = pages[0]
        await draw(page, +flags.poster)
        const poster = join(outDir, `${name}-poster.jpg`)
        await page.screenshot({ path: poster, type: 'jpeg', quality: 90 })
        outputs.push(poster)
      }
      for (const f of outputs) console.log(`${f}  ${(statSync(f).size / 1e6).toFixed(1)} MB`)
    }
  } finally {
    await browser.close()
    server.close()
  }
} else {
  console.log(readFileSync(new URL(import.meta.url), 'utf8').split('\n').slice(0, 9).join('\n'))
}
