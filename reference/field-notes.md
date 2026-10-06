# Field notes: measurements that age

Prices, timings and thresholds measured on real films, each under its date. They explain choices made in the other references and in the scripts. Measure again before you rely on a number, and add a dated line when you do.

## Generated footage (fal.ai, September 2026)

- Prices with audio off, which `gen.py` sets: Kling v3 standard, the default, $0.084/s for 3 to 15 s; Kling v3 pro $0.112/s; Veo 3.1 fast first-last-frame $0.10/s and Veo 3.1 $0.20/s, for 4, 6 or 8 s. `--arg resolution=1080p` costs the same as 720p on Veo.
- A 4 s Kling v3 standard shot between two 1280x720 stills took 60 s. On another day 8 s shots took about 7 minutes each.
- That 4 s shot's first and last frames differed from the stills by 1.4 of 255 on average (PSNR 41 dB), and the ball it moved landed within 1 px, so neither cut showed. It came back as 97 frames (4.042 s), not 96.

## Seedance 2.5 and Gemini stills (October 2026, list prices, not yet measured on a film)

- Seedance 2.5 image to video on fal is billed by frame area: about $0.47/s at 720p and $0.22/s at 480p for 16:9, the same with or without audio. Takes run 4 to 30 s; resolution stops at 720p.
- Gemini stills per image: Nano Banana 2.1 (`gemini-nano-banana-2.1`, gen.py's default) $0.034 at 1K, $0.050 at 2K, $0.076 at 4K; Nano Banana Pro (`gemini-3-pro-image`) $0.134 at 1K or 2K, $0.24 at 4K. Google's own preference test ranks 2.1 above Pro; early side-by-sides found Pro's photographs more natural, so try both on a still that has to pass as a photograph.

## Blender (5.2 on Apple Silicon, September 2026)

- On an M4 Max the torus in `templates/3d/shot.py` took 1.6 s a frame, after about 2 minutes on the very first render while Metal compiled its kernels.
- With a fixed seed and motion driven by the frame number, two runs of Cycles on Metal still differed by at most 1 level, in 0.01% of pixels.

## Long blurred renders (HTML engine, September 2026)

- A 47.5 s film at 1080x1080 and 16 subframes is 45,600 screenshots. In one browser a screenshot timed out (`page.screenshot: Timeout 30000ms`) with four workers, and again after about 23 minutes with one.
- With `--segments`, in 10 s parts with four workers, the same film rendered in about 18 minutes with no part rendered twice, and matched a render joined from parts cut elsewhere at 51.7 dB PSNR.

## `check --cold` (HTML engine, September 2026)

- On that film, with camera zooms over text, 96 comparisons of a frame drawn cold against the same frame drawn after others found at worst 0.03% of the pixels more than 4 levels apart and none more than 24. Its two marks (0.5% past 4 levels, 0.02% past 24) sit above that.
- Two bugs the film had once, put back on purpose, moved 0.05% to 7.6% of the frame by more than 24 levels: a height read from an element the frame before had hidden, and an overlay that one scene revealed and only that scene hid.
