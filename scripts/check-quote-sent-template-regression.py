#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
from collections import defaultdict
from datetime import datetime
from pathlib import Path
import re
from zoneinfo import ZoneInfo

import yaml


ROOT_DIR = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT_DIR / "ops/tests/regression/quote_sent_template_check/cases.yaml"
RENDERER_PATH = ROOT_DIR / "scripts/render-quote-sent-followup.py"
REPORT_DIR = ROOT_DIR / "runtime/regression/coconala-reply/quote-sent-template"
JST = ZoneInfo("Asia/Tokyo")


def load_renderer():
    import sys

    sys.path.insert(0, str(ROOT_DIR / "scripts"))
    spec = importlib.util.spec_from_file_location("render_quote_sent_followup", RENDERER_PATH)
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


def body_signature(rendered: str) -> str:
    paragraphs = [paragraph.strip() for paragraph in rendered.split("\n\n") if paragraph.strip()]
    if len(paragraphs) >= 3:
        target = paragraphs[1:-1]
    elif len(paragraphs) >= 2:
        target = paragraphs[1:]
    else:
        target = paragraphs
    return "\n".join(normalize(paragraph) for paragraph in target if paragraph.strip())


def direct_answer_signature(rendered: str) -> str:
    paragraphs = [paragraph.strip() for paragraph in rendered.split("\n\n") if paragraph.strip()]
    if len(paragraphs) < 2:
        return ""
    return normalize(paragraphs[1].splitlines()[0].strip())


def build_report_text(
    started_at: datetime,
    case_results: list[dict],
    duplicate_groups: list[list[str]],
    errors: list[str],
) -> str:
    lines = [f"generated_at: {started_at.strftime('%Y-%m-%d %H:%M:%S %Z')}", "", "[cases]"]
    for result in case_results:
        lines.append(f"{result['case_id']}: scenario={result['scenario']}")
    lines.extend(["", "[duplicate_body_groups]"])
    if duplicate_groups:
        for group in duplicate_groups:
            lines.append(", ".join(group))
    else:
        lines.append("<none>")
    if errors:
        lines.extend(["", "[errors]"])
        lines.extend(errors)
        lines.extend(["", "[status]", "[NG] quote_sent template regression failed"])
    else:
        lines.extend(["", "[status]", "[OK] quote_sent template regression passed"])
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
    parser = argparse.ArgumentParser(description="Check quote_sent template regression fixture.")
    parser.add_argument("--fixture", default=str(FIXTURE_PATH))
    parser.add_argument("--save-report", action="store_true")
    args = parser.parse_args()

    started_at = datetime.now(JST)
    fixture_path = Path(args.fixture)
    cases = load_cases(fixture_path)
    renderer = load_renderer()

    case_results: list[dict] = []
    errors: list[str] = []
    signatures: dict[str, list[str]] = defaultdict(list)
    direct_signatures: dict[str, list[str]] = defaultdict(list)

    for item in cases:
        source = {
            "case_id": item["case_id"],
            "raw_message": item["raw_message"],
            "route": "service",
            "user_type": "buyer",
        }
        case = renderer.build_case_from_source(source)
        rendered = renderer.render_case(case)
        scenario = case.get("scenario") or ""
        case_results.append(
            {
                "case_id": item["case_id"],
                "scenario": scenario,
                "rendered": rendered,
            }
        )

        expected_scenario = item.get("expected_scenario")
        if expected_scenario and scenario != expected_scenario:
            errors.append(f"{item['case_id']}: expected scenario {expected_scenario}, got {scenario}")

        context_markers = item.get("required_context_markers_any") or []
        if context_markers and not any(marker in rendered for marker in context_markers):
            errors.append(f"{item['case_id']}: missing required context pickup")

        support_markers = item.get("required_support_markers_any") or []
        if support_markers and not any(marker in rendered for marker in support_markers):
            errors.append(f"{item['case_id']}: missing required support pickup")

        signatures[body_signature(rendered)].append(item["case_id"])
        direct_signatures[direct_answer_signature(rendered)].append(item["case_id"])

    duplicate_groups = [group for group in signatures.values() if len(group) >= 3]
    for group in duplicate_groups:
        errors.append(f"body_signature duplicated across {len(group)} cases: {', '.join(group)}")
    duplicate_direct_groups = [group for key, group in direct_signatures.items() if key and len(group) >= 3]
    for group in duplicate_direct_groups:
        errors.append(f"direct_answer_signature duplicated across {len(group)} cases: {', '.join(group)}")

    report_text = build_report_text(started_at, case_results, duplicate_groups, errors)
    if args.save_report:
        latest_path, history_path = save_report(report_text, started_at)
        print(f"report_latest: {latest_path}")
        print(f"report_history: {history_path}")
    print(report_text.rstrip())
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
