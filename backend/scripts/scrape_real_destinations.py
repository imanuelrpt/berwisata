"""
Scrape a large list of real Indonesian tourist destinations from Wikidata.

Each row carries its official Indonesian name, real coordinates (P625) and the
administrative region it belongs to (P131 chain). Only items with an Indonesian
Wikipedia article are kept, so the names are genuinely findable on Google.

Output columns: name, category, province, regency, latitude, longitude, qid, images

The images column carries the Wikidata P18 photo (the item's primary image) as an
800px Wikimedia Commons URL when available. Run scripts/fetch_real_images.py
afterwards to enrich every destination with up to four real Commons photos.

Usage:
    python scripts/scrape_real_destinations.py --output app/ml/data/real_destinations.csv
"""
import argparse
import csv
import json
import math
import re
import sys
import time
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.generate_dataset import CATEGORIES, PROVINCES  # noqa: E402

WDQS = "https://query.wikidata.org/sparql"
HEADERS = {
    "Accept": "application/sparql-results+json",
    "User-Agent": "BerWisataDev/1.0 (local development; contact: none)",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
}

# Types that map straight to a category. Order = specificity: an item with
# several of these instance-of types keeps the most specific category.
TYPE_CATEGORY = [
    ("Q34038", "air-terjun"),  # waterfall
    ("Q40080", "pantai"),      # beach
    ("Q23442", "pulau"),       # island
    ("Q35509", "gua"),         # cave
    ("Q23397", "danau"),       # lake
    ("Q8502", "gunung"),       # mountain
    ("Q44539", "budaya"),      # temple
    ("Q32815", "religi"),      # mosque
    ("Q16560", "budaya"),      # palace
    ("Q46169", "taman"),       # national park
    ("Q33506", "budaya"),      # museum
    ("Q570116", None),         # generic tourist attraction -> keyword fallback
]
TYPE_IDS = " ".join("wd:%s" % qid for qid, _ in TYPE_CATEGORY)

PAGE_SIZE = 500


def item_query(type_qid: str, offset: int, limit: int) -> str:
    """One type + one page at a time keeps each WDQS response small enough to
    avoid the server truncating the JSON stream for big result sets."""
    return f"""
SELECT ?item ?itemLabel ?coord ?loc ?type ?img ?commons WHERE {{
  VALUES ?type {{ wd:{type_qid} }}
  ?item wdt:P31 ?type ;
        wdt:P625 ?coord ;
        wdt:P17 wd:Q252 ;
        wdt:P131 ?loc ;
        rdfs:label ?itemLabel .
  OPTIONAL {{ ?item wdt:P18 ?img . }}
  OPTIONAL {{ ?item wdt:P373 ?commons . }}
  FILTER(LANG(?itemLabel) = "id")
  ?sitelink schema:about ?item ;
             schema:isPartOf <https://id.wikipedia.org/> .
}}
ORDER BY ?item
LIMIT {limit}
OFFSET {offset}
"""

# Prefix-based keyword classification for generic "tourist attraction" items.
KEYWORD_CATEGORY = [
    ("curug ", "curug"),
    ("air terjun ", "air-terjun"),
    ("pantai ", "pantai"),
    ("danau ", "danau"),
    ("telaga ", "danau"),
    ("gunung ", "gunung"),
    ("puncak ", "gunung"),
    ("bukit ", "bukit"),
    ("gua ", "gua"),
    ("goa ", "gua"),
    ("pulau ", "pulau"),
    ("kepulauan ", "pulau"),
    ("taman ", "taman"),
    ("candi ", "budaya"),
    ("pura ", "budaya"),
    ("museum ", "budaya"),
    ("kraton ", "budaya"),
    ("keraton ", "budaya"),
    ("benteng ", "budaya"),
    ("situs ", "budaya"),
    ("masjid ", "religi"),
    ("gereja ", "religi"),
    ("klenteng ", "religi"),
    ("vihara ", "religi"),
    ("makam ", "religi"),
]

REGENCY_NAME = {}
for prov, cfg in PROVINCES.items():
    for r in cfg["regencies"]:
        REGENCY_NAME[r.lower()] = (prov, r)

# Main geographic islands are not tourist destinations, even though Wikidata
# classifies them as "island" (Pulau Jawa, Sumatera, Timor, Papua, ...).
BIG_ISLANDS = {
    "jawa", "sumatera", "sumatra", "kalimantan", "sulawesi", "papua", "timor",
    "flores", "sumbawa", "halmahera", "buru", "seram", "bali", "lombok",
    "bangka", "belitung", "kepulauan maluku", "banggi", "wetar", "yamdena",
    "buton", "muna", "wokam", "seram laut",
}

