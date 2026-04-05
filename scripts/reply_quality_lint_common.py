#!/usr/bin/env python3
from __future__ import annotations

import re


STYLE_RULES: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(r"(?:1つ|1点)だけ(?:そのまま)?(?:教えて|送って)ください"),
        "rendered text still uses the fixed `1つだけ` ask pattern",
    ),
    (
        re.compile(r"よさそうか"),
        "rendered text still uses the vague `よさそうか` ending",
    ),
    (
        re.compile(r"(?:次の|今回の|対応の)?進め方(?:を|が|で)"),
        "rendered text still uses PM-style `進め方` wording",
    ),
    (
        re.compile(r"流れになります"),
        "rendered text still uses PM-style `流れになります` wording",
    ),
    (
        re.compile(r"(?:共有します|共有が少なくて|共有を入れます)"),
        "rendered text still uses PM-style `共有` wording",
    ),
]

INTERNAL_TERM_RULES: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(r"公開サービス"),
        "rendered text leaked internal scope wording `公開サービス`",
    ),
    (
        re.compile(r"この中で"),
        "rendered text leaked internal scope wording `この中で`",
    ),
    (
        re.compile(r"入れる内容"),
        "rendered text leaked internal scope wording `入れる内容`",
    ),
    (
        re.compile(r"reply_contract|answer_map|ask_map"),
        "rendered text leaked internal contract wording",
    ),
]

DEFENSE_RULES: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(r"そう感じ(?:させ|させてしま).*理由"),
        "rendered text explains the user's negative feeling instead of just receiving it",
    ),
    (
        re.compile(r"その見え方になった"),
        "rendered text still uses defensive explanation wording",
    ),
]

BURDEN_SHIFT_RULES: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(r"優先順位.*教えてください"),
        "rendered text still asks the user to decide priorities",
    ),
    (
        re.compile(r"どちら(?:にするか|から入るか).*教えてください"),
        "rendered text still pushes branching judgment back to the user",
    ),
    (
        re.compile(r"判断.*お願いします"),
        "rendered text still asks the user to make the branching judgment",
    ),
    (
        re.compile(r"選んでください"),
        "rendered text still pushes the choice back to the user",
    ),
]

NEGATIVE_LEAD_RULE = re.compile(r"^(?:ただ|ですが)?[^。\n]*(?:しません|ありません|できません)")
SYMPTOM_REQUEST_RULE = re.compile(r"(症状|箇所|画面|エラー文|操作手順).*(送って|教えて|ください)")
MONEY_CONCERN_RULE = re.compile(r"(返金|追加料金|料金|金額|高い|高かった|15000|15,?000|5000|5,?000|払)")


def _normalized_text(text: str) -> str:
    return re.sub(r"[\s。、，,.！？?「」『』（）()・:：/／\-]+", "", text)


def _contains_money_anchor(text: str) -> bool:
    return any(
        marker in text
        for marker in [
            "15,000",
            "15000",
            "5,000",
            "5000",
            "返金",
            "追加料金",
            "固定料金",
            "提案",
            "料金",
            "金額",
            "ココナラ",
            "手続き",
        ]
    )


def _is_procedural_direct_answer(text: str) -> bool:
    stripped = text.strip("。")
    weak_markers = [
        "確認します",
        "確認して",
        "見ます",
        "見ていきます",
        "整理します",
        "お返しします",
        "ご相談します",
        "相談します",
        "案内します",
    ]
    return any(marker in stripped for marker in weak_markers)


def _split_sections(rendered: str) -> list[str]:
    sections: list[str] = []
    current: list[str] = []
    for raw_line in rendered.splitlines():
        line = raw_line.strip()
        if not line:
            if current:
                sections.append("\n".join(current))
                current = []
            continue
        current.append(line)
    if current:
        sections.append("\n".join(current))
    return sections


def _iter_texts(rendered: str, slot_values: dict[str, str] | None = None) -> list[str]:
    texts: list[str] = []
    if slot_values:
        texts.extend(value for value in slot_values.values() if value)
    if rendered:
        texts.append(rendered)
    return texts


def _first_nonempty_text(rendered: str, slot_values: dict[str, str] | None = None) -> str:
    if slot_values:
        for key in ("ack", "bridge_to_hold", "bridge_to_ask", "closing"):
            value = (slot_values.get(key) or "").strip()
            if value:
                return value
    for line in rendered.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return ""


def _opening_block_text(rendered: str, slot_values: dict[str, str] | None = None) -> str:
    if slot_values:
        parts = []
        for key in ("ack", "bridge_to_hold", "bridge_to_ask", "closing"):
            value = (slot_values.get(key) or "").strip()
            if value:
                parts.append(value)
        if parts:
            return "\n".join(parts)

    lines: list[str] = []
    for raw_line in rendered.splitlines():
        stripped = raw_line.strip()
        if not stripped:
            if lines:
                break
            continue
        lines.append(stripped)
    return "\n".join(lines)


def _answer_window_text(rendered: str) -> str:
    sections = _split_sections(rendered)
    return "\n".join(sections[:2])


