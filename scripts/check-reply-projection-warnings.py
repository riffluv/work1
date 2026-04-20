#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
from collections import Counter
from pathlib import Path

import yaml

from reply_quality_lint_common import (
    collect_report_anchor_warnings,
    collect_secondary_answer_projection_warnings,
    collect_technical_explanation_warnings,
)


ROOT_DIR = Path(__file__).resolve().parents[1]
EVAL_SOURCES = ROOT_DIR / "ops/tests/eval-sources.yaml"
UNIFIED_RENDERER = ROOT_DIR / "scripts/render-coconala-reply.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to load module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_active_sources(
    config_path: Path,
    roles: set[str] | None = None,
    exclude_roles: set[str] | None = None,
) -> list[dict]:
    data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    sources = [item for item in data.get("primary_sources", []) if item.get("status") == "active"]
    filtered: list[dict] = []
    for item in sources:
        role = item.get("role")
        if roles and role not in roles:
            continue
        if exclude_roles and role in exclude_roles:
            continue
        filtered.append(item)
    return filtered


def render_case(tools: dict[str, dict], module, source: dict) -> tuple[str, dict] | None:
    state = source.get("state")
    if state not in tools:
        return None
    tool = tools[state]
    case = tool["prepare_case_fn"](tool["drafter"], source)
    lane = module.choose_lane(case)
    if lane not in tools:
        return None
    rendered = tools[lane]["draft_fn"](tools[lane]["drafter"], case)
    return rendered, case


def main() -> int:
    parser = argparse.ArgumentParser(description="Warn-only projection checks for active coconala reply cases.")
    parser.add_argument("--role", action="append", help="Only include these roles from eval-sources. Repeatable.")
    parser.add_argument("--exclude-role", action="append", help="Exclude these roles from eval-sources. Repeatable.")
    args = parser.parse_args()

    module = load_module("render_coconala_reply", UNIFIED_RENDERER)
    tools = module.load_tools()
    sources = load_active_sources(
        EVAL_SOURCES,
        roles=set(args.role or []) or None,
        exclude_roles=set(args.exclude_role or []) or None,
    )

    tag_counter: Counter[str] = Counter()
    warning_count = 0
    rendered_count = 0

    case_loader = tools["prequote"]["drafter"].load_cases

    for source_item in sources:
        path = ROOT_DIR / source_item["path"]
        cases = case_loader(path)
        for source in cases:
            result = render_case(tools, module, source)
            if result is None:
                continue
            rendered, case = result
            rendered_count += 1
            warnings: list[str] = []
            warnings.extend(collect_secondary_answer_projection_warnings(rendered, case.get("reply_contract")))
            warnings.extend(collect_technical_explanation_warnings(rendered))
            warnings.extend(collect_report_anchor_warnings(rendered))
            warnings = list(dict.fromkeys(warnings))
            if not warnings:
                continue

            case_id = source.get("case_id") or source.get("id") or "<unknown>"
            print(f"[WARN] {case_id}")
            for item in warnings:
                print(f"  - {item}")
                warning_count += 1
                if item.startswith("secondary_answers_projected"):
                    tag_counter["secondary_answers_projected"] += 1
                elif item.startswith("report_verb_has_concrete_anchor"):
                    tag_counter["report_verb_has_concrete_anchor"] += 1
                elif item.startswith("technical line"):
                    tag_counter["technical_speculation"] += 1

    if tag_counter:
        print("")
        print("[summary]")
        for tag, count in sorted(tag_counter.items()):
            print(f"{tag}: {count}")

    print("")
    print(
        f"[OK] reply projection warnings completed: rendered={rendered_count} warnings={warning_count}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