BOUNDS = {prov: cfg["bbox"] for prov, cfg in PROVINCES.items()}
ANCHORS = {prov: cfg["anchors"]["inland"] + cfg["anchors"]["coastal"] for prov, cfg in PROVINCES.items()}
for prov, lst in ANCHORS.items():
    if not lst:
        lst.extend(PROVINCES[prov]["anchors"]["inland"] or PROVINCES[prov]["anchors"]["coastal"])


def sparql(query: str, retries: int = 5) -> dict:
    body = urllib.parse.urlencode({"query": query}).encode()
    last = None
    for attempt in range(retries):
        req = urllib.request.Request(WDQS, data=body, headers=HEADERS)
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                return json.load(resp)
        except urllib.error.HTTPError as e:
            last = e
            if e.code in (429, 500, 503, 504):
                time.sleep(4 * (attempt + 1))
                continue
            raise
        except Exception as e:  # truncated/odd JSON or network blip -> retry
            last = e
            time.sleep(4 * (attempt + 1))
            continue
    raise last if last else RuntimeError("sparql failed")


def value(binding, key):
    return binding.get(key, {}).get("value")


def p18_url(img_uri: str) -> str:
    """Turn the P18 CommonsMedia URI into an 800px Special:FilePath URL."""
    if not img_uri:
        return ""
    return img_uri.replace("http://commons.wikimedia.org", "https://commons.wikimedia.org") + "?width=800"


def value(binding, key):
    return binding.get(key, {}).get("value")


def parse_coord(wkt: str):
    m = re.match(r"Point\(([-\d.]+) ([-\d.]+)\)", wkt)
    if not m:
        return None
    return float(m.group(2)), float(m.group(1))


def haversine_km(lat1, lon1, lat2, lon2):
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def province_by_coord(lat, lon):
    best = None
    for prov, (lat_min, lat_max, lon_min, lon_max) in BOUNDS.items():
        if lat_min - 0.05 <= lat <= lat_max + 0.05 and lon_min - 0.05 <= lon <= lon_max + 0.05:
            best = prov
            break
    return best


def nearest_anchor_regency(lat, lon, province):
    best, best_d = None, float("inf")
    for a in ANCHORS[province]:
        d = haversine_km(lat, lon, a["lat"], a["lon"])
        if d < best_d:
            best, best_d = a["regency"], d
    return best


def classify(name: str, types: list[str]) -> str:
    for qid, cat in TYPE_CATEGORY:
        if qid in types:
            if cat is None:
                break
            return cat
    lower = name.lower()
    for prefix, cat in KEYWORD_CATEGORY:
        if lower.startswith(prefix):
            return cat
    return None


def fetch_items():
    items = {}
    for type_qid, _ in TYPE_CATEGORY:
        page = 0
        while True:
            data = sparql(item_query(type_qid, page * PAGE_SIZE, PAGE_SIZE))
            bindings = data["results"]["bindings"]
            if not bindings:
                break
            for b in bindings:
                qid = value(b, "item").rsplit("/", 1)[-1]
                coord = parse_coord(value(b, "coord") or "")
                if not coord:
                    continue
                rec = items.setdefault(qid, {
                    "name": value(b, "itemLabel"),
                    "lat": coord[0],
                    "lon": coord[1],
                    "loc": value(b, "loc").rsplit("/", 1)[-1] if value(b, "loc") else None,
                    "loc_name": None,
                    "types": [],
                    "img": value(b, "img"),
                    "commons": value(b, "commons"),
                })
                rec["types"].append(value(b, "type").rsplit("/", 1)[-1])
            if len(bindings) < PAGE_SIZE:
                break
            page += 1
            time.sleep(1)
    return items


def fetch_labels(loc_qids):
    """Map loc qid -> Indonesian label."""
    out = {}
    for i in range(0, len(loc_qids), 400):
        chunk = loc_qids[i:i + 400]
        values = " ".join("wd:%s" % q for q in chunk)
        query = f"""
        SELECT DISTINCT ?loc ?locLabel WHERE {{
          VALUES ?loc {{ {values} }}
          ?loc rdfs:label ?locLabel .
          FILTER(LANG(?locLabel) = "id")
        }}
        """
        data = sparql(query)
        for b in data["results"]["bindings"]:
            loc = value(b, "loc").rsplit("/", 1)[-1]
            out[loc] = value(b, "locLabel")
    return out


