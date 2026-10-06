---
name: product-film
description: Makes showreel-grade motion films in code for a product or brand, built on its own design system, components and voice, with one or several voices, music and sound design (ElevenLabs optional), GSAP and Lottie motion, generated footage and 3D renders, and partners in their official identity (Brandfetch). Covers launch films, teasers and announcements, feature demos and walkthroughs, explainers, social cuts (1:1, 9:16, 4:5), muted landing-page loops, partner co-launches, event openers and data or metrics stories. Use when someone asks for a product video, promo, launch or teaser video, explainer, demo reel, social video, landing loop or any motion design video for their app, SaaS, codebase or brand. It interviews for the brief, sound and engine (HTML render(t) by default, Remotion as an opt-in), then runs discovery, story and energy planning, voice-led timing, music sync, measured review loops and a verified final render.
license: MIT
compatibility: Needs Node 20+ with pnpm, Python 3 with uv, ffmpeg, and Google Chrome or Chromium. Optional: ElevenLabs (ELEVENLABS_API_KEY) for voice, music and sound effects; Gemini (GEMINI_API_KEY) for a reviewer that watches and hears the film and for generated stills; fal.ai (FAL_KEY) for generated footage; Blender for 3D renders.
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

Stop for the user at: the interview, the story checkpoint, the first full draft, anything that spends real money or time (a long music generation, many retakes), and anything outward or hard to undo (committing, pushing, uploading, publishing). Between those, keep going. Don't stop to ask about taste you can show in a still or about a fix a check already points to; fix it and show the result.

The first full draft is a stop because only the user can say what a first-time viewer fails to follow, and their notes can replace a whole scene. Send it once it plays end to end with its sound and has had one round of fixes, with the defects you still know of and what you would call flat. More rounds before they have seen it polish scenes they may cut. When you send it, say that note rounds which fix rather than rethink run well at medium effort (`/effort medium` in Claude Code), and that fast mode (`/fast`) answers sooner at a higher price, so the user can choose; the model's own turns take the largest share of a film's time.

When the user asks for a run without stops ("no questions", "surprise me", "don't wait for me", a brief to run overnight), take your recommended option at every question and at the checkpoint, write each choice into `film-prompt.md` marked "(chosen for you)", keep the checkpoint's work (ideas, beat sheet, style frames, peak test) as the record, and run the review loop through to a verified render without the draft stop. Outward and hard-to-undo actions still stop. Spending stays within what the user named, or one pass of the film's voice, music and effects if they named nothing.

## Workflow

1. **Quick discovery.** Just enough to ask good questions: rules files, tokens, components, the logo (and any mascot), the landing page, the main features. Reuse BRAND.md if it exists. See [reference/discovery.md](reference/discovery.md).
2. **Interview.** The film type, the brief and the engine gate, then the sound (voice, music, sound design). Ingredients come later, with the ideas. See [reference/interview.md](reference/interview.md).
3. **Brand kit → `BRAND.md`.** Finish discovery on what they chose, and fill [templates/BRAND.md](templates/BRAND.md).
4. **Set up the film folder** for the chosen engine:
   - HTML (default): [reference/engine-html.md](reference/engine-html.md). Copy `templates/html/` and run `pnpm install`.
   - Remotion (gate passed): [reference/engine-remotion.md](reference/engine-remotion.md).
5. **Idea, then story → `film-prompt.md`.** Name one or two reference films and study any the user sent as a file, then pitch 2 or 3 ideas before any beat sheet. Read [reference/story.md](reference/story.md) (it has a shape per film type) and [reference/ingredients.md](reference/ingredients.md), then fill [templates/film-prompt.md](templates/film-prompt.md). With a voice, write the script first ([reference/voice.md](reference/voice.md)). Checkpoint with the user: the chosen idea, the beat sheet with its energy and camera plan and what a viewer understands from each scene, the script, style frames and a motion test of the peak with a sketch of its sound (the real voice and music come in step 6).
6. **Sound.** Voice: `scripts/eleven.py tts` (or a recorded read, timed with `align` or turned into the voice with `sts`), then place the lines in `film.json`. Music: composed, cut or synthesized; `scripts/beats.py` for the grid, `scripts/audio-edit.py` to cut it on bars onto the film's cues, and stems if the voice needs the drums kept. Sound design: `eleven.py sfx`, or synthesized in code without a key, with hits keyed to cues or words. Then `scripts/mix.py`, and `scripts/verify.py audio/mix.wav --script film.json` to find a word the mix buries before a render is spent on it. See [reference/voice.md](reference/voice.md) and [reference/music.md](reference/music.md).
7. **Scenes.** Build them keyed to words, cues and the grid, per the engine reference.
8. **Review loop.** Stills and the text check at the film's own moments (`film.mjs check --cues --cold`), then a draft measured with `scripts/energy.py` (its motion and loudness side by side) and looked at in contact sheets, and two fresh reviewers on the first full draft (the critic looks at a silent pack; the watcher, `scripts/watch.py`, watches and hears the film). One round of fixes, then the draft goes to the user, and their notes set the next round. See [reference/review.md](reference/review.md).
9. **Final render, verify, deliver.** See [reference/render.md](reference/render.md): render with motion blur (`--segments` for a long film), look at the fastest moves in the encode, run `scripts/verify.py --script film.json`, then send the files and the verify output.

