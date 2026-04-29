#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import re
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
ESTIMATE_DRAFTER = ROOT_DIR / "scripts/render-prequote-estimate-initial.py"
ESTIMATE_VALIDATOR = ROOT_DIR / "scripts/check-rendered-prequote-estimate.py"
PURCHASED_DRAFTER = ROOT_DIR / "scripts/render-post-purchase-quick.py"
PURCHASED_VALIDATOR = ROOT_DIR / "scripts/check-rendered-post-purchase-quick.py"
CLOSED_DRAFTER = ROOT_DIR / "scripts/render-closed-followup.py"
CLOSED_VALIDATOR = ROOT_DIR / "scripts/check-rendered-closed-followup.py"
DELIVERED_DRAFTER = ROOT_DIR / "scripts/render-delivered-followup.py"
DELIVERED_VALIDATOR = ROOT_DIR / "scripts/check-rendered-delivered-followup.py"
QUOTE_SENT_DRAFTER = ROOT_DIR / "scripts/render-quote-sent-followup.py"
QUOTE_SENT_VALIDATOR = ROOT_DIR / "scripts/check-rendered-quote-sent-followup.py"

COMMON_VALIDATOR_ITEMS = (
    "near_echo",
    "awkward_phrase",
    "buyer_questions",
    "buyer_word_pickup",
    "known_info_reask",
    "template_leakage",
    "hallucination",
    "direct_answer_first",
    "complaint_opening",
    "positive_acknowledgment",
    "closing_present",
    "negation_only_answer",
)

PUBLIC_MODE_LEAK_MARKERS = [
    "handoff-25000",
    "25,000円",
    "25000円",
    "25,000円側",
    "主要1フロー",
    "主要な処理の流れ1つ",
    "future-dual",
]

COMMON_BUYER_WORD_MARKERS: dict[str, list[str]] = {
    "proposal_change": ["提案", "同じ原因", "別原因", "メール", "決済"],
    "dashboard_scope_question": ["Webhook", "ダッシュボード", "設定"],
    "extra_fee_fear": ["キャンセル", "別原因", "料金", "追加対応"],
    "secret_share_reassurance": ["本番", "URL", "evt_", "ログ"],
    "no_meeting_request": ["Zoom", "通話", "スクショ", "箇条書き"],
    "extra_scope_question": ["読み込み", "ページ", "画面", "今回の件"],
    "keys_shared": ["キー名", "この情報", "値"],
    "progress_anxiety": ["48時間", "原因", "確認結果"],
    "delay_complaint_refund": ["進み具合", "返金", "状況"],
    "extra_fee_anxiety": ["追加料金", "別原因", "キャンセル"],
    "evidence_offer_question": ["スクショ", "Stripe", "管理画面"],
    "dashboard_test_label": ["Stripe", "テスト", "モード"],
    "side_effect_question": ["メール", "修正", "影響"],
    "redelivery_same_error": ["Vercel", "500", "デプロイ", "ローカル"],
    "delivery_scope_mismatch": ["診断レポート", "修正ファイル", "納品内容"],
    "approval_wait_request": ["承諾", "待ち", "確認"],
    "same_symptom_recur": ["同じ", "症状", "追加費用"],
    "similar_but_not_same": ["invoice.payment_failed", "イベント", "エラー"],
    "new_issue_repeat_client": ["見積り", "別の件", "定期課金"],
    "feedback_for_next_time": ["報告書", "噛み砕", "問題なかった"],
}

POSITIVE_FEEDBACK_MARKERS = [
    "前回の対応がよかった",
    "とてもよかった",
    "問題なかった",
    "安心しました",
    "助かりました",
    "順調に進んでいる",
]

COMPLAINT_MARKERS = [
    "納得いかない",
    "放置",
    "まだ何も進んでいません",
    "何度もやり取りしているのに",
    "いつになったら",
    "高いと感じます",
]

DIRECT_ANSWER_MARKERS = [
    "はい、",
    "いいえ、",
    "大丈夫です",
    "可能です",
    "できます",
    "進められます",
    "問題ありません",
    "見積りできます",
    "このまま",
    "そのまま",
]

