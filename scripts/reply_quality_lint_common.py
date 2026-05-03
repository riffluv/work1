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
        re.compile(r"(?:進め方になります|進め方を(?:お返し|返せます|返します)|次の進め方をお返しします|その前提で進め方)"),
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
        re.compile(r"確認しました。[\s\n]+はい、[^。\n]{0,60}(?:確認できています|届いています)"),
        "rendered text repeats receipt confirmation with mechanical `はい` after `確認しました`",
    ),
    (
        re.compile(r"今の情報だけではまだ判断し切れない[\s\S]{0,90}まず必要な情報を見てから判断[\s\S]{0,90}まだ断定しません"),
        "rendered text repeats the information-insufficient judgment three times",
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

TECHNICAL_CONTEXT_MARKERS = [
    "Stripe",
    "Webhook",
    "webhook",
    "API",
    "API Routes",
    "endpoint",
    "エンドポイント",
    "Vercel",
    "Firestore",
    "Checkout",
    "会員ステータス",
    "バリデーション",
    "環境変数",
    "環境差",
    "ログ",
    "受信",
]

TECHNICAL_SPECULATION_RULES: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(r"可能性が高(?:い|く|そう)"),
        "technical line uses strong speculation wording around `可能性が高い`",
    ),
    (
        re.compile(r"おそらく"),
        "technical line uses speculation wording `おそらく`",
    ),
    (
        re.compile(r"思われます"),
        "technical line uses speculation wording `思われます`",
    ),
    (
        re.compile(r"線が濃い"),
        "technical line uses speculation wording `線が濃い`",
    ),
    (
        re.compile(r"っぽいです"),
        "technical line uses speculation wording `っぽいです`",
    ),
    (
        re.compile(r"原因(?:は|が)[^。\n]{0,24}です"),
        "technical line states a likely cause too directly",
    ),
]

FLOW_WARNING_SAFETY_MARKERS = [
    "15,000円",
    "25,000円",
    "範囲外",
    "含まれません",
    "対応できません",
    "返金",
    "無料",
    "保証",
    "secret",
    "Secret",
    "APIキー",
    "Webhook secret",
    ".env",
    "直接push",
    "直接 push",
    "本番反映",
    "クローズ",
    "旧トークルーム",
]

FLOW_WARNING_EMAIL_PHRASES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"平素より"), "conversation_flow warning: email-style phrase `平素より` appears in chat reply"),
    (re.compile(r"ご査収"), "conversation_flow warning: email-style phrase `ご査収` appears in chat reply"),
    (
        re.compile(r"何卒よろしくお願い申し上げます"),
        "conversation_flow warning: heavy email closing `何卒よろしくお願い申し上げます` appears in chat reply",
    ),
]

FLOW_DEICTIC_AGENCY_WARNINGS: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(r"(?:無理に)?こちらで(?:選び切|絞)"),
        "agency_alignment warning: `こちらで選ぶ/絞る` may reverse buyer material work and seller checking work",
    ),
]

FLOW_ANSWERABILITY_WARNINGS: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(r"(?:ログ|スクショ|関係ファイル|ZIP|zip|ファイル)[^。\n]{0,40}(?:届いています|受け取っています|受け取りました|確認できています)"),
        "answerability_boundary warning: material receipt is asserted; ensure material_received evidence is available",
    ),
    (
        re.compile(r"(?:今は|現在は|現時点では)[^。\n]{0,70}(?:見ています|確認しています|照合しています|進めています)"),
        "answerability_boundary warning: current work status is asserted; ensure work_status evidence is available",
    ),
    (
        re.compile(r"本日\d{1,2}:\d{2}まで"),
        "answerability_boundary warning: specific same-day deadline is asserted; ensure deadline_authorized is available",
    ),
    (
        re.compile(r"(?:反映するファイル|確認する画面|どの画面|どのファイル|どの順番)[^。\n]{0,90}(?:整理します|お伝えします|まとめます)"),
        "answerability_boundary warning: delivered follow-up may promise a concrete answer without delivery context",
    ),
]

FLOW_ASSERTIVE_ENDING_RE = re.compile(
    r"(?:です|ます|ません|できます|しました|しています|なります|ありません|ください)[。！？!?]?$"
)

