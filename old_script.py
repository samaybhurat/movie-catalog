#!/usr/bin/env python3
"""
movie_catalog.py — generate an HTML poster-and-trailer catalog
from all .torrent files in the current folder.
"""

import re, html, urllib.parse, pathlib, sys, requests
from datetime import datetime

TMDB_API_KEY = "c4d65cf9f8544414072b0125da2ee342"          # ① drop your key here
IMAGE_WIDTH  = 342
OUTPUT_HTML  = "movie_catalog.html"
TORRENT_GLOB = "*.torrent"

BASE_IMAGE_URL = f"https://image.tmdb.org/t/p/w{IMAGE_WIDTH}"
SEARCH_URL = "https://api.themoviedb.org/3/search/movie"
VIDEO_URL  = "https://api.themoviedb.org/3/movie/{id}/videos"

session = requests.Session()
session.params = {"api_key": TMDB_API_KEY, "language": "en-US"}

def slug_to_title(slug: str) -> str:
    slug = slug.rsplit(".", 1)[0]
    slug = re.sub(r"\[.*?\]|\(.*?\)", "", slug)
    slug = re.sub(r"\b(19|20)\d{2}\b", "", slug)
    slug = re.sub(r"\b(480p|720p|1080p|2160p|x264|x265|HEVC|BluRay|WEBRip|YIFY|AAC).*",
                  "", slug, flags=re.I)
    slug = slug.replace(".", " ").replace("_", " ")
    return " ".join(slug.split()).strip() or slug

def tmdb_lookup(title: str):
    try:
        r = session.get(SEARCH_URL, params={"query": title, "page": 1})
        r.raise_for_status()
        results = r.json().get("results", [])
        if not results:
            return None, None
        movie_id = results[0]["id"]
        poster_path = results[0]["poster_path"]
        poster_url = BASE_IMAGE_URL + poster_path if poster_path else None

        vr = session.get(VIDEO_URL.format(id=movie_id))
        vr.raise_for_status()
        vids = vr.json().get("results", [])
        yt = next((v for v in vids if v["site"] == "YouTube" and v["type"] == "Trailer"), None)
        trailer_url = (f"https://www.youtube.com/watch?v={yt['key']}"
                       if yt else
                       None)
        return poster_url, trailer_url
    except Exception as e:
        print(f"⚠️ TMDb lookup failed for '{title}': {e}")
        return None, None

def build_html(entries):
    head = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<title>Movie Catalog</title>
<style>
body{{font-family:sans-serif;background:#111;color:#eee}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:1rem;padding:1rem}}
.card{{background:#222;border-radius:12px;overflow:hidden;box-shadow:0 2px 6px #0009}}
.card img{{width:100%;display:block}}
.card a{{text-decoration:none;color:#0af}}
h3{{font-size:1rem;margin:0.5rem}}
footer{{text-align:center;margin:2rem;font-size:.8rem;color:#888}}
</style></head><body>
<h1 style="text-align:center;">Movie Catalog · {datetime.now().date()}</h1>
<section class="grid">"""
    cards = []
    for title, poster, trailer in entries:
        trailer = trailer or "#"
        img_tag = (f'<img src="{poster}" alt="{html.escape(title)} poster">'
                   if poster else
                   '<div style="height:300px;background:#444;"></div>')
        cards.append(f"""<article class="card">
  <a href="{html.escape(trailer)}" target="_blank">{img_tag}
  <h3>{html.escape(title or 'Unknown')}</h3></a>
</article>""")
    tail = "</section><footer>Generated with TMDb.org data (poster & trailer links).</footer></body></html>"
    return head + "\n".join(cards) + tail

EXTRA_TITLE_FILE = "extra_titles.txt"   # ← name of the optional text file

def main():
    if TMDB_API_KEY == "PASTE_YOUR_KEY_HERE":
        print("❌  Edit the script and paste your TMDb API key in TMDB_API_KEY.")
        sys.exit(1)

    folder   = pathlib.Path.cwd()
    torrents = sorted(folder.glob(TORRENT_GLOB))

    # ─────── gather titles from torrents ───────
    titles = [slug_to_title(tor.name) for tor in torrents]

    # ─────── add titles from extra_titles.txt ───────
    extra = folder / EXTRA_TITLE_FILE
    if extra.exists():
        with extra.open(encoding="utf-8") as f:
            titles.extend(line.strip() for line in f if line.strip())

    # ─────── dedupe while preserving order ───────
    seen, unique = set(), []
    for t in titles:
        key = t.lower()
        if key not in seen:
            seen.add(key)
            unique.append(t)

    if not unique:
        print("No titles found (torrent glob + text file both empty).")
        return

    # ─────── TMDb look-ups & HTML build ───────
    entries = []
    for title in unique:
        poster, trailer = tmdb_lookup(title)
        entries.append((title, poster, trailer))
        print(f"✔ {title}")

    (folder / OUTPUT_HTML).write_text(build_html(entries), encoding="utf-8")
    print(f"\n✅ Done! Open {OUTPUT_HTML} in your browser.")

if __name__ == "__main__":
    main()

