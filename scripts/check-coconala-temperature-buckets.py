#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from reply_quality_lint_common import collect_answer_coverage_errors, collect_temperature_constraint_errors


ROOT_DIR = Path(__file__).resolve().parents[1]
INVENTORY_PATH = ROOT_DIR / "ops/tests/temperature-assets/inventory.jsonl"
UNIFIED_RENDERER = ROOT_DIR / "scripts/render-coconala-reply.py"
PREQUOTE_RENDERER = ROOT_DIR / "scripts/render-prequote-estimate-initial.py"
REPORT_DIR = ROOT_DIR / "runtime/regression/coconala-reply/temperature/buckets"
JST = ZoneInfo("Asia/Tokyo")


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to load module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_inventory(path: Path) -> list[dict]:
    rows: list[dict] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def first_nonempty_line(text: str) -> str:
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line:
            return line
    return ""


def opening_block(text: str) -> str:
    lines: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            if lines:
                break
            continue
        lines.append(line)
    return "\n".join(lines)


def split_sections(text: str) -> list[str]:
    sections: list[str] = []
    current: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            if current:
                sections.append("\n".join(current))
                current = []
            continue
        current.append(line)
    if current:
        sections.append("\n".join(current))
    return sections


def looks_like_direct_answer(text: str) -> bool:
    markers = [
        "はい、",
        "いいえ、",
        "この時点では、",
        "今の内容なら、",
        "今の段階では、",
        "大丈夫です",
        "可能です",
        "できます",
        "進められます",
        "対象外になります",
        "範囲内です",
    ]
    return any(marker in text for marker in markers)


def looks_like_action_or_reassurance(text: str) -> bool:
    return any(marker in text for marker in ["すぐ", "まず", "先に", "大丈夫です", "気にしなくて", "気を遣っていただかなくて"])


def looks_like_feedback_receipt(text: str) -> bool:
    return any(marker in text for marker in ["率直に", "伝えていただいて", "ありがとうございます", "受け止めます"])


def build_case_index(parser_module, source_paths: list[str]) -> dict[tuple[str, str], dict]:
    index: dict[tuple[str, str], dict] = {}
    for raw_path in sorted(set(source_paths)):
        path = Path(raw_path)
        if not path.exists():
            continue
        for case in parser_module.load_cases(path):
            case_id = case.get("case_id") or case.get("id")
            if case_id:
                key = (str(path), case_id)
                current = index.get(key)
                current_score = 0
                new_score = 0
                if current:
                    current_score += 2 if current.get("raw_message") else 0
                    current_score += 1 if current.get("state") else 0
                new_score += 2 if case.get("raw_message") else 0
                new_score += 1 if case.get("state") else 0
                if current is None or new_score >= current_score:
                    index[key] = case
    return index


def summarize_bucket(bucket: str, counter: Counter) -> list[str]:
    total = max(counter["total"], 1)
    lines = [f"{bucket}: total={counter['total']}"]
    if bucket == "stress":
        lines.append(f"  action_or_reassurance_pass={counter['action_or_reassurance_pass']}/{counter['total']}")
        lines.append(f"  burden_leak_rate={counter['burden_shift_fail']}/{total}")
        lines.append(f"  opening_overlength_rate={counter['opening_overlength_fail']}/{total}")
    elif bucket == "boundary":
        lines.append(f"  direct_answer_pass={counter['direct_answer_pass']}/{counter['total']}")
        lines.append(f"  answer_coverage_fail_rate={counter['answer_coverage_fail']}/{total}")
        lines.append(f"  internal_term_leak_rate={counter['internal_term_fail']}/{total}")
        lines.append(f"  negative_lead_rate={counter['negative_lead_fail']}/{total}")
    elif bucket == "negative_feedback":
        lines.append(f"  receive_feedback_pass={counter['receive_feedback_pass']}/{counter['total']}")
        lines.append(f"  defense_rate={counter['defense_fail']}/{total}")
        lines.append(f"  burden_leak_rate={counter['burden_shift_fail']}/{total}")
    lines.append(f"  reasks_known_info_rate={counter['reasks_known_info_fail']}/{total}")
    lines.append(f"  validator_fail={counter['validator_fail']}/{total}")
    lines.append(f"  missing_temperature_plan={counter['missing_temperature_plan']}/{total}")
    return lines


