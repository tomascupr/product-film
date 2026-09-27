# Review loop: look at frames, fix, repeat

Stills are cheap; renders are not. Review in this order.

## 1. Stills at the moments that matter

```bash
node film.mjs stills out/review/v3 0.5 4.2 9.4 14.0 21.5        # HTML engine: seconds; also writes sheet.png
node film.mjs measure 9.4                                         # target boxes, for moves and cursor stops
node scripts/stills.ts out/review/v3 30 252 564 --composition MyFilm [--debug]   # Remotion: frames at 60 fps
```

- Pick the times from the beat sheet: every scene's first settled frame, every handoff, every key word.
- Look at full resolution for anything with small text, and at the sheet for rhythm and consistency.

```bash
node film.mjs check 4.2 9.4 14.0 21.5 --view 390      # HTML engine
```

- A check, not a rule: it lists text that would be smaller than `--min` px (default 10) at the width people watch at (`--view`, about 390 for a phone feed, wider for a landing page), text partly covered by something painted over it, text overlapping other text, and text running off frame. Hidden text (clipped, or under a whole layer) is skipped. It saves `out/check/<t>-view.png` at the viewing width to look at.
- Run it at settled frames; mid-move frames flag on purpose. Judge each finding: a background wall of tiny text may be the idea, a covered label never is.

## 2. A draft, then a contact sheet

```bash
node film.mjs render draft --scale 0.5                    # -> out/draft/; or: npx remotion render src/index.ts MyFilm out/draft/draft.mp4 --scale=0.5
ffmpeg -v error -y -i out/draft/draft.mp4 -vf "select='not(mod(n\,24))',scale=240:135,tile=9x15:padding=4:color=0x333333" -frames:v 1 -fps_mode vfr out/review/contact.png
```

- Watch the draft with sound once, from start to finish, as a viewer. Pacing problems only show up in motion.
- For a handoff, render a slice at full quality: `node film.mjs render handoff --from 9 --to 10.5`.

## 3. The energy check, before every handoff

Measure first, then watch:

```bash
uv run --with numpy --with imageio-ffmpeg python3 $SKILL/scripts/energy.py out/draft/draft.mp4
```

It prints the energy curve, every dead stretch (more than 1.5 s of stillness, end cards included) and every loud hit in the music and SFX that lands on a still picture. Fix each finding or say why it stays. Compare drafts by mean motion and dead seconds; a new draft should not lose on both.

Then watch the draft muted at 1x on a phone-sized window and ask: would I stop scrolling for this? If the honest answer is "it's fine", it is flat. Then check:

- **Camera:** it changes scale at least three times (macro, wide, push, whip). A camera that only drifts reads as a slideshow. Every move is decisive: a nudge (under ~20% zoom or a line's height) reads as a mistake. Merge it into one hold that frames both lines, or make it a real move.
- **Escalation:** each scene is bigger, faster or closer than the last. The same transition repeated three times is a template, not a film.
- **One peak:** the strongest moment gets everything at once: the music's drop, the biggest hit, the biggest scale change, the brand color flooding. Plan the music so the drop lands on it (music.md), don't hope.
- **Words act themselves out:** "faster" moves fast, "sharper" snaps into focus, "live" switches on. A key word that looks like every other word is a missed moment.
- **Contrast:** stillness before the peak, speed after it. Big against small, dark against the brand color.
- **Frame 0 and the ending:** every render prints a `cover (frame 0)` line and saves `<name>-cover-300.png`. Look at it: would someone click it? The subject is whole and readable, and the line reports nothing cropped, covered or mid-move. The first second then moves. The ending lands on a hit; it doesn't fade in politely.

Name what's flat when you hand off, with the fix you made or propose. Never hand off a draft you'd call flat.

## 4. The checklist, every round

- **Background:** one color. No invented shades. Surfaces only where the product has them.
- **Borders:** none around floating elements. Lines only where they mean something.
- **Text:**
  - above everything, readable at 1080p, never off frame
  - never cropped by a camera push: run `check` at every camera hold, not only at wide frames
  - never covered by a cursor or chip
  - never crossing other text in a move
  - never re-centering while it builds
- **Words:** fewer. Anything that restates the picture goes. Brand names have their logos.
- **Loading states:** buttons keep their width.
- **Textures:** calm behind UI, thinned behind words.
- **Pacing:** something happens on every beat. No dead bar. Nothing too fast to read.
- **Energy:** the energy check above passes.
- **Handoffs:** each lands exactly on its destination (debug-measured).
- **Brand element (if any):** on brand, alive from the first second, nothing showing through its cut-outs.
- **Loop:** the last frame equals frame 0 (decode and compare).
- **Stray layers:** one still per scene; nothing from another scene shows through (empty tiles, a faded card).
- **Voice:** every keyed moment lands on or just before its word; no on-screen words fight the voice; the music never buries a key word.
- **Claims:** only what the product does, as the user states it.

## 5. Show the product owner

Send frames or a draft as soon as a round is coherent. Their notes come fast and precise ("remove the borders", "same background", "it's slow here"). Fold every note into BRAND.md or the prompt, so the next film starts from it.
