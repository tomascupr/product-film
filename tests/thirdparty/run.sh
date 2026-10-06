#!/bin/sh
# Lottie and GSAP stay a pure function of t: a frame drawn cold must equal the same frame drawn after others.
set -e
cd "$(dirname "$0")"
cp ../../templates/html/kit.js ../../templates/html/film.mjs .
pnpm install --silent
node film.mjs stills out/cold 1.3 > /dev/null
node film.mjs stills out/seq 0.4 1.9 0.9 1.3 > /dev/null
a=$(shasum out/cold/000.png | cut -d' ' -f1); b=$(shasum out/seq/003.png | cut -d' ' -f1)
[ "$a" = "$b" ] && echo "ok: t=1.3 cold equals t=1.3 after other frames" || { echo "FAIL: frames differ"; exit 1; }
# --size draws the same film at another size: boot() sizes the stage from it.
node film.mjs measure 0 --size 300x600 | tr -d ' \n' | grep -q '"w":300,"h":600' && echo "ok: --size 300x600 sizes the stage" || { echo "FAIL: --size"; exit 1; }

# render --segments: parts rendered in browsers of their own join into the film one browser renders, with the mix.
mkdir -p audio && ffmpeg -v error -y -f lavfi -i sine=frequency=440:duration=2 -ar 48000 -ac 2 audio/mix.wav
frames() { ffmpeg -v info -i "$1" -map 0:v -c copy -f null - 2>&1 | grep -o 'frame= *[0-9]*' | tail -1 | tr -dc 0-9; }
node film.mjs render one --blur 2 > /dev/null
node film.mjs render seg --blur 2 --segments 0.5 > /dev/null
[ "$(frames out/one/one.mp4)" = 120 ] && [ "$(frames out/seg/seg.mp4)" = 120 ] && echo "ok: four parts join into all 120 frames" || { echo "FAIL: frame count"; exit 1; }
psnr=$(ffmpeg -v info -i out/one/one.mp4 -i out/seg/seg.mp4 -lavfi psnr -f null - 2>&1 | sed -n 's/.*average:\([^ ]*\).*/\1/p')
{ [ "$psnr" = inf ] || awk "BEGIN { exit !($psnr > 45) }"; } && echo "ok: the joined film matches the single render ($psnr dB)" || { echo "FAIL: parts differ from the single render ($psnr dB)"; exit 1; }
ffmpeg -i out/seg/seg.mp4 2>&1 | grep -q 'Audio: aac' && ! ffmpeg -i out/seg/seg-muted.mp4 2>&1 | grep -q 'Audio:' && echo "ok: the mix is muxed once, and the muted copy has none" || { echo "FAIL: audio"; exit 1; }
# A part whose encode dies is rendered once more in a fresh browser.
printf '#!/bin/sh\nn=$(cat out/calls 2>/dev/null || echo 0); echo $((n + 1)) > out/calls\n[ "$n" = 1 ] && exit 1\nexec ffmpeg "$@"\n' > out/flaky-ffmpeg
chmod +x out/flaky-ffmpeg; rm -f out/calls
FFMPEG=out/flaky-ffmpeg node film.mjs render again --segments 1 > out/again.log 2>&1
grep -q 'once more in a fresh browser' out/again.log && [ "$(frames out/again/again.mp4)" = 120 ] && echo "ok: a failed part is rendered again" || { echo "FAIL: retry"; exit 1; }
# A render that fails says so on its last line and leaves the render before it alone.
before=$(shasum out/seg/seg.mp4)
if FFMPEG=false node film.mjs render seg --segments 1 > out/fail.log 2>&1; then echo "FAIL: a render without ffmpeg passed"; exit 1; fi
tail -1 out/fail.log | grep -q '^FAILED: ' && [ "$before" = "$(shasum out/seg/seg.mp4)" ] && [ ! -e out/seg/.parts ] && echo "ok: a failed render ends on FAILED and keeps the last good file" || { echo "FAIL: failed render"; exit 1; }
