# Music and sound: compose or cut, measure the beat, land every hit, mix

Scripts live in `$SKILL/scripts/` (`$S` below, where `$SKILL` is this skill's folder) and run from the film folder. Python runs through uv, so nothing is installed system-wide: `uv run --with numpy --with imageio-ffmpeg python3 $S/<script>.py`. `beats.py` takes `--with beat-this==1.1.0` in place of `--with numpy` (B). `eleven.py` needs only `python3`.

The order, whatever the source: compose or pick the track, measure its grid (B), cut it on bars to the film's cues (C), separate the cut track into stems if the mix needs them, then mix.

## Where the music comes from (interview choice)

### A. Composed with ElevenLabs (default when there is no track)

Use it when the film's acts are known. With a voiceover, compose after the lines are placed (voice.md).

```bash
python3 $S/eleven.py music-plan --prompt "<genre, mood, tempo in BPM, instruments; no vocals>" --seconds 30
# edit audio/music-plan.json: one section per act, duration_ms = the act's length, lines [] (instrumental)
python3 $S/eleven.py music --plan audio/music-plan.json
```

- **Chunk `text` and section `lines` are lyrics: the model sings them.** An instrumental chunk's `text` is the tag alone (`[Drop]`); every direction ("big wide chords, triumphant") goes in `positive_styles`. A description left in `text` once came back spoken over the end card, under the voiceover. `eleven.py music` refuses such a plan (`--lyrics` when the words are meant), then transcribes the result and fails on any word. `eleven.py listen <file>` runs the same check on any track.
- `music-plan` is free and returns sections; `eleven.py music` converts them to the `chunks` that `music_v2` and `music_v2_5` take (you can also write chunks directly: `{"chunks": [{"text": "[Intro]", "duration_ms": 4000, "positive_styles": [...], "negative_styles": ["vocals"]}]}`). Edit the plan so the sections are the film's acts: the intro under the opening, the build under the features, the drop on the strongest moment, and a resolve under the end card.
- **The models keep the total length and the tempo, not where the sections change.** One 22 s plan at 120 BPM with its drop at 12 s came back 22.03 s long from both models, at 119.99 BPM (`music_v2_5`) and 119.97 BPM (`music_v2`). `music_v2_5` dropped 4 s late, after a bar of hush (+11.7 dB). `music_v2` never dropped (+3.7 dB at most), and an earlier `music_v2` plan with its drop at 3.06 s came back as one slow build. So read where `beats.py` puts the biggest rise, and if the drop isn't on the peak, cut on bars (C): end the build on a bar at the hush, then play the drop on the peak. A silence between them works when it lasts a whole number of beats, so the drop lands on the pulse the build set up (C).
- `music_v2_5` is the default here: from one try each, it was the one that built a real drop.
- A plain `--prompt --seconds` works for a sketch, but its length can drift (seen: 96 s returned for a 30 s ask). If it does, cut on bars (C).
- Put the tempo in the prompt (four tracks asked for 120 BPM measured 119.96 to 120.04), then measure it anyway (B).
- The track is licensed under the account's ElevenLabs plan. Write that into BRAND.md.

### B. The beat grid (for any music)

```bash
uv run --with beat-this==1.1.0 --with imageio-ffmpeg python3 $S/beats.py --drums audio/music.mp3 --out beats.json
# with stems, loudness per bar for each: --stem bass=audio/stems/bass.mp3
```

- Beats and downbeats come from Beat This!, a beat-tracking model (MIT), run on the CPU in a few seconds. The first run downloads torch and the model (81 MB); later runs reuse the cache. The grid is the one tempo and phase that fit the model's beats best, and the downbeat is the beat of the bar most of the model's downbeats fall on.
- It prints the tempo, the first downbeat, `gridCheckMs.spread` (how far the model's beats sit from the grid; 3 to 9 ms on four composed tracks), the biggest rise in the drums with its bar and beat, and the loudness per bar. Then any warnings:
  - Model beats off the grid, with their span: a free intro, a fill or a tempo change. The grid doesn't hold there, so listen before cutting in it.
  - Too few model downbeats on one beat of the bar: the meter or the downbeat may be wrong. `--meter 3` is waltz time, and `--downbeat <seconds>` sets a known downbeat.
  - The biggest rise lands off a downbeat. A drop starts a section, so if that rise is the drop, rerun with `--downbeat <its seconds>`.
- `--bpm` fixes the tempo and fits only the phase.
- `--numpy` measures without torch or a network (`uv run --with numpy --with imageio-ffmpeg`). Keep it for offline use: it read a 120 BPM track as 160 BPM and put another track's downbeat a beat late, and every cut on bars inherited the error.
- Copy `bpm`, `firstDownbeat` (as `firstBeat`, with `pickupBeats: 0`) and `beatsPerBar` into `film.json` `grid`.
- Read the song map from the per-bar loudness: intro, drops, breakdowns, the big hit, the outro. Map the story onto it: busy scenes on the full groove, the strongest moment on the drop, the end card on the ring-out. Listen to the peak once before you cut to it.

### C. Cut on bars, placed on the film's cues (any track)

A composed track that missed its marks, or the user's licensed track:

```json
{
  "source": "audio/music.mp3",
  "out": "audio/music.wav",
  "bpm": 120,
  "firstDownbeat": 0.04,
  "segments": [
    { "fromBar": "start", "toBar": 15, "endAt": "hush", "why": "the build ends on a bar at the hush" },
    { "fromBar": 15, "toBar": 19, "at": "peak", "why": "after the silence, the drop lands on the peak" },
    { "fromBar": 17, "toBar": 19, "why": "two groove bars again under the list" },
    { "fromBar": 19, "toBar": "end", "why": "the outro" }
  ],
  "duration": 44,
  "fadeOutSeconds": 1.2
}
```

```bash
uv run --with numpy --with imageio-ffmpeg python3 $S/audio-edit.py edit.json
```

- Bars are `beats.json` bar indexes (0 is the first downbeat; `"start"` and `"end"` are the song's very beginning and end), and `toBar` is exclusive. Each cut gets a 5 ms fade.
- A segment follows the one before it, so the grid runs straight through the join. A segment can instead carry a film time, in seconds or as a `film.json` cue name: `at` plays its first sample then, and `endAt` ends it then, its start trimmed so it fits after the segment before. The gap before a placed segment is silence, the hush before a hit. Make it a whole number of beats, or none: `audio-edit.py` reports a gap that is not, because the next downbeat then lands off the pulse of the bars before it. A pause of 0.7 of a beat before a final chord was heard as lag, and the watcher called a 0.6-beat hush too long. A segment placed less than a frame inside the one before it follows it, since bars of a measured tempo rarely end on a round time; a larger overlap is an error.
- List a segment twice to loop its bars, a groove held under a longer scene.
- It prints where each segment lands on the film's clock. After an `at`, the bars run from that time, so key later beats to the printed times.
- Cut slow intros short.
- Keep licensed audio out of any git repo, and write its source and license into BRAND.md.

### D. Synthesized in code (no key needed)

Write a short numpy script (`uv run --with numpy python3 synth.py`) that renders WAVs straight onto the grid: a kick and hat bed at the film's tempo, a riser that ends on the peak, sub thumps, clicks. It is free, and every hit lands on the exact sample. Plain synthesis sounds thin next to a composed track, so make it the score only when the idea wants a synthetic sound (a terminal, a machine, a countdown); otherwise use it for sound effects and placeholders. Point `film.json` `music.file` and `sfx[].file` at the WAVs; `mix.py` reads any format.

### E. Silent

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
Generate a small set once (`riser`, `impact`, `whip`, `texture`, `click`) and reuse them; vary gain, not files. Without a key, synthesize the set instead (D).
- In `film.json` `sfx`, `hit` is the moment the transient should land: film seconds, a cue name (`"peak"`), or a word of a voice line (`"v2:reconciled"`, `"v2:SAP#2"` for its second time), with an optional `offset` in seconds (`{"file": "audio/sfx/click.mp3", "hit": "v6:signs", "offset": -0.05}`). Words match the way `wordAt` matches them, so a hit follows its word when the line is retimed or regenerated. `mix.py` prints each resolved time, stops on a word or cue it can't find, and starts each clip at `hit` minus its peak.
- **Measure every generated effect before you place it.** Prompts that read fine have returned a marble clack peaking at -55 dBFS and a whoosh at -80 dBFS, which no gain setting rescues, and a riser that peaked before its end and trailed into the hush after it. Because `mix.py` places a clip by its peak, a peak in the wrong place moves the hit. Print each clip's length, its peak time and its level per 0.1 s (a few lines of numpy) before you choose its `hit`; regenerate or synthesize (D) any clip that comes back quiet, and trim a tail that would run into a planned silence. `mix.py` also warns about a nearly silent clip.
- The music's drop and the picture's peak are the same frame. After generating, check the biggest rise `beats.py` prints; if the drop missed, cut on bars (C) so it lands.

## Traps

- **Chunk `text` is sung.** Direction written there comes back as a second voice; keep it to the tag and put direction in `positive_styles` (`eleven.py music` guards and checks this).
- **Sections must be 3 s or longer**, or the request fails.
- **Generated length and section timing drift:** a bare prompt once returned 96 s for 30 s, and a plan keeps the total but not where the drop lands. Measure, then cut on bars.
- **Compressor make-up gain can push the bed past 0 dBFS**, so every loud beat hits the limiter. Leave it off, or cap the bed with a limiter. When the limiter works hard, `mix.py` says when the mix peaks and which sources are hottest.

## The mix

```bash
uv run --with numpy --with imageio-ffmpeg python3 $S/mix.py     # -> audio/mix.wav, -14 LUFS
```

- It places the music (from `music.from`, with fades), the voice lines at their `at`, and the SFX on their hits. The music ducks under the voice. One linear gain brings the mix to -14 LUFS, and a limiter holds peaks at -1 dBFS; it warns when the limiter has to work hard.
- `music.dips` lowers the music where no voice plays: `[["reveal", 24.5, -4]]` is 4 dB down from the `reveal` cue to 24.5 s, with a 0.4 s ramp on each side. Its ends are seconds, cue names or words.
- **Stems keep the groove under the voice.** After the cut (C), `python3 $S/eleven.py stems audio/music.wav --out audio/stems` writes one MP3 per stem (`bass`, `drums`, `guitar`, `other`, `piano`, `vocals`), each the track's full length. Set `music.stems` to `{name: file}` for those files and keep `music.file` on the cut track: `mix.py` plays the stems instead and lines them up with it first, because the MP3 stems came back 25 ms late (the encoder's delay). Set `music.duck_stems` to the names the voice should push down, leaving the drums out so they keep driving. Separate the cut track, not the source: then the stems carry every cut, placement and loop.
- It warns when voice lines overlap, run past the end, or the music is shorter than the film.
- Check the words before you render: `uv run --with numpy --with imageio-ffmpeg python3 $S/verify.py audio/mix.wav --script film.json` transcribes the mix and lists every script word that did not come back, one a riser or the music buried (voice.md has the fix). Found here it costs a mix; found in the final it costs a render. It needs `ELEVENLABS_API_KEY`.
- Re-run it after any timing change. `film.mjs render` picks up `audio/mix.wav` automatically, and `#play` previews with it.
