# Interview: ask what goes in

The user decides what the film shows, how it sounds, and how it is built. Ask after a quick discovery pass, so every option is concrete and names their real features, screens, components, logo and partners. Put your recommendation first, and when BRAND.md already answers a question from an earlier film, offer that answer marked "(last time)". Write every answer into BRAND.md (product-wide) or `film-prompt.md` (this film), so later decisions trace back to it.

## Round 1: the brief and the engine

| Question | Options (adapt to what you found) |
|---|---|
| What kind of film? | The 3 or 4 types from story.md "Film types" that fit what you found |
| Where will the film play? | Landing page, muted loop / Social, with sound / Launch or demo video, with sound / Event screen |
| How long? | Ranges that suit the type and the placement |
| What must it show? (multi) | The 3 or 4 strongest features, screens or moments you found, by their product names (for a teaser with no UI: the statement it makes) |
| How should it be built? **(the engine gate)** | HTML `render(t)` (Recommended): one file, no license, UI redrawn faithfully / Remotion: imports the product's real React components, needs a Remotion company license above a small team size |

- Ask the engine question only when the product's UI is React. Otherwise use HTML and say so in one line. Recommend Remotion only when reusing real components clearly beats redrawing them (many complex screens, a design system that changes often, a team that will keep editing films), and name the license cost.
- Add the formats (16:9, 9:16, 1:1, 4:5) if social is in play. Several can come from one film, each reframed (engine-html.md "Several formats").
- Ask for a film whose feel they want, as a file you can open (a video, a frame, a folder of stills). None is a fine answer: you will name one (story.md).

## Round 2: sound

Ask about the voice every time, even when BRAND.md has one: a film's voice is a choice, not a setting.

| Question | Options |
|---|---|
| Voiceover? | ElevenLabs narrator / Their own recorded voice / No voice, music and sound design only (often right for muted loops and short teasers) |
| Which voice, and how many? | The account's voices from `eleven.py voices`, cloned and professional first, the last used one marked "(last time)". More than one only if the idea has a room, a dialogue or a call and answer. |
| What music? | Composed with ElevenLabs to the film's acts / Their licensed track or stems / Synthesized in code / Silent |
| Sound design? | Designed with ElevenLabs (music.md) / Synthesized in code / UI sounds only / None |

- If `eleven.py voices` fails with `missing the permission voices_read`, offer the voice recorded in BRAND.md and ask for a voice ID pasted from the ElevenLabs Voices page; enabling `voices_read` on the key brings the list back.
- If `ELEVENLABS_API_KEY` is not set, say so before asking, since the voice and composed music need it; music and sound design can still be synthesized in code (music.md).

## Ingredients come with the idea

How words appear, how scenes connect, what carries the brand (logo animation, a mascot, the UI alone), and extras such as cursors, partner logos, proof moments, the brand's own Lottie files or generated footage: each pitched idea proposes its own set (story.md), so the user picks an idea and its ingredients together. Asking for them before an idea exists fixes the film's shape too early.

## Only if needed

- The ending: the tagline, a call to action, a URL, the logo lockup.
- Claims: what the film cannot promise. Take the user's answer as settled.
- Which real components or screens to feature.
- Dark or light, if the product has both.

## Don't ask

- Anything the code already answers: colors, fonts, radius, spacing.
- Taste you can show instead: style frames get faster answers than questions.
- The film's idea: pitch ideas rather than asking for one.
