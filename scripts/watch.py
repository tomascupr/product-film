"""A second fresh-eyes critic that watches and hears the film itself: Gemini, through its API.

    python3 watch.py out/<name>/<name>.mp4 [--brief film-prompt.md] [--fps 10] [--model gemini-3.8-flash] [--no-audio-file]

Run it from the film folder, like critic.py. Needs GEMINI_API_KEY and ffmpeg. Standard library only.

- Uploads the film to Google's Files API and, unless --no-audio-file, its soundtrack again as a lossless
  file: the API hears the sound inside a video at 1 kbps mono, and a separate audio file at 16 kbps mono.
- Sends reference/critic.md's reviewer prompt, read at run time, with its "What you have" paragraph
  swapped for this reviewer's, a sound section only a listener can answer, and the brief if it exists.
- Prints the answer (critic.md's shape plus a SOUND block), the tokens and an estimated cost, then deletes
  the uploads, also when something fails on the way. The request is sent with store: false.

--fps: 10 by default, a frame every 0.1 s, so a whip or slam a few frames long is still seen. At high media
resolution a frame measured 258 tokens, so a 60 s film comes to about 160k tokens: about $0.13 on Flash,
and under the 200k-token step where Pro's price doubles, up to a film of about 75 s.
"""

import argparse
import json
import mimetypes
import os
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

API = "https://generativelanguage.googleapis.com"
CRITIC = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, "reference", "critic.md")
# USD per 1M tokens, standard tier (ai.google.dev/gemini-api/docs/pricing, Sept 2026): input, output with
# thinking, then both again for prompts over 200k tokens. Flash's rates double on 1 Jan 2027.
PRICES = {"gemini-3.8-flash": (0.75, 3.75, 0.75, 3.75), "gemini-3.1-pro-preview": (2.0, 12.0, 4.0, 18.0)}

HAVE = "**What you have.** The film itself, as a viewer meets it: the video with its sound{audio}. The video's first frame is the cover."
AUDIO = (", then the same soundtrack again as an audio file. The audio file is the video's own sound on the same clock from 0 s,"
         " heard in more detail than the copy inside the video: listen to it for words, music and hits, and look at the video"
         " for what is on screen at each moment")
SOUND = """You also hear the film, so judge its sound as a viewer hears it. You hear a reduced copy, so say what should be louder or quieter, never by how many dB. Give every time in your answer in seconds with one decimal (6.5 s, not 0:06). Listen for these:
- **Words.** A word that is hard to make out, and what buries it.
- **Music against the voice.** Music that fights the voice for attention instead of carrying it.
- **Hits against the picture.** A hit, stamp or drop that lands before or after the move it belongs to, and by about how much.
- **Pauses.** A pause or silence that reads as lag rather than a held breath.
- **The peak.** Whether the peak is the biggest moment in sound and picture together, or only in one of them.
- **Cuts.** Sound that starts, stops or jumps abruptly at a cut.
- **Harshness.** Clipping, distortion, or a harsh or piercing sound.

Then add this block after KEEP, most serious first:

```
SOUND:
1. [high|medium|low] <time or range, e.g. 6.0-7.5 s> <what you hear, and what is on screen then> -> <a concrete fix>
2. ...
```"""


def request(method, url, data=None, headers=None):
    """One API call: the response headers and its JSON body. Raises on an HTTP error."""
    req = urllib.request.Request(url, data=data, method=method, headers={"x-goog-api-key": os.environ["GEMINI_API_KEY"], **(headers or {})})
    with urllib.request.urlopen(req, timeout=600) as response:
        return response.headers, json.loads(response.read() or "{}")


def reviewer_prompt(with_audio):
    """critic.md's reviewer prompt, told what this reviewer has, plus the sound section."""
    text = open(CRITIC).read().split("\n---\n", 1)[1].strip()
    pack = next((p for p in text.split("\n\n") if p.startswith("**What you have.**")), None)
    if pack is None:
        sys.exit(f"{CRITIC}: the reviewer prompt has no **What you have.** paragraph to swap")
    return text.replace(pack, HAVE.format(audio=AUDIO if with_audio else "")) + "\n\n" + SOUND


def soundtrack(video, folder):
    """The film's own sound as a lossless file, so the only reduction is the API's."""
    out = os.path.join(folder, os.path.splitext(os.path.basename(video))[0] + ".flac")
    run = subprocess.run(["ffmpeg", "-v", "error", "-i", video, "-vn", "-c:a", "flac", out], capture_output=True, text=True)
    if run.returncode:
        sys.exit(f"{video}: no soundtrack to extract ({run.stderr.strip()}). For a muted film, pass --no-audio-file.")
    return out


