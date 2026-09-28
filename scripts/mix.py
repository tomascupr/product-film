"""Mix the film's audio from film.json: music ducked under the voice, SFX on their hits, loudness-normalised.

    uv run --with numpy --with imageio-ffmpeg python3 mix.py [--lufs -14] [--out audio/mix.wav]

It also writes audio/bed.wav: the same music and SFX without the voice, at the same gain.
energy.py reads it to find the sound's big hits without mistaking words for them.

Reads, from film.json in the current folder:
    duration
    music: {file, from: 0, gain_db: 0, duck_db: -9, fade_in: 0, fade_out: 1.2, dips: []}   (or null)
    voice.lines: [{id, at, gain_db?}]      clips from audio/vo/<id>.mp3 (eleven.py tts)
    sfx: [{file, hit, offset: 0, gain_db: -10}]   `hit` is when the transient lands: the clip starts at hit - its peak

A time (a hit, a dip's ends) is film seconds, a film.json cue name, or "lineId:word", the start of
that word in the line ("v2:SAP#2" for its second time), matched as kit.js wordAt matches it.
Ducking: the music dips by duck_db while any voice line plays (0.15 s attack, 0.4 s release).
music.dips [[from, to, db], ...] dip it where no voice plays (0.4 s ramps outside from and to).
music.stems {name: file} replaces music.file (each read from music.from), and music.duck_stems
[names] ducks only those, so the drums keep driving under the voice. With music.file still set to the
track they were separated from, the stems are lined up with it first: MP3 stems came back 25 ms late.
Loudness: measured with EBU R128, then one linear gain to --lufs (default -14, web and social) and a
peak limiter at -1 dBFS, so ducking and dynamics stay exactly as mixed.
Prints voice windows and resolved hits, and warns on overlaps or lines that run past the end.
"""

import argparse
import json
import os
import re
import subprocess
import sys

import imageio_ffmpeg
import numpy as np

SR = 48000
FF = imageio_ffmpeg.get_ffmpeg_exe()


def decode(path, af=None):
    raw = subprocess.run([FF, "-v", "error", "-i", path, *(["-af", af] if af else []), "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"],
                         check=True, capture_output=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2).copy()


def gain(db):
    return 10 ** (db / 20)


def place(bus, clip, start):
    """Add clip into bus at sample `start`, clipping at both ends."""
    a, b = max(start, 0), min(start + len(clip), len(bus))
    if b > a:
        bus[a:b] += clip[a - start: b - start]


def plain(word):
    """kit.js wordAt's normalisation: lower case, letters and digits only."""
    return "".join(c for c in word.lower() if c.isalnum())


