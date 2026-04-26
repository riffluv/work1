#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

import yaml

from reply_quality_lint_common import collect_temperature_constraint_errors


ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_FIXTURE = ROOT_DIR / "ops/tests/prequote-contract-v2-top5.yaml"
REPLY_SAVE = ROOT_DIR / "scripts/reply-save.sh"
REPLIES_DIR = ROOT_DIR / "runtime/replies"
REPLY_MEMORY_PATH = REPLIES_DIR / "latest-memory.json"
ACTIVE_CASE_PATH = ROOT_DIR / "runtime/active-case.txt"
OPEN_CASES_DIR = ROOT_DIR / "ops/cases/open"

REPLY_MEMORY_DEFAULT = {
    "followup_count": 0,
    "prior_tone": "neutral",
    "previous_assistant_commitment": "none",
    "previous_deadline_promised": None,
    "commitment_fulfilled": True,
}
ALLOWED_REPLY_MEMORY_TONES = {"neutral", "formal", "anxious", "frustrated", "patient_urgent"}
ALLOWED_REPLY_MEMORY_COMMITMENTS = {"none", "share_status", "share_summary", "share_eta", "share_result"}


def strip_period(text: str) -> str:
    return text.strip().rstrip("。")


def compact_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def default_reply_memory() -> dict:
    return dict(REPLY_MEMORY_DEFAULT)


def normalize_reply_memory(memory: dict | None) -> dict:
    if not isinstance(memory, dict):
        return default_reply_memory()

    normalized = default_reply_memory()
    raw_followup = memory.get("followup_count", 0)
    try:
        followup_count = int(raw_followup)
    except (TypeError, ValueError):
        followup_count = 0
    normalized["followup_count"] = min(max(followup_count, 0), 2)

    prior_tone = str(memory.get("prior_tone") or "neutral").strip()
    normalized["prior_tone"] = prior_tone if prior_tone in ALLOWED_REPLY_MEMORY_TONES else "neutral"

    previous_commitment = str(memory.get("previous_assistant_commitment") or "none").strip()
    normalized["previous_assistant_commitment"] = (
        previous_commitment if previous_commitment in ALLOWED_REPLY_MEMORY_COMMITMENTS else "none"
    )

    previous_deadline = compact_text(str(memory.get("previous_deadline_promised") or ""))
    normalized["previous_deadline_promised"] = previous_deadline or None
    normalized["commitment_fulfilled"] = bool(memory.get("commitment_fulfilled", True))
    return normalized


def active_case_id() -> str | None:
    try:
        case_id = ACTIVE_CASE_PATH.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    return case_id or None


def case_reply_memory_path(case_id: str | None) -> Path | None:
    if not case_id:
        return None
    case_dir = OPEN_CASES_DIR / case_id
    if not case_dir.is_dir():
        return None
    return case_dir / "reply-memory.json"


def resolve_reply_memory_path(path: Path | None = None) -> Path:
    if path is not None:
        return path
    case_path = case_reply_memory_path(active_case_id())
    if case_path is not None:
        return case_path
    return REPLY_MEMORY_PATH


def _read_reply_memory_file(path: Path) -> dict:
    if not path.exists():
        return default_reply_memory()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default_reply_memory()
    return normalize_reply_memory(data)


def load_reply_memory(path: Path | None = None) -> dict:
    resolved_path = resolve_reply_memory_path(path)
    if resolved_path != REPLY_MEMORY_PATH and not resolved_path.exists() and REPLY_MEMORY_PATH.exists():
        return _read_reply_memory_file(REPLY_MEMORY_PATH)
    return _read_reply_memory_file(resolved_path)


def save_reply_memory(memory: dict | None, path: Path | None = None) -> None:
    normalized = normalize_reply_memory(memory)
    resolved_path = resolve_reply_memory_path(path)
    active_case_path = case_reply_memory_path(active_case_id())
    write_reset_latest = active_case_path is not None and resolved_path == active_case_path

    def write_memory(target_path: Path, payload: dict) -> None:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = target_path.with_suffix(".tmp")
        tmp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        tmp_path.replace(target_path)

    write_memory(resolved_path, normalized)
    if write_reset_latest:
        write_memory(REPLY_MEMORY_PATH, default_reply_memory())
        return
    if resolved_path != REPLY_MEMORY_PATH:
        write_memory(REPLY_MEMORY_PATH, normalized)


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
    service_id = source.get("service") or source.get("service_id")
    note = source.get("note", "")
    raw = source.get("raw_message", "")

    if state == "purchased":
        return "after_purchase"
    if state == "closed":
        return "after_close"
    if service_hint == "handoff" or service_id == "handoff-25000":
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
    service_id = source.get("service") or source.get("service_id")

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
    if is_plan_change_payment_not_reflected_case(source):
        return "plan_change_payment_not_reflected"
    if is_production_checkout_post_405_case(source):
        return "production_checkout_post_405"
    if is_preview_webhook_env_error_case(source):
        return "preview_webhook_env_error"
    if is_vercel_webhook_signature_400_case(source):
        return "vercel_webhook_signature_400"
    if is_frontend_stripe_mixed_scope_case(source):
        return "frontend_stripe_mixed_scope"
    if all(marker in combined for marker in ["Webhook", "署名検証"]) and any(
        marker in combined for marker in ["raw body", "request.text", "stripe-signature", "App Router"]
    ):
        return "stripe_webhook_raw_body_signature"
    if "customer.subscription.updated" in combined and any(marker in combined for marker in ["DB", "ダウングレード", "アップグレード"]):
        return "stripe_subscription_upgrade_db_update"
    if "お客さん" in combined and any(marker in combined for marker in ["カード引き落とし", "入金"]) and any(
        marker in combined for marker in ["商品ページ", "購入履歴"]
    ):
        return "customer_payment_access_response"
    if any(marker in combined for marker in ["100%直せる", "100%直せ", "原因が特定", "どのくらいの割合"]):
        return "success_rate_or_guarantee_question"
    if is_public_structure_scope_boundary_case(source):
        return "public_structure_scope_boundary"
    if is_fix_vs_structure_first_case(source):
        return "fix_vs_structure_first"
    if is_no_concrete_bug_anxiety_case(source):
        return "no_concrete_bug_anxiety"
    if is_multi_site_non_stripe_scope_case(source):
        return "multi_site_non_stripe_scope"
    if is_budget_completion_gate_case(source):
        return "budget_completion_gate"
    if any(marker in combined for marker in ["保証はあります", "確実に直る", "直らなかった場合", "直らなかったら"]):
        return "guarantee_or_refund_question"
    if any(marker in combined for marker in ["直せた場合", "調査だけ", "修正は別料金", "追加料金", "別料金"]):
        return "guarantee_or_refund_question"
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
    if service_hint == "handoff" or service_id == "handoff-25000":
        return "service_value_uncertain"
    if "設定変更だけ" in combined or "もっと安く" in combined:
        return "price_discount_expectation"
    if "商品名が間違" in combined or "テストプラン" in combined:
        return "possible_setting_issue"
    if "表示速度が遅い" in combined or "サイト全体が重い" in combined:
        return "performance_boundary"
    return "default_bugfix"


