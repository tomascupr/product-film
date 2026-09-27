# Discovery: learn the product before drawing a frame

The film is judged against the product's own look, so collect it first and write it down: `~/Films/<product>/BRAND.md` (template: `templates/BRAND.md`), shared by every film of the product. If it exists, read it and refresh only what changed.

## What to find

Read-only sweeps, in parallel where you can (one topic each, returning paths, values and quotes rather than opinions):
1. **Rules and voice:** hard copy rules (casing, dashes, banned words), design rules, claims and approved lines, each with its source.
2. **Tokens:** colors in dark and light, radius, fonts and where they load from, and the easing curves and springs the UI already uses. The film's motion should feel like the product's.
3. **Components and signatures:** the pieces the film may show (buttons, status glyphs, loaders, cards), the logo as SVG, any animation the brand owns (Lottie or After Effects files: ask for them), and the landing page's signature elements. For each, whether it runs its own clock (motion libraries, `requestAnimationFrame`, timers, CSS keyframes, shaders, async images), since those need frame-driven twins.
4. **Features on screen:** the real screens, their copy, the states they move through, and the demo data the landing already uses.
5. **Partners the film features:** `scripts/brandfetch.py <domain>` fetches official logos, colors and fonts (free key in `BRANDFETCH_API_KEY`; 100 fetches on the free plan, cached per domain).
6. **Old video work:** what was kept or dropped, and the licenses of any music and sound.

## Tour the live site

Open the landing page at desktop width and scroll every section. Screenshots do not persist between turns, so write what you see into BRAND.md as you go: layout, colors, type, how CTAs press, animated demos, how the logo moves, how partner logos appear.

## For the HTML engine: capture what you will redraw

- For each component the film shows, save its rendered HTML and computed styles; redraws start from these numbers, not from a screenshot.
- Copy the fonts and logo SVGs into the film folder. At render time nothing loads from the network.

## The logo and any character

- A mascot or character can appear only if the product has one and the user picks it. If it has animation code, drive its pure functions from `t`; otherwise animate its SVG transforms from `t`.
- If anything animates, render a pose sheet still before scene work.

## Feed the interview, then write BRAND.md

Stop once you can name the real options (features, screens, components worth showing, the logo, partners, any texture), run the interview, then finish discovery on what the user chose and fill `templates/BRAND.md`: every rule with its source, a "Components" table (import, frame-driven twin or redraw, and why), and a "Claims" section. Where the product says nothing, choose sensibly and mark the choice as yours so the product owner can overrule it.
