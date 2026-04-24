#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import re
import sys
from pathlib import Path

from reply_quality_lint_common import collect_quality_style_errors

ROOT_DIR = Path(__file__).resolve().parents[1]
RENDERER_PATH = ROOT_DIR / "scripts/render-prequote-estimate-initial.py"


def load_renderer_module():
    spec = importlib.util.spec_from_file_location("render_prequote_estimate_initial", RENDERER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to load renderer: {RENDERER_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def has_any(text: str, needles: list[str]) -> bool:
    return any(needle in text for needle in needles)


def needs_screenshot_guidance(question_text: str) -> bool:
    return "スクショ" in question_text or ("画面" in question_text and any(marker in question_text for marker in ["送", "見せ", "撮"]))


def is_private_service_case(case: dict) -> bool:
    service_id = case.get("service_id")
    return bool(service_id and service_id != "bugfix-15000")


def lint_case(module, case: dict) -> list[str]:
    normalized = case if case.get("reply_contract") else module.build_case_from_source(case)
    if is_private_service_case(normalized):
        return []
    rendered = module.render_case(normalized)
    contract = normalized["reply_contract"]
    temperature_plan = normalized.get("temperature_plan") or {}
    primary_id = contract["primary_question_id"]
    primary = next(item for item in contract["answer_map"] if item["question_id"] == primary_id)
    primary_question_type = primary.get("question_type")
    question_map = {item["id"]: item["text"] for item in contract["explicit_questions"]}
    errors: list[str] = []

    if not temperature_plan:
        errors.append("temperature_plan is missing")
    if not normalized.get("render_payload"):
        errors.append("render_payload is missing")
    if normalized.get("render_payload_violations"):
        for violation in normalized["render_payload_violations"]:
            errors.append(f"render payload validator violation: {violation}")

    if primary["disposition"] == "answer_now":
        direct_acceptance_markers = ["15,000円", "対応できます", "対応できる"]
        if primary_question_type == "service_selection":
            direct_acceptance_markers.extend(["まずこの不具合対応から入るのが近い", "まずこの不具合対応から"])
        if primary_question_type == "investigation_only":
            direct_acceptance_markers.extend(["調べるだけでも大丈夫です", "原因の調査から対応"])
        if not has_any(rendered, direct_acceptance_markers):
            errors.append("primary answer_now case is missing direct acceptance language")
    if primary["disposition"] == "answer_after_check":
        if not has_any(
            rendered,
            [
                "断定しにくい",
                "断定しません",
                "確認できます",
                "見てから判断",
                "言い切るより",
                "見てから案内",
                "言い切りにくい",
                "判断できます",
                "まず何が起きているかを確認する",
                "まず必要な情報を見てから判断",
                "まず困っている点から見ていく",
                "この入口から見ていけます",
                "今の情報だけではまだ判断し切れない",
                "追加情報を受領したあとに",
                "この内容も確認できますが",
            ],
        ):
            errors.append("primary answer_after_check case is missing defer language")
        if not contract.get("ask_map"):
            errors.append("primary answer_after_check case has no ask_map")
    if contract.get("ask_map") and not has_any(rendered, ["教えてください", "送ってください", "ください"]):
        errors.append("ask_map exists but rendered text has no ask request")
    if any(ask.get("default_path_text") for ask in contract.get("ask_map") or []):
        if not has_any(rendered, ["なければ", "難しければ", "決まっていなければ", "すぐ出せなければ", "まだ絞れていなければ"]):
            errors.append("optional ask exists but rendered text has no default-path language")

    forbidden_terms = [
        "GitHubに招待",
        "Driveに置いて",
        "Dropbox",
        "外部決済",
        "無料で対応",
        "sk_live_",
        "whsec_",
    ]
    for term in forbidden_terms:
        if term in rendered:
            errors.append(f"forbidden term leaked into rendered text: {term}")

    for answer in contract["answer_map"]:
        qtext = question_map.get(answer["question_id"], "")
        if ".env" in qtext or "APIキー" in qtext:
            if not has_any(rendered, [".env", "キー名だけ"]):
                errors.append("secret sharing question exists but rendered text does not block raw secret sharing")
        if needs_screenshot_guidance(qtext):
            if not has_any(rendered, ["スクショ", "画面"]):
                errors.append("screenshot question exists but rendered text does not mention screenshot guidance")
        if "税込" in qtext:
            if not has_any(rendered, ["ココナラ画面", "表示される金額"]):
                errors.append("tax question exists but rendered text does not answer displayed price directly")
        if "今週中" in qtext or "今日中" in qtext or "何日" in qtext or "いつ" in qtext:
            if not has_any(rendered, ["納期", "見通し"]):
                errors.append("timeline question exists but rendered text does not mention timing follow-up")
        if "不正アクセス" in qtext:
            if "不正アクセスかどうかは" not in rendered:
                errors.append("security question exists but rendered text does not defer security judgment explicitly")
        if has_any(qtext, ["直接会って", "Zoom", "通話"]):
            if not has_any(rendered, ["トークルーム", "テキスト", "Zoomではなく", "通話やZoomではなく"]):
                errors.append("meeting request exists but rendered text does not keep text-only boundary")
        if "もっと安く" in qtext or "安くなりますか" in qtext:
            if not has_any(rendered, ["15,000円で固定", "15,000円", "公開サービス"]):
                errors.append("discount question exists but rendered text does not keep fixed-price boundary")

    raw_message = normalized.get("raw_message", "")
    if (
        "価値があるか" in raw_message
        or "内容に差があるなら" in raw_message
        or (
            re.search(r"(^|[^0-9])5,000円", raw_message)
            and not has_any(raw_message, ["5,000円とか", "5,000円くらい", "10,000円", "もっと安く", "値引", "お試し"])
        )
    ):
        if not has_any(rendered, ["今の公開サービス", "断定しにくい", "案内できる範囲"]):
            errors.append("value comparison case exists but rendered text does not keep service-boundary framing")

    errors.extend(collect_quality_style_errors(rendered))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Lint rendered estimate_initial replies against minimal structural checks.")
    parser.add_argument("--fixture", required=True)
    parser.add_argument("--case-id")
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()

    module = load_renderer_module()
    cases = module.load_cases(Path(args.fixture))
    if args.case_id:
        cases = [case for case in cases if case.get("id") == args.case_id or case.get("case_id") == args.case_id]
    if args.limit is not None:
        cases = cases[: args.limit]
    if not cases:
        print("[NG] no cases selected")
        return 1

    had_error = False
    checked = 0
    for case in cases:
        normalized = case if case.get("reply_contract") else module.build_case_from_source(case)
        if normalized.get("state") != "prequote":
            continue
        if normalized.get("reply_stance", {}).get("reply_skeleton") != "estimate_initial":
            continue
        checked += 1
        errors = lint_case(module, case)
        if errors:
            had_error = True
            case_id = normalized.get("id", "<unknown>")
            for error in errors:
                print(f"[NG] {case_id}: {error}")

    if had_error:
        return 1
    print(f"[OK] rendered estimate_initial lint passed: {checked} case(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
