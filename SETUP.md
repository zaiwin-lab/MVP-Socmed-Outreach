# Setup

## 1. scout itself

Nothing to install. Python 3.9+ and the standard library.

```bash
git clone <this repo>
cd MVP-Socmed-Outreach
python3 -m scout doctor
python3 tests/test_scout.py
```

A healthy `doctor` looks like this:

```
scout doctor
----------------------------------------------
  transport used        : direct (666,382 chars)
  structured data       : json-ld
  public profile parsed : yes -> 'Bill Gates'
  experience entries    : 3
  auth-walled           : no
  JINA_API_KEY          : not set (optional fallback)
  store                 : 0 candidates
----------------------------------------------
OK
```

If you see `HTTP 999`, LinkedIn is throttling your IP. Options, in order of
preference: run from a normal home/office connection, wait it out, or set a
`JINA_API_KEY`.

## 2. Optional — JINA_API_KEY

Only needed if the direct transport is blocked (cloud host, or a heavily
throttled connection). Free tier, no card required.

1. Get a key at <https://jina.ai/reader/>
2. `export JINA_API_KEY=jina_xxxxx` (add it to your shell profile)
3. `python3 -m scout doctor` should now show `JINA_API_KEY : set`

Without a key, `r.jina.ai` returns
`401 — blocked from performing anonymous queries due to bad IP reputation`
from most datacenter IPs.

## 3. Facebook scouting — Agent Reach

`scout` handles LinkedIn. Facebook has no public JSON-LD equivalent and no
logged-out profile search, so it needs a different tool:
[Agent Reach](https://github.com/Panniantong/Agent-Reach) (MIT).

**What it actually does — worth being clear about, because the summaries
circulating about it overstate things:**

| Platform | What Agent Reach gives you | Requirement |
|---|---|---|
| LinkedIn | public pages via Jina Reader | zero config (or a key) |
| Facebook | search, profiles, feed, groups list | **desktop + your logged-in browser session** |
| Instagram | user search, profiles, recent posts | desktop + logged-in session |
| Twitter/X | read + search | cookie |
| Reddit | read + search | login |
| YouTube, GitHub, RSS, web | read + search | zero config |

It does **not** magically bypass gated platforms, and "zero API fees" is not the
same as zero cost or zero risk. Facebook and Instagram access works by driving a
browser you are already logged into. That means:

- It only runs on a desktop machine, not in a cloud container or CI.
- You are acting as yourself. Automated activity on your main account can get it
  restricted. Use a secondary account you can afford to lose.
- You remain bound by Facebook's terms. Scraping at volume breaches them.

### Install

```bash
pipx install https://github.com/Panniantong/agent-reach/archive/main.zip
agent-reach install --env=auto
agent-reach doctor
```

If your Python is externally managed (Homebrew, most Linux distros):

```bash
python3 -m venv ~/.agent-reach-venv
source ~/.agent-reach-venv/bin/activate
pip install https://github.com/Panniantong/agent-reach/archive/main.zip
agent-reach install --env=auto
```

It is **not** on PyPI — `pip install agent-reach` will fail. Install from the
archive URL above. Config lands in `~/.agent-reach/`.

### Feeding Facebook finds back into scout

Agent Reach gives you profiles and group members. To triage them alongside your
LinkedIn candidates, the practical loop is:

1. Use Agent Reach to find people (group members, page followers, local
   business pages).
2. For anyone promising, find their LinkedIn and `scout add` that URL — LinkedIn
   is where the professional history actually lives.
3. For Facebook-only candidates, save the profile page from your browser and
   `scout add --html saved.html --url <fb-url>`, then add notes by hand.

Facebook is better at **discovery** (who is in the local F&B operators group,
who runs that shop). LinkedIn is better at **evaluation**. Use each for what it
is good at.

## 4. Claude Code integration

The `/scout` skill in `.claude/skills/scout/` wires this into Claude Code so you
can say "find me a digital marketing exec in Kuching" and have Claude run
discovery, add the profiles, score them, and draft outreach.

Claude handles the search step (it has web search); `scout` handles fetching,
parsing, scoring, and tracking. That split is deliberate — search engines block
scripted queries, but Claude can search natively.
