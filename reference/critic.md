# Fresh-eyes critic

The prompt for a reviewer that has not seen the film being built. Whoever built a film has watched it a hundred times and knows what every frame is meant to say; a first-time viewer only sees what is there. That gap is where flat stretches, empty space, unreadable covers and cropped words hide. Checks measure what they can; this review catches what a person would notice in one watch.

## How to run it

1. Bring `film-prompt.md` up to date with the film as built (the frame-0 row, the beat sheet, the camera plan). The critic judges against it, and a stale brief turns into findings that ask for what was deliberately changed.
2. Pack the draft or final: `uv run --with numpy --with imageio-ffmpeg python3 $SKILL/scripts/critic.py out/<name>/<name>.mp4 [--peak <s>]`, from the film folder. It writes `out/critic/<name>/` with a README listing what to look at, in order.
3. Give a fresh reviewer everything below the line, plus the folder's path. In Claude Code, that is a new subagent: pass this prompt and the path, and nothing from the build conversation, because its value is that it has not seen it. Without subagents, open a new session with the same two things.
4. Treat each finding as a place to look: confirm it in the frames (review.md says what each reviewer can and cannot see), then fix it or say in the handoff why it stays. Compare SAID BACK with the sentence the film was built to leave (`film-prompt.md`): a gap there matters more than any score. A second review after the fixes uses a new reviewer too.

## A second reviewer that watches and hears

The pack is silent and shows a frame every third of a second. `watch.py` gives this prompt to Gemini, which watches the film itself and hears it, so it also judges the sound. Run it next to the critic, not instead of it.

1. From the film folder: `python3 $SKILL/scripts/watch.py out/<name>/<name>.mp4`. It needs `GEMINI_API_KEY` and ffmpeg, and reads `film-prompt.md` as the brief (`--brief` for another file).
2. It uploads the film to Google's Files API, plus its soundtrack as a separate lossless file: the API hears the sound inside a video at 1 kbps, and a separate file at 16 kbps. Both are deleted when the review ends, also when it fails, and the request asks Google not to store it. Don't run it on a film that must not leave the machine.
3. It is fresh by construction: it gets only the two files, the brief and the prompt below, with its **What you have.** paragraph swapped and a sound section added. It answers in the same shape plus a SOUND block, prints the tokens and an estimated cost, and saves all of it to `out/watch/<name>.txt`: about $0.14 for a 63 s film and $0.05 for a 20 s one on the default `gemini-3.8-flash`. On the same 63 s film, `--model gemini-3.1-pro-preview` cost 2.7 times as much and found less.
4. Treat its findings like the critic's.

---

You are reviewing a short motion film as a first-time viewer would meet it: a thumbnail in a feed, then one watch, often on a phone. You have not seen it being made, and that is the point: say what you actually see, not what it was probably meant to show.

**What you have.** A folder packed from the film. Its `README.txt` lists the files in the order to look at them; `cover.png` is the cover. The contact sheets show one frame every third of a second, so a pattern that repeats across several frames is something a viewer sits through. Each `cue-*.png` strip shows ten frames a second around one of the film's cues: judge a hit or a handoff there, because it can be over between two frames of a sheet. Open single frames from `frames/` whenever a detail matters. `energy.txt` is measured motion: use it to confirm or question what the sheets suggest. There is no audio in the pack: `energy.txt` prints the sound's loudness beside the motion, so judge sound through it and the brief.

Judge the film first, as a viewer, before reading the brief, and write SAID BACK then: what the film told you, from the film alone. Then read the brief and judge whether the film delivers it.

Look for these, because they are what separates a film people finish from one they scroll past:
- **The cover.** Would someone click the first frame at thumbnail size? Is the subject named and whole, or is it a crop of nothing, mid-motion, or blank?
- **The first second.** Does something happen right away that makes you want the next second?
- **What each scene says.** Can you tell what is happening in every scene, and why it is in the film? Name any scene you could not follow, and say what you took it to show.
- **Energy.** Where does it sag? A stretch of near-identical frames is a stretch the viewer waits through. Is there one clear peak, bigger than everything around it, and does the film build to it and ride out of it, or does every moment weigh the same?
- **Repetition.** Does the same move, transition or layout happen three or more times, so the film starts to feel like a template?
- **Composition.** Is anything off balance: a large empty band, content crowded to one side, a line that sits low with nothing under it?
- **Readability.** Can every line being read be read at phone size? Is any word cropped by the frame, covered, crossed by other text, or on screen too briefly to read?
- **Generic looks.** Centered text fading up in every scene, slow drifts over screenshots, gradient blobs, glows and particles, floating device mockups, numbered chapter cards, labels parked in the corners, decorative frame borders, the same transition everywhere.
- **The ending.** Does it land, or fade out politely? Does the last image say who made this and what to do next?
- **Against the brief.** Does the film say what the brief says, in the order it plans, with the peak where it plans it? Anything on screen that the brief does not contain?

The brief's claims, permissions and dated decisions (casing, colors, what the product does) are settled by the people who own them; judge how the film delivers them, not whether they are allowed.

Report everything you notice, from serious to small. Rank it yourself; the builder decides what to fix. Keep praise to what should not change.

Answer in exactly this shape:

```
VERDICT: <one sentence a colleague would say after one watch>
SAID BACK: <what the film told you, in your own words: what the product is and what it does for whom. Write "unclear" for a part you could not tell>
WOULD CLICK THE COVER: yes | no, because <reason>
SCORES (1-5): cover <n> · first second <n> · clarity <n> · energy <n> · peak <n> · composition <n> · readability <n> · originality <n> · ending <n> · brief <n>
FINDINGS:
1. [high|medium|low] <time or range, e.g. 6.0-7.5 s> <what you see> -> <a concrete fix>
2. ...
KEEP: <what works and should survive the fixes>
```
