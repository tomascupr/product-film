"""ElevenLabs for product films: voices, voiceover with word timings, music, sound effects.

Run from the film folder (it reads film.json). Needs ELEVENLABS_API_KEY. Standard library only.

    python3 eleven.py voices                                  list the account's voices (for the interview)
    python3 eleven.py tts [--only v2] [--force]               film.json voice lines -> audio/vo/<id>.mp3 + <id>.json
    python3 eleven.py align v2 takes/v2.m4a                   your own recording of line v2, timed to its words
    python3 eleven.py sts v2 takes/v2.m4a                     your read of line v2 in the line's voice, then timed
    python3 eleven.py music-plan --prompt "..." --seconds 30 --out audio/music-plan.json   free draft of a plan
    python3 eleven.py music --plan audio/music-plan.json --out audio/music.mp3            sections keep their durations
    python3 eleven.py music --prompt "..." --seconds 30 --out audio/music.mp3            quick, length may drift
    python3 eleven.py listen audio/music.mp3                                          words in a track = vocals (exit 1)
    python3 eleven.py sfx --text "soft UI click" --seconds 0.5 --out audio/sfx/click.mp3
    python3 eleven.py stems audio/music.mp3 [--out audio/stems] [--variation six_stems_v1]   one file per stem

tts caches: a line is only regenerated when its text, voice, model or the pronounce rules for its words
changed (or --force). It keeps a take from align or sts unless --force.
A line may set its own "voice_id" (and "settings") for a second speaker; voice.voice_id is the default.
voice.pronounce fixes a word in every line: [{"word": "live", "ipa": "laɪv"}, {"word": "SQL", "alias": "sequel"}].
<id>.json holds {text, voice_id, model_id, duration, words: [{w, start, end}]} (align and sts add "source"),
seconds from the clip's start; [audio tags] are not words. kit.js wordAt() adds the line's `at` to put a
word on the film's clock. align and sts need ffmpeg on PATH.
"""

import argparse
import base64
import io
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
import zipfile

API = "https://api.elevenlabs.io"
# Measured: these models honour an ipa rule. eleven_multilingual_v2 drops the word from the audio instead.
PHONEME_MODELS = ("eleven_v4", "eleven_v4_turbo", "eleven_v3", "eleven_flash_v2")
STS_MODEL = "eleven_multilingual_sts_v2"  # the docs say it often beats eleven_english_sts_v2, even on English


def call(method, path, body=None, raw=False, file=None, field="file"):
    """A JSON request, or with `file` a multipart form of `body`'s fields plus that file."""
    key = os.environ.get("ELEVENLABS_API_KEY")
    if not key:
        sys.exit("ELEVENLABS_API_KEY is not set. Export it in your shell (e.g. ~/.zshrc) and retry.")
    headers = {"xi-api-key": key, "content-type": "application/json"}
    data = json.dumps(body).encode() if body is not None else None
    if file:
        boundary = "productfilm" + os.urandom(8).hex()
        headers["content-type"] = f"multipart/form-data; boundary={boundary}"
        data = b"".join(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode() for k, v in (body or {}).items())
        data += (f"--{boundary}\r\nContent-Disposition: form-data; name=\"{field}\"; filename=\"{os.path.basename(file)}\"\r\n"
                 "Content-Type: application/octet-stream\r\n\r\n").encode() + open(file, "rb").read() + f"\r\n--{boundary}--\r\n".encode()
    request = urllib.request.Request(API + path, method=method, data=data, headers=headers)
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


def words_from(timed):
    """Group (character, start, end) timings into words, split on whitespace. [Audio tags] are not words."""
    words, current, tag = [], None, False
    for char, start, end in timed:
        tag = tag or char == "["
        if tag or char.isspace():
            tag = tag and char != "]"
            current = None
            continue
        if current is None:
            current = {"w": "", "start": round(start, 3), "end": round(end, 3)}
            words.append(current)
        current["w"] += char
        current["end"] = round(end, 3)
    return words


def spoken(text):
    """A line's text without its [audio tags]: what a voice actually says."""
    return " ".join(re.sub(r"\[[^\]]*\]", " ", text).split())


def said(word, text):
    """Whether a pronounce rule's word is in a line, matched as the dictionary does (whole word, any case)."""
    return re.search(rf"(?<!\w){re.escape(word)}(?!\w)", text, re.I)


