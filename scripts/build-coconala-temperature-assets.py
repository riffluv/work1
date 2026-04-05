#!/usr/bin/env python3
from __future__ import annotations

import argparse
import glob
import importlib.util
import json
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Iterable
from zoneinfo import ZoneInfo

import yaml


ROOT_DIR = Path(__file__).resolve().parents[1]
EVAL_SOURCES = ROOT_DIR / "ops/tests/eval-sources.yaml"
QUALITY_CASES = ROOT_DIR / "ops/tests/quality-cases/inbox/claude-quality-cases-50-v1.txt"
TEMPERATURE_DIR = ROOT_DIR / "ops/tests/temperature-assets"
PREFERRED_DIR = TEMPERATURE_DIR / "preferred"
PAIRS_DIR = TEMPERATURE_DIR / "pairs"
REPORT_DIR = ROOT_DIR / "runtime/regression/coconala-reply/temperature"
RENDERER_PATH = ROOT_DIR / "scripts/render-prequote-estimate-initial.py"
DEFAULT_REPORTS_GLOB = (
    "/home/hr-hm/.gemini/antigravity/brain/4d5c064a-bb3b-4121-b2be-2b918acc75cb/artifacts/"
    "quality-audit-qlt*.md.resolved"
)
JST = ZoneInfo("Asia/Tokyo")

PRIMARY_BUCKETS = ["stress", "boundary", "negative_feedback"]

STRESS_EMOTIONS = {"anxious", "frustrated", "mixed", "mildly_frustrated", "price_sensitive"}
STRESS_MARKERS = [
    "急ぎ",
    "怖",
    "不安",
    "焦",
    "毎日謝",
    "売上に直結",
    "間に合",
    "社内で聞かれて",
    "大丈夫そう",
    "連絡取れなく",
    "予算",
    "追加費用が怖",
    "止まっている",
]
BOUNDARY_MARKERS = [
    "どっちのサービス",
    "25,000円",
    "修正含まない",
    "対象外",
    "返金",
    "Zoom",
    "通話",
    "直接会",
    "主要1フロー",
    "切り替える",
    "範囲内",
    "また新規",
    "整理のほう",
    "修正じゃなくて整理",
    "何を選んでいいか",
    "どこまで",
]
NEGATIVE_FEEDBACK_MARKERS = [
    "高かった",
    "もう少し途中",
    "安心だったかな",
    "気になった",
    "参考にしていただければ",
    "コメントが英語",
    "率直に",
    "そう感じ",
    "押しつけ",
    "営業感",
    "botっぽ",
    "途中で状況",
]
HESITATION_MARKERS = [
    "すみません",
    "うまく説明でき",
    "相談だけ",
    "気を遣",
    "急かしたいわけではない",
    "比較させて",
    "気のせいかも",
]
CONFUSION_MARKERS = [
    "わから",
    "分から",
    "どっち",
    "何を選",
    "判断つか",
    "全体像",
    "仕様なのか",
    "原因が",
    "どうなってる",
    "怪しく",
]
RELATIONSHIP_MARKERS = [
    "以前お世話",
    "先日は",
    "また何か",
    "お世話にな",
    "昨日お送り",
    "ありがとうございました",
]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to load module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_eval_sources(path: Path) -> list[dict]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return [item for item in data.get("primary_sources", []) if item.get("status") == "active"]


