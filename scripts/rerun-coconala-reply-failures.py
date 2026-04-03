#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml


ROOT_DIR = Path(__file__).resolve().parents[1]
EVAL_SOURCES = ROOT_DIR / "ops/tests/eval-sources.yaml"
UNIFIED_RENDERER = ROOT_DIR / "scripts/render-coconala-reply.py"
FAILURE_FILE = ROOT_DIR / "runtime/regression/coconala-reply/failures/latest.txt"
RERUN_DIR = ROOT_DIR / "runtime/regression/coconala-reply/failures/reruns"
JST = ZoneInfo("Asia/Tokyo")


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to load module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_source_index(config_path: Path, include_secondary: bool) -> dict[str, Path]:
    data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    entries = [item for item in data.get("primary_sources", []) if item.get("status") == "active"]
    if include_secondary:
        entries.extend(item for item in data.get("secondary_sources", []) if item.get("status") == "active")

    index: dict[str, Path] = {}
    for item in entries:
        path = Path(item["path"])
        index[path.name] = path
    return index


def parse_failure_cases(path: Path) -> list[tuple[str, str]]:
    if not path.exists():
        raise FileNotFoundError(path)

    cases: list[tuple[str, str]] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line.startswith("- case: "):
            continue
        value = line.removeprefix("- case: ").strip()
        if ":" not in value:
            continue
        source_name, case_id = value.split(":", 1)
        cases.append((source_name, case_id))
    return cases


def save_rerun_report(report_text: str, started_at: datetime) -> tuple[Path, Path]:
    RERUN_DIR.mkdir(parents=True, exist_ok=True)
    stamp = started_at.strftime("%Y%m%d-%H%M%S")
    latest_path = RERUN_DIR / "latest.txt"
    history_path = RERUN_DIR / f"{stamp}.txt"
    latest_path.write_text(report_text, encoding="utf-8")
    history_path.write_text(report_text, encoding="utf-8")
    return latest_path, history_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Rerun failed coconala reply cases from the latest failure artifact.")
    parser.add_argument("--from-file", default=str(FAILURE_FILE))
    parser.add_argument("--config", default=str(EVAL_SOURCES))
    parser.add_argument("--include-secondary", action="store_true")
    parser.add_argument("--save-report", action="store_true")
    args = parser.parse_args()

    started_at = datetime.now(JST)
    unified = load_module("render_coconala_reply", UNIFIED_RENDERER)
    tools = unified.load_tools()
    estimate_renderer = tools["prequote"]["renderer"]
    source_index = load_source_index(Path(args.config), args.include_secondary)

    failure_cases = parse_failure_cases(Path(args.from_file))
    if not failure_cases:
        print("[OK] no failed cases to rerun")
        if args.save_report:
            report_text = (
                f"generated_at: {started_at.strftime('%Y-%m-%d %H:%M:%S %Z')}\n\n"
                "[status]\n[OK] no failed cases to rerun\n"
            )
            latest_path, history_path = save_rerun_report(report_text, started_at)
            print(f"rerun_latest: {latest_path}")
            print(f"rerun_history: {history_path}")
        return 0

    blocks: list[str] = []
    had_error = False

    for source_name, case_id in failure_cases:
        source_path = source_index.get(source_name)
        if source_path is None:
            blocks.append(f"[NG] {source_name}:{case_id}: source not found in eval-sources")
            had_error = True
            continue

        cases = estimate_renderer.load_cases(source_path)
        selected = [case for case in cases if case.get("case_id") == case_id or case.get("id") == case_id]
        if not selected:
            blocks.append(f"[NG] {source_name}:{case_id}: case not found in source")
            had_error = True
            continue

        source = selected[0]
        lane = unified.choose_lane(source)
        if lane is None:
            blocks.append(f"[NG] {source_name}:{case_id}: unsupported state / reply_skeleton combination")
            had_error = True
            continue

        tool = tools[lane]
        reply = tool["render_fn"](tool["renderer"], source)
        errors = tool["lint_fn"](source)

        block_lines = [
            f"source: {source_name}",
            f"case_id: {case_id}",
            f"state: {source.get('state', '<unknown>')}",
            f"lane: {lane}",
            "[reply]",
            reply,
        ]

        if errors:
            had_error = True
            block_lines.extend(["", "[lint]", *[f"[NG] {error}" for error in errors]])
        else:
            block_lines.extend(["", "[lint]", "[OK] rerun passed"])

        blocks.append("\n".join(block_lines))

    report_text = (
        f"generated_at: {started_at.strftime('%Y-%m-%d %H:%M:%S %Z')}\n\n" + "\n\n----\n\n".join(blocks) + "\n"
    )
    print(report_text.rstrip())

    if args.save_report:
        latest_path, history_path = save_rerun_report(report_text, started_at)
        print(f"rerun_latest: {latest_path}")
        print(f"rerun_history: {history_path}")

    return 1 if had_error else 0


if __name__ == "__main__":
    raise SystemExit(main())
