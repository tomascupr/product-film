# Interview: ask what goes in

The user decides what the film shows, how it sounds, and how it is built. Ask after a quick discovery pass, so every option is concrete and names their real features, screens, components, logo and partners. Use AskUserQuestion:
- at most 4 questions per call, with 2 to 4 options each ("Other" is added for them)
- `multiSelect` where several answers fit
- your recommendation first, marked "(Recommended)"

Write every answer into BRAND.md (product-wide) or `film-prompt.md` (this film), so later decisions trace back to it. If BRAND.md already answers a product-level question from an earlier film, offer that answer first, marked "(last time)". Still ask the voice question every time.

## Round 1: the brief and the engine

| Question | Options (adapt to what you found) |
|---|---|
| What kind of film? | The 3 or 4 types from story.md "Film types" that fit what you found (launch film, teaser, feature demo, explainer, social cut, landing loop, partner co-launch, event opener, data story) |
| Where will the film play? | Landing page, muted loop / Social, with sound / Launch or demo video, with sound / Event screen |
| How long? | 15 to 20 s / 20 to 30 s / 30 to 45 s / 45 to 60 s |
| What must it show? (multi) | The 3 or 4 strongest features, screens or moments you found, by their product names (for a teaser with no UI: the statement it makes) |
| How should it be built? **(the engine gate)** | HTML `render(t)` (Recommended): one file, no license, UI redrawn faithfully / Remotion: imports the product's real React components, needs a Remotion company license above a small team size |

- Ask the engine question only when the product's UI is React. Otherwise use HTML and say so in one line.
- Recommend Remotion only when reusing real components clearly beats redrawing them: many complex screens, a design system that changes often, or a team that will keep editing films. Name the license cost in the option.
- Add the format (16:9, 9:16, 1:1) if social is in play.

## Round 2: sound

| Question | Options |
|---|---|
| Voiceover? | ElevenLabs narrator (Recommended for launch, demo and explainer films) / Their own recorded voice / No voice, music and sound design only (Recommended for muted loops and short teasers) |
| More than one voice? (only if the idea has a room, a dialogue or a call and answer) | One narrator (Recommended) / A main voice plus answering voices, each its own `voice_id` |
| Which voice? (ask every time a voice is chosen) | The account's voices from `eleven.py voices`: cloned and professional first, the last used one first of all, marked "(last time)" |
| What music? | Composed with ElevenLabs to the film's acts (Recommended) / Your licensed track or stems / Silent |
| Sound design? | Designed with ElevenLabs: risers, impacts, whooshes on moves, a texture from the idea's world, UI sounds (Recommended) / UI sounds only / None |

- If `eleven.py voices` fails with `missing the permission voices_read`, don't stop: offer the voice recorded in BRAND.md (marked "(last time)") and ask for a voice ID pasted from the ElevenLabs Voices page. Mention that enabling `voices_read` on the key brings the list back.
- If `ELEVENLABS_API_KEY` is not set, say so before asking. The voice and composed music options need it, so offer the other options or pause until the key is set.
- If the voice is chosen after the music question, list the voices in a follow-up call.

## Round 3: the ingredients

| Question | Options (offer only what the product can support) |
|---|---|
| What carries the brand on screen? (multi) | Logo animation (it draws or reveals itself) / Their mascot or character (only if they have one) / Wordmark and tagline / Product UI only |
| How do words appear? | Big punchlines between scenes, word by word / Short captions over the scenes / No words, the UI (and voice) speaks |
| How do scenes connect? | Magic moves (one element travels into the next scene) / One big canvas with camera moves / Clean cuts on the beat |
| What else should it include? (multi) | Cursor interactions (clicks, typing) / Partner or integration logos (from Brandfetch) / Proof moments (results, metrics, quotes) / Their brand texture or pattern (only if they have one) / Their own Lottie animation (logo sting, icons, character) / Generated footage for the idea's world (needs a video-generation key) |

With a voiceover, recommend punchlines that echo the voice's key phrase, or no words at all. Captions that say something different from the voice compete with it.

## Round 4 (only if needed)

- The ending: the tagline, a call to action, a URL, the logo lockup.
- Claims: what the film cannot promise. Take the user's answer as settled; don't ask for proof or approvals.
- Which real components or screens to feature (list what you found).
- Dark or light, if the product has both.

## Don't ask

- Anything the code already answers: colors, fonts, radius, spacing.
- Taste you can show instead. Make 3 style frames and let them react. People answer pictures faster than questions.
- The film's idea. Pitch ideas (story.md) rather than asking for one.