def is_handoff_source(source: dict) -> bool:
    service_hint = source.get("service_hint")
    service_id = source.get("service") or source.get("service_id")
    return service_hint == "handoff" or service_id == "handoff-25000"


def detect_handoff_prequote_scenario(raw: str) -> str:
    if any(marker in raw for marker in ["直接会って", "Zoom", "ビデオ", "通話"]):
        return "handoff_no_meeting_request"
    if any(marker in raw for marker in ["内容に差", "何が違う", "高い", "ChatGPT", "メモを作るだけで25,000円"]):
        return "handoff_value_compare"
    if "主要1フロー" in raw and any(marker in raw for marker in ["どう決める", "どうやって決める", "具体的にどう"]):
        return "handoff_main_flow_selection"
    if (
        any(
            marker in raw
            for marker in [
                "整理をスキップ",
                "修正だけお願い",
                "修正だけ",
                "修正は不要",
                "整理も軽く",
                "15,000円の方でまず見てもらって",
            ]
        )
        or ("15,000円" in raw and "25,000円" in raw)
        or ("15000円" in raw and "25000円" in raw)
    ) and any(marker in raw for marker in ["25,000円", "25000円", "15,000円", "15000円"]):
        return "handoff_boundary_service_choice"
    if any(marker in raw for marker in ["ついでに不具合も直して", "修正もしてもらえ", "不具合も直して", "どこまでやってもらえますか"]):
        return "handoff_fix_boundary"
    if any(marker in raw for marker in ["引き継ぐ前に", "次の担当者", "読める形", "非エンジニア", "引き継ぎ"]):
        return "handoff_readable_handoff"
    if any(marker in raw for marker in ["どこが危ない", "触ると壊れそう", "壊れそうで怖い", "まずどこが危ないか"]):
        return "handoff_risk_mapping"
    if any(marker in raw for marker in ["25,000円で具体的に何がもらえる", "仕様書みたい", "修正は含まない", "修正は含まないんですよね"]):
        return "handoff_scope_explanation"
    return "handoff_general"


def build_handoff_prequote_reply(source: dict) -> str:
    raw = source.get("raw_message", "")
    scenario = detect_handoff_prequote_scenario(raw)
    opener = "ご相談ありがとうございます。"

    if scenario == "handoff_no_meeting_request":
        paragraphs = [
            "\n".join(
                [
                    opener,
                    "通話やZoomではなく、トークルームのテキストで進めています。",
                ]
            ),
            "その前提で問題なければ、引き継ぎ前の整理として対応できます。",
            "もしテキストで進められそうかだけ、分かる範囲で教えてください。問題なければ、このまま必要な範囲を整理します。",
        ]
        return "\n\n".join(paragraphs)

    if scenario == "handoff_value_compare":
        paragraphs = [
            "\n".join(
                [
                    opener,
                    "高く感じる点を先に確認しておきたい、というご不安は自然です。",
                ]
            ),
            "違いは、コードを断片ではなく主要1フローとして読み、危険箇所・関連ファイル・次の着手順まで実務向けにまとめる点です。",
            "非エンジニアの方や次の担当者がそのまま使える形まで整える前提なので、ChatGPTに断片を貼って聞く使い方とは役割が少し違います。",
        ]
        return "\n\n".join(paragraphs)

    if scenario == "handoff_boundary_service_choice":
        paragraphs = [
            "\n".join(
                [
                    opener,
                    "常に整理と修正の両方が必要になる形ではありません。",
                ]
            ),
            "いま直したい不具合がはっきりしているなら修正側から、どこを直すべきか整理自体が必要なら整理側から入るのが近いです。",
            "15,000円の修正側で引き継ぎ用の整理までまとめて含める形ではなく、整理を主目的にする場合は25,000円側で切り分けています。",
            "整理側では、主要1フローを1つ決めて、危険箇所・関連ファイル・次の着手順が分かる引き継ぎメモを返す形です。",
            "いまの内容なら、まず一番困っている不具合が明確かどうかで入口を切るのが近いです。",
        ]
        return "\n\n".join(paragraphs)

    if scenario == "handoff_main_flow_selection":
        paragraphs = [
            "\n".join(
                [
                    opener,
                    "主要1フローは、購入後にコードを見て、一番影響範囲が広い処理か、次の担当者が最初に把握すべき処理からこちらで決めます。",
                ]
            ),
            "判断の軸は、実際に困っている動きに近いか、関連ファイルがどこまで広がるか、そこを押さえると全体像が追いやすくなるかです。",
            "今のご相談内容なら、まず動いている中でも把握しにくくなっている主要な処理を1つ選んで、関連ファイルと次の着手順が分かる形で整理します。",
        ]
        return "\n\n".join(paragraphs)

    if scenario == "handoff_fix_boundary":
        paragraphs = [
            "\n".join(
                [
                    opener,
                    "はい、まずはコード整理と引き継ぎメモ作成までの整理対応です。",
                ]
            ),
            "返るのは、主要1フローについての危険箇所・関連ファイル・次の着手順が分かる整理結果です。修正自体は含まないので、必要なら整理後に別対応をご相談いただけます。",
            "今回の内容なら、まずは決済まわりの流れを1つ対象にするのが近いです。",
        ]
        return "\n\n".join(paragraphs)

    if scenario == "handoff_readable_handoff":
        timing_line = ""
        if any(marker in raw for marker in ["間に合いますか", "契約終了前", "来月で契約終了"]):
            timing_line = "現時点の内容なら、契約終了前に主要1フローを整理して引き継ぎ用の形までまとめる進め方は取りやすいです。"
        paragraphs = [
            "\n".join(
                [
                    opener,
                    "はい、引き継ぎ前の整理として対応できます。",
                ]
            ),
            timing_line,
            "この整理では、主要1フローについて危険箇所・関連ファイル・次の着手順が分かる引き継ぎメモを作ります。非エンジニアの方でも追いやすいように、技術用語だけを並べず要点から読める形でまとめます。",
            "正式な仕様書作成やコード修正は含みませんが、次の担当者へ渡せる状態までは整理します。",
        ]
        return "\n\n".join([p for p in paragraphs if p])

    if scenario == "handoff_risk_mapping":
        paragraphs = [
            "\n".join(
                [
                    opener,
                    "はい、まずどこが危ないかを整理する形で対応できます。",
                ]
            ),
            "この整理では、主要1フローを読んで、どこを触ると影響が広がりやすいか・関連ファイルがどこか・次にどこから着手すべきかを引き継ぎメモとしてまとめます。",
            "修正自体は含まないので、まず壊しやすい場所を把握したい段階に向いています。",
        ]
        return "\n\n".join(paragraphs)

    if scenario == "handoff_scope_explanation":
        paragraphs = [
            "\n".join(
                [
                    opener,
                    "お返しするのは、主要1フローについての結論と引き継ぎメモです。",
                ]
            ),
            "中身は、危険箇所・関連ファイル・次の着手順が分かる整理結果で、次の担当者が迷わず触り始められる状態を目指します。正式な仕様書作成ではなく、現状コードを読んで実務向けにまとめるイメージです。",
            "修正自体は含みません。整理のあとに修正が必要になった場合は、別対応として続けてご相談いただけます。",
        ]
        return "\n\n".join(paragraphs)

    paragraphs = [
        "\n".join(
            [
                opener,
                "はい、コードの中身が分からない状態からでも対応できます。",
            ]
        ),
        "この整理では、主要1フローについて危険箇所・関連ファイル・次の着手順が分かる引き継ぎメモを作ります。修正そのものではなく、次の担当者が迷わず触れる状態に整理する内容です。",
        "必要になった場合は、そのあとで修正側の相談へつなげられます。",
    ]
    return "\n\n".join(paragraphs)


