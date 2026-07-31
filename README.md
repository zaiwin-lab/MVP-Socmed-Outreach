# scout — staff scouting from public profiles

A small, dependency-free pipeline for finding and triaging potential hires from
**public** LinkedIn profiles, scoring them against a role brief, and tracking
them through a hiring pipeline.

Built to be driven either by hand or by Claude Code (see `.claude/skills/scout/`).

```
discover  →  add  →  score  →  shortlist  →  outreach  →  track
(search)     (fetch)  (rubric)  (your call)   (your words)  (status)
```

## Quick start

Python 3.9+. No dependencies, no install step.

```bash
python3 -m scout doctor                              # check connectivity
python3 -m scout add https://www.linkedin.com/in/some-profile/
python3 -m scout score --role roles/example-role.json
python3 -m scout list --min-score 60
python3 -m scout status some-profile shortlist
python3 -m scout export --csv shortlist.csv
```

Run the tests (offline, no network):

```bash
python3 tests/test_scout.py
```

## Where to run this

**Run it on your own machine.** This matters more than it sounds.

LinkedIn aggressively throttles datacenter IPs. From a cloud container the first
request often succeeds and everything after it returns `HTTP 999`. From a normal
home or office connection it behaves fine. Verified during development: the exact
same code parsed a full profile on the first call from a cloud host, then got
`999` on every subsequent call.

| Environment | LinkedIn public fetch | Facebook |
|---|---|---|
| Your laptop / desktop | works | works via Agent Reach (see `SETUP.md`) |
| Cloud container / CI | rate-limited fast | not available |

If you must run from a cloud host, set a free `JINA_API_KEY` (see `SETUP.md`) so
the fallback transport is usable.

## How a profile is read

Every public LinkedIn profile embeds a JSON-LD `Person` block — the same
structured data LinkedIn hands to search engines. That is what `scout` reads:

- name, headline, location
- roles with employer and start/end years
- education with years
- follower count, badges, languages

It is far more reliable than scraping rendered HTML, and it is the data LinkedIn
publishes deliberately. If JSON-LD is missing, a markdown fallback recovers the
basics.

Three transports, tried in order:

1. **direct** — a plain logged-out HTTPS GET. What a crawler sees.
2. **jina** — `r.jina.ai` rendering. Anonymous use is blocked from most
   datacenter IPs; set `JINA_API_KEY` to make it dependable.
3. **saved-html** — you open a page in your own browser, save it, and pass it in:

   ```bash
   python3 -m scout add --html ~/Downloads/profile.html \
                        --url https://www.linkedin.com/in/that-person/
   ```

   This is the route for anything that needs you to be logged in. You do the
   browsing; `scout` only structures the file you saved.

## Scoring

Role briefs are plain JSON (`roles/example-role.json`). Scoring is deliberately
transparent — every point traces back to a matched term, so you can argue with it:

```
   82.0  Nurul A.                      Digital Marketing Executive at ...
         + digital marketing, social media, meta ads
         - missing: content
         ! location not confirmed against brief
```

Weights are per-role (`must_have` / `nice_to_have` / `location`). An `exclude`
hit multiplies the score by 0.4 rather than zeroing it, so a promising person
is flagged rather than silently dropped.

**The score is triage, not a decision.** It ranks who to read properly. It does
not know who is good at the job.

## Boundaries

This tool is built to stay on the right side of the line:

- Only public, logged-out pages are fetched. No cookies, no stored sessions, no
  credential replay, no logging in as you.
- No attempt to defeat an auth wall. Gated profiles are reported as `[gated]`
  and skipped.
- Requests are rate-limited (3s apart) and cached for 14 days, so a re-score
  never re-hits the network.
- Anything requiring a login is your manual step, via `--html`.

Automating a logged-in LinkedIn or Facebook session violates their terms and
risks your account. `scout` does not do it, and you should not bolt it on.

### Personal data

Candidate records are personal data. Under Malaysia's PDPA (and GDPR if you ever
recruit into the EU) that carries real obligations:

- `data/` is gitignored — **do not commit candidate files.**
- Collect only what is relevant to the role. Delete people you reject.
- Be ready to tell someone what you hold on them and why, if asked.
- Use it for recruiting, which is what it is for.

## Layout

```
scout/
  fetch.py           transports, caching, backoff
  parse_linkedin.py  JSON-LD → candidate record
  score.py           explainable rubric scoring
  store.py           JSONL store, dedup, pipeline status
  cli.py             command line entry point
roles/               role briefs (JSON)
tests/               offline tests + fixture
data/                candidates + page cache (gitignored)
.claude/skills/scout/  Claude Code skill
```

## Commands

| Command | Purpose |
|---|---|
| `doctor` | check transports, parsing, store health |
| `add` | fetch + store profiles (URLs, `--from-file`, `--html`) |
| `score --role R` | score everyone against a role brief |
| `list` | list candidates, `--status`, `--min-score` |
| `show ID` | dump one candidate as JSON |
| `status ID S` | move through `new → shortlist → contacted → replied → interviewing → hired/rejected` |
| `note ID "..."` | attach a note |
| `export --csv F` | export to CSV |

See `SETUP.md` for Facebook scouting via Agent Reach.
