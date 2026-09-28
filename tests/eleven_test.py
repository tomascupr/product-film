"""eleven.py offline: alignment to words, and tts keeping a recorded take. Run: python3 tests/eleven_test.py"""
import base64
import json
import os
import sys
import tempfile
from types import SimpleNamespace

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
import eleven  # noqa: E402


def timed(text):
    """One character every 0.1 s, the shape both alignments come in."""
    return [(c, i / 10, (i + 1) / 10) for i, c in enumerate(text)]


# tags are not words, a run of spaces splits once, punctuation stays on its word
words = eleven.words_from(timed("[whispers] Keep  it, [laughs]okay?"))
assert [w["w"] for w in words] == ["Keep", "it,", "okay?"], words
assert (words[0]["start"], words[0]["end"]) == (1.1, 1.5), words[0]
assert eleven.spoken("[whispers] Keep  it, [laughs]okay?") == "Keep it, okay?"

os.chdir(tempfile.mkdtemp())
os.makedirs("audio/vo")
text = "[sighs] Go live now"
json.dump({"voice": {"voice_id": "v", "model_id": "eleven_multilingual_v2", "lines": [{"id": "a", "text": text}],
                     "pronounce": [{"word": "live", "ipa": "laɪv"}, {"word": "now", "alias": "naow"}]}}, open("film.json", "w"))
recorded = {"text": text, "voice_id": None, "model_id": None, "source": "recorded", "duration": 0, "words": []}
json.dump(recorded, open("audio/vo/a.json", "w"))
sent = []


def fake(method, path, body=None, raw=False, **_):
    sent.append(body)
    if "pronunciation" in path:
        return {"id": "d", "version_id": "1"}
    chars, starts, ends = zip(*timed(text))
    return {"audio_base64": base64.b64encode(b"mp3").decode(),
            "alignment": {"characters": chars, "character_start_times_seconds": starts, "character_end_times_seconds": ends}}


eleven.call = fake
eleven.tts(SimpleNamespace(only=None, force=False))
assert not sent and json.load(open("audio/vo/a.json")) == recorded, "tts replaced a recorded take"
eleven.tts(SimpleNamespace(only=None, force=True))
assert [r["type"] for r in sent[0]["rules"]] == ["alias"], "an ipa rule reached a model that drops the word"
assert sent[1]["pronunciation_dictionary_locators"] == [{"pronunciation_dictionary_id": "d", "version_id": "1"}]
meta = json.load(open("audio/vo/a.json"))
assert [w["w"] for w in meta["words"]] == ["Go", "live", "now"] and "source" not in meta, meta
eleven.tts(SimpleNamespace(only=None, force=False))
assert len(sent) == 2, "an unchanged line was generated again"
print("eleven_test: ok")