def build_handoff_prequote_case(source: dict) -> dict:
    raw = source.get("raw_message", "")
    scenario = detect_handoff_prequote_scenario(raw)
    return {
        "id": source.get("case_id") or source.get("id"),
        "title": source.get("category") or source.get("title") or source.get("case_id") or "handoff",
        "service_id": "handoff-25000",
        "src": source.get("route", source.get("src", "service")),
        "state": source.get("state", "prequote"),
        "raw_message": raw,
        "summary": derive_summary(source),
        "user_intent": "handoff の価値と範囲確認",
        "case_type": "handoff",
        "certainty": "high",
        "service_fit": "high",
        "risk_level": "medium" if source.get("emotional_tone") in {"anxious", "mixed", "frustrated"} else "low",
        "risk_flags": [],
        "scope_judgement": "same_cause_likely",
        "known_facts": extract_known_facts(source),
        "routing_meta": {"scenario": scenario, "service_lane": "handoff"},
        "scenario": scenario,
        "ask_count": 0,
        "reply_stance": {
            "burden_owner": "us",
            "empathy_first": source.get("emotional_tone") in {"anxious", "mixed", "frustrated"},
            "reply_skeleton": "estimate_initial",
            "answer_timing": "now",
        },
        "temperature_plan": build_temperature_plan(source, case_type="handoff"),
        "reply_contract": {
            "primary_question_id": "q1",
            "explicit_questions": [{"id": "q1", "text": "handoff-25000 の範囲と価値", "priority": "primary"}],
            "answer_map": [{"question_id": "q1", "disposition": "answer_now", "answer_brief": "handoff の範囲を直答する"}],
            "ask_map": [],
            "issue_plan": [{"issue": "handoff の範囲説明", "disposition": "answer_now", "reason": "service grounding"}],
            "required_moves": ["answer_directly_now", "give_purchase_path"],
            "forbidden_moves": ["generic_bugfix_fallback", "repair_scope_blur", "internal_term_exposure"],
        },
        "custom_rendered_reply": build_handoff_prequote_reply(source),
    }


def summarize_raw_message(raw: str) -> str:
    if "月額プラン" in raw and any(marker in raw for marker in ["メールが届かない", "完了メールが届かない", "購入後にメール"]):
        return "月額プラン購入後にメールが届かない"
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
        "budget_completion_gate",
        "service_selection_confusion",
        "service_value_uncertain",
        "followon_fix_question",
        "no_meeting_request",
        "possible_setting_issue",
        "performance_boundary",
        "guarantee_or_refund_question",
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
        "どちらのサービス",
        "何を選んでいいか",
        "25,000円の方が安全",
        "修正含まない",
        "コードも分からない",
        "実装が途中",
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


def is_fix_vs_structure_first_case(source: dict) -> bool:
    raw = source.get("raw_message", "")
    note = source.get("note", "")
    combined = f"{raw}\n{note}"
    if any(marker in combined for marker in ["25,000円", "25000円", "2万5千円", "どっちを買"]):
        return False
    if not any(marker in combined for marker in ["修正", "直す", "直して"]):
        return False
    if not any(marker in combined for marker in ["整理", "コード全体", "全体を理解", "把握", "リファクタ"]):
        return False
    return any(marker in combined for marker in ["どっち", "どちら", "先に", "先か", "先なのか", "どちらが先", "どっちが先", "まず"])


def is_public_structure_scope_boundary_case(source: dict) -> bool:
    raw = source.get("raw_message", "")
    note = source.get("note", "")
    combined = f"{raw}\n{note}"
    if not any(marker in combined for marker in ["整理", "コード全体", "全体を理解", "把握", "リファクタ"]):
        return False
    if not any(marker in combined for marker in ["修正", "直す", "直して", "バグ"]):
        return False
    return any(
        marker in combined
        for marker in [
            "25,000円",
            "25000円",
            "2万5千円",
            "引き継ぎ",
            "両方のサービス",
            "比較",
            "スキップ",
            "ついで",
            "合計",
            "どっちを買",
        ]
    )


def is_no_concrete_bug_anxiety_case(source: dict) -> bool:
    raw = source.get("raw_message", "")
    note = source.get("note", "")
    combined = f"{raw}\n{note}"
    no_bug = any(marker in combined for marker in ["不具合はたぶんない", "不具合は多分ない", "不具合がない", "不具合はない"])
    anxiety = any(marker in combined for marker in ["なんとなく不安", "漠然", "変ですか", "不安です", "よく分からないけど動いてる"])
    return no_bug and anxiety


def is_multi_site_non_stripe_scope_case(source: dict) -> bool:
    raw = source.get("raw_message", "")
    note = source.get("note", "")
    combined = f"{raw}\n{note}"
    multi_site = any(marker in combined for marker in ["2つのサイト", "2サイト", "２つのサイト", "複数サイト"])
    non_stripe_payment = any(marker in combined for marker in ["Square", "PayPay", "GMO", "PayPal", "別の決済"])
    return multi_site and "Stripe" in combined and non_stripe_payment


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


def is_budget_completion_gate_case(source: dict) -> bool:
    raw = source.get("raw_message", "")
    note = source.get("note", "")
    combined = f"{raw}\n{note}"
    price_or_budget = any(
        marker in combined
        for marker in [
            "15,000円",
            "15000円",
            "1万5千円",
            "30,000円",
            "30000円",
            "3万",
            "予算",
            "追加費用",
            "追加料金",
            "2件",
            "２件",
            "2つ",
            "二つ",
            "3本",
            "×3",
            "複数",
        ]
    )
    completion_risk = any(
        marker in combined
        for marker in [
            "追加費用が怖",
            "追加料金が怖",
            "金額が増え",
            "返金",
            "無駄にならない",
            "無駄になら",
            "原因不明",
            "直せなかった",
            "直らなかった",
            "解決しなかった",
            "解決しない",
            "修正範囲が広",
            "範囲が広",
            "2件だった",
            "２件だった",
            "2件だと",
            "２件だと",
            "2つがあります",
            "3本とも",
            "1件15,000円×3",
            "1件15000円×3",
            "念のため3本",
            "両方一緒",
            "全部見てもらって",
            "全部見て",
            "全部直して",
        ]
    )
    discount_only = any(marker in combined for marker in ["値下げ", "値引", "10,000円", "10000円", "もう少し安く"])
    if discount_only and not any(marker in combined for marker in ["返金", "追加費用", "追加料金", "2件", "２件", "2つ", "原因不明"]):
        return False
    return price_or_budget and completion_risk


