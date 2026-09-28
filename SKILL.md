---
name: product-film
description: Makes showreel-grade motion films in code for a product or brand, built on its own design system, components and voice, with one or several voices, music and sound design (ElevenLabs optional), GSAP and Lottie motion, generated footage and 3D renders, and partners in their official identity (Brandfetch). Covers launch films, teasers and announcements, feature demos and walkthroughs, explainers, social cuts (1:1, 9:16, 4:5), muted landing-page loops, partner co-launches, event openers and data or metrics stories. Use when someone asks for a product video, promo, launch or teaser video, explainer, demo reel, social video, landing loop or any motion design video for their app, SaaS, codebase or brand. It interviews for the brief, sound and engine (HTML render(t) by default, Remotion as an opt-in), then runs discovery, story and energy planning, voice-led timing, music sync, measured review loops and a verified final render.
license: MIT
compatibility: Needs Node 20+ with pnpm, Python 3 with uv, ffmpeg, and Google Chrome or Chromium. Optional: ElevenLabs (ELEVENLABS_API_KEY) for voice, music and sound effects; Gemini (GEMINI_API_KEY) for a reviewer that watches and hears the film; fal.ai (FAL_KEY) for generated footage; Blender for 3D renders.
---

# Product film

A film that looks like the product made it: its colors, type, components, logo and voice, cut to a voiceover, music and sound design, with the energy of a real launch film.

**Paths.** `$SKILL` is this skill's folder (`${CLAUDE_SKILL_DIR}` in Claude Code). Films live outside any repo, by default in `~/Films/<product>/<film>/`, with one `~/Films/<product>/BRAND.md` shared by all of a product's films. Use another folder if the user prefers one.

## Principles

- **Their design wins on their product.** The product's UI, colors, type and copy come from its code and rules, because the film is judged against the real product. Around it the film is free: an idea can bring its own world (a format, a setting, props, a borrowed type), and a partner the film features appears in its own official identity next to the product's.
- **Energy that fits the type.** A film that is correct but flat has failed: even a calm walkthrough has one clear peak and no stillness it doesn't want. Measure and watch before handing off ([reference/review.md](reference/review.md)), and say plainly what you would still call flat.
- **The user decides what goes in.** What the film shows, how it sounds and which engine builds it are their call ([reference/interview.md](reference/interview.md)). Offer options drawn from their code and brand; generic options produce generic films.
- **Every frame is a pure function of time.** No CSS transitions or keyframes, no timers, no `Date.now()` or `Math.random()`, no state carried between frames, so any frame renders the same cold or in sequence and parallel renders agree. A component that runs its own clock gets a frame-driven twin.
- **Measure instead of guessing.** Word times come from the voice alignment, beats from the audio, positions and text boxes from the DOM, energy from the rendered draft, colors and loudness from the decoded final files.
- **Honest claims, as the user states them.** Show and say only what the product does. Find its claims rules and approved lines before writing. Take the user's claims, dates, partner permissions and legal clearance as given; they did that homework, so don't gate the film on sign-offs or proof. If a copy-review skill is installed, run the script and on-screen words through it.
- **Keep every version** (`out/v1`, `v2`, ...), so a note can always be compared against what came before.

## When to stop and ask, and when to keep going

Stop for the user at: the interview, the story checkpoint, anything that spends real money or time (a long music generation, many retakes), and anything outward or hard to undo (committing, pushing, uploading, publishing). Between those, keep going. Don't stop to ask about taste you can show in a still, about a fix a check already points to, or to hand back a draft you would call flat; fix it and show the result.

When the user asks for a run without stops ("no questions", "surprise me", "don't wait for me", a brief to run overnight), take your recommended option at every question and at the checkpoint, write each choice into `film-prompt.md` marked "(chosen for you)", keep the checkpoint's work (ideas, beat sheet, style frames, peak test) as the record, and run the review loop through to a verified render. Outward and hard-to-undo actions still stop. Spending stays within what the user named, or one pass of the film's voice, music and effects if they named nothing.

## Workflow

1. **Quick discovery.** Just enough to ask good questions: rules files, tokens, components, the logo (and any mascot), the landing page, the main features. Reuse BRAND.md if it exists. See [reference/discovery.md](reference/discovery.md).
2. **Interview.** The film type, the brief and the engine gate, then the sound (voice, music, sound design). Ingredients come later, with the ideas. See [reference/interview.md](reference/interview.md).
3. **Brand kit → `BRAND.md`.** Finish discovery on what they chose, and fill [templates/BRAND.md](templates/BRAND.md).
4. **Set up the film folder** for the chosen engine:
   - HTML (default): [reference/engine-html.md](reference/engine-html.md). Copy `templates/html/` and run `pnpm install`.
   - Remotion (gate passed): [reference/engine-remotion.md](reference/engine-remotion.md).
