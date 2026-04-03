#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml


ROOT_DIR = Path(__file__).resolve().parents[1]
EVAL_SOURCES = ROOT_DIR / "ops/tests/eval-sources.yaml"
PREQUOTE_RENDERER = ROOT_DIR / "scripts/render-prequote-estimate-initial.py"
REPORT_DIR = ROOT_DIR / "runtime/regression/coconala-reply/stock"
JST = ZoneInfo("Asia/Tokyo")


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to load module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_sources(config_path: Path, include_secondary: bool) -> list[dict]:
    data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    sources = [item for item in data.get("primary_sources", []) if item.get("status") == "active"]
    if include_secondary:
        sources.extend(item for item in data.get("secondary_sources", []) if item.get("status") == "active")
    return sources


def build_report_text(started_at: datetime, rows: list[str], role_totals: dict[str, Counter], totals: Counter) -> str:
    lines = [
        f"generated_at: {started_at.strftime('%Y-%m-%d %H:%M:%S %Z')}",
        f"total_sources: {totals['sources']}",
        f"total_cases: {totals['cases']}",
        "",
        "[sources]",
    ]
    lines.extend(rows)
    lines.extend(["", "[role_totals]"])
    for role in sorted(role_totals):
        counter = role_totals[role]
        lines.append(
            f"{role}: sources={counter['sources']} cases={counter['cases']} "
            f"prequote={counter['prequote']} quote_sent={counter['quote_sent']} "
            f"purchased={counter['purchased']} closed={counter['closed']} "
            f"delivered={counter['delivered']} other={counter['other']}"
        )
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
    parser = argparse.ArgumentParser(description="Summarize current coconala reply stock by role and state.")
    parser.add_argument("--config", default=str(EVAL_SOURCES))
    parser.add_argument("--include-secondary", action="store_true")
    parser.add_argument("--save-report", action="store_true")
    args = parser.parse_args()

    renderer = load_module("render_prequote_estimate_initial", PREQUOTE_RENDERER)
    started_at = datetime.now(JST)
    rows: list[str] = []
    role_totals: dict[str, Counter] = defaultdict(Counter)
    totals = Counter()

    for source in load_sources(Path(args.config), args.include_secondary):
        path = Path(source["path"])
        role = source.get("role", "unknown")
        cases = renderer.load_cases(path) if path.suffix in {".txt", ".yaml", ".yml"} else []
        state_counter = Counter()
        for case in cases:
            state = case.get("state") or "other"
            if state not in {"prequote", "quote_sent", "purchased", "closed", "delivered"}:
                state = "other"
            state_counter[state] += 1
        row = (
            f"{path.name}: role={role} cases={len(cases)} "
            f"prequote={state_counter['prequote']} quote_sent={state_counter['quote_sent']} "
            f"purchased={state_counter['purchased']} closed={state_counter['closed']} "
            f"delivered={state_counter['delivered']} other={state_counter['other']}"
        )
        rows.append(row)
        role_totals[role]["sources"] += 1
        role_totals[role]["cases"] += len(cases)
        for key, value in state_counter.items():
            role_totals[role][key] += value
        totals["sources"] += 1
        totals["cases"] += len(cases)

    report_text = build_report_text(started_at, rows, role_totals, totals)
    if args.save_report:
        latest_path, history_path = save_report(report_text, started_at)
        print(f"report_latest: {latest_path}")
        print(f"report_history: {history_path}")
    print(report_text.rstrip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
