"""ElevenLabs for product films: voices, voiceover with word timings, music, sound effects.

Run from the film folder (it reads film.json). Needs ELEVENLABS_API_KEY. Standard library only.

    python3 eleven.py voices                                  list the account's voices (for the interview)
    python3 eleven.py tts [--only v2] [--force]               film.json voice lines -> audio/vo/<id>.mp3 + <id>.json
    python3 eleven.py music-plan --prompt "..." --seconds 30 --out audio/music-plan.json   free draft of a plan
    python3 eleven.py music --plan audio/music-plan.json --out audio/music.mp3            sections keep their durations
    python3 eleven.py music --prompt "..." --seconds 30 --out audio/music.mp3            quick, length may drift
    python3 eleven.py listen audio/music.mp3                                          words in a track = vocals (exit 1)
    python3 eleven.py sfx --text "soft UI click" --seconds 0.5 --out audio/sfx/click.mp3

tts caches: a line is only regenerated when its text, voice or model changed (or --force).
<id>.json holds {text, voice_id, model_id, duration, words: [{w, start, end}]}, seconds from the
clip's start; kit.js wordAt() adds the line's `at` to put a word on the film's clock.
"""

import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.request

API = "https://api.elevenlabs.io"


def call(method, path, body=None, raw=False):
    key = os.environ.get("ELEVENLABS_API_KEY")
    if not key:
        sys.exit("ELEVENLABS_API_KEY is not set. Export it in your shell (e.g. ~/.zshrc) and retry.")
    request = urllib.request.Request(
        API + path, method=method, data=json.dumps(body).encode() if body is not None else None,
        headers={"xi-api-key": key, "content-type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=600) as response:
            data = response.read()
    except urllib.error.HTTPError as error:
        sys.exit(f"ElevenLabs {method} {path}: HTTP {error.code}\n{error.read().decode(errors='replace')[:2000]}")
    return data if raw else json.loads(data)


def write(path, data):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "wb") as handle:
        handle.write(data)
    print(f"{path}  {len(data) / 1e3:.0f} kB")


def words_from(alignment):
    """Group character timings into words (split on whitespace)."""
    words, current = [], None
    for char, start, end in zip(alignment["characters"], alignment["character_start_times_seconds"], alignment["character_end_times_seconds"]):
        if char.isspace():
            current = None
            continue
        if current is None:
            current = {"w": "", "start": round(start, 3), "end": round(end, 3)}
            words.append(current)
        current["w"] += char
        current["end"] = round(end, 3)
    return words


def voices(_):
    data = call("GET", "/v1/voices")
    rank = {"cloned": 0, "professional": 0, "generated": 1, "premade": 2}
    for voice in sorted(data["voices"], key=lambda v: (rank.get(v.get("category"), 3), v["name"])):
        labels = ", ".join(f"{k}: {v}" for k, v in (voice.get("labels") or {}).items())
        print(f"{voice['voice_id']}  {voice.get('category', ''):<12} {voice['name']}  ({labels})")


def tts(args):
    film = json.load(open("film.json"))
    voice = film["voice"]
    if not voice.get("voice_id"):
        sys.exit("film.json voice.voice_id is empty: pick a voice in the interview first (eleven.py voices).")
    lines = voice["lines"]
    for index, line in enumerate(lines):
        if args.only and line["id"] not in args.only:
            continue
        meta_path = f"audio/vo/{line['id']}.json"
        model = line.get("model_id", voice.get("model_id", "eleven_multilingual_v2"))
        if not args.force and os.path.exists(meta_path):
            old = json.load(open(meta_path))
            if (old["text"], old["voice_id"], old["model_id"]) == (line["text"], voice["voice_id"], model):
                print(f"{line['id']}: unchanged, cached")
                continue
        body = {
            "text": line["text"],
            "model_id": model,
            # Neighbouring lines keep intonation continuous across separate clips.
            "previous_text": lines[index - 1]["text"] if index else None,
            "next_text": lines[index + 1]["text"] if index + 1 < len(lines) else None,
        }
        if voice.get("settings"):
            body["voice_settings"] = voice["settings"]
        if voice.get("seed") is not None:
            body["seed"] = voice["seed"]
        data = call("POST", f"/v1/text-to-speech/{voice['voice_id']}/with-timestamps?output_format=mp3_44100_192", body)
        write(f"audio/vo/{line['id']}.mp3", base64.b64decode(data["audio_base64"]))
        words = words_from(data["alignment"])
        meta = {"text": line["text"], "voice_id": voice["voice_id"], "model_id": model,
                "duration": words[-1]["end"] if words else 0, "words": words}
        with open(meta_path, "w") as handle:
            json.dump(meta, handle, indent=1)
        rate = len(words) / meta["duration"] if meta["duration"] else 0
        print(f"{line['id']}: {meta['duration']:.2f} s, {len(words)} words, {rate:.1f} words/s")


def music_plan(args):
    plan = call("POST", "/v1/music/plan", {"prompt": args.prompt, "music_length_ms": int(args.seconds * 1000)})
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w") as handle:
        json.dump(plan, handle, indent=1)
    for section in plan.get("sections", []):
        print(f"{section['section_name']:<24} {section['duration_ms'] / 1000:>6.2f} s")
    print(f"{args.out}: set each section's duration_ms to its act (3 s minimum), empty `lines` for instrumental.")


def as_chunks(plan):
    """music-plan returns sections (music_v1's shape); music_v2 takes chunks. Global styles
    go on the first chunk (it sets the tone) and every chunk keeps the global negatives."""
    if "chunks" in plan:
        return plan
    chunks = []
    for index, section in enumerate(plan["sections"]):
        chunks.append({
            "text": "\n".join([f"[{section['section_name']}]"] + section.get("lines", [])),
            "duration_ms": section["duration_ms"],
            "positive_styles": (plan["positive_global_styles"] if index == 0 else []) + section["positive_local_styles"],
            "negative_styles": plan["negative_global_styles"] + section["negative_local_styles"],
        })
    return {"chunks": chunks}


def sung_lines(plan):
    """Lines the model will sing: chunk text other than [Section] tags and {directions}, or section lyrics."""
    if "chunks" in plan:
        texts = [line.strip() for chunk in plan["chunks"] for line in chunk["text"].splitlines()]
        return [t for t in texts if t and not (t[0] + t[-1] in ("[]", "{}"))]
    return [line for section in plan["sections"] for line in section.get("lines", [])]


def listen(path, quiet=False):
    """Transcribe an audio or video file: words in a music track mean vocals; verify.py uses it on the final mix."""
    key = os.environ.get("ELEVENLABS_API_KEY")
    if not key:
        sys.exit("ELEVENLABS_API_KEY is not set.")
    boundary = "productfilm" + os.urandom(8).hex()
    audio = open(path, "rb").read()
    data = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"model_id\"\r\n\r\nscribe_v1\r\n"
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{os.path.basename(path)}\"\r\n"
            f"Content-Type: application/octet-stream\r\n\r\n").encode() + audio + f"\r\n--{boundary}--\r\n".encode()
    request = urllib.request.Request(API + "/v1/speech-to-text", method="POST", data=data,
                                     headers={"xi-api-key": key, "content-type": f"multipart/form-data; boundary={boundary}"})
    with urllib.request.urlopen(request, timeout=600) as response:
        result = json.loads(response.read())
    words = [w for w in result.get("words", []) if w.get("type") == "word"]
    for w in words if not quiet else []:
        print(f"  {w['start']:6.2f} s  {w['text']}")
    return words