def build_report_text(
    started_at: datetime,
    rows: list[dict],
    bucket_counters: dict[str, Counter],
    failures: list[str],
    opening_moves: dict[str, Counter],
) -> str:
    lines = [
        f"generated_at: {started_at.strftime('%Y-%m-%d %H:%M:%S %Z')}",
        f"total_cases: {len(rows)}",
        "",
        "[buckets]",
    ]
    for bucket in sorted(bucket_counters):
        lines.extend(summarize_bucket(bucket, bucket_counters[bucket]))
    lines.extend(["", "[opening_moves]"])
    for bucket in sorted(opening_moves):
        counts = " ".join(f"{name}={count}" for name, count in sorted(opening_moves[bucket].items()))
        lines.append(f"{bucket}: {counts}")
    if failures:
        lines.extend(["", "[failures]"])
        lines.extend(failures[:120])
    else:
        lines.extend(["", "[status]", "[OK] no bucket failures recorded"])
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
    parser = argparse.ArgumentParser(description="Deterministic temperature bucket checks for coconala reply cases.")
    parser.add_argument("--inventory", default=str(INVENTORY_PATH))
    parser.add_argument("--bucket", action="append", help="Only include these buckets")
    parser.add_argument("--role", action="append", help="Only include these source roles")
    parser.add_argument("--save-report", action="store_true")
    args = parser.parse_args()

    inventory_rows = load_inventory(Path(args.inventory))
    wanted_buckets = set(args.bucket or [])
    wanted_roles = set(args.role or [])
    filtered_rows = [
        row
        for row in inventory_rows
        if row.get("buckets")
        and (not wanted_buckets or wanted_buckets.intersection(row.get("buckets", [])))
        and (not wanted_roles or row.get("source_role") in wanted_roles)
    ]

    unified = load_module("render_coconala_reply", UNIFIED_RENDERER)
    parser_module = load_module("render_prequote_estimate_initial", PREQUOTE_RENDERER)
    tools = unified.load_tools()
    case_index = build_case_index(parser_module, [row["source_path"] for row in filtered_rows])

    bucket_counters: dict[str, Counter] = defaultdict(Counter)
    opening_moves: dict[str, Counter] = defaultdict(Counter)
    failures: list[str] = []

    for row in filtered_rows:
        key = (row["source_path"], row["case_id"])
        source_case = case_index.get(key)
        if not source_case:
            failures.append(f"{row['asset_id']}: source case not found")
            continue

        lane = unified.choose_lane(source_case)
        if lane is None:
            failures.append(f"{row['asset_id']}: unsupported lane")
            continue

        tool = tools[lane]
        renderer = tool["renderer"]
        normalized = source_case if lane == "prequote" and source_case.get("reply_contract") else renderer.build_case_from_source(source_case)
        rendered = renderer.render_case(normalized)
        plan = normalized.get("temperature_plan") or {}
        editable_slots = ((normalized.get("render_payload") or {}).get("editable_slots")) or {}
        errors = collect_temperature_constraint_errors(rendered, plan, editable_slots)
        errors.extend(
            collect_answer_coverage_errors(
                rendered,
                source_case.get("raw_message", ""),
                normalized.get("reply_contract"),
                normalized.get("routing_meta"),
                normalized.get("state"),
            )
        )
        first_line = first_nonempty_line(rendered)
        opening = opening_block(rendered)
        opening_move = plan.get("opening_move") or "missing"
        answer_core = (((normalized.get("render_payload") or {}).get("fixed_slots")) or {}).get("answer_core", "")
        sections = split_sections(rendered)
        fallback_second_section = sections[1] if len(sections) > 1 else ""
        answer_window = "\n".join(part for part in [opening, answer_core or fallback_second_section] if part)

        flags = {
            "internal_term_fail": any("internal" in err for err in errors),
            "defense_fail": any("defensive" in err or "explains the user's negative feeling" in err for err in errors),
            "burden_shift_fail": any("burden" in err or "pushes" in err or "choice back" in err for err in errors),
            "negative_lead_fail": any("negative lead" in err for err in errors),
            "validator_fail": bool(normalized.get("render_payload_violations")),
            "missing_temperature_plan": not bool(plan),
            "answer_coverage_fail": any("answer the main question early" in err for err in errors),
            "reasks_known_info_fail": any("already provided by the user" in err for err in errors),
            "action_or_reassurance_pass": looks_like_action_or_reassurance(opening),
            "direct_answer_pass": opening_move == "yes_no_first" or looks_like_direct_answer(answer_window),
            "receive_feedback_pass": looks_like_feedback_receipt(opening),
            "opening_overlength_fail": opening.count("\n") >= 2 or len(opening) > 85,
        }

        for bucket in row["buckets"]:
            counter = bucket_counters[bucket]
            counter["total"] += 1
            opening_moves[bucket][opening_move] += 1
            for name, value in flags.items():
                if value:
                    counter[name] += 1

            if bucket == "stress" and not flags["action_or_reassurance_pass"]:
                failures.append(f"{row['asset_id']}: stress opening lacks action/reassurance")
            if bucket == "boundary" and not flags["direct_answer_pass"]:
                failures.append(f"{row['asset_id']}: boundary reply lacks early direct answer")
            if bucket == "negative_feedback" and not flags["receive_feedback_pass"]:
                failures.append(f"{row['asset_id']}: negative_feedback reply does not receive feedback early")
            if flags["internal_term_fail"]:
                failures.append(f"{row['asset_id']}: internal term leak")
            if flags["defense_fail"]:
                failures.append(f"{row['asset_id']}: defensive explanation leak")
            if flags["negative_lead_fail"]:
                failures.append(f"{row['asset_id']}: negative lead opening")

    started_at = datetime.now(JST)
    report_text = build_report_text(started_at, filtered_rows, bucket_counters, failures, opening_moves)

    if args.save_report:
        latest_path, history_path = save_report(report_text, started_at)
        print(f"report_latest: {latest_path}")
        print(f"report_history: {history_path}")

    print(report_text.rstrip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
