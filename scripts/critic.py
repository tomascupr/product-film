"""Pack a rendered film for a fresh-eyes critic: what a viewer sees, with none of the build's history.

    uv run --with numpy --with imageio-ffmpeg python3 critic.py out/draft/draft.mp4 [--peak 3.06] [--brief film-prompt.md]

Writes out/critic/<video name>/:
  cover.png          frame 0 at 300 px, the thumbnail many players show
  sheet-N.png        the film every 1/3 s, 4 x 4 frames per sheet, row by row (sheet-1 starts at 0.0 s)
  cue-<name>.png     10 frames 0.1 s apart from 0.3 s before each film.json cue, and before --peak as
                     cue-peak.png: a hit or a handoff is over between two frames of a sheet
  frames/t=S.png     each sampled frame at 540 px, to zoom in on one moment
  energy.txt         energy.py's report on the same file
  brief.md           the film's direction and beat sheet (from --brief), for the second half of the review
  README.txt         what each file is, in the order the critic should look

Then give reference/critic.md and this folder to a reviewer that has not seen the build (reference/review.md).
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys

import imageio_ffmpeg

FF = imageio_ffmpeg.get_ffmpeg_exe()
HERE = os.path.dirname(os.path.abspath(__file__))


def grab(video, t, width, out):
    subprocess.run([FF, "-v", "error", "-y", "-ss", f"{t:.3f}", "-i", video, "-frames:v", "1",
                    "-vf", f"scale={width}:-2:flags=area", out], check=True)


def tile(files, cols, out, width=270):
    inputs = sum((["-i", f] for f in files), [])
    rows = -(-len(files) // cols)
    layout = "|".join(f"{(i % cols) * width}_{(i // cols) * width}" for i in range(len(files)))
    scaled = "".join(f"[{i}:v]scale={width}:{width}:force_original_aspect_ratio=decrease,pad={width}:{width}:(ow-iw)/2:(oh-ih)/2[s{i}];" for i in range(len(files)))
    stack = "".join(f"[s{i}]" for i in range(len(files)))
    subprocess.run([FF, "-v", "error", "-y", *inputs, "-filter_complex",
                    f"{scaled}{stack}xstack=inputs={len(files)}:layout={layout}:fill=0x333333", out] if len(files) > 1
                   else [FF, "-v", "error", "-y", "-i", files[0], out], check=True)
    return rows


def duration(video):
    text = subprocess.run([FF, "-hide_banner", "-i", video], capture_output=True, text=True).stderr
    h, m, s = text.split("Duration: ")[1].split(",")[0].split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("video")
    p.add_argument("--peak", type=float)
    p.add_argument("--brief", default="film-prompt.md")
    # 1/3 s: fine enough to see every move, and off the common beat lengths (0.4-0.6 s at 100-150 BPM)
    # so a blink or pulse on the beat is not sampled at the same phase every time and made invisible
    p.add_argument("--step", type=float, default=1 / 3)
    args = p.parse_args()

    name = os.path.splitext(os.path.basename(args.video))[0]
    out = os.path.join("out", "critic", name)
    shutil.rmtree(out, ignore_errors=True)
    os.makedirs(os.path.join(out, "frames"))
    dur = duration(args.video)

    grab(args.video, 0, 300, os.path.join(out, "cover.png"))
    times = [round(i * args.step, 3) for i in range(int(dur / args.step) + 1) if i * args.step < dur - 0.02]
    files = []
    for t in times:
        f = os.path.join(out, "frames", f"t={t:05.2f}.png")  # times are rounded to 0.01 s in names
        grab(args.video, t, 540, f)
        files.append(f)
    sheets = []
    for k in range(0, len(files), 16):
        sheet = os.path.join(out, f"sheet-{k // 16 + 1}.png")
        tile(files[k:k + 16], 4, sheet)
        sheets.append((sheet, times[k], times[min(k + 15, len(times) - 1)]))

    cues = json.load(open("film.json")).get("cues", {}) if os.path.exists("film.json") else {}
    if args.peak is not None:
        cues["peak"] = args.peak
    moments = {}  # cues that share a time share a strip
    for name, t in cues.items():
        if isinstance(t, (int, float)) and 0 <= t < dur:
            moments.setdefault(round(t, 2), []).append(name)
    strips = []
    for t, names in sorted(moments.items()):
        name = "+".join(names)
        strip = os.path.join(out, f"cue-{re.sub(r'[^\w+-]', '_', name)}.png")
        frames = []
        for i in range(10):
            f = strip.replace(".png", f"-{i}.png")
            grab(args.video, min(dur - 0.02, max(0, t - 0.3 + i * 0.1)), 540, f)
            frames.append(f)
        tile(frames, 5, strip)
        for f in frames:
            os.remove(f)
        strips.append((strip, name, t))

    report = subprocess.run([sys.executable, os.path.join(HERE, "energy.py"), args.video], capture_output=True, text=True)
    open(os.path.join(out, "energy.txt"), "w").write(report.stdout + report.stderr)
    if os.path.exists(args.brief):
        shutil.copy(args.brief, os.path.join(out, "brief.md"))

    guide = [f"Film: {os.path.basename(args.video)}, {dur:.1f} s. Look in this order:",
             "1. cover.png: frame 0 at 300 px, the thumbnail many players show."]
    guide += [f"{i + 2}. {os.path.basename(s)}: the film from {a:.2f} s to {b:.2f} s, one frame every {args.step:.2f} s, 4 per row, row by row."
              for i, (s, a, b) in enumerate(sheets)]
    n = len(sheets) + 2
    for strip, name, t in strips:
        guide.append(f"{n}. {os.path.basename(strip)}: 10 frames 0.1 s apart from {max(0, t - 0.3):.2f} s, 5 per row, around the cue {name} at {t:.2f} s.")
        n += 1
    guide.append(f"{n}. frames/: every sampled frame at 540 px, named by time, to zoom in.")
    guide.append(f"{n + 1}. energy.txt: measured motion per 0.25 s with the sound's loudness beside it, dead stretches, and loud hits that land on still frames.")
    if os.path.exists(os.path.join(out, "brief.md")):
        guide.append(f"{n + 2}. brief.md: what the film was meant to do. Read it only after judging the film as a viewer.")
    open(os.path.join(out, "README.txt"), "w").write("\n".join(guide) + "\n")
    print(out)
    print("\n".join(guide))


if __name__ == "__main__":
    main()
