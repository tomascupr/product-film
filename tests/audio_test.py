"""Where audio-edit.py puts segments and where mix.py puts hits named by cue or word. Offline, on synthetic WAVs.

    uv run --with numpy --with imageio-ffmpeg python3 tests/audio_test.py
"""

import json
import os
import subprocess
import sys
import tempfile
import wave

import imageio_ffmpeg
import numpy as np

SCRIPTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts")
SR = 48000


def write_wav(path, mono):
    with wave.open(path, "wb") as handle:
        handle.setnchannels(2)
        handle.setsampwidth(2)
        handle.setframerate(SR)
        handle.writeframes(np.repeat((np.clip(mono, -1, 1) * 32767).astype(np.int16), 2).tobytes())


def read(path):
    """The left channel: ffmpeg's -ac 1 downmix would scale the level by 3 dB."""
    raw = subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-v", "error", "-i", path, "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"],
                         check=True, capture_output=True).stdout
    return np.frombuffer(raw, np.float32)[::2]


def run(folder, script, *args):
    return subprocess.run([sys.executable, os.path.join(SCRIPTS, script), *args], cwd=folder, capture_output=True, text=True)


def dump(path, data):
    with open(path, "w") as handle:
        json.dump(data, handle)


def edit_places_segments(folder):
    # The song's level is its own clock (0.5 at 20 s), so every film sample says which song time it plays.
    write_wav(f"{folder}/song.wav", 0.5 * np.arange(20 * SR) / (20 * SR))
    dump(f"{folder}/film.json", {"cues": {"hush": 3.0, "peak": 3.3}})
    # 120 BPM, bars of 2 s from 0.25 s: bars 0-2 end on the hush (start trimmed), silence, bar 3 on the peak, then bar 3 again.
    dump(f"{folder}/edit.json", {"source": "song.wav", "out": "music.wav", "bpm": 120, "firstDownbeat": 0.25, "duration": 7.3,
                                 "segments": [{"fromBar": 0, "toBar": 2, "endAt": "hush"}, {"fromBar": 3, "toBar": 4, "at": "peak"},
                                              {"fromBar": 3, "toBar": 4}]})
    result = run(folder, "audio-edit.py", "edit.json")
    assert result.returncode == 0, result.stderr
    film = read(f"{folder}/music.wav")
    for t, song in [(0.5, 1.75), (2.99, 4.24), (3.15, None), (3.31, 6.26), (5.2, 8.15), (5.31, 6.26), (7.2, 8.15)]:
        value = film[int(round(t * SR))]
        if song is None:
            assert abs(value) < 1e-4, f"film {t} s should be silent, plays song {value / 0.5 * 20:.3f} s"
        else:
            assert abs(value / 0.5 * 20 - song) < 0.003, f"film {t} s plays song {value / 0.5 * 20:.3f} s, expected {song} s"
    assert abs(len(film) / SR - 7.3) < 1e-3, len(film) / SR


def mix_places_hits(folder):
    os.makedirs(f"{folder}/audio/vo")
    click = np.zeros(int(0.3 * SR))
    click[int(0.1 * SR)] = 0.9  # the transient sits 0.1 s into the clip
    write_wav(f"{folder}/click.wav", click)
    write_wav(f"{folder}/audio/vo/v1.mp3", 0.1 * np.sin(2 * np.pi * 440 * np.arange(int(1.5 * SR)) / SR))  # ffmpeg probes the content
    dump(f"{folder}/audio/vo/v1.json", {"words": [{"w": "Hello,", "start": 0.1, "end": 0.3}, {"w": "world", "start": 0.4, "end": 0.6},
                                                  {"w": "World!", "start": 0.9, "end": 1.2}]})
    film = {"duration": 3.0, "cues": {"boom": 1.0}, "voice": {"lines": [{"id": "v1", "at": 0.5}]}, "music": None,
            "sfx": [{"file": "click.wav", "hit": "boom", "gain_db": -20},
                    {"file": "click.wav", "hit": "v1:world#2", "offset": 0.05, "gain_db": -20},
                    {"file": "click.wav", "hit": 2.2, "gain_db": -20}]}
    dump(f"{folder}/film.json", film)
    result = run(folder, "mix.py")
    assert result.returncode == 0, result.stderr
    assert "v1:world#2 +0.05 s: 1.450 s" in result.stdout, result.stdout
    bed = np.abs(read(f"{folder}/audio/bed.wav"))
    for hit in (1.0, 1.45, 2.2):
        window = slice(int((hit - 0.02) * SR), int((hit + 0.02) * SR))
        found = (window.start + int(np.argmax(bed[window]))) / SR
        assert abs(found - hit) <= 1 / SR, f"click meant for {hit} s lands at {found:.5f} s"
    for bad, message in [("v1:nope", 'is not in voice line v1'), ("nocue", "is not a cue")]:
        film["sfx"] = [{"file": "click.wav", "hit": bad}]
        dump(f"{folder}/film.json", film)
        result = run(folder, "mix.py")
        assert result.returncode != 0 and message in result.stderr, (bad, result.returncode, result.stderr)


def mix_lines_up_stems(folder):
    # Two stems of a click track, each 1203 samples late like the MP3 stems a separator returned: the mix must land them on time.
    clicks = {0.5: "a", 1.0: "b", 1.5: "a"}
    os.makedirs(f"{folder}/audio")
    track, stems = np.zeros(2 * SR), {"a": np.zeros(2 * SR + 1203), "b": np.zeros(2 * SR + 1203)}
    for t, name in clicks.items():
        track[int(t * SR)] = stems[name][int(t * SR) + 1203] = 0.9
    write_wav(f"{folder}/track.wav", track)
    for name, stem in stems.items():
        write_wav(f"{folder}/{name}.wav", stem)
    dump(f"{folder}/film.json", {"duration": 2.0, "music": {"file": "track.wav", "stems": {"a": "a.wav", "b": "b.wav"},
                                                             "gain_db": -20, "fade_out": 0}})
    result = run(folder, "mix.py")
    assert result.returncode == 0, result.stderr
    assert "music stems: +25.1 ms against track.wav, lined up" in result.stdout, result.stdout
    bed = np.abs(read(f"{folder}/audio/bed.wav"))
    for t in clicks:
        window = slice(int((t - 0.05) * SR), int((t + 0.05) * SR))
        found = (window.start + int(np.argmax(bed[window]))) / SR
        assert abs(found - t) <= 1 / SR, f"stem click meant for {t} s lands at {found:.5f} s"


if __name__ == "__main__":
    for check in (edit_places_segments, mix_places_hits, mix_lines_up_stems):
        with tempfile.TemporaryDirectory() as folder:
            check(folder)
        print(f"ok {check.__name__}")
