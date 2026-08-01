"""Caller grouping PDF — one call sheet per caller, printable."""

from __future__ import annotations

import csv
from pathlib import Path

from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import PageBreak, Paragraph, Spacer

from .make_pdf import (GOLD, NAVY, RED, WIDTH_LANDSCAPE, P, S, build_doc,
                       callout, fit, kpi_row, table)

ROWS_PER_CALLER_PAGE = 26


def _load(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _cover(batches: dict[str, list[dict[str, str]]], total: int) -> list:
    s: list = []
    s.append(P("Caller Grouping — Call Sheets", "h1"))
    s.append(P("IECONS 2026 Delegate Drive  •  4 callers  •  100 calls per caller "
               "per day  •  Kuching district, CIDB Grade G1–G3", "sub"))

    s.append(kpi_row([
        ("CALLERS", "4"),
        ("CONTACTS ISSUED", f"{total:,}"),
        ("PER CALLER", f"~{total // 4}"),
        ("CALLS / DAY EACH", "100"),
        ("TEAM TARGET", "75 confirmed"),
    ]))
    s.append(Spacer(1, 10))

    s.append(P("How the lists were built", "h3"))
    s.append(table([
        ["Rule", "Why"],
        ["Kuching district only",
         "Proximity to Pusat Konvensyen CIDB Sarawak is the strongest predictor of "
         "actually turning up on the day."],
        ["Grades interleaved (G3, G2, G1)",
         "Every caller gets the same mix. Nobody is handed all the hardest calls."],
        ["Round-robin allocation",
         "Lists are equal in quality from top to bottom, not just in length."],
        ["Deduplicated by phone number",
         "One number is one phone call, even where it covers several registered "
         "companies."],
        ["Unreachable numbers removed",
         "The registry carries placeholder and truncated numbers. These are held in "
         "NO_PHONE_email_only.csv, not in your sheet."],
    ], fit([130, None], WIDTH_LANDSCAPE)))

    s.append(callout(
        "WORK YOUR LIST FROM THE TOP",
        "The list is already in priority order. Do not skip ahead or cherry-pick "
        "familiar names — the ordering is what keeps the four lists equal, and it "
        "is how the Team Lead reads progress across the team."))

    s.append(P("The bil_syarikat column", "h3"))
    s.append(P(
        "Where a single phone number covers more than one registered company, "
        "<b>bil_syarikat</b> shows how many, and <b>syarikat_lain</b> names the "
        "others. That is the same owner. He can send more than one attendee — ask "
        "for it. These are the cheapest extra seats on the list."))

    s.append(callout(
        "DAILY MATHS",
        "100 calls a day is roughly five hours on the telephone: about 55 calls in "
        "the 9.00 a.m. – 12.30 p.m. window and 45 in the 2.30 – 5.30 p.m. window. "
        "Log each outcome as the call ends, not at the end of the day.", RED))

    s.append(P("Status values to use", "h3"))
    s.append(table([
        ["Status", "Meaning"],
        ["TO CALL", "Not yet attempted"],
        ["NO ANSWER", "Rang, no pick-up — try again in the other window"],
        ["INTERESTED", "Said yes by voice — send the registration link now"],
        ["LINK SENT", "Link delivered, waiting for the form"],
        ["CONFIRMED", "Form submitted and verified — this is the only status that counts"],
        ["DECLINED", "Said no — record the reason in catatan"],
        ["DO NOT CONTACT", "Asked not to be called again — stop entirely, no messages"],
    ], fit([90, None], WIDTH_LANDSCAPE)))
    return s


def _sheet(name: str, rows: list[dict[str, str]]) -> list:
    s: list = [PageBreak()]
    s.append(P(f"{name.replace('_', ' ').title()} — Call Sheet", "h1"))
    s.append(P(f"{len(rows)} contractors  •  target 100 calls per day  •  "
               f"work from the top", "sub"))

    header = ["No", "Company", "Gred", "Phone", "Email", "Coy",
              "Status", "Nama Peserta / Catatan"]
    data = [header]
    for r in rows:
        data.append([
            r.get("no", ""),
            Paragraph(r.get("company", "")[:46], S["cell"]),
            r.get("grade", ""),
            Paragraph(f"<b>{r.get('phone','')}</b>", S["cell"]),
            Paragraph(r.get("email", "")[:34], S["tiny"]),
            r.get("bil_syarikat", "1"),
            "", "",
        ])

    s.append(table(data, fit([22, 168, 24, 60, 148, 20, 58, None], WIDTH_LANDSCAPE),
                   align={0: "CENTER", 2: "CENTER", 5: "CENTER"},
                   font_size=7.2, pad=2.2))
    return s


def build(batch_dir: Path, out: Path) -> int:
    files = sorted(batch_dir.glob("caller_*.csv"))
    if not files:
        raise SystemExit(f"no caller_*.csv found in {batch_dir}")

    batches = {f.stem: _load(f) for f in files}
    total = sum(len(v) for v in batches.values())

    story = _cover(batches, total)
    for name, rows in batches.items():
        story += _sheet(name, rows)

    build_doc(out, story, page=landscape(A4))
    print(f"  wrote {out}  ({total} contacts across {len(batches)} callers)")
    return 0
