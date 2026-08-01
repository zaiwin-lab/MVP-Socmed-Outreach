"""Build the Kuching contractors masterlist workbook.

Tabs:
    README        how to use it, and which cells to fill in
    SCOREBOARD    live counts per caller, team total, milestone tracker
    MASTERLIST    all callable contractors, the single source of truth
    CALLER 1..4   each caller's own slice
    NAMELIST      auto-populates with CONFIRMED records — the SEA deliverable
    NO PHONE      records with unusable numbers, held out of the call sheets

Usage:
    python3 -m scout.make_xlsx batches/ --out MASTERLIST.xlsx
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from openpyxl import Workbook
from openpyxl.formatting.rule import CellIsRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

FONT = "Arial"
NAVY = "12263F"
LIGHT = "EEF2F7"
GOLD = "FFF4CC"
GREEN = "C6EFCE"
GREY = "808080"

STATUSES = ["TO CALL", "NO ANSWER", "INTERESTED", "LINK SENT",
            "CONFIRMED", "DECLINED", "DO NOT CONTACT"]

# (header, source key, width)
COLUMNS = [
    ("No", "no", 6),
    ("Nama Syarikat", "company", 40),
    ("Gred", "grade", 7),
    ("Daerah", "district", 11),
    ("No. Telefon", "phone", 15),
    ("Email", "email", 32),
    ("Bil Syarikat", "bil_syarikat", 8),
    ("Syarikat Lain", "syarikat_lain", 26),
    ("Caller", "caller", 11),
    ("Status", "status", 15),
    ("Nama Peserta", "nama_peserta", 22),
    ("No. HP Peserta", "no_hp_peserta", 16),
    ("Email Peserta", "email_peserta", 26),
    ("No. Pendaftaran CIDB", "cidb_reg", 20),
    ("Tarikh Call", "tarikh_call", 13),
    ("Catatan", "catatan", 34),
]

# Columns the caller fills in (1-based index into COLUMNS).
INPUT_COLS = [10, 11, 12, 13, 14, 15, 16]

THIN = Side(style="thin", color="C7D2DF")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)


def _load(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _style_header(ws, ncols: int, row: int = 1) -> None:
    for c in range(1, ncols + 1):
        cell = ws.cell(row=row, column=c)
        cell.font = Font(name=FONT, bold=True, size=10, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor=NAVY)
        cell.alignment = Alignment(vertical="center", wrap_text=True)
        cell.border = BORDER
    ws.row_dimensions[row].height = 28


def _write_grid(ws, rows: list[dict[str, str]], caller: str = "") -> None:
    ws.append([h for h, _, _ in COLUMNS])
    _style_header(ws, len(COLUMNS))

    for i, r in enumerate(rows, start=1):
        values = []
        for _, key, _ in COLUMNS:
            if key == "no":
                values.append(i)
            elif key == "caller":
                values.append(caller or r.get("caller", ""))
            elif key == "status":
                values.append("TO CALL")
            elif key == "cidb_reg":
                values.append("")
            else:
                values.append(r.get(key, ""))
        ws.append(values)

    last = ws.max_row
    for row in ws.iter_rows(min_row=2, max_row=last, max_col=len(COLUMNS)):
        for cell in row:
            cell.font = Font(name=FONT, size=9)
            cell.border = BORDER
            cell.alignment = Alignment(vertical="center")
    # Phone is what the caller dials — make it unmissable.
    for r in range(2, last + 1):
        ws.cell(row=r, column=5).font = Font(name=FONT, size=9, bold=True)
        for c in INPUT_COLS:
            ws.cell(row=r, column=c).fill = PatternFill("solid", fgColor=GOLD)

    for idx, (_, _, width) in enumerate(COLUMNS, start=1):
        ws.column_dimensions[get_column_letter(idx)].width = width

    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:{get_column_letter(len(COLUMNS))}{last}"

    if last >= 2:
        dv = DataValidation(type="list", formula1=f'"{",".join(STATUSES)}"',
                            allow_blank=False, showDropDown=False)
        ws.add_data_validation(dv)
        dv.add(f"J2:J{last}")

        ws.conditional_formatting.add(
            f"J2:J{last}",
            CellIsRule(operator="equal", formula=['"CONFIRMED"'],
                       fill=PatternFill("solid", fgColor=GREEN),
                       font=Font(name=FONT, size=9, bold=True, color="006100")))
        ws.conditional_formatting.add(
            f"J2:J{last}",
            CellIsRule(operator="equal", formula=['"DO NOT CONTACT"'],
                       fill=PatternFill("solid", fgColor="FFC7CE"),
                       font=Font(name=FONT, size=9, bold=True, color="9C0006")))


def _readme(ws, totals: dict[str, int]) -> None:
    ws.column_dimensions["A"].width = 30
    ws.column_dimensions["B"].width = 96

    ws["A1"] = "KUCHING CONTRACTORS MASTERLIST"
    ws["A1"].font = Font(name=FONT, bold=True, size=16, color=NAVY)
    ws["A2"] = "IECONS 2026 Delegate Drive  •  Sarawak Entrepreneurs Association (SEA)"
    ws["A2"].font = Font(name=FONT, size=10, color=GREY)

    rows = [
        ("", ""),
        ("WHAT IS IN THIS FILE", ""),
        ("MASTERLIST", f"All {totals['master']} callable contractors. The single source of truth."),
        ("CALLER 1 – CALLER 4", "Each caller's own slice. Work from the top, do not skip ahead."),
        ("SCOREBOARD", "Live counts. Updates itself as callers change Status."),
        ("NAMELIST", "Fills itself with CONFIRMED records. This is what goes to SEA."),
        ("NO PHONE", f"{totals['nophone']} records with unusable numbers. Not for calling."),
        ("", ""),
        ("WHICH CELLS YOU FILL IN", ""),
        ("Yellow cells only", "Status, Nama Peserta, No. HP Peserta, Email Peserta, "
                              "No. Pendaftaran CIDB, Tarikh Call, Catatan."),
        ("Never edit", "Nama Syarikat, Gred, Daerah, No. Telefon, Email. These came from "
                       "the CIDB registry."),
        ("Status", "Pick from the dropdown. Do not type your own wording — the "
                   "SCOREBOARD counts these exactly."),
        ("", ""),
        ("EXAMPLE OF A COMPLETED ROW", ""),
        ("Status", "CONFIRMED"),
        ("Nama Peserta", "Ahmad bin Zulkifli"),
        ("No. HP Peserta", "013-8765432"),
        ("Email Peserta", "ahmad@syarikatcontoh.com.my"),
        ("No. Pendaftaran CIDB", "0120180315-SR123456"),
        ("Tarikh Call", "3/8/2026"),
        ("Catatan", "Owner attending. Also owns 2 other companies, may send 2nd person."),
        ("", ""),
        ("RULES THAT MATTER", ""),
        ("Call first, always", "Never send the registration link before the contractor "
                               "confirms interest by voice."),
        ("CONFIRMED means verified", "Only mark CONFIRMED after the registration form is "
                                     "submitted and checked. Not when the link is sent."),
        ("CIDB number is mandatory", "A record without it will be rejected by SEA and does "
                                     "not count towards the 60."),
        ("Log as you go", "Update the row when the call ends, not at the end of the day."),
        ("DO NOT CONTACT is final", "If he asks not to be called again, mark it and stop. "
                                    "No further calls, no messages."),
    ]
    for label, text in rows:
        ws.append([label, text])
        r = ws.max_row
        if text == "" and label:
            ws.cell(row=r, column=1).font = Font(name=FONT, bold=True, size=11,
                                                 color="FFFFFF")
            ws.cell(row=r, column=1).fill = PatternFill("solid", fgColor=NAVY)
            ws.cell(row=r, column=2).fill = PatternFill("solid", fgColor=NAVY)
        else:
            ws.cell(row=r, column=1).font = Font(name=FONT, bold=True, size=10)
            ws.cell(row=r, column=2).font = Font(name=FONT, size=10)
        ws.cell(row=r, column=2).alignment = Alignment(wrap_text=True, vertical="top")


def _scoreboard(ws, caller_sheets: list[str], caller_counts: list[int]) -> None:
    ws.column_dimensions["A"].width = 22
    for col in "BCDEFG":
        ws.column_dimensions[col].width = 14

    ws["A1"] = "SCOREBOARD"
    ws["A1"].font = Font(name=FONT, bold=True, size=16, color=NAVY)
    ws["A2"] = "Updates automatically as callers set Status. Nothing here is typed by hand."
    ws["A2"].font = Font(name=FONT, size=9, color=GREY)

    ws["A4"] = "TEAM CONFIRMED"
    ws["A4"].font = Font(name=FONT, bold=True, size=11, color="FFFFFF")
    ws["A4"].fill = PatternFill("solid", fgColor=NAVY)
    ws["B4"] = "=SUM(B8:B11)"
    ws["B4"].font = Font(name=FONT, bold=True, size=26, color="006100")
    ws["B4"].alignment = Alignment(horizontal="center")
    ws["C4"] = "of 75 target"
    ws["C4"].font = Font(name=FONT, size=10, color=GREY)

    headers = ["Caller", "Confirmed", "Interested", "Link Sent",
               "Called", "Declined", "Remaining"]
    ws.append([])
    ws.append([])
    ws.append(headers)
    hrow = ws.max_row
    _style_header(ws, len(headers), row=hrow)

    for sheet, total in zip(caller_sheets, caller_counts):
        q = f"'{sheet}'!$J$2:$J${total + 1}"
        ws.append([
            sheet,
            f'=COUNTIF({q},"CONFIRMED")',
            f'=COUNTIF({q},"INTERESTED")',
            f'=COUNTIF({q},"LINK SENT")',
            f'=COUNTA({q})-COUNTIF({q},"TO CALL")',
            f'=COUNTIF({q},"DECLINED")+COUNTIF({q},"DO NOT CONTACT")',
            f'=COUNTIF({q},"TO CALL")',
        ])
        r = ws.max_row
        for c in range(1, len(headers) + 1):
            cell = ws.cell(row=r, column=c)
            cell.font = Font(name=FONT, size=10,
                             bold=(c == 2), color="006100" if c == 2 else "000000")
            cell.border = BORDER
            cell.alignment = Alignment(horizontal="center" if c > 1 else "left")

    tot = ws.max_row + 1
    ws.append(["TEAM TOTAL"] + [f"=SUM({get_column_letter(c)}8:{get_column_letter(c)}11)"
                                for c in range(2, len(headers) + 1)])
    for c in range(1, len(headers) + 1):
        cell = ws.cell(row=tot, column=c)
        cell.font = Font(name=FONT, bold=True, size=11)
        cell.fill = PatternFill("solid", fgColor=LIGHT)
        cell.border = BORDER
        cell.alignment = Alignment(horizontal="center" if c > 1 else "left")

    ws.append([])
    ws.append(["MILESTONES"])
    mrow = ws.max_row
    ws.cell(row=mrow, column=1).font = Font(name=FONT, bold=True, size=11, color="FFFFFF")
    for c in range(1, 4):
        ws.cell(row=mrow, column=c).fill = PatternFill("solid", fgColor=NAVY)

    ws.append(["Milestone", "Target", "Status"])
    _style_header(ws, 3, row=ws.max_row)
    for label, target in [("Target hit", 60), ("Buffer secured", 80),
                          ("Triple digits", 100), ("Stretch", 120)]:
        ws.append([label, target, f'=IF($B$4>={target},"REACHED","")'])
        r = ws.max_row
        for c in range(1, 4):
            cell = ws.cell(row=r, column=c)
            cell.font = Font(name=FONT, size=10, bold=(c == 3))
            cell.border = BORDER
            cell.alignment = Alignment(horizontal="center" if c > 1 else "left")
        ws.conditional_formatting.add(
            f"C{r}",
            CellIsRule(operator="equal", formula=['"REACHED"'],
                       fill=PatternFill("solid", fgColor=GREEN),
                       font=Font(name=FONT, bold=True, size=10, color="006100")))


def _namelist(ws, master_rows: int, rank_col: str) -> None:
    ws["A1"] = "NAMELIST FOR SEA"
    ws["A1"].font = Font(name=FONT, bold=True, size=16, color=NAVY)
    ws["A2"] = ("Fills itself from MASTERLIST as records are marked CONFIRMED. "
                "Do not type into this sheet.")
    ws["A2"].font = Font(name=FONT, size=9, color=GREY)

    headers = ["No", "Nama Syarikat", "Gred", "Nama Peserta", "No. HP Peserta",
               "Email Peserta", "No. Pendaftaran CIDB", "Caller"]
    widths = [6, 40, 7, 24, 16, 28, 22, 12]
    ws.append([])
    ws.append(headers)
    hrow = ws.max_row
    _style_header(ws, len(headers), row=hrow)
    for i, w in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(i)].width = w

    # MASTERLIST columns pulled into each NAMELIST column.
    src = {2: "B", 3: "C", 4: "K", 5: "L", 6: "M", 7: "N", 8: "I"}
    end = master_rows + 1

    # The row lookup is resolved once per row into a helper column rather than
    # repeated inside all seven INDEX calls. Over 120 rows that is 120 MATCHes
    # across 1,158 records instead of 960 — the difference between a
    # recalculation that finishes and one that does not.
    helper = get_column_letter(len(headers) + 2)
    ws[f"{helper}{hrow}"] = "row_match"
    ws[f"{helper}{hrow}"].font = Font(name=FONT, size=8, color=GREY)

    for n in range(1, 121):
        r = hrow + n
        ws[f"{helper}{r}"] = (
            f'=IFERROR(MATCH({n},MASTERLIST!${rank_col}$2:${rank_col}${end},0),0)')
        ws[f"{helper}{r}"].font = Font(name=FONT, size=8, color=GREY)

        hit = f"${helper}{r}"
        ws.cell(row=r, column=1).value = f'=IF({hit}=0,"",{n})'
        for col, letter in src.items():
            ws.cell(row=r, column=col).value = (
                f'=IF({hit}=0,"",INDEX(MASTERLIST!${letter}$2:${letter}${end},{hit}))')
        for c in range(1, len(headers) + 1):
            cell = ws.cell(row=r, column=c)
            cell.font = Font(name=FONT, size=9)
            cell.border = BORDER

    ws.column_dimensions[helper].hidden = True
    ws.freeze_panes = f"A{hrow + 1}"


def build(batch_dir: Path, out: Path) -> int:
    master = _load(batch_dir / "MASTER_all_contractors.csv")
    nophone_path = batch_dir / "NO_PHONE_email_only.csv"
    nophone = _load(nophone_path) if nophone_path.exists() else []

    caller_files = sorted(batch_dir.glob("caller_*.csv"))
    caller_data = {f"CALLER {i}": _load(f) for i, f in enumerate(caller_files, start=1)}

    # Stamp caller ownership onto the master rows so SEA can see who closed each.
    owner = {}
    for name, rows in caller_data.items():
        for r in rows:
            owner[(r.get("company", ""), r.get("phone", ""))] = name
    for r in master:
        r["caller"] = owner.get((r.get("company", ""), r.get("phone", "")), "")

    wb = Workbook()
    _readme(wb.active, {"master": len(master), "nophone": len(nophone)})
    wb.active.title = "README"

    sb = wb.create_sheet("SCOREBOARD")

    ws_master = wb.create_sheet("MASTERLIST")
    _write_grid(ws_master, master)

    # Two helper columns let NAMELIST pull CONFIRMED rows without an array
    # formula (LibreOffice cannot evaluate the spilling alternatives).
    #
    # The running total is deliberately incremental rather than a COUNTIF over
    # an expanding range: the latter is O(n^2) and, across 1,158 rows, takes
    # long enough that LibreOffice gives up before finishing the recalculation.
    run_idx = len(COLUMNS) + 1
    rank_idx = len(COLUMNS) + 2
    run_col = get_column_letter(run_idx)
    rank_col = get_column_letter(rank_idx)

    ws_master.cell(row=1, column=run_idx).value = "running_count"
    ws_master.cell(row=1, column=rank_idx).value = "rank_confirmed"
    _style_header(ws_master, rank_idx)
    ws_master.column_dimensions[run_col].width = 13
    ws_master.column_dimensions[rank_col].width = 13

    for r in range(2, len(master) + 2):
        prior = "0" if r == 2 else f"${run_col}{r - 1}"
        ws_master.cell(row=r, column=run_idx).value = (
            f'={prior}+IF($J{r}="CONFIRMED",1,0)')
        ws_master.cell(row=r, column=rank_idx).value = (
            f'=IF($J{r}="CONFIRMED",${run_col}{r},"")')
        for c in (run_idx, rank_idx):
            ws_master.cell(row=r, column=c).font = Font(name=FONT, size=9, color=GREY)

    for name, rows in caller_data.items():
        _write_grid(wb.create_sheet(name), rows, caller=name)

    _namelist(wb.create_sheet("NAMELIST"), len(master), rank_col)

    if nophone:
        ws_np = wb.create_sheet("NO PHONE")
        _write_grid(ws_np, nophone)
        ws_np["R1"] = ("No usable telephone number in the CIDB registry. "
                       "Email only — do not assign to a caller.")
        ws_np["R1"].font = Font(name=FONT, size=9, italic=True, color="9C0006")

    _scoreboard(sb, list(caller_data), [len(v) for v in caller_data.values()])

    out.parent.mkdir(parents=True, exist_ok=True)
    wb.save(out)
    print(f"  wrote {out}")
    print(f"    MASTERLIST {len(master)}  |  "
          f"{'  '.join(f'{k} {len(v)}' for k, v in caller_data.items())}  |  "
          f"NO PHONE {len(nophone)}")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("batch_dir")
    p.add_argument("--out", required=True)
    args = p.parse_args(argv)
    return build(Path(args.batch_dir), Path(args.out))


if __name__ == "__main__":
    raise SystemExit(main())
