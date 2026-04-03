#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
RENDERER_PATH = ROOT_DIR / "scripts/render-closed-followup.py"


def load_renderer():
    spec = importlib.util.spec_from_file_location("render_closed_followup", RENDERER_PATH)
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

    if not has_any(rendered, ["ありがとうございます", "確認しました", "承知しました"]):
        errors.append("missing brief reaction at the top")
    if "本日" not in rendered or "までに" not in rendered:
        errors.append("missing time commitment")
    if has_any(rendered, ["15,000円", "25000円", "25,000円"]):
        errors.append("closed follow-up should not front-load price")

    if primary["disposition"] == "answer_after_check":
        if not has_any(rendered, ["確認します", "断定", "状況確認", "見て"]):
            errors.append("answer_after_check exists but defer language is weak")
        if not has_any(rendered, ["トークルーム", "閉じて"]):
            errors.append("closed defer case does not mention closed-room boundary")
        if contract.get("ask_map") and not has_any(rendered, ["送ってください", "教えてください"]):
            errors.append("answer_after_check case has ask_map but no ask request")

    if primary["disposition"] in {"answer_now", "decline"}:
        if not primary.get("answer_brief", "") or primary["answer_brief"] not in rendered:
            errors.append("direct primary answer is missing from rendered text")

    if "返金" in raw:
        if has_any(rendered, ["返金します", "返金できます"]):
            errors.append("refund request was answered too definitively")
        if not has_any(rendered, ["返金", "状況確認", "つながり"]):
            errors.append("refund request is not acknowledged clearly")

    if "新しい機能" in raw or "クーポン機能" in raw:
        if not has_any(rendered, ["範囲ではありません", "機能追加"]):
            errors.append("new feature request is not declined clearly")

    if scenario == "new_issue_repeat_client":
        if not has_any(rendered, ["確認できます"]):
            errors.append("repeat client new issue is not answered positively")
        if not has_any(rendered, ["送ってください"]):
            errors.append("repeat client new issue is missing minimal ask")

    forbidden_terms = ["GitHubに招待", "Driveに置いて", "Dropbox", "Zoom", "外部決済", "このトークルームでそのまま"]
    for term in forbidden_terms:
        if term in rendered:
            errors.append(f"forbidden term leaked into rendered text: {term}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Lint rendered closed follow-up replies.")
    parser.add_argument("--fixture", required=True)
    parser.add_argument("--case-id")
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()

    module = load_renderer()
    cases = module.shared.load_cases(Path(args.fixture))
    cases = [case for case in cases if case.get("state") == "closed"]
    if args.case_id:
        cases = [case for case in cases if case.get("case_id") == args.case_id or case.get("id") == args.case_id]
    if args.limit is not None:
        cases = cases[: args.limit]
    if not cases:
        print("[NG] no closed cases selected")
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
    print(f"[OK] rendered closed follow-up lint passed: {len(cases)} case(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
