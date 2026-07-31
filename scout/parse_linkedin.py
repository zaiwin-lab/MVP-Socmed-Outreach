"""Turn a public LinkedIn profile page into a structured candidate record.

Primary source is the JSON-LD `Person` node LinkedIn embeds in every public
profile — the same structured data it hands search engines. It carries name,
headline, location, roles with start/end years, education with years, and
follower counts, which is plenty for hiring triage.

Falls back to markdown/HTML heuristics when JSON-LD is absent (older pages,
or when the body came from Jina Reader instead of a direct fetch).

Anything behind "Sign in to view" is not public, is not fetched, and is left
empty rather than guessed at.
"""

from __future__ import annotations

import html as html_mod
import json
import re
from datetime import date
from typing import Any

RE_LDJSON = re.compile(
    r'<script[^>]+type="application/ld\+json"[^>]*>(.*?)</script>', re.S | re.I)
RE_TITLE_TAG = re.compile(r"<title>(.*?)</title>", re.S | re.I)
RE_TITLE_MD = re.compile(r"^Title:\s*(.+?)\s*$", re.M)
RE_SLUG = re.compile(r"linkedin\.com/in/([A-Za-z0-9\-_%\.]+)")
RE_TAGS = re.compile(r"<[^>]+>")

# Markdown-fallback patterns (Jina Reader output).
RE_LOCATION_MD = re.compile(r"^###\s+(.+?)\s*Contact Info\s*$", re.M)
RE_COUNTS_MD = re.compile(r"([\d,.]+[KMB]?)\s+followers?", re.I)
RE_MD_LINK = re.compile(r"\[([^\]]+)\]\([^)]*\)")
RE_MD_IMAGE = re.compile(r"!\[[^\]]*\]\([^)]*\)")


def _clean(text: str) -> str:
    text = RE_MD_IMAGE.sub("", text)
    text = RE_MD_LINK.sub(r"\1", text)
    text = RE_TAGS.sub(" ", text)
    return re.sub(r"\s+", " ", html_mod.unescape(text)).strip()


def _strip_suffix(title: str) -> str:
    """`Bill Gates - Chair, Gates Foundation | LinkedIn` -> name + headline."""
    return re.sub(r"\s*\|\s*LinkedIn\s*$", "", title).strip()


def _split_name_headline(title: str) -> tuple[str, str]:
    parts = _strip_suffix(title).split(" - ", 1)
    if len(parts) == 2:
        return parts[0].strip(), parts[1].strip()
    return parts[0].strip(), ""


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def _find_person(body: str) -> dict[str, Any] | None:
    for block in RE_LDJSON.findall(body):
        try:
            data = json.loads(block.strip())
        except json.JSONDecodeError:
            continue
        nodes = data.get("@graph", []) if isinstance(data, dict) else []
        if isinstance(data, dict) and data.get("@type") == "Person":
            nodes = [data, *nodes]
        for node in nodes:
            if isinstance(node, dict) and node.get("@type") == "Person":
                return node
    return None


def _org_entries(items: list[Any], role_key: str) -> list[dict[str, Any]]:
    """Normalise worksFor / alumniOf into {name, title?, start, end}."""
    out: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        member = item.get("member") or {}
        if isinstance(member, list):
            member = member[0] if member else {}
        entry = {
            "name": (item.get("name") or "").strip(),
            "url": item.get("url", ""),
            "start": member.get("startDate"),
            "end": member.get("endDate"),
        }
        if role_key in item:
            entry["title"] = item.get(role_key, "")
        if entry["name"]:
            out.append(entry)
    return out


def _years(entry: dict[str, Any]) -> float | None:
    start, end = entry.get("start"), entry.get("end")
    if not isinstance(start, int):
        return None
    finish = end if isinstance(end, int) else date.today().year
    return max(0, finish - start)


