"""Build the static HTML index from the Markdown directory files.

Usage:
    python3 build.py            # generate index.html and urls.txt
    python3 build.py --check    # parse only; print a summary and exit

The Markdown files under directory/ are the source of truth. Each entry file
contains one or more Markdown tables whose header row starts with "Source".
Everything else in the file (intro paragraphs, tips) is documentation and is
not parsed into entries.
"""

from __future__ import annotations

import argparse
import html
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DIRECTORY = ROOT / "directory"

REQUIRED_COLUMNS = ["Source", "What's inside", "License notes", "Safe to sell", "Link"]
VALID_FLAGS = {"SAFE", "SAFE-ATTR", "SAFE-COND", "CHECK", "N/A", "NO"}


def parse_entry_tables(markdown_text: str) -> list[dict[str, str]]:
    """Return every entry row from tables whose header starts with 'Source'."""
    entries: list[dict[str, str]] = []
    lines = markdown_text.splitlines()
    i = 0
    while i < len(lines):
        stripped = lines[i].strip()
        if stripped.startswith("|") and stripped.endswith("|"):
            cells = [c.strip() for c in stripped.strip("|").split("|")]
            if cells and cells[0] == "Source" and len(cells) >= len(REQUIRED_COLUMNS):
                # skip separator row
                i += 2
                while i < len(lines):
                    row = lines[i].strip()
                    if not (row.startswith("|") and row.endswith("|")):
                        break
                    values = [c.strip() for c in row.strip("|").split("|")]
                    if len(values) != len(REQUIRED_COLUMNS):
                        raise ValueError(
                            "Malformed table row (expected "
                            f"{len(REQUIRED_COLUMNS)} columns): {row}"
                        )
                    source, inside, license_notes, flag, link = values
                    if flag not in VALID_FLAGS:
                        raise ValueError(
                            f"Unknown safe-to-sell flag {flag!r} in row for {source!r}"
                        )
                    entries.append(
                        {
                            "source": source,
                            "inside": inside,
                            "license": license_notes,
                            "flag": flag,
                            "url": link,
                        }
                    )
                    i += 1
                continue  # fall through without double-increment mistakes
        i += 1
    return entries


def parse_file(path: Path) -> dict:
    """Parse one entry file into {title, intro, entries}."""
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    title = None
    for line in lines:
        if line.startswith("# "):
            title = line[2:].strip()
            break
    if title is None:
        raise ValueError(f"{path.name}: no H1 title found")

    # intro = plain-text paragraph lines before the first table
    intro_lines: list[str] = []
    in_code_fence = False
    for line in lines:
        if line.strip().startswith("```"):
            in_code_fence = not in_code_fence
            continue
        if in_code_fence:
            continue
        if line.strip().startswith("|"):
            break
        if started(line):
            intro_lines.append(line.strip())
    intro = " ".join(intro_lines).strip()

    entries = parse_entry_tables(text)
    return {"file": path.name, "title": title, "intro": intro, "entries": entries}


def started(line: str) -> bool:
    return bool(line.strip()) and not line.strip().startswith("#")


def load_all() -> list[dict]:
    medley = sorted(DIRECTORY.glob("*.md"))
    files = [p for p in medley if "how-to-use" not in p.name.lower()]
    if not files:
        raise SystemExit("No markdown files found in directory/")
    sections = []
    for path in files:
        if path.name.lower().startswith("00-") or path.name.lower() == "readme.md":
            continue  # guide file, not an entry listing
        parsed = parse_file(path)
        if not parsed["entries"]:
            raise SystemExit(f"{path.name}: no entry table found")
        sections.append(parsed)
    return sections


