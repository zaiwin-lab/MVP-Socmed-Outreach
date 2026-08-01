"""Render one professional persona into platform-native profile copy.

The premise: your GitHub profile README, your LinkedIn and your Facebook should
say the same thing in three different registers. Keeping three hand-written
profiles in sync fails the moment you ship something new — so the positioning
lives in one JSON file and each platform is rendered from it.

    persona/zaiwin.json  ->  LinkedIn headline / About / Experience / Skills
                         ->  Facebook bio / intro / Page description

Every field carries the platform's real character limit and is checked against
it. LinkedIn silently truncates an over-long headline in search results rather
than rejecting it, so an unchecked 240-character headline looks fine while you
are editing it and gets cut mid-word everywhere it actually matters.

Nothing here touches a logged-in session. It produces text you paste in.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

# Platform limits, in characters. Verified against the live editors — these are
# the values the field itself enforces, not the guidance in help articles.
LIMITS = {
    "linkedin_headline": 220,
    "linkedin_about": 2600,
    "linkedin_experience": 2000,
    "facebook_bio": 101,
    "facebook_page_description": 255,
}

# LinkedIn ranks and displays the first three skills differently from the rest;
# it caps the list at 50.
LINKEDIN_SKILL_CAP = 50
LINKEDIN_PINNED_SKILLS = 3


def load(path: str | Path) -> dict[str, Any]:
    """Read a persona JSON file."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    missing = [k for k in ("name", "positioning", "current_role") if k not in data]
    if missing:
        raise ValueError(f"persona file missing required key(s): {', '.join(missing)}")
    return data


def _field(label: str, text: str, limit_key: str | None = None,
           note: str = "") -> dict[str, Any]:
    """One paste-ready block, measured against its platform limit."""
    limit = LIMITS.get(limit_key or "", 0)
    return {
        "label": label,
        "text": text,
        "limit": limit,
        "used": len(text),
        "over": len(text) - limit if limit and len(text) > limit else 0,
        "note": note,
    }


def _full_name(p: dict[str, Any]) -> str:
    honorific = p.get("honorific", "").strip()
    return f"{honorific} {p['name']}".strip()


def _education_short(p: dict[str, Any]) -> str:
    """'Master of Business Administration' -> 'MBA', for headline use."""
    short = []
    for line in p.get("education", []):
        low = line.lower()
        if "business administration" in low:
            short.append("MBA")
        elif "mechatronic" in low:
            short.append("BEng Mechatronics")
        else:
            short.append(line)
    return " · ".join(short)


# --------------------------------------------------------------------- LinkedIn

def linkedin_headlines(p: dict[str, Any]) -> list[dict[str, Any]]:
    """Three headlines with different strategies — pick one, do not merge them.

    Merging them is the common failure: you end up at 240 characters, LinkedIn
    truncates, and the part that gets cut is the part you added last.
    """
    role = p["current_role"]
    pos = p["positioning"]
    anchor = f"{role['title']}, {role['company']}"
    shipped = len(p.get("proof", []))
    titles = pos.get("titles", [])

    # The one-liner ends with a full stop in prose; a headline is not a sentence.
    hook = pos["one_liner"].rstrip(".")

    authority = " | ".join(filter(None, [
        anchor,
        titles[0] if titles else "",
        hook,
        _education_short(p),
        p.get("location_short", ""),
    ]))

    outcome = " | ".join(filter(None, [
        f"{hook} — {shipped} shipped, all live" if shipped else hook,
        "Digital Product Strategy · Solution Architecture · Programme Innovation",
        anchor,
    ]))

    searchable = " | ".join(filter(None, [
        "Digital Product Strategist",
        "Solution Architect",
        "Programme Innovation",
        "Rapid MVP",
        "AI-Enabled Delivery",
        anchor,
        p.get("location_short", ""),
    ]))

    return [
        _field("Headline A — authority-led", authority, "linkedin_headline",
               "Leads with the title. Best when the room already knows KOBIS."),
        _field("Headline B — outcome-led", outcome, "linkedin_headline",
               "Leads with what you deliver. Best for people meeting you cold. "
               "Recommended."),
        _field("Headline C — search-led", searchable, "linkedin_headline",
               "Keyword-dense for LinkedIn search. Reads flatter to a human, "
               "ranks better for recruiters and procurement."),
    ]


def linkedin_about(p: dict[str, Any]) -> dict[str, Any]:
    """The About section.

    LinkedIn collapses this after roughly the first three lines behind a
    '...see more' link, so the first 250 characters carry the whole load. The
    hook and the proof go first; the credentials go last.
    """
    pos = p["positioning"]
    role = p["current_role"]
    parts: list[str] = [
        pos["one_liner"],
        "",
        pos.get("sharper_one_liner", ""),
        "",
    ]

    proof = p.get("proof", [])
    if proof:
        parts.append(f"{len(proof)} platforms shipped and live:")
        parts.append("")
        for item in proof:
            parts.append(f"→ {item['name']} — {item.get('short', item['outcome'])}")
        parts.append("")

    parts.append("WHAT I ACTUALLY DO")
    parts.append("")
    for cap in p.get("capabilities", []):
        parts.append(f"{cap['name']} — {cap['detail']}.")
    parts.append("")

    ai = p.get("ai_position", [])
    if ai:
        parts.append("ON AI")
        parts.append("")
        parts.extend(ai)
        parts.append("")

    parts.append(pos.get("motto", ""))
    parts.append("")
    parts.append("BACKGROUND")
    parts.append("")
    parts.append(
        f"{role['title']}, {role['company']}, leading the {role['team']} on "
        + ", ".join(role.get("covers", [])[:3]) + ".")
    parts.append("")
    parts.append(f"{_education_short(p)}. Based in {p.get('location', '')}.")
    parts.append("")
    parts.append(
        "The engineering background is why the systems hold together. The MBA "
        "is why they solve a business problem rather than an interesting "
        "technical one.")
    parts.append("")

    collab = p.get("collaboration", [])
    if collab:
        parts.append("OPEN TO")
        parts.append("")
        parts.append(" · ".join(collab).capitalize())
        parts.append("")

    if p.get("closing_hook"):
        parts.append(p["closing_hook"])

    text = "\n".join(parts).strip()
    # Collapse any run of blank lines the templating produced.
    while "\n\n\n" in text:
        text = text.replace("\n\n\n", "\n\n")

    return _field("About", text, "linkedin_about",
                  "First ~250 characters show before '...see more'. Everything "
                  "that must land is above the fold.")