def compact(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def detect_signals(case: dict) -> tuple[list[str], dict[str, list[str]]]:
    raw = compact(case.get("raw_message", ""))
    note = compact(case.get("note", ""))
    combined = f"{raw}\n{note}"
    emotional = (case.get("emotional_tone") or "").strip()
    signals: list[str] = []
    reasons: dict[str, list[str]] = {}

    if emotional in STRESS_EMOTIONS:
        reasons.setdefault("stress", []).append(f"emotional_tone:{emotional}")
    for marker in STRESS_MARKERS:
        if marker in combined:
            reasons.setdefault("stress", []).append(f"marker:{marker}")
    for marker in NEGATIVE_FEEDBACK_MARKERS:
        if marker in combined:
            reasons.setdefault("negative_feedback", []).append(f"marker:{marker}")
    for marker in HESITATION_MARKERS:
        if marker in combined:
            reasons.setdefault("hesitation", []).append(f"marker:{marker}")
    for marker in CONFUSION_MARKERS:
        if marker in combined:
            reasons.setdefault("confusion", []).append(f"marker:{marker}")
    for marker in RELATIONSHIP_MARKERS:
        if marker in combined:
            reasons.setdefault("relationship", []).append(f"marker:{marker}")

    for key in ["stress", "negative_feedback", "hesitation", "confusion", "relationship"]:
        if reasons.get(key):
            signals.append(key)
    if not signals:
        signals.append("neutral")
        reasons["neutral"] = ["fallback:no_specific_signal"]
    return signals, reasons


def detect_buckets(case: dict, signals: list[str]) -> tuple[list[str], dict[str, list[str]]]:
    raw = compact(case.get("raw_message", ""))
    note = compact(case.get("note", ""))
    combined = f"{raw}\n{note}"
    state = (case.get("state") or "").strip()
    service_hint = (case.get("service_hint") or "").strip()

    bucket_reasons: dict[str, list[str]] = defaultdict(list)

    if "stress" in signals:
        bucket_reasons["stress"].append("signal:stress")

    if service_hint == "boundary":
        bucket_reasons["boundary"].append("service_hint:boundary")
    if state in {"closed", "delivered"} and any(marker in combined for marker in ["範囲内", "また新規", "同じような", "整理"]):
        bucket_reasons["boundary"].append(f"state:{state}")
    for marker in BOUNDARY_MARKERS:
        if marker in combined:
            bucket_reasons["boundary"].append(f"marker:{marker}")

    if "negative_feedback" in signals:
        bucket_reasons["negative_feedback"].append("signal:negative_feedback")
    if state == "delivered" and any(marker in combined for marker in ["気になった", "高かった", "安心だったかな"]):
        bucket_reasons["negative_feedback"].append("state:delivered")

    buckets = [bucket for bucket in PRIMARY_BUCKETS if bucket_reasons.get(bucket)]
    return buckets, bucket_reasons


def render_asset_id(source_name: str, case: dict) -> str:
    case_id = case.get("case_id") or case.get("id") or "unknown"
    return f"{Path(source_name).stem}:{case_id}"


def build_inventory_rows(renderer, sources: list[dict], supplemental_sources: list[dict]) -> tuple[list[dict], list[dict]]:
    rows: list[dict] = []
    source_rows: list[dict] = []

    for source in [*sources, *supplemental_sources]:
        path = Path(source["path"])
        role = source.get("role", "supplemental")
        if not path.exists():
            continue
        cases = renderer.load_cases(path)
        source_rows.append(
            {
                "path": str(path),
                "role": role,
                "case_count": len(cases),
                "status": source.get("status", "supplemental"),
            }
        )
        for case in cases:
            signals, signal_reasons = detect_signals(case)
            buckets, bucket_reasons = detect_buckets(case, signals)
            rows.append(
                {
                    "asset_id": render_asset_id(path.name, case),
                    "source_path": str(path),
                    "source_name": path.name,
                    "source_role": role,
                    "case_id": case.get("case_id") or case.get("id"),
                    "state": case.get("state"),
                    "route": case.get("route"),
                    "service_hint": case.get("service_hint"),
                    "user_type": case.get("user_type"),
                    "emotional_tone": case.get("emotional_tone"),
                    "signals": signals,
                    "signal_reasons": signal_reasons,
                    "buckets": buckets,
                    "bucket_reasons": bucket_reasons,
                    "raw_message": case.get("raw_message", ""),
                    "note": case.get("note", ""),
                }
            )
    return rows, source_rows


def parse_preferred_reply(block: str) -> str | None:
    match = re.search(r"\*\*最小修正版:\*\*\s*\n\s*\n((?:>.*\n?)*)", block)
    if match:
        quote_lines = []
        for raw_line in match.group(1).splitlines():
            if not raw_line.strip().startswith(">"):
                continue
            quote_lines.append(raw_line.strip()[1:].lstrip())
        text = "\n".join(quote_lines).strip()
        if text:
            return text

    fenced = re.search(r"####\s*最小修正版\s*\n\s*\n```(?:text)?\n(.*?)\n```", block, re.S)
    if fenced:
        text = fenced.group(1).strip()
        if text:
            return text
    return None


def extract_quality_audit_preferred(report_paths: Iterable[Path]) -> list[dict]:
    rows: list[dict] = []
    for path in sorted(report_paths):
        text = path.read_text(encoding="utf-8")
        for match in re.finditer(r"###\s+([A-Z]+-\d+)\n(.*?)(?=\n---\n|\n###\s+[A-Z]+-\d+|\Z)", text, re.S):
            case_id = match.group(1)
            block = match.group(2)
            user_match = re.search(r"\*\*相手文:\*\*\s*(.+?)(?:\n\n|\n\|)", block, re.S)
            user_message = compact(user_match.group(1)) if user_match else ""
            preferred_reply = parse_preferred_reply(block)
            if not preferred_reply:
                continue
            signals, _signal_reasons = detect_signals({"raw_message": user_message, "note": ""})
            buckets, _bucket_reasons = detect_buckets({"raw_message": user_message, "note": ""}, signals)
            send_ok_match = re.search(r"\*\*このまま送ってよいか:\s*([^*]+)\*\*", block)
            if not send_ok_match:
                send_ok_match = re.search(r"####\s*このまま送ってよいか:\s*\*\*([^*]+)\*\*", block)
            rows.append(
                {
                    "case_id": case_id,
                    "report_path": str(path),
                    "user_message": user_message,
                    "preferred_reply": preferred_reply,
                    "signals": signals,
                    "buckets": buckets,
                    "send_ok": compact(send_ok_match.group(1)) if send_ok_match else "",
                }
            )
    return rows


def ensure_dirs() -> None:
    TEMPERATURE_DIR.mkdir(parents=True, exist_ok=True)
    PREFERRED_DIR.mkdir(parents=True, exist_ok=True)
    PAIRS_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)


