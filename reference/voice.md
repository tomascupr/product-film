# Voice: script, generate, time the film to the words

Only if the interview chose a voiceover. Once there is a voice, it leads the timing: scenes land on words, the music sits under it, and the beat grid only places accents.

## 1. Write the script

- **Budget:** about 2.3 words per second of speech. A 30 s film carries 50 to 60 words, with room for an opening and an end card with no voice.
- **One line per scene or idea.** Each line becomes one clip (`film.json` `voice.lines[]`: `{id, text, at}`), so it can be retimed or regenerated alone.
- **Written for the ear.** Short sentences, one idea each, and numbers written the way they are said ("five times", "a hundred million"). A product name the voice might mispronounce gets tested first.
- **Direction goes in the line** as an audio tag, where the delivery should change: `"[whispers] Keep this between us."`, `[laughs]`, `[sighs]`. Tags need `eleven_v4` or `eleven_v3`, which act them out rather than say them. They are billed as characters but are never words, so `wordAt` and `verify.py --script` skip them.
- **Claims:** the voice says only what BRAND.md "Claims" allows, and never more than the screen shows at that moment.
- **Copy review:** run the product's copy rules over the script. If the `human-copy-review` skill is installed, run it on the script and on every on-screen word before generating.
- **Picture first:** mark each line with the moment it has to land on (for example "'reconciled' lands as the row turns green"). These marks become `wordAt` cues.

## 2. Pick the voice

```bash
python3 $SKILL/scripts/eleven.py voices
```

The interview asks for it (interview.md). Write the choice to `film.json` `voice.voice_id` (plus `model_id`, default `eleven_v4`) and to BRAND.md.

- **A professional clone needs its v4 fine-tune** (My Voices, the plus next to Eleven v4), and `voices` marks one without it. v4 still generates with such a voice and gives no error, so fine-tune it first or give that voice `eleven_multilingual_v2`.
- **v4 has only `stability` and `similarity_boost`:** no style or speed setting, and no SSML. It accepts `style` and `speed` without an error, so don't count on them. Tags direct the delivery instead.
- **Try one line before you switch a voice's model.** A cloned narrator read two lines 27% slower on v4 than on `eleven_multilingual_v2` (3.76 s against 2.93 s, and 6.96 s against 5.48 s), and v4 has no speed setting to win that back. A film cut tight to its voice keeps the model it was timed on; a line's own `model_id` lets you hear both.

## 3. Generate with word timings

```bash
python3 $SKILL/scripts/eleven.py tts            # all changed lines
python3 $SKILL/scripts/eleven.py tts --only v3 --force   # redo one take
```

- This writes `audio/vo/<id>.mp3` and `audio/vo/<id>.json` with every word's start and end. Unchanged lines are cached, so re-running costs nothing.
- Neighbouring lines are sent as context, so the intonation carries across clips.
- Listen to every clip, then fix each problem the cheapest way:
  - **A word said wrong:** fix it once for every line in `voice.pronounce` instead of respelling the script: `[{"word": "live", "ipa": "laɪv"}, {"word": "SQL", "alias": "sequel"}]`. `tts` makes the dictionary once and retakes only the lines with that word. An `ipa` rule works on `eleven_v4`, `eleven_v4_turbo`, `eleven_v3` and `eleven_flash_v2`. `eleven_multilingual_v2` drops the word from the audio instead, so `tts` leaves the rule out there and says so. An `alias` works on v4 and on `eleven_multilingual_v2`, and `wordAt` still finds the script's spelling.
  - **A stumble or a flat read:** retake it (`--only v2 --force`), or add a tag.
  - **A read no retake gets right:** record the line's exact words the way you want them (alignment times the script's words even where a take says another) and run `eleven.py sts v2 takes/v2.m4a`. It comes back in the line's voice with your timing. To keep your own voice, run `eleven.py align v2 takes/v2.m4a`. Both time the words the way `tts` does and mark the take with a `source`. `tts` keeps that take unless `--force`, and says so when the line's text has changed since.
- More than one speaker: a line's own `voice_id` (and `settings`) overrides `voice.voice_id`. Neighbouring-line context is only passed between lines of the same speaker, so each voice keeps its own intonation.
- A word the final mix buries (`verify.py --script` lists it): lift that line with `gain_db` (2 to 4 dB) before ducking the music harder, and re-check.
- Treated voices: a line's `filter` is an ffmpeg audio filter chain `mix.py` applies to that clip, e.g. a PA or phone voice: `"filter": "highpass=f=400,lowpass=f=3200,aecho=0.8:0.6:40:0.25"`.
- Voice feel: `film.json` `voice.settings` (`stability`, `similarity_boost`) and `voice.seed` pass straight through.

## 4. Place the lines and key the picture to words

- Set each line's `at` so its mark lands on its moment, with a breath between lines (a few tenths of a second is a starting point) and the first line after the opening has moved.
- In `render`, a moment that belongs to a word reads `wordAt(film, 'v2', 'reconciled')`. `wordAt` fails if the word disappears from the script, so an edit cannot silently break sync.
- The picture leads the word slightly: a visual that illustrates a word lands 0.1 to 0.2 s before or on the word, never after it.
- Words on screen never compete with the voice. Either punchlines repeat the key phrase at the moment it is said, or the screen carries UI only. There are no captions saying something different from the voice.
- Captions for muted autoplay are a separate deliverable: the voice words with their timings are already in `audio/vo/*.json`.

## 5. With music

- Compose or cut the music after the voice is placed, to the film's real duration (music.md).
- `mix.py` ducks the music under every line (its defaults are in the script). Put the music's big moments in gaps between lines, not under a key word, and keep sound effects under the voice quiet.
