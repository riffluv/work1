#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT_DIR = Path(__file__).resolve().parents[1]
SHADOW_DIR = ROOT_DIR / "runtime/rehearsal/coconala-reply-shadow"
REVIEWS_JSONL = SHADOW_DIR / "reviews.jsonl"
EXPORT_LEDGER_JSONL = SHADOW_DIR / "exported-reviews.jsonl"
DEFAULT_INBOX_DIR = ROOT_DIR / "ops/tests/stock/inbox"
JST = ZoneInfo("Asia/Tokyo")

DEFAULT_EXPORT_OUTCOMES = {"one_word_fix", "rewrite_sentence", "discard"}


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows: list[dict] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def append_jsonl(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def normalize_inline(text: str) -> str:
    compact = re.sub(r"\s+", " ", (text or "").strip())
    return compact.replace(":", "：")


def build_review_key(review: dict) -> str:
    return "|".join(
        [
            review.get("shadow_generated_at", ""),
            review.get("reviewed_at", ""),
            review.get("case_id", ""),
            review.get("outcome", ""),
        ]
    )


def build_run_key(review: dict) -> str:
    run_key = (review.get("run_key") or "").strip()
    if run_key:
        return run_key
    return f"{review.get('shadow_generated_at', '')}|{review.get('case_id', '')}"


def latest_reviews_by_run(reviews: list[dict]) -> list[dict]:
    latest_by_run: dict[str, dict] = {}
    ordered_keys: list[str] = []
    for row in reviews:
        run_key = build_run_key(row)
        if run_key and run_key not in latest_by_run:
            ordered_keys.append(run_key)
        if run_key:
            latest_by_run[run_key] = row
    return [latest_by_run[key] for key in ordered_keys if key in latest_by_run]


def load_exported_keys(path: Path) -> set[str]:
    keys: set[str] = set()
    for row in load_jsonl(path):
        key = row.get("review_key")
        if key:
            keys.add(key)
    return keys


def default_output_path(now: datetime) -> Path:
    return DEFAULT_INBOX_DIR / f"{now.strftime('%Y-%m')}-shadow-review-batch-01.txt"


def build_note(review: dict) -> str:
    parts = [
        f"shadow_review {review.get('outcome_label', '')}",
    ]
    scenario = review.get("scenario")
    if scenario:
        parts.append(f"scenario={scenario}")
    primary_concern = normalize_inline(review.get("primary_concern", ""))
    if primary_concern:
        parts.append(f"concern={primary_concern}")
    source_note = normalize_inline(review.get("source_note", ""))
    if source_note:
        parts.append(f"source_note={source_note}")
    review_note = normalize_inline(review.get("note", ""))
    if review_note:
        parts.append(f"review_note={review_note}")
    return " / ".join(parts)


def build_block(review: dict) -> str:
    lines = [
        "----",
        "",
        f"case_id: {review.get('case_id', '')}",
        f"route: {review.get('route', '')}",
        f"state: {review.get('state', '')}",
        f"user_type: {review.get('user_type', '')}",
        f"emotional_tone: {review.get('emotional_tone', '')}",
        f"service_hint: {review.get('service_hint', '')}",
        f"raw_message: {normalize_inline(review.get('source_text', ''))}",
        f"note: {build_note(review)}",
        "",
    ]
    return "\n".join(lines)


def ensure_header(path: Path, now: datetime, exported_count: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_text(encoding="utf-8").strip():
        return
    header = "\n".join(
        [
            "# shadow review 取り込み batch",
            f"# 作成日: {now.strftime('%Y-%m-%d')}",
            f"# 用途: shadow 運用で手直し・不採用になった実メッセージを stock inbox へ戻す",
            f"# exported_count: {exported_count}",
            "",
        ]
    )
    path.write_text(header, encoding="utf-8")


def append_blocks(path: Path, blocks: list[str]) -> None:
    with path.open("a", encoding="utf-8") as f:
        for block in blocks:
            f.write(block)


def main() -> int:
    parser = argparse.ArgumentParser(description="Export reviewed shadow replies into stock inbox plain-text batches.")
    parser.add_argument("--reviews", default=str(REVIEWS_JSONL))
    parser.add_argument("--output")
    parser.add_argument("--include-outcome", action="append", choices=["paste_as_is", "one_word_fix", "rewrite_sentence", "discard"])
    parser.add_argument("--all", action="store_true", help="Export all matching reviews, including already-exported ones.")
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()

    now = datetime.now(JST)
    reviews = load_jsonl(Path(args.reviews))
    if not reviews:
        print("[NG] no shadow reviews found")
        return 1
    effective_reviews = latest_reviews_by_run(reviews)

    wanted_outcomes = set(args.include_outcome or [])
    if not wanted_outcomes:
        wanted_outcomes = set(DEFAULT_EXPORT_OUTCOMES)

    exported_keys = set() if args.all else load_exported_keys(EXPORT_LEDGER_JSONL)
    selected: list[dict] = []
    for review in effective_reviews:
        if review.get("outcome") not in wanted_outcomes:
            continue
        review_key = build_review_key(review)
        if review_key in exported_keys:
            continue
        enriched = dict(review)
        enriched["review_key"] = review_key
        selected.append(enriched)

    if args.limit is not None:
        selected = selected[: args.limit]

    if not selected:
        print("[OK] no shadow reviews to export")
        return 0

    output_path = Path(args.output) if args.output else default_output_path(now)
    ensure_header(output_path, now, len(selected))
    append_blocks(output_path, [build_block(review) for review in selected])

    for review in selected:
        append_jsonl(
            EXPORT_LEDGER_JSONL,
            {
                "exported_at": now.strftime("%Y-%m-%d %H:%M:%S %Z"),
                "review_key": review["review_key"],
                "case_id": review.get("case_id", ""),
                "outcome": review.get("outcome", ""),
                "output_path": str(output_path),
            },
        )

    print(f"output: {output_path}")
    print(f"exported: {len(selected)}")
    for review in selected:
        print(f"- {review.get('case_id', '')}: {review.get('outcome_label', '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
