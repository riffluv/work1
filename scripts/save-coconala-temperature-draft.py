#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
PAIRS_INBOX_DIR = ROOT_DIR / "ops/tests/temperature-assets/pairs/inbox"
INVENTORY_PATH = ROOT_DIR / "ops/tests/temperature-assets/inventory.jsonl"
PREFERRED_PATH = ROOT_DIR / "ops/tests/temperature-assets/preferred/quality-audit-preferred.jsonl"
PAIR_BUILDER = ROOT_DIR / "scripts/build-coconala-temperature-pairs.py"
RERANKER_EXPORTER = ROOT_DIR / "scripts/export-coconala-temperature-reranker-set.py"
RUNTIME_REPLY_PATH = ROOT_DIR / "runtime/replies/latest.txt"
RUNTIME_SOURCE_PATH = ROOT_DIR / "runtime/replies/latest-source.txt"


def read_text_arg(*, file_path: str | None, text_value: str | None) -> str:
    if file_path:
        return Path(file_path).read_text(encoding="utf-8").strip()
    if text_value:
        return text_value.strip()
    return ""


def read_runtime_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8").strip()


def load_jsonl_index(path: Path, key_name: str) -> dict[str, dict]:
    if not path.exists():
        return {}
    rows: dict[str, dict] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        row = json.loads(line)
        key = row.get(key_name)
        if key:
            rows[key] = row
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description="Save a temperature draft sample for later pairwise joining.")
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--draft-file")
    parser.add_argument("--draft-text")
    parser.add_argument("--source-file")
    parser.add_argument("--source-text")
    parser.add_argument("--bucket", action="append", default=[])
    parser.add_argument("--signal", action="append", default=[])
    parser.add_argument("--from-runtime", action="store_true")
    parser.add_argument("--refresh-assets", action="store_true")
    args = parser.parse_args()

    draft_reply = read_text_arg(file_path=args.draft_file, text_value=args.draft_text)
    if args.from_runtime and not draft_reply:
        draft_reply = read_runtime_text(RUNTIME_REPLY_PATH)
    if not draft_reply:
        raise SystemExit("draft reply is required via --draft-file or --draft-text")
    user_message = read_text_arg(file_path=args.source_file, text_value=args.source_text)
    if args.from_runtime and not user_message:
        user_message = read_runtime_text(RUNTIME_SOURCE_PATH)

    inventory_index = load_jsonl_index(INVENTORY_PATH, "case_id")
    preferred_index = load_jsonl_index(PREFERRED_PATH, "case_id")
    inventory_row = inventory_index.get(args.case_id, {})
    preferred_row = preferred_index.get(args.case_id, {})

    payload = {
        "case_id": args.case_id,
        "user_message": user_message or preferred_row.get("user_message") or inventory_row.get("raw_message", ""),
        "draft_reply": draft_reply,
        "signals": args.signal or preferred_row.get("signals") or inventory_row.get("signals", []),
        "buckets": args.bucket or preferred_row.get("buckets") or inventory_row.get("buckets", []),
        "source_name": inventory_row.get("source_name", ""),
        "source_role": inventory_row.get("source_role", ""),
    }

    PAIRS_INBOX_DIR.mkdir(parents=True, exist_ok=True)
    out_path = PAIRS_INBOX_DIR / f"{args.case_id}.json"
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(out_path)

    if args.refresh_assets:
        subprocess.run(["python3", str(PAIR_BUILDER), "--save-report"], check=True)
        subprocess.run(["python3", str(RERANKER_EXPORTER), "--save-report"], check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