def is_plan_change_payment_not_reflected_case(source: dict) -> bool:
    combined = f"{source.get('raw_message', '')}\n{source.get('note', '')}"
    return (
        "プラン変更" in combined
        and any(marker in combined for marker in ["支払いは完了", "決済は完了", "Stripeの画面"])
        and any(marker in combined for marker in ["反映され", "変わっていません", "変わらない"])
    )


def is_production_checkout_post_405_case(source: dict) -> bool:
    combined = f"{source.get('raw_message', '')}\n{source.get('note', '')}"
    return (
        "405" in combined
        and any(marker in combined for marker in ["POST", "post"])
        and "Vercel" in combined
        and any(marker in combined for marker in ["Checkout", "セッション作成", "APIルート", "API Route"])
    )


def is_preview_webhook_env_error_case(source: dict) -> bool:
    combined = f"{source.get('raw_message', '')}\n{source.get('note', '')}"
    combined_lower = combined.lower()
    return (
        any(marker in combined for marker in ["プレビュー環境", "preview環境", "Preview"])
        and "webhook" in combined_lower
        and any(marker in combined for marker in ["STRIPE_WEBHOOK_SECRET", "イベントID", "evt_"])
    )


def is_vercel_webhook_signature_400_case(source: dict) -> bool:
    combined = f"{source.get('raw_message', '')}\n{source.get('note', '')}"
    combined_lower = combined.lower()
    return (
        "webhook" in combined_lower
        and "Vercel" in combined
        and any(marker in combined for marker in ["400", "署名検証"])
        and any(marker in combined for marker in ["環境変数", "endpoint", "Route Handler", "Next.js 14", "Next.js 15"])
    )


def is_frontend_stripe_mixed_scope_case(source: dict) -> bool:
    combined = f"{source.get('raw_message', '')}\n{source.get('note', '')}"
    return (
        any(marker in combined for marker in ["フロントエンド", "フロント"])
        and "Stripe" in combined
        and any(marker in combined for marker in ["2つ", "二つ", "管理画面", "ポップアップ"])
    )


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
    if "追加料金" in text or "別料金" in text:
        return "refund_policy"
    if "直せた場合" in text or "直せた時" in text:
        return "refund_policy"
    if any(marker in text for marker in ["調査だけ", "原因が分かりません", "原因がわかりません"]) and any(
        price_marker in text for price_marker in ["15,000円", "15000円", "1万5千円"]
    ):
        return "refund_policy"
    if "保証" in text or "確実に直る" in text or "直らなかった" in text:
        return "guarantee"
    if ".env" in text or "APIキー" in text:
        return "secret_sharing"
    if "スクショ" in text or ("画面" in text and any(marker in text for marker in ["送", "見せ", "撮"])):
        return "evidence_screenshot"
    if "調べるだけ" in text:
        return "investigation_only"
    if "どうやって直す" in text or "どう直す" in text:
        return "solution_only"
    if any(marker in text for marker in ["対処法", "直し方"]) and any(marker in text for marker in ["教えて", "自分で直せ", "だけ"]):
        return "solution_only"
    if "手順書" in text or "どう直すか" in text or "自分で直す" in text:
        return "procedure_only"
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
        or "どちらのサービス" in text
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
        if qtype in {"price_acceptance", "price_general", "can_handle", "service_selection", "guarantee", "refund_policy", "solution_only"}:
            needs_implicit_primary = False
            break

    if needs_implicit_primary and source.get("state", "prequote") == "prequote":
        extracted.insert(0, derive_primary_question(raw))

    primary_index = 0
    scored: list[tuple[int, str]] = []
    for idx, question in enumerate(extracted):
        qtype = classify_question_type(question)
        score = 0
        if qtype in {"price_acceptance", "can_handle", "price_general", "service_selection", "guarantee", "refund_policy", "solution_only"}:
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
    if question_type == "solution_only":
        return "購入前に具体的な修正手順や、コード上の直し方まではお伝えしていません。"
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
        return "今の症状なら、まずこの不具合対応から入るのが近いです。"
    if question_type == "guarantee":
        return "いいえ、必ず直ると約束して受ける形ではありません。"
    if question_type == "refund_policy":
        return "いいえ、原因不明のまま正式納品に進めて15,000円だけいただく形ではありません。"
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
            "15,000円は調査だけの料金ではなく、原因確認から修正、修正済みファイルの返却まで進める前提の料金です。",
            "原因不明のまま終わる場合や、修正済みファイルを返せない場合は正式納品に進めず、キャンセルを含めてご相談します。",
        )
    if question_type == "guarantee":
        return (
            "必ず直ると断定して受けるのではなく、まず原因の切り分けから進めます。",
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
        return "確認対象ではありますが、いまは通常の不具合修正として進められるかをまだ断定しません。"
    return "今の情報だけではまだ判断し切れないので、まず必要なところだけ確認したいです。"


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
        "budget_completion_gate",
        "public_structure_scope_boundary",
        "no_concrete_bug_anxiety",
        "multi_site_non_stripe_scope",
        "service_value_uncertain",
        "followon_fix_question",
        "no_meeting_request",
        "possible_setting_issue",
        "performance_boundary",
        "security_fear",
    }:
        return "answer_after_check"
    if scenario == "service_selection_confusion":
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
            "いちばん困っている症状と、公開中のサイトだけか自分のPCでも起きるかが分かれば教えてください。",
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
        "どの画面や操作で起きるか、表示されている文言やエラー、公開中のサイトだけか自分のPCでも起きるかを分かる範囲で教えてください。",
        "15,000円の範囲で進められるかを先に切るため",
        None,
        "まだ整理できていなければ、いちばん困っている症状からで大丈夫です。",
    )


