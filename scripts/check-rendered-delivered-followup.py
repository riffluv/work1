#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
RENDERER_PATH = ROOT_DIR / "scripts/render-delivered-followup.py"


def load_renderer():
    spec = importlib.util.spec_from_file_location("render_delivered_followup", RENDERER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to load renderer: {RENDERER_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def has_any(text: str, needles: list[str]) -> bool:
    return any(needle in text for needle in needles)


def lint_case(module, source: dict) -> list[str]:
    case = module.build_case_from_source(source)
    rendered = module.render_case(case)
    contract = case["reply_contract"]
    primary_id = contract["primary_question_id"]
    primary = next(item for item in contract["answer_map"] if item["question_id"] == primary_id)
    raw = source.get("raw_message", "")
    scenario = case.get("scenario")
    errors: list[str] = []

    if not has_any(rendered, ["ありがとうございます", "確認しました"]):
        errors.append("missing brief reaction at the top")

    if primary["disposition"] == "answer_after_check":
        if not has_any(rendered, ["確認", "断定", "見直し"]):
            errors.append("answer_after_check exists but defer language is weak")
        if contract.get("ask_map") and not has_any(rendered, ["送ってください", "教えてください", "ください"]):
            errors.append("answer_after_check case has ask_map but no ask request")
        if "本日" not in rendered or "までに" not in rendered:
            errors.append("answer_after_check delivered case is missing time commitment")

    if primary["disposition"] == "answer_now":
        if not primary.get("answer_brief", "") or primary["answer_brief"] not in rendered:
            errors.append("direct primary answer is missing from rendered text")

    if scenario == "approval_ok" and "承諾" not in rendered:
        errors.append("approval case does not mention 承諾 directly")
    if scenario == "prevention_question" and not has_any(rendered, ["再発", "起きにくく", "可能性"]):
        errors.append("prevention case does not answer recurrence directly")
    if scenario == "delivery_scope_mismatch" and not has_any(rendered, ["期待と違っていた", "認識差", "差し戻し"]):
        errors.append("delivery mismatch complaint is not acknowledged clearly")
    if "Stripeのダッシュボードに「テスト」" in raw and "テストモード" not in rendered:
        errors.append("dashboard test label case does not mention mode check")

    forbidden_terms = ["GitHubに招待", "Driveに置いて", "Dropbox", "外部決済", "無料で対応"]
    for term in forbidden_terms:
        if term in rendered:
            errors.append(f"forbidden term leaked into rendered text: {term}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Lint rendered delivered follow-up replies.")
    parser.add_argument("--fixture", required=True)
    parser.add_argument("--case-id")
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()

    module = load_renderer()
    cases = module.shared.load_cases(Path(args.fixture))
    cases = [case for case in cases if case.get("state") == "delivered"]
    if args.case_id:
        cases = [case for case in cases if case.get("case_id") == args.case_id or case.get("id") == args.case_id]
    if args.limit is not None:
        cases = cases[: args.limit]
    if not cases:
        print("[NG] no delivered cases selected")
        return 1

    had_error = False
    for source in cases:
        case_id = source.get("case_id") or source.get("id") or "<unknown>"
        errors = lint_case(module, source)
        for error in errors:
            print(f"[NG] {case_id}: {error}")
            had_error = True

    if had_error:
        return 1
    print(f"[OK] rendered delivered follow-up lint passed: {len(cases)} case(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