def dictionary(rules):
    """The locator of a pronunciation dictionary with exactly these rules, created once per film."""
    path = "audio/vo/pronounce.json"
    made = json.load(open(path)) if os.path.exists(path) else []
    entry = next((d for d in made if d["rules"] == rules), None)
    if not entry:
        new = call("POST", "/v1/pronunciation-dictionaries/add-from-rules", {"name": os.path.basename(os.getcwd()), "rules": rules})
        entry = {"rules": rules, "pronunciation_dictionary_id": new["id"], "version_id": new["version_id"]}
        os.makedirs("audio/vo", exist_ok=True)
        with open(path, "w") as handle:
            json.dump(made + [entry], handle, indent=1)
    return {k: entry[k] for k in ("pronunciation_dictionary_id", "version_id")}


def save(line_id, meta, words):
    meta.update(duration=words[-1]["end"] if words else 0, words=words)
    with open(f"audio/vo/{line_id}.json", "w") as handle:
        json.dump(meta, handle, indent=1)
    rate = len(words) / meta["duration"] if meta["duration"] else 0
    print(f"{line_id}: {meta['duration']:.2f} s, {len(words)} words, {rate:.1f} words/s")


def voices(_):
    data = call("GET", "/v1/voices")
    rank = {"cloned": 0, "professional": 0, "generated": 1, "premade": 2}
    for voice in sorted(data["voices"], key=lambda v: (rank.get(v.get("category"), 3), v["name"])):
        labels = ", ".join(f"{k}: {v}" for k, v in (voice.get("labels") or {}).items())
        # eleven_v4 still takes a professional voice without its v4 fine-tune, and says nothing
        tuned = ((voice.get("fine_tuning") or {}).get("state") or {}).get("eleven_v4") == "fine_tuned"
        note = "  no v4 fine-tune" if voice.get("category") == "professional" and not tuned else ""
        print(f"{voice['voice_id']}  {voice.get('category', ''):<12} {voice['name']}  ({labels}){note}")


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
        model = line.get("model_id", voice.get("model_id", "eleven_v4"))
        # A line can have its own speaker (dialogue, a control room, an interview).
        speaker = line.get("voice_id", voice["voice_id"])
        same = lambda other: other.get("voice_id", voice["voice_id"]) == speaker
        # Only rules for this line's words, so a new rule retakes just the lines that say it.
        pronounce = [r for r in voice.get("pronounce", []) if said(r["word"], line["text"])]
        if not args.force and os.path.exists(meta_path):
            old = json.load(open(meta_path))
            if old.get("source"):
                stale = ", but the script changed since: redo the take, or tts --force" if old["text"] != line["text"] else ""
                print(f"{line['id']}: {old['source']} take kept{stale}")
                continue
            if (old["text"], old["voice_id"], old["model_id"], old.get("pronounce", [])) == (line["text"], speaker, model, pronounce):
                print(f"{line['id']}: unchanged, cached")
                continue
        body = {
            "text": line["text"],
            "model_id": model,
            # Neighbouring lines by the same speaker keep intonation continuous across separate clips.
            "previous_text": lines[index - 1]["text"] if index and same(lines[index - 1]) else None,
            "next_text": lines[index + 1]["text"] if index + 1 < len(lines) and same(lines[index + 1]) else None,
        }
        if line.get("settings", voice.get("settings")):
            body["voice_settings"] = line.get("settings", voice.get("settings"))
        if voice.get("seed") is not None:
            body["seed"] = voice["seed"]
        rules = []
        for rule in voice.get("pronounce", []):
            if "ipa" in rule and model in PHONEME_MODELS:
                rules.append({"string_to_replace": rule["word"], "type": "phoneme", "phoneme": rule["ipa"], "alphabet": "ipa", "case_sensitive": False})
            elif "alias" in rule:
                rules.append({"string_to_replace": rule["word"], "type": "alias", "alias": rule["alias"], "case_sensitive": False})
            elif rule in pronounce:
                print(f"{line['id']}: {model} would drop \"{rule['word']}\" for its ipa rule, so it keeps its usual "
                      f"pronunciation here. Give the rule an alias, or use eleven_v4.")
        if rules:
            body["pronunciation_dictionary_locators"] = [dictionary(rules)]
        data = call("POST", f"/v1/text-to-speech/{speaker}/with-timestamps?output_format=mp3_44100_192", body)
        write(f"audio/vo/{line['id']}.mp3", base64.b64decode(data["audio_base64"]))
        meta = {"text": line["text"], "voice_id": speaker, "model_id": model}
        if pronounce:
            meta["pronounce"] = pronounce
        a = data["alignment"]
        save(line["id"], meta, words_from(zip(a["characters"], a["character_start_times_seconds"], a["character_end_times_seconds"])))


