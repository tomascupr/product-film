# Engine: the Remotion kit and how scenes are built

Contents: Workspace (tested against a Next 16 + Tailwind v3 product monorepo) · Real product screens (tested: a process diagram, a workflow graph and a chat transcript) · The kit (copy `templates/remotion/kit/` into `src/kit/`) · Rules for scene code · Frame-driven twins · An animated logo or mascot (only if chosen) · Textures (dither) · Measuring (never guess positions)

Only when the interview's engine gate chose Remotion. Its reason to exist: the film imports the product's real React components, so styling stays in sync with the product. Remotion needs a company license above a small team size (remotion.dev/license): confirm the user has one or accepts that.

## Workspace (tested against a Next 16 + Tailwind v3 product monorepo)

```bash
cd ~/Films/<product>/<film>
T=$SKILL/templates/remotion
mkdir -p src/kit src/stubs scripts
cp $T/kit/* src/kit/ && cp $T/stubs/* src/stubs/ && cp $T/{render.ts,stills.ts} scripts/
cp $T/{webpack-override.ts,remotion.config.ts,tailwind.config.ts,tsconfig.json} . && cp $T/{Root.tsx,freeze.css} src/
# edit the product path in webpack-override.ts and tailwind.config.ts; write src/index.ts (registerRoot) and src/fonts.css, then:
pnpm add remotion@X @remotion/cli@X @remotion/bundler@X @remotion/renderer@X @remotion/tailwind@X react@<product's> react-dom@<product's> @fontsource-variable/<font>
```

- **Versions.** Pin `remotion` and every `@remotion/*` to one exact version (`npm view remotion version`). Use React at the product's version.
- **`src/index.ts`** is `registerRoot(Root)`. `src/Film.tsx` is the composition, and `film.json` plus `audio/vo/*.json` are the same data the HTML engine uses. The composition renders muted; `mix.py` makes `audio/mix.wav` and `scripts/render.ts` muxes it.
- **`webpack-override.ts`** exports `webpackOverride`, which `remotion.config.ts` (CLI) and `scripts/stills.ts` both use:
  - `@` points at the product app (its tsconfig `@/*`). Add its other path aliases (workspace packages) the same way.
  - `resolve.modules` includes the product's `node_modules` and the monorepo root's, so the product's own dependencies (lucide, cva, Radix, clsx) resolve from there. Nothing is copied.
  - `next/link` and `next/navigation` go to the stubs (a plain `<a>`, a fixed pathname). Add stubs for any other framework import a component touches (`next/image` to `<Img>`).
- **`tsconfig.json`** must exist in the film folder. The Remotion CLI refuses to render without one; the bundler API used for stills does not care.
- **Tailwind v3:** `tailwind.config.ts` spreads the product's config and scans the film plus the product folders you import from. `@remotion/tailwind` bundles its own `tailwindcss`, so don't add one. For Tailwind v4, use `@remotion/tailwind-v4`, `@import` the product CSS and `@source` the folders.
- **Global CSS:** `import '@/app/globals.css'` from `Root.tsx`. An `@import` of it from a film CSS file silently skips Tailwind (unstyled frames).
- **Fonts:** `next/font` sets a CSS variable (`--font-inter`) that does not exist outside Next, so text falls back to serif. Load the same font from a local package (`@fontsource-variable/inter`) and set the variable in `src/fonts.css` (`:root { --font-inter: 'Inter Variable'; }`).
- **Providers:** components can need the app's context providers. `TruncatedText` threw "`Tooltip` must be used within `TooltipProvider`". Wrap the composition in the providers the imported components use (tooltip, theme, i18n), with static values.
- **Server components and data fetching** do not run here. Import presentational leaf components and pass demo data as props.
- **Composition.** `fps` comes from props through `calculateMetadata` (see `Root.tsx`): 60 in Studio and for stills, 240 for the final render.
- **Several formats:** register one `<Composition>` per format (its own `id`, `width` and `height`) on the same component. The camera helpers take the frame from `useVideoConfig()`, so each format frames itself. Reframe the layout per format rather than cropping.

