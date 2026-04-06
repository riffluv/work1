#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import re
import shutil
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml


ROOT_DIR = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT_DIR / "ops/tests/regression/reply_memory_check/cases.yaml"
RENDERER_PATH = ROOT_DIR / "scripts/render-post-purchase-quick.py"
REPORT_DIR = ROOT_DIR / "runtime/regression/coconala-reply/reply-memory"
JST = ZoneInfo("Asia/Tokyo")


def load_renderer():
    import sys

    sys.path.insert(0, str(ROOT_DIR / "scripts"))
    spec = importlib.util.spec_from_file_location("render_post_purchase_quick", RENDERER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to load renderer: {RENDERER_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_cases(path: Path) -> list[dict]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data.get("cases") or []


def normalize(text: str) -> str:
    return re.sub(r"[\s。、，,.！？?「」『』（）()・:：/／\\-]+", "", text)


def build_source(raw_message: str, reply_memory: dict | None = None) -> dict:
    source = {
        "state": "purchased",
        "route": "talkroom",
        "user_type": "buyer",
        "raw_message": raw_message,
    }
    if reply_memory is not None:
        source["reply_memory"] = reply_memory
    return source


def build_report_text(
    started_at: datetime,
    case_results: list[dict],
    errors: list[str],
) -> str:
    lines = [f"generated_at: {started_at.strftime('%Y-%m-%d %H:%M:%S %Z')}", "", "[cases]"]
    for result in case_results:
        lines.append(
            f"{result['case_id']}: scenario={result['scenario']} changed={result['changed_from_baseline']}"
        )
    if errors:
        lines.extend(["", "[errors]"])
        lines.extend(errors)
        lines.extend(["", "[status]", "[NG] reply memory regression failed"])
    else:
        lines.extend(["", "[status]", "[OK] reply memory regression passed"])
    return "\n".join(lines) + "\n"


def save_report(text: str, started_at: datetime) -> tuple[Path, Path]:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = started_at.strftime("%Y%m%d-%H%M%S")
    latest_path = REPORT_DIR / "latest.txt"
    history_path = REPORT_DIR / f"{stamp}.txt"
    latest_path.write_text(text, encoding="utf-8")
    history_path.write_text(text, encoding="utf-8")
    return latest_path, history_path


def check_thread_scoped_roundtrip(renderer) -> list[str]:
    errors: list[str] = []
    shared = renderer.shared
    test_case_id = "__reply-memory-test__"
    case_dir = ROOT_DIR / "ops/cases/open" / test_case_id
    case_memory_path = case_dir / "reply-memory.json"
    active_case_path = ROOT_DIR / "runtime/active-case.txt"
    latest_memory_path = ROOT_DIR / "runtime/replies/latest-memory.json"

    original_active_case = active_case_path.read_text(encoding="utf-8") if active_case_path.exists() else None
    original_latest_memory = latest_memory_path.read_text(encoding="utf-8") if latest_memory_path.exists() else None

    shutil.rmtree(case_dir, ignore_errors=True)
    case_dir.mkdir(parents=True, exist_ok=True)
    active_case_path.parent.mkdir(parents=True, exist_ok=True)
    active_case_path.write_text(test_case_id + "\n", encoding="utf-8")

    payload = {
        "followup_count": 1,
        "prior_tone": "patient_urgent",
        "previous_assistant_commitment": "share_status",
        "previous_deadline_promised": "本日20:00までに",
        "commitment_fulfilled": False,
    }

    try:
        shared.save_reply_memory(payload)
        loaded = shared.load_reply_memory()
        if loaded != shared.normalize_reply_memory(payload):
            errors.append("thread-scoped load/save roundtrip did not preserve the case-scoped memory")
        if not case_memory_path.exists():
            errors.append("thread-scoped save did not create ops/cases/open/{case_id}/reply-memory.json")
        latest_loaded = shared._read_reply_memory_file(latest_memory_path)
        if latest_loaded != shared.default_reply_memory():
            errors.append("thread-scoped save did not reset runtime/replies/latest-memory.json to default")
    finally:
        if original_active_case is None:
            active_case_path.write_text("", encoding="utf-8")
        else:
            active_case_path.write_text(original_active_case, encoding="utf-8")
        if original_latest_memory is None:
            try:
                latest_memory_path.unlink()
            except FileNotFoundError:
                pass
        else:
            latest_memory_path.write_text(original_latest_memory, encoding="utf-8")
        shutil.rmtree(case_dir, ignore_errors=True)

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Check purchased reply_memory regression fixture.")
    parser.add_argument("--fixture", default=str(FIXTURE_PATH))
    parser.add_argument("--save-report", action="store_true")
    args = parser.parse_args()

    started_at = datetime.now(JST)
    fixture_path = Path(args.fixture)
    cases = load_cases(fixture_path)
    renderer = load_renderer()

    case_results: list[dict] = []
    errors: list[str] = []
    errors.extend(check_thread_scoped_roundtrip(renderer))

    for item in cases:
        baseline_case = renderer.build_case_from_source(build_source(item["raw_message"]))
        baseline_rendered = renderer.render_case(baseline_case)

        source = build_source(item["raw_message"], item.get("reply_memory"))
        case = renderer.build_case_from_source(source)
        rendered = renderer.render_case(case)
        scenario = case.get("scenario") or ""
        reply_memory_update = renderer.build_reply_memory_update(case, rendered)

        changed_from_baseline = normalize(rendered) != normalize(baseline_rendered)
        case_results.append(
            {
                "case_id": item["case_id"],
                "scenario": scenario,
                "changed_from_baseline": changed_from_baseline,
            }
        )

        expected_scenario = item.get("expected_scenario")
        if expected_scenario and scenario != expected_scenario:
            errors.append(f"{item['case_id']}: expected scenario {expected_scenario}, got {scenario}")

        if item.get("require_diff_from_baseline") and not changed_from_baseline:
            errors.append(f"{item['case_id']}: reply_memory did not change the rendered output")

        for marker in item.get("required_markers_any") or []:
            if marker in rendered:
                break
        else:
            if item.get("required_markers_any"):
                errors.append(f"{item['case_id']}: missing required reply_memory marker")

        for marker in item.get("forbidden_markers_any") or []:
            if marker in rendered:
                errors.append(f"{item['case_id']}: forbidden baseline-like marker survived: {marker}")

        expected_update = item.get("expected_memory_update") or {}
        for key, expected_value in expected_update.items():
            if key == "previous_deadline_promised_required":
                if expected_value and not reply_memory_update.get("previous_deadline_promised"):
                    errors.append(f"{item['case_id']}: reply_memory_update lost the promised deadline")
                continue
            actual_value = reply_memory_update.get(key)
            if actual_value != expected_value:
                errors.append(
                    f"{item['case_id']}: reply_memory_update[{key}] expected {expected_value!r}, got {actual_value!r}"
                )

    report_text = build_report_text(started_at, case_results, errors)
    if args.save_report:
        latest_path, history_path = save_report(report_text, started_at)
        print(f"report_latest: {latest_path}")
        print(f"report_history: {history_path}")
    print(report_text.rstrip())
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
