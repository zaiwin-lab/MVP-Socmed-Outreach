"""Trainer & Coach Guide — companion to the LPC Campaign Operations Playbook.

Mirrors the playbook's five-section structure so both documents read as one
standard. The playbook tells a caller what to do; this tells the trainer how to
get them doing it correctly, quickly, and without supervision by the afternoon.
"""

from __future__ import annotations

from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.platypus import PageBreak, Spacer

from .make_pdf import (GOLD, NAVY, RED, WIDTH_PORTRAIT, P, build_doc, callout,
                       fit, kpi_row, script_box, set_header, table)

W = WIDTH_PORTRAIT


def story() -> list:
    s: list = []

    s.append(P("Trainer &amp; Coach Guide", "h1"))
    s.append(P("Companion to the Campaign Operations Playbook  •  How to bring "
               "four callers to independent, correct execution in one morning", "sub"))

    s.append(kpi_row([
        ("CALLERS TO CERTIFY", "4"),
        ("CERTIFY BY", "Mon 10.00 a.m."),
        ("SOLO BY", "Mon 12.00 noon"),
        ("PASS MARK", "6 of 7"),
        ("TEAM TARGET", "75 confirmed"),
    ]))
    s.append(Spacer(1, 8))

    s.append(callout(
        "YOUR JOB IS TO MAKE YOURSELF UNNECESSARY BY LUNCHTIME",
        "You are not here to make the calls. Every call you take is a call a "
        "caller did not learn from. Your success is measured by how independent "
        "the team is on Monday afternoon — not by how many registrations you "
        "personally closed.", RED))

    # ---------------------------------------------------------------- 1
    s.append(P("1. Mission at a Glance — Trainer's View", "h2"))
    s.append(table([
        ["Item", "Detail"],
        ["Your accountability",
         "Four callers executing the approved script correctly and unsupervised "
         "by Monday afternoon."],
        ["Timeline",
         "3-4 Aug: Calling & Registration   |   5 Aug: Final verification"],
        ["What you certify",
         "Each caller passes the 7-point Call Quality Standard (Section 3) before "
         "dialling a real contact unsupervised."],
        ["What you protect",
         "SEA's reputation. Zero spam complaints. No link sent without voice "
         "confirmation."],
        ["What you never do",
         "Take over the call. Coach after it ends, never during."],
    ], fit([110, None], W)))

    s.append(P("The workflow they must follow", "h3"))
    s.append(P(
        "Greeting → Introduce → Explain 10 CCD + Premier → Check Availability &amp; "
        "Interest → <b>Reveal SEA Special Invitation</b> → WhatsApp Link → "
        "Registration → Verification → Update Master Sheet"))

    s.append(callout(
        "THE SEQUENCE IS THE WHOLE METHOD",
        "The sponsorship is revealed <b>after</b> the contractor confirms interest, "
        "never before. Leading with 'percuma' turns a professional invitation into "
        "a giveaway call and invites the spam reaction we are trying to avoid. "
        "If a caller reveals the sponsorship early, stop and re-drill it — this is "
        "the single most common failure and the most damaging."))

    # ---------------------------------------------------------------- 2
    s.append(PageBreak())
    s.append(P("2. Pre-Launch — Certify Before They Dial", "h2"))
    s.append(P("Monday morning, before any real contact is called. Four phases, "
               "about ninety minutes total. Do not shorten this — an uncertified "
               "caller burns real contacts learning."))

    s.append(table([
        ["Phase", "Time", "What happens"],
        ["1. I DO", "8.45 – 9.05", "You demonstrate three live calls on speaker while "
                                   "the team listens in silence. At least one must be "
                                   "a rejection so they hear how it is closed politely."],
        ["2. WE DO", "9.05 – 9.30", "Each caller role-plays two calls with you as the "
                                    "contractor. Score them against Section 3. Correct "
                                    "on the spot."],
        ["3. YOU DO (watched)", "9.30 – 10.00", "Each caller makes three real calls with "
                                                "you listening. Score. Certify at 6 of 7 "
                                                "or repeat Phase 2."],
        ["4. SOLO", "10.00 onwards", "Certified callers work independently. You spot-check "
                                     "two calls per caller per hour until noon, then move "
                                     "to escalation only."],
    ], fit([88, 62, None], W)))

    s.append(callout(
        "WHAT TO DEMONSTRATE IN PHASE 1",
        "Callers copy what they hear, so demonstrate the hard parts deliberately: "
        "the pause after the qualification question, the polite close on a 'no', "
        "and the moment the SEA invitation is revealed. Say out loud what you are "
        "doing and why before each call."))

    s.append(P("Materials each caller must have before Phase 3", "h3"))
    s.append(table([
        ["", "Item"],
        ["1", "Printed Campaign Operations Playbook — script and objection table"],
        ["2", "Their own call sheet (caller_1 to caller_4), worked from the top"],
        ["3", "Edit access to the shared Master Sheet, opened and tested"],
        ["4", "The registration link, tested once on their own phone"],
        ["5", "WhatsApp ready on the number they will send from"],
    ], fit([16, None], W)))

    # ---------------------------------------------------------------- 3
    s.append(PageBreak())
    s.append(P("3. Call Quality Standard — What Good Sounds Like", "h2"))
    s.append(P("Score every call you listen to. Six of seven is a pass. Below six, "
               "the caller returns to Phase 2 before continuing."))

    s.append(table([
        ["", "Standard", "Fail looks like"],
        ["1", "Identified self and SEA within the first ten seconds",
         "Rambling opening, company name buried or missing"],
        ["2", "Confirmed speaking to the owner or an authorised wakil",
         "Pitching to whoever answered"],
        ["3", "Led with 10 Mata CCD and the Premier before anything else",
         "Leading with 'free' or with the programme theme"],
        ["4", "Asked availability and interest as a question — then stopped talking",
         "Talking through the pause and answering their own question"],
        ["5", "Revealed the SEA sponsorship only after a yes",
         "Offering 'percuma' in the opening"],
        ["6", "Reached the qualification question inside 45 seconds",
         "Long preamble, contractor disengages"],
        ["7", "Logged the outcome immediately after hanging up",
         "Batching entries to the end of the session"],
    ], fit([16, 168, None], W)))

    s.append(callout(
        "COACH ONE THING AT A TIME",
        "After a call, name one thing done well and one thing to change — never "
        "more. A caller given five corrections at once fixes none of them. Pick "
        "the highest-numbered failure on the list above and drill only that.",
        GOLD))

    s.append(P("The model call, for reference", "h3"))
    s.append(script_box("GREETING", (
        "Salam Tuan. Saya [Nama] menelefon bagi pihak Sarawak Entrepreneurs "
        "Association (SEA). Adakah saya bercakap dengan pemilik atau wakil "
        "syarikat?")))
    s.append(Spacer(1, 4))
    s.append(script_box("VALUE", (
        "Kami ingin memaklumkan mengenai Program Hari Integriti dan Kecemerlangan "
        "Industri Pembinaan Sarawak pada 6 Ogos nanti. Program ini dirasmikan oleh "
        "YAB Premier Sarawak dan peserta akan menerima <b>10 Mata CCD</b>.")))
    s.append(Spacer(1, 4))
    s.append(script_box("QUALIFICATION  —  then stop talking", (
        "Boleh saya semak dahulu, Tuan available pada 6 Ogos dan berminat untuk "
        "menyertai?")))
    s.append(Spacer(1, 4))
    s.append(script_box("REVEAL  —  only after a yes", (
        "Terima kasih Tuan. Sebenarnya Tuan dipilih di bawah jemputan khas SEA. "
        "Kami mempunyai kuota tajaan yang terhad. Saya akan WhatsApp pautan "
        "pendaftaran selepas panggilan ini untuk pengesahan tempat.")))

    # ---------------------------------------------------------------- 4
    s.append(PageBreak())
    s.append(P("4. Daily Coaching Rhythm &amp; Diagnostics", "h2"))

    s.append(P("Your day", "h3"))
    s.append(table([
        ["Time", "What you run", "Length"],
        ["8.45 a.m.", "Standup. Yesterday's number, today's target, one skill focus.", "15 min"],
        ["9.00 – 12.30", "Spot-check calls. Two per caller per hour until noon.", "—"],
        ["1.00 p.m.", "Half-day check. Read the funnel, diagnose, correct before the "
                      "afternoon window opens.", "15 min"],
        ["2.30 – 5.30", "Second window. Spot-check only where a caller is below standard.", "—"],
        ["6.00 p.m.", "Debrief. Numbers, one lesson learned, tomorrow's focus.", "20 min"],
    ], fit([62, None, 44], W)))

    s.append(P("Diagnosing a low number — read the funnel, not the total", "h3"))
    s.append(P("A low confirmed count has four different causes and four different "
               "fixes. Find where the funnel breaks before you coach anything."))
    s.append(table([
        ["Where it breaks", "Likely cause", "What you do"],
        ["Answer rate below 40%",
         "Wrong calling window, or a run of bad numbers",
         "Move to 9.00–12.30, check the next 20 numbers on the sheet, escalate if "
         "dead numbers exceed 30%"],
        ["Answered but interest below 15%",
         "Script problem — usually leading with 'free' or with the theme",
         "Listen to three consecutive calls. Re-drill Standards 3 and 5."],
        ["Interested but few links sent",
         "Caller is not sending during or immediately after the call",
         "Enforce: link goes out before the next number is dialled"],
        ["Links sent but few registered",
         "Friction in the form, or no follow-up",
         "Test the link yourself. Add a follow-up call after three hours."],
        ["Registered but not verified",
         "Incomplete capture — usually the CIDB number",
         "Re-drill the six required fields. An incomplete record does not count."],
    ], fit([88, 120, None], W)))

    s.append(callout(
        "GATE CHECKS",
        "Monday 6.00 p.m. the team should be at 40 confirmed. Tuesday 6.00 p.m. at "
        "75. Below 30 on Monday, escalate to Management that evening — not Tuesday. "
        "With only two calling days, a problem found on Tuesday morning has already "
        "cost half the campaign.", RED))

    # ---------------------------------------------------------------- 5
    s.append(PageBreak())
    s.append(P("5. Building Independence &amp; Success Standards", "h2"))

    s.append(P("Withdraw support on this schedule", "h3"))
    s.append(table([
        ["When", "Your role", "Caller's role"],
        ["Mon morning", "Demonstrate, score, correct after every call", "Copy the model exactly"],
        ["Mon afternoon", "Spot-check only. Answer questions when asked.", "Work independently, ask when stuck"],
        ["Tue morning", "Available for escalation. No routine listening.", "Fully independent"],
        ["Tue afternoon", "Read the sheet, not the calls.", "Self-correcting, helping each other"],
    ], fit([70, None, 150], W)))

    s.append(callout(
        "THE HANDOVER TEST",
        "By Tuesday a caller should be able to answer three questions without you: "
        "<i>What do I say if he asks whether it is really free? What do I do if he "
        "says send me the details first? What counts as a confirmed name?</i> "
        "If any caller cannot, they were certified too early — take fifteen minutes "
        "and fix it."))

    s.append(P("Signs the team is on the right path", "h3"))
    s.append(table([
        ["", "What you should see by Monday afternoon"],
        ["•", "Callers reaching the qualification question inside 45 seconds without reading"],
        ["•", "The Master Sheet updating live during calls, not in an evening batch"],
        ["•", "Callers asking each other for wording rather than asking you"],
        ["•", "Polite, unhurried closes on rejections"],
        ["•", "Someone volunteering an objection answer that is not on the sheet, and it being a good one"],
    ], fit([14, None], W)))

    s.append(P("Signs to intervene immediately", "h3"))
    s.append(table([
        ["", "Warning sign"],
        ["•", "Any link sent before voice confirmation — stop the caller, re-drill Standard 5"],
        ["•", "A contractor sounding annoyed or asking where the number came from"],
        ["•", "Records entered in batches at the end of a session"],
        ["•", "A caller inventing benefits not in the playbook"],
        ["•", "Anyone recording a name the contractor did not agree to by voice"],
    ], fit([14, None], W)))

    s.append(callout(
        "THE ONE FAILURE THAT MATTERS MOST",
        "A shortfall is recoverable. A padded namelist at an anti-corruption "
        "programme is not. If a caller is tempted to record an unconfirmed name to "
        "reach a milestone, that is a coaching emergency — deal with it in front "
        "of the whole team, immediately, and make the standard unmistakable.", RED))

    s.append(Spacer(1, 8))
    s.append(P("Mission Statement", "h3"))
    s.append(callout(
        "75 PLANNED  •  60 VERIFIED  •  QUALITY FIRST  •  ZERO INTEGRITY COMPROMISED",
        "Coach to the standard, not to the number. A team that holds the standard "
        "reaches the number; a team chasing the number loses both."))
    return s


def main(out: str) -> int:
    set_header(
        "LPC AI SANDBOX  |  IECONS 2026 DELEGATE DRIVE",
        "Trainer & Coach Guide  •  Companion to the Campaign Operations Playbook",
        "LPC-KAPT / TRAINER / 2026-08",
        "Internal Use Only  •  Trainer & Coach  •  Confidential",
        "Use alongside the Campaign Operations Playbook")
    build_doc(Path(out), story(), page=A4)
    print(f"  wrote {out}")
    return 0
