# Final render, verification and delivery

## Render

**HTML engine** (engine-html.md):

```bash
node film.mjs render <name> --blur --poster <headline seconds> [--webm]
```

The output goes to `out/<name>/`: `<name>.mp4` with `audio/mix.wav`, `<name>-muted.mp4`, and optionally `<name>.webm` and `<name>-poster.jpg`.

**Remotion engine** (engine-remotion.md):

```bash
node scripts/render.ts <CompositionId> <name> --duration <s> --poster <s>
```

It renders a 240 fps PNG master (H.264 CRF 8, 4:4:4, BT.709), blends 4 subframes into 60 fps motion blur with a full ffmpeg, and writes `out/<name>/`: `<name>-1080p60.mp4` (muted), `<name>-1080p60-audio.mp4` (with `audio/mix.wav`), `<name>-1080p60.webm`, `poster.jpg` and `loop-seam.png`. The master and the intermediate are deleted at the end.

Both engines:
- Motion blur means 4 subframes averaged per frame. Use it only for finals, since it takes 4x the render time. Run long renders in the background and review other things meanwhile.
- Frame 0 must work as a cover on its own (review.md), because many players ignore the poster. Where a platform takes a custom thumbnail, upload the poster too.
- The poster is a settled frame that states the message (the headline, the product name with its status), never a mid-effect frame and never frame 0.
- After the blurred render, look at the encode's consecutive frames at the fastest moves (the strip in review.md, on `out/<name>/<name>.mp4`): motion blur can smear text on a whip.
- The output is BT.709, limited range, and tagged as such.

## Verify before sending

```bash
uv run --with numpy --with imageio-ffmpeg python3 $SKILL/scripts/verify.py out/<name> \
  --duration 30 --bg 10,10,10 [--bg-at 0] [--loop] [--probe 9.4:944,800] [--script film.json] [--allow-gap 12.6]
```

For every deliverable, it checks:
- the duration, to the frame
- the BT.709 tags (matrix, primaries, transfer, limited range)
- frame 0's center against the background (±2), with `--bg`
- the last frame against frame 0, with `--loop`: only encoder noise is allowed
- loudness at -14 LUFS (±1), on files with audio
- probes: each prints a decoded color at a time and position, to check an accent or a surface
- frame 0 is not blank or fading in (it is the cover in many players)
- no silence over 0.1 s inside the film (a splice dropout), unless the gap holds an `--allow-gap` time
- `--script film.json`: the final mix is transcribed and every script word must come back; a lost word is one the music buried. It needs ELEVENLABS_API_KEY.

If the background comes back lighter (#171717 for #0a0a0a), the color range was read wrong. Fix the encode, never the tokens.

## Deliver

- Before the next render, copy the deliverables into `out/v<N>/`. Keep every version.
- Send the version with sound for review, the muted file for a landing page, and the WebM and poster when asked. Add a two-line caption of what changed.
- Report durations, sizes and the verify output, verbatim.
- Do not publish, upload or commit anything unless asked.
