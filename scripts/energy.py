"""Measure a draft's energy: where the picture moves, where it sits dead, and whether the big hits in
the sound land on big moves in the picture.

    uv run --with numpy --with imageio-ffmpeg python3 energy.py out/draft/draft.mp4 [--dead 0.6] [--span 1.5]

Run it from the film folder: the hits come from audio/bed.wav (music + SFX, written by mix.py) when it
exists, so the voice's words are not mistaken for hits; otherwise from the video's own audio.

- motion: mean absolute change between frames (0-255, 20 fps, grayscale at 160 px), per 0.25 s window,
  printed as one bar per window so the film's energy curve reads at a glance
- dead stretches: runs longer than --span seconds where motion stays under --dead. A dead stretch on a
  settled end card is still a dead stretch; give it life (a push, a beat, a second reveal) or cut it.
- sound: loudness per window (RMS dB) of the video's own sound, the full mix a viewer hears, printed
  after each motion bar.
- hits: the loudest onsets in the audio. Each should sit on a move (motion in the top third of the film
  within 0.15 s). A hit on a still frame is a peak the picture missed.
Exits non-zero when it finds a dead stretch or a missed hit. Compare drafts by their mean and dead time.

Calibration: the defaults come from a 16 s 1:1 teaser whose flat first draft scored mean 0.33 with
11 s dead, and whose approved cut scored 3.6 with 2.5 s dead (its end-card hold). Under 0.6 a frame
reads as still at phone size; a hit is a rise of 10 dB or more within 100 ms (a riser climbs slower);
"on a move" means motion in the top third of the film within 0.15 s, about the slack the eye allows.
A long readable end card can stay flagged by choice: keep the verdict visible and say why.
"""

import argparse
import os
import subprocess
import sys

import imageio_ffmpeg
import numpy as np

FF = imageio_ffmpeg.get_ffmpeg_exe()
FPS, SIZE, WIN, RATE = 20, 160, 0.25, 8000


def motion(path):
    raw = subprocess.run([FF, "-v", "error", "-i", path, "-vf", f"fps={FPS},scale={SIZE}:{SIZE},format=gray",
                          "-f", "rawvideo", "-"], capture_output=True).stdout
    frames = np.frombuffer(raw, np.uint8).reshape(-1, SIZE, SIZE).astype(np.int16)
    diff = np.abs(np.diff(frames, axis=0)).mean(axis=(1, 2))  # diff[i]: change from frame i to i+1
    per = int(FPS * WIN)
    return np.array([diff[i:i + per].mean() for i in range(0, len(diff) - per + 1, per)])


def sound(path):
    raw = subprocess.run([FF, "-v", "error", "-i", path, "-vn", "-ac", "1", "-ar", str(RATE), "-f", "s16le", "-"],
                         capture_output=True).stdout
    return np.frombuffer(raw, np.int16).astype(float) / 32768


def level(a, hop):
    """RMS dB of the audio per `hop` samples."""
    return np.array([20 * np.log10(np.sqrt((a[i:i + hop] ** 2).mean()) + 1e-6) for i in range(0, len(a) - hop, hop)])


def onsets(a, top):
    hop = RATE // 20  # 50 ms
    db = level(a, hop)
    jump = np.maximum(0, db[2:] - db[:-2])  # rise over 100 ms
    picked = []
    for i in np.argsort(-jump):
        t = (i + 2) * hop / RATE
        if jump[i] < 10 or len(picked) == top:  # a riser climbs under 10 dB per 100 ms; a hit jumps more
            break
        if all(abs(t - p) > 0.5 for p, _ in picked):
            picked.append((t, jump[i]))
    return sorted(picked)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("video")
    p.add_argument("--dead", type=float, default=0.6, help="motion under this is a still frame")
    p.add_argument("--span", type=float, default=1.5, help="seconds of stillness that count as dead")
    p.add_argument("--hits", type=int, default=5)
    p.add_argument("--audio", default="audio/bed.wav" if os.path.exists("audio/bed.wav") else None)
    args = p.parse_args()

    m = motion(args.video)
    heard = sound(args.video)
    db = level(heard, int(RATE * WIN))
    if len(db):
        print(f"motion per {WIN} s, each followed by the loudness of the film's sound")
    top = np.quantile(m, 2 / 3)
    cells = [f"{v:5.1f} {'#' * min(24, int(v))}".ljust(30) + (f"{db[j]:4.0f} dB" if j < len(db) else "") for j, v in enumerate(m)]
    for i in range(0, len(m), 4):
        print(f"{i * WIN:5.1f} s  " + "  ".join(cells[i:i + 4]))

    dead, run = [], 0
    for i, v in enumerate(list(m) + [np.inf]):
        if v < args.dead:
            run += 1
            continue
        if run * WIN > args.span:
            dead.append(((i - run) * WIN, i * WIN))
        run = 0

    missed = []
    for t, rise in onsets(sound(args.audio) if args.audio else heard, args.hits):
        near = m[max(0, int((t - 0.15) / WIN)):int((t + 0.15) / WIN) + 1]
        ok = len(near) and near.max() >= top
        if not ok:
            missed.append(t)
        print(f"hit {t:5.2f} s (+{rise:.0f} dB): {'on a move' if ok else 'MISSED, the picture is still'}")

    print(f"mean motion {m.mean():.2f} | dead {sum(b - a for a, b in dead):.1f} s"
          + "".join(f" | DEAD {a:.2f} to {b:.2f} s" for a, b in dead))
    sys.exit(1 if dead or missed else 0)


if __name__ == "__main__":
    main()
