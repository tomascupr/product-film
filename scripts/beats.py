"""Measure a song's beat grid with numpy.

    uv run --with numpy --with imageio-ffmpeg python3 beats.py \
        --drums drums.mp3 --stem bass=bass.mp3 --stem melody=melody.mp3 \
        --out beats.json

Decodes with the ffmpeg shipped in imageio-ffmpeg. The onset envelope is the spectral flux of the drum stem. Tempo is
the autocorrelation peak, refined by a comb over the whole song. Beat phase is
the comb's best offset. The downbeat is the bar position with the most kick; it warns when the
biggest rise in the drums (the drop) lands off a downbeat, and --downbeat <seconds> overrides the vote.
It writes every beat, every bar start and each stem's loudness per bar, so a
video picks its section from data instead of by ear.
"""

import argparse
import json
import subprocess

import imageio_ffmpeg
import numpy as np

SR = 22050
HOP = 128
N_FFT = 1024


def decode(path):
    out = subprocess.run(
        [imageio_ffmpeg.get_ffmpeg_exe(), "-v", "error", "-i", path, "-ac", "1",
         "-ar", str(SR), "-f", "s16le", "-acodec", "pcm_s16le", "-"],
        check=True, capture_output=True,
    ).stdout
    return np.frombuffer(out, dtype=np.int16).astype(np.float32) / 32768.0