NEGATION_MARKERS = [
    "できません",
    "しません",
    "ありません",
    "ではありません",
    "決まっているわけではありません",
    "言い切れません",
    "断定できていません",
    "断定できません",
]

NEGATION_RECOVERY_MARKERS = [
    "このまま",
    "そのまま",
    "まず",
    "対象フロー",
    "確認の範囲",
    "という意味",
    "送ってください",
    "教えてください",
    "キー名",
    "ご相談",
    "確認します",
    "確認できます",
    "確認結果",
    "ココナラ",
    "ご購入",
    "大丈夫です",
    "見積り",
    "見ます",
    "見て",
    "見立て",
    "状況",
    "症状",
    "同じ原因",
    "つながり",
    "スクショ",
    "手順",
    "意識します",
    "お伝えできます",
    "対応できます",
]

CLOSING_MARKERS = [
    "本日",
    "までに",
    "お返しします",
    "お送りします",
    "送ってください",
    "確認します",
    "見ます",
    "進めます",
    "大丈夫です",
    "問題ありません",
    "承諾",
    "ご購入",
    "ご相談します",
    "見立て",
    "意識します",
    "整えます",
]

AWKWARD_REPLY_PHRASE_MARKERS = [
    "見られる",
    "見られれば",
    "見たいです",
    "確認したいです",
    "切りたいです",
]

NEAR_ECHO_SHARED_PHRASES = [
    "優先して確認",
    "関係があるか",
    "つながりを確認",
    "今回の範囲",
    "分かる範囲",
    "続きとして",
    "フォーム送信後のリダイレクト",
    "PayPay対応で触った",
    "まず確認",
    "そのままご購入いただいて大丈夫です",
]

GENERIC_REASK_TEMPLATES = [
    "気になっている点を1〜2点だけそのまま送ってください。",
    "気になっている点を1〜2点だけそのまま送ってください",
]

OPTIONAL_ASK_MARKERS = [
    "もし今後",
    "もし気になる",
    "難しければ",
    "まだ出せなければ",
    "必要なら",
]

SUSPICIOUS_CAMELCASE_RE = re.compile(r"\b[a-z]+[A-Z][A-Za-z0-9_]*\b")
SUSPICIOUS_DOTTED_TOKEN_RE = re.compile(r"\b[a-z_]+\.[a-z_]+\.[a-z_]+\b")
SUSPICIOUS_EVENT_ID_RE = re.compile(r"\bevt_[A-Za-z0-9_.-]+\b")

def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to load module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def prepare_prequote_case(drafter, source: dict) -> dict:
    if source.get("reply_contract"):
        return source
    return drafter.build_case_from_source(source)


def prepare_lane_case(drafter, source: dict) -> dict:
    return drafter.build_case_from_source(source)


def draft_case(drafter, case: dict) -> str:
    return drafter.render_case(case)


def render_prequote_from_source(drafter, source: dict) -> str:
    case = prepare_prequote_case(drafter, source)
    return draft_case(drafter, case)


def render_lane_from_source(drafter, source: dict) -> str:
    case = prepare_lane_case(drafter, source)
    return draft_case(drafter, case)