def upload(path, mime):
    """Resumable upload to the Files API. Returns the file, which may still be PROCESSING."""
    print(f"uploading {os.path.basename(path)} ({os.path.getsize(path) / 1e6:.1f} MB)", file=sys.stderr)
    start = json.dumps({"file": {"display_name": os.path.basename(path)}}).encode()
    headers, _ = request("POST", f"{API}/upload/v1beta/files", start, {
        "content-type": "application/json", "x-goog-upload-protocol": "resumable", "x-goog-upload-command": "start",
        "x-goog-upload-header-content-length": str(os.path.getsize(path)), "x-goog-upload-header-content-type": mime})
    with open(path, "rb") as handle:
        _, body = request("POST", headers["x-goog-upload-url"], handle.read(),
                          {"x-goog-upload-offset": "0", "x-goog-upload-command": "upload, finalize"})
    return body["file"]


def active(file):
    while file["state"] == "PROCESSING":
        time.sleep(2)
        _, file = request("GET", f"{API}/v1beta/{file['name']}")
    if file["state"] != "ACTIVE":
        sys.exit(f"Google could not process {file['displayName']}: {file.get('error', file['state'])}")
    return file


def delete(file):
    try:
        request("DELETE", f"{API}/v1beta/{file['name']}")
        print(f"deleted {file['displayName']} from Google's Files API", file=sys.stderr)
    except urllib.error.URLError as error:  # keep going: the other upload still needs deleting
        print(f"could not delete {file['name']} ({error}); Google removes it at {file.get('expirationTime')}", file=sys.stderr)


def review(model, fps, files, brief, prompt):
    video, *audio = files
    parts = [{"type": "video", "uri": video["uri"], "mime_type": video["mimeType"], "resolution": "high",
              "processing": {"type": "static", "fps": fps}}]
    parts += [{"type": "audio", "uri": a["uri"], "mime_type": a["mimeType"]} for a in audio]
    if brief:
        parts.append({"type": "text", "text": "The brief:\n\n" + brief})
    parts.append({"type": "text", "text": prompt})
    print(f"reviewing with {model} at {fps:g} fps", file=sys.stderr)
    _, result = request("POST", f"{API}/v1beta/interactions", json.dumps({"model": model, "input": parts, "store": False}).encode(),
                        {"content-type": "application/json"})
    text = "\n".join(c["text"] for s in result.get("steps", []) if s.get("type") == "model_output"
                     for c in s.get("content", []) if c.get("type") == "text")
    if result.get("status") != "completed" or not text:
        sys.exit(f"Gemini returned no review (status {result.get('status')}):\n{json.dumps(result)[:2000]}")
    return text, result.get("usage", {})


def cost(model, usage):
    """The tokens used and an estimated price from PRICES."""
    tokens_in, thought, answer = (usage.get(k, 0) for k in ("total_input_tokens", "total_thought_tokens", "total_output_tokens"))
    modalities = ", ".join(f"{m['modality']} {m['tokens']}" for m in usage.get("input_tokens_by_modality", []))
    line = f"tokens: {tokens_in} in ({modalities}), {thought} thinking, {answer} answer"
    if model not in PRICES:
        return line + f" | no price for {model} in watch.py PRICES"
    rate_in, rate_out = PRICES[model][2:] if tokens_in > 200_000 else PRICES[model][:2]
    return line + f" | about ${(tokens_in * rate_in + (thought + answer) * rate_out) / 1e6:.3f}"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("video")
    p.add_argument("--brief", default="film-prompt.md")
    p.add_argument("--fps", type=float, default=10)
    p.add_argument("--model", default="gemini-3.8-flash")
    p.add_argument("--no-audio-file", action="store_true", help="send only the video, whose sound the API hears at 1 kbps")
    args = p.parse_args()
    if not os.environ.get("GEMINI_API_KEY"):
        sys.exit("GEMINI_API_KEY is not set. Export it in ~/.zshenv or ~/.profile, which non-interactive shells read, and retry.")

    prompt = reviewer_prompt(not args.no_audio_file)
    brief = open(args.brief).read() if os.path.exists(args.brief) else None
    files = []
    with tempfile.TemporaryDirectory() as folder:
        media = [(args.video, mimetypes.guess_type(args.video)[0])]
        if not args.no_audio_file:
            media.append((soundtrack(args.video, folder), "audio/flac"))
        try:
            for path, mime in media:
                files.append(upload(path, mime))
            files = [active(f) for f in files]
            text, usage = review(args.model, args.fps, files, brief, prompt)
            print(text)
            print()
            print(cost(args.model, usage))
        except urllib.error.HTTPError as error:
            sys.exit(f"Gemini {error.url.split('?')[0]}: HTTP {error.code}\n{error.read().decode(errors='replace')[:2000]}")
        finally:
            for file in files:
                delete(file)


if __name__ == "__main__":
    main()