def build_case_from_source(source: dict) -> dict:
    if is_handoff_source(source):
        return build_handoff_prequote_case(source)

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
        if scenario in {"boundary_bugfix_first", "budget_completion_gate", "service_selection_confusion", "service_value_uncertain", "followon_fix_question", "no_meeting_request"}:
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
            "guarantee",
            "refund_policy",
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

        if qtype in {"timeline", "cause_owner", "security", "impact", "service_selection", "value_compare"}:
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
                "question_type": item.get("question_type"),
            }
            for item in explicit_questions
        ],
        "answer_map": answer_map,
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
    raw = case.get("raw_message", "")
    user_signal = temperature_plan.get("user_signal")
    opening_move = temperature_plan.get("opening_move")
    primary_question_item, primary_answer_item = primary_question(case)
    primary_question_type = primary_answer_item.get("question_type") or primary_question_item.get("question_type")

    if primary_question_type in {"refund_policy", "guarantee"} or any(
        marker in raw for marker in ["直せた場合", "調査だけ", "修正は別料金", "追加料金", "別料金"]
    ):
        return ""

    if any(marker in raw for marker in ["すぐ対応", "すぐ見てほしい", "お客さんから", "連絡が3件", "連絡が６件", "連絡が6件"]):
        return "お急ぎの状況は承知しました。"

    if opening_move == "action_first":
        if "checkout.session.completed" in raw and any(marker in raw for marker in ["DB 更新", "DB更新"]):
            return "checkout.session.completed までは来ているとのことなので、まずその先を確認します。"
        if any(marker in raw for marker in ["急ぎ", "すぐ見てほしい", "お客さんからも連絡"]):
            return "お急ぎの状況は承知しました。"
        if any(marker in raw for marker in ["調査だけで終わる", "まず調べます", "何も直らなかった"]):
            return "同じように調査だけで終わらないか心配ですよね。"
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
    if any(marker in raw for marker in ["保証はあります", "確実に直る", "直らなかった場合", "直らなかったら"]):
        return "見積もり前に確認しておきたい点、ありがとうございます。"
    if not summary:
        return "内容ありがとうございます。"
    if "進め方" in summary:
        return "ご相談の内容、分かりました。"
    return "内容ありがとうございます。"


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
        if qtype == "solution_only":
            return [
                "購入前に具体的な修正手順や、コード上の直し方まではお伝えしていません。",
                "購入前は、症状・エラー内容・環境から対応範囲の見立てまでお返しできます。",
            ]
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
        if qtype == "service_selection":
            return ["今の症状なら、まずこの不具合対応から入るのが近いです。"]
        if qtype == "price_acceptance":
            return ["この不具合なら15,000円で進められます。"]
    return None


def answer_now_lines(case: dict, question: dict, answer: dict) -> list[str]:
    question_text = question.get("text", "")
    question_type = answer.get("question_type") or question.get("question_type")
    brief = answer.get("answer_brief", "")
    raw = case.get("raw_message", "")
    lines: list[str] = []

    if brief.endswith("対応できる。"):
        brief = brief[: -len("対応できる。")] + "対応できます。"
    elif brief.endswith("対応できる"):
        brief = brief[: -len("対応できる")] + "対応できます"

    if "切り分け" in question_text or "切り分け" in brief:
        lines.append("原因確認から修正、修正済みファイルの返却まで含めて、15,000円で進める前提です。")
        return lines

    if question_type == "refund_policy":
        lines.append("いいえ、調査だけで15,000円をいただいて終わる形ではありません。")
        return lines
    if question_type == "guarantee":
        lines.append("いいえ、必ず直ると約束して受ける形ではありません。")
        return lines
    if question_type == "solution_only":
        lines.append("購入前に具体的な修正手順や、コード上の直し方まではお伝えしていません。")
        lines.append("Webhook署名検証エラーであれば対応範囲に入る可能性は高いので、購入前は症状・エラー内容・環境から見立てまでお返しできます。")
        lines.append("具体的な原因確認と修正は購入後に進めます。")
        return lines
    if question_type in {"can_handle", "price_acceptance"} and any(
        marker in raw for marker in ["直せた場合", "調査だけ", "修正は別料金", "原因が分かりません", "原因がわかりません"]
    ):
        lines.append("いいえ、調査だけで15,000円をいただいて終わる形ではありません。")
        return lines
    if question_type in {"can_handle", "price_acceptance"}:
        lines.append("この不具合なら15,000円で進められます。")
        return lines
    if question_type == "service_selection":
        lines.append("今の症状なら、まずこの不具合対応から入るのが近いです。")
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
    if any(marker in raw for marker in ["直せた場合", "調査だけ", "修正は別料金", "追加料金", "別料金"]):
        return ""
    if any(marker in raw for marker in ["保証はあります", "確実に直る", "直らなかった場合", "直らなかったら"]):
        return "まずは原因の切り分けと、修正まで進められるかを確認します。"
    if "ダッシュボード" in raw and "成功" in raw and any(marker in raw for marker in ["反映がなく", "何も反映", "表示されません"]):
        return "まずは Stripe で成功になっている決済が、サイト側に反映されない箇所を優先して確認します。"
    if "checkout.session.completed" in raw and any(marker in raw for marker in ["DB 更新", "DB更新"]):
        return "まずは checkout.session.completed のあとで DB 更新が止まっている箇所を確認します。"
    if "会員ページ" in raw and "反映されない" in raw:
        return "まずは購入後の反映がどこで止まっているかを確認します。"
    if "Payment Intent" in raw and "success" in raw:
        return "まずは Payment Intent が立っている状態で、success に遷移しない箇所を優先して確認します。"
    if any(marker in raw for marker in ["調査だけで終わる", "まず調べます", "何も直らなかった"]):
        return "調査だけで止める形ではなく、まずこの不具合がどこで止まっているかを確認します。"
    if "会員状態" in summary or "無料へ戻って" in summary:
        return "まずは会員状態の反映まわりを、1件の不具合として確認します。"
    if "Firestore" in summary or "timeout" in summary:
        return "まずは Firestore 反映までの流れを確認して、timeout が出る箇所を切り分けます。"
    if "購入完了メール" in raw or "注文完了メール" in raw:
        return "まずは決済後のメール送信と反映処理のどちらで止まっているかを確認します。"
    if any(marker in raw for marker in ["月額プラン", "購入後"]) and any(marker in raw for marker in ["メールが届かない", "完了メールが届かない", "メールが行かない"]):
        return "まずは購入完了後のメール送信処理がどこで止まっているかを確認します。"
    if "メール" in summary:
        return "まずはメール送信処理がどこで止まっているかを、1件の不具合として確認します。"
    if "404" in summary or "完了ページ" in summary:
        return "まずは決済完了後の遷移先まわりを、1件の不具合として確認します。"
    return "まずはこの不具合がどこで止まっているかを確認します。"


def next_action_now_for(case: dict) -> str:
    src = case.get("src")
    question, answer = primary_question(case)
    question_type = answer.get("question_type") or question.get("question_type")
    raw = case.get("raw_message", "")
    if question_type in {"refund_policy", "guarantee"} or any(
        marker in raw for marker in ["直せた場合", "調査だけ", "修正は別料金", "追加料金", "別料金"]
    ):
        return "この前提で気になる点があれば、そのまま続けて聞いてください。"
    if src == "service":
        return "この内容で進める場合は、そのままご購入いただいて大丈夫です。必要情報がそろい次第、一次結果は48時間以内を目安にお返しします。"
    if src in {"profile", "message"}:
        return "進める場合は、この内容でご提案します。必要情報がそろい次第、一次結果は48時間以内を目安にお返しします。"
    return "必要情報がそろい次第、一次結果は48時間以内を目安にお返しします。"