def fetch_parents(loc_qids):
    """Map loc qid -> (parent_qid, parent_label) using direct P131."""
    out = {}
    for i in range(0, len(loc_qids), 400):
        chunk = loc_qids[i:i + 400]
        values = " ".join("wd:%s" % q for q in chunk)
        query = f"""
        SELECT DISTINCT ?loc ?parent ?parentLabel WHERE {{
          VALUES ?loc {{ {values} }}
          ?loc wdt:P131 ?parent .
          ?parent rdfs:label ?parentLabel .
          FILTER(LANG(?parentLabel) = "id")
        }}
        """
        data = sparql(query)
        for b in data["results"]["bindings"]:
            loc = value(b, "loc").rsplit("/", 1)[-1]
            parent = value(b, "parent").rsplit("/", 1)[-1]
            out.setdefault(loc, []).append((parent, value(b, "parentLabel")))
    return out


def resolve_regencies(items, loc_labels):
    """Best-effort: regency from P131 chain, else nearest anchor in the province."""
    for qid, it in items.items():
        if it["loc"] and it["loc"] in loc_labels:
            it["loc_name"] = loc_labels[it["loc"]]

    parent_map = {}  # qid -> [(parent_qid, parent_label)]
    current = {qid for qid, it in items.items() if it["loc"]}
    for _ in range(3):
        if not current:
            break
        parents = fetch_parents(sorted(current))
        if not parents:
            break
        for loc, pairs in parents.items():
            parent_map.setdefault(loc, []).extend(pairs)
        current = {p for pairs in parents.values() for p, _ in pairs}

    def first_regency_match(qid, loc_label):
        labels = [loc_label]
        seen = set()
        cur = qid
        while len(labels) <= 4:
            if cur is None or cur in seen:
                break
            seen.add(cur)
            pairs = parent_map.get(cur)
            if not pairs:
                break
            parent_qid, parent_label = pairs[0]
            labels.append(parent_label)
            cur = parent_qid
        for label in labels:
            if label and label.lower() in REGENCY_NAME:
                return REGENCY_NAME[label.lower()]
        return None

    for qid, it in items.items():
        loc = it["loc"]
        if loc:
            match = first_regency_match(loc, it["loc_name"])
            if match:
                it["province"], it["regency"] = match
                continue
        prov = province_by_coord(it["lat"], it["lon"])
        if prov:
            it["province"] = prov
            it["regency"] = nearest_anchor_regency(it["lat"], it["lon"], prov)


def clean_name(name: str) -> str:
    name = re.sub(r"\s*\(disambiguasi\)\s*$", "", name, flags=re.IGNORECASE)
    return " ".join(name.split())


def main() -> None:
    parser = argparse.ArgumentParser(description="Scrape real Indonesian destinations from Wikidata")
    parser.add_argument("--output", default="app/ml/data/real_destinations.csv")
    args = parser.parse_args()

    items = fetch_items()
    print(f"Fetched {len(items)} notable items")

    loc_labels = fetch_labels(sorted({qid for qid, it in items.items() if it["loc"]}))
    resolve_regencies(items, loc_labels)

    rows = []
    seen_names = set()
    dropped_noloc = dropped_nocat = dropped_dup = 0
    for qid, it in items.items():
        name = clean_name(it["name"])
        if not name:
            dropped_noloc += 1
            continue
        key = name.lower()
        if key in seen_names:
            dropped_dup += 1
            continue
        cat = classify(name, it["types"])
        if cat is None:
            dropped_nocat += 1
            continue
        if "province" not in it or "regency" not in it:
            dropped_noloc += 1
            continue
        if cat not in CATEGORIES:
            dropped_nocat += 1
            continue
        if name.lower() in BIG_ISLANDS:
            dropped_nocat += 1
            continue
        seen_names.add(key)
        images = [p18_url(it["img"])] if it["img"] else []
        rows.append({
            "name": name,
            "category": cat,
            "province": it["province"],
            "regency": it["regency"],
            "latitude": round(it["lat"], 6),
            "longitude": round(it["lon"], 6),
            "qid": qid,
            "images": "|".join(images),
        })

    print(f"After filter: {len(rows)} (dropped: dup={dropped_dup} noloc={dropped_noloc} nocat={dropped_nocat})")
    print("Top categories:", Counter(r["category"] for r in rows).most_common(8))
    print("Provinces:", len(set(r["province"] for r in rows)))
    with_photo = sum(1 for r in rows if r["images"])
    print(f"Primary photos (P18): {with_photo}/{len(rows)}")

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "name", "category", "province", "regency", "latitude", "longitude", "qid", "images",
        ])
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} real destinations -> {out}")


if __name__ == "__main__":
    main()