5. **Idea, then story → `film-prompt.md`.** Name one or two reference films and study any the user sent as a file, then pitch 2 or 3 ideas before any beat sheet. Read [reference/story.md](reference/story.md) (it has a shape per film type) and [reference/ingredients.md](reference/ingredients.md), then fill [templates/film-prompt.md](templates/film-prompt.md). With a voice, write the script first ([reference/voice.md](reference/voice.md)). Checkpoint with the user: the chosen idea, the beat sheet with its energy and camera plan, the script, style frames and a motion test of the peak with a sketch of its sound (the real voice and music come in step 6).
6. **Sound.** Voice: `scripts/eleven.py tts` (or a recorded read, timed with `align` or turned into the voice with `sts`), then place the lines in `film.json`. Music: composed, cut or synthesized; `scripts/beats.py` for the grid, `scripts/audio-edit.py` to cut it on bars onto the film's cues, and stems if the voice needs the drums kept. Sound design: `eleven.py sfx`, or synthesized in code without a key, with hits keyed to cues or words. Then `scripts/mix.py`. See [reference/voice.md](reference/voice.md) and [reference/music.md](reference/music.md).
7. **Scenes.** Build them keyed to words, cues and the grid, per the engine reference.
8. **Review loop.** Stills and the text check, then a draft measured with `scripts/energy.py` (its motion and loudness side by side) and looked at in contact sheets, two fresh reviewers on the first full draft (the critic looks at a silent pack; the watcher, `scripts/watch.py`, watches and hears the film), then fix and repeat, showing the user frames as you go. See [reference/review.md](reference/review.md).
9. **Final render, verify, deliver.** See [reference/render.md](reference/render.md): render with motion blur, look at the fastest moves in the encode, run `scripts/verify.py --script film.json`, then send the files and the verify output.

## Tools, and when each earns its place

Reach for these when the film calls for them, not by default; each one exists because a hand-coded version was weaker or slower.
- **GSAP** (`pnpm add gsap`; every plugin is free, including SplitText, DrawSVG, MotionPath and MorphSVG): choreography that would take pages of tweens. Letters arriving one by one, a line drawing itself, an object flying along a path, a shape morphing. Build one paused timeline on word times and seek it from `render(t)` with `gsapAt` ([reference/engine-html.md](reference/engine-html.md)).
- **Lottie** (`pnpm add lottie-web`): designed animation the product already owns, such as a logo sting, animated icons or a character from After Effects or LottieFiles. Drive it with `lottieClip`. Stock animation from a marketplace is usually a generic look; prefer the brand's own files.
- **Brandfetch** (`scripts/brandfetch.py <domain>`, free key): any partner the film features, in its official logos and colors, instead of hand-sourced files.
- **More than one voice** (`voice_id` per line in `film.json`): dialogue, a control room, an interview. A radio `filter` on a line puts it on air.
- **Directing the voice** (`eleven_v4`, [reference/voice.md](reference/voice.md)): an audio tag in the line changes the delivery, `voice.pronounce` fixes a word in every line, and `eleven.py sts` turns your own read of a line into its voice with your timing.
- **Generated footage and 3D renders** (`scripts/gen.py` on fal.ai, `FAL_KEY`; Blender): the idea's world or a physical object, played frame-exact as an image sequence with `footage()`. Generate between two of the film's own stills so the cuts don't show. Never the product's own screens, which a model would get wrong and make into a false claim.
- **Two fresh reviewers** ([reference/critic.md](reference/critic.md)): the critic (a subagent with a silent pack) and the watcher (`scripts/watch.py`, `GEMINI_API_KEY`), which watches and hears the film. On the first full draft and the final, for what only a first-time viewer notices. The watcher's silence is not a pass: it timed a pause a person heard as lag and called it clean.

## Quality floor (whatever the type and ingredients)

- **The product looks like itself.** Its screens use only its own surfaces, colors, borders and shades. An invented card background or tint is the fastest way to make a film look fake to the people who built the product.
- **Readable at the delivery size.** Fewer words beat smaller words. Cut labels that restate the picture.
- **Text stays whole and uncovered.** No cursor, chip or texture over it, and no camera crop: every hold fits the whole line being read, computed from the text's box with an edge margin and a zoom cap, and stays on the content so a low line doesn't pull empty space into the frame. Text doesn't cross other text in a move, and a line keeps every word's slot so it doesn't re-center while it builds.
- **Frame 0 is the cover.** Chat apps and feeds with autoplay off show the first frame, not the uploaded poster, so it reads as a still that sells the film at about 300 px: the subject whole and legible, nothing half-cropped or mid-move. The motion starts right after. Every render prints a `cover (frame 0)` line to check it.
- **Loading states keep their width.** Use the product's own loading pattern.
- **The first draft is the bold one.** Notes tone a film down; they rarely build it up.
- **Something happens on every beat or phrase** unless the type wants calm. `energy.py` finds the still stretches; keep only the ones you can name a reason for.
- **The picture meets the voice.** A moment tied to a word lands on it or just before. On-screen words say what the voice says.
- **Scene boundaries land on bars or words.** A loop's last frame equals its first. A landing loop reads muted.
- **Restraint belongs to the product's screens, not the film.** Keep effects the product never uses (glows, click rings, bouncy easing) off its UI unless the idea calls for them. Camera, pacing and sound can be as bold as the idea wants.