def write_jsonl(path: Path, rows: Iterable[dict]) -> None:
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def build_bucket_yaml(rows: list[dict], bucket: str) -> dict:
    bucket_rows = [row for row in rows if bucket in row.get("buckets", [])]
    role_counts = Counter(row.get("source_role") or "unknown" for row in bucket_rows)
    return {
        "bucket": bucket,
        "case_count": len(bucket_rows),
        "role_counts": dict(sorted(role_counts.items())),
        "cases": [
            {
                "asset_id": row["asset_id"],
                "source_name": row["source_name"],
                "source_role": row["source_role"],
                "case_id": row["case_id"],
                "state": row["state"],
                "service_hint": row["service_hint"],
                "emotional_tone": row["emotional_tone"],
                "signals": row["signals"],
                "bucket_reasons": row["bucket_reasons"].get(bucket, []),
                "raw_message": row["raw_message"],
                "note": row["note"],
            }
            for row in bucket_rows
        ],
    }


def build_summary(started_at: datetime, source_rows: list[dict], inventory_rows: list[dict], preferred_rows: list[dict]) -> str:
    bucket_counts = Counter()
    signal_counts = Counter()
    role_counts = Counter()
    for row in inventory_rows:
        role_counts[row["source_role"]] += 1
        for bucket in row["buckets"]:
            bucket_counts[bucket] += 1
        for signal in row["signals"]:
            signal_counts[signal] += 1

    lines = [
        f"generated_at: {started_at.strftime('%Y-%m-%d %H:%M:%S %Z')}",
        f"total_sources: {len(source_rows)}",
        f"total_cases: {len(inventory_rows)}",
        f"preferred_rewrites: {len(preferred_rows)}",
        "",
        "[source_roles]",
    ]
    for role, count in sorted(role_counts.items()):
        lines.append(f"{role}: {count}")
    lines.extend(["", "[bucket_counts]"])
    for bucket in PRIMARY_BUCKETS:
        lines.append(f"{bucket}: {bucket_counts[bucket]}")
    lines.extend(["", "[signal_counts]"])
    for signal, count in sorted(signal_counts.items()):
        lines.append(f"{signal}: {count}")
    lines.extend(["", "[sources]"])
    for row in source_rows:
        lines.append(f"{Path(row['path']).name}: role={row['role']} cases={row['case_count']}")
    return "\n".join(lines) + "\n"


