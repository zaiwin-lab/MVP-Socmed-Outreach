"""Turn a raw CIDB pull into call-ready batches, one per caller.

Ordering matters: contractors closest to the venue are called first, because
proximity is the strongest predictor of actually turning up. Within that,
grades are interleaved so every caller gets the same mix rather than one person
getting all the hardest calls.

Usage:
    python3 -m scout.split_batches raw.csv --callers 4 --out-dir batches/
"""

from __future__ import annotations

import argparse
import csv
import re
from collections import defaultdict
from pathlib import Path

# Distance from Pusat Konvensyen CIDB Sarawak, nearest first.
DISTRICT_PRIORITY = {"KUCHING": 0, "SAMARAHAN": 1, "ASAJAYA": 2, "BAU": 3, "SERIAN": 4}

CALL_COLUMNS = [
    "no", "company", "grade", "district", "phone", "email",
    "bil_syarikat", "syarikat_lain", "cidb_id",
    # Filled in by the caller:
    "status", "nama_peserta", "no_hp_peserta", "email_peserta",
    "tarikh_call", "catatan",
]


def normalise_phone(raw: str) -> str:
    """Malaysian mobile/landline to a consistent 0XX-XXXXXXX shape."""
    digits = re.sub(r"\D", "", raw or "")
    if not digits:
        return ""
    if digits.startswith("60"):
        digits = "0" + digits[2:]
    if not digits.startswith("0"):
        digits = "0" + digits
    if len(digits) < 9 or len(digits) > 12:
        return ""  # implausible — flag by emptying
    return f"{digits[:3]}-{digits[3:]}"


def load(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def dedupe(rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], int]:
    """One record per phone number — a firm listed twice is still one call.

    Where one number covers several registered companies it is the same owner,
    which is a selling point rather than noise: he can send more than one
    person. The extra company names are kept on the surviving record.
    """
    first: dict[str, dict[str, str]] = {}
    extras: dict[str, list[str]] = defaultdict(list)
    order_keys: list[str] = []
    dropped = 0

    for r in rows:
        phone = normalise_phone(r.get("phone", ""))
        company = (r.get("company") or "").strip()
        if not company:
            dropped += 1
            continue
        key = phone or f"name:{company.upper()}"
        r["phone"] = phone
        if key not in first:
            first[key] = r
            order_keys.append(key)
        else:
            dropped += 1
            if company.upper() != first[key]["company"].strip().upper():
                extras[key].append(company)

    out: list[dict[str, str]] = []
    for key in order_keys:
        rec = first[key]
        others = extras.get(key, [])
        if others:
            rec["syarikat_lain"] = "; ".join(dict.fromkeys(others))
            rec["bil_syarikat"] = str(len(others) + 1)
        else:
            rec["syarikat_lain"] = ""
            rec["bil_syarikat"] = "1"
        out.append(rec)
    return out, dropped


def order(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    """Nearest district first; interleave grades within each district."""
    by_district: dict[int, dict[str, list[dict[str, str]]]] = defaultdict(
        lambda: defaultdict(list))
    for r in rows:
        d = (r.get("district") or "").strip().upper()
        by_district[DISTRICT_PRIORITY.get(d, 9)][(r.get("grade") or "").upper()].append(r)

    ordered: list[dict[str, str]] = []
    for prio in sorted(by_district):
        grade_buckets = by_district[prio]
        keys = sorted(grade_buckets, reverse=True)  # G3, G2, G1
        i = 0
        while any(grade_buckets[k] for k in keys):
            k = keys[i % len(keys)]
            if grade_buckets[k]:
                ordered.append(grade_buckets[k].pop(0))
            i += 1
    return ordered


def write_batches(rows: list[dict[str, str]], callers: int, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    batches: list[list[dict[str, str]]] = [[] for _ in range(callers)]

    # Round-robin so every caller gets the same quality of list, top to bottom.
    for i, r in enumerate(rows):
        r = {**r, "no": i + 1,
             "status": "TO CALL", "nama_peserta": "", "no_hp_peserta": "",
             "email_peserta": "", "tarikh_call": "", "catatan": ""}
        batches[i % callers].append(r)

    for n, batch in enumerate(batches, start=1):
        path = out_dir / f"caller_{n}.csv"
        with path.open("w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=CALL_COLUMNS, extrasaction="ignore")
            w.writeheader()
            w.writerows(batch)
        print(f"  caller_{n}.csv  {len(batch):>5} contractors")

    master = out_dir / "MASTER_all_contractors.csv"
    with master.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=CALL_COLUMNS, extrasaction="ignore")
        w.writeheader()
        for i, r in enumerate(rows):
            w.writerow({**r, "no": i + 1, "status": "TO CALL"})
    print(f"  MASTER_all_contractors.csv  {len(rows):>5} contractors")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("raw_csv")
    p.add_argument("--callers", type=int, default=4)
    p.add_argument("--out-dir", default="batches")
    p.add_argument("--limit", type=int, help="cap the total (e.g. 800 for the campaign)")
    args = p.parse_args(argv)

    rows = load(Path(args.raw_csv))
    print(f"  loaded          {len(rows)}")

    rows, dropped = dedupe(rows)
    print(f"  after dedupe    {len(rows)}  ({dropped} removed)")

    # A call sheet must only contain numbers a caller can actually dial.
    # The registry carries placeholder values ("0") and truncated numbers.
    callable_rows = [r for r in rows if r["phone"]]
    unreachable = [r for r in rows if not r["phone"]]
    if unreachable:
        print(f"  ! {len(unreachable)} records have no usable phone number "
              f"— held out of the call sheets")
        out_dir = Path(args.out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        with (out_dir / "NO_PHONE_email_only.csv").open(
                "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=CALL_COLUMNS, extrasaction="ignore")
            w.writeheader()
            w.writerows(unreachable)
    rows = callable_rows

    rows = order(rows)
    if args.limit:
        rows = rows[:args.limit]
        print(f"  capped to       {len(rows)}")

    print()
    write_batches(rows, args.callers, Path(args.out_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
