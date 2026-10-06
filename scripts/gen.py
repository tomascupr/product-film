"""Generated footage for product films: a clip from fal.ai as an image sequence that kit.js
footage() plays frame-exact on the film's clock.

Run from the film folder. `video` needs FAL_KEY; both commands need ffmpeg and ffprobe on PATH.
Standard library only.

    python3 gen.py video --prompt "..." --first footage/in/000.png --last footage/in/001.png --seconds 4 --out footage/<name>
    python3 gen.py video --prompt "..." --model fal-ai/kling-video/v3/standard/text-to-video --seconds 8 --arg aspect_ratio=1:1 --out footage/<name>
    python3 gen.py frames clip.mp4 --out footage/<name>          an MP4 from anywhere else, as frames

--first and --last are the film's own stills (`node film.mjs stills` at the handoff times), so the
shot starts or ends on a coded frame. Local files go up as data URIs. --model takes any fal endpoint
id; --arg key=value adds or overrides a request field (JSON when it parses, a local file becomes a
data URI). Audio is off on the endpoints gen.py maps: the frames drop it, and it costs extra.
<out>/ gets clip.mp4, 0001.jpg... and clip.json {fps, frames, seconds, size, ext, model, prompt, request_id}.
`video` will not generate into a folder that has a clip.json (it costs money again); --force does.
"""

import argparse
import base64
import json
import mimetypes
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request

QUEUE = "https://queue.fal.run/"
# What --first, --last and --seconds are called on each endpoint (its API page on fal.ai).
FIELDS = {
    "fal-ai/kling-video/v3/standard/image-to-video": ("start_image_url", "end_image_url", "{}"),
    "fal-ai/kling-video/v3/pro/image-to-video": ("start_image_url", "end_image_url", "{}"),
    "fal-ai/veo3.1/fast/first-last-frame-to-video": ("first_frame_url", "last_frame_url", "{}s"),
    "fal-ai/veo3.1/first-last-frame-to-video": ("first_frame_url", "last_frame_url", "{}s"),
    "fal-ai/kling-video/v3/standard/text-to-video": (None, None, "{}"),   # no stills: the prompt makes the shot
}


def data_uri(path):
    kind = mimetypes.guess_type(path)[0] or "application/octet-stream"
    return f"data:{kind};base64,{base64.b64encode(open(path, 'rb').read()).decode()}"


def value(text):
    """An --arg value: a local file as a data URI, else JSON when it parses, else the text."""
    if os.path.isfile(text):
        return data_uri(text)
    try:
        return json.loads(text)
    except ValueError:
        return text


def fal(url, body=None):
    key = os.environ.get("FAL_KEY")
    if not key:
        sys.exit("FAL_KEY is not set. Export it in ~/.zshenv or ~/.profile, which non-interactive shells read, and retry.")
    request = urllib.request.Request(url, data=None if body is None else json.dumps(body).encode(),
                                     headers={"Authorization": f"Key {key}", "Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=120) as response:
        return json.loads(response.read())


def extract(mp4, out):
    """Every frame of an MP4 as a JPEG in `out`, and the numbers clip.json needs."""
    probe = json.loads(subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_frames", "-of", "json",
         "-show_entries", "stream=width,height,avg_frame_rate,nb_read_frames,color_space,color_range", mp4],
        capture_output=True, text=True, check=True).stdout)["streams"][0]
    # Decode with the clip's own matrix and range, BT.709 limited when untagged: ffmpeg reads an
    # untagged clip as BT.601 and shifts its colors. JPEG stores BT.601 full range, as browsers expect.
    matrix = {"smpte170m": "smpte170m", "bt470bg": "bt470"}.get(probe.get("color_space"), "bt709")
    limits = "pc" if probe.get("color_range") == "pc" else "tv"
    # JPEG at q 2 with full chroma: the clip is already lossy 4:2:0, and PNG measured 2 to 20 times larger.
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", mp4, "-fps_mode", "passthrough", "-vf",
                    f"scale=in_color_matrix={matrix}:in_range={limits}:out_color_matrix=bt601:out_range=pc,format=yuv444p",
                    "-q:v", "2", os.path.join(out, "%04d.jpg")], check=True)
    num, den = map(int, probe["avg_frame_rate"].split("/"))
    frames = int(probe["nb_read_frames"])
    return {"fps": num / den, "frames": frames, "seconds": round(frames * den / num, 3),
            "size": [probe["width"], probe["height"]], "ext": "jpg"}


