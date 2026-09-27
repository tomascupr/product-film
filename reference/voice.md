# Voice: script, generate, time the film to the words

Only if the interview chose a voiceover. Once there is a voice, it leads the timing: scenes land on words, the music sits under it, and the beat grid only places accents.

## 1. Write the script

- **Budget:** about 2.3 words per second of speech. A 30 s film carries 50 to 60 words, with room for an opening and an end card with no voice.
- **One line per scene or idea.** Each line becomes one clip (`film.json` `voice.lines[]`: `{id, text, at}`), so it can be retimed or regenerated alone.
- **Written for the ear.** Short sentences, one idea each, and numbers written the way they are said ("five times", "a hundred million"). A product name the voice might mispronounce gets tested first.
- **Claims:** the voice says only what BRAND.md "Claims" allows, and never more than the screen shows at that moment.
- **Copy review:** run the product's copy rules over the script. If the `human-copy-review` skill is installed, run it on the script and on every on-screen word before generating.
- **Picture first:** mark each line with the moment it has to land on (for example "'reconciled' lands as the row turns green"). These marks become `wordAt` cues.

## 2. Pick the voice (always ask)

```bash
python3 $SKILL/scripts/eleven.py voices
```

Ask in the interview every time, with AskUserQuestion. Put cloned and professional voices first, and offer BRAND.md's last-used voice as the first option, marked as last used. Write the choice to `film.json` `voice.voice_id` (plus `model_id`, default `eleven_multilingual_v2`) and to BRAND.md.

## 3. Generate with word timings

```bash
python3 $SKILL/scripts/eleven.py tts            # all changed lines
python3 $SKILL/scripts/eleven.py tts --only v3 --force   # redo one take
```

- This writes `audio/vo/<id>.mp3` and `audio/vo/<id>.json` with every word's start and end. Unchanged lines are cached, so re-running costs nothing.
- Neighbouring lines are sent as context, so the intonation carries across clips.
- Listen to every clip. Retake a clip for a stumble, a wrong stress or a mispronounced name. Changing the text to fix pronunciation is fine ("S A P" or "sap", whichever the product says).
- Treated voices: a line's `filter` is an ffmpeg audio filter chain `mix.py` applies to that clip, e.g. a PA or phone voice: `"filter": "highpass=f=400,lowpass=f=3200,aecho=0.8:0.6:40:0.25"`.
- Voice feel: `film.json` `voice.settings` (`stability`, `similarity_boost`, `style`) and `voice.seed` pass straight through.

## 4. Place the lines and key the picture to words

- Set each line's `at` so its mark lands on its moment. Leave 0.3 to 0.6 s of air between lines, and start the first line after the opening has moved (about 1 s).
- In `render`, a moment that belongs to a word reads `wordAt(film, 'v2', 'reconciled')`. `wordAt` fails if the word disappears from the script, so an edit cannot silently break sync.
- The picture leads the word slightly: a visual that illustrates a word lands 0.1 to 0.2 s before or on the word, never after it.
- Words on screen never compete with the voice. Either punchlines repeat the key phrase at the moment it is said, or the screen carries UI only. There are no captions saying something different from the voice.
- Captions for muted autoplay are a separate deliverable: the voice words with their timings are already in `audio/vo/*.json`.

## 5. With music

- Compose or cut the music after the voice is placed, to the film's real duration (music.md).
- `mix.py` dips the music by `music.duck_db` (default -9 dB) under every line, with a 0.15 s attack and a 0.4 s release. Raise the music between lines only if it has room.
- Put the music's big moments (the drop, a hit) in gaps between lines, not under a key word.
- Sound effects under the voice stay at -14 dB or quieter.
