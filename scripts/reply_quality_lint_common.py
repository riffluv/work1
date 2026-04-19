#!/usr/bin/env python3
from __future__ import annotations

import re


STYLE_RULES: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(r"日本語が少し整理しきれていない"),
        "rendered text comments on the buyer's Japanese ability",
    ),
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
    (
        re.compile(r"大丈夫です。[\s\n]+大丈夫です。"),
        "rendered text still repeats `大丈夫です` too closely",
    ),
    (
        re.compile(r"(?:^|[^A-Za-z])(?:bugfix|handoff)(?:[^A-Za-z]|$)", re.IGNORECASE),
        "rendered text leaked internal service label `bugfix/handoff`",
    ),
    (
        re.compile(r"整理サービス"),
        "rendered text leaked internal service label `整理サービス`",
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
    (
        re.compile(r"(?:^|[^A-Za-z])(?:bugfix|handoff)(?:[^A-Za-z]|$)", re.IGNORECASE),
        "rendered text leaked internal service label `bugfix/handoff`",
    ),
    (
        re.compile(r"整理サービス"),
        "rendered text leaked internal service label `整理サービス`",
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
EMOTION_MARKER_MAP: dict[str, list[str]] = {
    "urgency": ["急ぎ", "お急ぎ", "売上影響", "売上への影響", "機会損失", "契約に影響", "今日中"],
    "frustration": ["お待たせしてすみません", "心配になりますよね", "気を遣わなくて大丈夫", "もっともです", "その点はもっとも", "お困り"],
    "anxiety": ["大丈夫", "心配", "不安", "気になる", "もっともです", "その点はもっとも", "気を遣わなくて大丈夫"],
    "distrust": ["前回", "経緯", "その点はもっとも", "大丈夫", "切り分け", "確認できます"],
}
EMPTY_PROMISE_MARKERS = [
    "先にお伝えします",
    "確認できているところから",
    "見えているところから",
]
PRICE_QUESTION_MARKERS = [
    "15,000",
    "15000",
    "10,000",
    "10000",
    "5,000",
    "5000",
    "25,000",
    "25000",
]
PRICE_RENDER_MARKERS = [
    "料金",
    "金額",
    "返金",
    "費用",
    "固定",
    "値引",
    "予算",
    "提案",
]
YEN_AMOUNT_RE = re.compile(r"[0-9]{1,3}(?:,[0-9]{3})*円|[0-9]{4,}円")


def infer_buyer_emotion(source_text: str) -> str:
    if any(marker in source_text for marker in ["信用するのが怖い", "半信半疑", "対象外ですと言われ", "再現できませんでした", "音沙汰なし"]):
        return "distrust"
    if any(marker in source_text for marker in ["参ってます", "困ってます", "まだ何も返事", "どうなってるんですか", "催促", "心配になってき", "気を遣わせ", "変なこと聞いて"]):
        return "frustration"
    if any(marker in source_text for marker in ["急ぎ", "今日中", "3日後", "契約に影響", "売上", "機会損失", "取りこぼし"]):
        return "urgency"
    if any(marker in source_text for marker in ["不安", "心配", "怖い", "恐縮", "恥ずかしい話", "初歩的", "よく分からない"]):
        return "anxiety"
    return "none"


def _normalized_text(text: str) -> str:
    return re.sub(r"[\s。、，,.！？?「」『』（）()・:：/／\-]+", "", text)


def _has_repeated_mazuha_opening(rendered: str) -> bool:
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", rendered) if part.strip()]
    starts = [paragraph for paragraph in paragraphs if paragraph.startswith("まずは")]
    return len(starts) >= 2


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


def _base_price_variants(base_price: int) -> set[str]:
    return {f"{base_price:,}円", f"{base_price}円"}


def _contains_base_price(text: str, base_price: int) -> bool:
    return any(variant in text for variant in _base_price_variants(base_price))


def _affirmative_hard_no_violation(rendered: str, key: str) -> bool:
    sentence_delims = ["。", "\n"]
    segments = [rendered]
    for delim in sentence_delims:
        next_segments: list[str] = []
        for segment in segments:
            next_segments.extend(part.strip() for part in segment.split(delim))
        segments = [segment for segment in next_segments if segment]

    negative_markers = ["使わず", "使わない", "切り替えず", "しません", "前提にしていません", "送らず", "避けて"]
    pattern_by_key: dict[str, list[re.Pattern[str]]] = {
        "external_share": [
            re.compile(r"(?:Google ?ドライブ|Dropbox|外部リンク).*(?:共有|リンク|ダウンロード).*(?:大丈夫|お願いします|ください)"),
        ],
        "external_contact": [
            re.compile(r"(?:Slack|LINE|Zoom|電話)で.*(?:進め|やり取り|連絡|お願いします|大丈夫)"),
            re.compile(r"メールで.*(?:やり取り|連絡|送って).*(?:大丈夫|お願いします)"),
        ],
        "external_payment": [
            re.compile(r"(?:銀行振込|PayPay|直接支払い).*(?:支払|お支払|振込|送金).*(?:大丈夫|お願いします|進め)"),
        ],
        "direct_push": [
            re.compile(r"(?:直接 ?push|master ブランチに push|pushしておいて|pushします)"),
        ],
        "prod_deploy": [
            re.compile(r"(?:こちらで|そのまま).*(?:本番反映|デプロイ).*(?:します|しておきます|進めます)"),
            re.compile(r"(?:本番反映|デプロイ)を.*(?:お願いします|進めます)"),
        ],
        "raw_secret_values": [
            re.compile(r"(?:\.env|シークレット|secret|キー).*(?:そのまま|値を).*(?:送って|貼って|共有して)"),
            re.compile(r"(?:そのまま|値を).*(?:送って|貼って).*(?:大丈夫|お願いします)"),
        ],
    }

    for segment in segments:
        if any(marker in segment for marker in negative_markers):
            continue
        for pattern in pattern_by_key.get(key, []):
            if pattern.search(segment):
                return True
    return False


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


def _common_prefix_len(left: str, right: str) -> int:
    count = 0
    for lch, rch in zip(left, right):
        if lch != rch:
            break
        count += 1
    return count


def _has_adjacent_near_echo(rendered: str) -> bool:
    sections = _split_sections(rendered)
    for left, right in zip(sections, sections[1:]):
        nl = _normalized_text(left)
        nr = _normalized_text(right)
        if not nl or not nr:
            continue
        shorter = min(len(nl), len(nr))
        if shorter < 12:
            continue
        if nl in nr or nr in nl:
            return True
        prefix_len = _common_prefix_len(nl, nr)
        if prefix_len >= 12 and prefix_len / shorter >= 0.55:
            return True
    return False




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


def _normalize_reply_memory(reply_memory: dict | None) -> dict:
    if not isinstance(reply_memory, dict):
        return {
            "followup_count": 0,
            "prior_tone": "neutral",
            "previous_assistant_commitment": "none",
            "previous_deadline_promised": None,
            "commitment_fulfilled": True,
        }
    raw_followup_count = reply_memory.get("followup_count") or 0
    try:
        followup_count = int(raw_followup_count)
    except (TypeError, ValueError):
        followup_count = 0
    return {
        "followup_count": followup_count,
        "prior_tone": str(reply_memory.get("prior_tone") or "neutral"),
        "previous_assistant_commitment": str(reply_memory.get("previous_assistant_commitment") or "none"),
        "previous_deadline_promised": (reply_memory.get("previous_deadline_promised") or None),
        "commitment_fulfilled": bool(reply_memory.get("commitment_fulfilled", True)),
    }


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
    reply_memory: dict | None = None,
) -> list[str]:
    errors: list[str] = []
    decision_plan = decision_plan or {}
    reply_memory = _normalize_reply_memory(reply_memory)
    direct_answer_line = (decision_plan.get("direct_answer_line") or "").strip()
    primary_question_id = (decision_plan.get("primary_question_id") or "").strip()
    buyer_emotion = (decision_plan.get("buyer_emotion") or "none").strip()
    response_order = decision_plan.get("response_order") or []
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

    if primary_question_id and direct_answer_line and len(response_order) >= 2 and response_order[1] == "direct_answer":
        answer_window = _answer_window_text(rendered)
        if direct_answer_line not in answer_window and not _rendered_has_direct_answer(answer_window):
            errors.append("plan says the main question should be answered early, but the opening block does not do so")

    if buyer_emotion in {"frustration", "distrust"}:
        opening_window = _answer_window_text(rendered)
        emotion_markers = EMOTION_MARKER_MAP.get(buyer_emotion) or []
        if emotion_markers and not any(marker in opening_window for marker in emotion_markers):
            errors.append("buyer emotion in plan is not reflected in the opening block")

    if any(marker in rendered for marker in EMPTY_PROMISE_MARKERS):
        concrete_markers = [
            "いまは、",
            "現時点では",
            "昨日いただいた内容をもとに",
            "原因の切り分けを進めています",
            "切り分け中",
            "見えている候補",
            "次に見る点",
            "環境変数",
            "Vercel",
            "Webhook",
            "signing secret",
            "payment_intent",
            "handleCardAction",
            "商品ID",
            "特定の商品",
        ]
        if not any(marker in rendered for marker in concrete_markers):
            errors.append("rendered text makes a progress promise without concrete status detail")

    if "目安をお返しします" in rendered and not any(marker in rendered for marker in ["原因の方向性", "次の見通し", "おおよその目安"]):
        errors.append("rendered text promises a timeline update without saying what concrete update will be sent")

    if "中間報告としてお返しできます" in rendered:
        errors.append("rendered text promises a progress summary without concretely framing the deliverable")

    followup_count = reply_memory.get("followup_count") or 0
    previous_commitment = reply_memory.get("previous_assistant_commitment") or "none"
    previous_deadline = str(reply_memory.get("previous_deadline_promised") or "")
    commitment_fulfilled = bool(reply_memory.get("commitment_fulfilled", True))
    first_text = _first_nonempty_text(rendered)

    if followup_count > 0 and first_text.startswith("ご連絡ありがとうございます"):
        errors.append("follow-up reply still opens like a first-contact reply")

    if previous_commitment != "none" and not commitment_fulfilled:
        progress_markers = [
            "いまは、",
            "現時点では",
            "原因の方向性",
            "次の見通し",
            "箇条書き",
            "見えている点",
            "切り分け中",
            "見立て",
            "昨日いただいた内容をもとに",
            "前回お伝えした",
        ]
        if previous_commitment == "share_summary" and not any(marker in rendered for marker in ["箇条書き", "見えている点", "整理した内容"]):
            errors.append("reply does not carry forward the previously promised summary deliverable")
        if previous_commitment == "share_eta" and not any(marker in rendered for marker in ["原因の方向性", "次の見通し", "見通し"]):
            errors.append("reply does not carry forward the previously promised timeline deliverable")
        if previous_commitment == "share_status" and not any(marker in rendered for marker in ["いまは、", "現時点では", "切り分け中", "見立て", "状況"]):
            errors.append("reply does not carry forward the previously promised status deliverable")
        if any(marker in rendered for marker in ["お返しします", "お送りします", "まとめます", "整理します"]) and not any(
            marker in rendered for marker in progress_markers
        ):
            errors.append("reply repeats an unfulfilled prior commitment without concrete progress")
        if previous_deadline and any(marker in rendered for marker in ["お返しします", "お送りします", "まとめます", "整理します"]) and not any(
            marker in rendered for marker in [previous_deadline, "原因の方向性", "次の見通し", "箇条書き", "見えている点"]
        ):
            errors.append("reply drops a previously promised deadline and replaces it with a vague new promise")

    return list(dict.fromkeys(errors))


def collect_service_binding_errors(
    rendered: str,
    source_text: str,
    service_grounding: dict | None = None,
    *,
    state: str | None = None,
    scenario: str | None = None,
) -> list[str]:
    del scenario
    errors: list[str] = []
    service_grounding = service_grounding or {}
    base_price = service_grounding.get("base_price")
    hard_no = service_grounding.get("hard_no") or []

    if isinstance(base_price, int):
        rendered_yen_amounts = set(YEN_AMOUNT_RE.findall(rendered))
        source_yen_amounts = set(YEN_AMOUNT_RE.findall(source_text))
        allowed_amounts = _base_price_variants(base_price)
        denial_markers = ["していません", "できません", "受けていません", "値引き", "値下げ", "変更はしていません", "下げる形では"]
        unsupported: list[str] = []
        for amount in sorted(rendered_yen_amounts):
            if amount in allowed_amounts or amount in source_yen_amounts:
                continue
            if any(amount in segment and any(marker in segment for marker in denial_markers) for segment in re.split(r"[。\n]", rendered)):
                continue
            unsupported.append(amount)
        if unsupported:
            errors.append(f"rendered text uses unsupported yen amount(s): {', '.join(unsupported)}")

        rendered_has_price_language = bool(rendered_yen_amounts) or any(marker in rendered for marker in PRICE_RENDER_MARKERS)
        if state == "quote_sent" and any(marker in source_text for marker in PRICE_QUESTION_MARKERS) and rendered_has_price_language:
            if not _contains_base_price(rendered, base_price):
                errors.append("price-related quote_sent reply does not anchor the service base_price explicitly")
            if any(marker in rendered for marker in PRICE_RENDER_MARKERS) and not _contains_base_price(rendered, base_price):
                errors.append("price-related quote_sent reply still uses vague fee wording without the service base_price")

    for key in hard_no:
        if _affirmative_hard_no_violation(rendered, key):
            errors.append(f"rendered text affirmatively permits a hard-no behavior: {key}")

    return list(dict.fromkeys(errors))


def collect_quality_style_errors(rendered: str) -> list[str]:
    errors: list[str] = []
    for pattern, message in STYLE_RULES:
        if pattern.search(rendered):
            errors.append(message)
    if _has_repeated_mazuha_opening(rendered):
        errors.append("rendered text still repeats `まずは` at paragraph openings")
    if _has_adjacent_near_echo(rendered):
        errors.append("rendered text still has near-echo across adjacent sections")
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
