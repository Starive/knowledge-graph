"""Fetch one photo per built case from Wikimedia Commons.

Reads photos/sources.json. Each entry is either
  {"file": "<Commons file name>", "from": "Miro board card"}   - the photo already chosen on the Miro board
  {"search": "<Commons search>",  "from": "Wikimedia Commons search"} - the first suitable search result
Writes photos/<case>.jpg|png, photos/manifest.json (read by index.html) and CREDITS.md.
Standard library only, so it runs on a bare GitHub Actions runner.
"""
import json
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PHOTOS = ROOT / "photos"
API = "https://commons.wikimedia.org/w/api.php"
UA = "knowledge-graph-photo-fetch/1.0 (https://github.com/Starive/knowledge-graph)"
WIDTH = 640


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code in (429, 503) and attempt < 3:
                time.sleep(5 * (attempt + 1))
                continue
            raise


def api(params):
    params = dict(params, format="json", formatversion="2")
    return json.loads(get(API + "?" + urllib.parse.urlencode(params)))


def plain(html):
    text = re.sub(r"<[^>]+>", "", html or "")
    return re.sub(r"\s+", " ", text).strip()


def slug(name):
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


IIPROP = {"prop": "imageinfo", "iiprop": "url|extmetadata|mime|size", "iiurlwidth": str(WIDTH)}


def by_file(name):
    names = [name]
    stem, dot, ext = name.rpartition(".")
    if dot:
        names += [f"{stem}.{ext.upper()}", f"{stem}.{ext.lower()}", f"{stem}.jpeg", f"{stem}.JPEG"]
    for n in dict.fromkeys(names):
        pages = api(dict(IIPROP, action="query", titles="File:" + n))["query"].get("pages", [])
        if pages and not pages[0].get("missing") and pages[0].get("imageinfo"):
            return pages[0]
    return None


CANDIDATES = {}


def by_search(query, case):
    d = api(dict(IIPROP, action="query", generator="search", gsrsearch=query + " filetype:bitmap",
                 gsrnamespace="6", gsrlimit="12"))
    pages = sorted(d.get("query", {}).get("pages", []), key=lambda p: p.get("index", 99))
    CANDIDATES[case] = [{"file": p["title"], "width": (p.get("imageinfo") or [{}])[0].get("width", 0)} for p in pages]
    for p in pages:
        ii = (p.get("imageinfo") or [{}])[0]
        if ii.get("mime") in ("image/jpeg", "image/png") and ii.get("width", 0) >= 800:
            return p
    return None


def main():
    sources = json.loads((PHOTOS / "sources.json").read_text(encoding="utf-8"))
    manifest, missing = {}, []
    for old in PHOTOS.glob("*"):
        if old.suffix.lower() in (".jpg", ".png"):
            old.unlink()
    for case, spec in sources.items():
        try:
            page = by_file(spec["file"]) if spec.get("file") else None
            if not page and spec.get("search"):
                page = by_search(spec["search"], case)
            if not page:
                missing.append(case)
                print(f"no photo: {case}")
                continue
            ii = page["imageinfo"][0]
            md = ii.get("extmetadata", {})
            ext = ".png" if ii["mime"] == "image/png" else ".jpg"
            path = f"photos/{slug(case)}{ext}"
            (ROOT / path).write_bytes(get(ii.get("thumburl") or ii["url"]))
            manifest[case] = {
                "path": path,
                "file": page["title"],
                "page": ii.get("descriptionurl", ""),
                "author": plain(md.get("Artist", {}).get("value"))[:160],
                "license": plain(md.get("LicenseShortName", {}).get("value")),
                "licenseUrl": md.get("LicenseUrl", {}).get("value", ""),
                "from": spec.get("from", "") if not (spec.get("file") and page["title"].replace("File:", "").replace(" ", "_") != spec["file"].replace(" ", "_")) or not spec.get("search") else "Wikimedia Commons search",
            }
            print(f"ok: {case} <- {page['title']}")
        except Exception as e:  # keep going; report at the end
            missing.append(case)
            print(f"failed: {case}: {e}", file=sys.stderr)
        time.sleep(0.4)

    (PHOTOS / "candidates.json").write_text(json.dumps(CANDIDATES, ensure_ascii=False, indent=1), encoding="utf-8")
    (PHOTOS / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    lines = ["# Photo credits", "",
             "Each built-case photo in the graph, where it came from and its licence. "
             "Photos marked *Miro board card* are the ones chosen on the project's Miro board; "
             "*Wikimedia Commons search* marks a photo picked automatically for a case the board had none for, "
             "and these should be checked.", "",
             "| Case | Photo | Author | Licence | Chosen from |", "|---|---|---|---|---|"]
    for case in sorted(manifest):
        m = manifest[case]
        title = m["file"].replace("File:", "").replace("|", "\\|")
        lines.append(f"| {case} | [{title}]({m['page']}) | {m['author'].replace('|', '/') or 'not stated'} | "
                     f"{m['license'] or 'not stated'} | {m['from']} |")
    if missing:
        lines += ["", "## No photo found", ""] + [f"- {c}" for c in missing]
    (ROOT / "CREDITS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\n{len(manifest)} photos, {len(missing)} missing")


if __name__ == "__main__":
    main()
