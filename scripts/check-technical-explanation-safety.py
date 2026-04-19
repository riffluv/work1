#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from reply_quality_lint_common import collect_technical_explanation_warnings


ROOT_DIR = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT_DIR / "ops/tests/regression/technical_explanation_safety/cases.yaml"


def load_cases(path: Path) -> list[dict]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data.get("cases") or []


def main() -> int:
    parser = argparse.ArgumentParser(description="Check warn-only technical explanation safety fixture.")
    parser.add_argument("--fixture", default=str(FIXTURE_PATH))
    args = parser.parse_args()

    cases = load_cases(Path(args.fixture))
    if not cases:
        print("[NG] no cases loaded")
        return 1

    errors: list[str] = []
    for case in cases:
        warnings = collect_technical_explanation_warnings(case["text"])
        has_warning = bool(warnings)
        expected = bool(case.get("expect_warning"))
        if has_warning != expected:
            errors.append(
                f"{case['case_id']}: expected warning={expected}, got warning={has_warning}"
            )
        if has_warning:
            print(f"[WARN] {case['case_id']}")
            for item in warnings:
                print(f"  - {item}")

    if errors:
        for error in errors:
            print(f"[NG] {error}")
        return 1

    print(f"[OK] technical explanation safety fixture passed: {len(cases)} case(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
