#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT_DIR = Path(__file__).resolve().parents[1]
SHADOW_DIR = ROOT_DIR / "runtime/rehearsal/coconala-reply-shadow"
RUNS_JSONL = SHADOW_DIR / "runs.jsonl"
REVIEWS_JSONL = SHADOW_DIR / "reviews.jsonl"
EXPORTED_JSONL = SHADOW_DIR / "exported-reviews.jsonl"
STATUS_LATEST_TXT = SHADOW_DIR / "status-latest.txt"
STATUS_LATEST_JSON = SHADOW_DIR / "status-latest.json"
JST = ZoneInfo("Asia/Tokyo")

EXPORT_OUTCOMES = {"one_word_fix", "rewrite_sentence", "discard"}
OUTCOME_LABELS = {
    "paste_as_is": "無修正で貼れた",
    "one_word_fix": "1語修正",
    "rewrite_sentence": "文組み替え",
    "discard": "不採用",
}


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


def build_run_key(generated_at: str, case_id: str) -> str:
    return f"{generated_at}|{case_id}"


def collect_run_rows() -> list[dict]:
    rows: dict[str, dict] = {}

    for row in load_jsonl(RUNS_JSONL):
        run_key = row.get("run_key") or build_run_key(row.get("generated_at", ""), (row.get("source") or {}).get("case_id", ""))
        if run_key.strip("|"):
            enriched = dict(row)
            enriched["run_key"] = run_key
            rows[run_key] = enriched

    for path in sorted(SHADOW_DIR.glob("20*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        source = payload.get("source") or {}
        generated_at = payload.get("generated_at", "")
        case_id = source.get("case_id", "")
        run_key = payload.get("run_key") or build_run_key(generated_at, case_id)
        if not run_key.strip("|"):
            continue
        payload["run_key"] = run_key
        rows.setdefault(run_key, payload)

    return sorted(rows.values(), key=lambda row: row.get("generated_at", ""))


def load_reviews() -> list[dict]:
    rows = load_jsonl(REVIEWS_JSONL)
    for row in rows:
        if not row.get("run_key"):
            row["run_key"] = build_run_key(row.get("shadow_generated_at", ""), row.get("case_id", ""))
    return rows


def latest_reviews_by_run(reviews: list[dict]) -> list[dict]:
    latest_by_run: dict[str, dict] = {}
    for row in reviews:
        run_key = row.get("run_key", "")
        if run_key:
            latest_by_run[run_key] = row
    return sorted(
        latest_by_run.values(),
        key=lambda row: (
            row.get("shadow_generated_at", ""),
            row.get("case_id", ""),
            row.get("reviewed_at", ""),
        ),
    )


def load_exported_review_keys() -> set[str]:
    keys: set[str] = set()
    for row in load_jsonl(EXPORTED_JSONL):
        key = row.get("review_key")
        if key:
            keys.add(key)
    return keys


def build_review_key(review: dict) -> str:
    return "|".join(
        [
            review.get("shadow_generated_at", ""),
            review.get("reviewed_at", ""),
            review.get("case_id", ""),
            review.get("outcome", ""),
        ]
    )


def compute_paste_streak(reviews: list[dict]) -> int:
    streak = 0
    for row in reversed(reviews):
        if row.get("outcome") != "paste_as_is":
            break
        streak += 1
    return streak


def summarize(runs: list[dict], reviews: list[dict], exported_review_keys: set[str]) -> dict:
    effective_reviews = latest_reviews_by_run(reviews)
    reviewed_run_keys = {row.get("run_key", "") for row in effective_reviews if row.get("run_key")}
    pending_reviews = [row for row in runs if row.get("run_key") not in reviewed_run_keys]

    pending_exports: list[dict] = []
    for review in effective_reviews:
        outcome = review.get("outcome")
        if outcome not in EXPORT_OUTCOMES:
            continue
        review_key = build_review_key(review)
        if review_key in exported_review_keys:
            continue
        pending_exports.append(review)

    outcome_counts = Counter(row.get("outcome", "unknown") for row in effective_reviews)
    paste_streak = compute_paste_streak(effective_reviews)
    latest_run = runs[-1] if runs else {}
    latest_review = effective_reviews[-1] if effective_reviews else {}

    return {
        "generated_at": datetime.now(JST).strftime("%Y-%m-%d %H:%M:%S %Z"),
        "total_runs": len(runs),
        "total_reviews": len(reviews),
        "reviewed_runs": len(reviewed_run_keys),
        "pending_review_count": len(pending_reviews),
        "pending_export_count": len(pending_exports),
        "current_paste_as_is_streak": paste_streak,
        "remaining_to_shadow_graduation": max(0, 5 - paste_streak),
        "shadow_graduation_ready": paste_streak >= 5,
        "outcome_counts": {
            "paste_as_is": outcome_counts["paste_as_is"],
            "one_word_fix": outcome_counts["one_word_fix"],
            "rewrite_sentence": outcome_counts["rewrite_sentence"],
            "discard": outcome_counts["discard"],
        },
        "latest_run": {
            "generated_at": latest_run.get("generated_at", ""),
            "case_id": ((latest_run.get("source") or {}).get("case_id", "")),
            "state": ((latest_run.get("source") or {}).get("state", "")),
            "lane": latest_run.get("lane", ""),
            "scenario": latest_run.get("scenario", ""),
        },
        "latest_review": {
            "reviewed_at": latest_review.get("reviewed_at", ""),
            "case_id": latest_review.get("case_id", ""),
            "state": latest_review.get("state", ""),
            "outcome": latest_review.get("outcome", ""),
            "outcome_label": latest_review.get("outcome_label", ""),
        },
        "pending_reviews": [
            {
                "generated_at": row.get("generated_at", ""),
                "case_id": ((row.get("source") or {}).get("case_id", "")),
                "state": ((row.get("source") or {}).get("state", "")),
                "lane": row.get("lane", ""),
                "scenario": row.get("scenario", ""),
            }
            for row in pending_reviews[-5:]
        ],
        "pending_exports": [
            {
                "reviewed_at": row.get("reviewed_at", ""),
                "case_id": row.get("case_id", ""),
                "state": row.get("state", ""),
                "outcome": row.get("outcome", ""),
                "outcome_label": row.get("outcome_label", ""),
            }
            for row in pending_exports[-5:]
        ],
    }


def build_text(summary: dict) -> str:
    counts = summary["outcome_counts"]
    lines = [
        f"generated_at: {summary['generated_at']}",
        f"total_runs: {summary['total_runs']}",
        f"reviewed_runs: {summary['reviewed_runs']}",
        f"total_reviews: {summary['total_reviews']}",
        f"pending_review_count: {summary['pending_review_count']}",
        f"pending_export_count: {summary['pending_export_count']}",
        f"paste_as_is: {counts['paste_as_is']}",
        f"one_word_fix: {counts['one_word_fix']}",
        f"rewrite_sentence: {counts['rewrite_sentence']}",
        f"discard: {counts['discard']}",
        f"current_paste_as_is_streak: {summary['current_paste_as_is_streak']}",
        f"remaining_to_shadow_graduation: {summary['remaining_to_shadow_graduation']}",
        f"shadow_graduation_ready: {'yes' if summary['shadow_graduation_ready'] else 'no'}",
        "",
        "[latest_run]",
    ]
    latest_run = summary["latest_run"]
    if latest_run.get("case_id"):
        lines.append(
            f"{latest_run.get('generated_at', '')} {latest_run.get('case_id', '')} "
            f"{latest_run.get('state', '')} lane={latest_run.get('lane', '')} scenario={latest_run.get('scenario', '')}"
        )
    else:
        lines.append("(none)")

    lines.extend(["", "[latest_review]"])
    latest_review = summary["latest_review"]
    if latest_review.get("case_id"):
        lines.append(
            f"{latest_review.get('reviewed_at', '')} {latest_review.get('case_id', '')} "
            f"{latest_review.get('state', '')} {latest_review.get('outcome_label', '')}"
        )
    else:
        lines.append("(none)")

    lines.extend(["", "[pending_reviews]"])
    if summary["pending_reviews"]:
        for row in summary["pending_reviews"]:
            lines.append(
                f"- {row.get('generated_at', '')} {row.get('case_id', '')} {row.get('state', '')} "
                f"lane={row.get('lane', '')} scenario={row.get('scenario', '')}"
            )
    else:
        lines.append("(none)")

    lines.extend(["", "[pending_exports]"])
    if summary["pending_exports"]:
        for row in summary["pending_exports"]:
            lines.append(
                f"- {row.get('reviewed_at', '')} {row.get('case_id', '')} {row.get('state', '')} {row.get('outcome_label', '')}"
            )
    else:
        lines.append("(none)")

    return "\n".join(lines).rstrip() + "\n"


def save_latest(text: str, summary: dict) -> tuple[Path, Path]:
    SHADOW_DIR.mkdir(parents=True, exist_ok=True)
    STATUS_LATEST_TXT.write_text(text, encoding="utf-8")
    STATUS_LATEST_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return STATUS_LATEST_TXT, STATUS_LATEST_JSON


def main() -> int:
    parser = argparse.ArgumentParser(description="Show current shadow reply operation status.")
    parser.add_argument("--save", action="store_true")
    args = parser.parse_args()

    runs = collect_run_rows()
    reviews = load_reviews()
    exported = load_exported_review_keys()
    summary = summarize(runs, reviews, exported)
    text = build_text(summary)
    print(text.rstrip())

    if args.save:
        latest_txt, latest_json = save_latest(text, summary)
        print()
        print(f"status_latest_txt: {latest_txt}")
        print(f"status_latest_json: {latest_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
