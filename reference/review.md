# Review loop: look, measure, fix, repeat

Stills are cheap; renders are not.

## 1. Stills and the text check

```bash
node film.mjs stills out/review/v3 0.5 4.2 9.4 14.0 21.5        # HTML engine: seconds; also writes sheet.png
node film.mjs measure 9.4                                         # target boxes, for moves and cursor stops
node film.mjs check 0 4.2 9.4 14.0 --view 390                     # text too small at phone width, covered, overlapping or cropped
node scripts/stills.ts out/review/v3 30 252 564 --composition MyFilm [--debug]   # Remotion: frames at 60 fps
```

- Take stills at every scene's first settled frame, every handoff and every key word; look at full resolution for small text and at the sheet for rhythm.
- `check` is a report, not a rule: run it at holds and on frame 0 (mid-move frames flag on purpose), and judge each finding. A background wall of tiny text may be the idea; a cropped or covered line being read never is.

## 2. A draft, measured, then watched

```bash
node film.mjs render draft --scale 0.5
uv run --with numpy --with imageio-ffmpeg python3 $SKILL/scripts/energy.py out/draft/draft.mp4 [--dead 0.6] [--span 1.5]
```

- Every render prints a `cover (frame 0)` line and saves the cover at thumbnail size: look at it.
- `energy.py` prints the energy curve, still stretches and loud hits that land on a still picture. Its defaults suit a punchy social cut; raise `--span` for types that want calm (a landing loop, an explainer's diagram). Fix each finding or name why the stillness stays. Compare drafts on mean motion and still seconds.
- Then watch the draft once with sound and once muted, at 1x, at phone size, and ask whether you would stop scrolling. Look for where it sags, whether the peak is clearly the biggest moment, whether moves repeat until they feel like a template, whether key words act themselves out ("faster" moving fast), and whether the camera ever makes a nudge instead of a decision (under about 20% zoom or a line's height reads as a mistake).
- When you hand off, say plainly what you would still call flat, and what you did about it.

## 3. Fresh eyes on the first full draft and the final

Checks cannot say "that empty band looks wrong". A reviewer who has not watched the build can: pack the film with `critic.py` and give it, with [critic.md](critic.md), to a new subagent that gets nothing from the build conversation. Run it on the first full draft and on the final, not after every change. Fix the high findings or say why they stay, and show the user the verdict and scores.

## 4. Things no check catches

- **Stray layers:** one still per scene; nothing from another scene shows through (empty tiles, a faded card).
- **Handoffs:** each magic move lands exactly on its destination (measured).
- **Loops:** the last frame equals frame 0 (decode and compare).
- **Fast moves in the final encode:** motion blur can smear text on a whip (render.md).

## 5. Show the product owner

Send frames or a draft as soon as a round is coherent. Their notes come fast and precise ("remove the borders", "same background", "it's slow here"). Fold every note into BRAND.md or the prompt, so the next film starts from it.