## Generic looks to avoid

"Make it not look generic" only swaps one default for another, so here are the specific defaults to leave out unless the product or the idea genuinely uses them:
- every scene opening with centered text fading and rising in
- slow Ken Burns drifts over static screenshots
- purple-to-blue gradient blobs, glowing particles, lens flares, a "futuristic" HUD
- a floating 3D device mockup spinning in empty space
- labels parked in the frame's corners, and decorative borders around the picture
- typewriter captions under every scene, or numbered "01 / 02 / 03" chapter cards
- stock whoosh-and-ding on every element, or royalty-free "corporate uplifting" music
- the same transition between every pair of scenes

## Traps that cost real time

- **Color range.** Browser screenshots and Remotion frames are RGB. An untagged or wrongly read YUV encode lifts `#0a0a0a` to `#171717`, a gray box on a dark page. Both engines encode BT.709 limited range and tag the matrix, primaries and transfer. `verify.py` checks all the tags, and `--bg` decodes a frame to prove the colors.
- **Generated music misses its marks** (where the drop lands, sung direction): music.md has the traps and the fix, cutting on bars onto the film's cues. `beats.py` measures with a beat-tracking model; its offline `--numpy` fallback read one 120 BPM track as 160 and put another's downbeat a beat late.
- **Generated sound effects can come back nearly silent** or peak in the wrong place. Measure each clip before you place it (music.md); `mix.py` warns about a silent one.
- **Four motion-blur subframes step on fast moves.** Whips, whole-frame shakes and spins show ghost copies; render them with `--blur 8` or `--blur 16` (render.md).
- **Voice drift.** Timing scenes by hand to a clip breaks the first time the line is regenerated. Key moments to `wordAt(...)`, which fails loudly when a cue word disappears, and sound effects to words the same way (`"hit": "v2:reconciled"`).
- **A professional voice without its v4 fine-tune still renders on `eleven_v4`, with no error.** `eleven.py voices` marks it: fine-tune it, or give that voice `eleven_multilingual_v2`.
- **Generated clips come back without color tags.** Read as BT.601, ffmpeg's guess, `#ffd400` became 248,223,9; `gen.py` decodes them as BT.709. A 4 s shot came back as 97 frames, so resume the coded scene at `start + clip.seconds`.
- **ElevenLabs keys can lack permissions.** A restricted key fails with 401 `missing the permission <name>` on those calls only (`voices_read`, text to speech, music, sound effects). Name the missing permission to the user rather than debugging the script.
- **The key may be set only for interactive shells.** An agent's tool shell is usually non-interactive and skips `~/.zshrc` or `~/.bashrc`. If a script says its key is not set, run it through an interactive shell (`zsh -ic '…'`) and suggest moving the export to `~/.zshenv` or `~/.profile`.
- **GSAP `from` and `fromTo` draw their start state at time 0.** A pop added for a later moment (a clock that bumps on each count) showed its scaled-up start in frame 0 and cropped the cover. Give such tweens `immediateRender: false`; keep the default only for entrances that should be hidden until they play.
- **Loose GSAP tweens run on GSAP's own clock.** Put every tween on the one paused timeline, and create anything a tween needs (SplitText, generated nodes) once at boot, never inside `render(t)`.
- **Lottie's time argument is milliseconds.** `lottieClip` seeks by frame to avoid it.
- `interpolateColors` (Remotion) and hand-written tweens cannot mix `color-mix()`. Any color that animates is a hex token (kit `mixHex`).
- Async images (Radix or base-ui avatars, lazy `<img>`) can render empty in a frame. HTML: `boot()` waits for `img.decode()`; keep images in the initial DOM. Remotion: use `<Img>`.
- Springs that retarget: sum one closed-form step per key, with keys sorted by time.
- CSS dashed borders crawl while a box resizes. Draw dashes as SVG strokes at a fixed pitch.
- WebGL or shader effects on their own clock paint a different picture each run. Prefer textures painted per frame.
- Remotion only: `npx remotion still` re-bundles every call (use `scripts/stills.ts`), stills do not forward console logs (use `kit/debug.tsx`), and its bundled ffmpeg lacks `tmix`, `select` and `tile`.
- Stop only the processes you started (preview servers included). Other sessions may be waiting on the machine.
