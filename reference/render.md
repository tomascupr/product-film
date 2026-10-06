# Final render, verification and delivery

## Render

**HTML engine** (engine-html.md):

```bash
node film.mjs render <name> --blur --poster <headline seconds> [--webm] [--segments]
```

The output goes to `out/<name>/`: `<name>.mp4` with `audio/mix.wav`, `<name>-muted.mp4`, and optionally `<name>.webm` and `<name>-poster.jpg`.
- A long blurred render can stall in one browser: a screenshot times out after tens of thousands of them. `--segments` renders the film in 10 s parts, each in a browser of its own, renders a failed part once more and joins them, so use it when subframes times seconds gets large (field-notes.md has the measured case).
- Read the render's last line. A failed render ends on `FAILED:`, exits non-zero and leaves the render before it in place, so the old file is still there to be mistaken for the new one.

**Remotion engine** (engine-remotion.md):

```bash
node scripts/render.ts <CompositionId> <name> --duration <s> --poster <s>
```

It renders a 60 x N fps PNG master (N subframes per frame, `--blur N`, 4 by default; H.264 CRF 8, 4:4:4, BT.709), blends the subframes into 60 fps motion blur with a full ffmpeg, and writes `out/<name>/`: `<name>-1080p60.mp4` (muted), `<name>-1080p60-audio.mp4` (with `audio/mix.wav`), `<name>-1080p60.webm`, `poster.jpg` and `loop-seam.png`. The master and the intermediate are deleted at the end.

Both engines:
- Motion blur averages N subframes per frame: `--blur` alone is 4, `--blur 8` or `--blur 16` takes more. Four suits most moves. On a fast whip, a whole-frame shake or anything spinning, four show as distinct ghost copies (a stack of rings, doubled type) rather than a smear, so raise N for a film with those moves; 16 smoothed a camera whip and a spinning logo that 4 and 8 still stepped. Render time grows with N: use it for finals only, and run long renders as a background job while you review other things. The harness says when the job ends, so don't poll it with `sleep` loops; one film spent two hours in them.
- Frame 0 must work as a cover on its own (review.md), because many players ignore the poster. Where a platform takes a custom thumbnail, upload the poster too.
- The poster is a settled frame that states the message (the headline, the product name with its status), never a mid-effect frame and never frame 0.
- After the blurred render, look at the encode's consecutive frames at the fastest moves (the strip in review.md, on `out/<name>/<name>.mp4`): motion blur can smear text on a whip, and too few subframes show as ghost copies.
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
- A version you may have to rebuild keeps its sources beside the video: `film.json`, `index.html` and `audio/vo/`, because the next `tts` overwrites the takes. A take lost that way can come back from the ElevenLabs history (`GET /v1/history`, then `/v1/history/<id>/audio`); time it again with `eleven.py align <line> <file>`.
- Send the version with sound for review, the muted file for a landing page, and the WebM and poster when asked. Add a two-line caption of what changed.
- Report durations, sizes and the verify output, verbatim.
- Do not publish, upload or commit anything unless asked.
