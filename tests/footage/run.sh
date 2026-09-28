#!/bin/sh
# footage() plays an image sequence frame-exact: a frame drawn cold equals the same frame drawn after
# others, and a film time between two source frames shows the earlier one.
set -e
cd "$(dirname "$0")"
cp ../../templates/html/kit.js ../../templates/html/film.mjs .
pnpm install --silent
# 1 s of testsrc at 24 fps as PNG, so a still of the 1:1 image can be compared with its source frame.
mkdir -p footage/test
ffmpeg -v error -y -f lavfi -i testsrc=size=320x180:rate=24:duration=1 footage/test/%04d.png
echo '{ "fps": 24, "frames": 24, "seconds": 1, "ext": "png" }' > footage/test/clip.json
rgb() { ffmpeg -v error -i "$1" -f rawvideo -pix_fmt rgb24 - | shasum | cut -d' ' -f1; }
same() { [ "$(rgb "$1")" = "$(rgb "$2")" ] && echo "ok: $3" || { echo "FAIL: $3"; exit 1; }; }
# The clip starts at 0.25 s (index.html). 1/3 s is film frame 20 at 60 fps, exactly source frame 2.
node film.mjs stills out/cold 0.35 > /dev/null
node film.mjs stills out/seq 0.9 0.1 1.4 0.3333333333333333 0.35 > /dev/null
same out/cold/000.png out/seq/004.png "t=0.35 cold equals t=0.35 after other frames"
same out/cold/000.png footage/test/0003.png "t=0.35, between source frames 2 and 3, shows frame 2"
same out/seq/003.png footage/test/0003.png "t=1/3, exactly on source frame 2, shows frame 2"
same out/seq/001.png footage/test/0001.png "before the start it holds the first frame"
same out/seq/002.png footage/test/0024.png "after the end it holds the last frame"
# gen.py frames: an untagged BT.709 limited-range clip, as generators often send them, comes back as
# the RGB it was made from (within 2). Read as BT.601, ffmpeg's guess, #ffd400 comes out 248,223,9.
ffmpeg -v error -y -f lavfi -i "color=c=0x0a0a0a:s=64x36,format=rgb24[a];color=c=0xffd400:s=64x36,format=rgb24[b];[a][b]hstack" -frames:v 1 footage/color.png
ffmpeg -v error -y -loop 1 -r 24 -i footage/color.png -t 0.25 -vf scale=out_color_matrix=bt709:out_range=tv,format=yuv420p,setparams=colorspace=unknown -c:v libx264 -crf 1 footage/color.mp4
python3 ../../scripts/gen.py frames footage/color.mp4 --out footage/color > /dev/null
near() { ffmpeg -v error -i footage/color/0001.jpg -vf "crop=1:1:$1:18" -f rawvideo -pix_fmt rgb24 - | od -An -tu1 |
  awk -v want="$2" 'NF { split(want, w); for (i = 1; i <= 3; i++) if ($i - w[i] > 2 || w[i] - $i > 2) exit 1 }' && echo "ok: $3" || { echo "FAIL: $3"; exit 1; }; }
near 10 "10 10 10" "gen.py frames keeps #0a0a0a"
near 100 "255 212 0" "gen.py frames keeps #ffd400"
