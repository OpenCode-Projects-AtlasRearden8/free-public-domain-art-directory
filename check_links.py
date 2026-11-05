"""Link checker for the free art directory.

Reads urls.txt (built by build.py), requests every URL, and records the result.

Verdicts:
    OK      - HTTP 2xx
    BLOCKED - the site answered but refuses automated clients (403/429/999).
              The page exists for humans; re-check in a normal browser.
    BROKEN  - 4xx (other than bot blocks), 5xx after retry, DNS failure,
              timeout, or TLS errors.

Exit code is 1 if any link is BROKEN, 0 otherwise. Writes
link-check-report.json for STATUS.md and CI use.
"""

from __future__ import annotations

import json
import ssl
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / "urls.txt"
REPORT = ROOT / "link-check-report.json"

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "free-art-vault-link-checker/1.0 (+https://dylanasdale.github.io) "
    "python-urllib link verification"
)

BLOCK_STATUSES = {401, 403, 429, 999}
# 401 note: some sites (e.g. Unsplash) answer automated clients with 401 while the
# page serves fine in a normal browser.
TIMEOUT = 25
RETRIES = 2
CTX = ssl.create_default_context()

BLOCKED_PATTERNS = [
    # Some sites return 200 with an anti-bot interstitial page.
    b"captcha", b"Attention Required", b"Just a moment", b"Access denied",
]


def verdict_for(status: int) -> str:
    if 200 <= status < 300:
        return "OK"
    if status in BLOCK_STATUSES:
        return "BLOCKED"
    return "BROKEN"


def fetch(url: str, method: str) -> tuple[int, bytes | None, str | None]:
    request = urllib.request.Request(url, method=method, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=TIMEOUT, context=CTX) as response:
        data = response.read(4096) if method == "GET" else None
        return response.status, data, None


def check_url(url: str) -> dict:
    last_error = None
    for attempt in range(RETRIES + 1):
        try:
            status, body, _ = fetch(url, "GET")
            verdict = verdict_for(status)
            if verdict == "OK" and body and any(p in body for p in BLOCKED_PATTERNS):
                verdict = "BLOCKED"
            return {"url": url, "status": status, "verdict": verdict, "detail": ""}
        except urllib.error.HTTPError as exc:
            status = exc.code
            if status in BLOCK_STATUSES:
                return {"url": url, "status": status, "verdict": "BLOCKED",
                        "detail": "site refuses automated clients"}
            last_error = f"HTTP {status}"
            time.sleep(1.5 * (attempt + 1))
        except (urllib.error.URLError, TimeoutError, ssl.SSLError) as exc:
            last_error = str(exc.reason or exc)
            time.sleep(1.5 * (attempt + 1))
    return {"url": url, "status": None, "verdict": "BROKEN", "detail": last_error or "unreachable"}


def main() -> int:
    if not MANIFEST.exists():
        print("urls.txt not found - run `python3 build.py` first.", file=sys.stderr)
        return 2

    lines = [
        line
        for line in MANIFEST.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    urls: list[str] = []
    seen: set[str] = set()
    for line in lines:
        _file, _source, url = (line.split("\t", 2) + ["", ""])[:3]
        if url not in seen:
            seen.add(url)
            urls.append(url)

    print(f"Checking {len(urls)} unique URLs (patience requested)...")
    results: list[dict] = []
    for n, url in enumerate(urls, 1):
        result = check_url(url)
        results.append(result)
        validate = result["verdict"].ljust(7)
        print(f"  [{n:>3}/{len(urls)}] {validate} {url} {result['detail']}")

    counts = {v: sum(1 for r in results if r["verdict"] == v) for v in ("OK", "BLOCKED", "BROKEN")}
    broken = [r for r in results if r["verdict"] == "BROKEN"]
    blocked = [r for r in results if r["verdict"] == "BLOCKED"]
    checked = time.strftime("%Y-%m-%d")
    REPORT.write_text(
        json.dumps(
            {
                "checked": checked,
                "count": len(urls),
                "ok": counts["OK"],
                "blocked": counts["BLOCKED"],
                "broken": counts["BROKEN"],
                "broken_urls": [r["url"] for r in broken],
                "blocked_urls": [r["url"] for r in blocked],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    print(
        f"\nDone: {counts['OK']} OK, {counts['BLOCKED']} blocked-by-bot-wall, "
        f"{counts['BROKEN']} broken."
    )
    if broken:
        print("Broken URLs:", *broken, sep="\n  ", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