def load_tools() -> dict[str, dict]:
    estimate_drafter = load_module("render_prequote_estimate_initial", ESTIMATE_DRAFTER)
    purchased_drafter = load_module("render_post_purchase_quick", PURCHASED_DRAFTER)
    closed_drafter = load_module("render_closed_followup", CLOSED_DRAFTER)
    delivered_drafter = load_module("render_delivered_followup", DELIVERED_DRAFTER)
    quote_sent_drafter = load_module("render_quote_sent_followup", QUOTE_SENT_DRAFTER)
    estimate_validator = load_module("check_rendered_prequote_estimate", ESTIMATE_VALIDATOR)
    purchased_validator = load_module("check_rendered_post_purchase_quick", PURCHASED_VALIDATOR)
    closed_validator = load_module("check_rendered_closed_followup", CLOSED_VALIDATOR)
    delivered_validator = load_module("check_rendered_delivered_followup", DELIVERED_VALIDATOR)
    quote_sent_validator = load_module("check_rendered_quote_sent_followup", QUOTE_SENT_VALIDATOR)

    tools = {
        "prequote": {
            "drafter": estimate_drafter,
            "renderer": estimate_drafter,
            "prepare_case_fn": prepare_prequote_case,
            "draft_fn": draft_case,
            "render_fn": render_prequote_from_source,
            "lane_validator_module": estimate_validator,
            "lane_validator_fn": lambda source: estimate_validator.lint_case(estimate_drafter, source),
        },
        "purchased": {
            "drafter": purchased_drafter,
            "renderer": purchased_drafter,
            "prepare_case_fn": prepare_lane_case,
            "draft_fn": draft_case,
            "render_fn": render_lane_from_source,
            "lane_validator_module": purchased_validator,
            "lane_validator_fn": lambda source: purchased_validator.lint_case(purchased_drafter, source),
        },
        "closed": {
            "drafter": closed_drafter,
            "renderer": closed_drafter,
            "prepare_case_fn": prepare_lane_case,
            "draft_fn": draft_case,
            "render_fn": render_lane_from_source,
            "lane_validator_module": closed_validator,
            "lane_validator_fn": lambda source: closed_validator.lint_case(closed_drafter, source),
        },
        "delivered": {
            "drafter": delivered_drafter,
            "renderer": delivered_drafter,
            "prepare_case_fn": prepare_lane_case,
            "draft_fn": draft_case,
            "render_fn": render_lane_from_source,
            "lane_validator_module": delivered_validator,
            "lane_validator_fn": lambda source: delivered_validator.lint_case(delivered_drafter, source),
        },
        "quote_sent": {
            "drafter": quote_sent_drafter,
            "renderer": quote_sent_drafter,
            "prepare_case_fn": prepare_lane_case,
            "draft_fn": draft_case,
            "render_fn": render_lane_from_source,
            "lane_validator_module": quote_sent_validator,
            "lane_validator_fn": lambda source: quote_sent_validator.lint_case(quote_sent_drafter, source),
        },
    }
    for lane in tools:
        tools[lane]["lint_fn"] = lambda source, lane=lane, tools=tools: lint_pipeline_case(lane, source, tools)
    return tools


def choose_lane(case: dict) -> str | None:
    state = case.get("state")
    skeleton = (case.get("reply_stance") or {}).get("reply_skeleton")

    if skeleton == "estimate_initial" and state == "prequote":
        return "prequote"
    if skeleton == "post_purchase_quick" and state == "purchased":
        return "purchased"
    if skeleton == "estimate_followup" and state == "closed":
        return "closed"
    if skeleton == "delivery" and state == "delivered":
        return "delivered"
    if skeleton == "estimate_followup" and state == "quote_sent":
        return "quote_sent"

    if skeleton:
        return None
    if state in {"prequote", "purchased", "closed", "delivered", "quote_sent"}:
        return state
    return None


def has_any(text: str, needles: list[str]) -> bool:
    return any(needle in text for needle in needles)


