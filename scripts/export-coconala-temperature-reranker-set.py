#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT_DIR = Path(__file__).resolve().parents[1]
PAIRS_COMPLETE_PATH = ROOT_DIR / "ops/tests/temperature-assets/pairs/complete.jsonl"
EXPORT_DIR = ROOT_DIR / "ops/tests/temperature-assets/reranker"
REPORT_DIR = ROOT_DIR / "runtime/regression/coconala-reply/temperature/reranker"
JST = ZoneInfo("Asia/Tokyo")


def load_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    if not path.exists():
        return rows
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def stable_bucket(case_id: str, holdout_ratio: float) -> str:
    digest = hashlib.sha256(case_id.encode("utf-8")).hexdigest()
    value = int(digest[:8], 16) / 0xFFFFFFFF
    return "holdout" if value < holdout_ratio else "train"


def to_pair_row(row: dict) -> dict:
    return {
        "case_id": row["case_id"],
        "user_message": row.get("user_message", ""),
        "candidate_a": row.get("draft_reply", ""),
        "candidate_b": row.get("preferred_reply", ""),
        "preferred": "b",
        "signals": row.get("signals", []),
        "buckets": row.get("buckets", []),
        "send_ok": row.get("send_ok", ""),
        "preferred_source": row.get("preferred_source", ""),
        "draft_source_name": row.get("draft_source_name", ""),
        "draft_source_role": row.get("draft_source_role", ""),
    }


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def build_summary(started_at: datetime, train_rows: list[dict], holdout_rows: list[dict]) -> str:
    bucket_counts_train = Counter()
    bucket_counts_holdout = Counter()
    signal_counts = Counter()

    for row in train_rows:
        for bucket in row.get("buckets", []):
            bucket_counts_train[bucket] += 1
        for signal in row.get("signals", []):
            signal_counts[f"train:{signal}"] += 1

    for row in holdout_rows:
        for bucket in row.get("buckets", []):
            bucket_counts_holdout[bucket] += 1
        for signal in row.get("signals", []):
            signal_counts[f"holdout:{signal}"] += 1

    lines = [
        f"generated_at: {started_at.strftime('%Y-%m-%d %H:%M:%S %Z')}",
        f"train_pairs: {len(train_rows)}",
        f"holdout_pairs: {len(holdout_rows)}",
        "",
        "[bucket_counts.train]",
    ]
    for bucket, count in sorted(bucket_counts_train.items()):
        lines.append(f"{bucket}: {count}")
    lines.extend(["", "[bucket_counts.holdout]"])
    for bucket, count in sorted(bucket_counts_holdout.items()):
        lines.append(f"{bucket}: {count}")
    lines.extend(["", "[signal_counts]"])
    for key, count in sorted(signal_counts.items()):
        lines.append(f"{key}: {count}")
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
    parser = argparse.ArgumentParser(description="Export complete temperature pairs to reranker-ready train/holdout jsonl.")
    parser.add_argument("--pairs", default=str(PAIRS_COMPLETE_PATH))
    parser.add_argument("--holdout-ratio", type=float, default=0.2)
    parser.add_argument("--save-report", action="store_true")
    args = parser.parse_args()

    complete_rows = load_jsonl(Path(args.pairs))
    pair_rows = [to_pair_row(row) for row in complete_rows if row.get("draft_reply") and row.get("preferred_reply")]
    train_rows: list[dict] = []
    holdout_rows: list[dict] = []

    for row in pair_rows:
        target = stable_bucket(row["case_id"], args.holdout_ratio)
        if target == "holdout":
            holdout_rows.append(row)
        else:
            train_rows.append(row)

    write_jsonl(EXPORT_DIR / "train.jsonl", train_rows)
    write_jsonl(EXPORT_DIR / "holdout.jsonl", holdout_rows)

    started_at = datetime.now(JST)
    summary = build_summary(started_at, train_rows, holdout_rows)
    if args.save_report:
        latest_path, history_path = save_report(summary, started_at)
        print(f"report_latest: {latest_path}")
        print(f"report_history: {history_path}")
    print(summary.rstrip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