def spectrogram(signal):
    padded = np.pad(signal, (N_FFT // 2, N_FFT // 2))
    count = 1 + (len(padded) - N_FFT) // HOP
    frames = np.lib.stride_tricks.as_strided(
        padded, shape=(count, N_FFT), strides=(padded.strides[0] * HOP, padded.strides[0])
    )
    return np.abs(np.fft.rfft(frames * np.hanning(N_FFT), axis=1))


def flux(magnitude, low_hz=0.0, high_hz=SR / 2):
    freqs = np.fft.rfftfreq(N_FFT, 1 / SR)
    band = np.log1p(1000 * magnitude[:, (freqs >= low_hz) & (freqs < high_hz)])
    rise = np.maximum(np.diff(band, axis=0, prepend=band[:1]), 0).sum(axis=1)
    return rise / (rise.max() or 1)


def sample(envelope, times):
    """Envelope value at arbitrary times, linear between hops."""
    return np.interp(times * SR / HOP, np.arange(len(envelope)), envelope)


def comb(envelope, period, duration, phases):
    beats = np.arange(0, duration, period)
    return np.array([sample(envelope, beats + phase).sum() for phase in phases])


def measure_tempo(envelope, duration):
    centered = envelope - envelope.mean()
    spectrum = np.fft.rfft(centered, 2 * len(centered))
    autocorr = np.fft.irfft(spectrum * np.conj(spectrum))[: len(centered)]
    lags = np.arange(len(autocorr)) * HOP / SR
    window = (lags >= 60 / 200) & (lags <= 60 / 100)
    coarse = 60 / lags[window][np.argmax(autocorr[window])]

    best = (0.0, coarse, 0.0)
    for bpm in np.arange(coarse - 1.5, coarse + 1.5, 0.01):
        period = 60 / bpm
        phases = np.arange(0, period, 0.002)
        scores = comb(envelope, period, duration, phases)
        if scores.max() > best[0]:
            best = (scores.max(), bpm, phases[np.argmax(scores)])
    _, bpm, phase = best
    period = 60 / bpm
    fine = np.arange(phase - 0.004, phase + 0.004, 0.0002)
    phase = fine[np.argmax(comb(envelope, period, duration, fine))]
    return bpm, phase % period


def refine_phase(signal, phase, period, duration, reach=0.03):
    """Move the grid onto the raw attacks. The spectral flux uses a centred 46 ms window,
    so its peaks lead the real transients by ~15 ms; the sharpest rise of the 1 ms
    amplitude envelope near each beat does not."""
    step = SR // 1000
    envelope = np.abs(signal[: len(signal) // step * step]).reshape(-1, step).max(axis=1)
    rise = np.diff(envelope, prepend=envelope[0])
    shifts = []
    bin_seconds = step / SR
    for beat in np.arange(phase, duration, period):
        lo, hi = int((beat - reach) / bin_seconds), int((beat + reach) / bin_seconds)
        if lo < 0 or hi >= len(rise) or rise[lo:hi].max() <= 0.02:
            continue
        # The attack starts in the bin before the sharpest rise's bin ends.
        shifts.append((lo + int(np.argmax(rise[lo:hi]))) * bin_seconds - beat)
    # A beat at t = 0 shifted forward must not fall off the grid: keep phase in [0, period).
    return (phase + float(np.median(shifts))) % period if shifts else phase


def local_offsets(envelope, beats, reach=0.03):
    """How far each beat sits from the nearest onset peak, in ms."""
    offsets = []
    for beat in beats:
        times = np.linspace(beat - reach, beat + reach, 121)
        values = sample(envelope, times)
        if values.max() > 0.2:
            offsets.append((times[np.argmax(values)] - beat) * 1000)
    return np.array(offsets)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--drums", required=True)
    parser.add_argument("--stem", action="append", default=[], help="name=path, measured per bar")
    parser.add_argument("--bpm", type=float, help="skip tempo search and use this tempo")
    parser.add_argument("--meter", type=int, default=4, help="beats per bar (3 for waltz time, 6 for 6/8 counted in eighths)")
    parser.add_argument("--downbeat", type=float, help="seconds of a known downbeat (the drop, say): overrides the vote")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    drums = decode(args.drums)
    duration = len(drums) / SR
    magnitude = spectrogram(drums)
    onsets = flux(magnitude)
    kick = flux(magnitude, 20, 160)
    snare = flux(magnitude, 1500, 6000)

    if args.bpm:
        period = 60 / args.bpm
        phases = np.arange(0, period, 0.0002)
        bpm, phase = args.bpm, phases[np.argmax(comb(onsets, period, duration, phases))]
    else:
        bpm, phase = measure_tempo(onsets, duration)
    period = 60 / bpm
    phase = refine_phase(drums, phase, period, duration)
    beats = np.arange(phase, duration, period)

    kick_at = np.array([sample(kick, np.linspace(b - 0.025, b + 0.025, 11)).max() for b in beats])
    snare_at = np.array([sample(snare, np.linspace(b - 0.025, b + 0.025, 11)).max() for b in beats])

    stems = {"drums": drums}
    for item in args.stem:
        name, path = item.split("=", 1)
        stems[name] = decode(path)

    # Sections start on downbeats, so the bar position where stems come and go
    # decides. Kick and backbeat only break ties: this kick lands on every beat.
    def beat_db(signal):
        return np.array([
            20 * np.log10(max(float(np.sqrt(np.mean(signal[int(b * SR): int((b + period) * SR)] ** 2))), 1e-3))
            for b in beats
        ])

    change = sum(np.abs(np.diff(beat_db(signal), prepend=-60.0)) for signal in stems.values())
    change[0] = 0
    m = args.meter
    bar_position_score = [
        # Backbeat (snare on beats 2 and 4) only means something in 4/4.
        float(change[p::m].sum() + kick_at[p::m].sum() + (snare_at[(p + 1)::m].sum() + snare_at[(p + 3)::m].sum() if m == 4 else 0))
        for p in range(m)
    ]
    downbeat = int(np.argmax(bar_position_score))
    # A drop starts a section, so it lands on a downbeat. When the biggest rise in the drums falls on
    # another beat of the bar, the vote picked the wrong beat (seen on a composed track whose kick
    # played every beat): say so, with the flag that fixes it.
    drum_db = beat_db(drums)
    rise = np.diff(drum_db, prepend=drum_db[0])
    drop = int(np.argmax(rise))
    warning = None
    if args.downbeat is not None:
        downbeat = int(np.argmin(np.abs(beats - args.downbeat))) % m
    elif rise[drop] > 6 and (drop - downbeat) % m:
        warning = (f"WARNING the biggest rise in the drums (+{rise[drop]:.1f} dB at {beats[drop]:.2f} s) lands on beat "
                   f"{(drop - downbeat) % m + 1} of the bar, not a downbeat. If that is the drop, rerun with --downbeat {beats[drop]:.4f}")
    bar_starts = beats[downbeat::m]

    bars = []
    for index, start in enumerate(bar_starts):
        end = start + m * period
        loudness = {}
        for name, signal in stems.items():
            chunk = signal[int(start * SR): int(end * SR)]
            rms = float(np.sqrt(np.mean(chunk ** 2))) if len(chunk) else 0.0
            loudness[name] = round(20 * np.log10(max(rms, 1e-6)), 1)
        bars.append({"index": index, "start": round(float(start), 4), "loudnessDb": loudness})

    offsets = local_offsets(onsets, beats)
    result = {
        "source": args.drums,
        "bpm": round(float(bpm), 3),
        "beatSeconds": round(float(period), 6),
        "firstBeat": round(float(phase), 4),
        "firstDownbeat": round(float(bar_starts[0]), 4),
        "downbeatBeatIndex": downbeat,
        "gridCheckMs": {
            "meanOffset": round(float(offsets.mean()), 2) if len(offsets) else None,
            "spread": round(float(offsets.std()), 2) if len(offsets) else None,
            "beatsChecked": int(len(offsets)),
        },
        "downbeatScoreByBeat": [round(s, 2) for s in bar_position_score],
        "beatsPerBar": m,
        "kickByBarPosition": [round(float(kick_at[(downbeat + p)::m].mean()), 3) for p in range(m)],
        "snareByBarPosition": [round(float(snare_at[(downbeat + p)::m].mean()), 3) for p in range(m)],
        "duration": round(duration, 3),
        "beats": [round(float(b), 4) for b in beats],
        "bars": bars,
    }
    with open(args.out, "w") as handle:
        json.dump(result, handle, indent=1)

    print(f"bpm {result['bpm']}  first downbeat {result['firstDownbeat']}s  grid {result['gridCheckMs']}")
    print(f"kick by bar position {result['kickByBarPosition']}  snare {result['snareByBarPosition']}")
    names = list(stems)
    print("bar   start  " + "  ".join(f"{n[:6]:>6}" for n in names))
    for bar in bars:
        cells = "  ".join(f"{bar['loudnessDb'][n]:>6}" for n in names)
        print(f"{bar['index']:>3}  {bar['start']:>6.2f}  {cells}")
    if warning:
        print(warning)


if __name__ == "__main__":
    main()
