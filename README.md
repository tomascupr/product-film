# product-film

An agent skill that makes motion films in code for a product or brand: launch films, teasers, feature demos, explainers, social cuts, landing loops, partner co-launches, event openers and data stories. The film is built from the product's own design system, components and voice, cut to a voiceover, music and sound design, and checked by measurement rather than by eye.

Every frame is a pure function of time, rendered by headless Chrome (or Remotion) and encoded by ffmpeg, so a film is a folder of code you can diff, re-render and change.

## What it does

1. Reads the product's code and site for its colors, type, components, logo and copy rules.
2. Interviews you for the film type, the brief, the sound and the engine, and for the sentence a viewer should be able to say after one watch.
3. Pitches ideas, then writes a beat sheet with an energy curve, a camera plan, a planned first frame (the cover most players show) and what a viewer understands from each scene, and checks the peak in a short motion test before building everything.
4. Generates the voice with word timings (one voice or several, directed with audio tags and a pronunciation dictionary, or your own read turned into the voice), music and sound design with ElevenLabs, or uses your own. It measures the beat with a beat-tracking model and cuts the music on bars onto the film's cues. Partners appear in their official identity via Brandfetch.
5. Choreographs with GSAP (letter reveals, drawn lines, flights along a path) and plays Lottie animation, generated footage (fal.ai) and Blender renders, all driven frame by frame so every render is identical.
6. Builds the scenes keyed to words and beats. Camera holds are fitted to the text being read and kept on the content, so lines are never cropped and the frame never drifts into empty space.
7. Reviews drafts by measurement and by fresh eyes: `energy.py` finds dead stretches and loud hits that land on still frames, `film.mjs check` finds text that is too small at phone size, covered, overlapping or cropped by the camera, and frames that change with the order they are drawn in, and `critic.py` packs the draft for a reviewer that never saw the build, who says back what the film told them and scores the cover, clarity, energy, peak, composition, readability and originality. `watch.py` has Gemini watch and hear the film itself, for what a silent pack can't show: a buried word, a hit off its picture. The first full draft goes to you after one round of fixes.
8. Renders the final with motion blur, in fresh-browser segments when the film is long, saves the first frame at thumbnail size with its text checked, and verifies duration, color tags, loudness, a first frame that is not blank, audio gaps and that every script word survives the mix.

## Requirements

- Node 20+ and pnpm
- Python 3 and [uv](https://docs.astral.sh/uv/) (scripts run as `uv run --with numpy --with imageio-ffmpeg python3 …`)
- ffmpeg on PATH
- Google Chrome, or any Chromium via `CHROME_PATH`
- Optional: an ElevenLabs API key in `ELEVENLABS_API_KEY` for voice, music and sound effects
- Optional: a Gemini API key in `GEMINI_API_KEY` for `watch.py`, which uploads the film to Google's API
- Optional: a fal.ai key in `FAL_KEY` for generated footage (`gen.py`), and Blender for 3D renders (tested with 5.2 on Apple Silicon)
- Optional: a Brandfetch key in `BRANDFETCH_API_KEY` (free) for partner logos and colors
- Optional, per film: `pnpm add gsap lottie-web` for GSAP choreography and Lottie animation
- Optional: a Remotion company license, if you choose the Remotion engine above Remotion's free team size

## Install

Copy or clone this folder into your agent's skills directory, for example `~/.claude/skills/product-film/` for Claude Code. Then ask for a video ("make a 20 s launch teaser for our new feature") or invoke `/product-film`.

Start a new film at high reasoning effort (`/effort xhigh` in Claude Code, or `max` when the first seconds have to carry a launch); medium is enough for re-renders and small fixes, and the skill offers the switch when it sends the first draft. Most of a film's time goes to the model's own turns, so `/fast` shortens a session more than any render setting. The skill leaves `effort` out of its frontmatter on purpose: a frontmatter level overrides the session's, so it would also pull a `max` session down to it.

## Layout

| Path | What it holds |
|---|---|
| `SKILL.md` | Principles, workflow, quality floor, traps |
| `reference/` | One file per step: discovery, interview, story (film types), ingredients, voice, music, engines, review, the critic's prompt, render. `field-notes.md` holds dated prices, timings and thresholds |
| `templates/html/` | The HTML engine: `index.html`, `kit.js` (time, springs, camera moves, `fit` and `inside` for text holds, shake, beat kicks, color mixing), `film.mjs` (serve, stills, measure, check, render with a cover preview) |
| `templates/remotion/` | The Remotion engine's config and kit twins |
| `templates/BRAND.md`, `templates/film-prompt.md` | The product kit and the per-film brief |
| `templates/3d/shot.py` | A starting Blender scene for a 3D shot |
| `scripts/` | `eleven.py`, `brandfetch.py`, `beats.py`, `audio-edit.py`, `mix.py`, `energy.py`, `critic.py`, `watch.py`, `gen.py`, `verify.py`. `beats.py` runs a beat-tracking model through uv; its first run downloads torch and the model (about 200 MB) |
| `tests/` | `node --test tests/` for the kit's camera and color maths; `tests/thirdparty/run.sh` proves GSAP and Lottie render frame-exact and a render in segments equal to one in a single browser, `tests/footage/run.sh` does the same for image sequences, and `tests/check/run.sh` covers `film.mjs check` and `stills --cues`; `python3 tests/eleven_test.py` checks word timings and takes; under `uv run --with numpy --with imageio-ffmpeg python3`, `tests/audio_test.py` checks where hits and music segments land and the word check on a mix, and `tests/review_test.py` the critic's pack and the watcher's prompt |

## Changing the skill

A lesson from a film goes where it will be used:
- What a script can check or do becomes a tool or a warning in one, with a test in `tests/` that runs offline on synthetic input. `film.mjs check --cold` started as frames that changed with render order.
- A judgment the model has to make becomes one line in the reference for that step, with its reason.
- A number that will age (a price, a timing, a threshold) goes in `reference/field-notes.md` under its date.
- A product's own rulings go in that product's `BRAND.md`, not here.

`SKILL.md` holds the principles and the workflow and is read in full for every film. An incident told there as a story costs every later film its attention, so the story stays in the commit message.

## Credits

Forked from [Rieranthony/product-film-skill](https://github.com/Rieranthony/product-film-skill) (MIT). This fork adds the HTML engine, the Remotion gate, ElevenLabs sound, film types, the energy plan and the measured checks. MIT licensed; see `LICENSE`.
