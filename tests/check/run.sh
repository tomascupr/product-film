#!/bin/sh
# film.mjs check and stills on a page with known faults: the text findings, a frame that is not a pure
# function of t (--cold), the film's own moments (--cues), sheets of 16, and a film error named by its time.
set -e
cd "$(dirname "$0")"
cp ../../templates/html/film.mjs .
pnpm install --silent
rm -rf out && mkdir out
ok() { echo "ok: $1"; }
fail() { echo "FAIL: $1"; exit 1; }
has() { grep -qF -- "$2" "$1" && ok "$3" || fail "$3"; }
hasnt() { grep -qF -- "$2" "$1" && fail "$3" || ok "$3"; }

if node film.mjs check 0 > out/text.txt 2>&1; then fail "check exits non-zero on findings"; fi
has out/text.txt 'small (1): "tiny caption"' "small text is reported"
has out/text.txt 'covered (1): "Spreadsheets"' "covered text is reported"
has out/text.txt 'overlap (1): "Hello" and "World"' "overlapping text is reported"
hasnt out/text.txt 'Clean line' "a clean line is left alone"
hasnt out/text.txt 'Hidden below' "text under another layer is left alone"

# From 1 s the note's place depends on the frame drawn before it; earlier frames are pure.
node film.mjs check 0.5 --cold > out/pure.txt 2>&1 || true
hasnt out/pure.txt 'cold (1)' "--cold passes a frame that is a pure function of t"
node film.mjs check 1.2 --cold > out/impure.txt 2>&1 || true
has out/impure.txt 'cold (1)' "--cold reports a frame that depends on the one before it"
[ -f out/check/1.20-cold.png ] && [ -f out/check/1.20-warm.png ] && ok "and saves both pictures" || fail "cold and warm pictures"

# --cues: frame 0, the cue, and the middle and last word of the voice line. A switch does not swallow the time after it.
node film.mjs stills out/cues --cues 1.9 > out/cues.txt
for line in 't=1.9' 't=0  frame 0, the cover' 't=0.5  v1 halfway' 't=0.65  v1 said: Hello there' 't=1.2  cue hit'; do
  has out/cues.txt "$line" "--cues: $line"
done
[ "$(grep -c '\.png  t=' out/cues.txt)" = 5 ] && ok "--cues adds no other time" || fail "--cues times"

# More than 16 stills go onto sheets of 16.
node film.mjs stills out/many 0 .1 .2 .3 .4 .5 .6 .7 .8 .9 1 1.1 1.2 1.3 1.4 1.5 1.6 > /dev/null
[ -f out/many/sheet-1.png ] && [ -f out/many/sheet-2.png ] && [ ! -f out/many/sheet-3.png ] && ok "17 stills make two sheets" || fail "sheets of 16"

# An error thrown by render(t) stops the run, names its time on the last line, and is not rendered again.
if node film.mjs render boom --from 8.9 --to 9.1 > out/boom.txt 2>&1; then fail "a film error fails the render"; fi
tail -1 out/boom.txt | grep -q '^FAILED: page error: render(9.*no such scene' && ok "the last line names the film's error and its time" || fail "FAILED line"
hasnt out/boom.txt 'once more' "a film error is not retried"
