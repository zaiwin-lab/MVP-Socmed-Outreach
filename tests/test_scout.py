"""Offline tests — no network. Run: python3 -m tests.test_scout (or pytest)."""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scout import parse_linkedin, score  # noqa: E402

FIXTURE = Path(__file__).parent / "fixtures" / "linkedin_public_profile.html"
PROFILE_URL = "https://www.linkedin.com/in/williamhgates/"


def _rec():
    return parse_linkedin.parse(FIXTURE.read_text(encoding="utf-8"), PROFILE_URL)


def test_parses_identity():
    rec = _rec()
    assert rec["source"] == "json-ld"
    assert rec["name"] == "Bill Gates"
    assert rec["slug"] == "williamhgates"
    assert "Gates Foundation" in rec["headline"]


def test_location_is_not_double_suffixed():
    rec = _rec()
    assert rec["location"] == "Seattle, Washington, United States"
    assert not rec["location"].endswith(", US")


def test_experience_has_titles_companies_and_dates():
    rec = _rec()
    exp = rec["experience"]
    assert len(exp) >= 3
    assert exp[0]["company"] == "Gates Foundation"
    assert exp[0]["title"] == "Co-chair"
    assert exp[0]["start"] == 2000
    companies = {e["company"] for e in exp}
    assert "Microsoft" in companies


def test_career_span_does_not_stack_concurrent_roles():
    rec = _rec()
    # Earliest start is 1975 and roles are ongoing, so span runs to this year.
    assert rec["career_span_years"] == date.today().year - 1975
    # The old bug summed overlapping roles into an impossible total.
    assert rec["career_span_years"] < 100


def test_education_parsed():
    rec = _rec()
    assert rec["education"][0]["name"] == "Harvard University"
    assert rec["education"][0]["end"] == 1975


def test_public_profile_is_not_gated():
    assert parse_linkedin.is_gated(FIXTURE.read_text(encoding="utf-8")) is False


def test_authwall_is_detected():
    assert parse_linkedin.is_gated("<html>authwall — please sign in</html>") is True


def test_scoring_rejects_an_irrelevant_candidate():
    role = {
        "role": "Digital Marketing Executive",
        "location_hint": ["Kuching", "Sarawak", "Malaysia"],
        "must_have": ["digital marketing", "social media", "meta ads"],
        "nice_to_have": ["seo", "copywriting"],
        "exclude": [],
    }
    result = score.score(_rec(), role)
    assert result["score"] == 0.0
    assert len(result["missing"]) == 3
    assert "location not confirmed against brief" in result["flags"]


def test_scoring_rewards_a_matching_candidate():
    role = {
        "role": "Digital Marketing Executive",
        "location_hint": ["Kuching"],
        "must_have": ["digital marketing", "social media"],
        "nice_to_have": ["seo"],
        "exclude": [],
    }
    candidate = {
        "headline": "Digital Marketing Lead",
        "about": "I run social media and SEO for regional brands.",
        "location": "Kuching, Sarawak, Malaysia",
        "current_title": "Digital Marketing Lead",
        "current_company": "Acme",
        "experience": [{"title": "Digital Marketing Lead", "company": "Acme"}],
        "education": [],
    }
    result = score.score(candidate, role)
    assert result["score"] == 100.0
    assert result["missing"] == []
    assert result["matched"]["location"] == ["Kuching"]


def test_word_boundary_prevents_false_positives():
    role = {"must_have": ["seo"], "nice_to_have": [], "exclude": [], "location_hint": []}
    candidate = {"headline": "Analyst based in Seoul", "about": "", "experience": [],
                 "education": [], "location": "Seoul"}
    assert score.score(candidate, role)["score"] == 0.0


def test_exclusion_signal_penalises():
    role = {"must_have": ["marketing"], "nice_to_have": [], "exclude": ["intern"],
            "location_hint": []}
    candidate = {"headline": "Marketing intern", "about": "", "experience": [],
                 "education": [], "location": ""}
    result = score.score(candidate, role)
    assert result["score"] < 55
    assert any("exclusion" in f for f in result["flags"])


def _run() -> int:
    tests = [(n, f) for n, f in sorted(globals().items())
             if n.startswith("test_") and callable(f)]
    failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"  PASS  {name}")
        except AssertionError as e:
            failed += 1
            print(f"  FAIL  {name}: {e}")
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"  ERROR {name}: {type(e).__name__}: {e}")
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(_run())