def save_report(text: str, started_at: datetime) -> tuple[Path, Path]:
    stamp = started_at.strftime("%Y%m%d-%H%M%S")
    latest_path = REPORT_DIR / "latest.txt"
    history_path = REPORT_DIR / f"{stamp}.txt"
    latest_path.write_text(text, encoding="utf-8")
    history_path.write_text(text, encoding="utf-8")
    return latest_path, history_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Build temperature asset inventory and preferred rewrite assets.")
    parser.add_argument("--config", default=str(EVAL_SOURCES))
    parser.add_argument("--quality-cases", default=str(QUALITY_CASES))
    parser.add_argument("--reports-glob", default=DEFAULT_REPORTS_GLOB)
    parser.add_argument("--save-report", action="store_true")
    args = parser.parse_args()

    ensure_dirs()
    renderer = load_module("render_prequote_estimate_initial", RENDERER_PATH)
    started_at = datetime.now(JST)

    sources = load_eval_sources(Path(args.config))
    supplemental_sources: list[dict] = []
    quality_cases_path = Path(args.quality_cases)
    if quality_cases_path.exists():
        supplemental_sources.append(
            {
                "path": str(quality_cases_path),
                "role": "quality_cases",
                "status": "active",
            }
        )

    inventory_rows, source_rows = build_inventory_rows(renderer, sources, supplemental_sources)
    preferred_rows = extract_quality_audit_preferred(Path(path) for path in glob.glob(args.reports_glob))

    inventory_path = TEMPERATURE_DIR / "inventory.jsonl"
    write_jsonl(inventory_path, inventory_rows)

    preferred_path = PREFERRED_DIR / "quality-audit-preferred.jsonl"
    write_jsonl(preferred_path, preferred_rows)

    sources_yaml = {
        "version": 1,
        "generated_at": started_at.strftime("%Y-%m-%d %H:%M:%S %Z"),
        "sources": source_rows,
        "artifacts": {
            "inventory": str(inventory_path),
            "preferred_rewrites": str(preferred_path),
            "pairs_status": "pending_initial_drafts",
        },
    }
    (TEMPERATURE_DIR / "sources.yaml").write_text(
        yaml.safe_dump(sources_yaml, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )

    for bucket in PRIMARY_BUCKETS:
        path = TEMPERATURE_DIR / f"{bucket}-candidates.yaml"
        path.write_text(
            yaml.safe_dump(build_bucket_yaml(inventory_rows, bucket), allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )

    pair_readme = PAIRS_DIR / "README.ja.md"
    pair_readme.write_text(
        "\n".join(
            [
                "# temperature pairs",
                "",
                "- 現時点では quality-audit の最小修正版は抽出済みだが、初稿返信が workspace に残っていないため full pair は未生成。",
                "- 次回以降は batch 初稿も保存し、`draft_reply` と `preferred_reply` の比較ペアをここに置く。",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    summary = build_summary(started_at, source_rows, inventory_rows, preferred_rows)
    if args.save_report:
        latest_path, history_path = save_report(summary, started_at)
        print(f"report_latest: {latest_path}")
        print(f"report_history: {history_path}")
    print(summary.rstrip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
