"""Explainable rubric scoring against a role brief.

Deliberately transparent: every point is traceable to a matched signal, so a
hiring decision is never handed to an opaque number.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


def load_role(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _haystack(rec: dict[str, Any]) -> str:
    parts = [
        rec.get("headline", ""),
        rec.get("about", ""),
        rec.get("current_title", ""),
        rec.get("current_company", ""),
        " ".join(f"{r.get('title', '')} {r.get('company', '')}"
                 for r in rec.get("experience", [])),
        # Education entries are dicts from JSON-LD, plain strings from fallback.
        " ".join(e.get("name", "") if isinstance(e, dict) else str(e)
                 for e in rec.get("education", [])),
        rec.get("badges", ""),
        " ".join(rec.get("languages", [])),
    ]
    return " ".join(parts).lower()


def _hits(haystack: str, terms: list[str]) -> list[str]:
    found = []
    for term in terms:
        t = term.lower().strip()
        if not t:
            continue
        # Word-boundary match so "seo" doesn't fire inside "seoul".
        if re.search(rf"(?<!\w){re.escape(t)}(?!\w)", haystack):
            found.append(term)
    return found


def score(rec: dict[str, Any], role: dict[str, Any]) -> dict[str, Any]:
    """Return {score, breakdown, matched, missing, flags} for one candidate."""
    hay = _haystack(rec)
    loc = (rec.get("location", "") or "").lower()

    must = role.get("must_have", [])
    nice = role.get("nice_to_have", [])
    exclude = role.get("exclude", [])
    loc_hints = role.get("location_hint", [])

    must_hits = _hits(hay, must)
    nice_hits = _hits(hay, nice)
    exclude_hits = _hits(hay, exclude)
    loc_hits = _hits(loc, loc_hints) or _hits(hay, loc_hints)

    w = role.get("weights", {})
    w_must = w.get("must_have", 55)
    w_nice = w.get("nice_to_have", 25)
    w_location = w.get("location", 20)

    must_pts = (len(must_hits) / len(must) * w_must) if must else w_must
    nice_pts = (len(nice_hits) / len(nice) * w_nice) if nice else 0
    loc_pts = w_location if loc_hits else 0

    total = must_pts + nice_pts + loc_pts

    flags: list[str] = []
    if exclude_hits:
        total *= 0.4
        flags.append(f"exclusion signal: {', '.join(exclude_hits)}")
    if not rec.get("experience"):
        flags.append("no public experience section (profile may be gated or sparse)")
    if not loc_hits and loc_hints:
        flags.append("location not confirmed against brief")

    return {
        "score": round(min(total, 100), 1),
        "breakdown": {
            "must_have": round(must_pts, 1),
            "nice_to_have": round(nice_pts, 1),
            "location": round(loc_pts, 1),
        },
        "matched": {"must_have": must_hits, "nice_to_have": nice_hits, "location": loc_hits},
        "missing": [m for m in must if m not in must_hits],
        "flags": flags,
    }