## Real product screens (tested: a process diagram, a workflow graph and a chat transcript)

Whole screens need more than leaf components. Every item below broke a render once:

- **Start from the product's Storybook config** if it has one (`.storybook/main.ts`, its mocks and providers decorator). It lists the aliases, stubs and providers the components need outside the app.
- **Survey first.** Before choosing screens, have an Explore agent return, per candidate: props, the hooks and providers it needs, its own clocks, and a verdict (import / import with providers and stubs / twin / avoid). Skip whole pages that fetch data; import the container below them and pass props.
- **Stubs** (all in `templates/remotion/stubs/`): `next/link`, `next/navigation` (with a settable pathname for nav active states), `next/image` (maps `/x` to `staticFile('x')`) and `noop-module.cjs` for telemetry SDKs (`@sentry/nextjs` imports `next/router`).
- **Env validation:** products often validate `NEXT_PUBLIC_*` at import time. Give placeholders in `webpack-override.ts` (`env`), never real secrets.
- **Implicit React:** Next injects `React`; some files use it without importing. `webpack.ProvidePlugin({ React: 'react' })` fixes "React is not defined".
- **Public assets:** symlink the product's `public/` folders the components use (`integration-icons/`) into the film's `public/`.
- **Providers:** wrap the film in the providers the components throw without (react-query `QueryClient` with queries disabled, tooltip, team or user context with static demo values, feature contexts). The error message names each one.
- **Wall-clock motion, three kinds, three fixes:**
  - CSS animations and transitions: `freeze.css` turns them off. Watch for elements that start at `opacity: 0` and depend on the animation to appear.
  - framer-motion: `MotionGlobalConfig.skipAnimations = true` in `Root.tsx`.
  - JavaScript timers and async renders (typewriter effects, lazy markdown): hold the frame with `useTextOnScreen` (`kit/settle.ts`) until the text is really there. A missing message is most often this, not a filter.
- **Async layout** (ELK in a worker, xyflow measuring, fitView): `useSettled` holds the first frame until nodes exist and the viewport stops moving. Keep such a component's props constant (module-level objects): many graphs re-run their async layout whenever a prop changes identity, and a frame then captures the old layout. Move the camera around the component instead of animating its props.
- **fitView surprises:** a fitView capped at zoom 1, or measured against a smaller container, leaves a tiny graph. Prefer a fixed `initialZoom` where the component offers one, and give the canvas an explicit pixel height.
- **Duplicate content grows nodes:** a layout sized for one badge clips the title when you add a second (e.g. an agent name that repeats the role). Check titles in every still.
- **Time from the product:** components that show relative times ("5m ago") read the wall clock. Pass fixed dates, or avoid those components.

## The kit (copy `templates/remotion/kit/` into `src/kit/`)

| File | What it gives |
|---|---|
| `time.ts` | `useTime()` (seconds), the beat grid `at(grid, bar, beat, fraction)`, `progress`, `clamp01` |
| `spring.ts` | `step(t, config)`: a closed-form spring step (0 to 1). `track(t, keys, config)`: a value that retargets, as a sum of one step per key |
| `move.ts` | `move(t, start, fromRect, toRect)` for magic moves, `swapIn` (blur swap in and out), `Rect` |
| `camera.ts` | Camera keys `[t, x, y, zoom]` on springs (zoom in log space), `project`, `worldTransform` |
| `cursor.tsx` | `cursorAt(t, keys, toScreen)`: curved glides that arrive exactly at `t`, click squash. `UserCursor` (macOS arrow). Add the product's own cursor next to it |
| `cursor-path.ts` | A smooth free-form path through timed stops (Hermite), plus sampled look-at keys, for when something on screen follows the cursor |
| `punchlines.tsx` | Word-by-word punchline cards with kept slots, accent words and inline logos (if punchlines were chosen) |
| `dither.ts` | The 4x4 Bayer matrix, `bayerPath` (a reveal front as an SVG path) and `bayerReveal` (a mask style) |
| `debug.tsx` | `TargetLog`: prints every `[data-target]` box into the frame (stills do not forward console logs) |
| `settle.ts` | `useSettled` (hold until async layout settles) and `useTextOnScreen` (hold until late text renders), for real product screens |

