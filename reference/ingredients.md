# Ingredients: how to make each one good

Notes that held up in real reviews. They describe what good looks like; the numbers where they appear are starting points, and the product's own rules and easing (discovery.md) win.

## Opening

- Something moves in the first second; cut slow music intros.
- **Logo:** it can draw itself (`stroke-dashoffset` on its paths) and then fill, or land letter by letter on the beat.
- **Mascot or character** (only if the product has one): animate it the way the product already does, in its poses and personality.
- **Product UI:** open on the hero screen already moving.

## Words on screen

- **Punchlines** (big words between scenes): nothing else on screen but the words and the brand element. Each word lands crisply on its beat, key words in the accent color, readable at the delivery size (shrink a long card rather than wrap to three lines). Every word keeps its slot before it lands, so the line never re-centers: in HTML all words sit in the DOM from the start with `visibility: hidden` (see the starter `index.html`); in Remotion, `kit/punchlines.tsx`. A starting point that worked: blur in from about 16 px and rise about 36 px over 0.3 s.
- **Captions** (instead of punchlines): one short line in a fixed band that never overlaps the UI, swapped on a calm beat.
- Over a texture, thin the texture behind the words instead of adding a panel.

## Scenes

- Show, don't tell: the only text is the product's own UI text, big enough to read at the delivery size.
- Real components where they are pure; frame-driven twins where they run a clock (engine-html.md or engine-remotion.md).
- Demo data from the landing page, so the film and the site agree. One idea per scene.

## Transitions

- **Magic moves:** one element that exists in both scenes travels there (position, size, color) while the rest blur-swaps: avatars into list rows, a clicked row into the detail header, logos into the closing headline. The traveler and its destination share a line-height ratio so the move only scales; measure both ends (`node film.mjs measure`, or `--debug` stills in Remotion); move images and marks rather than flying words across words.
- **Camera moves:** scenes on one world canvas, each key with the spring that fits its moment (kit `snap`, `whip`, `creep`), holds on text fitted to the text. Leave `will-change` off the world layer, or scaled text blurs.
- **Cuts on the beat:** hard cuts exactly on a beat or bar, matching the background and accent across the cut.

## Cursors

- **The user's cursor:** the OS arrow, arriving exactly on the cue; a click is a short squash, then the target reacts.
- **The product's own cursor** (if it automates actions): its real overlay look. The user's cursor sets up and approves; the product's does the work.
- Keep cursors off words being read or typed.

## Partners

- Every partner name comes with its logo. A partner the film is about can co-star in its own identity: `scripts/brandfetch.py <domain>` fetches its official marks and colors (cached), and a partner font marked custom stays inside its logo. The partner's accent can mark its own row, card or label, while the film's key color stays the product's.

## Proof moments

- A search result, an AI answer, a dashboard number, a quote: each its own scene, faithful, on the product's background, big enough to read. Only true outcomes and the product's own demo numbers.

## Motion vocabulary (GSAP)

Use these where a word or moment asks for them, so the motion says something:
- **Letters arriving** (SplitText with a small stagger): a name, a claim, a status, paired with the word being spoken.
- **A line drawing itself** (DrawSVG): a trail, a route, a graph, an underline on the key word.
- **Travel along a path** (MotionPath): something launching, delivering, connecting two places.
- **A shape turning into another** (MorphSVG): a problem becoming a solution, one icon becoming the next.
- **A snap with overshoot** (`back.out`, `expo.out`): status changes, stamps, a lockup landing.

## Brand texture

- Only if the product has one (a pattern, a dither, a gradient, a grain), painted per frame in screen space: calm behind UI, thinned behind words.

## One brand element across the film (optional)

- If a logo mark or mascot carries the film, keep one instance for continuity, with a `placement(t)` of named spots and arcing leaps between them.
- If it has cut-outs (eyes, holes), put a background-colored shape behind them wherever lines or UI pass behind.
- It stays on brand: never sad or hurt unless the brand does that.

## Loops

- Fold back to the first frame's state (the logo un-draws, the UI resets); the last frame equals frame 0.
