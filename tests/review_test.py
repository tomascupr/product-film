"""critic.py's pack, and watch.py's prompt and saved review. Offline: a synthetic video, and the watcher's network calls stubbed.

    uv run --with numpy --with imageio-ffmpeg python3 tests/review_test.py
"""
import json
import os
import subprocess
import sys
import tempfile

import imageio_ffmpeg

SCRIPTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts")
sys.path.insert(0, SCRIPTS)
import watch  # noqa: E402

os.chdir(tempfile.mkdtemp())
subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-v", "error", "-f", "lavfi", "-i", "testsrc=size=320x180:rate=30:duration=3",
                "-f", "lavfi", "-i", "sine=duration=3", "-shortest", "-pix_fmt", "yuv420p", "film.mp4"], check=True)

# critic.py: a strip of fast frames around every cue inside the film, one strip where two cues share a time
json.dump({"cues": {"hit": 1.0, "drop": 2.0, "stop": 2.0, "late": 9.0}}, open("film.json", "w"))
run = subprocess.run([sys.executable, os.path.join(SCRIPTS, "critic.py"), "film.mp4"], capture_output=True, text=True)
assert run.returncode == 0, run.stderr
pack = os.path.join("out", "critic", "film")
assert sorted(f for f in os.listdir(pack) if f.startswith("cue-")) == ["cue-drop+stop.png", "cue-hit.png"], os.listdir(pack)
assert "cue-hit.png: 10 frames 0.1 s apart from 0.70 s" in open(os.path.join(pack, "README.txt")).read()

# watch.py: critic.md's prompt with the watcher's own "What you have" paragraph and the sound section
prompt = watch.reviewer_prompt(True)
assert "The film itself, as a viewer meets it" in prompt and "A folder packed from the film" not in prompt, prompt
assert all(part in prompt for part in ("VERDICT:", "SAID BACK:", "FINDINGS:", "KEEP:", "SOUND:")), prompt

# and its review saved under out/watch, away from the critic's pack
os.environ["GEMINI_API_KEY"] = "offline"
watch.upload = lambda path, mime: {"name": path, "displayName": path, "state": "ACTIVE", "uri": path, "mimeType": mime}
watch.delete = lambda file: None
watch.review = lambda *args: ("VERDICT: fine", {})
sys.argv = ["watch.py", "film.mp4"]
watch.main()
assert open(os.path.join("out", "watch", "film.txt")).read().startswith("VERDICT: fine")
print("review_test: ok")
