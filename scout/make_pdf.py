"""Generate the IECONS campaign PDFs in the KOBIS house style.

Two documents:
  1. The revised job order (4 callers, 100 calls per caller per day)
  2. The caller grouping — one call sheet per caller

Usage:
    python3 -m scout.make_pdf joborder --out JOB_ORDER.pdf
    python3 -m scout.make_pdf batches --dir batches/ --out CALL_SHEETS.pdf
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (BaseDocTemplate, Frame, KeepTogether, PageBreak,
                                Paragraph, Spacer, Table, TableStyle)

NAVY = colors.HexColor("#12263F")
SLATE = colors.HexColor("#33547A")
GOLD = colors.HexColor("#B8860B")
LIGHT = colors.HexColor("#EEF2F7")
RULE = colors.HexColor("#C7D2DF")
RED = colors.HexColor("#A3231D")

TITLE = "LPC SPECIAL TASK — IECONS 2026 DELEGATE DRIVE"
ORG = "KOBIS BERHAD  •  LPC AI SANDBOX  •  Sarawak Entrepreneurs Association"
REF = "JO/LPC-KAPT/2026-08/IECONS-01  (Rev. B)"


def styles() -> dict:
    base = getSampleStyleSheet()
    return {
        "h1": ParagraphStyle("h1", parent=base["Heading1"], fontName="Helvetica-Bold",
                             fontSize=15, leading=19, textColor=NAVY, spaceAfter=2),
        "sub": ParagraphStyle("sub", parent=base["Normal"], fontName="Helvetica",
                              fontSize=9.5, leading=13, textColor=SLATE, spaceAfter=10),
        "h2": ParagraphStyle("h2", parent=base["Heading2"], fontName="Helvetica-Bold",
                             fontSize=11.5, leading=15, textColor=colors.white,
                             backColor=NAVY, borderPadding=(5, 6, 5, 6),
                             spaceBefore=14, spaceAfter=8),
        "h3": ParagraphStyle("h3", parent=base["Heading3"], fontName="Helvetica-Bold",
                             fontSize=10, leading=13, textColor=NAVY,
                             spaceBefore=10, spaceAfter=4),
        "body": ParagraphStyle("body", parent=base["Normal"], fontName="Helvetica",
                               fontSize=9, leading=12.8, spaceAfter=6),
        "cell": ParagraphStyle("cell", parent=base["Normal"], fontName="Helvetica",
                               fontSize=8.2, leading=10.5),
        "cellb": ParagraphStyle("cellb", parent=base["Normal"],
                                fontName="Helvetica-Bold", fontSize=8.2, leading=10.5),
        "callout": ParagraphStyle("callout", parent=base["Normal"],
                                  fontName="Helvetica-Bold", fontSize=9.2, leading=12.5,
                                  textColor=NAVY),
        "script": ParagraphStyle("script", parent=base["Normal"], fontName="Helvetica",
                                 fontSize=9, leading=13, leftIndent=8, rightIndent=8,
                                 textColor=colors.HexColor("#12263F")),
        "tiny": ParagraphStyle("tiny", parent=base["Normal"], fontName="Helvetica",
                               fontSize=7.4, leading=9, textColor=SLATE),
        "kpi": ParagraphStyle("kpi", parent=base["Normal"], fontName="Helvetica-Bold",
                              fontSize=13, leading=15, textColor=NAVY,
                              alignment=TA_CENTER),
        "kpil": ParagraphStyle("kpil", parent=base["Normal"], fontName="Helvetica",
                               fontSize=7, leading=9, textColor=SLATE,
                               alignment=TA_CENTER),
    }


S = styles()


def _header_footer(canvas, doc):
    canvas.saveState()
    w, h = doc.pagesize

    canvas.setFillColor(NAVY)
    canvas.rect(0, h - 20 * mm, w, 20 * mm, stroke=0, fill=1)
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica-Bold", 10)
    canvas.drawString(15 * mm, h - 10 * mm, TITLE)
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(colors.HexColor("#AFC2D8"))
    canvas.drawString(15 * mm, h - 15 * mm, ORG)
    canvas.drawRightString(w - 15 * mm, h - 10 * mm, REF)
    canvas.drawRightString(w - 15 * mm, h - 15 * mm, f"Page {doc.page}")

    canvas.setStrokeColor(RULE)
    canvas.setLineWidth(0.5)
    canvas.line(15 * mm, 13 * mm, w - 15 * mm, 13 * mm)
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(SLATE)
    canvas.drawString(15 * mm, 9 * mm,
                      "Internal Use Only  •  LPC-KAPT  •  Confidential")
    canvas.drawRightString(w - 15 * mm, 9 * mm,
                           "Do not distribute outside the assigned team")
    canvas.restoreState()


def build_doc(path: Path, story: list, page=A4):
    doc = BaseDocTemplate(str(path), pagesize=page,
                          leftMargin=15 * mm, rightMargin=15 * mm,
                          topMargin=25 * mm, bottomMargin=17 * mm,
                          title=TITLE, author="KOBIS BERHAD")
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="f")
    from reportlab.platypus import PageTemplate
    doc.addPageTemplates([PageTemplate(id="all", frames=[frame],
                                       onPage=_header_footer)])
    doc.build(story)


# Usable text width, in points, for each orientation (A4 less 15mm margins).
WIDTH_PORTRAIT = A4[0] - 30 * mm
WIDTH_LANDSCAPE = A4[1] - 30 * mm


def fit(widths: list, total: float) -> list:
    """Expand a single None column to fill `total`."""
    fixed = sum(w for w in widths if w is not None)
    slack = max(total - fixed, 40)
    return [slack if w is None else w for w in widths]


def table(data, widths, *, header=True, align=None, font_size=8.2, pad=4):
    t = Table(data, colWidths=widths, repeatRows=1 if header else 0)
    cmds = [
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), font_size),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), pad),
        ("BOTTOMPADDING", (0, 0), (-1, -1), pad),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("GRID", (0, 0), (-1, -1), 0.4, RULE),
    ]
    if header:
        cmds += [("BACKGROUND", (0, 0), (-1, 0), NAVY),
                 ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                 ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                 ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT])]
    if align:
        for col, a in align.items():
            cmds.append(("ALIGN", (col, 0), (col, -1), a))
    t.setStyle(TableStyle(cmds))
    return t


def callout(label: str, text: str, tone=GOLD):
    inner = [[Paragraph(f'<font color="{tone.hexval()}"><b>{label}</b></font>'
                        f'<br/>{text}', S["callout"])]]
    t = Table(inner, colWidths=[None])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT),
        ("LINEBEFORE", (0, 0), (0, -1), 3, tone),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING", (0, 0), (-1, -1), 9),
        ("RIGHTPADDING", (0, 0), (-1, -1), 9),
    ]))
    return t


def script_box(label: str, text: str):
    inner = [[Paragraph(f'<b><font color="{GOLD.hexval()}">{label}</font></b>',
                        S["tiny"])],
             [Paragraph(text, S["script"])]]
    t = Table(inner, colWidths=[None])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F7F9FC")),
        ("BOX", (0, 0), (-1, -1), 0.6, RULE),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    return t


def kpi_row(items):
    cells = [[Paragraph(v, S["kpi"]) for _, v in items],
             [Paragraph(k, S["kpil"]) for k, _ in items]]
    t = Table(cells, colWidths=[None] * len(items))
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT),
        ("BOX", (0, 0), (-1, -1), 0.6, RULE),
        ("INNERGRID", (0, 0), (-1, -1), 0.4, RULE),
        ("TOPPADDING", (0, 0), (-1, 0), 8),
        ("BOTTOMPADDING", (0, 1), (-1, 1), 8),
    ]))
    return t


def P(text, style="body"):
    return Paragraph(text, S[style])
