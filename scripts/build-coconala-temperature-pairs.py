#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT_DIR = Path(__file__).resolve().parents[1]
PAIRS_DIR = ROOT_DIR / "ops/tests/temperature-assets/pairs"
PAIRS_INBOX_DIR = PAIRS_DIR / "inbox"
PREFERRED_PATH = ROOT_DIR / "ops/tests/temperature-assets/preferred/quality-audit-preferred.jsonl"
REPORT_DIR = ROOT_DIR / "runtime/regression/coconala-reply/temperature/pairs"
JST = ZoneInfo("Asia/Tokyo")


def load_jsonl_index(path: Path, key_name: str) -> dict[str, dict]:
    rows: dict[str, dict] = {}
    if not path.exists():
        return rows
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        row = json.loads(line)
        key = row.get(key_name)
        if key:
            rows[key] = row
    return rows


def load_draft_index(path: Path) -> dict[str, dict]:
    rows: dict[str, dict] = {}
    if not path.exists():
        return rows
    for item in sorted(path.glob("*.json")):
        row = json.loads(item.read_text(encoding="utf-8"))
        case_id = row.get("case_id")
        if case_id:
            rows[case_id] = row
    return rows


def write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def build_summary(started_at: datetime, complete_rows: list[dict], pending_preferred_rows: list[dict], dangling_draft_rows: list[dict]) -> str:
    bucket_counts = Counter()
    for row in complete_rows:
        for bucket in row.get("buckets", []):
            bucket_counts[bucket] += 1

    lines = [
        f"generated_at: {started_at.strftime('%Y-%m-%d %H:%M:%S %Z')}",
        f"complete_pairs: {len(complete_rows)}",
        f"pending_preferred_only: {len(pending_preferred_rows)}",
        f"dangling_drafts: {len(dangling_draft_rows)}",
        "",
        "[bucket_counts]",
    ]
    for bucket, count in sorted(bucket_counts.items()):
        lines.append(f"{bucket}: {count}")
    lines.extend(["", "[notes]"])
    lines.append("- complete_pairs は draft_reply と preferred_reply の両方が揃っている件数")
    lines.append("- pending_preferred_only は preferred rewrite はあるが、draft が未保存の件数")
    lines.append("- dangling_drafts は draft はあるが、preferred rewrite が未接続の件数")
    return "\n".join(lines) + "\n"


def save_report(text: str, started_at: datetime) -> tuple[Path, Path]:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = started_at.strftime("%Y%m%d-%H%M%S")
    latest_path = REPORT_DIR / "latest.txt"
    history_path = REPORT_DIR / f"{stamp}.txt"
    latest_path.write_text(text, encoding="utf-8")
    history_path.write_text(text, encoding="utf-8")
    return latest_path, history_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Join saved temperature drafts with preferred rewrites.")
    parser.add_argument("--preferred", default=str(PREFERRED_PATH))
    parser.add_argument("--draft-dir", default=str(PAIRS_INBOX_DIR))
    parser.add_argument("--save-report", action="store_true")
    args = parser.parse_args()

    preferred_index = load_jsonl_index(Path(args.preferred), "case_id")
    draft_index = load_draft_index(Path(args.draft_dir))

    complete_rows: list[dict] = []
    pending_preferred_rows: list[dict] = []
    for case_id, preferred in sorted(preferred_index.items()):
        draft = draft_index.get(case_id)
        if not draft:
            pending_preferred_rows.append(preferred)
            continue
        complete_rows.append(
            {
                "case_id": case_id,
                "user_message": draft.get("user_message") or preferred.get("user_message", ""),
                "draft_reply": draft.get("draft_reply", ""),
                "preferred_reply": preferred.get("preferred_reply", ""),
                "signals": preferred.get("signals") or draft.get("signals", []),
                "buckets": preferred.get("buckets") or draft.get("buckets", []),
                "send_ok": preferred.get("send_ok", ""),
                "preferred_source": preferred.get("report_path", ""),
                "draft_source_name": draft.get("source_name", ""),
                "draft_source_role": draft.get("source_role", ""),
            }
        )

    dangling_draft_rows = [draft for case_id, draft in sorted(draft_index.items()) if case_id not in preferred_index]

    PAIRS_DIR.mkdir(parents=True, exist_ok=True)
    write_jsonl(PAIRS_DIR / "complete.jsonl", complete_rows)
    write_jsonl(PAIRS_DIR / "pending-preferred-only.jsonl", pending_preferred_rows)
    write_jsonl(PAIRS_DIR / "dangling-drafts.jsonl", dangling_draft_rows)

    started_at = datetime.now(JST)
    summary = build_summary(started_at, complete_rows, pending_preferred_rows, dangling_draft_rows)
    if args.save_report:
        latest_path, history_path = save_report(summary, started_at)
        print(f"report_latest: {latest_path}")
        print(f"report_history: {history_path}")
    print(summary.rstrip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
