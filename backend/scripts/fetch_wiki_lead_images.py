"""
Give every real destination a REAL photo of the actual place.

Each destination is an Indonesian Wikipedia article. This script pulls each
article's lead image (pageimages -> pageimage) from id.wikipedia.org, which by
construction is a photo of the real place. The reliable Wikidata P18 primary
(Special:FilePath URLs already present in the images column) is kept as a second
real photo when it differs.

Titles are queried in batches of up to 50 per request so the whole run only
needs ~40 HTTP calls and stays well within Wikipedia's rate limits. Results are
also cached to app/ml/data/real_lead_images.json for inspection.

Usage:
    python scripts/fetch_wiki_lead_images.py [--input app/ml/data/real_destinations.csv]
"""
import argparse
import csv
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

MAX_IMAGES = 4
TITLES_PER_QUERY = 50
API = "https://id.wikipedia.org/w/api.php"

# Commons filenames that are never a photo of the place.
BAD_LEAD = re.compile(
    r"(location_map|relief|map|peta|locator|diagram|layout|sketch|denah|lambang|"
    r"seal|emblem|flag|coat of arms|insignia|logo|icon|collage|stub|blank|"
    r"topography|topografi|terrain|modis|landsat|satellite|iss0\d|sts-\d+\.|"
    r"orthophoto|aerial view of the map|geomorph)", re.IGNORECASE)
# NASA MODIS/VIIRS naming, e.g. "Timor.A2002179.0205.500m.jpg"
BAD_SATELLITE = re.compile(r"\.a\d{7}\.", re.IGNORECASE)


def basename(url: str) -> str:
    seg = url.split("?")[0].rsplit("/", 1)[-1]
    seg = urllib.parse.unquote(seg)
    return re.sub(r"^\d+px-", "", seg).lower()


def is_photo(url: str) -> bool:
    return bool(url) and basename(url).endswith((".jpg", ".jpeg", ".png")) \
        and not BAD_LEAD.search(basename(url)) and not BAD_SATELLITE.search(basename(url))


def api_get(params: dict, retries: int = 4) -> dict:
    params = dict(params)
    params["format"] = "json"
    url = API + "?" + urllib.parse.urlencode(params)
    for attempt in range(retries):
        req = urllib.request.Request(url, headers={
            "User-Agent": "BerWisataDev/1.0 (local dev seed; contact: none)",
            "Accept": "application/json",
        })
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.load(resp)
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 503, 504):
                time.sleep(3 * (attempt + 1))
                continue
            raise
        except Exception:
            time.sleep(3 * (attempt + 1))
            continue
    return {}


def wiki_leads(titles: list[str]) -> dict[str, str]:
    """title -> lead image URL ('' if the article has no lead image)."""
    out: dict[str, str] = {t: "" for t in titles}
    for i in range(0, len(titles), TITLES_PER_QUERY):
        chunk = titles[i:i + TITLES_PER_QUERY]
        data = api_get({
            "action": "query",
            "prop": "pageimages",
            "piprop": "thumbnail",
            "pithumbsize": "800",
            "redirects": "1",
            "titles": "|".join(chunk),
        })
        q = data.get("query") or {}
        pages = {p.get("title"): p for p in (q.get("pages") or {}).values()}
        nxt = {}
        for lst in (q.get("normalized", []), q.get("redirects", [])):
            for r in lst:
                nxt[r.get("from")] = r.get("to")
        for t in chunk:
            cur = t
            seen = 0
            while cur in nxt and seen < 5:
                cur = nxt[cur]
                seen += 1
            img = ((pages.get(cur) or {}).get("thumbnail") or {}).get("source") or ""
            if img and is_photo(img):
                out[t] = img
        time.sleep(0.5)
    return out


def is_p18(url: str) -> bool:
    return "Special:FilePath" in url


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch Wikipedia lead images for real destinations")
    parser.add_argument("--input", default="app/ml/data/real_destinations.csv")
    parser.add_argument("--cache", default="app/ml/data/real_lead_images.json")
    args = parser.parse_args()

    csv_path = Path(args.input)
    cache_path = Path(args.cache)

    with csv_path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    names = [r["name"] for r in rows]
    print(f"Rows: {len(rows)}", flush=True)
    cache = wiki_leads(names)
    with cache_path.open("w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False)

    with_lead = sum(1 for v in cache.values() if v)
    print(f"Lead image coverage: {with_lead}/{len(rows)}", flush=True)

    # Rebuild each row's images: [lead] + [p18], generator pads the rest.
    for r in rows:
        existing = [u for u in (r.get("images") or "").split("|") if u]
        real = []
        lead = cache.get(r["name"], "")
        if lead:
            real.append(lead)
        for u in existing:
            if is_p18(u) and is_photo(u) and u != lead and len(real) < MAX_IMAGES:
                real.append(u)
        r["images"] = "|".join(real)
        r["qid"] = r.get("qid", "")

    fieldnames = ["name", "category", "province", "regency", "latitude", "longitude", "qid", "images"]
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    total = sum(1 for r in rows if r["images"])
    all_imgs = sum(len(r["images"].split("|")) for r in rows if r["images"])
    print(f"Rows with real photos: {total}/{len(rows)}; total real photos: {all_imgs}", flush=True)


if __name__ == "__main__":
    main()
