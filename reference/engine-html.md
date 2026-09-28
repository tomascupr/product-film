# Engine: HTML and `render(t)` (the default)

One HTML page per film. `render(t, film)` sets every style and paints every canvas from time, and nothing else draws. Headless Chrome steps it frame by frame and ffmpeg encodes the result. There is no bundler and no license, and the whole source is a folder you can open.

## Set up the film folder

```bash
mkdir -p ~/Films/<product>/<film> && cd ~/Films/<product>/<film>
cp -R $SKILL/templates/html/. .
pnpm install            # playwright-core; it drives your installed Google Chrome
node film.mjs serve     # preview at http://127.0.0.1:4173/#play
```

No Google Chrome? Set `CHROME_PATH` to any Chromium binary. ffmpeg comes from PATH (`FFMPEG` overrides).

| File | Role |
|---|---|
| `index.html` | The film: tokens and fonts in CSS, all layers in the DOM, `render(t, film)` in a module script |
| `kit.js` | Time, easing, springs, magic moves, camera, cursor paths, dither, voice word lookup, `set()`, `boot()` |
| `film.json` | The data both the page and the audio scripts read: size, fps, duration, loop, grid, cues, voice lines, music, sfx |
| `film.mjs` | `serve`, `stills`, `measure`, `check`, `render` |
| `audio/` | `vo/`, `music.mp3`, `sfx/`, `mix.wav` (the scripts write these) |
| `fonts/`, `img/` | Local copies of the product's fonts, logo SVGs and images. Nothing loads from the network at render time. |

## Rules for scene code

- `render(t, film)` is a pure function. No CSS transitions or animations, no `setTimeout` or `requestAnimationFrame`, and no state carried between calls. Rendering t = 12 cold must give the same picture as playing up to it.
- Build the whole DOM once in HTML. `render` changes styles, text and attributes (use `set(el, {x, y, s, r, op, blur, vis})`) and repaints canvases. Show and hide with `vis` or `op`; never add or remove nodes.
- The idea's world can be painted in whatever technique suits it: a 2D canvas, WebGL, or SVG shapes whose attributes are set from `t` (a texture, a generative background, a hand-drawn look). Clear and redraw a canvas whole every frame, and seed any noise per frame instead of calling `Math.random`. Keep text and the product's UI in the DOM: `check` and `measure` read DOM boxes and cannot see into a canvas.
- **Schedule by landing, not by start.** Anything that builds up to a moment (flips, typing, counters, springs, a riser) is timed backwards from when it lands: `start = landing - duration`. Key the landing to the word or beat; the start follows.
- **Gate every layer to its scene.** A layer outside its scene is hidden with `vis`, not only faded, or its empty shapes show through other scenes.
- **Camera:** keys are `[t, x, y, zoom, spring]` with `snap`, `whip` or `creep` per key (kit.js). Every hold on text uses `fit(textBox(el, world))` so a line is never cropped, passed through `inside(hold, contentBounds)` so a line near the content's edge doesn't pull empty space into the frame. Add `shake(t, peak)` on impacts and `beatKick(t, grid, from, to)` so holds breathe.
- Every time comes from `film.json` cues, the beat grid (`at(grid, bar, beat)`) or a voice word (`wordAt(film, 'v2', 'SAP')`). There are no literal times in scene code apart from small offsets inside a moment.
- Text that grows (typing, counters) keeps its box: fixed widths, `font-variant-numeric: tabular-nums`, typed text drawn inside a full-width slot.
- Hex colors for anything that animates. Individual transforms. No `will-change` on anything a camera scales.
- Layers, bottom to top: world scenes under the camera, screen-space textures, world scenes above the texture, the brand element, the product's cursor, words, the user's cursor.
- Keep the product's look by copying its real markup and classes where you can: open the product's page in the browser, copy the component's rendered HTML and computed styles, and replace its clock with `t`. Mark every redrawn component in BRAND.md "Components" as a faithful reconstruction.

## GSAP and Lottie

Both run inside `render(t)` as long as nothing plays on its own clock.

```html
<script src="node_modules/lottie-web/build/player/lottie_svg.min.js"></script>
<script type="module">
import { boot, gsapAt, lottieClip, wordAt } from './kit.js'
import { gsap } from './node_modules/gsap/index.js'
import { SplitText } from './node_modules/gsap/SplitText.js'
gsap.registerPlugin(SplitText)
const sting = lottieClip(window.lottie, document.getElementById('sting'), 'img/sting.json')
let tl
boot((t, film) => {
  if (!tl) {                                  // build once, from word times
    tl = gsap.timeline({ paused: true })
    tl.from(new SplitText('#title', { type: 'chars' }).chars, { opacity: 0, y: 60, stagger: 0.03 }, wordAt(film, 'v1', 'launch'))
  }
  gsapAt(tl, t)
  sting.at(t, 0.4)
}, { wait: [sting.ready] })
</script>
```

- One paused timeline for the whole film, positioned on word times and cues. A second clock anywhere breaks the frame-exact render.
- A tween that changes something already on screen (a pop, a bump) gets `immediateRender: false`, or its start state shows from frame 0.
- Keep the page's purity check (render a time, render another, render the first again, compare): it catches a tween that escaped the timeline. `tests/thirdparty/run.sh` shows the same check for both libraries.

## Look and measure

```bash
node film.mjs stills out/review/v1 0.5 3.2 6.0 9.4    # PNG per time + sheet.png
node film.mjs measure 9.4                              # boxes of every [data-target] at t = 9.4
```

- Put `data-target="name"` on anything a cursor clicks or a traveller lands on, and measure both ends of every move. Console output and errors surface in the terminal.
- Browser preview: `/#play` plays the film with `audio/mix.wav` (click to restart), and `/#t=12.4` holds one frame.

## Several formats from one film

`film.json` `size` is the main format. `--size 1080x1920` on `stills`, `measure`, `check` and `render` draws the same film at another size, and `/?size=1080x1920#play` previews it. `boot()` sizes the stage (`--w` and `--h` in CSS) and the camera helpers to it, and `render` sees it as `film.size`.
- Lay scenes out from the size, never from fixed pixels: CSS sizes in `cqw` and `cqh` (the stage is a size container), and a small `layout(film)` for positions that differ by format.
- Reframe each format instead of cropping one out of another: a 9:16 stacks what a 16:9 puts side by side.
- Check each format at its holds and its cover (`check ... --size 1080x1920`), then render the formats in parallel under their own names: `node film.mjs render launch-9x16 --size 1080x1920 --blur`.

## Render

```bash
node film.mjs render draft --scale 0.5                    # fast review draft -> out/draft/
node film.mjs render <name> --blur --poster 27.5 --webm   # final -> out/<name>/  (--blur 8 or 16 for whips, shakes, spins)
```

- `--blur [N]` renders N subframes per frame (4 by default) and averages them into motion blur. It costs N times the render time, so use it for finals only. Raise N when fast whips, shakes or spins show ghost copies in the encode (render.md).
- The output is BT.709 limited range, with matrix, primaries and transfer all tagged. `audio/mix.wav` is muxed when it exists and a `-muted` copy is written next to it; `--muted` skips the audio altogether.
- `--from`/`--to` render a slice, for checking one scene at full quality.
- Frames render in parallel pages (`--workers 4`). A 30 s film at 60 fps takes a few minutes, or about N times that with `--blur N`.
