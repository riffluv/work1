#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT_DIR = Path(__file__).resolve().parents[1]
SHADOW_DIR = ROOT_DIR / "runtime/rehearsal/coconala-reply-shadow"
LATEST_SHADOW_JSON = SHADOW_DIR / "latest.json"
REPLY_SAVE = ROOT_DIR / "scripts/reply-save.sh"
REVIEWS_JSONL = SHADOW_DIR / "reviews.jsonl"
LATEST_REVIEW_TXT = SHADOW_DIR / "latest-review.txt"
LATEST_REVIEW_JSON = SHADOW_DIR / "latest-review.json"
LATEST_SUMMARY_TXT = SHADOW_DIR / "summary-latest.txt"
LATEST_SUMMARY_JSON = SHADOW_DIR / "summary-latest.json"
JST = ZoneInfo("Asia/Tokyo")

OUTCOME_LABELS = {
    "paste_as_is": "無修正で貼れた",
    "one_word_fix": "1語修正",
    "rewrite_sentence": "文組み替え",
    "discard": "不採用",
}


def load_shadow_payload(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))


def read_text_arg(*, file_path: str | None, text_value: str | None) -> str:
    if file_path:
        return Path(file_path).read_text(encoding="utf-8").strip()
    if text_value:
        return text_value.strip()
    return ""