def extract_buyer_questions(raw: str, state: str | None) -> list[dict]:
    questions: list[dict] = []

    def add(question_id: str, markers: list[str]) -> None:
        questions.append({"id": question_id, "markers": markers})

    if has_any(raw, ["影響しますか", "影響ありますか", "影響しますでしょうか"]):
        add("impact_check", ["影響します", "影響があります", "影響する", "前提で見ています"])
    if has_any(raw, ["届いてますでしょうか", "届いてますか", "届いているか"]):
        add("receipt_confirm", ["確認できています", "届いています", "確認しました"])
    if has_any(raw, ["どういう流れ", "イメージできてなく", "流れで進む"]):
        add("process_flow", ["追加で必要なものがあれば", "こちらからお願いします", "まず受け取っている内容を"])
    if has_any(raw, ["追加で用意", "準備しておきます", "用意した方がいい"]):
        add("prep_need", ["追加で準備いただくものはありません", "必要なものがあれば", "こちらからお願いします"])
    if has_any(raw, ["どのくらいかか", "大体どのくらい", "今週末", "調査結果だけでも"]):
        add("timeline_check", ["調査結果", "今週末", "先にお送りします", "直せるか", "完了時期", "見通し"])
    if has_any(raw, ["対応してもらえますか", "対応してもらえますでしょうか"]) and has_any(raw, ["書き直して", "自分で触った", "余計に壊してる", "変に触っ"]):
        add("self_edit_support", ["今の状態を見て", "対応可否", "確認できます"])
    if "追加料金" in raw:
        add("fee_anxiety", ["追加料金", "追加見積り", "料金", "事前にご相談", "決まるわけではなく", "自動で"])
    if has_any(raw, ["受信側だけ", "受信側だけですよね"]):
        add("scope_confirmation", ["Webhook", "受信側"])
    if has_any(raw, ["本番で試すのが怖", "テストしてから承諾", "送信テストしてみた"]):
        add("safe_test_before_approval", ["送信テスト", "承諾前", "本番で決済を試さなくても", "十分です"])
    if state == "closed" and has_any(raw, ["お願いできるもの", "見積りをいただけますか"]):
        add("can_request", ["見積りできます", "確認できます", "お願いします"])

    deduped: list[dict] = []
    seen: set[str] = set()
    for question in questions:
        question_id = question["id"]
        if question_id in seen:
            continue
        seen.add(question_id)
        deduped.append(question)
    return deduped


def normalized(text: str) -> str:
    return re.sub(r"[\s。、，,.！？?「」『』（）()・:：/／\\-]+", "", text)


def split_sections(text: str) -> list[str]:
    sections: list[str] = []
    current: list[str] = []
    for raw_line in text.splitlines():
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


def first_nonempty_line(text: str) -> str:
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line:
            return line
    return ""


def opening_window(text: str, sections: int = 2) -> str:
    return "\n".join(split_sections(text)[:sections])


def final_section(text: str) -> str:
    sections = split_sections(text)
    return sections[-1] if sections else ""


def has_near_echo(rendered: str) -> bool:
    sections = split_sections(rendered)
    for left, right in zip(sections, sections[1:]):
        nl = normalized(left)
        nr = normalized(right)
        if not nl or not nr:
            continue
        if len(nl) >= 10 and (nl in nr or nr in nl):
            return True
        for phrase in NEAR_ECHO_SHARED_PHRASES:
            normalized_phrase = normalized(phrase)
            if normalized_phrase and normalized_phrase in nl and normalized_phrase in nr:
                return True
    return False


def is_complaint_like(source: dict, case: dict | None = None) -> bool:
    raw = source.get("raw_message", "")
    tone = ((case or {}).get("emotional_tone") or source.get("emotional_tone") or "").strip()
    if tone == "complaint_like":
        return True
    if "放置して大丈夫" in raw or "放置しても大丈夫" in raw:
        return False
    return has_any(raw, COMPLAINT_MARKERS)


def has_positive_signal(raw: str) -> bool:
    return has_any(raw, POSITIVE_FEEDBACK_MARKERS)


def direct_answer_visible_early(rendered: str) -> bool:
    return has_any(opening_window(rendered), DIRECT_ANSWER_MARKERS)


def buyer_word_pickup_ok(rendered: str, raw: str, scenario: str | None) -> bool:
    markers = COMMON_BUYER_WORD_MARKERS.get(scenario or "", [])
    if not markers:
        return True
    if not has_any(raw, markers):
        return True
    return has_any(opening_window(rendered), markers)


def buyer_questions_covered(rendered: str, buyer_questions: list[dict]) -> list[str]:
    errors: list[str] = []
    for question in buyer_questions:
        markers = question.get("markers") or []
        if markers and not has_any(rendered, markers):
            errors.append(f"common_validator buyer_questions failed: `{question.get('id', '')}` was not answered directly")
    return errors


def has_known_info_reask(rendered: str, buyer_questions: list[dict], blocking_missing_facts: list[str]) -> bool:
    _ = blocking_missing_facts
    if not buyer_questions:
        return False
    if has_any(rendered, OPTIONAL_ASK_MARKERS):
        return False
    return has_any(rendered, GENERIC_REASK_TEMPLATES)


