# Review loop: look, measure, fix, repeat

Stills are cheap; renders are not.

## 1. Stills and the text check

```bash
node film.mjs stills out/review/v3 --cues 4.2 14.0                # HTML engine: the film's own moments plus any seconds; sheets of 16
node film.mjs measure 9.4                                         # target boxes, for moves and cursor stops
node film.mjs check --cues --view 390                             # text too small at phone width, covered, overlapping or cropped
node film.mjs check --cues --cold                                 # and a frame that changes with what was drawn before it
node scripts/stills.ts out/review/v3 30 252 564 --composition MyFilm [--debug]   # Remotion: frames at 60 fps
```

- `--cues` is frame 0, every `film.json` cue, and the middle and last word of every voice line, each printed with the line being said. It is the same set every round, and the place to see whether the screen says what the voice is saying. Add the holds and handoffs it misses; look at full resolution for small text and at the sheets for rhythm.
- `check` is a report, not a rule: run it at holds and on frame 0 (mid-move frames flag on purpose), and judge each finding. A background wall of tiny text may be the idea; a cropped or covered line being read never is.
- `--cold` also draws each time in a fresh page and reports a frame that differs from the same frame drawn after others. A render draws frames in another order than a preview does (parallel workers, a fresh browser per segment), so such a frame flickers or jumps there. Fix the cause (engine-html.md "Rules for scene code") before the first draft render.

## 2. A draft, measured, then watched

```bash
node film.mjs render draft --scale 0.5
uv run --with numpy --with imageio-ffmpeg python3 $SKILL/scripts/energy.py out/draft/draft.mp4 [--dead 0.6] [--span 1.5]
```

- Every render prints a `cover (frame 0)` line and saves the cover at thumbnail size: look at it.
- A fix to one moment needs a slice, not the film: `node film.mjs render fix --from 21 --to 26` around it, or stills. Render the whole draft again once per round, after that round's fixes, for `energy.py` and the sheets. One film rendered its full draft 22 times while fixing single moments.
- `energy.py` prints the energy curve with the sound's loudness beside each window, still stretches, and loud hits that land on a still picture. Its defaults suit a punchy social cut; raise `--span` for types that want calm (a landing loop, an explainer's diagram). Look at each stretch it names: a line being read can hold still, a gap nobody chose should move. Compare drafts on mean motion and still seconds.
- Then look at the draft as a first-time viewer meets it: contact sheets at phone width for the picture (`ffmpeg -v error -i out/draft/draft.mp4 -vf "fps=3,scale=360:-2,tile=6x3" out/review/draft-%02d.png`) and the loudness column for the sound, since you cannot hear it. Ask whether you would stop scrolling. Look for where it sags, whether the peak is clearly the biggest moment, whether moves repeat until they feel like a template, whether key words act themselves out ("faster" moving fast), and whether the camera ever makes a nudge instead of a decision (under about 20% zoom or a line's height reads as a mistake).
- When you hand off, say plainly what you would still call flat, and what you did about it.

## 3. Fresh eyes on the first full draft and the final

Checks cannot say "that empty band looks wrong" or "that word is hard to hear". Two reviewers who have not watched the build can ([critic.md](critic.md)). Run both on the first full draft and on the final, not after every change:
- **The critic** looks: pack the film with `critic.py` and give it, with critic.md, to a new subagent that gets nothing from the build conversation. It sees a frame every third of a second and a faster strip around each cue, so trust it on layout, legibility, cropped or covered text and the cover. Check what it says about motion against the film: a move shorter than a third of a second can fall between its frames, and on one film it scored energy and peak 2 where the watcher, seeing the same cut move, scored them 4 and 5.
- **The watcher** listens too: `watch.py` sends the film itself to Gemini (`GEMINI_API_KEY`; the film is uploaded to Google's API). It judges what stills cannot: a word that is hard to make out, a hit before or after its picture, and whether the peak is the biggest moment in sound and picture together, and it times each finding to about a tenth of a second. It hears a 16 kbps mono reduction, so levels still come from `energy.py` and `verify.py`. Its silence is not a pass. In a blind test, three runs on two models missed a pause before the peak that the product owner heard as lag; one timed that pause to the tenth of a second and called it clean. Its scores are not steady either: a cover and an idea it scored 5 on one cut it scored 3 on the next, nearly unchanged, so read its findings and not its numbers.

A finding is a place to look, not a target: confirm it in the frames or the mix before you act on it, then fix it or say why it stays. Give each review one round of fixes. When the reviewers disagree, or a second review repeats a matter of taste you already weighed, put it to the user with the frames instead of running another round; more rounds move the scores without settling it. Show the user both verdicts, and set what each reviewer said back beside the sentence the film was built to leave (critic.md).

## 4. Things no check catches

- **Stray layers:** one still per scene; nothing from another scene shows through (empty tiles, a faded card).
- **Handoffs:** each magic move lands exactly on its destination (measured).
- **Loops:** the last frame equals frame 0 (decode and compare).
- **Pops:** a layer that shows for a frame or two at a handoff, or text crossing during a swap. Samples a third of a second apart step over them, so look at 12 consecutive frames around every handoff and the fastest moves: `ffmpeg -ss <t - 0.1> -i out/draft/draft.mp4 -vf "scale=320:-1,tile=6x2" -frames:v 1 out/review/strip-<t>.png`.
- **Fast moves in the final encode:** motion blur can smear text on a whip (render.md).

## 5. Show the product owner

The first full draft goes to them after one round of fixes, not once the scores stop moving (SKILL.md). Ask for one watch on a phone with the sound on, and one with it off where the film plays muted. Only they can say which scene a newcomer fails to follow. The watcher hears a reduced copy and can miss a pause that drags (section 3), so how the mix plays on a real speaker and how the pauses feel are theirs to judge too. Their notes come fast and precise ("remove the borders", "same background", "it's slow here"). Fold every note into BRAND.md or the prompt, so the next film starts from it.