def secondary_lines(case: dict) -> list[str]:
    lines: list[str] = []
    raw = case.get("raw_message", "")
    added_refund_policy = False
    for question, answer in secondary_answer_items(case):
        disposition = answer.get("disposition")
        qtext = question.get("text", "")
        qtype = answer.get("question_type") or question.get("question_type")
        brief = answer.get("answer_brief", "")
        if qtype == "refund_policy" or "追加料金" in qtext or "別料金" in qtext:
            lines.append("15,000円は、不具合1件について原因確認から修正、修正済みファイルの返却まで進める前提の料金です。")
            lines.append("原因不明のまま終わる場合や、修正済みファイルを返せない場合は正式納品に進めず、キャンセルを含めてご相談します。")
            lines.append("調査だけで15,000円を使い切って、修正が別料金になる形でもありません。")
            added_refund_policy = True
            continue
        if disposition == "answer_now":
            if qtype == "procedure_only":
                lines.append("手順書だけを別で作る形ではなく、15,000円で原因調査から修正まで対応しています。")
                lines.append("調査で分かった原因と修正内容は、分かる形でお渡しできます。")
            elif qtype == "solution_only":
                lines.append("購入前に具体的な修正手順や、コード上の直し方まではお伝えしていません。")
                lines.append("購入前は、症状・エラー内容・環境から対応範囲の見立てまでお返しできます。")
            elif qtype == "investigation_only":
                lines.append("調べるだけでも大丈夫です。")
                lines.append("原因の調査から対応するので、直し方が分からない状態でも問題ありません。")
            elif qtype == "service_selection":
                lines.append("今の症状なら、まずこの不具合対応から入るのが近いです。")
            elif qtype in {"guarantee", "refund_policy"}:
                lines.append("15,000円は、不具合1件について原因確認から修正、修正済みファイルの返却まで進める前提の料金です。")
                lines.append("原因不明のまま終わる場合や、修正済みファイルを返せない場合は正式納品に進めず、キャンセルを含めてご相談します。")
            else:
                lines.append(brief)
        elif disposition == "answer_after_check":
            if qtype in {"refund_policy", "guarantee"}:
                lines.append("原因の切り分けと、修正できるかの確認は基本料金の中で進めます。")
                lines.append("原因を特定できず、修正方針にもつながらない場合は正式納品へ進めません。")
            if "cause_owner" in qtext or "Stripeの問題" in qtext or "コードの問題" in qtext:
                lines.append("Stripe側かコード側かは、今の時点ではまだ断定しません。")
            elif "今週中" in qtext or "今日中" in qtext or "何日" in qtext or "いつ" in qtext:
                lines.append("納期はコードとエラー内容を見てからの方が正確です。")
            elif "不正アクセス" in qtext:
                lines.append("不正アクセスかどうかは、今の時点ではまだ断定しません。")
            elif brief and qtype != "refund_policy":
                lines.append(brief)
    if not added_refund_policy and ("追加料金" in raw or "別料金" in raw):
        lines.append("15,000円は、不具合1件について原因確認から修正、修正済みファイルの返却まで進める前提の料金です。")
        lines.append("原因不明のまま終わる場合や、修正済みファイルを返せない場合は正式納品に進めず、キャンセルを含めてご相談します。")
        lines.append("調査だけで15,000円を使い切って、修正が別料金になる形でもありません。")
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
        bridge_to_hold.append("今の情報だけではまだ判断し切れないので、まず必要なところだけ確認したいです。")
    else:
        bridge_to_hold.append("今の情報だけではまだ判断し切れないので、まず必要なところだけ確認したいです。")

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


def render_budget_completion_gate_case(case: dict) -> str:
    raw = case.get("raw_message", "")
    opener = opener_for(case)

    if any(marker in raw for marker in ["どっちを買", "どちらを買", "整理を買", "整理が先"]):
        paragraphs = [
            "\n".join([opener, "どれを選ぶべきか、という点を先に整理します。"]),
            "この場合は、まず決済が通らない不具合修正から先に見るのが近いです。\nコード全体を整理し直す前提ではなく、修正に必要な範囲を確認します。",
            "15,000円内で修正完了まで進められないと分かった場合は、そこで止めてご説明します。\n勝手に料金が増えたり、そのまま追加作業へ進むことはありません。",
            "この内容で進める場合は、ご購入後にエラー内容やログを送ってください。",
        ]
        return "\n\n".join(paragraphs)

    if any(marker in raw for marker in ["全部見てもらって", "全部見て", "全部直して"]):
        paragraphs = [
            "\n".join([opener, "予算内で全部見て全部直せるか、という点を先に整理します。"]),
            "今の時点では、3万円以内で全体を直し切れるとは断定できません。\nこのサービスで進める場合は、まず直したい不具合を1件に絞り、15,000円の範囲で確認します。",
            "見ていく中で別原因が複数あり、この金額内では修正完了まで進められないと分かった場合は、そこで止めてご説明します。\n勝手に料金が増えたり、そのまま追加作業へ進むことはありません。",
            "まず一番困っている症状を送ってください。そこから対応範囲を見立てます。",
        ]
        return "\n\n".join(paragraphs)

    if any(marker in raw for marker in ["3本", "×3"]):
        paragraphs = [
            "\n".join([opener, "3本分の料金になるのか、という点を先に整理します。"]),
            "症状が出ているのが1本だけであれば、まずそのAPIを不具合1件として15,000円の範囲で確認します。\n念のため3本すべてを同じ深さで確認する前提ではありません。",
            "見ていく中で別のAPIも直さないと修正完了まで進められないと分かった場合は、そこで止めてご説明します。\n勝手に3件分の料金にしたり、そのまま追加作業へ進むことはありません。",
            "まずは、レスポンスが返らなくなる1本のAPIと、発生時の状況を送ってください。そこから不具合1件として対応できそうかをお返しします。",
        ]
        return "\n\n".join(paragraphs)

    if any(marker in raw for marker in ["2件", "２件", "2つ", "二つ", "複数", "両方", "30,000円", "30000円"]):
        known_symptoms = "「" in raw or "1つ目" in raw or "2つがあります" in raw
        closing = (
            "今書いていただいた2つを起点に、不具合1件として対応できそうかを先にお返しします。"
            if known_symptoms
            else "まずは2つの症状をそのまま送ってください。不具合1件として対応できそうかを先にお返しします。"
        )
        paragraphs = [
            "\n".join([opener, "追加費用が不安という点を先に整理します。"]),
            "2つの症状が同じ原因で起きている場合は、不具合1件として15,000円の範囲で対応できる可能性があります。\n別原因だった場合は、両方をこの金額内で直し切れるとは限りません。",
            "その場合も、勝手に料金が増えたり、そのまま追加作業へ進むことはありません。\nこの金額内では修正完了まで進められないと分かった時点で止めてご説明します。",
            closing,
        ]
        return "\n\n".join(paragraphs)

    if any(marker in raw for marker in ["返金", "無駄", "原因不明", "直せなかった", "直らなかった", "修正範囲が広"]):
        paragraphs = [
            "\n".join([opener, "無駄にならないかという点を先に整理します。"]),
            "15,000円は調査だけの料金ではなく、原因確認から修正、確認手順、修正済みファイルの返却まで進める前提です。",
            "確認の結果、この金額内では修正完了まで進められないと分かった場合は、未完成のまま正式納品へは進めず、そこで止めて状況をご説明します。",
            "勝手に料金が増えたり、そのまま追加作業へ進むことはありません。",
            "返金やキャンセル扱いをこの時点で断定することはできませんが、必要になった場合はココナラ上の手続きに沿ってご相談します。",
            "具体的な症状がまだであれば、分かる範囲で送ってください。対応範囲に入りそうかを先に見立てます。",
        ]
        return "\n\n".join(paragraphs)

    paragraphs = [
        "\n".join([opener, "金額が増えるのが不安という点を先に整理します。"]),
        "今回の見積もりは15,000円の範囲で進める前提です。\n確認の結果、この金額内では修正完了まで進められないと分かった場合は、そこで止めてご説明します。",
        "勝手に料金が増えたり、そのまま追加作業へ進むことはありません。",
        "具体的な症状がまだであれば、分かる範囲で送ってください。対応範囲に入りそうかを先に見立てます。",
    ]
    return "\n\n".join(paragraphs)


