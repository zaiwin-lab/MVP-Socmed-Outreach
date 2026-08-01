"""Revised job order (Rev. B) — 4 callers, 100 calls per caller per day."""

from __future__ import annotations

from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.platypus import KeepTogether, PageBreak, Spacer

from .make_pdf import (GOLD, NAVY, P, RED, build_doc, callout, kpi_row,
                       script_box, table)


def story() -> list:
    s: list = []

    s.append(P("From a Contact List to 60 Confirmed Contractors", "h1"))
    s.append(P("at the Premier's Programme — Hari Integriti dan Kecemerlangan "
               "Industri Pembinaan Sarawak 2026", "sub"))

    s.append(kpi_row([
        ("KICK-OFF", "Mon 3 Aug"),
        ("DEADLINE", "Wed 5 Aug"),
        ("CALLING DAYS", "2"),
        ("CALLS / CALLER / DAY", "100"),
        ("TARGET", "60 verified"),
    ]))
    s.append(Spacer(1, 6))
    s.append(P("Submission: one Google Sheet link to SEA, copied to KOBIS Management",
               "tiny"))

    s.append(callout(
        "REVISION B — READ THIS FIRST",
        "The original job order assumed a Saturday start over four days. The team "
        "now kicks off on <b>Monday 3 August</b>, which leaves <b>two calling "
        "days</b>, not four. Every target in this revision has been rebuilt around "
        "that. Section B.4 replaces the previous schedule entirely.", RED))

    # ------------------------------------------------------------------ A
    s.append(P("A. THE ASSIGNMENT", "h2"))
    s.append(P(
        "The LPC-KAPT team is assigned to deliver <b>60 confirmed contractors</b> "
        "for paid registration under the <b>Sarawak Entrepreneurs Association "
        "(SEA)</b> delegation to Hari Integriti dan Kecemerlangan Industri "
        "Pembinaan Sarawak 2026, officiated by YAB the Premier of Sarawak on "
        "6 August 2026. Management has secured the seats. The team's "
        "responsibility is to fill them."))

    s.append(P("The Programme You Are Offering", "h3"))
    s.append(table([
        ["Item", "Detail"],
        ["Programme", "Hari Integriti dan Kecemerlangan Industri Pembinaan Sarawak 2026"],
        ["Date", "6 August 2026, Thursday, 9.00 a.m. – 5.00 p.m."],
        ["Venue", "Pusat Konvensyen CIDB Sarawak"],
        ["Officiated by", "YAB Datuk Patinggi Tan Sri (Dr) Abang Johari, Premier Sarawak"],
        ["Normal Fee", "RM54 per participant"],
        ["SEA Offer", "Free of charge, sponsored, limited seats"],
    ], [95, None]))

    s.append(P("The Task in Numbers", "h3"))
    s.append(table([
        ["Item", "Target"],
        ["Callers", "4"],
        ["Calls per caller, per day", "100"],
        ["Team calls per day", "400"],
        ["Total calls across the two days", "800"],
        ["Contact list supplied", "Kuching and surrounding districts, CIDB Grade G1 – G3"],
        ["Confirmed registrations needed", "75  (working buffer)"],
        ["Final namelist to SEA", "60  (verified)"],
    ], [200, None]))

    s.append(callout(
        "WHY 75 AND NOT 60",
        "Some confirmations are withdrawn and some records arrive incomplete. A "
        "team that stops at exactly 60 delivers fewer than 60. Build the buffer "
        "on Monday, while there is still a day left to recover."))

    s.append(P("The Three Selling Points — In Order of Strength", "h3"))
    s.append(table([
        ["", "Point", "Why it works"],
        ["1", "10 CCD Points",
         "Required for CIDB registration renewal. For a G1–G3 contractor this is "
         "the strongest reason to attend, and it is normally paid for."],
        ["2", "Officiated by the Premier", "Prestige, access and visibility."],
        ["3", "SEA Certificate + hospitality",
         "Certificate, lunch, refreshments and exhibition access."],
    ], [16, 120, None]))

    s.append(callout(
        "LEAD WITH CCD POINTS AND THE PREMIER",
        "Contractors do not register because of the theme of a programme. They "
        "register because of CCD points and the presence of the Premier."))

    s.append(PageBreak())

    # ------------------------------------------------------------------ B
    s.append(P("B. HOW THE WORK MUST BE DONE", "h2"))

    s.append(P("1. Call First, Always", "h3"))
    s.append(P(
        "Every contractor must be telephoned before any message is sent. The "
        "registration link is released only after a contractor has confirmed, "
        "<b>by voice</b>, that he is both interested and available on 6 August."))
    s.append(table([
        ["", "Step", "What you do"],
        ["1", "CALL", "Introduce, congratulate, confirm interest and availability."],
        ["2", "SEND", "If interested, send the registration link by WhatsApp immediately."],
        ["3", "VERIFY", "Confirm the form was actually submitted, not merely received."],
        ["4", "RECORD", "Log the outcome and complete the row in the Master Sheet."],
    ], [16, 55, None]))
    s.append(P(
        "A link sent without a call converts very poorly and places our WhatsApp "
        "numbers at risk of restriction. The call is what persuades; the link only "
        "captures. If a contractor declines, thank him politely and close the "
        "record with the reason. If he asks not to be contacted again, stop "
        "immediately and mark the record accordingly."))

    s.append(P("2. The Call Script — keep the opening under 45 seconds", "h3"))
    s.append(script_box("OPENING", (
        "Salam Tuan, saya [Nama] dari SEA — Sarawak Entrepreneurs Association. "
        "Tahniah Tuan! Syarikat Tuan antara kontraktor yang dijemput ke program "
        "rasmi anjuran CIDB Sarawak, yang akan dirasmikan oleh YAB Premier Sarawak "
        "sendiri, pada 6 Ogos ini di Pusat Konvensyen CIDB. Yang penting, Tuan "
        "dapat <b>10 MATA CCD</b> — untuk renew pendaftaran CIDB. Yuran asal RM54, "
        "tetapi SEA tajaan <b>PERCUMA</b> untuk tempat yang terhad. "
        "Tuan available tak pada 6 Ogos? Berminat nak join?")))
    s.append(Spacer(1, 5))
    s.append(script_box("IF YES", (
        "Bagus Tuan! Saya WhatsApp link pendaftaran sekarang. Tuan isi terus ya — "
        "tempat terhad, siapa cepat dia dapat. Nanti saya follow up.")))
    s.append(Spacer(1, 5))
    s.append(script_box("IF UNSURE / BUSY", (
        "Faham Tuan. Tapi 10 Mata CCD ni jarang dapat percuma. Kalau Tuan tak dapat "
        "pergi, boleh hantar wakil syarikat — staff atau partner pun boleh. "
        "Nak saya lockkan satu tempat dulu?")))
    s.append(Spacer(1, 5))
    s.append(script_box("IF NO", (
        "Tak apa Tuan, terima kasih atas masa. Kalau ada perubahan sebelum 5 Ogos, "
        "WhatsApp saya. Semoga murah rezeki Tuan.")))

    s.append(P("3. Answering Common Objections", "h3"))
    s.append(table([
        ["What he says", "What you answer"],
        ['"Hari kerja, saya sibuk"',
         "Hantar wakil — staff atau partner boleh. CCD points masuk atas nama syarikat."],
        ['"Betul ke free?"', "Betul. Ditaja penuh oleh SEA. Tuan tak bayar apa-apa."],
        ['"Jauh"',
         "Pusat Konvensyen CIDB, dalam Kuching. Ada parking, makan tengah hari disediakan."],
        ['"CCD tu apa?"',
         "Mata CCD wajib untuk renew pendaftaran CIDB. 10 mata sekali hadir — "
         "biasanya kena bayar kursus."],
        ['"Saya fikir dulu"',
         "Boleh Tuan. Tapi tempat terhad — saya lock dulu nama Tuan, kalau tak jadi "
         "bagitahu sebelum Selasa."],
    ], [110, None]))

    s.append(PageBreak())

    s.append(P("4. Daily Targets — REVISED", "h3"))
    s.append(table([
        ["Day", "Date", "Calls / caller", "Team calls", "New confirmed", "Cumulative"],
        ["Day 1", "Mon, 3 Aug", "100", "400", "40", "40"],
        ["Day 2", "Tue, 4 Aug", "100", "400", "38", "78"],
        ["Day 3", "Wed, 5 Aug", "—", "—", "Verification only", "60 delivered"],
    ], [38, 68, 68, 55, 82, None], align={2: "CENTER", 3: "CENTER", 4: "CENTER"}))

    s.append(callout(
        "FINISH EARLY IF YOU CAN",
        "The sooner the 75 is reached, the better. If Monday closes above 45, push "
        "Tuesday morning hard and hand the namelist to SEA on Tuesday evening "
        "instead of Wednesday. An early finish gives SEA a full day to process "
        "payment and gives us room if CIDB queries any record."))

    s.append(P("Calling Hours", "h3"))
    s.append(table([
        ["Window", "Use"],
        ["9.00 a.m. – 12.30 p.m.", "Best window. Highest answer rate. Aim for 55 calls here."],
        ["12.30 p.m. – 2.30 p.m.", "Lunch and prayer. Do not call. Use for logging and follow-up messages."],
        ["2.30 p.m. – 5.30 p.m.", "Second window. Aim for 45 calls here."],
        ["Before 8.30 a.m. / after 7.00 p.m.", "Do not call."],
    ], [150, None]))

    s.append(P("5. Team Structure", "h3"))
    s.append(table([
        ["Role", "Number", "Responsibility"],
        ["Team Lead", "1", "Daily standup, progress reporting, escalation"],
        ["Callers", "4", "100 calls per day each, execute the flow, record every outcome"],
        ["Data & Verification", "1", "Master Sheet accuracy, deduplication, final namelist"],
    ], [110, 45, None], align={1: "CENTER"}))

    s.append(callout(
        "WHAT 100 CALLS A DAY ACTUALLY MEANS",
        "At roughly three minutes per attempt including no-answers and redials, "
        "100 calls is about five hours on the telephone. That is a full working "
        "day with two clear windows and little slack. If a caller drops out, the "
        "Team Lead must tell Management the same morning — not on Tuesday evening.",
        RED))

    s.append(PageBreak())

    # ------------------------------------------------------------------ C
    s.append(P("C. STANDARDS, RECORDS AND REPORTING", "h2"))

    s.append(P("1. What Counts as a Confirmed Name", "h3"))
    s.append(P("A record counts towards the 60 only when every one of the "
               "following is true:"))
    s.append(table([
        ["", "Requirement"],
        ["1", "The contractor was spoken to by telephone, not only by WhatsApp"],
        ["2", "He confirmed he is interested and available on 6 August"],
        ["3", "The registration form was submitted and verified"],
        ["4", "His CIDB registration number was captured"],
        ["5", "His telephone number was confirmed reachable"],
        ["6", "The record is complete in the Master Sheet"],
    ], [16, None]))
    s.append(P("Incomplete records will be rejected by SEA and will not count "
               "towards the target."))

    s.append(P("2. Records", "h3"))
    s.append(P("All work must be visible. Record outcomes as each call ends, not "
               "at the end of the day."))
    s.append(table([
        ["Tool", "What goes in it"],
        ["ClickUp",
         "One record per contractor, moving through: To Call → Called → Interested → "
         "Link Sent → Confirmed → Closed. Caller name, date, time, outcome and notes "
         "are required on every record."],
        ["Google Sheets",
         "Master Namelist — the single source of truth. Columns: Nama Syarikat, "
         "No. Pendaftaran CIDB, Gred, Nama Peserta, No. Telefon, Email, Daerah, "
         "Status, Caller, Tarikh Sahkan."],
        ["Google Drive",
         "One shared folder for the script, brochure, objection sheet and daily reports."],
    ], [80, None]))

    s.append(P("3. Reporting Cadence", "h3"))
    s.append(table([
        ["When", "What", "To whom"],
        ["Daily, 8.45 a.m.", "15-min standup: yesterday's result, today's target, obstacles",
         "Team Lead → Callers"],
        ["Daily, 1.00 p.m.", "Half-day check: calls made, confirmed so far",
         "Team Lead → Management"],
        ["Daily, 6.00 p.m.", "Progress summary: calls, interested, confirmed, cumulative",
         "Team Lead → Management"],
        ["Mon 3 Aug, 6.00 p.m.", "Gate check 1. Target 40. Below 30 → escalate.",
         "Team Lead → Management"],
        ["Tue 4 Aug, 6.00 p.m.", "Gate check 2. Target 75. Below 60 → escalate at once.",
         "Team Lead → Mgmt + SEA"],
        ["Wed 5 Aug, 9.00 a.m.", "Final namelist of 60 delivered to SEA",
         "Team Lead → SEA"],
    ], [80, None, 82]))

    s.append(P("4. When to Escalate — same day", "h3"))
    s.append(table([
        ["", "Trigger"],
        ["•", "Confirmed numbers fall more than 20% below the daily target"],
        ["•", "Any caller is unavailable or falls below 70 calls in a day"],
        ["•", "More than 30% of the supplied numbers are unreachable"],
        ["•", "The registration link or microsite is not working"],
        ["•", "A WhatsApp number is restricted or blocked"],
        ["•", "Any change to the event, the venue or the sponsorship arrangement"],
    ], [14, None]))

    s.append(P("5. Conduct", "h3"))
    s.append(P("This is a programme about integrity, and the team will be seen to "
               "represent SEA. Members are expected to hold to the following "
               "without exception."))
    s.append(table([
        ["", "Rule"],
        ["•", "Identify yourself as calling on behalf of SEA on every call."],
        ["•", "The seats are genuinely free and genuinely limited. Say exactly that "
              "and nothing more."],
        ["•", "Release the seats in real batches. When the first 50 are taken, "
              "announce the next. Do not claim a scarcity that does not exist."],
        ["•", "Never register a contractor who has not agreed by voice. A padded "
              "namelist at an anti-corruption event would damage SEA far more than "
              "a shortfall would."],
        ["•", "The contact list is supplied for this assignment only. It must not be "
              "copied, shared or reused."],
    ], [14, None]))

    s.append(PageBreak())
    s.append(P("MESSAGE FROM MANAGEMENT", "h2"))
    s.append(P(
        "This assignment is different from your usual work, and that is the point. "
        "You are not being asked to learn a platform this time — you are being asked "
        "to convert a list of names into real people in a real hall, in front of the "
        "Premier of Sarawak, in two days."))
    s.append(P(
        "The window is shorter than originally planned and the target has not moved. "
        "One hundred calls a day is demanding, and we are asking for it because the "
        "arithmetic leaves no other route. It is also an unusually clear test of the "
        "things that matter most in professional work: discipline on the telephone, "
        "honesty in what you record, and the persistence to make the second and "
        "third call when the first is not answered."))
    s.append(P(
        "Every member begins with a different level of confidence on the phone. That "
        "is expected. What is expected of everyone equally is that the call is made, "
        "the outcome is recorded truthfully, and help is asked for early rather than "
        "late."))
    s.append(P(
        "Do the work properly and SEA will have its delegation, KOBIS will have "
        "demonstrated what LPC-KAPT can deliver under pressure, and each of you will "
        "have something concrete to point to."))

    s.append(Spacer(1, 10))
    s.append(callout(
        "SIXTY NAMES IS THE TARGET.  SEVENTY-FIVE IS THE PLAN.",
        "A campaign that aims exactly at its target always lands beneath it. "
        "Build the buffer on Monday, while there is still a day to recover."))
    return s


def main(out: str) -> int:
    build_doc(Path(out), story(), page=A4)
    print(f"  wrote {out}")
    return 0
