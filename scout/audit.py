"""Audit a LinkedIn profile against a persona and report the gaps.

Answers one question: does the profile you actually have live say what your
persona file says it should? Every check returns a fix you can act on, not a
grade. A score with no instruction attached is not worth printing.

Input is a parsed profile record (`parse_linkedin.parse`) — normally from a
page you saved out of your own browser, since LinkedIn does not serve your own
profile to a logged-out fetch.
"""

from __future__ import annotations

import re
from typing import Any

from .persona import LIMITS

PASS, WARN, FAIL = "pass", "warn", "fail"

# LinkedIn's auto-assigned slugs look like `zaiwin-kassim-8a4b21079` — the name
# followed by a long alphanumeric run with digits in it. A claimed vanity URL
# does not have that tail.
RE_AUTO_SLUG = re.compile(r"-[a-z0-9]{6,}$")

# How much of the available headline to expect before calling it wasted space.
HEADLINE_TARGET = 0.55
ABOUT_TARGET = 0.45


def _digits(text: str) -> int:
    return sum(c.isdigit() for c in text)


def _check(name: str, status: str, detail: str, fix: str = "",
           weight: int = 1) -> dict[str, Any]:
    return {"name": name, "status": status, "detail": detail,
            "fix": fix, "weight": weight}


def _headline_checks(rec: dict[str, Any], p: dict[str, Any]) -> list[dict[str, Any]]:
    headline = (rec.get("headline") or "").strip()
    limit = LIMITS["linkedin_headline"]
    out = []

    if not headline:
        return [_check("Headline", FAIL, "empty",
                       "Paste one of the generated headlines.", weight=3)]

    used = len(headline) / limit
    if used < HEADLINE_TARGET:
        out.append(_check(
            "Headline length", WARN,
            f"{len(headline)}/{limit} characters ({used:.0%} used)",
            f"You have {limit - len(headline)} characters sitting unused. The "
            "headline follows you into every search result, comment and "
            "connection request — it is the most-read line you own.", weight=2))
    else:
        out.append(_check("Headline length", PASS,
                          f"{len(headline)}/{limit} characters", weight=2))

    low = headline.lower()
    primary = p.get("keywords", {}).get("primary", [])
    hits = [k for k in primary if k.lower() in low]
    if len(hits) >= 3:
        out.append(_check("Headline keywords", PASS,
                          f"{len(hits)}/{len(primary)} present: {', '.join(hits)}",
                          weight=2))
    else:
        missing = [k for k in primary if k.lower() not in low]
        out.append(_check(
            "Headline keywords", WARN if hits else FAIL,
            f"{len(hits)}/{len(primary)} present",
            "Recruiters and procurement search these terms. Missing: "
            + ", ".join(missing[:4]), weight=2))
    return out


def _about_checks(rec: dict[str, Any], p: dict[str, Any]) -> list[dict[str, Any]]:
    about = (rec.get("about") or "").strip()
    limit = LIMITS["linkedin_about"]
    out = []

    if not about:
        return [_check("About", FAIL, "empty",
                       "This is the single biggest gap a profile can have. "
                       "Paste the generated About section.", weight=3)]

    # A logged-out fetch truncates About, so only flag what is clearly short.
    used = len(about) / limit
    if used < ABOUT_TARGET:
        out.append(_check(
            "About length", WARN,
            f"~{len(about)}/{limit} characters visible ({used:.0%})",
            "Short About sections read as a placeholder. Note that a "
            "logged-out fetch truncates this field, so verify against the "
            "live page before rewriting.", weight=2))
    else:
        out.append(_check("About length", PASS,
                          f"~{len(about)}/{limit} characters", weight=2))

    demos = [item.get("demo", "") for item in p.get("proof", []) if item.get("demo")]
    linked = [d for d in demos if d and d.split("//")[-1].split("/")[0] in about]
    if linked:
        out.append(_check("Proof in About", PASS,
                          f"{len(linked)} of {len(demos)} platforms referenced"))
    else:
        out.append(_check(
            "Proof in About", WARN, "no platform links found",
            "Name the platforms you shipped. Claims without artefacts read as "
            "aspiration; a live URL ends the argument."))
    return out


def _structure_checks(rec: dict[str, Any], p: dict[str, Any]) -> list[dict[str, Any]]:
    out = []

    location = (rec.get("location") or "").strip()
    out.append(_check("Location", PASS, location) if location else _check(
        "Location", FAIL, "not set",
        f"Set it to {p.get('location', 'your city')}. Location is a hard "
        "filter in most recruiter and buyer searches — an unset location "
        "removes you from the result set entirely."))

    slug = (rec.get("slug") or "").strip().lower()
    if not slug:
        out.append(_check("Custom URL", WARN, "unknown", ""))
    elif RE_AUTO_SLUG.search(slug) and _digits(slug) >= 3:
        out.append(_check(
            "Custom URL", WARN, f"auto-assigned: /in/{slug}",
            "Claim a clean vanity URL under Edit public profile & URL. It goes "
            "on your email signature, business card and proposals."))
    else:
        out.append(_check("Custom URL", PASS, f"/in/{slug}"))

    exp = rec.get("experience") or []
    if not exp:
        out.append(_check(
            "Experience", FAIL, "no entries parsed",
            "Add the current role at minimum, with a description.", weight=2))
    else:
        titled = [e for e in exp if e.get("title")]
        out.append(_check(
            "Experience", PASS if titled else WARN,
            f"{len(exp)} entr{'y' if len(exp) == 1 else 'ies'}, "
            f"{len(titled)} with a title",
            "" if titled else "Entries are missing job titles.", weight=2))

    edu = rec.get("education") or []
    out.append(_check("Education", PASS, f"{len(edu)} entries") if edu else _check(
        "Education", WARN, "none parsed",
        "Add the MBA and the BEng — the combination is the differentiator, and "
        "neither one alone tells the story."))

    followers = (rec.get("followers") or "").strip()
    out.append(_check("Followers", PASS, followers) if followers else _check(
        "Followers", WARN, "not reported", ""))

    return out


def audit(rec: dict[str, Any], p: dict[str, Any]) -> dict[str, Any]:
    """Run every check and return the checks plus a weighted score."""
    checks = [
        *_headline_checks(rec, p),
        *_about_checks(rec, p),
        *_structure_checks(rec, p),
    ]
    points = {PASS: 1.0, WARN: 0.5, FAIL: 0.0}
    earned = sum(points[c["status"]] * c["weight"] for c in checks)
    total = sum(c["weight"] for c in checks)
    return {
        "score": round(100 * earned / total, 1) if total else 0.0,
        "checks": checks,
        "counts": {s: sum(1 for c in checks if c["status"] == s)
                   for s in (PASS, WARN, FAIL)},
    }
