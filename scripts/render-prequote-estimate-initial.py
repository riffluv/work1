#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

import yaml

from reply_quality_lint_common import collect_temperature_constraint_errors


ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_FIXTURE = ROOT_DIR / "ops/tests/prequote-contract-v2-top5.yaml"
REPLY_SAVE = ROOT_DIR / "scripts/reply-save.sh"


def strip_period(text: str) -> str:
    return text.strip().rstrip("。")


def compact_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def numbered_marker_count(text: str) -> int:
    return len(re.findall(r"[①-⑨]", text))


def parse_text_case_file(path: Path) -> list[dict]:
    cases: list[dict] = []
    current: dict[str, str] = {}

    with path.open("r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.rstrip("\n")
            stripped = line.strip()

            if not stripped or stripped.startswith("#") or stripped.startswith("="):
                continue
            if stripped == "----":
                if current.get("case_id"):
                    cases.append(current)
                current = {}
                continue
            if ":" not in line:
                continue

            key, value = line.split(":", 1)
            current[key.strip()] = value.strip()

    if current.get("case_id"):
        cases.append(current)

    return cases


def classify_case_type(source: dict) -> str:
    state = source.get("state")
    service_hint = source.get("service_hint")
    note = source.get("note", "")
    raw = source.get("raw_message", "")

    if state == "purchased":
        return "after_purchase"
    if state == "closed":
        return "after_close"
    if service_hint == "handoff":
        return "handoff"
    if service_hint == "boundary":
        return "boundary"
    if "新規実装" in note or "作り方が分からない" in raw:
        return "boundary"
    if "service_mismatch_but_feasible" in note or "Stripeは使っていない" in raw:
        return "boundary"
    return "bugfix"


def detect_prequote_scenario(source: dict) -> str:
    raw = source.get("raw_message", "")
    note = source.get("note", "")
    combined = f"{raw}\n{note}"
    service_hint = source.get("service_hint")

    repair_primary_markers = [
        "直してほしい",
        "修正してほしい",
        "まず直したい",
        "不具合を直したい",
        "動かしたい",
    ]
    structure_unknown_markers = [
        "中身が全然わから",
        "何がどうなってるか知りたい",
        "どっちのサービスが合う",
        "自分でもうまく説明できない",
        "外注で作ってもらった",
        "AIで作ってもらった",
    ]

    if "不正アクセス" in combined:
        return "security_fear"
    if is_multi_symptom_case(source):
        return "multi_symptom"
    if any(marker in combined for marker in repair_primary_markers) and any(
        marker in combined for marker in structure_unknown_markers
    ):
        return "boundary_bugfix_first"
    if is_scope_confusion_case(source):
        if "直接会って" in combined or "Zoom" in combined:
            return "no_meeting_request"
        if "返金" in combined or "価値があるか" in combined or "5,000円で" in combined or "内容に差" in combined:
            return "service_value_uncertain"
        if "修正までやってもらえますか" in combined or "合計でいくら" in combined:
            return "followon_fix_question"
        return "service_selection_confusion"
    if service_hint == "handoff":
        return "service_value_uncertain"
    if "設定変更だけ" in combined or "もっと安く" in combined:
        return "price_discount_expectation"
    if "商品名が間違" in combined or "テストプラン" in combined:
        return "possible_setting_issue"
    if "表示速度が遅い" in combined or "サイト全体が重い" in combined:
        return "performance_boundary"
    return "default_bugfix"


def summarize_raw_message(raw: str) -> str:
    sentences = [part.strip(" 。！？") for part in re.split(r"[。！？]", raw) if part.strip(" 。！？")]
    generic_openers = {
        "はじめまして",
        "こんにちは",
        "こんにちは！",
        "お世話になります",
        "ご相談です",
        "相談です",
        "ご連絡しました",
        "メッセージ失礼します",
        "突然のメッセージ失礼します",
    }
    filtered = [s for s in sentences if s not in generic_openers]
    candidates = filtered or sentences
    keywords = ["Stripe", "Webhook", "webhook", "決済", "会員", "メール", "画面", "サブスク", "Checkout", "エラー", "404", "タイムアウト"]
    for sentence in candidates:
        if any(keyword in sentence for keyword in keywords):
            return sentence[:70].rstrip("、。") + ("..." if len(sentence) > 70 else "")
    if candidates:
        sentence = candidates[0]
        return sentence[:70].rstrip("、。") + ("..." if len(sentence) > 70 else "")
    return raw[:70].rstrip("、。") + ("..." if len(raw) > 70 else "")


def derive_summary(source: dict) -> str:
    if source.get("summary"):
        return source["summary"]
    raw = source.get("raw_message", "")
    if raw:
        return summarize_raw_message(raw)
    note = source.get("note", "")
    if note:
        for sep in ["。", "。", "。", "。", ".", "。", "。", "。", "。"]:
            if sep in note:
                first = note.split(sep, 1)[0].strip()
                if first:
                    return first
        return note
    raw = source.get("raw_message", "")
    if len(raw) > 60:
        return raw[:60].rstrip("、。") + "..."
    return raw


def detect_provided_context(source: dict) -> list[str]:
    raw = source.get("raw_message", "")
    note = source.get("note", "")
    combined = f"{raw}\n{note}"
    tags: list[str] = []

    if any(marker in combined for marker in ["エラー", "500", "決済", "購入履歴", "通らない", "表示されません", "画面", "Webhook", "checkout", "パスワード再発行"]):
        tags.append("symptom_detail")
    if any(marker in combined for marker in ["そのまま購入", "購入でよい", "購入でいい", "ご購入いただいて", "購入したい"]):
        tags.append("purchase_path_question")
    if any(marker in combined for marker in ["承諾はもう少し", "正式な承諾", "待ってもら", "承諾に進んで", "承諾は", "承諾を"]):
        tags.append("approval_status")
    if any(marker in combined for marker in ["返金", "追加料金", "15,000円", "15000円", "25,000円", "25000円", "5,000円", "5000円", "安く", "割引", "高い", "キャッシュバック"]):
        tags.append("price_or_refund")
    if any(marker in combined for marker in ["追記", "書き直し", "手順書", "メモ", "DB", "書き込み部分", "追加で"]):
        tags.append("doc_followup")
    if any(marker in combined for marker in ["次回", "またお願い", "また依頼", "リピーター", "お気に入り"]):
        tags.append("repeat_or_future")
    if any(marker in combined for marker in ["CSS", "保守", "月額", "デザイン"]):
        tags.append("out_of_scope_service")
    if any(marker in combined for marker in ["不安", "怖い", "放置", "話が違う", "納得いかない", "高かった"]):
        tags.append("anxiety_or_complaint")

    return list(dict.fromkeys(tags))


def extract_known_facts(source: dict) -> list[str]:
    facts: list[str] = []
    summary = derive_summary(source)
    if summary:
        facts.append(f"summary:{summary}")
    for tag in detect_provided_context(source):
        facts.append(f"context:{tag}")
    return facts[:8]


def build_routing_meta(source: dict, scenario: str) -> dict:
    is_generic = scenario.startswith("generic_")
    return {
        "scenario": scenario,
        "scenario_confidence": "low" if is_generic else "high",
        "is_generic_fallback": is_generic,
        "provided_context": detect_provided_context(source),
    }


def derive_primary_question(raw: str) -> str:
    if "15,000円" in raw and ("対応" in raw or "済みます" in raw or "見てもら" in raw):
        return "15,000円で対応できるか"
    if "料金感" in raw or "お見積り" in raw or "見積り" in raw or "いくら" in raw:
        return "料金と対応可否を知りたい"
    if "直せ" in raw or "対応" in raw or "見ていただけ" in raw or "見てもらえ" in raw or "可能でしょうか" in raw:
        return "対応できるか"
    return "この内容を見てもらえるか"


def infer_user_signal(source: dict) -> str:
    emotional_tone = source.get("emotional_tone")
    raw = source.get("raw_message", "")
    note = source.get("note", "")
    combined = f"{raw}\n{note}"

    if any(marker in combined for marker in ["高かった", "説明が足りなかった", "途中で状況を教えてもらえたら", "安心だったかな"]):
        return "negative_feedback"
    if any(
        marker in combined
        for marker in [
            "急ぎ",
            "至急",
            "お客さんから",
            "半日以上",
            "売上",
            "止まって",
            "前任",
            "連絡取れない",
            "連絡取れなく",
            "予算があまりなくて",
            "予算",
            "不安",
            "怖",
            "追加費用が怖",
            "辞めた",
            "辞めてしまって",
            "ブラックボックス",
            "壊れそう",
            "何も分からない",
        ]
    ):
        return "stress"
    if any(marker in combined for marker in ["すみません", "恐縮", "相談だけ", "初歩的な質問", "自分でもうまく説明できない", "気を遣って"]):
        return "hesitation"
    if any(
        marker in combined
        for marker in [
            "わからなくて",
            "判断つか",
            "どっちが",
            "全然わから",
            "正直どこが何をやってるかわから",
            "どのファイル",
            "どこを触ると",
            "技術用語ばかり",
            "全部見てもらうことはできますか",
            "どのコードを見ればいいか",
        ]
    ):
        return "confusion"
    if emotional_tone in {"anxious", "frustrated", "mixed", "price_sensitive", "hesitant"}:
        return "stress"
    return "neutral"


def build_temperature_plan(source: dict, *, case_type: str | None = None) -> dict:
    user_signal = infer_user_signal(source)
    resolved_case_type = case_type or source.get("case_type") or classify_case_type(source)
    scenario = source.get("scenario") or detect_prequote_scenario(source)
    boundary_like_scenarios = {
        "boundary_bugfix_first",
        "service_selection_confusion",
        "service_value_uncertain",
        "followon_fix_question",
        "no_meeting_request",
        "possible_setting_issue",
        "performance_boundary",
    }

    if resolved_case_type == "boundary" or scenario in boundary_like_scenarios:
        support_goal = "set_boundary_calmly"
        opening_move = "yes_no_first"
    elif user_signal == "stress":
        support_goal = "reduce_burden"
        opening_move = "action_first"
    elif user_signal == "hesitation":
        support_goal = "reduce_burden"
        opening_move = "pressure_release"
    elif user_signal == "confusion":
        support_goal = "normalize"
        opening_move = "normalize_then_clarify"
    elif user_signal == "negative_feedback":
        support_goal = "receive_feedback"
        opening_move = "receive_and_own"
    else:
        support_goal = "move_forward"
        opening_move = "neutral_ack"

    return {
        "user_signal": user_signal,
        "support_goal": support_goal,
        "opening_move": opening_move,
        "tone_constraints": [
            "no_defense",
            "no_internal_terms",
            "no_burden_shift",
            "no_negative_lead",
        ],
    }


def ensure_temperature_plan(case: dict) -> dict:
    existing = case.get("temperature_plan")
    if existing:
        return existing
    case["temperature_plan"] = build_temperature_plan(case, case_type=case.get("case_type"))
    return case["temperature_plan"]


def is_scope_confusion_case(source: dict) -> bool:
    raw = source.get("raw_message", "")
    note = source.get("note", "")
    combined = f"{raw}\n{note}"
    markers = [
        "どっちのサービス",
        "何を選んでいいか",
        "25,000円の方が安全",
        "修正含まない",
        "コードも分からない",
        "両方です",
        "返金",
        "直接会って",
        "Zoom",
        "価値があるか",
        "合計でいくら",
    ]
    if source.get("service_hint") in {"handoff", "boundary"} and any(marker in combined for marker in markers):
        return True
    return any(marker in combined for marker in markers)


def is_multi_symptom_case(source: dict) -> bool:
    raw = source.get("raw_message", "")
    note = source.get("note", "")
    combined = f"{raw}\n{note}"
    if any(marker in combined for marker in ["3つが同時", "いろいろ壊れて", "パニック寄り"]):
        return True
    if "両方です" in raw and "不具合" in raw and "コード" in raw:
        return True
    if all(marker in raw for marker in ["完了ページ", "メール", "管理画面"]):
        return True
    if numbered_marker_count(raw) >= 3 and any(marker in combined for marker in ["同時", "全部", "パニック"]):
        return True
    return False


def split_explicit_questions(raw: str) -> list[str]:
    text = compact_text(raw)
    candidates: list[str] = []

    numbered = re.findall(r"[①-⑨]\s*([^①-⑨]+?)(?=(?:[①-⑨]|$))", text)
    if numbered:
        candidates.extend(compact_text(item) for item in numbered if compact_text(item))

    if not candidates:
        q_segments = re.findall(r"([^。！？\n]*[?？])", text)
        candidates.extend(compact_text(item) for item in q_segments if compact_text(item))

    normalized: list[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        stripped = candidate.strip(" ?？")
        if not stripped:
            continue
        if stripped in seen:
            continue
        seen.add(stripped)
        normalized.append(stripped)

    return normalized


def classify_question_type(question_text: str) -> str:
    text = compact_text(question_text)
    if ".env" in text or "APIキー" in text:
        return "secret_sharing"
    if "スクショ" in text or ("画面" in text and any(marker in text for marker in ["送", "見せ", "撮"])):
        return "evidence_screenshot"
    if "手順書" in text or "どう直すか" in text or "自分で直す" in text:
        return "procedure_only"
    if "調べるだけ" in text:
        return "investigation_only"
    if "相談だけでも" in text or "まず相談だけ" in text:
        return "consultation_ok"
    if "返金" in text:
        return "refund_policy"
    if "直接会って" in text or "Zoom" in text or "ビデオ" in text or "通話" in text:
        return "meeting_request"
    if (
        "もっと安く" in text
        or "安くなりますか" in text
        or "値引" in text
        or "5,000円とか" in text
        or "10,000円で" in text
        or "5,000円くらい" in text
        or "お試し" in text
    ):
        return "price_discount"
    if "内容に差" in text or "価値があるか" in text or re.search(r"(^|[^0-9])5,000円", text):
        return "value_compare"
    if "税込" in text:
        return "price_tax"
    if (
        "25,000円" in text
        or "25000円" in text
        or "2万5千円" in text
        or "どっちのサービス" in text
        or "どっちを買" in text
        or "どっちを依頼" in text
        or "どっちですか" in text
        or "修正含まない" in text
        or "返金" in text
    ):
        return "service_selection"
    if ("15,000円" in text or "15000円" in text or "1万5千円" in text) and ("対応" in text or "済み" in text or "直り" in text):
        return "price_acceptance"
    if "料金感" in text or "いくら" in text or "見積り" in text:
        return "price_general"
    if "今週中" in text or "今日中" in text or "何日" in text or "いつ" in text:
        return "timeline"
    if "Stripeの問題" in text or "コードの問題" in text or "どっち" in text:
        return "cause_owner"
    if "不正アクセス" in text:
        return "security"
    if "影響ありますか" in text:
        return "impact"
    if "対応" in text or "見てもら" in text or "可能でしょうか" in text or "直せ" in text:
        return "can_handle"
    return "general"


def infer_explicit_questions(source: dict) -> list[dict]:
    raw = source.get("raw_message", "")
    extracted = split_explicit_questions(raw)
    if not extracted:
        extracted = [derive_primary_question(raw)]

    scenario = detect_prequote_scenario(source)
    if scenario == "service_value_uncertain" and not any(
        classify_question_type(question) in {"value_compare", "refund_policy"} for question in extracted
    ):
        if "返金" in raw:
            extracted.append("返金前提で考えなくてよいか")
        else:
            extracted.append("内容にどんな差があるか")

    needs_implicit_primary = True
    for question in extracted:
        qtype = classify_question_type(question)
        if qtype in {"price_acceptance", "price_general", "can_handle"}:
            needs_implicit_primary = False
            break

    if needs_implicit_primary and source.get("state", "prequote") == "prequote":
        extracted.insert(0, derive_primary_question(raw))

    primary_index = 0
    scored: list[tuple[int, str]] = []
    for idx, question in enumerate(extracted):
        qtype = classify_question_type(question)
        score = 0
        if qtype in {"price_acceptance", "can_handle", "price_general"}:
            score = 30
        elif qtype in {"security", "cause_owner", "timeline", "impact"}:
            score = 20
        elif qtype in {"secret_sharing", "evidence_screenshot"}:
            score = 10
        scored.append((score, qtype))
        if score > scored[primary_index][0]:
            primary_index = idx

    questions: list[dict] = []
    for idx, question in enumerate(extracted):
        questions.append(
            {
                "id": f"q{idx + 1}",
                "text": question,
                "priority": "primary" if idx == primary_index else "secondary",
                "question_type": scored[idx][1],
            }
        )
    return questions


def answer_brief_for_question(question_type: str, primary_now: bool) -> str:
    if question_type == "secret_sharing":
        return ".envやAPIキーの値は不要です。キー名だけで大丈夫です。"
    if question_type == "evidence_screenshot":
        return "エラー内容が分かる画面なら、スクショが1枚あると助かります。"
    if question_type == "procedure_only":
        return "手順書だけを別で作る形ではなく、15,000円で原因調査から修正まで対応しています。"
    if question_type == "investigation_only":
        return "はい、原因の調査からで大丈夫です。"
    if question_type == "consultation_ok":
        return "はい、まずは状況整理からで大丈夫です。"
    if question_type == "meeting_request":
        return "通話やZoomではなく、トークルームのテキストで進めています。"
    if question_type == "price_tax":
        return "金額はココナラ画面に表示される金額のままです。"
    if question_type == "price_discount":
        return "このケースでも15,000円です。"
    if question_type == "price_general":
        return "この内容なら15,000円の範囲で進められる見込みです。"
    if question_type == "can_handle":
        return "この不具合なら15,000円で進められます。"
    if question_type == "price_acceptance":
        return "この不具合なら15,000円で進められます。"
    if question_type == "service_selection":
        return "この不具合なら15,000円で進められます。"
    if primary_now:
        return "この不具合なら15,000円で進められます。"
    return "確認対象ではあるが、今の情報ではまだ断定しない。"


def secondary_after_check_reason(question_type: str) -> tuple[str, str]:
    if question_type == "timeline":
        return (
            "納期はコードとエラー内容を見てからの方が正確です。",
            "必要情報を受領したあとに、見通しをお返しします。",
        )
    if question_type == "cause_owner":
        return (
            "Stripe側かコード側かは、今の時点ではまだ断定しません。",
            "必要情報を受領したあとに、切り分けの見立てをお返しします。",
        )
    if question_type == "security":
        return (
            "不正アクセスかどうかは、今の時点ではまだ断定しません。",
            "必要情報を受領したあとに、まず確認すべき範囲をお返しします。",
        )
    if question_type == "impact":
        return (
            "影響範囲は、今の時点ではまだ断定しません。",
            "必要情報を受領したあとに、優先して見る範囲をお返しします。",
        )
    if question_type == "service_selection":
        return (
            "いまの段階で、どちらから入るかまではまだ断定しません。",
            "必要情報を受領したあとに、今の内容で案内できる範囲をお返しします。",
        )
    if question_type == "value_compare":
        return (
            "他の方との比較は、内容差を確認してからの方が安全です。",
            "必要情報を受領したあとに、いま案内できる範囲をお返しします。",
        )
    if question_type == "refund_policy":
        return (
            "返金だけを先に断定するより、まず原因の切り分けと修正できるかの確認から進めます。",
            "確認できたところまでと、次にどう進めるかをお返しします。",
        )
    return (
        "この点は、今の情報だけではまだ断定しません。",
        "必要情報を受領したあとに、確認結果をお返しします。",
    )


def primary_hold_brief_for(source: dict) -> str:
    scenario = detect_prequote_scenario(source)
    if scenario == "boundary_bugfix_first":
        return "まず直したいところを起点に見るのが近いですが、今の情報だけでどちらから入るかまではまだ断定しません。"
    if scenario in {"service_selection_confusion", "service_value_uncertain", "followon_fix_question", "no_meeting_request"}:
        return "確認対象ではありますが、今の内容でそのまま進められるかはまだ断定しません。"
    if scenario == "possible_setting_issue":
        return "設定側で切り分けられる可能性もあるため、いまは15,000円で進める前に確認したいです。"
    if scenario == "performance_boundary":
        return "表示速度の問題はStripe起因とは限らないため、いまは15,000円で進める前に確認したいです。"
    if scenario == "security_fear":
        return "確認対象ではありますが、いまは通常のbugfixとして進められるかをまだ断定しません。"
    return "確認対象ではあるが、今の情報では15,000円の範囲で進められるかをまだ断定しない。"


def derive_disposition(source: dict) -> str:
    raw = source.get("raw_message", "")
    note = source.get("note", "")
    combined = f"{raw}\n{note}"
    scenario = detect_prequote_scenario(source)

    hold_markers = [
        "情報がほぼない",
        "情報は少なめ",
        "情報が少ない",
        "情報不足",
        "hold判定",
        "hold",
        "保留",
        "ざっくり相談",
        "相談だけ",
        "判定が必要",
        "境界",
        "技術理解が浅い",
        "一切不明",
        "セキュリティ調査寄り",
        "不正アクセス",
        "怖くて触れない",
    ]
    now_markers = [
        "15K判定しやすい",
        "15K案件",
        "典型的な高適合",
        "高適合",
        "情報量が多い",
        "情報は十分",
        "典型パターン",
    ]

    if scenario in {
        "boundary_bugfix_first",
        "service_selection_confusion",
        "service_value_uncertain",
        "followon_fix_question",
        "no_meeting_request",
        "possible_setting_issue",
        "performance_boundary",
        "security_fear",
    }:
        return "answer_after_check"
    if scenario == "multi_symptom":
        return "answer_after_check"
    if len(strip_period(raw)) <= 20:
        return "answer_after_check"
    if any(marker in combined for marker in hold_markers):
        return "answer_after_check"
    if any(marker in combined for marker in now_markers):
        return "answer_now"
    if "Stripeは使っていない" in raw or "Stripeは使っていない" in note:
        return "answer_after_check"
    if "ちょっと調子が悪い" in raw:
        return "answer_after_check"
    return "answer_now"


def derive_ask(source: dict) -> tuple[str, str, str | None, str | None]:
    raw = source.get("raw_message", "")
    note = source.get("note", "")
    combined = f"{raw}\n{note}"
    scenario = detect_prequote_scenario(source)

    if scenario == "multi_symptom":
        return (
            "もし優先して止めたい画面か症状があれば、そこを教えてください。",
            "最初に切る対象を1件に絞って、どこから入るかを判断するため",
            None,
            "優先がなければ、決済や反映に近い症状から先に見立てます。",
        )
    if scenario == "boundary_bugfix_first":
        return (
            "もし一番直したいところが決まっていれば、そこを教えてください。",
            "修正を起点に見ながら、先に整理が必要な範囲もこちらで切るため",
            None,
            "まだ絞れていなければ、いま一番困っている動きからで大丈夫です。",
        )
    if scenario in {"service_selection_confusion", "service_value_uncertain", "followon_fix_question"}:
        if scenario == "service_value_uncertain":
            return (
                "もし具体的な症状が決まっていれば、教えてください。",
                "まず何が起きているかを確認するため",
                None,
                "まだ整理できていなければ、分かる範囲で大丈夫です。",
            )
        return (
            "もし一番困っている点が決まっていれば、そこを教えてください。",
            "今の内容で案内できる範囲を先に切るため",
            None,
            "決まっていなければ、影響が大きそうなところから先に見立てます。",
        )
    if scenario == "no_meeting_request":
        return (
            "テキストでのやり取りで問題なさそうかだけ、分かる範囲で教えてください。",
            "通話なしで進められるかを先に確認するため",
            None,
            "問題なければ、このままテキスト前提で見立てを進めます。",
        )
    if scenario == "possible_setting_issue":
        return (
            "その表示が出ている画面のスクショがあれば、1枚送ってください。",
            "コード側か設定側かを先に切り分けるため",
            "screenshot",
            "スクショが難しければ、表示されている文言だけでも大丈夫です。",
        )
    if scenario == "performance_boundary":
        return (
            "もし特に遅い画面が決まっていれば、そこを教えてください。",
            "今回の内容で見られる範囲かを先に切るため",
            None,
            "決まっていなければ、決済に近い画面から先に見立てます。",
        )
    if "スクショ" in combined or "画面が真っ白" in combined or "画面" in raw:
        return (
            "いま困っている画面のスクショがあれば、1枚送ってください。",
            "どの画面で止まっているかを切り分けるため",
            "screenshot",
            "スクショが難しければ、画面名だけでも大丈夫です。",
        )
    if "Stripeは使っていない" in combined:
        return (
            "いちばん困っている症状と、それが本番かテストかが分かれば教えてください。",
            "今の内容で見られる範囲かを先に切るため",
            None,
            "まだ決まっていなければ、いま困り方が大きい症状から見立てます。",
        )
    if "Webhook" in raw or "webhook" in raw:
        return (
            "エラーが見えている画面かメッセージがあれば、1つ送ってください。",
            "Webhookの受信前後のどこで止まっているかを切り分けるため",
            "screenshot_or_text",
            "すぐ出せなければ、まずはWebhookまわりから見立てます。",
        )
    return (
        "いま起きている症状と、それが本番かテストかが分かれば教えてください。",
        "15,000円の範囲で進められるかを先に切るため",
        None,
        "まだ絞れていなければ、いちばん影響が大きそうな症状から見立てます。",
    )


def build_case_from_source(source: dict) -> dict:
    state = source.get("state", "prequote")
    raw = source.get("raw_message", "")
    disposition = derive_disposition(source)
    summary = derive_summary(source)
    src = source.get("route", source.get("src", "service"))
    scenario = detect_prequote_scenario(source)
    explicit_questions = infer_explicit_questions(source)
    primary_question = next(item for item in explicit_questions if item["priority"] == "primary")
    service_fit = "high"
    if "Stripeは使っていない" in raw:
        service_fit = "service_mismatch_but_feasible"
    elif "service_mismatch_but_feasible" in source.get("note", ""):
        service_fit = "service_mismatch_but_feasible"

    case: dict = {
        "id": source.get("case_id") or source.get("id"),
        "title": source.get("category") or source.get("title") or source.get("case_id") or "generated",
        "service_id": "bugfix-15000",
        "src": src,
        "state": state,
        "raw_message": raw,
        "user_intent": "対応可否の確認",
        "case_type": classify_case_type(source),
        "certainty": "low" if disposition == "answer_after_check" else "high",
        "service_fit": service_fit,
        "risk_level": "medium" if source.get("emotional_tone") in {"anxious", "mixed", "frustrated"} else "low",
        "risk_flags": [],
        "scope_judgement": "undecidable" if disposition == "answer_after_check" else "same_cause_likely",
        "summary": summary,
        "known_facts": extract_known_facts(source),
        "routing_meta": build_routing_meta(source, scenario),
        "emotional_caution": source.get("emotional_tone") in {"anxious", "mixed", "frustrated"},
        "ask_count": 0,
        "missing_info": [],
        "next_action": "見積り初回のため、estimate_initial renderer で返信する",
        "human_review_required": False,
        "reply_generation": "ready_to_draft",
        "scenario": scenario,
        "reply_stance": {
            "burden_owner": "us",
            "empathy_first": source.get("emotional_tone") in {"anxious", "mixed", "frustrated"},
            "reply_skeleton": "estimate_initial",
            "answer_timing": "after_check" if disposition == "answer_after_check" else "now",
        },
        "temperature_plan": build_temperature_plan(source, case_type=classify_case_type(source)),
    }

    answer_map = []
    ask_map = []
    issue_plan = [
        {
            "issue": "主質問への返答",
            "disposition": disposition,
            "reason": "直下テストケースからの自動推定",
        }
    ]
    required_moves = ["answer_directly_now", "give_purchase_path"]

    primary_answer_item = {
        "question_id": primary_question["id"],
        "disposition": disposition,
        "answer_brief": (
            answer_brief_for_question(primary_question["question_type"], primary_now=True)
            if disposition == "answer_now"
            else primary_hold_brief_for(source)
        ),
        "evidence_refs": ["raw_message", "note"],
        "question_type": primary_question["question_type"],
    }
    answer_map.append(primary_answer_item)

    if disposition == "answer_after_check":
        ask_text, why_needed, evidence_kind, default_path_text = derive_ask(source)
        primary_answer_item["hold_reason"] = "情報がまだ足りず、いま案内してよい範囲を断定しにくい。"
        if scenario in {"boundary_bugfix_first", "service_selection_confusion", "service_value_uncertain", "followon_fix_question", "no_meeting_request"}:
            primary_answer_item["revisit_trigger"] = "追加情報を受領したあとに、今の内容で案内できる範囲をお返しします。"
        else:
            primary_answer_item["revisit_trigger"] = "追加情報を受領したあとに、進められるかをお返しします。"
        ask_entry = {
            "id": "a1",
            "question_ids": [primary_question["id"]],
            "ask_text": ask_text,
            "why_needed": why_needed,
        }
        if evidence_kind:
            ask_entry["evidence_kind"] = evidence_kind
        if default_path_text:
            ask_entry["default_path_text"] = default_path_text
        ask_map.append(ask_entry)
        case["ask_count"] = 1
        case["missing_info"] = [why_needed]
        required_moves = ["defer_with_reason", "request_minimum_evidence"]
        issue_plan.append(
            {
                "issue": "最小証跡の取得",
                "disposition": "ask_client",
                "depends_on": [primary_question["id"]],
            }
        )

    for question in explicit_questions:
        if question["id"] == primary_question["id"]:
            continue
        qtype = question["question_type"]
        if qtype in {
            "secret_sharing",
            "evidence_screenshot",
            "consultation_ok",
            "meeting_request",
            "price_tax",
            "price_discount",
            "procedure_only",
            "investigation_only",
        }:
            secondary_disposition = "answer_now"
            brief = answer_brief_for_question(qtype, primary_now=(disposition == "answer_now"))
            answer_map.append(
                {
                    "question_id": question["id"],
                    "disposition": secondary_disposition,
                    "answer_brief": brief,
                    "evidence_refs": ["raw_message"],
                    "question_type": qtype,
                }
            )
            issue_plan.append(
                {
                    "issue": question["text"],
                    "disposition": secondary_disposition,
                    "reason": "明示質問に即答できる項目のため",
                }
            )
            continue

        if qtype == "service_selection" and disposition == "answer_now":
            secondary_disposition = "answer_now"
            brief = answer_brief_for_question(qtype, primary_now=True)
            answer_map.append(
                {
                    "question_id": question["id"],
                    "disposition": secondary_disposition,
                    "answer_brief": brief,
                    "evidence_refs": ["raw_message"],
                    "question_type": qtype,
                }
            )
            issue_plan.append(
                {
                    "issue": question["text"],
                    "disposition": secondary_disposition,
                    "reason": "公開中の bugfix で案内できる入口が明確なため",
                }
            )
            continue

        if qtype in {"timeline", "cause_owner", "security", "impact", "service_selection", "value_compare", "refund_policy"}:
            hold_reason, revisit_trigger = secondary_after_check_reason(qtype)
            answer_map.append(
                {
                    "question_id": question["id"],
                    "disposition": "answer_after_check",
                    "answer_brief": hold_reason,
                    "hold_reason": hold_reason,
                    "revisit_trigger": revisit_trigger,
                    "evidence_refs": ["raw_message"],
                    "question_type": qtype,
                }
            )
            issue_plan.append(
                {
                    "issue": question["text"],
                    "disposition": "answer_after_check",
                    "reason": "見積り初回では断定せず、確認後に返す方が安全なため",
                }
            )
            continue

        if disposition == "answer_now":
            secondary_disposition = "answer_now"
            brief = answer_brief_for_question(qtype, primary_now=True)
        else:
            secondary_disposition = "answer_after_check"
            hold_reason, revisit_trigger = secondary_after_check_reason(qtype)
            brief = hold_reason

        item = {
            "question_id": question["id"],
            "disposition": secondary_disposition,
            "answer_brief": brief,
            "evidence_refs": ["raw_message"],
            "question_type": qtype,
        }
        if secondary_disposition == "answer_after_check":
            item["hold_reason"] = hold_reason
            item["revisit_trigger"] = revisit_trigger
        answer_map.append(item)
        issue_plan.append(
            {
                "issue": question["text"],
                "disposition": secondary_disposition,
                "reason": "直下テストケースからの自動推定",
            }
        )

    case["reply_contract"] = {
        "primary_question_id": primary_question["id"],
        "explicit_questions": [
            {
                "id": item["id"],
                "text": item["text"],
                "priority": item["priority"],
            }
            for item in explicit_questions
        ],
        "answer_map": [
            {k: v for k, v in item.items() if k != "question_type"}
            for item in answer_map
        ],
        "ask_map": ask_map,
        "issue_plan": issue_plan,
        "required_moves": required_moves,
        "forbidden_moves": [
            "vague_hold_without_reason",
            "internal_term_exposure",
            "numbered_QA_for_all_questions",
        ],
    }
    return case


def opener_for(case: dict) -> str:
    src = case.get("src")
    if src == "profile":
        return "プロフィールをご覧いただきありがとうございます。"
    if src == "message":
        return "メッセージありがとうございます。"
    return "ご相談ありがとうございます。"


def acknowledge_for(case: dict) -> str:
    temperature_plan = ensure_temperature_plan(case)
    summary = case.get("summary")
    user_signal = temperature_plan.get("user_signal")
    opening_move = temperature_plan.get("opening_move")

    if opening_move == "action_first":
        return "まず必要なところから確認します。"
    if opening_move == "pressure_release":
        return "相談だけでも大丈夫です。"
    if opening_move == "normalize_then_clarify":
        return "いまの段階で迷うのは自然です。まず状況を確認します。"
    if opening_move == "receive_and_own":
        return "率直に書いていただいてありがとうございます。"
    if opening_move == "yes_no_first":
        if user_signal == "negative_feedback":
            return "率直に書いていただいてありがとうございます。"
        if user_signal == "stress":
            return "まず状況を確認します。"
        if user_signal == "confusion":
            return "いまの段階で迷うのは自然です。まず状況を確認します。"
        if user_signal == "hesitation":
            return "先に結論からお返しします。"
        return ""
    if not summary:
        return "内容ありがとうございます。"
    if "進め方" in summary:
        return "ご相談の内容、分かりました。"
    return f"{strip_period(summary)}とのことでした。"


def primary_question(case: dict) -> tuple[dict, dict]:
    contract = case["reply_contract"]
    primary_id = contract["primary_question_id"]
    questions = {item["id"]: item for item in contract["explicit_questions"]}
    answers = {item["question_id"]: item for item in contract["answer_map"]}
    return questions[primary_id], answers[primary_id]


def secondary_answer_items(case: dict) -> list[tuple[dict, dict]]:
    contract = case["reply_contract"]
    primary_id = contract["primary_question_id"]
    questions = {item["id"]: item for item in contract["explicit_questions"]}
    items = []
    for answer in contract.get("answer_map") or []:
        qid = answer["question_id"]
        if qid == primary_id:
            continue
        question = questions.get(qid)
        if question:
            items.append((question, answer))
    return items


def promoted_answer_now_lines(case: dict) -> list[str] | None:
    for question, answer in secondary_answer_items(case):
        qtype = answer.get("question_type") or question.get("question_type")
        if qtype == "procedure_only":
            return [
                "手順書だけを別で作る形ではなく、15,000円で原因調査から修正まで対応しています。",
                "調査で分かった原因と修正内容は、分かる形でお渡しできます。",
            ]
        if qtype == "investigation_only":
            return [
                "調べるだけでも大丈夫です。",
                "原因の調査から対応するので、直し方が分からない状態でも問題ありません。",
            ]
        if qtype in {"service_selection", "price_acceptance"}:
            return ["この不具合なら15,000円で進められます。"]
    return None


def answer_now_lines(case: dict, question: dict, answer: dict) -> list[str]:
    question_text = question.get("text", "")
    question_type = answer.get("question_type") or question.get("question_type")
    brief = answer.get("answer_brief", "")
    lines: list[str] = []

    if "切り分け" in question_text or "切り分け" in brief:
        lines.append("切り分けと修正可否の確認を含めて、15,000円で進められます。")
        return lines

    if question_type in {"can_handle", "price_acceptance", "service_selection"}:
        lines.append("この不具合なら15,000円で進められます。")
        return lines

    if "15,000円" in brief:
        lines.append(brief)
        return lines

    if brief:
        lines.append(brief)
    else:
        lines.append("この内容なら対応できます。")
    return lines


def scope_reason_for(case: dict) -> str:
    summary = case.get("summary", "")
    raw = case.get("raw_message", "")
    if "会員状態" in summary or "無料へ戻って" in summary:
        return "まずは会員状態の反映まわりを、1件の不具合として確認します。"
    if "Firestore" in summary or "timeout" in summary:
        return "まずは Firestore 反映までの流れを確認して、timeout が出る箇所を切り分けます。"
    if "購入完了メール" in raw or "注文完了メール" in raw:
        return "まずは決済後のメール送信と反映処理のどちらで止まっているかを確認します。"
    if "メール" in summary:
        return "まずは解約イベントを受けたあとのメール送信まわりを、1件の不具合として確認します。"
    if "404" in summary or "完了ページ" in summary:
        return "まずは決済完了後の遷移先まわりを、1件の不具合として確認します。"
    return "まずはこの不具合がどこで止まっているかを確認します。"


def next_action_now_for(case: dict) -> str:
    src = case.get("src")
    if src == "service":
        return "この内容で進める場合は、そのままご購入いただいて大丈夫です。必要情報がそろい次第、一次結果は48時間以内を目安にお返しします。"
    if src in {"profile", "message"}:
        return "進める場合は、この内容でご提案します。必要情報がそろい次第、一次結果は48時間以内を目安にお返しします。"
    return "必要情報がそろい次第、一次結果は48時間以内を目安にお返しします。"


def secondary_lines(case: dict) -> list[str]:
    lines: list[str] = []
    for question, answer in secondary_answer_items(case):
        disposition = answer.get("disposition")
        qtext = question.get("text", "")
        qtype = answer.get("question_type") or question.get("question_type")
        brief = answer.get("answer_brief", "")
        if disposition == "answer_now":
            if qtype == "procedure_only":
                lines.append("手順書だけを別で作る形ではなく、15,000円で原因調査から修正まで対応しています。")
                lines.append("調査で分かった原因と修正内容は、分かる形でお渡しできます。")
            elif qtype == "investigation_only":
                lines.append("調べるだけでも大丈夫です。")
                lines.append("原因の調査から対応するので、直し方が分からない状態でも問題ありません。")
            elif qtype == "service_selection":
                lines.append("この不具合なら15,000円で進められます。")
            else:
                lines.append(brief)
        elif disposition == "answer_after_check":
            if qtype == "refund_policy":
                lines.append("原因の切り分けと、修正できるかの確認は基本料金の中で進めます。")
                lines.append("修正できない状態のまま正式納品へ進めることはありません。")
            if "cause_owner" in qtext or "Stripeの問題" in qtext or "コードの問題" in qtext:
                lines.append("Stripe側かコード側かは、今の時点ではまだ断定しません。")
            elif "今週中" in qtext or "今日中" in qtext or "何日" in qtext or "いつ" in qtext:
                lines.append("納期はコードとエラー内容を見てからの方が正確です。")
            elif "不正アクセス" in qtext:
                lines.append("不正アクセスかどうかは、今の時点ではまだ断定しません。")
            elif brief and qtype != "refund_policy":
                lines.append(brief)
    deduped: list[str] = []
    seen: set[str] = set()
    for line in lines:
        cleaned = compact_text(line)
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            deduped.append(cleaned if cleaned.endswith("。") else f"{cleaned}。")
    return deduped


def answer_after_check_lines(case: dict, answer: dict) -> list[str]:
    ask_map = case["reply_contract"].get("ask_map") or []
    ask = ask_map[0] if ask_map else {}
    lines: list[str] = []
    scenario = case.get("scenario")

    hold_reason = answer.get("hold_reason", "")
    if scenario == "boundary_bugfix_first":
        lines.append("この場合は、まず直したいところを起点に見ていくのが合っています。")
        lines.append("その中で、修正に入る前にどこを整理した方がよいかはこちらで見ながら進めます。")
    if scenario in {"service_selection_confusion", "service_value_uncertain", "followon_fix_question", "no_meeting_request"}:
        lines.append("この内容も確認できますが、いまの情報だけでどちらから入るかまではまだ断定しにくいです。")
    elif scenario == "possible_setting_issue":
        lines.append("この内容も確認できますが、いまはコード側の不具合か設定側かを先に切り分けたいです。")
    elif scenario == "performance_boundary":
        lines.append("この内容も確認できますが、いまは今回の内容で見られる範囲かを先に確認したいです。")
    elif hold_reason:
        lines.append("この内容も確認できますが、いまの情報だとまだ15,000円の範囲で切れるかを断定しにくいです。")
    else:
        lines.append("この内容も確認できますが、いまの情報だとまだ範囲を断定しにくいです。")

    if ask.get("ask_text"):
        lines.append(ask["ask_text"])
    if ask.get("default_path_text"):
        lines.append(ask["default_path_text"])
    if ask.get("why_needed"):
        why_needed = strip_period(ask["why_needed"])
        if why_needed.endswith("ため"):
            lines.append(f"{why_needed}です。")
        else:
            lines.append(f"{why_needed}ためです。")
    return lines


def next_action_after_check(case: dict, answer: dict) -> str:
    scenario = case.get("scenario")
    revisit_trigger = answer.get("revisit_trigger")
    if revisit_trigger:
        revisit_text = strip_period(revisit_trigger)
        replacements = {
            "範囲判定を返す": "範囲判定をお返しします",
            "進められるかを返す": "進められるかをお返しします",
            "返す": "お返しします",
        }
        for old, new in replacements.items():
            if revisit_text.endswith(old):
                revisit_text = revisit_text[: -len(old)] + new
                break
        return f"{revisit_text}。"
    if scenario in {"boundary_bugfix_first", "service_selection_confusion", "service_value_uncertain", "followon_fix_question", "no_meeting_request"}:
        return "確認できしだい、今の相談に合う案内をお返しします。"
    return "確認できしだい、この内容で進められるかをお返しします。"


def answer_after_check_slot_parts(case: dict, answer: dict) -> tuple[list[str], str, list[str]]:
    ask_map = case["reply_contract"].get("ask_map") or []
    ask = ask_map[0] if ask_map else {}
    bridge_to_hold: list[str] = []
    bridge_to_ask: list[str] = []
    scenario = case.get("scenario")

    if scenario == "boundary_bugfix_first":
        bridge_to_hold.append("この場合は、まず直したいところを起点に見ていくのが合っています。")
        bridge_to_hold.append("その中で、修正に入る前にどこを整理した方がよいかはこちらで見ながら進めます。")
    if scenario == "service_selection_confusion":
        bridge_to_hold.append("いまの情報だけで入口を決め切るより、まず困っている点から見た方がずれにくいです。")
    elif scenario == "service_value_uncertain":
        bridge_to_hold.append("原因が分からない状態で相談いただいて大丈夫です。")
    elif scenario == "followon_fix_question":
        bridge_to_hold.append("いまの情報だけで合計の進め方まで決めるより、先に困っている点から見た方がずれにくいです。")
    elif scenario == "no_meeting_request":
        bridge_to_hold.append("通話なしで進められるかは、先に必要な情報だけそろえば判断できます。")
    elif scenario == "possible_setting_issue":
        bridge_to_hold.append("いまはコード側の不具合か設定側かを先に見分けたいです。")
    elif scenario == "performance_boundary":
        bridge_to_hold.append("いまは今回の内容で見られる範囲かを先に確認したいです。")
    elif answer.get("hold_reason"):
        bridge_to_hold.append("いまの情報だと、まだ15,000円の範囲で見られるかを言い切りにくいです。")
    else:
        bridge_to_hold.append("いまの情報だと、まだ範囲を断定しにくいです。")

    ask_core = ask.get("ask_text", "")
    if ask.get("default_path_text"):
        bridge_to_ask.append(ask["default_path_text"])
    if ask.get("why_needed"):
        why_needed = strip_period(ask["why_needed"])
        bridge_to_ask.append(f"{why_needed}です。" if why_needed.endswith("ため") else f"{why_needed}ためです。")
    return bridge_to_hold, ask_core, bridge_to_ask


def compose_render_payload(payload: dict, *, use_fallback_editable: bool = False) -> str:
    editable_key = "fallback_editable_slots" if use_fallback_editable else "editable_slots"
    editable_slots = payload.get(editable_key) or {}
    fixed_slots = payload.get("fixed_slots") or {}
    sections: list[str] = []
    for slot_name in payload.get("slot_manifest") or []:
        text = editable_slots.get(slot_name) or fixed_slots.get(slot_name) or ""
        cleaned = compact_text(text) if "\n" not in text else "\n".join(line.rstrip() for line in text.splitlines() if line.strip())
        if cleaned:
            sections.append(cleaned)
    return "\n\n".join(sections)


def validate_render_payload(case: dict, payload: dict, rendered: str) -> list[str]:
    temperature_plan = ensure_temperature_plan(case)
    editable_slots = payload.get("editable_slots") or {}
    errors = collect_temperature_constraint_errors(rendered, temperature_plan, editable_slots)

    answer_core = (payload.get("fixed_slots") or {}).get("answer_core", "")
    if temperature_plan.get("opening_move") == "yes_no_first":
        if not any(
            answer_core.startswith(prefix)
            for prefix in (
                "この内容なら",
                "この不具合なら",
                "この時点では",
                "この場合は",
                "今の内容なら",
                "今の段階では",
                "原因が分からない状態でも",
                "調べるだけでも",
                "手順書だけを別で作る形ではなく",
                "はい",
                "いいえ",
            )
        ):
            errors.append("yes_no_first opening has no direct yes/no-or-judgment core")

    if case["reply_contract"].get("ask_map") and not (payload.get("fixed_slots") or {}).get("ask_core"):
        errors.append("ask_map exists but ask_core is empty")
    return list(dict.fromkeys(errors))


def build_estimate_render_payload(case: dict) -> dict:
    question, answer = primary_question(case)
    disposition = answer.get("disposition")
    ensure_temperature_plan(case)

    fixed_slots: dict[str, str] = {}
    editable_slots: dict[str, str] = {
        "ack": "\n".join([opener_for(case), acknowledge_for(case)]),
        "bridge_to_hold": "",
        "bridge_to_ask": "",
        "closing": "",
    }

    if disposition == "answer_now":
        promoted_lines = promoted_answer_now_lines(case)
        fixed_slots["answer_core"] = "\n".join(promoted_lines or answer_now_lines(case, question, answer))
        secondary = secondary_lines(case)
        if secondary:
            answer_core_lines = {compact_text(line) for line in fixed_slots["answer_core"].splitlines() if compact_text(line)}
            secondary = [line for line in secondary if compact_text(line) not in answer_core_lines]
        if secondary:
            fixed_slots["secondary_core"] = "\n".join(secondary)
        fixed_slots["scope_core"] = scope_reason_for(case)
        fixed_slots["next_action"] = next_action_now_for(case)
        slot_manifest = ["ack", "answer_core", "secondary_core", "scope_core", "next_action"]
    elif disposition == "answer_after_check":
        bridge_to_hold, ask_core, bridge_to_ask = answer_after_check_slot_parts(case, answer)
        if bridge_to_hold:
            editable_slots["bridge_to_hold"] = "\n".join(bridge_to_hold)
        scenario = case.get("scenario")
        if (ensure_temperature_plan(case).get("opening_move") or "") == "yes_no_first":
            if scenario == "boundary_bugfix_first":
                fixed_slots["answer_core"] = "今の内容なら、まず直したいところから見るのが近いです。"
            elif scenario in {"service_selection_confusion", "followon_fix_question"}:
                fixed_slots["answer_core"] = "今の内容なら、まず困っている点から見ていくのが近いです。"
            elif scenario == "service_value_uncertain":
                fixed_slots["answer_core"] = "原因が分からない状態でも、この入口から見ていけます。"
            elif scenario == "no_meeting_request":
                fixed_slots["answer_core"] = "この場合は、通話なしでもまずはテキストだけで見立てできます。"
            elif scenario == "possible_setting_issue":
                fixed_slots["answer_core"] = "この時点では、まずコード側か設定側かを見てから判断します。"
            elif scenario == "performance_boundary":
                fixed_slots["answer_core"] = "この時点では、まず遅くなっている画面を見てから判断します。"
            else:
                fixed_slots["answer_core"] = "この時点では、まず必要な情報を見てから判断します。"
        else:
            fixed_slots["answer_core"] = answer.get("hold_reason", "")
        if ask_core:
            fixed_slots["ask_core"] = ask_core
        if bridge_to_ask:
            editable_slots["bridge_to_ask"] = "\n".join(bridge_to_ask)
        secondary = secondary_lines(case)
        if secondary:
            fixed_slots["secondary_core"] = "\n".join(secondary)
        fixed_slots["next_action"] = next_action_after_check(case, answer)
        slot_manifest = ["ack", "bridge_to_hold", "answer_core", "ask_core", "bridge_to_ask", "secondary_core", "next_action"]
    else:
        raise ValueError(f"{case.get('id')}: unsupported primary disposition {disposition}")

    return {
        "fixed_slots": fixed_slots,
        "editable_slots": editable_slots,
        "fallback_editable_slots": dict(editable_slots),
        "slot_manifest": slot_manifest,
    }


def render_case(case: dict) -> str:
    if case.get("state") != "prequote":
        raise ValueError(f"{case.get('id')}: only prequote is supported")
    reply_stance = case.get("reply_stance") or {}
    if reply_stance.get("reply_skeleton") != "estimate_initial":
        raise ValueError(f"{case.get('id')}: only estimate_initial is supported")

    payload = build_estimate_render_payload(case)
    case["render_payload"] = payload
    rendered = compose_render_payload(payload)
    violations = validate_render_payload(case, payload, rendered)
    if violations:
        case["render_payload_violations"] = violations
        fallback = compose_render_payload(payload, use_fallback_editable=True)
        case["rendered_reply_validator_mode"] = "fallback_fixed"
        return fallback
    case["rendered_reply_validator_mode"] = "pass"
    return rendered


def load_cases(path: Path) -> list[dict]:
    if path.suffix in {".yaml", ".yml"}:
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return data.get("cases") or []
    if path.suffix == ".txt":
        return parse_text_case_file(path)
    raise ValueError(f"unsupported fixture format: {path}")


def save_reply(reply: str, source: str) -> None:
    cmd = [
        str(REPLY_SAVE),
        "--text",
        reply,
        "--source-text",
        source,
    ]
    subprocess.run(cmd, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Render estimate_initial replies from reply_contract v2 fixtures.")
    parser.add_argument("--fixture", default=str(DEFAULT_FIXTURE))
    parser.add_argument("--case-id", help="Render one case only")
    parser.add_argument("--state", default="prequote", help="Filter state when using flat test case files")
    parser.add_argument("--limit", type=int, help="Limit rendered cases")
    parser.add_argument("--save", action="store_true", help="Save rendered reply to runtime/replies/latest.txt")
    args = parser.parse_args()

    fixture = Path(args.fixture)
    cases = load_cases(fixture)
    if not cases:
        print(f"[NG] no cases found: {fixture}", file=sys.stderr)
        return 1

    selected = cases
    if args.state:
        selected = [case for case in selected if case.get("state") == args.state]
    if args.case_id:
        selected = [case for case in cases if case.get("id") == args.case_id]
        if not selected:
            selected = [case for case in cases if case.get("case_id") == args.case_id]
        if not selected:
            print(f"[NG] case not found: {args.case_id}", file=sys.stderr)
            return 1
    if args.limit is not None:
        selected = selected[: args.limit]

    rendered_blocks = []
    for case in selected:
        normalized_case = case if case.get("reply_contract") else build_case_from_source(case)
        if normalized_case.get("state") != "prequote":
            continue
        if normalized_case.get("reply_stance", {}).get("reply_skeleton") != "estimate_initial":
            continue
        rendered = render_case(normalized_case)
        rendered_blocks.append(f"case_id: {normalized_case['id']}\n{rendered}")
        if args.save:
            if len(selected) != 1:
                print("[NG] --save requires exactly one case", file=sys.stderr)
                return 1
            save_reply(rendered, normalized_case.get("raw_message", ""))

    if not rendered_blocks:
        print("[NG] no renderable cases after filtering", file=sys.stderr)
        return 1
    print("\n\n----\n\n".join(rendered_blocks))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
