"""Check rendered deliverables by decoding them: duration, colors, loop seam, loudness.

    uv run --with numpy --with imageio-ffmpeg python3 verify.py out/<name> --duration 30 \
        [--bg 10,10,10] [--bg-at 0] [--loop] [--lufs -14] [--probe 9.4:944,800] [--probe 33.0:1000,860]
        [--script film.json] [--allow-gap 12.6]

For every .mp4 and .webm in the folder (point it at out/<name>, not out/):
- duration matches (to the frame)
- tagged BT.709 limited range: matrix, primaries and transfer (mp4)
- frame 0 (the cover in many players) has real contrast: a blank or faded-in first frame fails
- --bg: the center of the frame at --bg-at seconds (default 0) decodes to the background (within 2).
  Pick a time where the center is background (a film that opens on a close-up needs another time). #0a0a0a coming back
  as #171717 means the color range was read wrong: fix the encode, never the tokens.
- --loop: the last frame vs frame 0 is only encoder noise (a loop must not jump)
- files with audio: integrated loudness within 1 LU of --lufs
- each probe (seconds:x,y) prints its decoded color, to check an accent or a surface
- files with audio: no silence over 0.1 s inside the film (a dropout at a splice), except gaps that
  contain an --allow-gap time (a deliberate stop before a hit)
- --script film.json: transcribes the first file with audio (ElevenLabs speech to text, needs
  ELEVENLABS_API_KEY) and lists every script word the transcript lost: a word the music buried.
  Numbers are skipped, since "five point five" comes back as "5.5".
Exits non-zero when a check fails.
"""

import argparse
import glob
import json
import os
import re
import subprocess
import sys

import imageio_ffmpeg
import numpy as np

FF = imageio_ffmpeg.get_ffmpeg_exe()


def info(path):
    text = subprocess.run([FF, "-hide_banner", "-i", path], capture_output=True, text=True).stderr
    h, m, s = re.search(r"Duration: (\d+):(\d+):([\d.]+)", text).groups()
    video = re.search(r"Video: .*", text).group(0)
    width, height = map(int, re.search(r"(\d{2,5})x(\d{2,5})", video).groups())
    return int(h) * 3600 + int(m) * 60 + float(s), width, height, video, "Audio:" in text


