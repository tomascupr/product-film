# product-film

An agent skill that makes motion films in code for a product or brand: launch films, teasers, feature demos, explainers, social cuts, landing loops, partner co-launches, event openers and data stories. The film is built from the product's own design system, components and voice, cut to a voiceover, music and sound design, and checked by measurement rather than by eye.

Every frame is a pure function of time, rendered by headless Chrome (or Remotion) and encoded by ffmpeg, so a film is a folder of code you can diff, re-render and change.

## What it does

1. Reads the product's code and site for its colors, type, components, logo and copy rules.
2. Interviews you for the film type, the brief, the sound and the engine.
3. Pitches ideas, then writes a beat sheet with an energy curve, a camera plan and a planned first frame (the cover most players show), and checks the peak in a short motion test before building everything.
4. Generates the voice (with word timings), music and sound design with ElevenLabs, or uses your own.
5. Builds the scenes keyed to words and beats. Camera holds are fitted to the text being read and kept on the content, so lines are never cropped and the frame never drifts into empty space.
6. Reviews drafts by measurement: `energy.py` finds dead stretches and loud hits that land on still frames, and `film.mjs check` finds text that is too small at phone size, covered, overlapping or cropped by the camera.
7. Renders the final with motion blur, saves the first frame at thumbnail size with its text checked, and verifies duration, color tags, loudness, a first frame that is not blank, audio gaps and that every script word survives the mix.

## Requirements

- Node 20+ and pnpm
- Python 3 and [uv](https://docs.astral.sh/uv/) (scripts run as `uv run --with numpy --with imageio-ffmpeg python3 …`)
- ffmpeg on PATH
- Google Chrome, or any Chromium via `CHROME_PATH`
- Optional: an ElevenLabs API key in `ELEVENLABS_API_KEY` for voice, music and sound effects
- Optional: a Remotion company license, if you choose the Remotion engine above Remotion's free team size

## Install

Copy or clone this folder into your agent's skills directory, for example `~/.claude/skills/product-film/` for Claude Code. Then ask for a video ("make a 20 s launch teaser for our new feature") or invoke `/product-film`.

## Layout

| Path | What it holds |
|---|---|
| `SKILL.md` | Principles, workflow, quality floor, traps |
| `reference/` | One file per step: discovery, interview, story (film types), ingredients, voice, music, engines, review, render |
| `templates/html/` | The HTML engine: `index.html`, `kit.js` (time, springs, camera moves, `fit` and `inside` for text holds, shake, beat kicks, color mixing), `film.mjs` (serve, stills, measure, check, render with a cover preview) |
| `templates/remotion/` | The Remotion engine's config and kit twins |
| `templates/BRAND.md`, `templates/film-prompt.md` | The product kit and the per-film brief |
| `scripts/` | `eleven.py`, `beats.py`, `audio-edit.py`, `mix.py`, `energy.py`, `verify.py` |
| `tests/` | `node --test tests/` for the kit's camera and color maths; `tests/check/` is a fixture for `film.mjs check` |

## Credits

Forked from [Rieranthony/product-film-skill](https://github.com/Rieranthony/product-film-skill) (MIT). This fork adds the HTML engine, the Remotion gate, ElevenLabs sound, film types, the energy plan and the measured checks. MIT licensed; see `LICENSE`.
