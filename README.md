# Free Art Vault: public domain &amp; CC0 sources for covers and printables

A curated, human-built directory of free-to-use art sources for KDP book covers,
low-content printables, and anything else you sell. It points to:

- Wikimedia Commons vaults (botanical, anatomy, Gray's Anatomy, Audubon, CC0/PD categories)
- Vintage botanical and anatomy print collections (Biodiversity Heritage Library and friends)
- NASA imagery (Photojournal, SVS, Earth Observatory, astronaut photography, Hubble)
- Library of Congress "Free to Use & Reuse" sets and the P&P catalog
- Museum open-access programs (Smithsonian, Met, Rijksmuseum, Cleveland, AIC, NYPL)
- Openly licensed icon sets (MIT/ISC/CC0 - Bootstrap, Tabler, Lucide, Feather, Phosphor, and more)
- Search hubs (Openverse, Pixabay, Pexels, Unsplash, Openclipart) with honest license notes

Every entry carries a **license note** and a **safe-to-sell flag**:

| Flag | Meaning |
|------|---------|
| SAFE | Public domain or CC0. Use freely, even commercially. |
| SAFE-ATTR | Fine for products; include the requested credit. |
| SAFE-COND | Commercial use allowed under the site's own license conditions (read them once). |
| CHECK | Mixed licenses; verify each image's tag before use. |
| N/A | Reference page (policy/guidance), not an art source. |

No scraping instructions, no bulk downloads, no personal data - just links to the
libraries themselves and plain-English notes about what you can do with what you find.

## How to run it

Everything is Python standard library, local-first, no network keys, no dependencies.

```bash
# Rebuild the static HTML index and the URLs manifest
python3 build.py

# Parse-only sanity check (no files written)
python3 build.py --check

# Verify every catalogued URL actually resolves
python3 check_links.py

# Run the full verification suite (structure, licensing, safety, link report)
python3 verify_build.py
```

Open `index.html` in a browser for the polished, static index. The `directory/*.md`
files are the source of truth: edit a table row there, re-run `python3 build.py`, and
the HTML updates.

## Project layout

```
directory/                  Markdown source-of-truth, one file per category
index.html                  Static HTML index generated from directory/
urls.txt                    Machine-readable link manifest (generated)
link-check-report.json      Results of the last link check (generated)
build.py                    Markdown -> HTML builder
check_links.py              Link resolver (OK / BLOCKED / BROKEN)
verify_build.py             Verification suite
```

## What "safe to sell with" means here

Public domain and CC0 material can be used in products you sell, including KDP covers
and printables, with no permission needed. CC BY material can too, if you credit. The
flags encode exactly that, and the guide file
(`directory/01-how-to-use.md`) walks through a KDP-specific workflow.

## Known limitations

- Link health changes over time; re-run `python3 check_links.py` and treat the
  BLOCKED verdicts as "site exists, refuses bots" - those pages are fine in a browser.
- This directory is an informational tool, not legal advice. When something feels
  ambiguous, trust the library's own per-item rights statement over any summary,
  including ours.

## Credits

Built and maintained by **Asdale Dynamics, LLC** - beginner-friendly AI education,
books, and practical publishing tools by Dylan Asdale (dylanasdale.github.io).
Licensed under the MIT License (see `LICENSE`).
