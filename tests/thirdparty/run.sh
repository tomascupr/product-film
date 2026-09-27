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
