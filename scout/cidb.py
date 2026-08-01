"""Pull CIDB-registered contractors from the public MCP contractor search.

Source: https://mcp.cidb.gov.my/MCP/ContractorSearch — the public registry every
Malaysian contractor must appear in. Results carry company name, grade, state,
phone and email.

Public registry, logged-out access, rate limited. Same boundaries as the rest of
this toolkit: no login, no session replay, no auth-wall circumvention.
"""

from __future__ import annotations

import html as html_mod
import re
import time
import subprocess
import urllib.parse
import urllib.request
from typing import Any, Iterator

SEARCH_URL = "https://mcp.cidb.gov.my/MCP/ContractorSearch"
DISTRICT_URL = "https://mcp.cidb.gov.my/MCP/FilterDistrict"

BROWSER_UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

# State codes as used by the search form.
STATES = {
    "JOHOR": "12", "KEDAH": "6", "KELANTAN": "1", "MELAKA": "9",
    "NEGERI SEMBILAN": "5", "PAHANG": "10", "PERAK": "4", "PERLIS": "14",
    "PULAU PINANG": "7", "SABAH": "11", "SARAWAK": "13", "SELANGOR": "2",
    "TERENGGANU": "3", "KUALA LUMPUR": "16", "LABUAN": "15",
}

# Grade label -> form value. Note the form value is NOT the grade number.
GRADES = {"G7": "1", "G6": "2", "G5": "3", "G4": "4", "G3": "5", "G2": "6", "G1": "7"}

CATEGORIES = {"BUILDING": "1", "CIVIL": "2", "MECHANICAL_ELECTRICAL": "3",
              "FACILITY_MANAGEMENT": "4"}

RE_ROW = re.compile(r"<tr[^>]*>(.*?)</tr>", re.S)
RE_CELL = re.compile(r"<td[^>]*>(.*?)</td>", re.S)
RE_TAGS = re.compile(r"<[^>]+>")
RE_POPVIEW = re.compile(r"popview\('([^']*)'\s*,\s*'([^']*)'\)")
RE_TOTALPAGES = re.compile(r'name="TotalPages"[^>]*value="(\d+)"')
RE_OPTION = re.compile(r'"Text":"([^"]*)","Value":"([^"]*)"')


def _clean(fragment: str) -> str:
    return re.sub(r"\s+", " ", html_mod.unescape(RE_TAGS.sub(" ", fragment))).strip()


def _post(url: str, fields: dict[str, str], timeout: int = 45,
          retries: int = 4) -> str:
    """POST with retry.

    Uses curl rather than urllib: the registry drops keep-alive connections in a
    way that leaves urllib blocked on read until the full timeout, turning a
    4-second page into an 8-minute stall. curl handles the reset cleanly.
    """
    body = urllib.parse.urlencode(fields)
    last = ""
    for attempt in range(retries):
        try:
            proc = subprocess.run(
                ["curl", "-sS", "--max-time", str(timeout),
                 "--connect-timeout", "15", "--compressed",
                 "-H", f"User-Agent: {BROWSER_UA}",
                 "-H", "Content-Type: application/x-www-form-urlencoded",
                 "-H", "Accept: text/html,application/xhtml+xml,*/*;q=0.8",
                 "-H", "Origin: https://mcp.cidb.gov.my",
                 "-H", f"Referer: {SEARCH_URL}",
                 "-H", "Connection: close",
                 "--data-raw", body, url],
                capture_output=True, text=True,
                # curl's own --max-time does not cover a stall in the outbound
                # proxy handshake, so bound the process itself as well.
                timeout=timeout + 15)
            if proc.returncode == 0 and proc.stdout.strip():
                return proc.stdout
            last = proc.stderr.strip() or f"curl exit {proc.returncode}"
        except subprocess.TimeoutExpired:
            last = f"curl hung past {timeout + 15}s (killed)"
        if attempt < retries - 1:
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"CIDB request failed after {retries} attempts: {last}")


def districts(state: str = "SARAWAK") -> dict[str, str]:
    """Return {district name: code} for a state."""
    state_id = STATES.get(state.upper(), state)
    body = _post(DISTRICT_URL, {"stateId": state_id})
    out: dict[str, str] = {}
    for text, value in RE_OPTION.findall(body):
        if value and text.strip().lower() != "please select":
            out[text.strip().upper()] = value
    return out


def _parse_rows(body: str, district: str, grade_label: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for raw in RE_ROW.findall(body):
        cells = [_clean(c) for c in RE_CELL.findall(raw)]
        if len(cells) < 4 or not cells[0]:
            continue
        pv = RE_POPVIEW.search(raw)
        email, company_id = (pv.group(1), pv.group(2)) if pv else ("", "")
        rows.append({
            "company": cells[0],
            "grade": cells[1],
            "state": cells[2],
            "phone": cells[3],
            "email": email if "@" in email else "",
            "cidb_id": company_id,
            "district": district,
            "queried_grade": grade_label,
        })
    return rows


def fetch_page(state_id: str, district_id: str, grade_value: str,
               page: int, page_size: int = 100) -> tuple[list[dict[str, Any]], int]:
    """Fetch one page. Returns (rows, total_pages)."""
    body = _post(SEARCH_URL, {
        "ComName": "", "CidbRegNo": "",
        "State": state_id, "District": district_id,
        "Grade": grade_value, "Category": "", "Specialization": "", "ConType": "",
        "PageSize": str(page_size), "CtPage": str(page), "SortExp": "",
    })
    tp = RE_TOTALPAGES.search(body)
    return body, int(tp.group(1)) if tp else 0


def pull(state: str, district_name: str, grades: list[str], *,
         page_size: int = 100, delay: float = 2.0,
         max_pages: int = 60, log=print) -> Iterator[dict[str, Any]]:
    """Yield contractor records for a district across the given grades."""
    state_id = STATES.get(state.upper(), state)
    dist_map = districts(state)
    district_id = dist_map.get(district_name.upper())
    if not district_id:
        raise ValueError(f"unknown district {district_name!r} in {state}. "
                         f"Known: {', '.join(sorted(dist_map))}")

    for grade_label in grades:
        grade_value = GRADES.get(grade_label.upper())
        if not grade_value:
            raise ValueError(f"unknown grade {grade_label!r}")

        page = 1
        total_pages = None
        while True:
            try:
                body, tp = fetch_page(state_id, district_id, grade_value,
                                      page, page_size)
            except RuntimeError as e:
                # One bad page must not abort a run of thousands of records.
                log(f"    ! {district_name} {grade_label} page {page} skipped: {e}")
                page += 1
                if total_pages is not None and page > min(total_pages, max_pages):
                    break
                if total_pages is None:
                    break
                time.sleep(delay)
                continue

            if total_pages is None:
                # TotalPages is already expressed in the page size we requested.
                total_pages = max(1, tp)
                log(f"    {district_name} {grade_label}: {total_pages} page(s) "
                    f"@ {page_size} (up to ~{total_pages * page_size})")

            rows = _parse_rows(body, district_name.title(), grade_label.upper())
            if not rows:
                break
            yield from rows

            page += 1
            if page > min(total_pages, max_pages):
                break
            time.sleep(delay)

        time.sleep(delay)