def frame(path, index, width, height):
    raw = subprocess.run(
        [FF, "-v", "error", "-i", path, "-vf", f"select=eq(n\\,{index})", "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
        capture_output=True,
    ).stdout
    if len(raw) != width * height * 3:
        sys.exit(f"{path}: could not decode frame {index} (is --duration right?)")
    return np.frombuffer(raw, np.uint8).reshape(height, width, 3).astype(int)


def loudness(path):
    text = subprocess.run([FF, "-hide_banner", "-i", path, "-vn", "-af", "loudnorm=print_format=json", "-f", "null", "-"], capture_output=True, text=True).stderr
    return float(json.loads(re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", text).group(0))["input_i"])


def gaps(path, dur, floor_db=-50, longest=0.1):
    """Silent runs inside the film (20 ms windows under floor_db), skipping the first and last 0.3 s."""
    raw = subprocess.run([FF, "-v", "error", "-i", path, "-vn", "-ac", "1", "-ar", "8000", "-f", "s16le", "-"], capture_output=True).stdout
    a = np.frombuffer(raw, np.int16).astype(float) / 32768
    hop = 160
    quiet = [20 * np.log10(np.sqrt((a[i:i + hop] ** 2).mean()) + 1e-9) < floor_db for i in range(0, len(a) - hop, hop)]
    found, start = [], None
    for i, q in enumerate(quiet + [False]):
        t = i * hop / 8000
        if q and start is None:
            start = t
        elif not q and start is not None:
            if t - start > longest and start > 0.3 and t < dur - 0.3:
                found.append((start, t))
            start = None
    return found


NUMBERS = set("zero one two three four five six seven eight nine ten eleven twelve twenty thirty forty fifty hundred thousand million point percent".split())


def lost_words(path, film_json):
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import eleven  # noqa: E402  (stdlib only; same folder)
    words = lambda text: [w for w in re.findall(r"[a-z']+", text.lower().replace("’", "'")) if w not in NUMBERS]
    lines = json.load(open(film_json)).get("voice", {}).get("lines", [])
    heard = set(words(" ".join(w["text"] for w in eleven.listen(path, quiet=True))))
    return [w for w in words(" ".join(l["text"] for l in lines)) if w not in heard]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("folder")
    parser.add_argument("--duration", type=float, required=True)
    parser.add_argument("--fps", type=int, default=60)
    parser.add_argument("--bg", help="r,g,b expected at the center of frame 0")
    parser.add_argument("--loop", action="store_true")
    parser.add_argument("--lufs", type=float, default=-14.0)
    parser.add_argument("--probe", action="append", default=[])
    parser.add_argument("--bg-at", type=float, default=0.0)
    parser.add_argument("--script", help="film.json: check the voice survives the mix")
    parser.add_argument("--allow-gap", type=float, action="append", default=[])
    args = parser.parse_args()

    last = round(args.duration * args.fps) - 1
    failed = False
    files = sorted(glob.glob(os.path.join(args.folder, "*.mp4")) + glob.glob(os.path.join(args.folder, "*.webm")))
    for path in files:
        dur, width, height, video, has_audio = info(path)
        checks = []
        ok = abs(dur - args.duration) < 1.5 / args.fps
        checks.append(f"{dur:.3f}s {'ok' if ok else 'WRONG'}")
        if path.endswith(".mp4"):
            # e.g. "yuv420p(tv, bt709/bt709/bt709, progressive)"; a lone "bt709" means matrix only
            tags = re.search(r"\((tv|pc), ([\w/-]+)", video)
            tagged = bool(tags) and tags.group(1) == "tv" and set(tags.group(2).split("/")) == {"bt709"}
            checks.append(f"bt709 {'ok' if tagged else 'UNTAGGED ' + (tags.group(0) if tags else '')}")
            ok &= tagged
        first = frame(path, 0, width, height)
        # the cover: a near-uniform first frame (black, a fade up, one flat color) sells nothing
        spread = float(first.mean(axis=2).std())
        cover = spread >= 6
        checks.append(f"cover {'ok' if cover else 'FLAT (blank or fading in)'}")
        ok &= cover
        if args.bg:
            bg = np.array([int(v) for v in args.bg.split(",")])
            center = frame(path, round(args.bg_at * args.fps), width, height)[height // 2, width // 2]
            good = bool(np.all(np.abs(center - bg) <= 2))
            checks.append(f"bg {center.tolist()} {'ok' if good else 'OFF (color range?)'}")
            ok &= good
        if args.loop:
            diff = np.abs(first - frame(path, last, width, height)).max(axis=2)
            noisy = int((diff > 3).sum())
            good = noisy < 0.001 * width * height and diff.max() < 24
            checks.append(f"seam {noisy}px>3 max {int(diff.max())} {'ok' if good else 'JUMPS'}")
            ok &= good
        if has_audio:
            lufs = loudness(path)
            good = abs(lufs - args.lufs) <= 1
            checks.append(f"{lufs:.1f} LUFS {'ok' if good else 'OFF'}")
            ok &= good
            bad = [g for g in gaps(path, dur) if not any(g[0] <= a <= g[1] for a in args.allow_gap)]
            checks.append("no gaps" if not bad else "GAPS " + ", ".join(f"{a:.2f}-{b:.2f}s" for a, b in bad))
            ok &= not bad
        failed |= not ok
        print(f"{os.path.basename(path)} {width}x{height}: " + " | ".join(checks))
        for probe in args.probe:
            when, point = probe.split(":")
            x, y = (int(v) for v in point.split(","))
            print(f"    probe {probe}: {frame(path, round(float(when) * args.fps), width, height)[y, x].tolist()}")
    if args.script:
        voiced = [f for f in files if info(f)[4]]
        if voiced:
            lost = lost_words(voiced[0], args.script)
            print(f"voice in {os.path.basename(voiced[0])}: " + ("every script word heard" if not lost else "LOST " + " ".join(lost)))
            failed |= bool(lost)
    if not files:
        print("no .mp4 or .webm files found")
        failed = True
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
