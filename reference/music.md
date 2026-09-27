# Music and sound: compose or cut, measure the beat, land every hit, mix

Scripts live in `$SKILL/scripts/` (`$S` below, where `$SKILL` is this skill's folder) and run from the film folder. Python runs through uv, so nothing is installed system-wide: `uv run --with numpy --with imageio-ffmpeg python3 $S/<script>.py`. `eleven.py` needs only `python3`.

## Where the music comes from (interview choice)

### A. Composed with ElevenLabs (default when there is no track)

Use it when the film's acts are known. With a voiceover, compose after the lines are placed (voice.md).

```bash
python3 $S/eleven.py music-plan --prompt "<genre, mood, tempo in BPM, instruments; no vocals>" --seconds 30
# edit audio/music-plan.json: one section per act, duration_ms = the act's length, lines [] (instrumental)
python3 $S/eleven.py music --plan audio/music-plan.json
```

- **Chunk `text` and section `lines` are lyrics: the model sings them.** An instrumental chunk's `text` is the tag alone (`[Drop]`); every direction ("big wide chords, triumphant") goes in `positive_styles`. A description left in `text` once came back spoken over the end card, under the voiceover. `eleven.py music` refuses such a plan (`--lyrics` when the words are meant), then transcribes the result and fails on any word. `eleven.py listen <file>` runs the same check on any track.
- `music-plan` is free and returns sections; `eleven.py music` converts them to the `chunks` that `music_v2` takes (you can also write chunks directly: `{"chunks": [{"text": "[Intro]", "duration_ms": 4000, "positive_styles": [...], "negative_styles": ["vocals"]}]}`). Edit the plan so the sections are the film's acts: the intro under the opening, the build under the features, the drop on the strongest moment, and a resolve under the end card. `music_v2` keeps section durations.
- **`music_v2` keeps the total length, not where the sections change.** A plan with the drop at 3.06 s came back as one slow build with no drop. After generating, read the per-bar loudness (`beats.py`) and check the peak moment. If the drop isn't there, cut on bars (C): end the build segment exactly on the peak and jump to the loudest bar. A short silence before the final hit reads as a deliberate stop.
- A plain `--prompt --seconds` works for a sketch, but its length can drift (seen: 96 s returned for a 30 s ask). If it does, cut on bars (C).
- Put a tempo in the prompt, then measure it anyway (B). Generated music is not always on the tempo you asked for.
- The track is licensed under the account's ElevenLabs plan. Write that into BRAND.md.

### B. The beat grid (for any music)

```bash
uv run --with numpy --with imageio-ffmpeg python3 $S/beats.py --drums audio/music.mp3 --out beats.json
# with stems: --drums stems/drums.mp3 --stem bass=stems/bass.mp3 --stem melody=stems/melody.mp3
```

- Tempo comes from autocorrelation, refined by a comb. The downbeat is the bar position where the stems come and go.
- Check `gridCheckMs.spread` (under 10 ms is good; `meanOffset` reads about -15 ms by design, against the smoothed onset curve). It shows the grid is steady, not that its phase is right, so listen once with clicks on the grid. `--bpm` skips the search, and `--meter 3` handles waltz time.
- Copy `bpm`, `firstDownbeat` (as `firstBeat`, with `pickupBeats: 0`) and `beatsPerBar` into `film.json` `grid`.
- Read the song map from the per-bar loudness it prints: intro, drops, breakdowns, the big hit, the outro. Map the story onto it: busy scenes on the full groove, the strongest moment on the drop, the end card on the ring-out.

### C. The user's licensed track: cut it on bars

```json
{
  "source": "audio/song.mp3",
  "out": "audio/music.wav",
  "bpm": 150,
  "firstDownbeat": 1.2516,
  "segments": [{ "fromBar": 1, "toBar": 17, "why": "..." }, { "fromBar": 36, "toBar": 49, "why": "..." }],
  "duration": 52.8,
  "fadeOutSeconds": 1.2
}
```

```bash
uv run --with numpy --with imageio-ffmpeg python3 $S/audio-edit.py edit.json
```

- Bars are `beats.json` bar indexes (0 is the first downbeat; `"start"` means the song's very beginning), and `toBar` is exclusive. The film's bars are the segments back to back, and the grid runs straight through every join. Each cut gets a 5 ms fade.
- Film length is a whole number of bars. Cut slow intros short.
- Keep licensed audio out of any git repo, and write its source and license into BRAND.md.

### D. Silent

Pick a tempo anyway (120 BPM), set `film.json` `grid` from it, and plan on it.

## Sound effects

```bash
python3 $S/eleven.py sfx --text "soft UI click, dry, close" --seconds 0.5 --out audio/sfx/click.mp3
```

Sound design carries as much of the energy as the picture. Layer it like a trailer, not a UI demo:
- **Into the peak:** a riser that ends just before it, then a beat of near-silence (a pre-hit stop) that nothing else plays through: end the riser before the hush and check `audio/bed.wav` there. A hush filled by a riser's tail makes the peak no louder than what came before, and `energy.py` will not find it.
- **On the peak and the final hit:** an impact with sub bass, stacked with the moment's own sound (a clack, a stamp, a click).
- **On the moves that matter:** a whoosh sized to the move. On every move it becomes the stock whoosh-and-ding look.
- **A texture bed** from the idea's world (flaps clattering, a crowd, keys) under the build and the ride.
- **UI sounds** (clicks, pings, chimes) stay short and dry, one per meaningful event.
Generate a small set once (`riser`, `impact`, `whip`, `texture`, `click`) and reuse them; vary gain, not files.
- In `film.json` `sfx`, `hit` is the moment the transient should land. `mix.py` finds each clip's peak and starts it at `hit - peak`.
- The music's drop and the picture's peak are the same frame. After generating, check the per-bar loudness from `beats.py`; if the drop missed, cut on bars (C) so it lands.

## Traps

- **Chunk `text` is sung.** Direction written there comes back as a second voice; keep it to the tag and put direction in `positive_styles` (`eleven.py music` guards and checks this).
- **Sections must be 3 s or longer**, or the request fails.
- **Generated length and section timing drift:** a bare prompt once returned 96 s for 30 s, and a plan keeps the total but not where sections change. Measure, then cut on bars.
- **Compressor make-up gain can push the bed past 0 dBFS**, so every loud beat hits the limiter. Leave it off, or cap the bed with a limiter. When the limiter works hard, `mix.py` says when the mix peaks and which sources are hottest.

## The mix

```bash
uv run --with numpy --with imageio-ffmpeg python3 $S/mix.py     # -> audio/mix.wav, -14 LUFS
```

- It places the music (from `music.from`, with fades), the voice lines at their `at`, and the SFX on their hits. The music ducks under the voice. One linear gain brings the mix to -14 LUFS, and a limiter holds peaks at -1 dBFS; it warns when the limiter has to work hard.
- It warns when voice lines overlap, run past the end, or the music is shorter than the film.
- Re-run it after any timing change. `film.mjs render` picks up `audio/mix.wav` automatically, and `#play` previews with it.
