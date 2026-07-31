"""JSONL-backed candidate store with dedup and pipeline status."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
STORE = DATA_DIR / "candidates.jsonl"

STATUSES = ("new", "shortlist", "contacted", "replied", "interviewing", "hired", "rejected")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def candidate_id(rec: dict[str, Any]) -> str:
    """Stable identity: platform slug when present, else the URL."""
    return f"{rec.get('platform', '?')}:{rec.get('slug') or rec.get('url', '')}".lower()


def load() -> list[dict[str, Any]]:
    if not STORE.exists():
        return []
    out: list[dict[str, Any]] = []
    for line in STORE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            out.append(json.loads(line))
    return out


def save_all(records: list[dict[str, Any]]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with STORE.open("w", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")


def upsert(rec: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    """Insert or merge a candidate. Returns (record, created)."""
    records = load()
    cid = candidate_id(rec)
    for i, existing in enumerate(records):
        if candidate_id(existing) == cid:
            # Preserve human-owned fields; refresh scraped ones.
            merged = {**existing, **{k: v for k, v in rec.items() if v not in ("", [], None)}}
            merged["status"] = existing.get("status", "new")
            merged["notes"] = existing.get("notes", "")
            merged["updated_at"] = _now()
            records[i] = merged
            save_all(records)
            return merged, False

    rec = {**rec, "id": cid, "status": "new", "notes": "",
           "added_at": _now(), "updated_at": _now()}
    records.append(rec)
    save_all(records)
    return rec, True


def set_status(cid: str, status: str) -> dict[str, Any] | None:
    if status not in STATUSES:
        raise ValueError(f"status must be one of {', '.join(STATUSES)}")
    records = load()
    for rec in records:
        if rec.get("id") == cid or rec.get("slug") == cid:
            rec["status"] = status
            rec["updated_at"] = _now()
            save_all(records)
            return rec
    return None


def add_note(cid: str, note: str) -> dict[str, Any] | None:
    records = load()
    for rec in records:
        if rec.get("id") == cid or rec.get("slug") == cid:
            prior = rec.get("notes", "")
            rec["notes"] = f"{prior}\n{note}".strip() if prior else note
            rec["updated_at"] = _now()
            save_all(records)
            return rec
    return None


def iter_filtered(status: str | None = None, min_score: float | None = None
                  ) -> Iterator[dict[str, Any]]:
    for rec in load():
        if status and rec.get("status") != status:
            continue
        if min_score is not None and (rec.get("score") or 0) < min_score:
            continue
        yield rec