def lateness(reference, other, reach=SR // 2):
    """Samples by which `other` lags `reference`: the peak of their cross-correlation within +-reach."""
    n = min(len(reference), len(other))
    size = 1 << (2 * n - 1).bit_length()
    corr = np.fft.irfft(np.conj(np.fft.rfft(reference[:n].mean(axis=1), size)) * np.fft.rfft(other[:n].mean(axis=1), size), size)
    return int(np.argmax(np.concatenate([corr[-reach:], corr[:reach + 1]]))) - reach


def film_time(value, film):
    """Film seconds from a number, a film.json cue name, or "lineId:word[#n]" (the word's start)."""
    if not isinstance(value, str):
        return value
    if ":" not in value:
        cues = film.get("cues") or {}
        if value not in cues:
            sys.exit(f'"{value}" is not a cue in film.json (cues: {", ".join(cues) or "none"})')
        return cues[value]
    line_id, word = value.split(":", 1)
    word, _, nth = word.partition("#")
    line = next((l for l in (film.get("voice") or {}).get("lines", []) if l["id"] == line_id), None)
    if line is None:
        sys.exit(f'"{value}": film.json has no voice line {line_id}')
    words = json.load(open(f"audio/vo/{line_id}.json"))["words"]
    hits = [w for w in words if plain(w["w"]) == plain(word)]
    if len(hits) < int(nth or 1):
        sys.exit(f'"{value}": "{word}" (#{nth or 1}) is not in voice line {line_id}: {" ".join(w["w"] for w in words)}')
    return line["at"] + hits[int(nth or 1) - 1]["start"]


def ramp(length, attack, release, windows):
    """1 outside windows, 0 inside, with linear attack before and release after each window."""
    t = np.arange(length) / SR
    inside = np.zeros(length)
    for start, end in windows:
        rise = np.clip((t - (start - attack)) / attack, 0, 1)
        fall = np.clip(((end + release) - t) / release, 0, 1)
        inside = np.maximum(inside, np.minimum(rise, fall))
    return 1 - inside


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--lufs", type=float, default=-14.0)
    parser.add_argument("--out", default="audio/mix.wav")
    args = parser.parse_args()

    film = json.load(open("film.json"))
    length = int(round(film["duration"] * SR))
    bus = np.zeros((length, 2), np.float32)
    bed = np.zeros((length, 2), np.float32)  # music + SFX only

    windows = []
    peaks = []  # (dBFS at mix gain, source): named in the limiter warning so the hot source is obvious
    level = lambda clip: float(20 * np.log10(np.abs(clip).max() + 1e-9))
    for line in (film.get("voice") or {}).get("lines", []):
        clip = decode(f"audio/vo/{line['id']}.mp3", line.get("filter")) * gain(line.get("gain_db", 0))
        peaks.append((level(clip), f"voice {line['id']}"))
        start = int(round(line["at"] * SR))
        place(bus, clip, start)
        windows.append((line["at"], line["at"] + len(clip) / SR, line["id"]))
    windows.sort()
    for (s1, e1, a), (s2, e2, b) in zip(windows, windows[1:]):
        if s2 < e1:
            print(f"WARNING voice {b} starts {e1 - s2:.2f} s before {a} ends", file=sys.stderr)
    for s, e, name in windows:
        flag = "  WARNING runs past the end" if e > film["duration"] else ""
        print(f"voice {name}: {s:6.2f} to {e:6.2f} s{flag}")

    music = film.get("music")
    if music:
        stems = music.get("stems") or {"music": music["file"]}
        ducked = music.get("duck_stems", list(stems))
        if set(ducked) - set(stems):
            sys.exit(f"music.duck_stems names {sorted(set(ducked) - set(stems))}, which music.stems lacks ({', '.join(stems)})")
        envelope = np.ones(length)
        fade_in, fade_out = music.get("fade_in", 0), music.get("fade_out", 1.2)
        t = np.arange(length) / SR
        if fade_in:
            envelope *= np.clip(t / fade_in, 0, 1)
        if fade_out:
            envelope *= np.clip((film["duration"] - t) / fade_out, 0, 1)
        for start, end, db in music.get("dips", []):
            dip = ramp(length, 0.4, 0.4, [(film_time(start, film), film_time(end, film))])
            envelope *= dip + (1 - dip) * gain(db)
        duck = ramp(length, 0.15, 0.4, [(s, e) for s, e, _ in windows])
        duck = duck + (1 - duck) * gain(music.get("duck_db", -9))
        tracks = {name: decode(path) for name, path in stems.items()}
        if music.get("stems") and music.get("file"):
            # A separator's stems can come back shifted (MP3 stems: the encoder's 25 ms delay), so line them up with their track.
            longest = max(map(len, tracks.values()))
            late = lateness(decode(music["file"]), sum(np.pad(t, ((0, longest - len(t)), (0, 0))) for t in tracks.values()))
            print(f"music stems: {late / SR * 1000:+.1f} ms against {music['file']}, lined up")
            tracks = {name: t[late:] if late >= 0 else np.pad(t, ((-late, 0), (0, 0))) for name, t in tracks.items()}
        offset = int(round(music.get("from", 0) * SR))
        for name, path in stems.items():
            track = tracks[name][offset: offset + length] * gain(music.get("gain_db", 0))
            peaks.append((level(track), f"music {path}"))
            if len(track) < length:
                print(f"WARNING music {path} ends {(length - len(track)) / SR:.2f} s before the film", file=sys.stderr)
            shaped = track * (envelope * (duck if name in ducked else 1))[:len(track), None].astype(np.float32)
            place(bus, shaped, 0)
            place(bed, shaped, 0)

    quiet = set()
    for effect in film.get("sfx", []):
        offset = effect.get("offset", 0)
        hit = film_time(effect["hit"], film) + offset
        if isinstance(effect["hit"], str):
            print(f"sfx {os.path.basename(effect['file'])} on {effect['hit']}" + (f" {offset:+g} s" if offset else "") + f": {hit:.3f} s")
        clip = decode(effect["file"])
        # A generated effect can come back nearly silent (seen: -55 and -80 dBFS); its gain can't rescue it.
        if level(clip) < -35 and effect["file"] not in quiet:
            quiet.add(effect["file"])
            print(f"WARNING {effect['file']} peaks at {level(clip):.0f} dBFS before gain: nearly silent. Regenerate or synthesize it", file=sys.stderr)
        clip = clip * gain(effect.get("gain_db", -10))
        peaks.append((level(clip), f"sfx {os.path.basename(effect['file'])} at {hit:.2f} s"))
        peak = int(np.argmax(np.abs(clip).max(axis=1)))
        place(bus, clip, int(round(hit * SR)) - peak)
        place(bed, clip, int(round(hit * SR)) - peak)

    raw = bus.astype(np.float32).tobytes()
    base = [FF, "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-"]
    # loudnorm prints its measurement at info level, so this pass must not run with -v error.
    report = subprocess.run([FF, "-hide_banner", "-nostats"] + base[3:] + ["-af", "loudnorm=print_format=json", "-f", "null", "-"], input=raw, capture_output=True).stderr.decode()
    found = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", report)
    if not found:
        sys.exit(f"could not measure loudness:\n{report[-1500:]}")
    measured = json.loads(found.group(0))
    if float(measured["input_i"]) < -70:
        sys.exit("the mix is silent: check film.json music, voice and sfx")
    lift = args.lufs - float(measured["input_i"])
    over = float(measured["input_tp"]) + lift + 1
    # latency=1: without it the limiter's 2 ms lookahead delays the whole mix by 95 samples.
    chain = f"volume={lift:.2f}dB,alimiter=limit=0.891:attack=2:release=60:level=0:latency=1,aresample={SR}"
    subprocess.run(base + ["-af", chain, "-c:a", "pcm_s24le", "-y", args.out], input=raw, check=True)
    bed_out = os.path.join(os.path.dirname(args.out) or '.', 'bed.wav')
    subprocess.run(base + ['-af', chain, '-c:a', 'pcm_s24le', '-y', bed_out], input=bed.astype(np.float32).tobytes(), check=True)
    note = f", limiter catches {over:.1f} dB of peaks" if over > 0 else ""
    if over > 3:
        hot = ", ".join(f"{name} {p:+.1f} dBFS" for p, name in sorted(peaks, reverse=True)[:3])
        at = int(np.argmax(np.abs(bus).max(axis=1))) / SR
        note += (f" (WARNING: the mix peaks at {at:.2f} s, where sources stack; lower what plays there,"
                 f" or accept it if that is the film's intended loudest hit. Hottest single sources: {hot})")
    print(f"{args.out}: {film['duration']:.2f} s, {measured['input_i']} LUFS {lift:+.1f} dB -> {args.lufs} LUFS{note}")


if __name__ == "__main__":
    main()
