"""scout — public-profile talent scouting pipeline.

    python -m scout doctor
    python -m scout add <linkedin-url> [...]
    python -m scout add --from-file urls.txt
    python -m scout score --role roles/example-role.json
    python -m scout list [--status new] [--min-score 60]
    python -m scout show <id-or-slug>
    python -m scout status <id-or-slug> shortlist
    python -m scout note <id-or-slug> "spoke at DevFest"
    python -m scout export --csv out.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
from pathlib import Path

from . import fetch as fetch_mod
from . import parse_linkedin, score as score_mod, store

RATE_LIMIT_SECONDS = 3.0


def _err(msg: str) -> None:
    print(f"error: {msg}", file=sys.stderr)


def cmd_doctor(args: argparse.Namespace) -> int:
    probe = "https://www.linkedin.com/in/williamhgates/"
    print("scout doctor")
    print("-" * 46)
    ok = True
    try:
        body, transport = fetch_mod.fetch(probe, use_cache=not args.no_cache)
        gated = parse_linkedin.is_gated(body)
        rec = parse_linkedin.parse(body, probe)
        print(f"  transport used        : {transport} ({len(body):,} chars)")
        print(f"  structured data       : {rec['source']}")
        print(f"  public profile parsed : {'yes' if rec['name'] else 'no'} -> {rec['name']!r}")
        print(f"  experience entries    : {len(rec['experience'])}")
        print(f"  auth-walled           : {'yes' if gated else 'no'}")
        if gated or not rec["name"]:
            ok = False
    except Exception as e:  # noqa: BLE001
        print(f"  transport             : ALL FAILED\n    {e}")
        ok = False

    print(f"  JINA_API_KEY          : {'set' if os.environ.get('JINA_API_KEY') else 'not set'}"
          " (optional fallback)")

    print(f"  store                 : {len(store.load())} candidates")
    print("-" * 46)
    print("OK" if ok else "DEGRADED - see README troubleshooting")
    return 0 if ok else 1


def cmd_add(args: argparse.Namespace) -> int:
    # Saved-page path: you opened the profile in your own browser and saved it.
    # No automation touches the logged-in session; we only read the file.
    if args.html:
        path = Path(args.html)
        body = path.read_text(encoding="utf-8", errors="replace")
        rec = parse_linkedin.parse(body, args.url or "")
        if not rec["name"]:
            _err(f"could not parse a profile out of {path}")
            return 1
        if not rec["slug"] and not rec["url"]:
            _err("saved page has no profile URL — pass --url so it can be deduplicated")
            return 2
        rec["transport"] = "saved-html"
        saved, is_new = store.upsert(rec)
        print(f"  [{'new' if is_new else 'upd'}]     {saved['name']} — {saved['headline'][:60]}")
        return 0

    urls: list[str] = list(args.urls)
    if args.from_file:
        text = Path(args.from_file).read_text(encoding="utf-8")
        urls += [l.strip() for l in text.splitlines()
                 if l.strip() and not l.strip().startswith("#")]

    if not urls:
        _err("no URLs given (pass URLs, --from-file, or --html)")
        return 2

    created = updated = failed = gated = 0
    for i, url in enumerate(urls):
        if "linkedin.com/in/" not in url:
            _err(f"skipping non-profile URL: {url}")
            failed += 1
            continue
        try:
            body, transport = fetch_mod.fetch(url, use_cache=not args.no_cache)
            if parse_linkedin.is_gated(body):
                print(f"  [gated]   {url}")
                gated += 1
                continue
            rec = parse_linkedin.parse(body, url)
            if not rec["name"]:
                print(f"  [nodata]  {url}")
                failed += 1
                continue
            rec["transport"] = transport
            saved, is_new = store.upsert(rec)
            print(f"  [{'new' if is_new else 'upd'}]     {saved['name']} — "
                  f"{saved['headline'][:60]}")
            created += is_new
            updated += not is_new
        except Exception as e:  # noqa: BLE001
            print(f"  [fail]    {url} ({e})")
            failed += 1

        if i < len(urls) - 1:
            time.sleep(RATE_LIMIT_SECONDS)

    print(f"\n{created} new, {updated} updated, {gated} gated, {failed} failed")
    return 0


def cmd_score(args: argparse.Namespace) -> int:
    role = score_mod.load_role(args.role)
    records = store.load()
    if not records:
        _err("no candidates in store — run `scout add` first")
        return 1

    for rec in records:
        result = score_mod.score(rec, role)
        rec["score"] = result["score"]
        rec["score_detail"] = result
        rec["scored_against"] = role.get("role", str(args.role))
    store.save_all(records)

    ranked = sorted(records, key=lambda r: r.get("score", 0), reverse=True)
    print(f"Scored {len(records)} candidates against: {role.get('role', '?')}\n")
    for rec in ranked[:args.top]:
        print(f"  {rec['score']:5.1f}  {rec['name'][:28]:28}  {rec['headline'][:44]}")
        detail = rec["score_detail"]
        if detail["matched"]["must_have"]:
            print(f"         + {', '.join(detail['matched']['must_have'])}")
        if detail["missing"]:
            print(f"         - missing: {', '.join(detail['missing'])}")
        for flag in detail["flags"]:
            print(f"         ! {flag}")
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    rows = list(store.iter_filtered(args.status, args.min_score))
    rows.sort(key=lambda r: r.get("score", 0), reverse=True)
    if not rows:
        print("no candidates match")
        return 0
    print(f"{'SCORE':>6}  {'STATUS':<12}  {'NAME':<26}  HEADLINE")
    for rec in rows:
        sc = rec.get("score")
        print(f"{(f'{sc:.1f}' if sc is not None else '—'):>6}  "
              f"{rec.get('status', 'new'):<12}  {rec.get('name', '')[:26]:<26}  "
              f"{rec.get('headline', '')[:50]}")
    print(f"\n{len(rows)} candidate(s)")
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    for rec in store.load():
        if args.id in (rec.get("id"), rec.get("slug")):
            print(json.dumps(rec, indent=2, ensure_ascii=False))
            return 0
    _err(f"not found: {args.id}")
    return 1


def cmd_status(args: argparse.Namespace) -> int:
    try:
        rec = store.set_status(args.id, args.new_status)
    except ValueError as e:
        _err(str(e))
        return 2
    if not rec:
        _err(f"not found: {args.id}")
        return 1
    print(f"{rec['name']} -> {rec['status']}")
    return 0


def cmd_note(args: argparse.Namespace) -> int:
    rec = store.add_note(args.id, args.text)
    if not rec:
        _err(f"not found: {args.id}")
        return 1
    print(f"note added to {rec['name']}")
    return 0


def cmd_export(args: argparse.Namespace) -> int:
    rows = list(store.iter_filtered(args.status, args.min_score))
    rows.sort(key=lambda r: r.get("score", 0), reverse=True)
    fields = ["score", "status", "name", "headline", "location",
              "current_title", "current_company", "url", "notes"]
    out = Path(args.csv)
    with out.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for rec in rows:
            writer.writerow({k: rec.get(k, "") for k in fields})
    print(f"wrote {len(rows)} rows -> {out}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="scout", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--no-cache", action="store_true", help="bypass the local page cache")
    sub = p.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("doctor", help="check connectivity and parsing health")
    d.set_defaults(func=cmd_doctor)

    a = sub.add_parser("add", help="fetch + store public profiles")
    a.add_argument("urls", nargs="*")
    a.add_argument("--from-file", help="file with one profile URL per line")
    a.add_argument("--html", help="parse a page you saved from your own browser")
    a.add_argument("--url", help="canonical profile URL, used with --html")
    a.set_defaults(func=cmd_add)

    s = sub.add_parser("score", help="score everyone against a role brief")
    s.add_argument("--role", required=True, help="path to a role brief JSON")
    s.add_argument("--top", type=int, default=15)
    s.set_defaults(func=cmd_score)

    l = sub.add_parser("list", help="list candidates")
    l.add_argument("--status")
    l.add_argument("--min-score", type=float)
    l.set_defaults(func=cmd_list)

    sh = sub.add_parser("show", help="dump one candidate as JSON")
    sh.add_argument("id")
    sh.set_defaults(func=cmd_show)

    st = sub.add_parser("status", help="move a candidate through the pipeline")
    st.add_argument("id")
    st.add_argument("new_status", choices=store.STATUSES)
    st.set_defaults(func=cmd_status)

    n = sub.add_parser("note", help="attach a note")
    n.add_argument("id")
    n.add_argument("text")
    n.set_defaults(func=cmd_note)

    e = sub.add_parser("export", help="export to CSV")
    e.add_argument("--csv", required=True)
    e.add_argument("--status")
    e.add_argument("--min-score", type=float)
    e.set_defaults(func=cmd_export)

    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
