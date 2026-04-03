#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
RENDERER_PATH = ROOT_DIR / "scripts/render-post-purchase-quick.py"


def load_renderer():
    spec = importlib.util.spec_from_file_location("render_post_purchase_quick", RENDERER_PATH)
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
    errors: list[str] = []

    if not has_any(rendered, ["ありがとうございます", "確認しました"]):
        errors.append("missing brief reaction at the top")
    if "本日" not in rendered or "までに" not in rendered:
        errors.append("missing time commitment")

    for answer in contract["answer_map"]:
        qid = answer["question_id"]
        qtext = next(item["text"] for item in contract["explicit_questions"] if item["id"] == qid)
        disposition = answer["disposition"]

        if disposition == "answer_now":
            if "料金" in qtext and not has_any(rendered, ["料金", "金額", "別で請求", "変えません", "見積り"]):
                errors.append("price-related answer_now question is not answered directly")
            if ".env" in qtext and not has_any(rendered, [".env", "キー名だけ"]):
                errors.append("secret-sharing answer_now question is not blocked directly")

        if disposition == "answer_after_check":
            if not has_any(rendered, ["まだ", "確認します", "未確定", "断定"]):
                errors.append("answer_after_check exists but defer language is weak")

    raw = source.get("raw_message", "")
    if "Googleドライブ" in raw or "Google Drive" in raw:
        if not has_any(rendered, ["トークルーム", "Googleドライブは使わず"]):
            errors.append("external share suggestion exists but rendered text does not stop it clearly")
    if ".env" in raw and "値は送らなくて大丈夫" not in raw:
        if not has_any(rendered, [".env", "キー名だけ"]):
            errors.append("raw .env mention exists but rendered text does not mention secret handling")
    if has_any(raw, ["別なんですが", "別のところ", "一緒に見てもら", "これも一緒", "今回とは別", "別の画面"]):
        if not has_any(rendered, ["今回の件", "別の話", "つながっている"]):
            errors.append("scope-addition case exists but rendered text does not mention relation/scope split")

    forbidden_terms = ["GitHubに招待", "Driveに置いて", "Dropbox", "外部決済"]
    for term in forbidden_terms:
        if term in rendered:
            errors.append(f"forbidden term leaked into rendered text: {term}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Lint rendered post_purchase_quick replies.")
    parser.add_argument("--fixture", required=True)
    parser.add_argument("--case-id")
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()

    module = load_renderer()
    cases = module.shared.load_cases(Path(args.fixture))
    cases = [case for case in cases if case.get("state") == "purchased"]
    if args.case_id:
        cases = [case for case in cases if case.get("case_id") == args.case_id or case.get("id") == args.case_id]
    if args.limit is not None:
        cases = cases[: args.limit]
    if not cases:
        print("[NG] no purchased cases selected")
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
    print(f"[OK] rendered post_purchase_quick lint passed: {len(cases)} case(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