Add per product: `tokens.ts` (the product's colors, fonts, springs, all as hex), a rig for the logo or mascot if one animates, and twins of their components (a card, a search result, an AI answer...).

## Rules for scene code

- Camera: keys are `[t, x, y, zoom, spring]` with `snap`, `whip` or `creep` per key (`kit/camera.ts`). Every hold on text uses `fit(box, frame)` from the text's measured box (see Measuring), passed through `inside(hold, contentBounds, frame)` so the frame stays on the content, where `frame` is `useVideoConfig()`. Add `shake(t, peak)` on impacts and `beatKick(t, grid, from, to)` so holds breathe. Animated colors use Remotion's `interpolateColors` with hex tokens.

- Read time once: `const t = useTime()`. Everything is a function of `t` and the cues. No hooks with state, no effects that change what is drawn. A `useLayoutEffect` that paints a canvas from `t` is fine.
- Timeline in `cues.ts` from `film.json`, the beat grid (`b(bar, beat, fraction)`) and voice words (a `wordAt` like kit.js). Layout in `layout.ts`, with measured numbers commented as measured.
- Each act returns `null` outside its window. Enter and leave with `swapIn` or a traveler.
- **Layers, bottom to top:**
  1. world scenes under the camera
  2. screen-space textures (a flood, a wallpaper)
  3. world scenes that must sit above the texture (an app window)
  4. the brand element (logo or mascot), if it moves across scenes
  5. the product's cursor
  6. punchlines and text
  7. the user's cursor
- Hex colors for anything that animates (`interpolateColors` cannot parse `color-mix()`).
- Use the individual transform properties (`translate`, `scale`, `rotate`). Never `will-change` on anything the camera scales, or text blurs.
- **Magic moves.** Travelers render in the destination's style and scale from the source size (`scale: s / destSize`, `transformOrigin: 0 0`).
  - Left-aligned destinations only; to go from a centered source, blend `translate: -50%` out as the move lands.
  - Keep the source hidden from the start of the move, and the destination hidden until it lands, or let the traveler stay as the element.

## Frame-driven twins

Re-create a component when it:
- runs its own clock: motion or animation libraries, `requestAnimationFrame`, `setInterval` (a spinner), CSS keyframes, video, shaders
- loads images asynchronously (Radix or base-ui `Avatar`: a frame may catch it empty; use Remotion `<Img>`, which the renderer waits for)

Copy the structure, class names and tokens; change only the clock. Write in the file which component it twins and why.

## An animated logo or mascot (only if chosen)

- **One component, driven by `t`:** `<Mark t script size appearance="filled|outline" draw={0..1} />`.
- **`script` holds keyed tracks,** each a sum of springs over time-sorted keys: states `[t, name]`, look `[t, x, y]`, turns `[t, yaw, pitch, roll]`, hops `[t, height]`.
- **Drawing on:** an outline with `stroke-dasharray` and a `stroke-dashoffset` driven by `draw`, then a fill reveal (fade, wipe, or `bayerPath` for a dithered rise).
- **One instance across the film:** give it a `placement(t)` with named spots and arcing leaps between them.
- **Cut-outs:** if it has cut-outs, put a background-colored shape behind them wherever lines or UI pass behind.

## Textures (dither)

- Paint per frame on a canvas at cell resolution with `imageRendering: pixelated`, in screen space, with integer cells.
- If the product has its own texture code (a speed field, a pattern), import its pure painter and feed it `floor(t / step)`.
- A density function per cell gives flood, thin band and calm wallpaper states from one painter.

## Measuring (never guess positions)

- Put `data-target="name"` on anything a cursor clicks or a traveler lands on.
- Render with `debug: true`: `node scripts/stills.ts out/review/debug <frames> --composition <Id> --debug`, then read the box numbers printed in the frame.
- Re-measure after any layout change upstream of a target (a removed line moves everything under it).