def music(args):
    body = {"model_id": args.model}
    if args.plan:
        plan = json.load(open(args.plan))
        plan = as_chunks(plan) if args.model == "music_v2" else plan
        sung = sung_lines(plan)
        if sung and not args.lyrics:
            sys.exit("These lines would be sung (chunk text and section lines are lyrics):\n  " + "\n  ".join(sung)
                     + "\nKeep only the [Section] tag in text and move directions into positive_styles, or pass --lyrics.")
        body["composition_plan"] = plan
    else:
        body.update({"prompt": args.prompt, "music_length_ms": int(args.seconds * 1000), "force_instrumental": True})
    write(args.out, call("POST", "/v1/music?output_format=mp3_48000_192", body, raw=True))
    if not args.lyrics and listen(args.out):
        sys.exit(f"{args.out} has vocals (words above). Regenerate it; they would talk over the voiceover.")


def sfx(args):
    body = {"text": args.text, "prompt_influence": args.influence}
    if args.seconds:
        body["duration_seconds"] = args.seconds
    write(args.out, call("POST", "/v1/sound-generation?output_format=mp3_44100_192", body, raw=True))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("voices").set_defaults(run=voices)
    p = commands.add_parser("tts")
    p.add_argument("--only", nargs="*")
    p.add_argument("--force", action="store_true")
    p.set_defaults(run=tts)
    p = commands.add_parser("music-plan")
    p.add_argument("--prompt", required=True)
    p.add_argument("--seconds", type=float, required=True)
    p.add_argument("--out", default="audio/music-plan.json")
    p.set_defaults(run=music_plan)
    p = commands.add_parser("music")
    p.add_argument("--plan")
    p.add_argument("--prompt")
    p.add_argument("--seconds", type=float)
    p.add_argument("--model", default="music_v2")
    p.add_argument("--lyrics", action="store_true", help="the plan has lyrics on purpose; skip the vocal checks")
    p.add_argument("--out", default="audio/music.mp3")
    p.set_defaults(run=music)
    p = commands.add_parser("listen")
    p.add_argument("file")
    p.set_defaults(run=lambda a: sys.exit(1 if listen(a.file) else 0))
    p = commands.add_parser("sfx")
    p.add_argument("--text", required=True)
    p.add_argument("--seconds", type=float)
    p.add_argument("--influence", type=float, default=0.3)
    p.add_argument("--out", required=True)
    p.set_defaults(run=sfx)
    args = parser.parse_args()
    if args.command == "music" and not args.plan and not (args.prompt and args.seconds):
        parser.error("music needs --plan, or --prompt and --seconds")
    args.run(args)


if __name__ == "__main__":
    main()
