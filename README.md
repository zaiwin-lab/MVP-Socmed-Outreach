# Scout — Explainable Talent Sourcing & Triage

> **Portfolio maturity:** Functional Prototype · Local-First, Human-in-the-Loop Recruitment Intelligence

Scout is a dependency-free Python workflow for collecting public professional-profile information, comparing it with a role brief and organising candidates for human review.

It is designed to reduce repetitive sourcing work without turning an automated score into a hiring decision. The repository name retains MVP for development history; **Scout** is the permanent product identity.

## Business problem

Small recruitment and programme teams often move between browser tabs, spreadsheets and messaging threads when building a candidate pipeline. That creates inconsistent records, repeated searches and opaque shortlisting decisions.

Scout provides one auditable workflow:

**Discover → add → structure → score → shortlist → outreach → track**

## Intended users

- small recruitment and talent-sourcing teams;
- programme operators identifying trainers, facilitators or specialist contributors;
- hiring managers who need a transparent first-pass review;
- technical operators who prefer a local command-line workflow.

## Core capabilities

- reads deliberately public, logged-out LinkedIn profile data when available;
- accepts user-saved HTML for pages that require manual browser access;
- structures profile facts into a local candidate record;
- compares candidates with role-specific JSON criteria;
- explains matched, missing and exclusion terms behind each score;
- supports pipeline states, notes, deduplication and CSV export;
- applies request spacing and a 14-day cache to reduce repeated network access;
- includes offline test fixtures and a test script;
- can be operated manually or through the repository's Claude Code skill.

## Strategic value

Scout demonstrates an AI-assisted operating pattern where automation prepares evidence but people retain judgment. Its value is not a claim of perfect candidate prediction; it is a repeatable and inspectable process that can:

- reduce administrative sourcing effort;
- make first-pass criteria visible and contestable;
- keep candidate data local by default;
- separate evidence collection from hiring decisions;
- support a documented handoff from discovery to outreach.

## What is implemented

The repository contains a Python 3.9+ command-line application with modules for fetching, parsing, scoring, storage, auditing, exports and pipeline management. It also includes role-brief examples, offline fixtures and tests.

### Technology

Python standard library · JSON and JSONL · CSV export · JSON-LD parsing · local file storage · optional Jina transport · Claude Code skill integration

No cloud database, hosted dashboard or autonomous messaging service is included.

## Delivery role

**Ts. Zaiwin Kassim** leads product strategy, stakeholder requirements, solution architecture and supervised AI-assisted delivery with the **KOBIS AI Prodigy Team**. For Scout, that delivery role centres on the recruitment workflow, explainability, privacy boundaries and human approval points.

This portfolio attribution does not claim endorsement, deployment or affiliation by LinkedIn, Facebook, Jina or any other platform named for technical context.

## Responsible-use boundaries

Scout is a triage aid, not a hiring authority.

- A score ranks records for closer reading; it does not establish competence, suitability or employability.
- Only public, logged-out pages are fetched automatically.
- The tool does not replay credentials, store browser sessions or bypass authentication walls.
- Gated pages are skipped unless the user manually saves content they are authorised to review.
- Candidate records are personal data and must be collected for a legitimate purpose, minimised, protected, retained only as needed and deleted when no longer required.
- Sensitive attributes must not be inferred or used as proxy hiring criteria.
- Outreach requires human review and must not be sent automatically from a score.
- Teams remain responsible for applicable privacy, employment, anti-discrimination and platform rules, including Malaysia's PDPA where relevant.

## Known limitations

- Public profile formats and platform access controls can change without notice.
- Datacenter traffic may be throttled; the repository documents HTTP 999 behaviour observed during development.
- Profile data can be incomplete, outdated or self-reported.
- Keyword scoring can miss transferable experience and can encode a weak role brief.
- Location, identity and employment claims are not independently verified.
- The repository includes offline tests, but this README does not claim current production certification.
- There is no verified hosted demo; Scout is a local command-line tool.

## Quick start

Requirements: Python 3.9 or later. No third-party package installation is required for the core workflow.

    python3 -m scout doctor
    python3 -m scout add https://www.linkedin.com/in/some-profile/
    python3 -m scout score --role roles/example-role.json
    python3 -m scout list --min-score 60
    python3 -m scout status some-profile shortlist
    python3 -m scout export --csv shortlist.csv

Run the offline tests:

    python3 tests/test_scout.py

For a manually saved page:

    python3 -m scout add --html ~/Downloads/profile.html --url https://www.linkedin.com/in/that-person/

See **SETUP.md** for transport details and the boundaries around Facebook scouting.

## Main commands

| Command | Purpose |
|---|---|
| **doctor** | Check transport, parsing and local-store health |
| **add** | Add public URLs or user-saved HTML |
| **score --role R** | Apply a transparent role rubric |
| **list** | Filter candidates by state or minimum score |
| **show ID** | Inspect one structured candidate record |
| **status ID S** | Update the human-managed pipeline stage |
| **note ID TEXT** | Add a reviewer note |
| **export --csv FILE** | Export records for authorised review |

## Repository map

- **scout/fetch.py** — transports, caching and backoff
- **scout/parse_linkedin.py** — JSON-LD and fallback parsing
- **scout/score.py** — explainable role-rubric scoring
- **scout/store.py** — local records, deduplication and status
- **scout/audit.py** — workflow audit support
- **scout/make_pdf.py** and **scout/make_xlsx.py** — reporting exports
- **roles** — role-brief definitions
- **tests** — offline fixtures and test coverage
- **data** — local candidate records and cache; intentionally ignored by Git

## Portfolio evidence

Scout demonstrates explainable ranking, privacy-aware data handling, local-first architecture and human-controlled AI assistance. It should be evaluated as a functional prototype for governed sourcing workflows, not as an autonomous recruiter or validated predictor of job performance.