def render_fix_vs_structure_first_case(case: dict) -> str:
    raw = case.get("raw_message", "")
    opener = opener_for(case)
    symptom = (
        "customer.subscription.deleted のイベント処理が失敗する件"
        if "customer.subscription.deleted" in raw
        else "決済まわりの不具合"
        if "決済" in raw
        else "いま出ている不具合"
    )
    paragraphs = [
        "\n".join([opener, f"この場合は、まず全体整理より{symptom}から先に対応するのがよさそうです。"]),
        "コード全体を先に整理し直す前提ではなく、修正に必要な範囲を確認します。",
        "15,000円内で直し切れないと分かった場合は、追加作業へ進まず、そこでご説明します。",
        "この内容で進める場合は、ご購入後に発生時のログや関係ファイルを送ってください。",
    ]
    return "\n\n".join(paragraphs)


def render_public_structure_scope_boundary_case(case: dict) -> str:
    raw = case.get("raw_message", "")
    opener = opener_for(case)
    paragraphs = [
        "\n".join([opener, "まずは、実際に止まっている不具合を起点にするのが安全です。"]),
        "コード全体を整理し直す前提ではなく、不具合修正に必要な範囲を確認します。",
        "15,000円内で修正完了まで進められない、または全体整理が必要だと分かった場合は、そこで止めてご説明します。\n勝手に料金が増えたり、そのまま追加作業へ進むことはありません。",
        "この内容で進める場合は、ご購入後にエラー内容やログを送ってください。",
    ]
    if any(marker in raw for marker in ["どう直す", "直し方", "対処法", "手順書", "自分で直す"]):
        paragraphs.insert(2, "購入前に具体的な修正手順や、コード上の直し方まではお伝えしていません。")
    return "\n\n".join(paragraphs)


def render_no_concrete_bug_anxiety_case(case: dict) -> str:
    opener = opener_for(case)
    paragraphs = [
        "\n".join([opener, "変ではありません。"]),
        "ただ、このサービスは具体的な不具合が出ている状態を前提にしています。\n「動いているが、なんとなく不安」という段階であれば、無理に購入を急がなくて大丈夫です。",
        "決済が通らない、エラーが出る、表示がおかしいなど、気になる画面や操作があれば、それを1件の確認対象にできるか見立てます。",
    ]
    return "\n\n".join(paragraphs)


def render_multi_site_non_stripe_scope_case(case: dict) -> str:
    opener = opener_for(case)
    paragraphs = [
        "\n".join([opener, "まず範囲を整理します。"]),
        "2サイト分をまとめて15,000円で進める前提ではありません。\nまずは一番困っている1サイト・1症状を、不具合1件として確認します。",
        "Stripe 側であれば対応範囲に入ります。Square 側は内容が別になるため、必要であれば分けてご相談になります。",
        "まずは一番困っている症状とエラー内容を教えてください。対応範囲に入りそうかをお返しします。",
    ]
    return "\n\n".join(paragraphs)


def render_plan_change_payment_not_reflected_case(case: dict) -> str:
    return "\n\n".join(
        [
            "ご相談ありがとうございます。",
            "Stripeで支払いは完了しているのに、戻った後もサイト側のプランが反映されない状態ですね。\nこの不具合なら15,000円で対応できます。",
            "ログの場所が分からない状態でも大丈夫です。まずは決済後の反映処理と、サイト側のプラン更新処理のつながりを確認します。",
            "この内容で進める場合は、そのままご購入いただいて大丈夫です。必要情報がそろい次第、一次結果は48時間以内を目安にお返しします。",
        ]
    )


def render_production_checkout_post_405_case(case: dict) -> str:
    return "\n\n".join(
        [
            "ご相談ありがとうございます。",
            "本番のVercel上で、Stripe Checkoutのセッション作成APIだけが405になる状態ですね。\nこの不具合なら15,000円で対応できます。",
            "まずは本番とローカルで、Next.js API Route のルーティングやPOSTの扱いに差が出ていないかを確認します。",
            "この内容で進める場合は、そのままご購入いただいて大丈夫です。必要情報がそろい次第、一次結果は48時間以内を目安にお返しします。",
        ]
    )


def render_preview_webhook_env_error_case(case: dict) -> str:
    return "\n\n".join(
        [
            "ご相談ありがとうございます。",
            "ローカルは動くのに、プレビュー環境のWebhookだけエラーになる状態ですね。\nこの不具合なら15,000円で対応できます。",
            "共有いただいたEvent IDと STRIPE_WEBHOOK_SECRET の設定状況を起点に、プレビュー環境側のWebhook endpointと環境変数の反映を確認します。",
            "この内容で進める場合は、そのままご購入いただいて大丈夫です。必要情報がそろい次第、一次結果は48時間以内を目安にお返しします。",
        ]
    )


def render_vercel_webhook_signature_400_case(case: dict) -> str:
    return "\n\n".join(
        [
            "ご相談ありがとうございます。",
            "ローカルでは通るのに、Vercel上でWebhook署名検証が400になる状態ですね。\nこの不具合なら15,000円で対応できます。",
            "まずはVercel側の環境変数、endpoint URL、Next.js 14から15への更新でRoute Handlerまわりの扱いが変わっていないかを中心に確認します。",
            "この内容で進める場合は、そのままご購入いただいて大丈夫です。必要情報がそろい次第、一次結果は48時間以内を目安にお返しします。",
        ]
    )


def render_frontend_stripe_mixed_scope_case(case: dict) -> str:
    return "\n\n".join(
        [
            "ご相談ありがとうございます。",
            "Next.jsで動いているサイトであれば、フロント側の不具合も対応範囲に入ります。",
            "ただ、管理画面のボタン不反応とStripe決済後のポップアップ不具合は、同じ原因か別の原因かを先に切り分けます。\n同じ原因なら15,000円の範囲で見ます。別原因の場合は、勝手に追加作業へ進まず、対応方法と費用の有無をご相談します。",
            "まずは一番困っている方を起点に確認します。Stripe決済後のポップアップを優先する場合は、この内容でご購入いただいて大丈夫です。",
        ]
    )