def take(args, convert):
    """A read of one line: your recording as it is (align), or converted into the line's voice (sts)."""
    voice = json.load(open("film.json"))["voice"]
    line = next((each for each in voice["lines"] if each["id"] == args.line), None)
    if not line:
        sys.exit(f"film.json has no voice line {args.line}")
    # The take replaces the clip only once it is timed, so a failed call leaves clip and words matching.
    take_path = f"audio/vo/{line['id']}.take.mp3"
    os.makedirs("audio/vo", exist_ok=True)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", args.audio, "-vn", "-b:a", "192k", take_path], check=True)
    meta = {"text": line["text"], "voice_id": None, "model_id": None, "source": "recorded"}
    if convert:
        speaker = line.get("voice_id") or voice.get("voice_id")
        if not speaker:
            sys.exit("film.json has no voice for this line: pick one first (eleven.py voices).")
        # speech to speech keeps the read's timing but returns audio only, so it is timed after
        audio = call("POST", f"/v1/speech-to-speech/{speaker}?output_format=mp3_44100_192", {"model_id": STS_MODEL},
                     raw=True, file=take_path, field="audio")
        with open(take_path, "wb") as handle:
            handle.write(audio)
        meta.update(voice_id=speaker, model_id=STS_MODEL, source="converted")
    aligned = call("POST", "/v1/forced-alignment", {"text": spoken(line["text"])}, file=take_path)
    os.replace(take_path, f"audio/vo/{line['id']}.mp3")
    save(line["id"], meta, words_from((c["text"], c["start"], c["end"]) for c in aligned["characters"]))


def music_plan(args):
    plan = call("POST", "/v1/music/plan", {"prompt": args.prompt, "music_length_ms": int(args.seconds * 1000)})
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w") as handle:
        json.dump(plan, handle, indent=1)
    for section in plan.get("sections", []):
        print(f"{section['section_name']:<24} {section['duration_ms'] / 1000:>6.2f} s")
    print(f"{args.out}: set each section's duration_ms to its act (3 s minimum), empty `lines` for instrumental.")


def as_chunks(plan):
    """music-plan returns sections (music_v1's shape); music_v2 and music_v2_5 take chunks. Global styles
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
    result = call("POST", "/v1/speech-to-text", {"model_id": "scribe_v1"}, file=path)
    words = [w for w in result.get("words", []) if w.get("type") == "word"]
    for w in words if not quiet else []:
        print(f"  {w['start']:6.2f} s  {w['text']}")
    return words


def music(args):
    body = {"model_id": args.model}
    if args.plan:
        plan = json.load(open(args.plan))
        plan = as_chunks(plan) if args.model != "music_v1" else plan
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


def stems(args):
    data = call("POST", "/v1/music/stem-separation?output_format=mp3_44100_192", {"stem_variation_id": args.variation},
                raw=True, file=args.file)
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        for name in archive.namelist():
            if not name.endswith("/"):
                write(os.path.join(args.out, os.path.basename(name)), archive.read(name))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("voices").set_defaults(run=voices)
    p = commands.add_parser("tts")
    p.add_argument("--only", nargs="*")
    p.add_argument("--force", action="store_true")
    p.set_defaults(run=tts)
    p = commands.add_parser("align")
    p.add_argument("line")
    p.add_argument("audio")
    p.set_defaults(run=lambda a: take(a, convert=False))
    p = commands.add_parser("sts")
    p.add_argument("line")
    p.add_argument("audio")
    p.set_defaults(run=lambda a: take(a, convert=True))
    p = commands.add_parser("music-plan")
    p.add_argument("--prompt", required=True)
    p.add_argument("--seconds", type=float, required=True)
    p.add_argument("--out", default="audio/music-plan.json")
    p.set_defaults(run=music_plan)
    p = commands.add_parser("music")
    p.add_argument("--plan")
    p.add_argument("--prompt")
    p.add_argument("--seconds", type=float)
    p.add_argument("--model", default="music_v2_5")
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
    p = commands.add_parser("stems")
    p.add_argument("file")
    p.add_argument("--out", default="audio/stems")
    p.add_argument("--variation", default="six_stems_v1", help="six_stems_v1 or two_stems_v1")
    p.set_defaults(run=stems)
    args = parser.parse_args()
    if args.command == "music" and not args.plan and not (args.prompt and args.seconds):
        parser.error("music needs --plan, or --prompt and --seconds")
    args.run(args)


if __name__ == "__main__":
    main()
