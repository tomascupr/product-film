"""Cut a film's music out of a song on the song's bar grid, and place the pieces on the film's clock.

    uv run --with numpy --with imageio-ffmpeg python3 audio-edit.py edit.json

Run it from the film folder. Segments are song bars, so every cut lands on a downbeat. Bars are
beats.json bar indexes (0 = the first downbeat); `toBar` is exclusive; "start" and "end" are the
song's very beginning and end; `beatsPerBar` defaults to 4. A segment follows the one before it,
so the grid runs straight through the join, unless it carries a film time (seconds or a film.json
cue name): "at" plays its first sample then, and "endAt" ends it then, its start trimmed so it
fits after the segment before. A gap before a placed segment is silence, and it is reported when it
is not a whole number of beats: the next downbeat then lands off the pulse. List a segment twice to
loop its bars. Each cut gets a 5 ms fade so nothing clicks; the end fades out.
"""

import json
import subprocess
import sys
import wave

import imageio_ffmpeg
import numpy as np

SR = 48000
FADE = int(0.005 * SR)


def decode(path):
    out = subprocess.run(
        [imageio_ffmpeg.get_ffmpeg_exe(), "-v", "error", "-i", path, "-ac", "2", "-ar", str(SR),
         "-f", "s16le", "-acodec", "pcm_s16le", "-"],
        check=True, capture_output=True,
    ).stdout
    return np.frombuffer(out, dtype=np.int16).reshape(-1, 2).astype(np.float32) / 32768.0


def film_time(value):
    """Seconds, or a film.json cue name."""
    if not isinstance(value, str):
        return value
    cues = json.load(open("film.json")).get("cues") or {}
    if value not in cues:
        sys.exit(f'"{value}" is not a cue in film.json (cues: {", ".join(cues) or "none"})')
    return cues[value]


def main():
    edit = json.load(open(sys.argv[1]))
    song = decode(edit["source"])
    beat = 60 / edit["bpm"]
    bar = beat * edit.get("beatsPerBar", 4)

    def sample(value):
        seconds = {"start": 0, "end": len(song) / SR}[value] if isinstance(value, str) else edit["firstDownbeat"] + value * bar
        return int(round(seconds * SR))

    film = np.zeros((0, 2), np.float32)
    ramp = np.linspace(0, 1, FADE)[:, None]
    for number, segment in enumerate(edit["segments"], 1):
        if "at" in segment and "endAt" in segment:
            sys.exit(f"segment {number}: use at or endAt, not both")
        lo, hi = sample(segment["fromBar"]), sample(segment["toBar"])
        start = int(round(film_time(segment["at"]) * SR)) if "at" in segment else len(film)
        end = start + hi - lo
        if "endAt" in segment:
            end = int(round(film_time(segment["endAt"]) * SR))
            start = max(len(film), end - (hi - lo))
            lo = hi - (end - start)
        # Bars of a measured tempo rarely end on a round time (ten bars at 119.997 BPM run 0.5 ms past
        # 20 s), so a segment placed less than a frame inside the one before it follows it instead.
        if "at" in segment and 0 < len(film) - start <= SR // 60:
            start, end = len(film), len(film) + hi - lo
        if start < len(film) or end <= start:
            sys.exit(f"segment {number} is empty or overlaps the one before it, which ends at {len(film) / SR:.3f} s")
        gap = (start - len(film)) / SR / beat if len(film) else 0
        off_pulse = gap > 0.05 and abs(gap - round(gap)) > 0.05
        on_pulse = (len(film) + max(1, round(gap)) * beat * SR) / SR
        piece = song[lo:hi].copy()
        if start:
            piece[:FADE] *= ramp
        piece[-FADE:] *= ramp[::-1]
        film = np.concatenate([film, np.zeros((start - len(film), 2), np.float32), piece])
        print(f"  bars {segment['fromBar']} to {segment['toBar']}: film {start / SR:.3f} to {len(film) / SR:.3f} s"
              + (f" (from {lo / SR:.3f} s of the song)" if "endAt" in segment else ""))
        if off_pulse:
            print(f"    the {gap * beat:.3f} s of silence before it is {gap:.2f} of a beat, so its downbeat lands off the pulse of the bars"
                  f" before and can be heard as a stumble. On the pulse it would start at {on_pulse:.3f} s, or follow with no gap.")

    film = film[: int(round(edit["duration"] * SR))]
    fade = int(edit.get("fadeOutSeconds", 0) * SR)
    if fade:
        film[-fade:] *= np.linspace(1, 0, fade)[:, None] ** 2

    with wave.open(edit["out"], "wb") as handle:
        handle.setnchannels(2)
        handle.setsampwidth(2)
        handle.setframerate(SR)
        handle.writeframes((np.clip(film, -1, 1) * 32767).astype(np.int16).tobytes())
    print(f"{edit['out']}: {len(film) / SR:.3f} s from {len(edit['segments'])} segments")


if __name__ == "__main__":
    main()
