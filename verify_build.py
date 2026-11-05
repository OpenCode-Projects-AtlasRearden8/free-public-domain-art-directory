"""Verification suite for the free art directory.

Run:  python3 verify_build.py

Checks structure, parsing, licensing/attribution requirements, and safety invariants:
assembles the facts that STATUS.md reports, exits non-zero on any failure.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import build

ROOT = Path(__file__).resolve().parent

failures: list[str] = []


def check(condition: bool, message: str) -> None:
    if condition:
        print(f"  PASS  {message}")
    else:
        failures.append(message)
        print(f"  FAIL  {message}")


def main() -> int:
    print("== Verifying free-public-domain-art-directory ==")

    # --- required files -----------------------------------------------------
    required = ["build.py", "check_links.py", "verify_build.py", "LICENSE",
                "README.md", "index.html", "urls.txt", "link-check-report.json"]
    for name in required:
        check((ROOT / name).is_file(), f"required file exists: {name}")

    directory_files = sorted((ROOT / "directory").glob("*.md"))
    check(len(directory_files) >= 6, f"directory has >=6 category files (got {len(directory_files)})")

    # --- LICENSE exactness --------------------------------------------------
    license_text = (ROOT / "LICENSE").read_text(encoding="utf-8")
    check("Copyright (c) 2026 Asdale Dynamics, LLC" in license_text,
          "LICENSE contains exact copyright line")
    check("MIT License" in license_text, "LICENSE states MIT License")
    check(license_text.isascii(), "LICENSE is plain ASCII")

    # --- README credit ------------------------------------------------------
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    check("Asdale Dynamics, LLC" in readme, "README credits Asdale Dynamics, LLC")
    check(readme.isascii(), "README is plain ASCII")

    # --- markdown parses & entries well-formed ------------------------------
    sections = build.load_all()
    entries = [e for s in sections for e in s["entries"]]
    check(len(sections) >= 5, f"at least 5 entry sections parsed (got {len(sections)})")
    check(len(entries) >= 40, f"at least 40 sources catalogued (got {len(entries)})")

    urls = [e["url"] for e in entries]
    check(len(urls) == len(set(urls)), "no duplicate URLs across entries")
    check(all(u.startswith(("http://", "https://")) for u in urls),
          "all entry URLs are absolute http(s)")

    flags = [e["flag"] for e in entries]
    check("NO" not in flags, "no entry carries the unacceptable NO flag")
    safe_or_better = [f for f in flags if f in ("SAFE", "SAFE-ATTR", "SAFE-COND", "N/A")]
    check(len(safe_or_better) >= len(flags) - 12,
          f"most entries are SAFE/SAFE-ATTR (got {len(safe_or_better)}/{len(flags)})")

    # --- topic coverage ------------------------------------------------------
    titles = " ".join(s["title"].lower() for s in sections)
    for topic in ["botanical", "anatomy", "nasa", "library of congress", "icon", "commons"]:
        check(topic in titles, f"coverage: a section covers {topic!r}")

    # --- index.html built from the same data --------------------------------
    index_html = (ROOT / "index.html").read_text(encoding="utf-8")
    for section in sections:
        check(section["title"] in index_html,
              f"index.html contains section: {section['title']}")
    link_count = index_html.count('class="urllink"')
    check(link_count == len(entries),
          f"index.html links every entry ({link_count} of {len(entries)})")
    check("Asdale Dynamics, LLC" in index_html, "index.html credits Asdale Dynamics, LLC")

    # --- link report sanity -------------------------------------------------
    import json
    report = json.loads((ROOT / "link-check-report.json").read_text(encoding="utf-8"))
    check(report["broken"] == 0, "link check: zero broken links")

    # --- safety scan: no secrets / personal data -----------------------------
    secret_patterns = [
        r"sk-[A-Za-z0-9]{20,}", r"ghp_[A-Za-z0-9]{20,}", r"AKIA[0-9A-Z]{16}",
        r"(?i)api[_-]?key\s*[:=]\s*[\"']?[A-Za-z0-9]{16,}",
        r"(?i)password\s*[:=]\s*\S+",
    ]
    scan_targets = list(directory_files) + [
        ROOT / n for n in required if n.endswith((".py", ".md", ".html"))
    ]
    dirty = []
    for path in scan_targets:
        text = path.read_text(encoding="utf-8", errors="replace")
        for pattern in secret_patterns:
            if re.search(pattern, text):
                dirty.append(f"{path.name}: {pattern}")
    check(not dirty, f"no secrets or keys in project files{'' if not dirty else ' -> ' + '; '.join(dirty)}")

    # --- no encoding garbage in prose ---------------------------------------
    garbage = []
    for path in list(directory_files) + [ROOT / "README.md"]:
        text = path.read_text(encoding="utf-8")
        non_ascii = re.findall(r"[^\x00-\x7F]", text)
        if non_ascii:
            garbage.append(f"{path.name}: {len(non_ascii)} non-ASCII char(s)")
    check(not garbage, f"markdown files are clean ASCII{'' if not garbage else ' -> ' + '; '.join(garbage)}")

    print()
    if failures:
        print(f"FAILED: {len(failures)} check(s) failed.")
        return 1
    print("All checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
