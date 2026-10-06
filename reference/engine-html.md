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

A film folder keeps the `film.mjs` and `kit.js` it was set up with. Coming back to an older film, copy the current `film.mjs` over its copy (and `kit.js`, unless the film changed it) before you use a newer command.

| File | Role |
|---|---|
| `index.html` | The film: tokens and fonts in CSS, all layers in the DOM, `render(t, film)` in a module script |
| `kit.js` | Time, easing, springs, magic moves, camera, cursor paths, dither, voice word lookup, footage, `set()`, `boot()` |
| `film.json` | The data both the page and the audio scripts read: size, fps, duration, loop, grid, cues, voice lines, music, sfx |
| `film.mjs` | `serve`, `stills`, `measure`, `check`, `render` |
| `audio/` | `vo/`, `music.mp3`, `sfx/`, `mix.wav` (the scripts write these) |
| `fonts/`, `img/` | Local copies of the product's fonts, logo SVGs and images. Nothing loads from the network at render time. |
| `footage/`, `3d/` | Generated shots and 3D renders as frames plus `clip.json`, and the Blender scripts and HDRIs that make them |

## Rules for scene code

- `render(t, film)` is a pure function. No CSS transitions or animations, no `setTimeout` or `requestAnimationFrame`, and no state carried between calls. Rendering t = 12 cold must give the same picture as playing up to it.
- Build the whole DOM once in HTML, images included: `boot()` waits for each one to decode, and an image added later can render empty in a frame. `render` changes styles, text and attributes (use `set(el, {x, y, s, r, op, blur, vis})`) and repaints canvases. Show and hide with `vis` or `op`; never add or remove nodes.
- **The DOM carries state from one frame to the next, so it is part of the function.** Three habits keep a frame drawn cold equal to the same frame drawn in sequence: measure layout once at setup and not inside `render` (an element the frame before hid measures 0); let each scene set everything it owns before any early return; and start anything a scene reveals hidden in CSS. `node film.mjs check --cues --cold` draws each moment both ways and reports a difference, which a render would show as a flicker between workers or a jump where two segments join.
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

- One paused timeline for the whole film, positioned on word times and cues. A second clock anywhere breaks the frame-exact render, and so does a loose tween, which runs on GSAP's own clock. Build the timeline and what it needs (SplitText, generated nodes) once, never inside `render(t)`.
- A tween that changes something already on screen (a pop, a bump) gets `immediateRender: false`, or its start state shows from frame 0.
- `node film.mjs check --cues --cold` catches a tween that escaped the timeline: the frame then depends on what was drawn before it. `tests/thirdparty/run.sh` proves both libraries frame-exact the same way.

## Footage and 3D renders

A generated shot or a Blender render plays as an image sequence on the film's clock, not as a `<video>` seeked by `t`, so each film frame shows one decoded source frame, cold or in sequence. At 60 fps a 24 fps shot holds each frame for 2 or 3 film frames; nothing is interpolated. Never generate the product's own screens (ingredients.md).

Generate between two of the film's own stills, so the shot starts where a coded scene stops and ends where the next one starts:

```bash
node film.mjs stills footage/in 4.0 8.0      # the frames the shot starts and ends on
python3 $SKILL/scripts/gen.py video --prompt "..." --first footage/in/000.png --last footage/in/001.png --seconds 4 --out footage/<name>
```

- gen.py submits to fal.ai's queue (`FAL_KEY`), polls, downloads `clip.mp4` and writes every frame as a JPEG, plus `clip.json` (fps, frames, seconds, size, model, prompt, request id). Every run is paid, so it won't generate into a folder that has a clip unless you pass `--force`. With no stills to match, text to video makes the shot from the prompt alone: `--model fal-ai/kling-video/v3/standard/text-to-video --seconds 8 --arg aspect_ratio=1:1`.
- The default is Kling v3 standard; `--model` takes any fal endpoint and `--arg key=value` any field on its API page. A clip takes from a minute to several, so start every clip at once, one gen.py per clip. It can come back a frame longer than asked, so resume the coded scene at `start + clip.seconds`. Prices, timings and how closely the frames matched the stills are in field-notes.md.
- For a clip from elsewhere (a download, another generator), run `gen.py frames clip.mp4 --out footage/<name>`. Both commands read an untagged clip as BT.709 limited range. ffmpeg's own guess for an untagged clip is BT.601, which turned `#ffd400` into 248,223,9.

```js
import { boot, footage, set, $ } from './kit.js'
const shot = footage($('shot'), 'footage/<name>')      // an <img id="shot"> in the DOM
boot((t, film) => {
  const { handoff } = film.cues, back = handoff + shot.seconds
  set('shot', { vis: t >= handoff && t < back })       // the coded scenes hide in this window
  return shot.at(t, handoff)                           // resolves once the frame is decoded
}, { wait: [shot.ready] })
```

- `render(t)` may return a promise or be `async`, and film.mjs waits for it before it takes the frame. For several clips, `return Promise.all([a.at(t, 2), b.at(t, 9)])`. Without that wait, 1 in 24 stills of heavy 1080p frames showed the wrong frame.
- Take the handoff stills before the shot goes into the page, and hold both sides of each cut still for a moment.
- The shot is baked in: the camera can scale, crop and grade it, but it can't move into it.

**3D renders.** Script the scene for Blender, render it headless to PNGs at the film's fps and size, and play them with `footage()` like any shot. `templates/3d/shot.py` is a starting scene: a chrome torus that spins for a second on a transparent background, with `clip.json` written beside its frames. Light it with a Poly Haven HDRI (CC0). Their API asks for a User-Agent that names your software:

```bash
mkdir -p 3d && cp $SKILL/templates/3d/shot.py 3d/ && curl -sfA product-film https://api.polyhaven.com/files/studio_small_09 \
  | python3 -c "import json, sys; print(json.load(sys.stdin)['hdri']['1k']['hdr']['url'])" | xargs curl -sfA product-film -o 3d/studio_small_09_1k.hdr
/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P 3d/shot.py -a     # or `blender` on PATH
```

- Keep the motion a function of the frame (the template uses a driver expression) and the seed fixed, then render a shot once and let the film play the files: Cycles on Metal is not bit-exact between runs. Render times are in field-notes.md.

## Look and measure

```bash
node film.mjs stills out/review/v1 0.5 3.2 6.0 9.4    # PNG per time + sheet.png
node film.mjs stills out/review/v1 --cues              # the film's own moments: frame 0, every cue, the middle and last word of every line
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
- `--segments [s]` renders s seconds of film per browser (10 when bare) and joins the parts, for a long blurred final that would stall in one browser (render.md). A failed part is rendered once more; a render that fails ends on a `FAILED:` line and leaves the render before it in place.