def collect_template_leakage_errors(rendered: str, raw: str) -> list[str]:
    errors: list[str] = []
    if has_any(rendered, ["テストモード", "モード切り替え"]) and not has_any(raw, ["テストモード", "モード切り替え", "表示"]):
        errors.append("common_validator template_leakage failed: dashboard-test template leaked into a different buyer question")
    if "気になっている点を1〜2点だけそのまま送ってください" in rendered and has_any(
        raw,
        ["どのくらい", "届いてます", "対応してもらえますか", "追加料金", "承諾", "何かいい方法"],
    ):
        errors.append("common_validator template_leakage failed: generic ask template leaked over a concrete buyer question")
    return errors


def collect_hallucination_errors(rendered: str, raw: str) -> list[str]:
    errors: list[str] = []
    suspicious_tokens = set(SUSPICIOUS_CAMELCASE_RE.findall(rendered))
    suspicious_tokens.update(SUSPICIOUS_DOTTED_TOKEN_RE.findall(rendered))
    suspicious_tokens.update(SUSPICIOUS_EVENT_ID_RE.findall(rendered))

    for token in sorted(suspicious_tokens):
        if token in raw:
            continue
        errors.append(f"common_validator hallucination failed: token `{token}` is not present in the buyer message")
    return errors


def collect_awkward_phrase_errors(rendered: str) -> list[str]:
    errors: list[str] = []
    for marker in AWKWARD_REPLY_PHRASE_MARKERS:
        if marker in rendered:
            errors.append(f"common_validator awkward_phrase failed: `{marker}` should be rewritten")
    return errors


def is_public_reply_case(source: dict, case: dict) -> bool:
    service_grounding = case.get("service_grounding") or source.get("service_grounding") or {}
    service_id = case.get("service_id") or source.get("service_id") or service_grounding.get("service_id")
    public_service = service_grounding.get("public_service")
    if service_id == "handoff-25000":
        return False
    if public_service is False:
        return False
    return True


def collect_public_mode_leakage_errors(rendered: str, source: dict, case: dict) -> list[str]:
    if not is_public_reply_case(source, case):
        return []
    leaked = [marker for marker in PUBLIC_MODE_LEAK_MARKERS if marker in rendered]
    if not leaked:
        return []
    return [f"public_mode_leakage failed: private/shadow wording leaked into public reply: {', '.join(leaked)}"]


def has_negation_only_answer(rendered: str) -> bool:
    answer_window = opening_window(rendered, sections=3)
    if not has_any(answer_window, NEGATION_MARKERS):
        return False
    return not has_any(answer_window, NEGATION_RECOVERY_MARKERS)


def has_closing(rendered: str) -> bool:
    closing = final_section(rendered)
    if not closing:
        return False
    return has_any(closing, CLOSING_MARKERS)


def requires_closing(case: dict) -> bool:
    contract = case.get("reply_contract") or {}
    answer_map = contract.get("answer_map") or []
    primary_id = contract.get("primary_question_id")
    primary = next((item for item in answer_map if item.get("question_id") == primary_id), {})
    if primary.get("disposition") == "answer_now" and not contract.get("ask_map"):
        return False

    state = case.get("state")
    if state in {"purchased", "delivered"}:
        return True
    if primary.get("disposition") == "answer_after_check":
        return True
    if contract.get("ask_map"):
        return True
    return False


def has_error_marker(errors: list[str], markers: list[str]) -> bool:
    return any(any(marker in error for marker in markers) for error in errors)


