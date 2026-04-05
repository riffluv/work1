#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT_DIR = Path(__file__).resolve().parents[1]
INVENTORY_PATH = ROOT_DIR / "ops/tests/temperature-assets/inventory.jsonl"
UNIFIED_RENDERER = ROOT_DIR / "scripts/render-coconala-reply.py"
PREQUOTE_RENDERER = ROOT_DIR / "scripts/render-prequote-estimate-initial.py"
REPORT_DIR = ROOT_DIR / "runtime/regression/coconala-reply/routing"
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


def build_case_index(parser_module, source_paths: list[str]) -> dict[tuple[str, str], dict]:
    index: dict[tuple[str, str], dict] = {}
    for raw_path in sorted(set(source_paths)):
        path = Path(raw_path)
        if not path.exists():
            continue
        for case in parser_module.load_cases(path):
            case_id = case.get("case_id") or case.get("id")
            if not case_id:
                continue
            index[(str(path), case_id)] = case
    return index


def build_report_text(
    started_at: datetime,
    total_rows: int,
    lane_counts: dict[str, Counter],
    scenario_counts: dict[str, Counter],
    failures: list[str],
) -> str:
    lines = [
        f"generated_at: {started_at.strftime('%Y-%m-%d %H:%M:%S %Z')}",
        f"total_cases: {total_rows}",
        "",
        "[lanes]",
    ]
    for lane in sorted(lane_counts):
        counter = lane_counts[lane]
        total = max(counter["total"], 1)
        lines.append(
            f"{lane}: total={counter['total']} generic={counter['generic']} "
            f"generic_rate={counter['generic']}/{total} low_confidence={counter['low_confidence']}/{total}"
        )
    lines.extend(["", "[scenarios]"])
    for lane in sorted(scenario_counts):
        counts = " ".join(f"{name}={count}" for name, count in sorted(scenario_counts[lane].items()))
        lines.append(f"{lane}: {counts}")
    if failures:
        lines.extend(["", "[failures]"])
        lines.extend(failures[:160])
    else:
        lines.extend(["", "[status]", "[OK] no routing failures recorded"])
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
    parser = argparse.ArgumentParser(description="Scenario-selection visibility report for coconala reply system.")
    parser.add_argument("--inventory", default=str(INVENTORY_PATH))
    parser.add_argument("--save-report", action="store_true")
    args = parser.parse_args()

    inventory_rows = load_inventory(Path(args.inventory))
    unified = load_module("render_coconala_reply", UNIFIED_RENDERER)
    parser_module = load_module("render_prequote_estimate_initial", PREQUOTE_RENDERER)
    tools = unified.load_tools()
    case_index = build_case_index(parser_module, [row["source_path"] for row in inventory_rows])

    lane_counts: dict[str, Counter] = defaultdict(Counter)
    scenario_counts: dict[str, Counter] = defaultdict(Counter)
    failures: list[str] = []

    for row in inventory_rows:
        key = (row["source_path"], row["case_id"])
        source_case = case_index.get(key)
        if not source_case:
            failures.append(f"{row['asset_id']}: source case not found")
            continue

        lane = unified.choose_lane(source_case)
        if lane is None:
            continue

        renderer = tools[lane]["renderer"]
        normalized = source_case if lane == "prequote" and source_case.get("reply_contract") else renderer.build_case_from_source(source_case)
        routing_meta = normalized.get("routing_meta") or {}
        scenario = normalized.get("scenario") or routing_meta.get("scenario") or "missing"
        provided_context = routing_meta.get("provided_context") or []
        is_generic = bool(routing_meta.get("is_generic_fallback"))
        confidence = routing_meta.get("scenario_confidence") or "missing"

        lane_counts[lane]["total"] += 1
        scenario_counts[lane][scenario] += 1
        if is_generic:
            lane_counts[lane]["generic"] += 1
        if confidence == "low":
            lane_counts[lane]["low_confidence"] += 1

        if is_generic and provided_context:
            failures.append(
                f"{row['asset_id']}: generic fallback with provided_context={','.join(provided_context)}"
            )
    started_at = datetime.now(JST)
    report_text = build_report_text(started_at, len(inventory_rows), lane_counts, scenario_counts, failures)
    if args.save_report:
        latest_path, history_path = save_report(report_text, started_at)
        print(f"report_latest: {latest_path}")
        print(f"report_history: {history_path}")
    print(report_text.rstrip())
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
