#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
PREFERRED_PATH = ROOT_DIR / "ops/tests/temperature-assets/preferred/quality-audit-preferred.jsonl"
INVENTORY_PATH = ROOT_DIR / "ops/tests/temperature-assets/inventory.jsonl"
PAIRS_INBOX_DIR = ROOT_DIR / "ops/tests/temperature-assets/pairs/inbox"
PAIR_BUILDER = ROOT_DIR / "scripts/build-coconala-temperature-pairs.py"
RERANKER_EXPORTER = ROOT_DIR / "scripts/export-coconala-temperature-reranker-set.py"


def read_text_arg(*, file_path: str | None, text_value: str | None) -> str:
    if file_path:
        return Path(file_path).read_text(encoding="utf-8").strip()
    if text_value:
        return text_value.strip()
    return ""


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
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Save or update a preferred reply row for temperature pair assets.")
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--preferred-file")
    parser.add_argument("--preferred-text")
    parser.add_argument("--user-file")
    parser.add_argument("--user-text")
    parser.add_argument("--signal", action="append", default=[])
    parser.add_argument("--bucket", action="append", default=[])
    parser.add_argument("--send-ok", default="")
    parser.add_argument("--report-path", default="")
    parser.add_argument("--rebuild-pairs", action="store_true")
    parser.add_argument("--refresh-assets", action="store_true")
    args = parser.parse_args()

    preferred_reply = read_text_arg(file_path=args.preferred_file, text_value=args.preferred_text)
    if not preferred_reply:
        raise SystemExit("preferred reply is required via --preferred-file or --preferred-text")

    preferred_index = load_jsonl_index(PREFERRED_PATH, "case_id")
    inventory_index = load_jsonl_index(INVENTORY_PATH, "case_id")
    draft_index = load_draft_index(PAIRS_INBOX_DIR)

    existing = preferred_index.get(args.case_id, {})
    inventory_row = inventory_index.get(args.case_id, {})
    draft_row = draft_index.get(args.case_id, {})
    user_message = read_text_arg(file_path=args.user_file, text_value=args.user_text)

    payload = {
        "case_id": args.case_id,
        "report_path": args.report_path or existing.get("report_path", ""),
        "user_message": user_message
        or draft_row.get("user_message")
        or existing.get("user_message", "")
        or inventory_row.get("raw_message", ""),
        "preferred_reply": preferred_reply,
        "signals": args.signal or existing.get("signals") or draft_row.get("signals") or inventory_row.get("signals", []),
        "buckets": args.bucket or existing.get("buckets") or draft_row.get("buckets") or inventory_row.get("buckets", []),
        "send_ok": args.send_ok or existing.get("send_ok", ""),
    }

    preferred_index[args.case_id] = payload
    rows = [preferred_index[key] for key in sorted(preferred_index)]
    write_jsonl(PREFERRED_PATH, rows)
    print(PREFERRED_PATH)

    if args.rebuild_pairs or args.refresh_assets:
        subprocess.run(["python3", str(PAIR_BUILDER), "--save-report"], check=True)
    if args.refresh_assets:
        subprocess.run(["python3", str(RERANKER_EXPORTER), "--save-report"], check=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
