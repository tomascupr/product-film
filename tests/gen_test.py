"""gen.py offline: the image request and what it writes, and the Seedance fields. Run: python3 tests/gen_test.py"""
import base64
import io
import json
import os
import subprocess
import sys
import tempfile
from types import SimpleNamespace

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
import gen  # noqa: E402

os.chdir(tempfile.mkdtemp())
subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "color=c=0xffd400:s=32x18", "-frames:v", "1", "still.png"], check=True)
png = open("still.png", "rb").read()
os.environ["GEMINI_API_KEY"] = "test"
sent, reply = [], {}


def fake_urlopen(request, timeout=None):
    sent.append(json.loads(request.data))
    return io.BytesIO(json.dumps(reply).encode())


gen.urllib.request.urlopen = fake_urlopen


def args(**over):
    return SimpleNamespace(**{"prompt": "the same office at night", "ref": ["still.png"], "aspect": "16:9", "size": "2K",
                              "thinking": None, "model": "gemini-nano-banana-2.1", "out": "img/night.png", "force": False, **over})


reply = {"steps": [{"type": "model_output", "content": [{"type": "text", "text": "Here it is."},
                                                        {"type": "image", "mime_type": "image/png", "data": base64.b64encode(png).decode()}]}]}
gen.image(args())
body = sent[-1]
assert body["model"] == "gemini-nano-banana-2.1" and body["store"] is False, body
assert body["input"][0] == {"type": "image", "mime_type": "image/png", "data": base64.b64encode(png).decode()}, "the reference goes first"
assert body["input"][-1] == {"type": "text", "text": "the same office at night"}
assert body["response_format"] == {"type": "image", "image_size": "2K", "aspect_ratio": "16:9"}, "a PNG request names no mime_type, which the API refuses"
assert "generation_config" not in body
assert open("img/night.png", "rb").read() == png
assert json.load(open("img/night.json")) == {"model": "gemini-nano-banana-2.1", "prompt": "the same office at night",
                                             "ref": ["still.png"], "aspect": "16:9", "size": "2K"}

try:
    gen.image(args())
    raise AssertionError("an existing still was paid for again")
except SystemExit as stop:
    assert "--force" in str(stop)
assert len(sent) == 1

# The API answers in JPEG whatever it is asked; a .png still has to be a PNG
subprocess.run(["ffmpeg", "-v", "error", "-i", "still.png", "still.jpg"], check=True)
reply = {"steps": [{"type": "model_output", "content": [{"type": "image", "mime_type": "image/jpeg",
                                                         "data": base64.b64encode(open("still.jpg", "rb").read()).decode()}]}]}
gen.image(args(out="img/converted.png"))
assert open("img/converted.png", "rb").read().startswith(b"\x89PNG"), "JPEG bytes saved under a .png name"

gen.image(args(out="img/night.jpg", ref=[], aspect=None, thinking="high"))
body = sent[-1]
assert body["response_format"] == {"type": "image", "image_size": "2K", "mime_type": "image/jpeg"}, body["response_format"]
assert body["generation_config"] == {"thinking_level": "high"} and len(body["input"]) == 1

reply = {"steps": [{"type": "model_output", "content": [{"type": "text", "text": "I can't make that one."}]}]}
try:
    gen.image(args(out="img/refused.png"))
    raise AssertionError("no image, and no error")
except SystemExit as stop:
    assert "no image" in str(stop) and "can't make that one" in str(stop)
assert not os.path.exists("img/refused.png")

# Seedance takes the two stills as image_url and end_image_url, the length as a string, and no audio
posted = []


def fake_fal(url, body=None):
    posted.append((url, body))
    raise SystemExit("stop after the submit")


gen.fal = fake_fal
try:
    gen.video(SimpleNamespace(prompt="p", first="still.png", last="still.png", seconds=6, model="bytedance/seedance-2.5/image-to-video",
                              arg=[], out="footage/shot", force=False))
except SystemExit:
    pass
url, body = posted[0]
assert url == "https://queue.fal.run/bytedance/seedance-2.5/image-to-video"
assert body["image_url"].startswith("data:image/png;base64,") and body["end_image_url"] == body["image_url"]
assert body["duration"] == "6" and body["generate_audio"] is False, body

print("gen_test: ok")