def save(out, info):
    with open(os.path.join(out, "clip.json"), "w") as handle:
        json.dump(info, handle, indent=1)
    print(f"{out}: {info['frames']} frames at {info['fps']:g} fps ({info['seconds']} s), {info['size'][0]}x{info['size'][1]}")


def video(args):
    if os.path.exists(os.path.join(args.out, "clip.json")) and not args.force:
        sys.exit(f"{args.out} already has a clip. --force generates a new one, and pays for it again.")
    body = {"prompt": args.prompt}
    if args.model in FIELDS:
        first, last, duration = FIELDS[args.model]
        still = lambda path: path if path.startswith(("http://", "https://")) else data_uri(path)
        body["generate_audio"] = False
        for given, field in ((args.first, first), (args.last, last)):
            if given and not field:
                sys.exit(f"{args.model} takes no stills: use an image-to-video endpoint for --first and --last")
            if given:
                body[field] = still(given)
        if args.seconds:
            body["duration"] = duration.format(args.seconds)
    elif args.first or args.last or args.seconds:
        sys.exit(f"--first, --last and --seconds are mapped for {', '.join(FIELDS)}. "
                 f"Pass {args.model}'s own fields with --arg (its API page on fal.ai lists them).")
    for pair in args.arg:
        key, _, text = pair.partition("=")
        body[key] = value(text)
    os.makedirs(args.out, exist_ok=True)
    try:
        job = fal(QUEUE + args.model, body)
    except urllib.error.HTTPError as error:
        sys.exit(f"fal {args.model}: HTTP {error.code}\n{error.read().decode(errors='replace')[:2000]}")
    print(f"{args.model}: request {job['request_id']}", flush=True)
    # Poll the URLs the queue returned: they stay right for endpoint ids with a subpath.
    started, state, misses = time.time(), None, 0
    while state != "COMPLETED":
        time.sleep(5)
        try:
            status = fal(job["status_url"])
        except (urllib.error.URLError, TimeoutError) as error:
            misses += 1
            if misses == 5:
                sys.exit(f"fal: 5 status checks failed ({error}). The clip may still finish: {job['response_url']}")
            continue
        misses = 0
        if status["status"] != state:
            state = status["status"]
            print(f"  {state.lower().replace('_', ' ')} at {time.time() - started:.0f} s", flush=True)
    try:
        result = fal(job["response_url"])
    except urllib.error.HTTPError as error:
        sys.exit(f"fal {args.model}: the request failed, HTTP {error.code}\n{error.read().decode(errors='replace')[:2000]}")
    mp4 = os.path.join(args.out, "clip.mp4")
    with urllib.request.urlopen(result["video"]["url"], timeout=600) as response, open(mp4, "wb") as handle:
        handle.write(response.read())
    save(args.out, {**extract(mp4, args.out), "model": args.model, "prompt": args.prompt, "request_id": job["request_id"]})


def frames(args):
    os.makedirs(args.out, exist_ok=True)
    save(args.out, extract(args.mp4, args.out))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)
    p = commands.add_parser("video")
    p.add_argument("--prompt", required=True)
    p.add_argument("--first", help="the film's still the shot starts on (a file or URL)")
    p.add_argument("--last", help="the film's still the shot ends on")
    p.add_argument("--seconds", type=int)
    p.add_argument("--model", default="fal-ai/kling-video/v3/standard/image-to-video")
    p.add_argument("--arg", action="append", default=[], metavar="KEY=VALUE")
    p.add_argument("--out", required=True)
    p.add_argument("--force", action="store_true")
    p.set_defaults(run=video)
    p = commands.add_parser("frames")
    p.add_argument("mp4")
    p.add_argument("--out", required=True)
    p.set_defaults(run=frames)
    args = parser.parse_args()
    args.run(args)


if __name__ == "__main__":
    main()