def render_html(sections: list[dict]) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    total = sum(len(s["entries"]) for s in sections)
    cat_count = len(sections)

    flags_legend = {
        "SAFE": "Public domain or CC0. Use freely in KDP covers and printables.",
        "SAFE-ATTR": "Fine for products; include the requested credit line.",
        "SAFE-COND": "Commercial use allowed under the site's own license conditions.",
        "CHECK": "Mixed licenses - verify the tag on each image before use.",
        "N/A": "Reference page (policy or guidance), not an art source.",
        "NO": "Not safe to sell with.",
    }

    parts: list[str] = []
    parts.append(
        "<!DOCTYPE html>\n"
        '<html lang="en">\n<head>\n'
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>Free Art Vault - public domain &amp; CC0 sources for covers and printables</title>\n"
        '<meta name="description" content="A curated directory of public domain and CC0 '
        'art sources: Wikimedia Commons, vintage botanical and anatomy prints, NASA '
        'imagery, Library of Congress, and icon sets - with license notes and '
        'safe-to-sell flags for KDP covers and printables.">\n'
        "<style>\n"
        ":root { --ink: #1d2530; --paper: #faf7f2; --card: #ffffff; --line: #e4dfd5;\n"
        "  --green: #2e7d4f; --amber: #9c6f19; --grey: #5a6472; --accent: #35507a; }\n"
        "* { box-sizing: border-box; }\n"
        "body { margin: 0; background: var(--paper); color: var(--ink);\n"
        "  font: 16px/1.65 Georgia, 'Times New Roman', serif; }\n"
        ".wrap { max-width: 1060px; margin: 0 auto; padding: 40px 20px 80px; }\n"
        "header.site { border-bottom: 3px double var(--line); padding-bottom: 24px;\n"
        "  margin-bottom: 32px; }\n"
        "h1.site { font-size: 2rem; margin: 0 0 6px; letter-spacing: .2px; }\n"
        "p.tag { margin: 0; color: var(--grey); font-style: italic; }\n"
        ".meta { margin-top: 10px; font-size: .85rem; color: var(--grey);\n"
        "  font-family: ui-monospace, Menlo, Consolas, monospace; }\n"
        ".legend { background: var(--card); border: 1px solid var(--line);\n"
        "  border-radius: 10px; padding: 18px 20px; margin-bottom: 36px; }\n"
        ".legend h2 { margin: 0 0 8px; font-size: 1.05rem; }\n"
        ".legend ul { margin: 0; padding-left: 20px; }\n"
        ".legend li { margin-bottom: 4px; font-size: .95rem; }\n"
        "section.cat { margin-bottom: 44px; }\n"
        "section.cat h2 { font-size: 1.4rem; margin: 0 0 6px; }\n"
        "section.cat p.intro { margin: 0 0 14px; color: var(--grey); }\n"
        ".card { background: var(--card); border: 1px solid var(--line);\n"
        "  border-radius: 10px; padding: 6px 18px 14px; overflow-x: auto; }\n"
        "table { border-collapse: collapse; width: 100%; font-size: .92rem; }\n"
        "th { text-align: left; font-family: ui-sans-serif, system-ui, sans-serif;\n"
        "  font-size: .78rem; text-transform: uppercase; letter-spacing: .06em;\n"
        "  color: var(--grey); border-bottom: 2px solid var(--line); padding: 8px 10px; }\n"
        "td { border-bottom: 1px solid var(--line); padding: 10px; vertical-align: top; }\n"
        "tr:last-child td { border-bottom: none; }\n"
        "td.src { font-family: ui-sans-serif, system-ui, sans-serif; font-weight: 600;\n"
        "  white-space: nowrap; }\n"
        ".flag { display: inline-block; font-family: ui-monospace, Menlo, monospace;\n"
        "  font-size: .74rem; padding: 2px 8px; border-radius: 999px;\n"
        "  border: 1px solid currentColor; white-space: nowrap; }\n"
        ".flag.SAFE { color: var(--green); }\n"
        '.flag.SAFE-ATTR, .flag.CHECK { color: var(--amber); }\n'
        ".flag.N-A { color: var(--grey); }\n"
        "a { color: var(--accent); }\n"
        "a.urllink { font-family: ui-monospace, Menlo, Consolas, monospace;\n"
        "  font-size: .8rem; word-break: break-all; }\n"
        "footer { border-top: 3px double var(--line); margin-top: 48px;\n"
        "  padding-top: 18px; color: var(--grey); font-size: .88rem; }\n"
        "@media (max-width: 640px) { td.src { white-space: normal; } }\n"
        "</style>\n"
        "</head>\n<body>\n"
        '<div class="wrap">\n'
        "<header class=\"site\">\n"
        "<h1 class=\"site\">Free Art Vault</h1>\n"
        "<p class=\"tag\">Public domain &amp; CC0 sources for KDP covers, printables, and everything you sell.</p>\n"
        f'<p class="meta">{cat_count} categories &middot; {total} sources &middot; verified links &middot; generated {now}</p>\n'
        "</header>\n"
    )

    parts.append('<div class="legend">\n<h2>How to read the flags</h2>\n<ul>\n')
    for flag, meaning in flags_legend.items():
        label = "SAFE" if flag == "N/A" else flag
        parts.append(
            f'<li><span class="flag {flag.replace("-", "-")}">{label}</span> &mdash; {html.escape(meaning)}</li>\n'
        )
    parts.append("</ul>\n</div>\n")

    for section in sections:
        parts.append('<section class="cat">\n')
        parts.append(f"<h2>{html.escape(section['title'])}</h2>\n")
        if section["intro"]:
            parts.append(f'<p class="intro">{html.escape(section["intro"])}</p>\n')
        parts.append('<div class="card">\n<table>\n<thead>\n<tr>')
        for col in ["Source", "What's inside", "License notes", "Safe to sell", "Where"]:
            parts.append(f"<th>{html.escape(col)}</th>")
        parts.append("</tr>\n</thead>\n<tbody>\n")
        for entry in section["entries"]:
            url = html.escape(entry["url"], quote=True)
            css_flag = entry["flag"].replace("-", "-").replace("/", "")
            parts.append("<tr>")
            parts.append(f'<td class="src">{html.escape(entry["source"])}</td>')
            parts.append(f"<td>{html.escape(entry['inside'])}</td>")
            parts.append(f"<td>{html.escape(entry['license'])}</td>")
            parts.append(f'<td><span class="flag {css_flag}">{html.escape(entry["flag"])}</span></td>')
            parts.append(f'<td><a class="urllink" href="{url}" target="_blank" rel="noopener">{url}</a></td>')
            parts.append("</tr>\n")
        parts.append("</tbody>\n</table>\n</div>\n</section>\n")

    parts.append(
        "<footer>\n"
        "<p>Curated by Asdale Dynamics, LLC. Links point to source libraries only - "
        "this directory redistributes nothing and scrapes nothing. Always read the "
        "license tag on the individual image before you build with it.</p>\n"
        "<p>MIT licensed. See <code>LICENSE</code> in the repository.</p>\n"
        "</footer>\n"
        "</div>\n</body>\n</html>\n"
    )
    return "".join(parts)


def write_manifest(sections: list[dict]) -> Path:
    out = ROOT / "urls.txt"
    with out.open("w", encoding="utf-8") as fh:
        for section in sections:
            for entry in section["entries"]:
                fh.write(f"{section['file']}\t{entry['source']}\t{entry['url']}\n")
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="parse and report only")
    args = parser.parse_args()

    sections = load_all()
    total = sum(len(s["entries"]) for s in sections)
    print(f"Parsed {len(sections)} category files, {total} sources.")

    if args.check:
        return 0

    html_doc = render_html(sections)
    (ROOT / "index.html").write_text(html_doc, encoding="utf-8")
    urls = write_manifest(sections)
    print(f"Wrote index.html and {urls.name} ({len(html_doc)} bytes).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
