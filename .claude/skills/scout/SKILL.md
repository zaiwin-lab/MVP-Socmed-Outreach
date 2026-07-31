---
name: scout
description: Find, triage, and track potential hires from public LinkedIn profiles. Use when the user wants to scout staff, source candidates, screen a talent pool, build a shortlist, or draft recruiting outreach. Also covers Facebook-side discovery via Agent Reach.
---

# scout — staff scouting

Drive the `scout` CLI in this repo to source and triage candidates.

## The split

You do **discovery** (you have web search; scripted search engines get blocked).
`scout` does **fetching, parsing, scoring, and tracking**. Never try to make the
CLI perform searches.

## Workflow

### 1. Pin down the brief first

Do not start searching until you know: role, location, must-have skills,
nice-to-haves, and any dealbreakers. Ask if the user has not said.

Write it to `roles/<slug>.json` following `roles/example-role.json`. Keep
`must_have` short — 3 to 5 terms. Every extra must-have drags scores down and
buries good people.

Terms are matched on word boundaries against headline, about, titles, employers,
and schools. So `"meta ads"` matches, `"advertising expert"` as a must-have does
not — write terms the way people write them on their own profiles.

### 2. Discover

Search for public profiles. Effective patterns:

- `site:linkedin.com/in "digital marketing" Kuching`
- `site:linkedin.com/in "<job title>" "<city>"`
- `site:linkedin.com/in "<skill>" "<company they'd come from>"`

Collect profile URLs into a file, one per line.

### 3. Add

```bash
python3 -m scout add --from-file /tmp/urls.txt
```

Read the output. `[gated]` means LinkedIn served an auth wall — do not retry it
in a loop, and never try to get around it. `HTTP 999` across the board means the
IP is throttled; tell the user to run it locally rather than grinding.

### 4. Score

```bash
python3 -m scout score --role roles/<slug>.json
```

Then **read the top candidates yourself** with `scout show <slug>`. The score is
keyword triage. Your job is the judgement it cannot make: career trajectory,
whether the experience is real depth or a list of titles, whether someone at a
big agency would actually take a small-team role.

Report a ranked shortlist with a one-line reason per person — the reason should
come from what you read, not from the score.

### 5. Track

```bash
python3 -m scout status <slug> shortlist
python3 -m scout note <slug> "why they're interesting"
python3 -m scout export --csv shortlist.csv
```

## Drafting outreach

When asked, draft per-candidate messages. Use `outreach_angle` from the role
brief and something specific from that person's actual profile.

Rules that make outreach land:

- Short. Under 120 words. LinkedIn opens on a phone.
- Say why *them* — reference real work from their profile, not "your impressive
  background".
- Be concrete about the role and that it is a real opening.
- One clear ask: a short call.
- No fake familiarity, no invented mutual connections, no flattery you cannot
  back up.

Draft them for the user to send. Do not send anything, and do not offer to
automate sending — outreach volume is what gets accounts restricted.

## Facebook

`scout` does not read Facebook. That needs Agent Reach on a desktop machine with
a logged-in browser session (see `SETUP.md`). If the user asks for Facebook
scouting:

- Point them to `SETUP.md` section 3.
- Be straight that it drives their own logged-in session, that it cannot run in a
  cloud session, and that a secondary account is wise.
- Use Facebook for discovery (groups, local business pages), then evaluate those
  people via their LinkedIn.

## Hard lines

- Public, logged-out pages only. Never automate a logged-in session, replay
  cookies, or work around an auth wall — for any platform.
- Never commit anything under `data/`. It is personal data and it is gitignored
  for a reason.
- Collect what the role needs, not everything obtainable.
- Do not infer protected characteristics (age, race, religion, gender, marital
  or family status, health) from a profile, and do not let them influence a
  score or a recommendation. If a role brief contains such a term, say so and
  refuse to score on it.