def _rendered_has_direct_answer(rendered: str) -> bool:
    answer_window = _answer_window_text(rendered)
    markers = [
        "はい、",
        "いいえ、",
        "大丈夫です",
        "できます",
        "可能です",
        "進められます",
        "受けていません",
        "対象外です",
        "対象外になります",
        "相談できます",
        "確認できます",
        "このまま",
        "そのまま",
        "問題ありません",
        "待っていただいて",
        "承諾は急がなくて",
    ]
    return any(marker in answer_window for marker in markers)


def collect_answer_coverage_errors(
    rendered: str,
    source_text: str,
    contract: dict | None = None,
    routing_meta: dict | None = None,
    state: str | None = None,
) -> list[str]:
    errors: list[str] = []
    routing_meta = routing_meta or {}
    provided_context = set(routing_meta.get("provided_context") or [])

    if contract and source_text and any(marker in source_text for marker in ["？", "?", "ですか"]):
        primary_id = contract.get("primary_question_id")
        answer_map = contract.get("answer_map") or []
        primary = next((item for item in answer_map if item.get("question_id") == primary_id), None)
        if primary and primary.get("disposition") in {"answer_now", "decline"} and not _rendered_has_direct_answer(rendered):
            errors.append("direct-answer contract exists but rendered text does not answer the main question early")

    if state in {"purchased", "delivered", "closed", "quote_sent"} and "symptom_detail" in provided_context and SYMPTOM_REQUEST_RULE.search(rendered):
        errors.append("rendered text asks again for symptom/context already provided by the user")

    return list(dict.fromkeys(errors))


def collect_reasoning_preservation_errors(
    rendered: str,
    source_text: str,
    decision_plan: dict | None = None,
    scenario: str | None = None,
) -> list[str]:
    errors: list[str] = []
    decision_plan = decision_plan or {}
    direct_answer_line = (decision_plan.get("direct_answer_line") or "").strip()
    concern = scenario or decision_plan.get("primary_concern") or ""
    dedupe_sensitive_concerns = {
        "risk_refund_question",
        "extra_scope_question",
        "progress_anxiety",
        "price_complaint",
    }
    money_sensitive_concerns = {
        "risk_refund_question",
        "price_pushback",
        "extra_fee_anxiety",
        "price_complaint",
        "refund_request",
        "price_discount_request",
        "repeat_bugfix_price_check",
    }

    if direct_answer_line and concern in dedupe_sensitive_concerns:
        normalized_direct = _normalized_text(direct_answer_line)
        if len(normalized_direct) >= 6:
            repeated_sections = 0
            for section in _split_sections(rendered):
                if normalized_direct == _normalized_text(section):
                    repeated_sections += 1
            if repeated_sections > 1:
                errors.append("direct answer meaning is duplicated across multiple sections")

    if concern in money_sensitive_concerns and MONEY_CONCERN_RULE.search(source_text):
        answer_window = _answer_window_text(rendered)
        if not _contains_money_anchor(answer_window):
            errors.append("money-related concern is not answered with a concrete early anchor")
        if direct_answer_line and _is_procedural_direct_answer(direct_answer_line) and not _contains_money_anchor(direct_answer_line):
            errors.append("direct answer line is still procedural for a money-related question")

    return list(dict.fromkeys(errors))


def collect_quality_style_errors(rendered: str) -> list[str]:
    errors: list[str] = []
    for pattern, message in STYLE_RULES:
        if pattern.search(rendered):
            errors.append(message)
    return errors


def collect_temperature_constraint_errors(
    rendered: str,
    temperature_plan: dict | None,
    slot_values: dict[str, str] | None = None,
) -> list[str]:
    if not temperature_plan:
        return []

    errors: list[str] = []
    constraints = set(temperature_plan.get("tone_constraints") or [])
    texts = _iter_texts(rendered, slot_values)
    first_text = _first_nonempty_text(rendered, slot_values)
    opening_text = _opening_block_text(rendered, slot_values)
    opening_move = temperature_plan.get("opening_move") or ""

    if "no_internal_terms" in constraints:
        for text in texts:
            for pattern, message in INTERNAL_TERM_RULES:
                if pattern.search(text):
                    errors.append(message)

    if "no_defense" in constraints:
        for text in texts:
            for pattern, message in DEFENSE_RULES:
                if pattern.search(text):
                    errors.append(message)

    if "no_burden_shift" in constraints:
        for text in texts:
            for pattern, message in BURDEN_SHIFT_RULES:
                if pattern.search(text):
                    errors.append(message)

    if "no_negative_lead" in constraints and first_text and NEGATIVE_LEAD_RULE.search(first_text):
        errors.append("rendered text still starts with a negative lead")

    if opening_move == "action_first" and opening_text:
        if "確認しました" in opening_text:
            errors.append("action_first opening still starts with `確認しました`")
        if not any(marker in opening_text for marker in ["すぐ", "まず", "先に", "優先", "大丈夫"]):
            errors.append("action_first opening does not show action or reassurance early")

    if opening_move == "receive_and_own" and opening_text:
        if not any(marker in opening_text for marker in ["ありがとうございます", "すみません", "受け止めます", "伝えていただいて"]):
            errors.append("receive_and_own opening does not receive the feedback directly")

    return list(dict.fromkeys(errors))
