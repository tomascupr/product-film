"""Fetch a partner's official brand kit from Brandfetch: logos (SVG first), colors and fonts.

    python3 brandfetch.py anthropic.com [--out img/brands] [--force]

Needs BRANDFETCH_API_KEY (free at brandfetch.com/developers; the free plan has 100 brand fetches
in total, so results are cached and a domain is fetched once unless --force). Standard library only.

Writes <out>/<domain>/:
  brand.json                    the API response, kept as the cache
  <type>-<theme>.<ext>          every logo: type is logo, symbol or icon; the file is the SVG when
                                there is one, else the largest PNG or JPEG
  kit.txt                       colors (hex, role), fonts (name, role, origin) and the files, for BRAND.md

Brandfetch's "theme" names the mark's own color, not the background: "dark" is a dark mark for
light backgrounds, "light" a light mark for dark backgrounds. kit.txt prints each SVG's fills so
nobody has to guess.
A font with origin "custom" is the owner's own typeface and cannot be downloaded here; use their
files if they share them, otherwise leave the partner's words in its logo and set the rest in the
product's type.
"""

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request

API = "https://api.brandfetch.io/v2/brands/domain/"


def get(url, key=None):
    headers = {"User-Agent": "product-film"}
    if key:
        headers["Authorization"] = f"Bearer {key}"
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=60) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("domain")
    p.add_argument("--out", default="img/brands")
    p.add_argument("--force", action="store_true", help="fetch again even if cached (costs a credit)")
    args = p.parse_args()

    folder = os.path.join(args.out, args.domain)
    cache = os.path.join(folder, "brand.json")
    os.makedirs(folder, exist_ok=True)
    if os.path.exists(cache) and not args.force:
        brand = json.load(open(cache))
        print(f"{args.domain}: cached ({cache}), no credit used")
    else:
        key = os.environ.get("BRANDFETCH_API_KEY")
        if not key:
            sys.exit("BRANDFETCH_API_KEY is not set. Get a free key at brandfetch.com/developers.")
        status, body = get(API + args.domain, key)
        if status == 204:
            sys.exit(f"{args.domain}: Brandfetch has not indexed this brand yet (204). Use the partner's press kit.")
        if status != 200:
            sys.exit(f"{args.domain}: Brandfetch returned {status}: {body[:200]!r}")
        brand = json.loads(body)
        open(cache, "w").write(json.dumps(brand, indent=1))

    files = []
    for logo in brand.get("logos", []):
        formats = logo.get("formats", [])
        pick = next((f for f in formats if f.get("format") == "svg"), None) or max(
            (f for f in formats if f.get("format") in ("png", "jpeg")), key=lambda f: f.get("width") or 0, default=None)
        if not pick:
            continue
        ext = "jpg" if pick["format"] == "jpeg" else pick["format"]
        name = os.path.join(folder, f"{logo.get('type')}-{logo.get('theme') or 'any'}.{ext}")
        if not os.path.exists(name) or args.force:
            status, body = get(pick["src"])
            if status != 200:
                print(f"  could not download {name}: {status}", file=sys.stderr)
                continue
            open(name, "wb").write(body)
        files.append(name)

    lines = [f"{brand.get('name')} ({args.domain}), from Brandfetch"]
    lines += [f"color {c.get('hex')}  {c.get('type')}" for c in brand.get("colors", [])]
    lines += [f"font  {f.get('name')}  {f.get('type')}  ({f.get('origin')})" for f in brand.get("fonts", [])]
    def fills(path):
        if not path.endswith(".svg"):
            return ""
        found = sorted(set(re.findall(r'fill[:=]\s*"?(#[0-9A-Fa-f]{3,8})', open(path, errors="ignore").read())))
        return "  fills " + " ".join(found) if found else ""
    lines += [f"file  {f}{fills(f)}" for f in files]
    open(os.path.join(folder, "kit.txt"), "w").write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
