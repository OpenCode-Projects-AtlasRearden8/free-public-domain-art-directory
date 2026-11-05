# STATUS

Project: Free Art Vault - public domain and CC0 art source directory
Owner: Asdale Dynamics, LLC
Date: 2026-11-05

## What was built

A curated, static directory of 63 verified free-art sources for KDP covers,
printables, and other products that are sold. No scraping, no re-hosting: every
entry points to the source library itself, with plain-English license notes and a
safe-to-sell flag.

- `directory/*.md` - source of truth, 9 Markdown files:
  - `01-how-to-use.md` - license primer, flag legend, KDP workflow, honest caveats
  - `02-wikimedia-commons.md` - Commons vaults (PD/CC0 categories, botanicals, herbals,
    seed catalogs, anatomy, Audubon)
  - `03-vintage-botanical-prints.md` - BHL site/collections/Flickr, NYPL, Old Book Illustrations
  - `04-vintage-anatomy-prints.md` - Gray's Anatomy plates, historic anatomical plates,
    anatomical models, Internet Archive
  - `05-nasa-space-imagery.md` - images.nasa.gov, JPL Photojournal, SVS, Earth Observatory,
    astronaut photography, Hubble, Air & Space Museum
  - `06-library-of-congress.md` - Free to Use & Reuse sets (Gardens, WPA posters,
    Nurses & Nursing, Classic Children's Books), P&P catalog, Chronicling America,
    copyright guidance
  - `07-icon-sets.md` - 12 MIT/ISC/CC0/CC-BY icon libraries
  - `08-museum-open-access.md` - Smithsonian, Met, AIC, Rijksmuseum, Cleveland
  - `09-search-hubs-and-photo-libraries.md` - Openverse, Pixabay, Pexels, Unsplash,
    PublicDomainPictures, Openclipart, PICRYL
- `index.html` - polished static HTML index generated from the Markdown
- `build.py` - Markdown-to-HTML builder (also writes `urls.txt` manifest; `--check`
  parses without writing)
- `check_links.py` - link verifier: GETs every URL, classifies OK / BLOCKED
  (bot walls: 401/403/429/999) / BROKEN, writes `link-check-report.json`
- `verify_build.py` - verification suite (39 checks)
- `LICENSE` - MIT, copyright line exactly "Copyright (c) 2026 Asdale Dynamics, LLC"
- `README.md` - usage and credits (Asdale Dynamics, LLC)

Flag system: SAFE (PD/CC0), SAFE-ATTR (credit required), SAFE-COND (site license with
conditions - stock sites), CHECK (verify per item), NO (unused on purpose).

## How to run it

Python 3 standard library only; no dependencies, no secrets, nothing leaves your machine.

```bash
python3 build.py             # rebuild index.html + urls.txt from directory/*.md
python3 build.py --check     # parse-only sanity pass
python3 check_links.py       # verify every URL (writes link-check-report.json)
python3 verify_build.py      # full verification suite
```

Open `index.html` in a browser for the render. Edit a table row in `directory/*.md`,
re-run `build.py`, done.

## Verification results

- `python3 build.py` - OK. 8 category files parsed, 63 sources rendered.
- `python3 check_links.py` - 63 unique URLs: **36 OK, 27 BLOCKED (bot walls), 0 broken**.
  Exit code 0. Bot-wall sites (Wikimedia, BHL, Smithsonian, Met, AIC, Openverse, Pixabay,
  Pexels, Unsplash, PICRYL, etc.) refuse automated clients by design but serve normal
  browsers; the Wikimedia pages were additionally confirmed present via the MediaWiki
  API, and every URL that returned 404/BROKEN during development was replaced with a
  verified live link.
- `python3 verify_build.py` - **All 39 checks passed**: required files present, LICENSE
  exact-line + ASCII, README credit, 63 well-formed entries with unique URLs and valid
  flags, all indexed topics covered, index.html renders every entry and credit, zero
  broken links in the report, no secret patterns anywhere, all Markdown clean ASCII.
- HTML structural sanity: DOCTYPE correct, 8 sections, zero non-ASCII, license text only
  in LICENSE.

## Known gaps / honest notes

- Link rot is inevitable. Re-run `check_links.py` before each release; treat BLOCKED as
  "site exists, refuses bots" and re-check those pages in a browser.
- Bot-walled pages could not be byte-level verified locally (Wikimedia confirmed via
  API; Pixabay/Pexels/Unsplash/PICRYL confirmed by their status classes only).
- Copyright summaries are practical guidance, not legal advice; each source page's own
  rights statement wins any conflict.
- The directory is an index only - it deliberately contains no images, no scraping
  scripts, and no bulk-download instructions.
- Future ideas: per-item license-tag bookmarks, cover-dimension cheat sheet per source,
  a Kanban-style "cleared for book X" tracker.
