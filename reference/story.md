# Story: the idea, the shape, the beat plan and the checkpoint

## Start from references and an idea

Name one or two films whose energy and camera grammar this one should match (the user's favourites, or launch films of the product's peers) and say what you borrow from each. It gives the taste a concrete target.

A reference you can open beats one you remember. When the user has one as a file (a video, a single frame, a folder of their own stills), study it before pitching:
- Put a video in its own folder (`refs/`) and pack it there: `uv run --with numpy --with imageio-ffmpeg python3 $SKILL/scripts/critic.py launch.mp4`. It writes contact sheets every 1/3 s and `energy.txt`, the reference's energy curve. Run it from `refs/`, not the film folder, or it reads the film's `film.json` and `audio/bed.wav` instead of the reference's own sound.
- List its hard cuts: `ffmpeg -i launch.mp4 -vf "select='gt(scene,0.3)',showinfo" -an -f null - 2>&1 | grep -o 'pts_time:[0-9.]*'`. A film built on camera moves lists few; read its transitions off the sheets.
- Write what you take into `film-prompt.md`: shot lengths, how scenes connect, how type enters and leaves, palette and texture, and its mean motion as the draft's target. Take the grammar, never the content, logos or characters.

A film people remember has an idea, not only a sequence of features. Pitch 2 or 3 ideas: a one-line premise, the opening image, and the ingredients the idea brings (how words appear, how scenes connect, what carries the brand, any cursor, partner logos, proof, Lottie, generated footage or a 3D render). At least one should look beyond the product's own screens: a familiar format, place or object the audience reads instantly, whose logic carries the message (a month-end close as a heist, a release as a weather forecast, a report as a receipt, a launch as a launch). One can be the straight product story. The user picks, then the beat sheet serves the idea.

Build the first draft ambitiously. Review notes pull a film back; they rarely push it further.

## Film types

Defaults to depart from when the idea asks for it. Every type still has a hook, one clear peak, and no stillness it doesn't want.

| Type | Length | Shape | The peak | Sound |
|---|---|---|---|---|
| Launch film | 30 to 60 s | the product-story shape below | the key feature switching on | voice + composed music with a drop |
| Teaser or announcement | 8 to 20 s | an idea world (a format the audience knows), one statement, the lockup | the reveal (the name, the date, the status flipping) | no voice or one line; music built to the reveal |
| Feature demo or walkthrough | 30 to 90 s | one task end to end in the real UI, cursor-led, one idea per scene | the result appearing | voice-led, music low; clicks and confirmations |
| Explainer | 45 to 120 s | problem, mechanism (a diagram or metaphor built step by step), outcome | the mechanism clicking into place | voice-led; music under it |
| Social cut | 6 to 30 s | hook in the first second, one idea, text that works muted, end on the brand | early, and again at the end | captions or punchlines carry it muted |
| Landing loop | 8 to 20 s | the product working, few or no words, last frame equals the first | a result that resolves once per loop | muted |
| Partner co-launch | 15 to 45 s | the two worlds meeting, both brands in their own identity | the two products working together | as launch or teaser |
| Event opener or title sequence | 10 to 40 s | music-led, type and brand elements in motion, the event name last | the title | music first, no voice |
| Data or metrics story | 20 to 60 s | numbers counting, charts drawing, each figure one scene | the biggest number landing | voice or punchlines naming each figure |

**The product-story shape**, for launch films and when the idea is the product itself: the brand element or hero screen alive in the first second; who and what in one line; 3 to 6 features, each a short scene of the real UI moving; the strong moment on the music's drop; proof as the viewer knows it (a result, an answer, a metric, a quote); the tagline and lockup; for a loop, a fold back into the first frame. One idea per scene.

## Energy

A film needs one peak bigger than everything around it, and no stretch that sits still unless the type wants it (a landing loop's calm, an explainer's diagram being read). For launches and teasers, a shape that works is hook, build, peak, ride, landing: a clean first frame that names the subject and then moves at once; tension that rises; everything at once on the peak (the drop, the biggest hit, the biggest scale change, the accent color), with a beat of stillness or silence just before it; a ride with moves that differ from each other; an ending that lands on a hit and keeps moving. Write the curve you chose above the beat sheet, with the camera plan beside it.

## Words

- With a voiceover, write the script first (voice.md); on-screen words echo it.
- Write from the product's approved lines and copy rules. Punchlines stay short (about six words); scenes carry only the UI's own text.
- Brand and partner names come with their logos. Promise nothing the product cannot do.

## Timing

- Measure the music first (music.md) and plan in bars and beats. A silent film still gets a tempo.
- Every moment is a named cue in `film.json`, a grid position (`at(grid, bar, beat)`) or a voice word (`wordAt`). Scene code holds no literal frame numbers, so a retimed line or a new track cannot silently break sync.
- With a voiceover the voice leads: place the lines, key moments to words, then fit the music.
- Keep the beat sheet in `film-prompt.md` current; it is what the product owner reads against the film.

## Checkpoint before building everything

Show the user the chosen idea in one line, the beat sheet (and the script, read aloud once for fit), style frames of the opening and one key scene built in the engine as those scenes' settled states, and a motion test of the peak with a sketch of its sound (`node film.mjs render peak --from <s> --to <s>`). The voice and composed music don't exist yet, so the sketch is the user's licensed track if there is one, or a riser and hit synthesized in code (music.md D) in `film.json` `sfx`, mixed with `mix.py` while `voice.lines` is still empty (it loads a clip for every line). Stills cannot show energy: a flat peak found here costs minutes, found in the draft it costs a round. Fold every note into BRAND.md or the prompt.

Beside each scene in the beat sheet, write one plain sentence: what a viewer who has never seen the product understands from it, from the picture alone where the film plays muted. Have the user confirm those sentences with the rest. A scene whose sentence you cannot write is not ready to build, and this is the cheapest place to find that out: in one film the two scenes built without such a sentence were the two the product owner could not follow, and one of them was cut.