def collect_common_validator_errors(
    rendered: str,
    source: dict,
    case: dict,
    lane_errors: list[str],
) -> list[str]:
    state = case.get("state")
    if state not in {"quote_sent", "purchased", "delivered", "closed"}:
        return []

    raw = source.get("raw_message", "")
    scenario = case.get("scenario")
    contract = case.get("reply_contract") or {}
    decision_plan = case.get("response_decision_plan") or {}
    direct_answer_line = (decision_plan.get("direct_answer_line") or "").strip()
    buyer_questions = source.get("buyer_questions") or []
    blocking_missing_facts = decision_plan.get("blocking_missing_facts") or []
    errors: list[str] = []

    if not has_error_marker(lane_errors, ["near_echo"]):
        if has_near_echo(rendered):
            errors.append("common_validator near_echo failed")

    if not has_error_marker(lane_errors, ["awkward_phrase"]):
        errors.extend(collect_awkward_phrase_errors(rendered))

    if not has_error_marker(lane_errors, ["buyer_questions"]):
        errors.extend(buyer_questions_covered(rendered, buyer_questions))

    if not has_error_marker(lane_errors, ["buyer_word_pickup"]):
        if not buyer_word_pickup_ok(rendered, raw, scenario):
            errors.append("common_validator buyer_word_pickup failed")

    if not has_error_marker(lane_errors, ["re-asks despite no blocking", "already provided by the user"]):
        if has_known_info_reask(rendered, buyer_questions, blocking_missing_facts):
            errors.append("common_validator known_info_reask failed: rendered text re-asks despite concrete buyer questions already being present")

    if not has_error_marker(lane_errors, ["template_leakage"]):
        errors.extend(collect_template_leakage_errors(rendered, raw))

    if not has_error_marker(lane_errors, ["hallucination"]):
        errors.extend(collect_hallucination_errors(rendered, raw))

    if not has_error_marker(lane_errors, ["direct answer", "answer the main question early"]):
        if direct_answer_line and direct_answer_line in rendered:
            if direct_answer_line not in opening_window(rendered):
                errors.append("common_validator direct_answer_first failed: answer is not visible in the opening window")
            direct_index = rendered.find(direct_answer_line)
            for ask in contract.get("ask_map") or []:
                ask_text = ask.get("ask_text", "")
                if ask_text and ask_text in rendered and rendered.find(ask_text) < direct_index:
                    errors.append("common_validator direct_answer_first failed: answer appears after ask")
                    break
            hold_reason = ""
            answer_map = contract.get("answer_map") or []
            primary_id = contract.get("primary_question_id")
            for answer in answer_map:
                if answer.get("question_id") == primary_id:
                    hold_reason = answer.get("hold_reason", "")
                    break
            if hold_reason and hold_reason in rendered and rendered.find(hold_reason) < direct_index:
                errors.append("common_validator direct_answer_first failed: answer appears after hold reason")

    if state in {"purchased", "delivered"} and is_complaint_like(source, case) and not has_error_marker(lane_errors, ["complaint_opening", "complaint opening"]):
        opening = first_nonempty_line(rendered)
        opening_text = opening_window(rendered, sections=3)
        if "ありがとう" in opening:
            errors.append("common_validator complaint_opening failed: still starts with gratitude")
        elif not has_any(opening_text, ["すみません", "申し訳", "お待たせ", "ごもっとも", "率直に伝えていただき", "受け止め"]):
            errors.append("common_validator complaint_opening failed: opening does not receive the complaint directly")

    if has_positive_signal(raw) and not has_error_marker(lane_errors, ["positive", "問題なかった", "よかった"]):
        if not has_any(opening_window(rendered), ["ありがとうございます", "よかった", "問題なかった", "安心", "フィードバック"]):
            errors.append("common_validator positive_acknowledgment failed")

    if requires_closing(case) and not has_error_marker(lane_errors, ["closing_present", "missing time commitment"]):
        if not has_closing(rendered):
            errors.append("common_validator closing_present failed")

    if state in {"purchased", "delivered"} and not has_error_marker(lane_errors, ["negation_only_answer"]):
        if has_negation_only_answer(rendered):
            errors.append("common_validator negation_only_answer failed")

    return list(dict.fromkeys(errors))


def apply_semantic_safe_naturalization(reply: str, case: dict, lane: str) -> str:
    # Keep this stage identity-only until we have a typed naturalizer that cannot change meaning.
    _ = (case, lane)
    return reply


