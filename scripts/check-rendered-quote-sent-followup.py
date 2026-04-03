#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
RENDERER_PATH = ROOT_DIR / "scripts/render-quote-sent-followup.py"


def load_renderer():
    spec = importlib.util.spec_from_file_location("render_quote_sent_followup", RENDERER_PATH)
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
    primary = case["reply_contract"]["answer_map"][0]
    scenario = case.get("scenario")
    raw = source.get("raw_message", "")
    errors: list[str] = []

    if not has_any(rendered, ["ありがとうございます", "確認しました"]):
        errors.append("missing brief reaction at the top")
    if primary["answer_brief"] not in rendered:
        errors.append("primary answer is missing from rendered text")

    if scenario == "proposal_change":
        if not has_any(rendered, ["変更したい点", "1〜2点"]):
            errors.append("proposal change case does not ask for minimal change points")
        if not has_any(rendered, ["同じ提案", "提案"]):
            errors.append("proposal change case does not mention proposal scope")

    if scenario == "purchase_timing" and not has_any(rendered, ["来週", "再提案"]):
        errors.append("purchase timing case does not answer timing directly")

    if scenario == "reissue_quote" and not has_any(rendered, ["再提案", "同じ内容"]):
        errors.append("reissue case does not answer re-proposal directly")

    if scenario == "risk_refund_question":
        if has_any(rendered, ["返金します", "返金できます", "返金をお約束"]):
            errors.append("risk/refund case answers refund too definitively")
        if not has_any(rendered, ["ココナラ", "手続き"]):
            errors.append("risk/refund case does not place refund on coconala-side procedure")

    if scenario == "payment_method" and not has_any(rendered, ["ココナラ側", "支払い画面"]):
        errors.append("payment method case does not clarify coconala-side limitation")

    forbidden_terms = ["GitHubに招待", "Driveに置いて", "Dropbox", "外部決済", "無料で対応"]
    for term in forbidden_terms:
        if term in rendered:
            errors.append(f"forbidden term leaked into rendered text: {term}")

    if "提案" in raw and not has_any(rendered, ["提案"]):
        errors.append("quote_sent case does not mention proposal context")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Lint rendered quote_sent follow-up replies.")
    parser.add_argument("--fixture", required=True)
    parser.add_argument("--case-id")
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()

    module = load_renderer()
    cases = module.shared.load_cases(Path(args.fixture))
    cases = [case for case in cases if case.get("state") == "quote_sent"]
    if args.case_id:
        cases = [case for case in cases if case.get("case_id") == args.case_id or case.get("id") == args.case_id]
    if args.limit is not None:
        cases = cases[: args.limit]
    if not cases:
        print("[NG] no quote_sent cases selected")
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
    print(f"[OK] rendered quote_sent follow-up lint passed: {len(cases)} case(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