def linkedin_experience(p: dict[str, Any]) -> dict[str, Any]:
    """The description under the current role."""
    role = p["current_role"]
    lines = [
        f"Leading the {role['team']} on "
        + ", ".join(role.get("covers", [])) + ".",
        "",
        "Selected platforms delivered:",
        "",
    ]
    for item in p.get("proof", []):
        lines.append(f"• {item['name']} — {item['outcome']}")
        if item.get("demo"):
            lines.append(f"  {item['demo']}")
    lines.append("")
    if p.get("stack"):
        lines.append("Stack: " + " · ".join(p["stack"]))

    return _field(f"Experience — {role['title']}, {role['company']}",
                  "\n".join(lines).strip(), "linkedin_experience",
                  "Paste into the description field of the role entry.")


def linkedin_skills(p: dict[str, Any]) -> dict[str, Any]:
    """Ordered skills list, capped and with the pinned three called out."""
    skills = p.get("skills_order", [])[:LINKEDIN_SKILL_CAP]
    pinned = skills[:LINKEDIN_PINNED_SKILLS]
    text = "\n".join(f"{i + 1:2}. {s}" for i, s in enumerate(skills))
    return _field("Skills", text, None,
                  f"Max {LINKEDIN_SKILL_CAP}. Pin the first three — they show on "
                  f"the profile itself and carry the most search weight: "
                  f"{', '.join(pinned)}.")


def linkedin_featured(p: dict[str, Any]) -> dict[str, Any]:
    """What to put in the Featured section, in order."""
    lines = []
    for i, item in enumerate(p.get("proof", []), 1):
        lines.append(f"{i}. {item['name']}")
        lines.append(f"   Link:  {item.get('demo', item.get('repo', ''))}")
        lines.append(f"   Title: {item['name']}")
        lines.append(f"   Desc:  {item.get('short', item['outcome'])}")
        lines.append("")
    if p.get("links", {}).get("github"):
        lines.append(f"{len(p.get('proof', [])) + 1}. GitHub profile")
        lines.append(f"   Link:  {p['links']['github']}")
        lines.append("   Title: Full portfolio and source")
        lines.append("   Desc:  Repositories, live deployments and delivery approach.")
    return _field("Featured section", "\n".join(lines).strip(), None,
                  "Featured is the highest-value real estate on the profile and "
                  "most people leave it empty. Link the live demo, not the repo — "
                  "a non-technical visitor will not click through a repo.")


def render_linkedin(p: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        *linkedin_headlines(p),
        linkedin_about(p),
        linkedin_experience(p),
        linkedin_featured(p),
        linkedin_skills(p),
    ]


# --------------------------------------------------------------------- Facebook

def render_facebook(p: dict[str, Any]) -> list[dict[str, Any]]:
    """Facebook copy.

    Facebook's professional surface is thin by comparison: a 101-character bio
    and a details block. The work is deciding what survives the cut.
    """
    pos = p["positioning"]
    role = p["current_role"]
    anchor = f"{role['title']}, {role['company']}"
    shipped = len(p.get("proof", []))

    bios = [
        _field("Bio A — authority", f"{anchor}. {pos['one_liner']}",
               "facebook_bio",
               "Recommended. Title first, because Facebook shows this under "
               "your name with no other context."),
        _field("Bio B — proof",
               f"Digital product strategist. {shipped} platforms shipped and "
               f"live. {p.get('location_short', '')}.",
               "facebook_bio", "Leads with evidence."),
        _field("Bio C — plain",
               "I build working digital platforms for programmes, training and "
               "community impact.",
               "facebook_bio", "No jargon. Best if your Facebook audience is "
               "mostly non-technical."),
    ]

    details = "\n".join([
        f"Works at {role['company']} — {role['title']}",
        f"Lives in {p.get('location', '')}",
        "Education:",
        *[f"  • {e}" for e in p.get("education", [])],
        f"Website: {p.get('links', {}).get('github', '')}",
    ])

    page_desc = (
        f"{pos['one_liner']} {role['team']} — "
        f"{role.get('team_tagline', '')} "
        f"Programme management, CRM, dashboards, training coordination and "
        f"community platforms. Based in {p.get('location_short', '')}."
    ).strip()

    return [
        *bios,
        _field("Intro → Details", details, None,
               "Profile → Edit details. Fill every line — an empty details "
               "block reads as an abandoned account."),
        _field("Page description (if you run a KOBIS Page)", page_desc,
               "facebook_page_description",
               "For a Page, not a personal profile. Keep the personal profile "
               "personal and the Page commercial."),
    ]


RENDERERS = {
    "linkedin": render_linkedin,
    "facebook": render_facebook,
}