def run_pipeline(source: dict, tools: dict[str, dict] | None = None, lint: bool = False) -> dict:
    tools = tools or load_tools()
    enriched_source = dict(source)
    enriched_source["buyer_questions"] = extract_buyer_questions(source.get("raw_message", ""), source.get("state"))
    if enriched_source.get("state") == "purchased" and "reply_memory" not in enriched_source:
        enriched_source["reply_memory"] = tools["prequote"]["drafter"].load_reply_memory()
    lane = choose_lane(enriched_source)
    case_id = source.get("case_id") or source.get("id") or "<unknown>"
    state = source.get("state") or "<unknown>"
    if lane is None:
        return {
            "case_id": case_id,
            "state": state,
            "lane": None,
            "case": None,
            "drafted_reply": "",
            "sendable_reply": "",
            "lane_errors": [],
            "common_errors": [],
            "errors": ["unsupported state / reply_skeleton combination"],
        }

    tool = tools[lane]
    drafter = tool["drafter"]
    case = tool["prepare_case_fn"](drafter, enriched_source)
    if case is not None and not case.get("buyer_questions"):
        case["buyer_questions"] = list(enriched_source.get("buyer_questions") or [])
    drafted_reply = tool["draft_fn"](drafter, case)
    sendable_reply = apply_semantic_safe_naturalization(drafted_reply, case, lane)

    lane_errors = tool["lane_validator_fn"](enriched_source) if lint else []
    common_errors = collect_common_validator_errors(sendable_reply, enriched_source, case, lane_errors) if lint else []
    mode_errors = collect_public_mode_leakage_errors(sendable_reply, enriched_source, case) if lint else []
    errors = list(dict.fromkeys([*lane_errors, *common_errors, *mode_errors]))

    return {
        "case_id": case_id,
        "state": state,
        "lane": lane,
        "case": case,
        "drafted_reply": drafted_reply,
        "sendable_reply": sendable_reply,
        "lane_errors": lane_errors,
        "common_errors": common_errors,
        "mode_errors": mode_errors,
        "errors": errors,
    }


def lint_pipeline_case(lane: str, source: dict, tools: dict[str, dict] | None = None) -> list[str]:
    tools = tools or load_tools()
    result = run_pipeline(source, tools=tools, lint=True)
    if result["lane"] != lane:
        return [f"pipeline lane mismatch: expected {lane}, got {result['lane'] or 'unsupported'}"]
    return result["errors"]


def format_block(case_id: str, state: str, lane: str, reply: str) -> str:
    return f"case_id: {case_id}\nstate: {state}\nlane: {lane}\n{reply}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Unified coconala reply pipeline for prequote / quote_sent / purchased / delivered / closed.")
    parser.add_argument("--fixture", required=True)
    parser.add_argument("--case-id")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--lint", action="store_true")
    parser.add_argument("--save", action="store_true")
    args = parser.parse_args()

    tools = load_tools()
    estimate_drafter = tools["prequote"]["drafter"]
    cases = estimate_drafter.load_cases(Path(args.fixture))

    if args.case_id:
        cases = [case for case in cases if case.get("case_id") == args.case_id or case.get("id") == args.case_id]
    if args.limit is not None:
        cases = cases[: args.limit]
    if not cases:
        print("[NG] no cases selected")
        return 1

    rendered_blocks: list[str] = []
    lint_errors: list[str] = []
    save_payload: tuple[str, str, dict | None] | None = None

    for source in cases:
        result = run_pipeline(source, tools=tools, lint=args.lint)
        if result["lane"] is None:
            lint_errors.extend(f"[NG] {result['case_id']}: {error}" for error in result["errors"])
            continue

        rendered_blocks.append(format_block(result["case_id"], result["state"], result["lane"], result["sendable_reply"]))

        if args.lint and result["errors"]:
            lint_errors.extend(f"[NG] {result['case_id']}: {error}" for error in result["errors"])

        if args.save:
            if len(cases) != 1:
                print("[NG] --save requires exactly one case")
                return 1
            save_payload = (
                result["sendable_reply"],
                source.get("raw_message", ""),
                (result.get("case") or {}).get("reply_memory_update"),
            )

    if save_payload is not None:
        estimate_drafter.save_reply(*save_payload)

    if rendered_blocks:
        print("\n\n----\n\n".join(rendered_blocks))

    if lint_errors:
        print()
        for line in lint_errors:
            print(line)
        return 1

    if args.lint:
        print()
        print(f"[OK] unified reply lint passed: {len(rendered_blocks)} case(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
