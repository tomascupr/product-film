# Story: the shape, the beat plan and the checkpoint

Build the story from the interview's answers. Each part below is optional unless the brief needs it; ingredients.md says how to make each one good.

## Start from references

Before pitching, name one or two films whose energy and camera grammar this one should match: the user's own favourites, or launch films of the product's peers. Say what you borrow from each (the macro open, whip pans between lines, the drop on the reveal). It gives the taste a concrete target.

## Start from an idea

A film people remember has an idea, not only a sequence of features. Before the beat sheet, pitch 2 or 3 ideas to the user: a one-line premise and the opening image for each. Come up with them yourself; the brief, the product and its moment are the inputs. At least one should look beyond the product's own screens: a familiar format, place or object the audience already reads instantly, whose logic carries the message (a month-end close as a heist, a release as a weather forecast, a report as a receipt). One can be the straight product story. The user picks, then the beat sheet serves the idea.

Build the first draft ambitiously. Review notes pull a film back; they rarely push it further, so a safe first draft costs a whole round.

## Film types

Pick the type in the interview; it sets the length, the shape and what the peak is. Energy scales with the type, but every type has a hook, one peak and no dead stretch.

| Type | Length | Shape | The peak | Sound |
|---|---|---|---|---|
| Launch film | 30 to 60 s | the product-story shape below | the key feature switching on | voice + composed music with a drop |
| Teaser or announcement | 8 to 20 s | an idea world (a format the audience knows), one statement, the lockup | the reveal (the name, the date, the status flipping) | no voice or one line; music built to the reveal |
| Feature demo or walkthrough | 30 to 90 s | one task end to end in the real UI, cursor-led, one idea per scene | the result appearing | voice-led, music low; clicks and confirmations |
| Explainer | 45 to 120 s | problem, mechanism (a diagram or metaphor built step by step), outcome | the mechanism clicking into place | voice-led; music under it |
| Social cut | 6 to 30 s | hook in the first second, one idea, text that works muted, end on the brand | early (by 3 s) and again at the end | captions or punchlines carry it muted |
| Landing loop | 8 to 20 s | the product working, no words or few, last frame equals the first | a result that resolves once per loop | muted |
| Partner co-launch | 15 to 45 s | the two worlds meeting, both brands in their own identity | the two products working together | as launch or teaser |
| Event opener or title sequence | 10 to 40 s | music-led, type and brand elements in motion, the event name last | the title | music first, no voice |
| Data or metrics story | 20 to 60 s | numbers counting, charts drawing, each figure one scene | the biggest number landing | voice or punchlines naming each figure |

## The product-story shape (30 to 60 s)

The launch film's default, and a fallback when the idea is the product story itself.

1. **Opening (1 to 2 bars).** The brand element comes alive: the logo draws, the wordmark lands, the mascot wakes, or the hero screen is already moving. Something moves in the first second.
2. **Who and what (1 bar).** A punchline or a caption. "Meet X." or the one-line promise.
3. **Features (3 to 6).** For each, an optional one-line punchline that frames it, then a 2 to 4 bar scene of the product's real UI moving. Consecutive scenes connect with the chosen transition.
4. **The strong moment on the song's drop.** The automation turning on, the result appearing, the before and after.
5. **Proof (optional).** The outcome as the viewer knows it: a search result, an AI answer, a metric, a quote. Each gets its own scene.
6. **Ending.** The product's own tagline, a call to action or URL if chosen, the logo lockup.
7. **Loop (if it loops).** Fold back into the first frame's state.

Keep each scene to one idea. Cut anything that needs explaining.

## Words

- With a voiceover, write the script first (voice.md). On-screen words then only echo it.

- Write from the product's approved lines and its copy rules (casing, dashes, reading level, banned words).
- Punchlines: at most 6 words. Captions: one short line. Scenes: only the UI's own text.
- Brand and partner names come with their logos.
- Never promise an outcome the product cannot guarantee.

## The energy curve

Plan the film as hook, build, peak, ride, landing, and write the curve above the beat sheet.
- **Hook (first second):** frame 0 is a clean still that names the subject (it is the thumbnail in many players), then motion starts at once: a snap, a clatter, a count. Never an empty frame, a fade up, or a close-up of nothing in particular.
- **Build:** tension that rises: a slow creep in, a riser, a blinking status, a count running.
- **Peak (one):** everything at once: the music's drop, the biggest hit, the biggest scale change, the accent color. Just before it, a beat of stillness or silence makes it land harder.
- **Ride:** faster cuts and moves than the build, each different from the last.
- **Landing:** the end card lands on a hit and keeps moving: a slow push, and a second reveal on the next bar.
Give every row of the beat sheet a camera entry (zoom and move type: snap, whip, creep, hold). A column of "hold" is a slideshow.

## The timing plan (`film.json` cues)

- Measure the song first (music.md). Plan in bars and beats; at 150 BPM a beat is 0.4 s and a bar 1.6 s. For a silent film, pick a tempo anyway (120 BPM) and plan on it.
- Every moment is a named cue in `film.json`, a grid position (`at(grid, bar, beat)`) or a voice word (`wordAt`). Scene code never holds a literal frame number.
- **With a voiceover the voice leads** (voice.md): place the lines first, key the moments to words, then fit the music to the result. The grid only times accents, such as word pops, clicks and counters.
- Rough budget: opening 1 to 2 bars, punchline 1 to 1.5, feature scene 2 to 4, proof 1.5 to 2.5, ending 2.
- Something happens on every beat: clicks, words, counters on eighths or sixteenths, pings. If a scene idles for a bar, give it beat-synced life or cut the bar.
- Keep a beat sheet table in `film-prompt.md` (time, bar or word, what happens on screen, what is heard) and keep it current. It is the document the product owner reads.

## Checkpoint before building everything

Show the user:
- the beat sheet, with the voice script if there is one (read it aloud once: does it fit?)
- the chosen idea in one line
- 2 style frames: the opening and one feature scene, built as those scenes' settled states in the engine itself, so the code carries into the film.
- **A motion test of the peak:** 2 to 3 seconds around the strongest moment, rendered at full quality with its sound (`node film.mjs render peak --from 2 --to 5`). Stills cannot show energy; a flat peak found here costs minutes, found in the draft it costs a round.
- a pose sheet, if a logo or mascot animates

People react fastest to pictures. Expect notes on pacing, words, shades and borders, and fold every note into BRAND.md or the prompt.
