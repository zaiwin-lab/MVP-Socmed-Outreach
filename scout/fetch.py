"""Fetch public profile pages, with caching and backoff.

Two transports, tried in order:

1. **direct**  — plain HTTPS GET of the logged-out public page. No cookies,
   no session, no login. This is what a search engine crawler sees.
2. **jina**    — https://r.jina.ai rendering, used only as a fallback.
   Anonymous use is blocked from most datacenter IPs ("bad IP reputation"),
   so set JINA_API_KEY to make this path dependable.

Only public, logged-out pages are ever fetched. See README "Boundaries".
"""

from __future__ import annotations

import gzip
import hashlib
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

READER = "https://r.jina.ai/"
BROWSER_UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

CACHE_DIR = Path(__file__).resolve().parent.parent / "data" / ".cache"

RETRYABLE = {408, 429, 500, 502, 503, 504}


class FetchError(RuntimeError):
    pass


class Blocked(FetchError):
    """The transport refused us (rate limit, IP reputation, auth wall)."""


def _cache_path(url: str, transport: str) -> Path:
    key = hashlib.sha256(f"{transport}:{url}".encode("utf-8")).hexdigest()[:20]
    return CACHE_DIR / f"{key}.txt"


def _read_body(resp) -> str:
    raw = resp.read()
    if resp.headers.get("Content-Encoding") == "gzip":
        raw = gzip.decompress(raw)
    return raw.decode("utf-8", errors="replace")


def _get(url: str, headers: dict[str, str], timeout: int) -> str:
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return _read_body(resp)


def _fetch_direct(url: str, timeout: int) -> str:
    return _get(url, {
        "User-Agent": BROWSER_UA,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }, timeout)


def _fetch_jina(url: str, timeout: int) -> str:
    headers = {
        "User-Agent": BROWSER_UA,
        "Accept": "text/plain, text/markdown, */*",
        "X-Retain-Images": "none",
    }
    key = os.environ.get("JINA_API_KEY", "").strip()
    if key:
        headers["Authorization"] = f"Bearer {key}"
    return _get(READER + url, headers, timeout)


TRANSPORTS = {"direct": _fetch_direct, "jina": _fetch_jina}


def fetch(url: str, *, timeout: int = 60, use_cache: bool = True,
          max_age_days: int = 14, retries: int = 3,
          transport: str = "auto") -> tuple[str, str]:
    """Fetch `url`. Returns (body, transport_used).

    Cached on disk so re-scoring a shortlist never re-hits the network.
    """
    order = ["direct", "jina"] if transport == "auto" else [transport]

    if use_cache:
        for name in order:
            cache = _cache_path(url, name)
            if cache.exists():
                age_days = (time.time() - cache.stat().st_mtime) / 86400
                if age_days < max_age_days:
                    return cache.read_text(encoding="utf-8"), name

    errors: list[str] = []

    for name in order:
        fn = TRANSPORTS[name]
        for attempt in range(retries):
            try:
                body = fn(url, timeout)
                if not body.strip():
                    raise FetchError("empty response")
                CACHE_DIR.mkdir(parents=True, exist_ok=True)
                _cache_path(url, name).write_text(body, encoding="utf-8")
                return body, name
            except urllib.error.HTTPError as e:
                # 401 from Jina means anonymous access was refused, not a
                # transient fault — stop hammering it and move on.
                if e.code in (401, 403):
                    errors.append(f"{name}: HTTP {e.code} (blocked/auth required)")
                    break
                if e.code not in RETRYABLE:
                    errors.append(f"{name}: HTTP {e.code}")
                    break
                errors.append(f"{name}: HTTP {e.code}")
            except Exception as e:  # noqa: BLE001 - network layer is broad by nature
                errors.append(f"{name}: {e}")

            if attempt < retries - 1:
                time.sleep(2 ** (attempt + 1))

    raise Blocked(f"all transports failed for {url} :: " + "; ".join(errors[-4:]))