def _from_jsonld(person: dict[str, Any], body: str, url: str) -> dict[str, Any]:
    title_m = RE_TITLE_TAG.search(body)
    _, headline = _split_name_headline(_clean(title_m.group(1))) if title_m else ("", "")

    address = person.get("address") or {}
    if isinstance(address, list):
        address = address[0] if address else {}
    locality = (address.get("addressLocality") or "").strip()
    country = (address.get("addressCountry") or "").strip()
    # Locality is usually already fully qualified ("Kuching, Sarawak, Malaysia").
    # Only fall back to the bare country code when it clearly is not.
    location = locality
    if country and "," not in locality:
        location = f"{locality}, {country}".strip(", ")

    works = _org_entries(_as_list(person.get("worksFor")), "description")
    schools = _org_entries(_as_list(person.get("alumniOf")), "description")
    job_titles = [t for t in _as_list(person.get("jobTitle")) if isinstance(t, str)]

    followers = ""
    stat = person.get("interactionStatistic")
    if isinstance(stat, dict):
        count = stat.get("userInteractionCount")
        if isinstance(count, int):
            followers = str(count)

    # Pair job titles with employers positionally — LinkedIn emits them in
    # matching order, and a missing pair is better left blank than invented.
    experience = []
    for i, org in enumerate(works):
        experience.append({
            "title": job_titles[i] if i < len(job_titles) else org.get("title", ""),
            "company": org["name"],
            "start": org.get("start"),
            "end": org.get("end"),
            "years": _years(org),
        })

    profile_url = person.get("url") or url
    slug_m = RE_SLUG.search(profile_url) or RE_SLUG.search(url)

    return {
        "platform": "linkedin",
        "source": "json-ld",
        "slug": slug_m.group(1) if slug_m else "",
        "url": profile_url,
        "name": (person.get("name") or "").strip(),
        "headline": headline,
        "location": location,
        "current_company": experience[0]["company"] if experience else "",
        "current_title": experience[0]["title"] if experience else "",
        "followers": followers,
        "about": _clean(person.get("description") or "")[:1500],
        "badges": _clean(person.get("disambiguatingDescription") or ""),
        "languages": [l for l in _as_list(person.get("knowsLanguage")) if isinstance(l, str)],
        "experience": experience[:10],
        "education": [
            {"name": s["name"], "start": s.get("start"), "end": s.get("end")}
            for s in schools[:5]
        ],
        # Career span, not a sum — concurrent roles must not stack.
        "career_span_years": _career_span(experience),
    }


def _career_span(experience: list[dict[str, Any]]) -> int | None:
    """Years from the earliest known start to the latest end (or today)."""
    starts = [e["start"] for e in experience if isinstance(e.get("start"), int)]
    if not starts:
        return None
    ends = [e["end"] for e in experience if isinstance(e.get("end"), int)]
    ongoing = any(e.get("end") is None for e in experience)
    latest = date.today().year if ongoing or not ends else max(ends)
    return max(0, latest - min(starts))


def _from_markdown(body: str, url: str) -> dict[str, Any]:
    """Heuristic fallback for Jina Reader markdown (no JSON-LD present)."""
    title_m = RE_TITLE_MD.search(body) or RE_TITLE_TAG.search(body)
    name, headline = _split_name_headline(_clean(title_m.group(1))) if title_m else ("", "")

    loc_m = RE_LOCATION_MD.search(body)
    counts_m = RE_COUNTS_MD.search(body)
    slug_m = RE_SLUG.search(url) or RE_SLUG.search(body)

    return {
        "platform": "linkedin",
        "source": "markdown",
        "slug": slug_m.group(1) if slug_m else "",
        "url": url,
        "name": name,
        "headline": headline,
        "location": _clean(loc_m.group(1)) if loc_m else "",
        "current_company": "",
        "current_title": "",
        "followers": counts_m.group(1) if counts_m else "",
        "about": "",
        "badges": "",
        "languages": [],
        "experience": [],
        "education": [],
        "career_span_years": None,
    }


def parse(body: str, url: str = "") -> dict[str, Any]:
    person = _find_person(body)
    if person:
        return _from_jsonld(person, body, url)
    return _from_markdown(body, url)


def is_gated(body: str) -> bool:
    """True when LinkedIn served an auth wall instead of a public profile."""
    if _find_person(body):
        return False
    lowered = body.lower()
    if "authwall" in lowered:
        return True
    return "sign in to view" in lowered and "experience" not in lowered