def render_stripe_webhook_raw_body_signature_case(case: dict) -> str:
    return "\n\n".join(
        [
            "ご相談ありがとうございます。",
            "Next.js 14 App Router の Stripe Webhook で、署名検証が通らない状態ですね。\nstripe-signature は取れていて、raw body の取得まわりが怪しいとのことなので、15,000円で対応できます。",
            "まずは request.text() で取得している本文と、Stripe の署名検証に渡している値がずれていないかを中心に確認します。",
            "この内容で進める場合は、そのままご購入いただいて大丈夫です。必要情報がそろい次第、一次結果は48時間以内を目安にお返しします。",
        ]
    )


def render_stripe_subscription_upgrade_db_update_case(case: dict) -> str:
    return "\n\n".join(
        [
            "ご相談ありがとうございます。",
            "Stripe側ではアップグレードが反映され、customer.subscription.updated も受け取れているのに、DB側のプランが更新されない状態ですね。\nダウングレードは正常とのことなので、アップグレード時の更新分岐を中心に15,000円で確認できます。",
            "まずは受信済みイベントの処理後に、DB更新がどこで止まっているかを確認します。",
            "この内容で進める場合は、そのままご購入いただいて大丈夫です。必要情報がそろい次第、一次結果は48時間以内を目安にお返しします。",
        ]
    )


def render_customer_payment_access_response_case(case: dict) -> str:
    return "\n\n".join(
        [
            "メッセージありがとうございます。\nお急ぎの状況は承知しました。",
            "お客さんへの対応と、不具合修正の進め方の2点ですね。\nお客さんには、Stripe側で入金は確認できていて、サイト側の購入履歴反映を確認中と伝えるのが安全です。再購入や再決済は案内しないでください。",
            "不具合修正としては、決済後に購入履歴が作成されない箇所を15,000円で確認できます。\nまずは Stripe で成功した決済が、サイト側の購入履歴作成まで届いているかを確認します。",
            "進める場合は、この内容でご提案します。必要情報がそろい次第、一次結果は48時間以内を目安にお返しします。",
        ]
    )


def render_success_rate_or_guarantee_question_case(case: dict) -> str:
    return "\n\n".join(
        [
            "メッセージありがとうございます。",
            "100%直せるとはお約束しておらず、案件ごとに環境やコードの状態が違うため、原因特定率を一律の数字でお伝えすることもしていません。",
            "15,000円は、不具合1件について原因確認から修正、修正済みファイルの返却まで進める前提の料金です。\n原因や修正方針につながらず、修正済みファイルを返せない状態のまま、一方的に正式納品へ進めることはありません。",
            "具体的な症状があれば、状況を教えてください。対応範囲に入りそうかを先にお返しします。",
        ]
    )


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
                "今の症状なら",
                "今の段階では",
                "原因が分からない状態でも",
                "調べるだけでも",
                "手順書だけを別で作る形ではなく",
                "購入前に",
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
        primary_lines = answer_now_lines(case, question, answer)
        if promoted_lines:
            answer_core_lines: list[str] = []
            seen_lines: set[str] = set()
            source_lines = (
                [*primary_lines, *promoted_lines]
                if (answer.get("question_type") or question.get("question_type")) in {"can_handle", "price_acceptance"}
                else [*promoted_lines, *primary_lines]
            )
            for line in source_lines:
                cleaned = compact_text(line)
                if not cleaned or cleaned in seen_lines:
                    continue
                seen_lines.add(cleaned)
                answer_core_lines.append(line)
            fixed_slots["answer_core"] = "\n".join(answer_core_lines)
        else:
            fixed_slots["answer_core"] = "\n".join(primary_lines)
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
    custom_rendered_reply = case.get("custom_rendered_reply")
    if custom_rendered_reply:
        return custom_rendered_reply

    if case.get("state") != "prequote":
        raise ValueError(f"{case.get('id')}: only prequote is supported")
    if case.get("scenario") == "budget_completion_gate":
        case["rendered_reply_validator_mode"] = "budget_completion_gate"
        return render_budget_completion_gate_case(case)
    if case.get("scenario") == "fix_vs_structure_first":
        case["rendered_reply_validator_mode"] = "fix_vs_structure_first"
        return render_fix_vs_structure_first_case(case)
    if case.get("scenario") == "public_structure_scope_boundary":
        case["rendered_reply_validator_mode"] = "public_structure_scope_boundary"
        return render_public_structure_scope_boundary_case(case)
    if case.get("scenario") == "no_concrete_bug_anxiety":
        case["rendered_reply_validator_mode"] = "no_concrete_bug_anxiety"
        return render_no_concrete_bug_anxiety_case(case)
    if case.get("scenario") == "multi_site_non_stripe_scope":
        case["rendered_reply_validator_mode"] = "multi_site_non_stripe_scope"
        return render_multi_site_non_stripe_scope_case(case)
    if case.get("scenario") == "plan_change_payment_not_reflected":
        case["rendered_reply_validator_mode"] = "plan_change_payment_not_reflected"
        return render_plan_change_payment_not_reflected_case(case)
    if case.get("scenario") == "production_checkout_post_405":
        case["rendered_reply_validator_mode"] = "production_checkout_post_405"
        return render_production_checkout_post_405_case(case)
    if case.get("scenario") == "preview_webhook_env_error":
        case["rendered_reply_validator_mode"] = "preview_webhook_env_error"
        return render_preview_webhook_env_error_case(case)
    if case.get("scenario") == "vercel_webhook_signature_400":
        case["rendered_reply_validator_mode"] = "vercel_webhook_signature_400"
        return render_vercel_webhook_signature_400_case(case)
    if case.get("scenario") == "frontend_stripe_mixed_scope":
        case["rendered_reply_validator_mode"] = "frontend_stripe_mixed_scope"
        return render_frontend_stripe_mixed_scope_case(case)
    if case.get("scenario") == "stripe_webhook_raw_body_signature":
        case["rendered_reply_validator_mode"] = "stripe_webhook_raw_body_signature"
        return render_stripe_webhook_raw_body_signature_case(case)
    if case.get("scenario") == "stripe_subscription_upgrade_db_update":
        case["rendered_reply_validator_mode"] = "stripe_subscription_upgrade_db_update"
        return render_stripe_subscription_upgrade_db_update_case(case)
    if case.get("scenario") == "customer_payment_access_response":
        case["rendered_reply_validator_mode"] = "customer_payment_access_response"
        return render_customer_payment_access_response_case(case)
    if case.get("scenario") == "success_rate_or_guarantee_question":
        case["rendered_reply_validator_mode"] = "success_rate_or_guarantee_question"
        return render_success_rate_or_guarantee_question_case(case)
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


def save_reply(reply: str, source: str, reply_memory: dict | None = None) -> None:
    cmd = [
        str(REPLY_SAVE),
        "--text",
        reply,
        "--source-text",
        source,
    ]
    subprocess.run(cmd, check=True)
    if reply_memory is not None:
        save_reply_memory(reply_memory)


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