## Tools, and when each earns its place

Reach for these when the film calls for them, not by default; each one exists because a hand-coded version was weaker or slower.
- **GSAP** (`pnpm add gsap`; every plugin is free, including SplitText, DrawSVG, MotionPath and MorphSVG): choreography that would take pages of tweens. Letters arriving one by one, a line drawing itself, an object flying along a path, a shape morphing. Build one paused timeline on word times and seek it from `render(t)` with `gsapAt` ([reference/engine-html.md](reference/engine-html.md)).
- **Lottie** (`pnpm add lottie-web`): designed animation the product already owns, such as a logo sting, animated icons or a character from After Effects or LottieFiles. Drive it with `lottieClip`. Stock animation from a marketplace is usually a generic look; prefer the brand's own files.
- **Brandfetch** (`scripts/brandfetch.py <domain>`, free key): any partner the film features, in its official logos and colors, instead of hand-sourced files.
- **More than one voice** (`voice_id` per line in `film.json`): dialogue, a control room, an interview. A radio `filter` on a line puts it on air.
- **Directing the voice** (`eleven_v4`, [reference/voice.md](reference/voice.md)): an audio tag in the line changes the delivery, `voice.pronounce` fixes a word in every line, and `eleven.py sts` turns your own read of a line into its voice with your timing.
- **Generated footage, stills and 3D renders** (`scripts/gen.py`: clips on fal.ai with `FAL_KEY`, stills from Gemini with `GEMINI_API_KEY`; Blender): the idea's world, a physical object or a person, played frame-exact as an image sequence with `footage()`. A still that must look real (a face, money, a product on a desk) comes from `gen.py image`, because code draws it as an illustration. Generate between two of the film's own stills so the cuts don't show. Never the product's own screens, which a model would get wrong and make into a false claim.
- **Two fresh reviewers** ([reference/critic.md](reference/critic.md)): the critic (a subagent with a silent pack) and the watcher (`scripts/watch.py`, `GEMINI_API_KEY`), which watches and hears the film. On the first full draft and the final, for what only a first-time viewer notices. Each judges what it can see: the critic layout and legibility from stills, the watcher pacing and sync from the film. Their findings are places to look and their scores move between runs, so neither is a target. The watcher's silence is not a pass: it timed a pause a person heard as lag and called it clean.

## Quality floor (whatever the type and ingredients)

- **The product looks like itself.** Its screens use only its own surfaces, colors, borders and shades. An invented card background or tint is the fastest way to make a film look fake to the people who built the product.
- **Readable at the delivery size.** Fewer words beat smaller words. Cut labels that restate the picture.
- **Text stays whole and uncovered.** No cursor, chip or texture over it, and no camera crop: every hold fits the whole line being read, computed from the text's box with an edge margin and a zoom cap, and stays on the content so a low line doesn't pull empty space into the frame. Text doesn't cross other text in a move, and a line keeps every word's slot so it doesn't re-center while it builds.
- **Frame 0 is the cover.** Chat apps and feeds with autoplay off show the first frame, not the uploaded poster, so it reads as a still that sells the film at about 300 px: the subject whole and legible, nothing half-cropped or mid-move. The motion starts right after. Every render prints a `cover (frame 0)` line to check it.
- **Loading states keep their width.** Use the product's own loading pattern.
- **The first draft is the bold one.** Notes tone a film down; they rarely build it up.
- **Something happens on every beat or phrase** unless the type wants calm. `energy.py` finds the still stretches; keep only the ones you can name a reason for.
- **The picture meets the voice.** A moment tied to a word lands on it or just before. On-screen words say what the voice says.
- **Where it plays muted, it reads muted.** A feed starts a film with the sound off, so there the point of each spoken line is on screen while it is said: a punchline, a caption in the film's own type, or a screen that shows the same thing.
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

Most traps are caught where they happen: a script warns about it or handles it (a nearly silent effect, a clip without color tags, a key that is missing or lacks a permission, a frame that depends on render order), or the reference for that step names it. These have no check:
- CSS dashed borders crawl while a box resizes. Draw dashes as SVG strokes at a fixed pitch.
- Stop only the processes you started (preview servers included). Other sessions may be waiting on the machine.