def append_jsonl(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def load_reviews(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows: list[dict] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


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


def compute_current_streak(reviews: list[dict], target: str) -> int:
    streak = 0
    for row in reversed(reviews):
        if row.get("outcome") != target:
            break
        streak += 1
    return streak


def build_summary(reviews: list[dict]) -> dict:
    effective_reviews = latest_reviews_by_run(reviews)
    counts = {name: 0 for name in OUTCOME_LABELS}
    for row in effective_reviews:
        outcome = row.get("outcome")
        if outcome in counts:
            counts[outcome] += 1

    current_paste_streak = compute_current_streak(effective_reviews, "paste_as_is")
    last_five = [
        {
            "case_id": row.get("case_id"),
            "state": row.get("state"),
            "outcome": row.get("outcome"),
            "outcome_label": row.get("outcome_label"),
            "reviewed_at": row.get("reviewed_at"),
        }
        for row in effective_reviews[-5:]
    ]
    return {
        "total_reviews": len(reviews),
        "effective_reviewed_runs": len(effective_reviews),
        "counts": counts,
        "current_paste_as_is_streak": current_paste_streak,
        "shadow_graduation_ready": current_paste_streak >= 5,
        "last_five": last_five,
    }


def build_review_text(review: dict, summary: dict) -> str:
    lines = [
        f"reviewed_at: {review['reviewed_at']}",
        f"case_id: {review.get('case_id', '')}",
        f"state: {review.get('state', '')}",
        f"lane: {review.get('lane', '')}",
        f"scenario: {review.get('scenario', '')}",
        f"outcome: {review.get('outcome_label', '')}",
        f"saved_final_to_runtime: {'yes' if review.get('saved_final_to_runtime') else 'no'}",
        f"current_paste_as_is_streak: {summary['current_paste_as_is_streak']}",
    ]
    note = (review.get("note") or "").strip()
    if note:
        lines.extend(["", "[note]", note])
    lines.extend(
        [
            "",
            "[source]",
            review.get("source_text", ""),
            "",
            "[draft_reply]",
            review.get("draft_reply", ""),
        ]
    )
    final_reply = (review.get("final_reply") or "").strip()
    if final_reply:
        lines.extend(["", "[final_reply]", final_reply])
    return "\n".join(lines).rstrip() + "\n"


def build_summary_text(summary: dict) -> str:
    counts = summary["counts"]
    lines = [
        f"total_reviews: {summary['total_reviews']}",
        f"effective_reviewed_runs: {summary['effective_reviewed_runs']}",
        f"paste_as_is: {counts['paste_as_is']}",
        f"one_word_fix: {counts['one_word_fix']}",
        f"rewrite_sentence: {counts['rewrite_sentence']}",
        f"discard: {counts['discard']}",
        f"current_paste_as_is_streak: {summary['current_paste_as_is_streak']}",
        f"shadow_graduation_ready: {'yes' if summary['shadow_graduation_ready'] else 'no'}",
        "",
        "[last_five]",
    ]
    for row in summary["last_five"]:
        lines.append(
            f"- {row.get('reviewed_at', '')} {row.get('case_id', '')} {row.get('state', '')} {row.get('outcome_label', '')}"
        )
    return "\n".join(lines).rstrip() + "\n"


def save_latest_files(review: dict, review_text: str, summary: dict, summary_text: str) -> tuple[Path, Path, Path, Path]:
    SHADOW_DIR.mkdir(parents=True, exist_ok=True)
    LATEST_REVIEW_TXT.write_text(review_text, encoding="utf-8")
    LATEST_REVIEW_JSON.write_text(json.dumps(review, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    LATEST_SUMMARY_TXT.write_text(summary_text, encoding="utf-8")
    LATEST_SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return LATEST_REVIEW_TXT, LATEST_REVIEW_JSON, LATEST_SUMMARY_TXT, LATEST_SUMMARY_JSON


def save_final_to_runtime(final_reply: str, source_text: str) -> None:
    subprocess.run(
        [
            str(REPLY_SAVE),
            "--text",
            final_reply,
            "--source-text",
            source_text,
        ],
        check=True,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Record a human review outcome for the latest shadow coconala reply.")
    parser.add_argument(
        "--outcome",
        required=True,
        choices=sorted(OUTCOME_LABELS),
        help="paste_as_is / one_word_fix / rewrite_sentence / discard",
    )
    parser.add_argument("--from-file", default=str(LATEST_SHADOW_JSON))
    parser.add_argument("--final-reply-file")
    parser.add_argument("--final-reply-text")
    parser.add_argument("--note")
    parser.add_argument("--save-final", action="store_true", help="Write final reply to runtime/replies/latest*.txt")
    args = parser.parse_args()

    shadow = load_shadow_payload(Path(args.from_file))
    draft_reply = (shadow.get("sendable_reply") or "").strip()
    source = shadow.get("source") or {}
    source_text = (source.get("raw_message") or "").strip()

    final_reply = read_text_arg(file_path=args.final_reply_file, text_value=args.final_reply_text)
    if args.outcome == "paste_as_is" and not final_reply:
        final_reply = draft_reply
    if args.outcome in {"one_word_fix", "rewrite_sentence"} and not final_reply:
        raise SystemExit("final reply is required for one_word_fix / rewrite_sentence")

    reviewed_at = datetime.now(JST).strftime("%Y-%m-%d %H:%M:%S %Z")
    review = {
        "reviewed_at": reviewed_at,
        "shadow_generated_at": shadow.get("generated_at", ""),
        "run_key": shadow.get("run_key", ""),
        "case_id": source.get("case_id", ""),
        "state": source.get("state", ""),
        "route": source.get("route", ""),
        "user_type": source.get("user_type", ""),
        "emotional_tone": source.get("emotional_tone", ""),
        "service_hint": source.get("service_hint", ""),
        "source_note": source.get("note", ""),
        "lane": shadow.get("lane", ""),
        "scenario": shadow.get("scenario", ""),
        "primary_concern": shadow.get("primary_concern", ""),
        "outcome": args.outcome,
        "outcome_label": OUTCOME_LABELS[args.outcome],
        "note": args.note or "",
        "source_text": source_text,
        "draft_reply": draft_reply,
        "final_reply": final_reply,
        "saved_final_to_runtime": False,
    }

    if args.save_final and final_reply:
        save_final_to_runtime(final_reply, source_text)
        review["saved_final_to_runtime"] = True

    append_jsonl(REVIEWS_JSONL, review)
    reviews = load_reviews(REVIEWS_JSONL)
    summary = build_summary(reviews)
    review_text = build_review_text(review, summary)
    summary_text = build_summary_text(summary)
    review_txt, review_json, summary_txt, summary_json = save_latest_files(review, review_text, summary, summary_text)

    print(review_text.rstrip())
    print()
    print(f"review_latest_txt: {review_txt}")
    print(f"review_latest_json: {review_json}")
    print(f"summary_latest_txt: {summary_txt}")
    print(f"summary_latest_json: {summary_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