FLOW_REPEATED_ENDINGS = [
    "確認します",
    "確認しました",
    "お返しします",
    "進めます",
    "ご連絡します",
    "お願いします",
    "ください",
    "対応できます",
    "対応できません",
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
QUOTE_SENT_CLOSING_MARKERS = [
    "見積り提案の内容で",
    "見積もり提案の内容で",
]
QUOTE_SENT_SOURCE_EVIDENCE_MARKERS = [
    "見積り提案ありがとうございます",
    "見積もり提案ありがとうございます",
    "見積りありがとうございます",
    "見積もりありがとうございます",
    "提案ありがとうございます",
]
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
SECONDARY_PROJECTION_MARKER_GROUPS: list[tuple[list[str], list[str]]] = [
    (
        ["追加料金", "別料金", "料金", "金額", "返金", "値引"],
        ["追加料金", "料金", "金額", "返金", "値引", "固定", "別対応", "先にお伝え"],
    ),
    (
        ["今日中", "いつ", "進捗", "目安", "いつまで"],
        ["本日", "明日", "までに", "進捗", "見通し", "いまは", "現時点", "切り分け"],
    ),
    (
        ["本番反映", "手順", "気をつけ"],
        ["本番反映", "手順", "環境変数", "差分", "確認"],
    ),
    (
        ["修正", "続けて", "頼め", "含ま", "別対応"],
        ["修正", "続けて", "別対応", "含み"],
    ),
    (
        ["どちらのサービス", "どちらが合"],
        ["この不具合対応", "引き継ぎ", "整理", "近い"],
    ),
]
REPORT_VERB_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"(?:整理|確認|共有|案内|ご案内)(?:して)?お返しします"),
    re.compile(r"(?:整理|確認)(?:して)?お送りします"),
    re.compile(r"まとめます"),
]
REPORT_ANCHOR_MARKERS = [
    "本日",
    "明日",
    "までに",
    "いまは",
    "現時点",
    "見通し",
    "原因の方向性",
    "箇条書き",
    "見えている点",
    "整理した内容",
    "危険箇所",
    "関連ファイル",
    "次の着手順",
    "手順",
    "進捗",
    "状況",
    "確認結果",
    "どこまで",
    "どこで",
    "何を",
    "何が",
    "見るポイント",
    "反映前",
    "差分",
    "結論",
    "要点",
    "一覧",
    "箇条書き",
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

    negative_markers = [
        "使わず",
        "使わない",
        "切り替えず",
        "しません",
        "前提にしていません",
        "行っていません",
        "行いません",
        "行っておりません",
        "送らず",
        "避けて",
    ]
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

    if any(marker in rendered for marker in QUOTE_SENT_CLOSING_MARKERS):
        has_quote_sent_evidence = state == "quote_sent" or any(marker in source_text for marker in QUOTE_SENT_SOURCE_EVIDENCE_MARKERS)
        if not has_quote_sent_evidence:
            errors.append("quote_sent-only closing used without quote_sent state/evidence")

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


def collect_technical_explanation_warnings(rendered: str) -> list[str]:
    warnings: list[str] = []
    segments = [segment.strip() for segment in re.split(r"[。\n]+", rendered) if segment.strip()]
    for segment in segments:
        if not any(marker in segment for marker in TECHNICAL_CONTEXT_MARKERS):
            continue
        for pattern, message in TECHNICAL_SPECULATION_RULES:
            if pattern.search(segment):
                warnings.append(f"{message}: {segment}")
    return list(dict.fromkeys(warnings))


def _conversation_flow_sentence_units(rendered: str) -> list[str]:
    units: list[str] = []
    for raw_line in rendered.splitlines():
        line = raw_line.strip()
        if not line or line.startswith((">", "- ", "・", "* ")):
            continue
        parts = re.split(r"(?<=[。！？!?])\s*", line)
        for part in parts:
            sentence = part.strip()
            if sentence:
                units.append(sentence)
    return units


def _conversation_flow_paragraph_units(rendered: str) -> list[str]:
    units: list[str] = []
    for block in re.split(r"\n\s*\n", rendered):
        paragraph = " ".join(line.strip() for line in block.splitlines() if line.strip())
        if not paragraph or paragraph.startswith((">", "- ", "・", "* ")):
            continue
        if len(re.findall(r"[。！？!?]", paragraph)) > 1:
            continue
        units.append(paragraph)
    return units


def _flow_segment_is_safety_boundary(segment: str) -> bool:
    return any(marker in segment for marker in FLOW_WARNING_SAFETY_MARKERS)


def _nearby_repetition_count(rendered: str, term: str, distance: int) -> int:
    positions = [match.start() for match in re.finditer(re.escape(term), rendered)]
    count = 0
    for left, right in zip(positions, positions[1:]):
        if right - left <= distance:
            count += 1
    return count + 1 if count else 0


def collect_conversation_flow_warnings(rendered: str) -> list[str]:
    warnings: list[str] = []

    for pattern, message in FLOW_WARNING_EMAIL_PHRASES:
        if pattern.search(rendered):
            warnings.append(message)

    for pattern, message in FLOW_DEICTIC_AGENCY_WARNINGS:
        if pattern.search(rendered):
            warnings.append(message)

    for pattern, message in FLOW_ANSWERABILITY_WARNINGS:
        if pattern.search(rendered):
            warnings.append(message)

    if "前回の修正と関係" in rendered and "確認" in rendered:
        if not any(marker in rendered for marker in ["見える範囲", "ここでできるのは", "実作業", "修正作業", "修正済みファイル"]):
            warnings.append(
                "post_completion_followup_scope_clarity warning: relation check is mentioned without clarifying visible-range check and work boundary"
            )

    if "関係ファイル" in rendered and "分かる範囲" in rendered:
        if not any(marker in rendered for marker in ["コード一式", "ZIP", "zip", "スクショ", "ログ"]):
            warnings.append(
                "material_selection_burden warning: file-unknown buyer may still be asked to choose relation files without safe default input"
            )

    if all(
        marker in rendered
        for marker in [
            "トークルームは閉じているため",
            "ログやスクショを送ってください",
            "見積り提案または新規依頼",
        ]
    ):
        warnings.append(
            "conversation_flow warning: closed follow-up materials reply is split into rule / request / route; "
            "answer that logs/screenshots can be sent here first, then keep the closed-room boundary"
        )

    sentences = _conversation_flow_sentence_units(rendered)
    paragraphs = _conversation_flow_paragraph_units(rendered)
    streak: list[str] = []
    for paragraph in paragraphs:
        stripped = paragraph.rstrip("。！？!?")
        if _flow_segment_is_safety_boundary(paragraph):
            streak = []
            continue
        if len(stripped) <= 28 and FLOW_ASSERTIVE_ENDING_RE.search(paragraph):
            streak.append(paragraph)
            if len(streak) >= 3:
                sample = " / ".join(streak[-3:])
                warnings.append(
                    "conversation_flow warning: short one-sentence paragraphs appear three times in a row; "
                    f"consider connecting only strongly related facts: {sample}"
                )
                streak = []
        else:
            streak = []

    for ending in FLOW_REPEATED_ENDINGS:
        count = sum(1 for sentence in sentences if sentence.rstrip("。！？!?").endswith(ending))
        if count >= 3:
            warnings.append(
                f"conversation_flow warning: repeated sentence ending `{ending}` appears {count} times"
            )

    if all(term in rendered for term in ["確認しました", "確認します", "確認結果"]):
        positions = [rendered.find(term) for term in ["確認しました", "確認します", "確認結果"]]
        if max(positions) - min(positions) <= 360:
            warnings.append(
                "conversation_flow warning: `確認しました` / `確認します` / `確認結果` appear nearby; "
                "separate receipt, checking, and reporting roles only if needed"
            )

    if _nearby_repetition_count(rendered, "お返しします", 420) >= 3:
        warnings.append(
            "conversation_flow warning: `お返しします` repeats nearby; consider varying the report verb"
        )

    if _nearby_repetition_count(rendered, "進めます", 420) >= 3:
        warnings.append(
            "conversation_flow warning: `進めます` repeats nearby; clarify which action is being progressed"
        )

    return list(dict.fromkeys(warnings))


def collect_secondary_answer_projection_warnings(rendered: str, contract: dict | None = None) -> list[str]:
    if not contract:
        return []

    warnings: list[str] = []
    primary_id = contract.get("primary_question_id")
    questions_by_id = {
        item.get("id"): item.get("text", "")
        for item in (contract.get("explicit_questions") or [])
        if item.get("id")
    }

    for answer in contract.get("answer_map") or []:
        question_id = answer.get("question_id")
        if not question_id or question_id == primary_id:
            continue
        if answer.get("disposition") not in {"answer_now", "decline"}:
            continue

        question_text = questions_by_id.get(question_id, "")
        answer_brief = (answer.get("answer_brief") or "").strip()
        if answer_brief and answer_brief in rendered:
            continue

        combined = f"{question_text} {answer_brief}"
        expected_markers: list[str] = []
        for triggers, anchors in SECONDARY_PROJECTION_MARKER_GROUPS:
            if any(trigger in combined for trigger in triggers):
                expected_markers.extend(anchors)

        if not expected_markers:
            continue
        if any(marker in rendered for marker in expected_markers):
            continue

        warnings.append(
            f"secondary_answers_projected warning: `{question_text}` may not be reflected in the rendered text"
        )

    return list(dict.fromkeys(warnings))


def collect_report_anchor_warnings(rendered: str) -> list[str]:
    warnings: list[str] = []
    segments = [segment.strip() for segment in re.split(r"[。\n]+", rendered) if segment.strip()]
    for segment in segments:
        if not any(pattern.search(segment) for pattern in REPORT_VERB_PATTERNS):
            continue
        if not any(token in segment for token in ["お返し", "お送り", "まとめ"]):
            continue
        if any(marker in segment for marker in REPORT_ANCHOR_MARKERS):
            continue
        warnings.append(
            f"report_verb_has_concrete_anchor warning: `{segment}`"
        )
    return list(dict.fromkeys(warnings))


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
        if not any(marker in opening_text for marker in ["すぐ", "まず", "先に", "優先", "大丈夫", "承知"]):
            errors.append("action_first opening does not show action or reassurance early")

    if opening_move == "receive_and_own" and opening_text:
        if not any(marker in opening_text for marker in ["ありがとうございます", "すみません", "受け止めます", "伝えていただいて"]):
            errors.append("receive_and_own opening does not receive the feedback directly")

    return list(dict.fromkeys(errors))
