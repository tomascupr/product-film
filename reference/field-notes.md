# Field notes: measurements that age

Prices, timings and thresholds measured on real films, each under its date. They explain choices made in the other references and in the scripts. Measure again before you rely on a number, and add a dated line when you do.

## Generated footage (fal.ai, September 2026)

- Prices with audio off, which `gen.py` sets: Kling v3 standard, the default, $0.084/s for 3 to 15 s; Kling v3 pro $0.112/s; Veo 3.1 fast first-last-frame $0.10/s and Veo 3.1 $0.20/s, for 4, 6 or 8 s. `--arg resolution=1080p` costs the same as 720p on Veo.
- A 4 s Kling v3 standard shot between two 1280x720 stills took 60 s. On another day 8 s shots took about 7 minutes each.
- That 4 s shot's first and last frames differed from the stills by 1.4 of 255 on average (PSNR 41 dB), and the ball it moved landed within 1 px, so neither cut showed. It came back as 97 frames (4.042 s), not 96.

## Seedance 2.5 and Gemini stills (October 2026)

- Seedance 2.5 image to video on fal is billed by frame area: about $0.47/s at 720p and $0.22/s at 480p for 16:9, the same with or without audio. Takes run 4 to 30 s; resolution stops at 720p.
- Gemini stills per image: Nano Banana 2.1 (`gemini-nano-banana-2.1`, gen.py's default) $0.034 at 1K, $0.050 at 2K, $0.076 at 4K; Nano Banana Pro (`gemini-3-pro-image`) $0.134 at 1K or 2K, $0.24 at 4K. Google's own preference test ranks 2.1 above Pro; early side-by-sides found Pro's photographs more natural, so try both on a still that has to pass as a photograph.
- Measured on one edit (a 1920x1080 office frame; phone down, eyes to camera, caption and banknotes removed): both models made it as asked in 19 to 23 s at 2K (2752x1536), and both came back as JPEG though PNG was asked for. The background the prompt said to keep was redrawn, 16 to 17 dB from the original, not pixel-aligned.

## Blender (5.2 on Apple Silicon, September 2026)

- On an M4 Max the torus in `templates/3d/shot.py` took 1.6 s a frame, after about 2 minutes on the very first render while Metal compiled its kernels.
- With a fixed seed and motion driven by the frame number, two runs of Cycles on Metal still differed by at most 1 level, in 0.01% of pixels.

## Long blurred renders (HTML engine, September 2026)

- A 47.5 s film at 1080x1080 and 16 subframes is 45,600 screenshots. In one browser a screenshot timed out (`page.screenshot: Timeout 30000ms`) with four workers, and again after about 23 minutes with one.
- With `--segments`, in 10 s parts with four workers, the same film rendered in about 18 minutes with no part rendered twice, and matched a render joined from parts cut elsewhere at 51.7 dB PSNR.

## `check --cold` (HTML engine, September 2026)

- On that film, with camera zooms over text, 96 comparisons of a frame drawn cold against the same frame drawn after others found at worst 0.03% of the pixels more than 4 levels apart and none more than 24. Its two marks (0.5% past 4 levels, 0.02% past 24) sit above that.
- Two bugs the film had once, put back on purpose, moved 0.05% to 7.6% of the frame by more than 24 levels: a height read from an element the frame before had hidden, and an overlay that one scene revealed and only that scene hid.

## Frame capture (HTML engine, October 2026, 16-core M4 Max; tried, not adopted)

- On a 59.6 s film at 1920x1080 and 60 fps, drawing a frame took 2 to 3 ms and Playwright's PNG screenshot 112 ms, so the screenshot sets a render's pace. The plain draft took 246 s; four pages in one browser captured 11 frames/s.
- Chrome's `Page.captureScreenshot` with `optimizeForSpeed`, sent on a CDP session of film.mjs's own with a browser per worker, captured 81 frames/s: the draft in 36 to 44 s, 2 s with 16 subframes in 19 to 27 s against 235 s, the whole blurred film in 408 s against about two hours. Frames drawn cold matched Playwright's exactly.
- It was not adopted. In a third of test renders, a browser among several captured a whole part at its window's 16:10 shape: without a clip the frame came back the wrong size and ffmpeg dropped frames silently on the size change; with a clip the content was wrong (29 dB). Setting the viewport again on that session fixed it but changed how text was rasterized (33 dB from Playwright's frames), so a final no longer matched its stills. Playwright's own screenshot in separate browsers was clean every time but no faster. A next try: send the fast capture through the session Playwright emulates the viewport on.
- Two renders of a film with canvas blur and scaled text can differ by up to 40 dB in some frames while frames drawn cold match. Compare renders by PSNR, not by checksum.
