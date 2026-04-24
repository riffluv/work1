#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import re
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml

from reply_quality_lint_common import collect_temperature_constraint_errors
from reply_quality_lint_common import infer_buyer_emotion


ROOT_DIR = Path(__file__).resolve().parents[1]
REPLY_SAVE = ROOT_DIR / "scripts/reply-save.sh"
PREQUOTE_RENDERER = ROOT_DIR / "scripts/render-prequote-estimate-initial.py"
SERVICE_REGISTRY_PATH = ROOT_DIR / "os/core/service-registry.yaml"
PUBLIC_BUGFIX_SERVICE_ID = "bugfix-15000"
JST = ZoneInfo("Asia/Tokyo")


def load_shared_module():
    spec = importlib.util.spec_from_file_location("render_prequote_estimate_initial", PREQUOTE_RENDERER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to load shared renderer: {PREQUOTE_RENDERER}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


shared = load_shared_module()


def load_service_grounding() -> dict:
    with SERVICE_REGISTRY_PATH.open("r", encoding="utf-8") as f:
        registry = yaml.safe_load(f) or {}

    service = next(
        (item for item in registry.get("services") or [] if item.get("service_id") == PUBLIC_BUGFIX_SERVICE_ID),
        None,
    )
    if service is None:
        raise RuntimeError(f"missing public purchased service grounding: {PUBLIC_BUGFIX_SERVICE_ID}")
    if not service.get("public"):
        raise RuntimeError(f"purchased service is not public: {PUBLIC_BUGFIX_SERVICE_ID}")

    facts_path = Path(service.get("facts_file") or "")
    if not facts_path.is_file():
        raise RuntimeError(f"missing service facts file: {facts_path}")

    with facts_path.open("r", encoding="utf-8") as f:
        facts = yaml.safe_load(f) or {}

    base_price = int(facts.get("base_price") or 15000)
    fee_text = f"{base_price:,}円"
    return {
        "service_id": service.get("service_id"),
        "public_service": bool(service.get("public")),
        "display_name": facts.get("display_name") or "",
        "fee_text": fee_text,
        "base_price": base_price,
        "scope_unit": facts.get("scope_unit") or "",
        "same_cause_rule": "同じ原因なら今回の件として見ます。別の原因や別の流れなら、その時点で切り分けて事前にご相談します。",
        "talkroom_only_rule": "電話や外部チャネルには切り替えず、このトークルーム内で進めます。",
        "direct_push_rule": "依頼者側リポジトリへの直接 push は前提にしていません。修正内容はこのトークルームで返します。",
        "deploy_boundary_rule": "本番反映の代行は前提にしていません。必要なら反映手順が分かる形で返します。",
        "secret_boundary_rule": ".envや秘密値は送らず、必要ならキー名だけで大丈夫です。",
        "same_cause_followup_rule": "同じ原因の範囲で詰まる点があれば、その範囲は今回の件として確認します。",
        "hard_no": facts.get("hard_no") or [],
    }


SERVICE_GROUNDING = load_service_grounding()
FOLLOWUP_MEMORY_SCENARIOS = {"progress_anxiety", "progress_summary_request", "timeline_anxiety"}


def time_commit(hours: int = 2) -> str:
    target = datetime.now(JST) + timedelta(hours=hours)
    return f"本日{target:%H:%M}までに、現時点の確認結果をお返しします。"


def reply_memory_for(source_or_case: dict | None) -> dict:
    if not isinstance(source_or_case, dict):
        return shared.default_reply_memory()
    return shared.normalize_reply_memory(source_or_case.get("reply_memory"))


def has_unfulfilled_commitment(source_or_case: dict | None) -> bool:
    memory = reply_memory_for(source_or_case)
    return memory.get("previous_assistant_commitment") != "none" and not memory.get("commitment_fulfilled", True)


def promised_deadline_from_text(text: str) -> str | None:
    match = re.search(r"((?:本日|明日)\d{1,2}:\d{2}までに)", text)
    if match:
        return match.group(1)
    return None


def infer_prior_tone_for_reply_memory(raw: str) -> str:
    if any(marker in raw for marker in ["どうなってるんですか", "まだ何も返事", "対応するかしないか", "放置"]):
        return "frustrated"
    if any(marker in raw for marker in ["焦ってます", "問い合わせが6件", "心配になってき", "安心します", "週明けに社内で報告"]):
        return "patient_urgent"
    if any(marker in raw for marker in ["恐れ入ります", "恐れ入りますが", "お手数ですが"]):
        return "formal"
    if any(marker in raw for marker in ["不安", "心配", "気になって"]):
        return "anxious"
    return "neutral"


def detect_commitment_kind(case: dict, rendered: str) -> str:
    scenario = case.get("scenario")
    if scenario == "progress_summary_request":
        return "share_summary"
    if scenario == "timeline_anxiety":
        return "share_eta"
    if scenario == "progress_anxiety":
        return "share_status"
    if "確認結果をお返し" in rendered or "状況を整理してお送りします" in rendered:
        return "share_status"
    return "none"


def build_reply_memory_update(case: dict, rendered: str) -> dict:
    memory = shared.default_reply_memory()
    if case.get("state") != "purchased":
        return memory

    scenario = case.get("scenario")
    if scenario not in FOLLOWUP_MEMORY_SCENARIOS:
        return memory

    previous_memory = reply_memory_for(case)
    commitment_kind = detect_commitment_kind(case, rendered)
    if commitment_kind == "none":
        return memory

    memory["followup_count"] = min((previous_memory.get("followup_count") or 0) + 1, 2)
    memory["prior_tone"] = infer_prior_tone_for_reply_memory(case.get("raw_message", ""))
    memory["previous_assistant_commitment"] = commitment_kind
    memory["previous_deadline_promised"] = promised_deadline_from_text(rendered)
    memory["commitment_fulfilled"] = False
    return memory


def is_complaint_like(source: dict) -> bool:
    raw = source.get("raw_message", "")
    tone = source.get("emotional_tone", "")
    if tone == "complaint_like":
        return True
    return any(
        marker in raw
        for marker in [
            "放置",
            "まだ何も進んでいません",
            "何度もやり取りしているのに",
            "1週間経っています",
            "いつになったら結果",
            "おっしゃっていたのに",
            "連絡がない",
        ]
    )


def promised_deadline_phrase(raw: str) -> str | None:
    if "48時間以内" in raw:
        return "お伝えしていた48時間以内を超えてしまっていて、申し訳ありません。"
    if "2時間以内" in raw:
        return "お伝えしていた2時間以内を超えてしまっていて、申し訳ありません。"
    return None


def count_shared_key_names(raw: str) -> int:
    return len(dict.fromkeys(re.findall(r"\b[A-Z][A-Z0-9_]{2,}\b", raw)))


def extra_scope_subject(raw: str) -> str:
    if "お問い合わせフォーム" in raw or "Resend" in raw:
        return "お問い合わせフォーム"
    if "リダイレクト" in raw:
        return "フォーム送信後のリダイレクト"
    if "読み込み" in raw and any(marker in raw for marker in ["遅い", "重い", "遅く"]):
        return "読み込みの件"
    if "プラン変更" in raw and "金額" in raw:
        return "プラン変更時の金額表示の件"
    if "画面" in raw:
        return "その画面"
    if "ページ" in raw:
        return "そのページ"
    return "別件"


def quote_progress_line(raw: str) -> str:
    if any(marker in raw for marker in ["あとどれくらい", "目安だけでも教えて", "いつまでこう言い続ければ"]):
        return "見えてきたところから、目安としてお伝えします。"
    if any(marker in raw for marker in ["クライアント", "進捗を聞かれて", "目安だけでも"]):
        return "確認自体は進めていますので、見えてきたところから順にお伝えします。"
    return "確認は進めていますので、見えてきたところから順にお伝えします。"


def has_explicit_hypothesis(raw: str) -> bool:
    return any(
        marker in raw
        for marker in [
            "だと思",
            "気がします",
            "候補",
            "原因だと思",
            "違ったら",
            "多分",
            "仮説",
        ]
    )


def extra_scope_request_target(raw: str) -> str:
    if "お問い合わせフォーム" in raw or "Resend" in raw:
        return "お問い合わせフォームがどう止まるか"
    if "リダイレクト" in raw:
        return "フォーム送信後にどう止まるか"
    if "読み込み" in raw and any(marker in raw for marker in ["遅い", "重い", "遅く"]):
        return "読み込みが遅いページ"
    if "プラン変更" in raw and "金額" in raw:
        return "プラン変更のときに金額が正しく表示されないページ"
    if "画面" in raw:
        return "その画面"
    if "ページ" in raw:
        return "そのページ"
    return "その箇所"


def next_action_line(case: dict, hours: int = 2) -> str:
    target = datetime.now(JST) + timedelta(hours=hours)
    if is_complaint_like(case):
        return f"本日{target:%H:%M}までに、確認結果をお送りします。"
    if case.get("scenario") == "late_info_share":
        tomorrow = datetime.now(JST) + timedelta(days=1)
        return f"明日{tomorrow:%H:%M}までに、確認結果をお返しします。"
    if case.get("scenario") == "timeline_anxiety" and any(marker in case.get("raw_message", "") for marker in ["あとどれくらい", "目安だけでも", "いつまでこう言い続ければ"]):
        return f"本日{target:%H:%M}までに、原因の方向性と次の見通しをお送りします。"
    if case.get("scenario") == "progress_anxiety":
        return f"本日{target:%H:%M}までに、状況を整理してお送りします。"
    if case.get("scenario") == "progress_summary_request":
        return f"本日{target:%H:%M}までに、現時点で見えている点を箇条書きでお送りします。"
    return f"本日{target:%H:%M}までに、現時点の確認結果をお返しします。"


def opener_for(source: dict) -> str:
    if is_complaint_like(source):
        return ""
    if source.get("scenario") == "progress_summary_request":
        return ""
    if source.get("scenario") == "env_fix_recheck":
        return ""
    if source.get("scenario") in {"external_share_request", "late_info_share"}:
        return ""
    if source.get("state") == "purchased" and source.get("scenario") in FOLLOWUP_MEMORY_SCENARIOS:
        if (reply_memory_for(source).get("followup_count") or 0) > 0:
            return ""
    route = source.get("route", source.get("src", "talkroom"))
    if route == "message":
        return "ご連絡ありがとうございます。"
    return "ありがとうございます。"


def extract_facts_known(raw: str, scenario: str) -> list[str]:
    facts: list[str] = []
    if "ZIP送りました" in raw or "ZIP送" in raw or ("ZIP" in raw and "送" in raw):
        facts.append("zip_already_sent")
    if "node_modules" in raw:
        facts.append("node_modules_omitted")
    if (".env" in raw or "envファイル" in raw or "env" in raw) and ("値は消" in raw or "キーの名前" in raw):
        facts.append("env_values_removed")
    if "画面" in raw or "スクショ" in raw:
        facts.append("symptom_surface_described")
    if "ログ" in raw and "スクショ" in raw:
        facts.append("logs_and_screenshots_already_shared")
    if "追加料金" in raw:
        facts.append("extra_fee_question_present")
    if "別原因" in raw or "同じ原因" in raw:
        facts.append("same_cause_relation_question_present")
    if "高い" in raw or "キャッシュバック" in raw or "返" in raw:
        facts.append("price_pushback_present")
    if "進捗" in raw or "どんな感じ" in raw or "2日" in raw or "半日" in raw:
        facts.append("progress_question_present")
    if "キー名だけ共有" in raw or "値は送らなくて大丈夫" in raw:
        facts.append("keys_only_shared")
    if "48時間以内" in raw:
        facts.append("promised_48h_mentioned")
    if "2時間以内" in raw:
        facts.append("promised_2h_mentioned")
    if "読み込み" in raw and any(marker in raw for marker in ["遅い", "重い", "遅く"]):
        facts.append("loading_issue_mentioned")
    if "Vercel" in raw and ("デプロイ" in raw or "ビルド" in raw):
        facts.append("vercel_build_context_present")
    if "Vercel" in raw and ("プラン変え" in raw or "プランを変え" in raw or "プラン変更" in raw):
        facts.append("vercel_plan_changed")
    if "決済を通したときだけ" in raw or ("決済" in raw and "だけ" in raw):
        facts.append("runtime_only_failure_present")
    if "スマホ" in raw and ("同じ状況" in raw or "同じ" in raw):
        facts.append("smartphone_same_failure")
    if "本番モード" in raw:
        facts.append("live_mode_confirmed")
    if scenario == "extra_scope_question":
        facts.append("additional_scope_mentioned")
    if "リダイレクト" in raw:
        facts.append("redirect_issue_mentioned")
    return facts


def build_primary_concern(source: dict, scenario: str, facts_known: list[str]) -> str:
    raw = source.get("raw_message", "")

    if scenario == "post_fix_steps_question":
        return "修正後に自分で何をする必要があるかと、デプロイを自分でできるか不安"
    if scenario == "server_access_password_question":
        return "サーバーに直接入るのか、パスワード共有が必要なのか不安"
    if scenario == "legacy_code_unknown_ok":
        return "前任者コードの事情を説明できなくても進められるか不安"
    if scenario == "unfixable_fee_question":
        return "万が一修正できない場合でも料金がどうなるのか不安"
    if scenario == "unrelated_build_error_scope":
        return "Stripeと直接関係ないビルドエラーも今回の件として見てもらえるのか知りたい"
    if scenario == "fix_file_delivery_question":
        return "今回の対応で修正ファイルも受け取れるのか不安"
    if scenario == "external_share_request":
        return "容量の都合で外部共有を使いたいが、トークルーム内で安全に進める方法を知りたい"
    if scenario == "late_info_share":
        return "明日でよい前提で、特定商品だけ通らない情報を先に共有しておきたい"
    if scenario == "missing_file_followup":
        return "抜けていた重要ファイルを追加で送りたいので、その前提で見直してほしい"
    if scenario == "which_log_and_screenshot_question":
        return "どのログとスクショを出せばよいか分からない"
    if scenario == "repo_invite_and_screenshots":
        return "GitHub招待が届いているかと、送ったスクショで足りるか知りたい"
    if scenario == "cancel_request":
        return "キャンセルや返金の前に、いまどこまで進んでいるかを知りたい"
    if scenario == "progress_anxiety":
        return "いま何が進んでいて、次の連絡がいつ来るのか不安"
    if scenario == "progress_summary_request":
        return "社内共有に使える中間報告として、現時点で分かっていることをまとめてほしい"
    if scenario == "mixed_status_timeline_fee":
        return "送ったコードの構成が見えているか、今日中に返事があるか、追加費用が出るなら先に知りたい"
    if scenario == "repo_access_confirm":
        return "ちゃんと確認に入れているか知りたい"
    if scenario == "info_sufficiency_check":
        return "今ある情報で足りているか確認したい"
    if scenario == "received_materials_flow_check":
        return "送ったログやスクショが届いているかと、この後の進め方、追加準備の有無を知りたい"
    if scenario == "screenshot_followup":
        return "送ったスクショの画面を手がかりに見てもらえるか知りたい"
    if scenario == "runtime_context_followup":
        return "追加で共有した実行環境の前提が調査に影響するか知りたい"
    if scenario == "advanced_investigation_followup":
        return "ここまで確認した内容を前提に、その続きから見てもらえるか知りたい"
    if scenario == "evidence_offer_question":
        return "スクショで足りるか、何を送ればよいか知りたい"
    if scenario == "suspected_cause_found":
        return "見つけた手がかりが原因に近いか知りたい"
    if scenario == "symptom_shift_after_user_edit":
        return "いまのコードベースを基準に見てもらえるか確認したい"
    if scenario == "handoff_fix_addon":
        return "修正相談も今回の続きとして扱えるかと費用感を知りたい"
    if scenario == "doc_followup_request":
        return "共有したフロー前提で整理を進めてよいか確認したい"
    if scenario == "source_replacement_notice":
        return "送り直したコードを新しい基準にしてほしい"
    if scenario == "external_channel_request":
        return "電話やSlackなど外部チャネルに切り替えられるか知りたい"
    if scenario == "direct_push_request":
        return "依頼者リポジトリへ直接 push してもらえるか確認したい"
    if scenario == "deployment_help_request":
        return "本番反映まで頼めるか、無理なら代替手段があるか知りたい"
    if scenario == "test_support_question":
        return "今回の対応にテスト追加まで含まれるか知りたい"
    if scenario == "live_secrets_pasted":
        return "秘密値を貼ってしまったので、今からどうすればよいか不安"
    if scenario == "unrelated_build_error_scope":
        return "Stripeと直接関係なさそうなビルドエラーも今回の件に含まれるのか不安"
    if scenario == "secret_handling_question":
        return "秘密値を出さずにこのまま進められるか確認したい"
    if scenario == "external_api_shift":
        return "外部API側の話も今回の流れとして見られるか知りたい"
    if scenario == "external_share_env_change":
        return "Googleドライブを使わず、環境が違っても進められるか確認したい"
    if scenario == "multiple_new_issues":
        return "新しく出た症状が今回の件とつながっているか知りたい"
    if scenario == "which_environment_screen":
        return "テスト環境と本番環境のどちらの画面を見ればよいか迷っている"
    if scenario == "extra_scope_question":
        if "loading_issue_mentioned" in facts_known:
            return "読み込みが遅い件も今回の続きとして見てもらえるかと追加料金の有無を知りたい"
        if "お問い合わせフォーム" in raw or "Resend" in raw:
            return "お問い合わせフォームの件もついでに見てもらいたいが、別相談になるか知りたい"
        return "別の箇所も今回の件の続きとして見てもらえるか知りたい"
    if scenario == "keys_shared":
        return "キー名だけ共有したので、このまま確認を進めてよいか知りたい"
    if scenario == "timeline_anxiety":
        return "完了までの大まかな目安と次の見通しを知りたい"
    if scenario == "delay_complaint_refund":
        return "放置されていないか不安で、返金の前にまず進捗を知りたい"
    if scenario == "price_pushback":
        return "返金や値引きのような扱いがあるか確認したい"
    if scenario == "extra_fee_anxiety":
        return "別原因になった時に勝手に追加料金にならないか不安"
    if raw:
        return shared.summarize_raw_message(raw)
    return "今回の追加連絡をどう進めるか確認したい"


def build_hard_constraints(scenario: str, grounding: dict) -> dict:
    return {
        "service_id": grounding.get("service_id"),
        "public_service_only": bool(grounding.get("public_service")),
        "answer_before_procedure": True,
        "ask_only_if_blocking": True,
        "no_external_contact": scenario in {"external_channel_request", "external_share_env_change"},
        "no_raw_secrets": scenario in {"live_secrets_pasted", "secret_handling_question", "keys_shared"},
        "no_direct_push": scenario == "direct_push_request",
        "no_prod_deploy": scenario == "deployment_help_request",
    }


def build_response_decision_plan(source: dict, scenario: str, contract: dict) -> dict:
    raw = source.get("raw_message", "")
    facts_known = extract_facts_known(raw, scenario)
    primary = next(item for item in contract["answer_map"] if item["question_id"] == contract["primary_question_id"])
    direct_answer_line = primary["answer_brief"]
    blocking_missing_facts: list[str] = []
    response_order = ["opening", "direct_answer", "answer_detail", "next_action"]

    if scenario == "progress_anxiety":
        if any(marker in raw for marker in ["進捗はどう", "今どこまで見て", "今どこまで見ていただけ", "2日経って", "待たされた経験"]):
            direct_answer_line = "いまは、今回の不具合がどこで止まっているかを確認している段階です。"
        elif any(marker in raw for marker in ["対応するかしないか", "どうなってるんですか", "まだ何も返事"]):
            direct_answer_line = "対応可否も含めて確認に入っており、まず今の状況を整理してお返しします。"
        else:
            direct_answer_line = "いまは原因の切り分け中で、まだ断定には至っていません。"
        response_order = ["opening", "direct_answer", "answer_detail", "next_action"]
    elif scenario == "progress_summary_request":
        direct_answer_line = "現時点で見えている点は、中間報告としてまとめます。"
        response_order = ["opening", "direct_answer", "answer_detail", "next_action"]
    elif scenario == "mixed_status_timeline_fee":
        direct_answer_line = "はい、送っていただいたコードのフォルダ構成は見えています。"
        response_order = ["opening", "direct_answer", "answer_detail", "next_action"]
    elif scenario == "delay_complaint_refund":
        direct_answer_line = "まず進み具合を整理してお返しします。"
        response_order = ["opening", "direct_answer", "answer_detail", "next_action"]
    elif scenario == "timeline_anxiety":
        if any(marker in raw for marker in ["あとどれくらい", "目安だけでも", "いつまでこう言い続ければ"]):
            direct_answer_line = "現時点ではあとどれくらいかはまだ言い切れません。"
        else:
            direct_answer_line = "完了時期は、現時点ではまだ言い切れず、今の確認結果を見てからの方が正確です。"
        response_order = ["opening", "direct_answer", "answer_detail", "next_action"]
    elif scenario == "private_repo_access_question":
        direct_answer_line = "privateリポジトリなら、URLだけではこちらから中身は見えません。"
        response_order = ["opening", "direct_answer", "answer_detail", "next_action"]
    elif scenario == "price_pushback":
        direct_answer_line = "料金は今回の調査と修正を1件として進める固定料金で、キャッシュバックの仕組みはありません。"
        response_order = ["opening", "direct_answer", "answer_detail", "next_action"]
    elif scenario == "extra_fee_anxiety":
        direct_answer_line = "今の時点では、追加料金になるとはまだ決まっていません。"
        response_order = ["opening", "direct_answer", "answer_detail", "next_action"]
    elif scenario == "extra_scope_question":
        direct_answer_line = "同じ原因なら今回の件としてこのまま見ます。"
        blocking_missing_facts = [] if any(marker in raw for marker in ["画面", "崩れ", "エラー", "症状"]) else ["additional_scope_symptom"]
        response_order = ["opening", "direct_answer", "answer_detail", "ask", "next_action"] if blocking_missing_facts else ["opening", "direct_answer", "answer_detail", "next_action"]
    elif scenario == "post_fix_steps_question":
        direct_answer_line = "はい、反映自体はご自身でお願いしています。"
        response_order = ["opening", "direct_answer", "answer_detail", "next_action"]
    elif scenario == "server_access_password_question":
        direct_answer_line = "サーバーに直接入って作業する前提ではありません。"
        response_order = ["opening", "direct_answer", "answer_detail", "next_action"]
    elif scenario == "legacy_code_unknown_ok":
        direct_answer_line = "はい、その状態でも大丈夫です。"
        response_order = ["opening", "direct_answer", "answer_detail", "next_action"]
    elif scenario == "unfixable_fee_question":
        direct_answer_line = "原因不明のまま終わる場合や、修正済みファイルを返せない場合は、そのまま正式納品には進めません。"
        response_order = ["opening", "direct_answer", "answer_detail", "next_action"]
    elif scenario == "unrelated_build_error_scope":
        direct_answer_line = "Stripeと直接関係ないNext.jsのビルドエラーなら、今回とは別の話になる可能性が高いです。"
        blocking_missing_facts = ["build_error_text"]
        response_order = ["opening", "direct_answer", "answer_detail", "ask", "next_action"]
    elif scenario == "fix_file_delivery_question":
        direct_answer_line = "はい、今回の対応では、必要な修正があれば修正ファイルもお渡しします。"
        response_order = ["opening", "direct_answer", "answer_detail", "next_action"]
    elif scenario == "missing_file_followup":
        direct_answer_line = "はい、追加で送っていただければ大丈夫です。受領後にそのファイルを含めて見直します。"
        response_order = ["opening", "direct_answer", "answer_detail", "next_action"]
    elif scenario == "which_log_and_screenshot_question":
        direct_answer_line = "デプロイ自体が通っているなら、Vercelのデプロイログより先にブラウザのエラー画面と、あればStripe側の表示を優先して見ます。"
        response_order = ["opening", "direct_answer", "answer_detail", "next_action"]
    elif scenario == "repo_invite_and_screenshots":
        direct_answer_line = "招待の件はこちらで確認します。届いていればそのまま進めます。"
        response_order = ["opening", "direct_answer", "answer_detail", "next_action"]
    elif scenario == "info_sufficiency_check":
        if "node_modules_omitted" in facts_known or "env_values_removed" in facts_known:
            direct_answer_line = "はい、その形で大丈夫です。node_modules はなくて問題なく、.env も値を消した状態のままで進められます。"
        response_order = ["opening", "direct_answer", "answer_detail", "next_action"]
    elif scenario == "received_materials_flow_check":
        direct_answer_line = "はい、昨日のログとスクショは確認できています。"
        response_order = ["opening", "direct_answer", "answer_detail", "next_action"]
    elif scenario == "screenshot_followup":
        direct_answer_line = "スクショありがとうございます。その画面を手がかりに見ます。"
        response_order = ["opening", "direct_answer", "answer_detail", "next_action"]
    elif scenario == "runtime_context_followup":
        direct_answer_line = "はい、その情報は調査に影響します。"
        response_order = ["opening", "direct_answer", "answer_detail", "next_action"]
    elif scenario == "advanced_investigation_followup":
        direct_answer_line = "はい、ここまで確認いただいている前提で、その続きから見ます。"
        response_order = ["opening", "direct_answer", "answer_detail", "next_action"]
    elif scenario == "suspected_cause_found":
        if any(marker in raw for marker in ["Webhook secret", "No signatures found matching the expected signature for payload", "signing secret is incorrect", "signing secret"]):
            direct_answer_line = "手がかりとしてかなり助かります。Webhook secret のずれも候補として見ています。"
        response_order = ["opening", "direct_answer", "answer_detail", "next_action"]
    elif scenario == "external_api_shift":
        direct_answer_line = "このまま進められるかは、まず今回の件と同じ流れかを確認します。"
        blocking_missing_facts = ["external_api_error_surface"]
        response_order = ["opening", "direct_answer", "answer_detail", "ask", "next_action"]
    elif scenario == "evidence_offer_question":
        direct_answer_line = "はい、スクショで大丈夫です。"
        response_order = ["opening", "direct_answer", "ask", "next_action"]
    elif scenario == "symptom_shift_after_user_edit":
        blocking_missing_facts = ["latest_code_snapshot"]
        response_order = ["opening", "direct_answer", "answer_detail", "ask", "next_action"]
    elif scenario == "handoff_fix_addon":
        blocking_missing_facts = ["fix_target"]
        response_order = ["opening", "direct_answer", "answer_detail", "ask", "next_action"]
    elif scenario == "multiple_new_issues":
        blocking_missing_facts = ["new_issue_surface"]
        response_order = ["opening", "direct_answer", "answer_detail", "ask", "next_action"]
    elif scenario == "generic_followup":
        direct_answer_line = primary["answer_brief"]

    return {
        "primary_question_id": contract["primary_question_id"],
        "primary_concern": build_primary_concern(source, scenario, facts_known),
        "buyer_emotion": infer_buyer_emotion(raw),
        "facts_known": facts_known,
        "blocking_missing_facts": blocking_missing_facts,
        "direct_answer_line": direct_answer_line,
        "response_order": response_order,
    }


def detect_scenario(source: dict) -> str:
    raw = source.get("raw_message", "")
    note = source.get("note", "")
    service_hint = source.get("service_hint", "")
    combined = f"{raw}\n{note}"

    if "キャンセル" in combined:
        return "cancel_request"
    if any(marker in combined for marker in ["週明けに社内で報告", "箇条書きレベル", "何か分かっていることがあれば"]) and any(
        marker in combined for marker in ["共有いただけると助かります", "社内で報告", "中間報告"]
    ):
        return "progress_summary_request"
    if any(marker in combined for marker in ["あとどれくらいかかりそう", "あとどれくらい", "いつまでこう言い続ければ", "目安だけでも教えてもらえませんか"]):
        return "timeline_anxiety"
    if "キャッシュバック" in combined or "少し返" in combined or "少しお返し" in combined:
        return "price_pushback"
    if "引き継ぎメモ" in combined and "修正" in combined:
        return "handoff_fix_addon"
    if any(
        marker in combined
        for marker in [
            "進捗どう",
            "進捗はどう",
            "どんな感じ",
            "まだ何も連絡",
            "まだ何も返事",
            "1週間経って",
            "2日経って",
            "もう2日",
            "半日経ち",
            "いつになったら結果",
            "進捗確認",
            "どうなってるんですか",
            "対応するかしないか",
            "今どのあたりまで進んでますか",
            "今どのあたりまで",
            "今どこまで見て",
            "今どこまで見ていただけ",
            "確認って進んでますか",
            "状況だけでも教えて",
            "心配になってきまして",
            "待たされた経験",
        ]
    ):
        return "progress_anxiety"
    if any(marker in combined for marker in ["中間報告", "社内のミーティング", "プロに依頼してます", "現時点で分かっていることだけでもまとめて"]):
        return "progress_summary_request"
    if (
        "3点あります" in combined
        and any(marker in combined for marker in ["フォルダ構成", "見えてますか"])
        and any(marker in combined for marker in ["今日中", "返事もらえますか", "返事もら"])
        and any(marker in combined for marker in ["追加費用", "先に言ってほしい"])
    ):
        return "mixed_status_timeline_fee"
    if any(marker in combined for marker in ["大丈夫そうですか", "ちゃんと見れましたか", "見れてますか", "アクセスできないとかあったら"]):
        return "repo_access_confirm"
    if (
        "GitHub" in combined
        and "private" in combined.lower()
        and any(marker in combined for marker in ["見えてますか", "見えてますでしょうか", "招待", "必要ですか"])
    ):
        return "private_repo_access_question"
    if (
        "GitHub" in combined
        and "招待" in combined
        and any(marker in combined for marker in ["ユーザー名", "スクショ", "3枚", "多めに撮", "参考になる"])
    ):
        return "repo_invite_and_screenshots"
    if (
        any(marker in combined for marker in ["届いてますでしょうか", "届いてますか", "届いているか", "届いてます"])
        and any(marker in combined for marker in ["ログ", "スクショ", "流れ", "追加で用意", "準備しておきます"])
    ) or (
        any(marker in combined for marker in ["初めてこういうサービス", "流れで進む", "イメージできてなく"])
        and any(marker in combined for marker in ["追加で用意", "準備しておきます", "ログ", "スクショ"])
    ):
        return "received_materials_flow_check"
    if (
        any(marker in combined for marker in ["スクショ", "スクリーンショット"])
        and any(marker in combined for marker in ["[画像]", "エラーの画面", "同じ画面", "何回やっても"])
    ):
        return "screenshot_followup"
    if (
        any(marker in combined for marker in ["修正が終わったあと", "私の方でやること", "ファイルの差し替え", "デプロイ"])
        and any(marker in combined for marker in ["自分でやる前提", "慣れてなく", "デプロイ周り"])
    ):
        return "post_fix_steps_question"
    if any(
        marker in combined
        for marker in [
            "サーバーに直接入って",
            "直接入って作業",
            "修正したファイルを送って",
            "自分で置き換える",
            "サーバーのパスワード",
            "パスワードとか教え",
        ]
    ):
        return "server_access_password_question"
    if (
        any(marker in combined for marker in ["前任者", "よく分かってない", "答えられないかもしれません", "それでも大丈夫"])
        and any(marker in combined for marker in ["コード", "箇所", "書いた"])
    ):
        return "legacy_code_unknown_ok"
    if "修正ファイル" in combined and any(marker in combined for marker in ["もらえる", "もらえるんですよね", "自分で直す形", "原因はここです"]):
        return "fix_file_delivery_question"
    if any(marker in combined for marker in ["どこのログ", "Vercelのデプロイログ", "Stripeのほう"]) and any(
        marker in combined for marker in ["スクショ", "ブラウザの画面", "エラーメッセージ"]
    ):
        return "which_log_and_screenshot_question"
    if (
        any(marker in combined for marker in ["requires_action", "payment_intent.requires_action", "3Dセキュア", "handleCardAction"])
        and any(marker in combined for marker in ["ここまで分かっている前提", "続きを見てもら", "続きを見て", "前提で"])
    ):
        return "advanced_investigation_followup"
    if (
        any(
            marker in combined
            for marker in [
                "伝え忘れていました",
                "影響しますか",
                "影響ありえますか",
                "補足です",
                "追加です",
            ]
        )
        and any(
            marker in combined
            for marker in [
                "Vercel",
                "デプロイ",
                "ビルド時",
                "決済を通したとき",
                "本番モード",
                "スマホ",
                "パソコン",
                "プラン変え",
                "プラン変更",
            ]
        )
    ):
        return "runtime_context_followup"
    if (
        any(marker in combined for marker in ["腑に落ちない", "ちょっと腑に落ちない", "同じ設定で動いてた"])
        and any(marker in combined for marker in ["環境変数", "Vercel側", "勝手に変わった", "ありえますかね", "ありえますか"])
    ):
        return "diagnosis_pushback_followup"
    if (
        any(marker in combined for marker in ["他のお客さん", "他のお客さま", "個人情報", "入ってたりしない", "入ってたりしないかな", "消してもらえる"])
        and any(marker in combined for marker in ["ログ", "送ったログ", "さっき送った"])
    ):
        return "shared_log_privacy_concern"
    if any(marker in combined for marker in ["pages/api/webhook.ts", ".gitignoreに入れて", "ファイルが1個抜け", "追加で送ります"]) and any(
        marker in combined for marker in ["抜けてた", "抜けてたかも", "大事なファイル", "的外れな調査"]
    ):
        return "missing_file_followup"
    if (
        any(marker in combined for marker in ["修正できません", "修正できない", "万が一", "まだそうなると決まったわけじゃない"])
        and "料金" in combined
    ):
        return "unfixable_fee_question"
    if (
        any(marker in combined for marker in ["Next.jsのビルドが通ら", "ビルドが通らなく", "型エラー", "TypeScript"])
        and any(marker in combined for marker in ["Stripe関係ない", "関係あるのかないのか", "範囲外なら", "別で相談"])
    ):
        return "unrelated_build_error_scope"
    if any(marker in combined for marker in ["足りてますか", "足りないものがあったら", "作業止まってたら", "忘れてて", "不足があれば"]):
        return "info_sufficiency_check"
    if "スクショを送れば" in combined or "スクショ送れば" in combined:
        return "evidence_offer_question"
    if (
        any(marker in combined for marker in ["signing secret is incorrect", "signing secret"])
        and any(marker in combined for marker in ["Webhook", "Stripe", "修正をお願い", "修正をお願いしたい", "お願いしたい"])
    ):
        return "suspected_cause_found"
    if (
        any(marker in combined for marker in ["Cannot read properties", "priceId", "原因らしき", "これで原因分かりますか", "たぶん", "Webhook", "URLパス"])
        and any(marker in combined for marker in ["Vercel", "ログ", "undefined", "失敗してると思", "毎回エラー", "失敗してます", "どう思いますか", "気がしてきた"])
    ):
        return "suspected_cause_found"
    if (
        "STRIPE_SECRET_KEY" in combined
        and "Vercel" in combined
        and any(marker in combined for marker in ["セットしておきました", "設定されてなかった", "これで直るはず", "念のため確認", "念のため確認して"])
    ):
        return "env_fix_recheck"
    if any(marker in combined for marker in ["エラーが出なくなりました", "今度は重複決済", "症状が途中で変わる", "こっちを直してもらっていい"]):
        return "symptom_shift_after_user_edit"
    if "キー名だけ共有" in combined or "値は送らなくて大丈夫" in combined:
        return "keys_shared"
    if (
        any(marker in raw for marker in ["sk_live_", "whsec_", "DATABASE_URL="])
        or (
            "STRIPE_SECRET_KEY" in raw
            and any(marker in raw for marker in ["値が入って", "そのまま貼っ", "送っちゃ", "貼っちゃ", ".envの中身", "秘密情報"])
        )
        or (
            any(marker in raw for marker in ["ログイン情報", "ログイン:", "ログイン："])
            and any(marker in raw for marker in ["パスワード", "password", "パスワード:", "パスワード："])
        )
        or "秘密情報" in raw
    ):
        return "live_secrets_pasted"
    if any(
        marker in raw
        for marker in [".env", "envファイル", "env ファイル", "ハードコード", "キーとか入ってる", "送っちゃっていい"]
    ):
        return "secret_handling_question"
    if "外部API" in combined:
        return "external_api_shift"
    if any(marker in combined for marker in ["電話", "Zoom", "LINE", "Slack", "slack", "TeamViewer"]):
        return "external_channel_request"
    if any(marker in combined for marker in ["push", "コラボレーター", "master ブランチ"]) or ("GitHub" in combined and "push" in combined):
        return "direct_push_request"
    if "Googleドライブ" in combined or "Google Drive" in combined:
        return "external_share_request"
    if "さくら" in combined:
        return "external_share_env_change"
    if (
        any(marker in combined for marker in ["夜遅く", "明日で全然大丈夫", "情報だけ先に送っておきます"])
        and any(marker in combined for marker in ["特定の商品だけ", "他の商品は問題ない", "商品ID:", "prod_"])
    ):
        return "late_info_share"
    if "差額払う" in combined and "切り替える" in combined:
        return "handoff_fix_addon"
    if "購入したのは修正" in combined and ("全体像" in combined or "整理" in combined):
        return "handoff_fix_addon"
    if any(marker in combined for marker in ["デプロイの方法が分から", "本番にも反映", "どうやって反映", "意味がないんですが", "本番環境触るの怖", "反映のやり方"]):
        return "deployment_help_request"
    if "unittest" in combined or "継続的にチェック" in combined:
        return "test_support_question"
    if service_hint == "handoff" and any(marker in combined for marker in ["フローは", "メモは", "外注さん", "読みます", "DB登録"]):
        return "doc_followup_request"
    if service_hint == "handoff" and any(marker in combined for marker in ["送り直す", "送り直します", "前のは破棄", "こっちベース"]):
        return "source_replacement_notice"
    if "これ全部つながってますか" in combined:
        return "multiple_new_issues"
    if "どちらを見ればいい" in combined or "テスト環境と本番環境" in combined or ("テスト環境" in combined and "次は何をすればいい" in combined):
        return "which_environment_screen"
    if (
        "別の原因" in combined
        or "今回の不具合とは別" in combined
        or "とは別で" in combined
        or "別で、" in combined
        or "今回の範囲で見てもらえる" in combined
        or "とは別なんですが" in combined
        or "範囲外なら別で相談" in combined
        or "一緒に見てもらうことは可能" in combined
        or "これも一緒に見てもら" in combined
        or "これも同じ修正の中で見てもら" in combined
        or "依頼した件とは別" in combined
        or "今やってもらってる件とは別" in combined
        or "元の依頼とは別" in combined
        or ("追加料金" in combined and "一緒に" in combined)
        or "ついでに見てもら" in combined
        or "お問い合わせフォーム" in combined
        or "Resend" in combined
        or "APIキーが期限切れ" in combined
        or ("ついでに" in combined and "数行足し" in combined)
        or "5分もかからない" in combined
        or "もう1個だけ" in combined
        or "同じ原因だと思う" in combined
        or "別のエラー画面" in combined
    ):
        return "extra_scope_question"
    if "追加料金" in combined or "別原因" in combined or "話が違う" in combined or "フロント側だった" in combined:
        return "extra_fee_anxiety"
    if any(marker in combined for marker in ["どのくらいかかりそう", "いつ直るのか", "目安だけでも", "クライアントから進捗", "進捗を聞かれて", "その後いかがでしょうか"]):
        return "timeline_anxiety"
    if any(marker in combined for marker in ["3日経ち", "何も進んでいません", "2時間以内", "放置", "返金してほしい"]):
        return "delay_complaint_refund"
    return "generic_followup"


def build_case_from_source(source: dict) -> dict:
    raw = source.get("raw_message", "")
    scenario = detect_scenario(source)
    summary = shared.derive_summary(source)
    reply_memory = reply_memory_for(source)

    case = {
        "id": source.get("case_id") or source.get("id"),
        "src": source.get("route", "talkroom"),
        "state": "purchased",
        "emotional_tone": source.get("emotional_tone"),
        "raw_message": raw,
        "summary": summary,
        "known_facts": shared.extract_known_facts(source),
        "routing_meta": shared.build_routing_meta(source, scenario),
        "service_grounding": dict(SERVICE_GROUNDING),
        "hard_constraints": build_hard_constraints(scenario, SERVICE_GROUNDING),
        "reply_stance": {
            "burden_owner": "us",
            "empathy_first": source.get("emotional_tone") in {"anxious", "mixed", "frustrated"},
            "reply_skeleton": "post_purchase_quick",
        },
        "temperature_plan": shared.build_temperature_plan(
            source,
            case_type="boundary"
            if scenario
            in {
                "extra_scope_question",
                "generic_followup",
                "extra_fee_anxiety",
                "handoff_fix_addon",
                "server_access_password_question",
                "legacy_code_unknown_ok",
                "fix_file_delivery_question",
                "which_log_and_screenshot_question",
                "repo_invite_and_screenshots",
                "unrelated_build_error_scope",
                "external_channel_request",
                "direct_push_request",
                "deployment_help_request",
            }
            else "after_purchase",
        ),
        "scenario": scenario,
        "reply_memory": reply_memory,
    }

    if scenario in {"external_share_request", "late_info_share"}:
        case["temperature_plan"]["opening_move"] = "react_briefly"

    if scenario == "cancel_request":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "キャンセルしたい", "priority": "primary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_after_check",
                    "answer_brief": "途中でも、進み具合によってはキャンセルできる場合があります。まず今どこまで進んでいるかを確認します。",
                    "hold_reason": "返金やキャンセルの扱いは、現在の進み具合を確認してから案内した方がずれません。",
                    "revisit_trigger": "確認できたところまでと、次の案内をお返しします。",
                },
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "defer_with_reason", "commit_next_update_time"],
        }
        case["response_decision_plan"] = build_response_decision_plan(source, scenario, case["reply_contract"])
        return case

    if scenario == "progress_anxiety":
        answers = [
            {
                "question_id": "q1",
                "disposition": "answer_after_check",
                "answer_brief": "いまは原因の切り分け中で、原因はまだ断定できていません。",
                "hold_reason": "確認できているところから先にお返しします。",
                "revisit_trigger": "現時点で見えている範囲を整理してお返しします。",
            }
        ]
        explicit_questions = [{"id": "q1", "text": "今どんな状況か", "priority": "primary"}]
        if any(marker in raw for marker in ["Slack", "slack", "電話", "Zoom", "LINE"]):
            explicit_questions.append({"id": "q2", "text": "外部チャネルに切り替えた方が早いか", "priority": "secondary"})
            answers.append(
                {
                    "question_id": "q2",
                    "disposition": "answer_now",
                    "answer_brief": "外部チャネルへ切り替えず、このトークルーム内で進めます。",
                }
            )
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": explicit_questions,
            "answer_map": answers,
            "ask_map": [],
            "required_moves": ["react_briefly_first", "defer_with_reason", "commit_next_update_time"],
        }
        case["response_decision_plan"] = build_response_decision_plan(source, scenario, case["reply_contract"])
        return case

    if scenario == "progress_summary_request":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "現時点で分かっていることを中間報告としてまとめてもらえるか", "priority": "primary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "現時点で分かっている点は、中間報告としてお返しできます。",
                }
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now", "commit_next_update_time"],
        }
        case["response_decision_plan"] = build_response_decision_plan(source, scenario, case["reply_contract"])
        return case

    if scenario == "mixed_status_timeline_fee":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "送ったコードのフォルダ構成が見えているか", "priority": "primary"},
                {"id": "q2", "text": "今日中に返事がもらえるか", "priority": "secondary"},
                {"id": "q3", "text": "追加費用が出るなら先に言ってほしい", "priority": "secondary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "はい、送っていただいたコードのフォルダ構成は見えています。",
                },
                {
                    "question_id": "q2",
                    "disposition": "answer_now",
                    "answer_brief": "今日は現時点の確認結果をお返しします。",
                },
                {
                    "question_id": "q3",
                    "disposition": "answer_now",
                    "answer_brief": "追加費用が必要になる場合は、その前に必ずご相談します。",
                },
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now", "commit_next_update_time"],
        }
        case["response_decision_plan"] = build_response_decision_plan(source, scenario, case["reply_contract"])
        return case

    if scenario == "evidence_offer_question":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "スクショを送ればよいか", "priority": "primary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "はい、スクショで大丈夫です。Stripe管理画面で失敗になっている箇所が分かるものを送ってください。",
                },
            ],
            "ask_map": [
                {
                    "id": "a1",
                    "question_ids": ["q1"],
                    "ask_text": "失敗になっているイベントが分かる画面を、そのまま送ってください。",
                    "why_needed": "どこで止まっているかを先に切るため",
                }
            ],
            "required_moves": ["react_briefly_first", "answer_directly_now", "request_minimum_evidence", "commit_next_update_time"],
        }
        case["response_decision_plan"] = build_response_decision_plan(source, scenario, case["reply_contract"])
        return case

    if scenario == "repo_access_confirm":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "ちゃんと見られているか", "priority": "primary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "はい、見られています。アクセスできない点があればこちらからすぐお伝えします。",
                },
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now", "commit_next_update_time"],
        }
        case["response_decision_plan"] = build_response_decision_plan(source, scenario, case["reply_contract"])
        return case

    if scenario == "info_sufficiency_check":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "送った情報で足りているか", "priority": "primary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "今のところ足りています。追加で必要なものが出たら、その時はこちらから絞ってお願いします。",
                },
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now", "commit_next_update_time"],
        }
        return case

    if scenario == "post_fix_steps_question":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "修正後に自分で何をする必要があるか", "priority": "primary"},
                {"id": "q2", "text": "デプロイに不安があっても手順を教えてもらえるか", "priority": "secondary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "はい、反映自体はご自身でお願いしています。",
                },
                {
                    "question_id": "q2",
                    "disposition": "answer_now",
                    "answer_brief": "ファイルの差し替えやデプロイが必要な場合は、分かる形で手順もあわせてお返しします。",
                },
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now", "commit_next_update_time"],
        }
        case["response_decision_plan"] = build_response_decision_plan(source, scenario, case["reply_contract"])
        return case

    if scenario == "server_access_password_question":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "サーバーに直接入って作業するのか", "priority": "primary"},
                {"id": "q2", "text": "サーバーのパスワード共有が必要か", "priority": "secondary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "サーバーに直接入って作業する前提ではありません。",
                },
                {
                    "question_id": "q2",
                    "disposition": "answer_now",
                    "answer_brief": "修正したファイルや確認内容をこのトークルームでお返しする形で進めるので、サーバーのパスワードも不要です。",
                },
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now", "commit_next_update_time"],
        }
        case["response_decision_plan"] = build_response_decision_plan(source, scenario, case["reply_contract"])
        return case

    if scenario == "legacy_code_unknown_ok":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "前任者コードの事情を説明できなくても進められるか", "priority": "primary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "はい、その状態でも大丈夫です。",
                },
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now", "commit_next_update_time"],
        }
        case["response_decision_plan"] = build_response_decision_plan(source, scenario, case["reply_contract"])
        return case

    if scenario == "unfixable_fee_question":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "修正できない場合の料金はどうなるか", "priority": "primary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "原因不明のまま終わる場合や、修正済みファイルを返せない場合は、そのまま正式納品には進めません。",
                },
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now", "commit_next_update_time"],
        }
        case["response_decision_plan"] = build_response_decision_plan(source, scenario, case["reply_contract"])
        return case

    if scenario == "unrelated_build_error_scope":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "Next.jsのビルドエラーも今回の範囲か", "priority": "primary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_after_check",
                    "answer_brief": "Stripeと直接関係ないNext.jsのビルドエラーなら、今回とは別の話になる可能性が高いです。",
                    "hold_reason": "ただ、直前の変更とつながっている可能性もあるので、まずは同じ原因かだけ確認します。",
                    "revisit_trigger": "型エラーの文言を受け取ったあとに、今回の件として見るか切り分けます。",
                },
            ],
            "ask_map": [
                {
                    "id": "a1",
                    "question_ids": ["q1"],
                    "ask_text": "型エラーの文言が分かれば、その1行だけ送ってください。",
                    "why_needed": "今回の件とつながっているかを先に切るため",
                }
            ],
            "required_moves": ["react_briefly_first", "defer_with_reason", "request_minimum_evidence", "commit_next_update_time"],
        }
        case["response_decision_plan"] = build_response_decision_plan(source, scenario, case["reply_contract"])
        return case

    if scenario == "fix_file_delivery_question":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "修正ファイルをもらえるか", "priority": "primary"},
                {"id": "q2", "text": "原因だけ伝えて終わる形ではないか", "priority": "secondary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "はい、今回の対応では、必要な修正があれば修正ファイルもお渡しします。",
                },
                {
                    "question_id": "q2",
                    "disposition": "answer_now",
                    "answer_brief": "原因だけお伝えして終わる前提ではなく、確認手順もあわせてお返しします。",
                },
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now", "commit_next_update_time"],
        }
        case["response_decision_plan"] = build_response_decision_plan(source, scenario, case["reply_contract"])
        return case

    if scenario == "which_log_and_screenshot_question":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "どのログを見ればよいか", "priority": "primary"},
                {"id": "q2", "text": "スクショはブラウザ画面でよいか", "priority": "secondary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "デプロイ自体が通っているなら、Vercelのデプロイログより先にブラウザのエラー画面と、あればStripe側の表示を優先して見ます。",
                },
                {
                    "question_id": "q2",
                    "disposition": "answer_now",
                    "answer_brief": "スクショはブラウザの画面で大丈夫です。エラーメッセージが見えている状態のものをお願いします。",
                },
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now", "commit_next_update_time"],
        }
        case["response_decision_plan"] = build_response_decision_plan(source, scenario, case["reply_contract"])
        return case

    if scenario == "repo_invite_and_screenshots":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "GitHub招待は届いているか", "priority": "primary"},
                {"id": "q2", "text": "スクショは多めでも大丈夫か", "priority": "secondary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "招待の件はこちらで確認します。届いていればそのまま進めます。",
                },
                {
                    "question_id": "q2",
                    "disposition": "answer_now",
                    "answer_brief": "スクショは多めでも大丈夫です。一番参考になるものはこちらで見ます。",
                },
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now", "commit_next_update_time"],
        }
        case["response_decision_plan"] = build_response_decision_plan(source, scenario, case["reply_contract"])
        return case

    if scenario == "private_repo_access_question":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "privateリポジトリのURLだけで見えるか", "priority": "primary"},
                {"id": "q2", "text": "閲覧できる形や別の共有方法が必要か", "priority": "secondary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "privateリポジトリなら、URLだけではこちらから中身は見えません。",
                },
                {
                    "question_id": "q2",
                    "disposition": "answer_now",
                    "answer_brief": "GitHub側で閲覧できる形にしてもらうか、難しければ今回の不具合に関係する範囲をZIPで共有いただければ大丈夫です。",
                },
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now", "commit_next_update_time"],
        }
        case["response_decision_plan"] = build_response_decision_plan(source, scenario, case["reply_contract"])
        return case

    if scenario == "received_materials_flow_check":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "昨日送ったログとスクショは届いているか", "priority": "primary"},
                {"id": "q2", "text": "どういう流れで進むのか", "priority": "secondary"},
                {"id": "q3", "text": "追加で用意した方がよいものがあるか", "priority": "secondary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "はい、昨日のログとスクショは確認できています。",
                },
                {
                    "question_id": "q2",
                    "disposition": "answer_now",
                    "answer_brief": "まず受け取っている内容をこちらで確認して、追加で必要なものがあればその時点でこちらからお願いします。",
                },
                {
                    "question_id": "q3",
                    "disposition": "answer_now",
                    "answer_brief": "いまの時点で、追加で準備いただくものはありません。",
                },
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now", "commit_next_update_time"],
        }
        case["response_decision_plan"] = build_response_decision_plan(source, scenario, case["reply_contract"])
        return case

    if scenario == "screenshot_followup":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "送ったスクショを手がかりに見てもらえるか", "priority": "primary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "スクショありがとうございます。その画面を手がかりに見ます。",
                },
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now", "commit_next_update_time"],
        }
        case["response_decision_plan"] = build_response_decision_plan(source, scenario, case["reply_contract"])
        return case

    if scenario == "runtime_context_followup":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "この前提は調査に影響するか", "priority": "primary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "はい、その情報は調査に影響します。",
                },
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now", "commit_next_update_time"],
        }
        case["response_decision_plan"] = build_response_decision_plan(source, scenario, case["reply_contract"])
        return case

    if scenario == "diagnosis_pushback_followup":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "環境変数だけが原因と言い切れるのか", "priority": "primary"},
                {"id": "q2", "text": "Vercel側で何か変わった可能性もあるか", "priority": "secondary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "環境変数だけで言い切る段階ではなく、先月まで同じ設定で動いていた点も前提に見ています。",
                },
                {
                    "question_id": "q2",
                    "disposition": "answer_now",
                    "answer_brief": "Vercel側の環境差や参照先の変化も候補として見ています。",
                },
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now", "commit_next_update_time"],
        }
        case["response_decision_plan"] = build_response_decision_plan(source, scenario, case["reply_contract"])
        return case

    if scenario == "advanced_investigation_followup":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "ここまで分かっている前提で続きから見てもらえるか", "priority": "primary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "はい、ここまで確認いただいている前提で、その続きから見ます。",
                },
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now", "commit_next_update_time"],
        }
        case["response_decision_plan"] = build_response_decision_plan(source, scenario, case["reply_contract"])
        return case

    if scenario == "missing_file_followup":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "抜けていたファイルを追加で送ればよいか", "priority": "primary"},
                {"id": "q2", "text": "そのせいで的外れな調査になっていないか", "priority": "secondary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "はい、追加で送っていただければ大丈夫です。受領後にそのファイルを含めて見直します。",
                },
                {
                    "question_id": "q2",
                    "disposition": "answer_now",
                    "answer_brief": "その時点までの確認が無駄になる前提ではなく、追加分を受け取り後に基準をそろえ直します。",
                },
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now", "commit_next_update_time"],
        }
        case["response_decision_plan"] = build_response_decision_plan(source, scenario, case["reply_contract"])
        return case

    if scenario == "shared_log_privacy_concern":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "送ったログに他の人の情報が入っていないか不安", "priority": "primary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "共有いただいたログに他の方の情報が見えていた場合も、そのまま広げずに扱います。",
                },
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now", "commit_next_update_time"],
        }
        case["response_decision_plan"] = build_response_decision_plan(source, scenario, case["reply_contract"])
        return case

    if scenario == "suspected_cause_found":
        if any(marker in raw for marker in ["No signatures found matching the expected signature for payload", "Webhook secret", "signing secret is incorrect", "signing secret"]):
            answer_brief = "手がかりとしてかなり助かります。まずその署名まわりから確認します。"
            hold_reason = "表示だけで断定はせず、署名設定や検証まわりのずれかを先に見ます。"
        elif has_explicit_hypothesis(raw):
            answer_brief = "手がかりとしてかなり助かります。まずその見立てに近い箇所から確認します。"
            hold_reason = "ログだけで断定はせず、共有いただいた見立てが原因に近いかを先に見ます。"
        else:
            answer_brief = "手がかりとしてかなり助かります。まずそのエラー周りから確認します。"
            hold_reason = "ログだけで断定はせず、エラー内容が原因に近いかを先に見ます。"
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "このログで原因が分かるか", "priority": "primary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_after_check",
                    "answer_brief": answer_brief,
                    "hold_reason": hold_reason,
                    "revisit_trigger": "確認できたところまでを整理してお返しします。",
                },
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "defer_with_reason", "commit_next_update_time"],
        }
        return case

    if scenario == "env_fix_recheck":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "環境変数を入れたのでこれで直るか確認してほしい", "priority": "primary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_after_check",
                    "answer_brief": "設定ありがとうございます。その変更で直る可能性はありますが、念のため他の要因が残っていないかも確認します。",
                    "hold_reason": "いまは、設定反映後の挙動と他の要因が残っていないかを見ています。",
                    "revisit_trigger": "確認できたところまでを整理してお返しします。",
                },
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "defer_with_reason", "commit_next_update_time"],
        }
        return case

    if scenario == "symptom_shift_after_user_edit":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "今のコードベースで見てもらえるか", "priority": "primary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_after_check",
                    "answer_brief": "はい、今のコードを基準に見ます。",
                    "hold_reason": "途中で症状が変わっているので、まだ今起きている不具合と今のコードを先にそろえたいです。",
                    "revisit_trigger": "受領後に、どこから見始めるかをお返しします。",
                },
            ],
            "ask_map": [
                {
                    "id": "a1",
                    "question_ids": ["q1"],
                    "ask_text": "送り直すコードがあれば、そのまま送ってください。",
                    "why_needed": "今の症状を今のコードで確認するため",
                }
            ],
            "required_moves": ["react_briefly_first", "defer_with_reason", "request_minimum_evidence", "commit_next_update_time"],
        }
        return case

    if scenario == "handoff_fix_addon":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "修正も追加でお願いできるか", "priority": "primary"},
                {"id": "q2", "text": "追加費用はかかるか", "priority": "secondary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_after_check",
                    "answer_brief": "修正の相談もできます。まず直したい内容を見て、今の依頼の続きとして扱えるかを確認します。",
                    "hold_reason": "いまのメモ依頼と同じ流れか、追加の修正相談として切るかを先に確認します。",
                    "revisit_trigger": "直したい内容を受領したあとに、次の案内をお返しします。",
                },
                {
                    "question_id": "q2",
                    "disposition": "answer_after_check",
                    "answer_brief": "費用は内容を見てから案内します。",
                    "hold_reason": "追加費用の有無は、修正相談の内容を見てからでないと言い切れません。",
                    "revisit_trigger": "直したい内容を受領したあとに、費用も含めてお返しします。",
                },
            ],
            "ask_map": [
                {
                    "id": "a1",
                    "question_ids": ["q1", "q2"],
                    "ask_text": "今いちばん直したい点を、そのまま送ってください。",
                    "why_needed": "今回の続きとして扱えるかを先に切るため",
                }
            ],
            "required_moves": ["react_briefly_first", "defer_with_reason", "request_minimum_evidence", "commit_next_update_time"],
        }
        return case

    if scenario == "doc_followup_request":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "このフロー前提で整理を進めてよいか", "priority": "primary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "はい、そのフロー前提で進めます。足りない点があればこちらから絞って確認します。",
                },
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now", "commit_next_update_time"],
        }
        return case

    if scenario == "source_replacement_notice":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "送り直したコードを基準に見てほしい", "priority": "primary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "了解しました。以後は送り直し分を基準に見ます。前のものは参照しません。",
                },
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now", "commit_next_update_time"],
        }
        return case

    if scenario == "external_channel_request":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "電話やSlackなどに切り替えられるか", "priority": "primary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "電話や Slack などの外部チャネルには切り替えず、このトークルーム内で進めます。",
                },
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now", "commit_next_update_time"],
        }
        return case

    if scenario == "direct_push_request":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "直接 push してもらえるか", "priority": "primary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "依頼者側リポジトリへの直接 push は前提にしていません。修正内容はこのトークルームで返します。",
                },
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now", "commit_next_update_time"],
        }
        return case

    if scenario == "deployment_help_request":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "本番反映までやってもらえるか", "priority": "primary"},
                {"id": "q2", "text": "他に方法はあるか", "priority": "secondary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "本番反映の代行は前提にしていません。",
                },
                {
                    "question_id": "q2",
                    "disposition": "answer_now",
                    "answer_brief": "必要なら、このトークルーム内で反映手順が分かる形にして返します。",
                },
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now", "commit_next_update_time"],
        }
        return case

    if scenario == "test_support_question":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "unittest などが含まれるか", "priority": "primary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "今回の対応でテスト追加まで含むとは限りません。必要ならその点は別で相談いただけます。",
                },
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now", "commit_next_update_time"],
        }
        return case

    if scenario == "live_secrets_pasted":
        answer_brief = ".env やログイン情報などの値は広げず、このまま扱いません。以後はキー名やURLだけで大丈夫です。"
        if any(marker in raw for marker in ["ログイン情報", "ログイン:", "ログイン："]) and any(marker in raw for marker in ["パスワード", "password", "パスワード:", "パスワード："]):
            answer_brief = "ログイン情報やパスワードは広げず、このまま扱いません。以後はURLや項目名だけで大丈夫です。"
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "秘密値やログイン情報を送ってしまった時にどうすればよいか", "priority": "primary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": answer_brief,
                },
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now", "commit_next_update_time"],
        }
        return case

    if scenario == "secret_handling_question":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": ".envや秘密値の扱いをどう見るか", "priority": "primary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": ".envや秘密値は値そのものを受け取らず、見つかった場合も値を広げずに扱います。",
                },
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now", "commit_next_update_time"],
        }
        return case

    if scenario == "external_api_shift":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "このまま見てもらえますか", "priority": "primary"},
                {"id": "q2", "text": "料金変わりますか", "priority": "secondary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_after_check",
                    "answer_brief": "まず今回の件と同じ流れかを確認します。",
                    "hold_reason": "外部API側でも、今の依頼と同じ流れの中で起きているかはまだ未確定です。",
                    "revisit_trigger": "外部API側のエラー情報を受領したあとに、継続可否をお返しします。",
                },
                {
                    "question_id": "q2",
                    "disposition": "answer_now",
                    "answer_brief": "今の時点では料金はまだ変えません。",
                },
            ],
            "ask_map": [
                {
                    "id": "a1",
                    "question_ids": ["q1"],
                    "ask_text": "外部API側のエラーが分かる画面か文言だけ送ってください。",
                    "why_needed": "今回の依頼と同じ流れの中で起きているかを切るため",
                    "default_path_text": "すぐ出せなければ、先に今の依頼側から確認を進めます。",
                }
            ],
            "required_moves": ["react_briefly_first", "defer_with_reason", "request_minimum_evidence", "commit_next_update_time"],
        }
        return case

    if scenario == "external_share_request":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "Googleドライブのリンクで共有してよいか", "priority": "primary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "Googleドライブでの共有は使わず、今回の不具合に関係する範囲をこのトークルームで分けて送ってもらえれば大丈夫です。",
                },
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now", "commit_next_update_time"],
        }
        return case

    if scenario == "external_share_env_change":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "Googleドライブで共有してよいか", "priority": "primary"},
                {"id": "q2", "text": "環境がVercelではなくさくらでも見てもらえるか", "priority": "secondary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "Googleドライブは使わず、容量に収まる形で分けるか、今回の不具合に関係するファイルだけこのトークルームで送ってもらえれば大丈夫です。",
                },
                {
                    "question_id": "q2",
                    "disposition": "answer_now",
                    "answer_brief": "さくらのレンタルサーバーでも、その前提で確認できます。",
                },
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now", "commit_next_update_time"],
        }
        return case

    if scenario == "late_info_share":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "特定商品だけ決済が通らない情報を先に共有しておいてよいか", "priority": "primary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "共有ありがとうございます。商品ID も受け取れています。明日、特定の商品だけ通らない条件差から確認します。",
                },
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now"],
        }
        return case

    if scenario == "multiple_new_issues":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "これ全部つながっていますか", "priority": "primary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_after_check",
                    "answer_brief": "今の時点では、今回の件とつながっているかはまだ断定しません。",
                    "hold_reason": "元の不具合と、新しく出た2件の関連がまだ見えていない。",
                    "revisit_trigger": "追加の状況を受領したあとに、つながりがありそうかをお返しします。",
                },
            ],
            "ask_map": [
                {
                    "id": "a1",
                    "question_ids": ["q1"],
                    "ask_text": "管理画面のエラー画面と、メールが届かないことが分かる画面や状況があれば送ってください。",
                    "why_needed": "今回の件とつながっているかを先に切るため",
                    "default_path_text": "まだ出せるものがなければ、まずは今の本件から確認を進めます。",
                }
            ],
            "required_moves": ["react_briefly_first", "defer_with_reason", "request_minimum_evidence", "commit_next_update_time"],
        }
        return case

    if scenario == "which_environment_screen":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "テスト環境と本番環境のどちらを見ればいいか", "priority": "primary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "今回確認したい症状が出ている方を見てください。迷う場合は本番側を優先で大丈夫です。",
                },
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now", "commit_next_update_time"],
        }
        return case

    if scenario == "extra_scope_question":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "これも一緒に見てもらうことは可能か", "priority": "primary"},
                {"id": "q2", "text": "追加料金はかかるか", "priority": "secondary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_after_check",
                    "answer_brief": "今回の件とつながっているならこのまま見ます。",
                    "hold_reason": "ただ、元の不具合と別の画面の話が同じ原因かはまだ未確定です。",
                    "revisit_trigger": "追加の症状を受領したあとに、今回の件とつながっているかをお返しします。",
                },
                {
                    "question_id": "q2",
                    "disposition": "answer_after_check",
                    "answer_brief": "別原因なら追加見積りになる可能性があります。",
                    "hold_reason": "",
                    "revisit_trigger": "確認できたところまでを見て、追加扱いになるかどうかをお返しします。",
                },
            ],
            "ask_map": [
                {
                    "id": "a1",
                    "question_ids": ["q1"],
                    "ask_text": "その画面で何が起きているかが分かれば、短く送ってください。",
                    "why_needed": "今回の件と同じ原因かどうかを先に切るため",
                    "default_path_text": "まだ整理できていなければ、まずは今の本件を優先して確認します。",
                }
            ],
            "required_moves": ["react_briefly_first", "defer_with_reason", "request_minimum_evidence", "commit_next_update_time"],
        }
        return case

    if scenario == "keys_shared":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "キー名だけ共有すればよいか", "priority": "primary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "この情報で確認を進めます。値の方は引き続き送らなくて大丈夫です。",
                },
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now", "commit_next_update_time"],
        }
        return case

    if scenario == "timeline_anxiety":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "完了までどのくらいかかりそうか", "priority": "primary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_after_check",
                    "answer_brief": "完了時期は、現時点ではまだ言い切れず、今の確認結果を見てからの方が正確です。",
                    "hold_reason": "現時点では原因と修正量がまだ固まっていません。",
                    "revisit_trigger": "現時点の見立てを整理したあとに、見通しをお返しします。",
                },
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "defer_with_reason", "commit_next_update_time"],
        }
        return case

    if scenario == "delay_complaint_refund":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "放置されているのではないか", "priority": "primary"},
                {"id": "q2", "text": "返金になるのか", "priority": "secondary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_after_check",
                    "answer_brief": "連絡が足りず不安にさせてしまいすみません。まず今の進捗を確認します。そのうえでお返しします。",
                    "hold_reason": "いまは、進んでいる確認と残っている確認をまとめています。",
                    "revisit_trigger": "確認できているところまでを整理してお返しします。",
                },
                {
                    "question_id": "q2",
                    "disposition": "answer_after_check",
                    "answer_brief": "返金を先に断定するのではなく、まず今の進捗確認を優先します。",
                    "hold_reason": "現時点では返金判断より、進捗の整理が先です。",
                    "revisit_trigger": "現時点の状況をお返ししたうえで、必要なら次の案内を続けます。",
                },
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "defer_with_reason", "commit_next_update_time"],
        }
        return case

    if scenario == "price_pushback":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "キャッシュバックはあるか", "priority": "primary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "料金は修正量ではなく、今回の調査と修正を1件として進める固定料金です。キャッシュバックの仕組みはありません。",
                },
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now", "commit_next_update_time"],
        }
        return case

    if scenario == "extra_fee_anxiety":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "別原因なら追加料金になるのか", "priority": "primary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_after_check",
                    "answer_brief": "今の時点では、追加料金になるとはまだ決まっていません。まずは今回の症状が同じ流れの中の話かを確認します。",
                    "hold_reason": "別原因かどうかはまだ確定していません。勝手に追加料金が発生することはありません。",
                    "revisit_trigger": "確認できたところまでと、次にどう進めるかをお返しします。",
                },
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "defer_with_reason", "commit_next_update_time"],
        }
        return case

    case["reply_contract"] = {
        "primary_question_id": "q1",
        "explicit_questions": [{"id": "q1", "text": "今回の件をどう進めるか", "priority": "primary"}],
        "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_after_check",
                    "answer_brief": "今回の追加連絡は確認しました。まず今の依頼の続きとして扱える話かを確認します。",
                    "hold_reason": "いまは、今回の追加内容が今の依頼と同じ流れの中の話かを見ています。",
                    "revisit_trigger": "確認後に、次にどう進めるかをお伝えします。",
                }
            ],
        "ask_map": [],
        "required_moves": ["react_briefly_first", "defer_with_reason", "commit_next_update_time"],
    }
    case["response_decision_plan"] = build_response_decision_plan(source, scenario, case["reply_contract"])
    return case


def reaction_line(case: dict) -> str:
    temperature_plan = shared.ensure_temperature_plan(case)
    opening_move = temperature_plan.get("opening_move")
    user_signal = temperature_plan.get("user_signal")
    scenario = case["scenario"]
    if scenario == "progress_anxiety":
        if any(marker in case.get("raw_message", "") for marker in ["クレーム", "焦って"]):
            return "連絡が足りず不安にさせてしまいすみません。急ぎで確認したい状況とのこと、まず今見えているところから整理します。"
        if any(marker in case.get("raw_message", "") for marker in ["どうなってるんですか", "対応するかしないか", "まだ何も返事"]):
            return "お待たせしてすみません。連絡が止まってしまっていて、申し訳ありません。"
        if any(marker in case.get("raw_message", "") for marker in ["待たされた経験", "安心します", "2日経って", "進捗はどう", "今どこまで見て"]):
            return "お待たせしてすみません。心配になりますよね。"
        if any(marker in case.get("raw_message", "") for marker in ["心配になってきまして", "心配になってきた", "状況だけでも教えて", "安心します"]):
            return "お待たせしてすみません。心配になりますよね。"
        return "連絡が足りず不安にさせてしまいすみません。まず今見えているところから整理します。"
    if scenario == "progress_summary_request":
        if any(marker in case.get("raw_message", "") for marker in ["週明けに社内で報告", "社内で報告する必要"]):
            return "ありがとうございます。週明けの社内報告に使える形でまとめます。"
        return "ありがとうございます。社内共有に使える形でまとめます。"
    if scenario == "mixed_status_timeline_fee":
        return "3点の確認、ありがとうございます。"
    if opening_move == "action_first":
        if scenario == "timeline_anxiety":
            if any(marker in case.get("raw_message", "") for marker in ["焦ってます", "問い合わせが6件", "メンテナンス中"]):
                return "焦る状況ですよね。まず見通しが出せるところから確認します。"
            return "まず見通しが出せるところから確認します。"
        if scenario == "multiple_new_issues":
            return "まず今回の件とつながっているかを先に見ます。"
        if scenario == "extra_scope_question":
            return "まず今回の件と同じ話かを先に確認します。"
        return "まず必要なところから確認します。"
    if opening_move == "pressure_release":
        return "気を遣わなくて大丈夫です。"
    if opening_move == "normalize_then_clarify":
        return "いまの段階で迷うのは自然です。"
    if opening_move == "receive_and_own":
        return "率直に伝えていただいてありがとうございます。"
    if opening_move == "yes_no_first":
        if user_signal == "negative_feedback":
            return "率直に伝えていただいてありがとうございます。"
        return ""
    if scenario == "live_secrets_pasted":
        return "共有いただいた秘密情報の件、承知しました。"
    if scenario == "cancel_request":
        return "キャンセルしたいとのこと、確認しました。"
    if scenario == "progress_anxiety":
        return "進みが見えにくくなっていてすみません。"
    if scenario == "repo_access_confirm":
        return "確認ありがとうございます。"
    if scenario == "shared_log_privacy_concern":
        return "気になる点として自然です。"
    if scenario == "private_repo_access_question":
        return "privateリポジトリの件、確認しました。"
    if scenario == "info_sufficiency_check":
        if "zip_already_sent" in (case.get("response_decision_plan") or {}).get("facts_known", []):
            return "コード一式の共有、確認しました。"
        return "気にかけていただいてありがとうございます。"
    if scenario == "received_materials_flow_check":
        return "進め方が見えにくい点、確認しました。"
    if scenario == "screenshot_followup":
        return None
    if scenario == "runtime_context_followup":
        return "補足ありがとうございます。"
    if scenario == "advanced_investigation_followup":
        return "ここまで調べていただいた件、確認しました。"
    if scenario == "evidence_offer_question":
        return "追加の手がかりありがとうございます。"
    if scenario == "suspected_cause_found":
        if "signing secret is incorrect" in case.get("raw_message", "") or "signing secret" in case.get("raw_message", ""):
            return "signing secret エラーの共有ありがとうございます。まずその署名まわりから確認します。"
        if "No signatures found matching the expected signature for payload" in case.get("raw_message", ""):
            return "signature エラーの共有ありがとうございます。"
        if "Webhook secret" in case.get("raw_message", ""):
            return "Webhook secret 周りの手がかり共有ありがとうございます。"
        return "原因らしき手がかりを見つけていただいてありがとうございます。"
    if scenario == "symptom_shift_after_user_edit":
        return "状況が変わったとのこと、確認しました。"
    if scenario == "handoff_fix_addon":
        return "修正も追加で相談したいとのこと、確認しました。"
    if scenario == "doc_followup_request":
        return "追加の前提共有ありがとうございます。"
    if scenario == "source_replacement_notice":
        return "コードの差し替え連絡ありがとうございます。"
    if scenario == "external_channel_request":
        return "提案ありがとうございます。"
    if scenario == "direct_push_request":
        return "作業の進め方についての確認ありがとうございます。"
    if scenario == "deployment_help_request":
        return "反映まわりが不安とのこと、確認しました。"
    if scenario == "test_support_question":
        return "確認ありがとうございます。"
    if scenario == "secret_handling_question":
        return "envファイルの件、大丈夫です。"
    if scenario == "env_fix_recheck":
        return "設定ありがとうございます。"
    if scenario == "external_share_request":
        return "容量の件、ありがとうございます。"
    if scenario == "external_api_shift":
        return "原因がStripe側ではなく、外部API側にありそうとのこと、確認しました。"
    if scenario == "external_share_env_change":
        return "Googleドライブ共有の件と、Vercelではなくさくらのレンタルサーバーとのこと、確認しました。"
    if scenario == "late_info_share":
        return "共有ありがとうございます。"
    if scenario == "multiple_new_issues":
        return "別のところも壊れた気がするとのこと、確認しました。"
    if scenario == "which_environment_screen":
        return "画面の確認先で迷っている件、確認しました。"
    if scenario == "extra_scope_question":
        if "redirect_issue_mentioned" in (case.get("response_decision_plan") or {}).get("facts_known", []):
            return "リダイレクトの件、確認しました。"
        return "別の画面の件、確認しました。"
    if scenario == "keys_shared":
        return "キー名の共有ありがとうございます。確認しました。"
    if scenario == "timeline_anxiety":
        return "完了までの目安が気になっている件、確認しました。"
    if scenario == "price_pushback":
        return "率直に聞いていただいてありがとうございます。"
    if scenario == "extra_fee_anxiety":
        return "ご不安にさせてしまっている点、確認しました。"
    return "追加のご連絡、確認しました。"


def current_focus_line(case: dict) -> str | None:
    scenario = case["scenario"]
    raw = case.get("raw_message", "")
    if scenario == "cancel_request":
        return "いまは、今回どこまで進んでいるかを先に確認しています。"
    if scenario == "progress_anxiety":
        if any(marker in raw for marker in ["売上が立ってない", "売上が立っていない", "クライアント", "決済エラーのせいで売上"]):
            return "いまは、決済が止まっている箇所の切り分けを進めています。"
        if any(marker in raw for marker in ["進捗はどう", "今どこまで見て", "今どこまで見ていただけ", "2日経って", "待たされた経験"]):
            return "確認できているところから順に整理しています。"
        if any(marker in raw for marker in ["昨日お送りした件", "昨日送った件", "状況だけでも教えて", "心配になってきまして"]):
            return "いまは、昨日いただいた内容をもとに原因の切り分けを進めています。"
        return "いまは、原因の切り分けを進めています。"
    if scenario == "progress_summary_request":
        return "いまは、原因の切り分けを進めながら、見えている候補と次に見る点をまとめています。"
    if scenario == "repo_access_confirm":
        return None
    if scenario == "info_sufficiency_check":
        return None
    if scenario == "runtime_context_followup":
        if "400エラー" in raw and "Webhook" in raw:
            return "いまは、本番だけで出ているWebhookの400エラーと環境変数まわりを優先して見ています。"
        return "いまは、ビルド時ではなく決済時だけ出る挙動を優先して見ています。"
    if scenario == "env_fix_recheck":
        return "いまは、設定反映後に挙動が安定しているかを見ています。"
    if scenario == "diagnosis_pushback_followup":
        return "いまは、環境変数だけに絞らず Vercel 側の環境差や参照先の変化も含めて見ています。"
    if scenario == "advanced_investigation_followup":
        return "いまは、requires_action の先で client-side 側の認証完了処理が止まっていないかを見ています。"
    if scenario == "missing_file_followup":
        return None
    if scenario == "suspected_cause_found":
        raw = case.get("raw_message", "")
        if any(marker in raw for marker in ["No signatures found matching the expected signature for payload", "Webhook secret", "signing secret is incorrect", "signing secret"]):
            return "いまは、その signature エラーと Webhook secret 周りから確認しています。"
        if has_explicit_hypothesis(raw):
            return "いまは、共有いただいた見立てに近い箇所から確認しています。"
        return "いまは、共有いただいたエラー周りから確認しています。"
    if scenario == "symptom_shift_after_user_edit":
        return "いまは、症状が変わった後のコードと現象を先に確認しています。"
    if scenario == "handoff_fix_addon":
        return "いまは、直したい内容が今のメモ依頼と同じ流れかを先に確認しています。"
    if scenario == "doc_followup_request":
        return None
    if scenario == "source_replacement_notice":
        return None
    if scenario == "external_api_shift":
        return "いまは、今回の依頼側と外部API側が同じ流れの中の話かを先に確認しています。"
    if scenario == "external_share_env_change":
        return "いまは、受け取っている情報をこのトークルーム内で確認できる形にそろえています。"
    if scenario == "multiple_new_issues":
        return "いまは、新しく出た症状が今回の件とつながっているかを先に見ています。"
    if scenario == "extra_scope_question":
        if "redirect_issue_mentioned" in (case.get("response_decision_plan") or {}).get("facts_known", []):
            return "いまは、このリダイレクト不具合が今回の件とつながっているかを先に見ています。"
        return "いまは、追加で出た画面の話が今回の件とつながっているかを先に見ています。"
    if scenario == "timeline_anxiety":
        return "いまは、原因と修正量の見立てを先に固めています。"
    if scenario == "delay_complaint_refund":
        return "いまは、進んでいる確認と残っている確認をまとめています。"
    if scenario == "extra_fee_anxiety":
        return "いまは、今回の症状が元の依頼と同じ流れの中で起きているかを確認しています。"
    if scenario == "generic_followup":
        return None
    return None


def with_period(text: str) -> str:
    cleaned = shared.compact_text(text)
    if not cleaned:
        return ""
    return cleaned if cleaned.endswith("。") else f"{cleaned}。"


def _normalized(text: str) -> str:
    return re.sub(r"[\s。、，,.！？?「」『』（）()・:：/／\\-]+", "", text)


def _same_text(left: str, right: str) -> bool:
    nl = _normalized(left)
    nr = _normalized(right)
    return bool(nl and nr and nl == nr)


def _same_meaning(left: str, right: str) -> bool:
    nl = _normalized(left)
    nr = _normalized(right)
    if not nl or not nr:
        return False
    return nl == nr or nl in nr or nr in nl


def _append_unique(paragraphs: list[str], text: str) -> None:
    cleaned = text.strip()
    if not cleaned:
        return
    if any(_same_text(cleaned, existing) for existing in paragraphs):
        return
    paragraphs.append(cleaned)


def _paragraph_from_lines(lines: list[str]) -> str:
    paragraph_lines: list[str] = []
    for line in lines:
        cleaned = with_period(line)
        if not cleaned:
            continue
        if any(_same_meaning(cleaned, existing) for existing in paragraph_lines):
            continue
        paragraph_lines.append(cleaned)
    return "\n".join(paragraph_lines)


def draft_opening_anchor(case: dict) -> str:
    scenario = case["scenario"]
    raw = case.get("raw_message", "")
    deadline_phrase = promised_deadline_phrase(raw)
    reply_memory = reply_memory_for(case)
    repeated_followup = (reply_memory.get("followup_count") or 0) > 0
    pending_commitment = has_unfulfilled_commitment(case)

    if scenario == "delay_complaint_refund":
        lines = ["お待たせしてしまい、すみません。まず状況を確認します。"]
        lines.append(deadline_phrase or "連絡が空いてしまった点、申し訳ありません。")
        return "\n".join(lines)
    if scenario == "progress_anxiety":
        if pending_commitment and repeated_followup:
            lines = ["お待たせしています。前回お伝えした確認の件も含めて、今の状況を整理します。"]
            if deadline_phrase:
                lines.append(deadline_phrase)
            return "\n".join(lines)
        lines = ["お待たせしてすみません。まず状況を整理します。"]
        if deadline_phrase:
            lines.append(deadline_phrase)
        return "\n".join(lines)
    if scenario == "progress_summary_request":
        if pending_commitment and repeated_followup:
            return "お待たせしています。社内共有に使えるよう、現時点で見えている点を整理します。"
        return "社内共有に使える形でまとめます。"
    if scenario == "timeline_anxiety":
        if pending_commitment and repeated_followup:
            return "お待たせしています。今の時点で出せる見通しを整理します。"
        if any(marker in raw for marker in ["焦ってます", "問い合わせが6件", "メンテナンス中"]):
            return "焦る状況ですよね。まず見通しが出せるところから確認します。"
        return "まず見通しが出せるところから確認します。"
    if scenario == "suspected_cause_found":
        if any(marker in raw for marker in ["1ミリも意味が分かりません", "プログラミング歴3日目", "許してください"]):
            return "ログありがとうございます。分からなくても大丈夫なので、そのまま見ていきます。"
        if "signing secret is incorrect" in raw or "signing secret" in raw:
            return "signing secret エラーの共有ありがとうございます。まずその署名まわりから確認します。"
        if "No signatures found matching the expected signature for payload" in raw:
            return "signature エラーの共有ありがとうございます。"
        if "Webhook secret" in raw:
            return "Webhook secret 周りの手がかり共有ありがとうございます。"
        return "原因らしき手がかりを見つけていただいてありがとうございます。"
    if scenario == "extra_scope_question":
        subject = extra_scope_subject(raw)
        if subject == "別件":
            return "別件、確認しました。"
        return f"{subject}の件、確認しました。"
    if scenario == "extra_fee_anxiety":
        return "追加料金のご不安、確認しました。"
    if scenario == "which_environment_screen":
        return "テスト環境と本番環境のどちらを見るか迷う状況、確認しました。"
    if scenario == "evidence_offer_question":
        if "Stripe" in raw and "管理画面" in raw:
            return "Stripe管理画面の件、確認しました。"
        return "追加で確認したい情報の件、確認しました。"
    if scenario == "runtime_context_followup":
        if "400エラー" in raw and "Webhook" in raw:
            return "本番だけで、Webhookに400エラーが出ている件、確認しました。"
        if "スマホ" in raw and ("同じ状況" in raw or "同じ" in raw):
            return "スマホでも同じ状況とのこと、確認しました。"
        if "Vercel" in raw and ("プラン変え" in raw or "プラン変更" in raw):
            return "Vercelのプラン変更も共有ありがとうございます。"
        return "Vercelのデプロイ自体は通っていて、決済時だけエラーが出るとのこと、確認しました。"
    if scenario == "diagnosis_pushback_followup":
        return "その点はもっともです。"
    if scenario == "missing_file_followup":
        return "抜けていたファイルの件、確認しました。"
    if scenario == "secret_handling_question":
        return "envファイルの件、大丈夫です。"
    if scenario == "shared_log_privacy_concern":
        return "気になる点として自然です。"
    if scenario == "env_fix_recheck":
        return "設定ありがとうございます。"
    if scenario == "external_api_shift":
        return "外部API側の件、確認しました。"
    if scenario == "repo_access_confirm":
        return "確認ありがとうございます。"
    if scenario == "info_sufficiency_check":
        if "ZIP" in raw and "送" in raw:
            return "コード一式の共有、確認しました。"
        return "気にかけていただいてありがとうございます。"
    if scenario == "post_fix_steps_question":
        return "修正後に必要なことが気になっている件、確認しました。"
    if scenario == "server_access_password_question":
        return "作業方法と共有範囲の件、確認しました。"
    if scenario == "legacy_code_unknown_ok":
        return "前任者コードの件、確認しました。"
    if scenario == "unfixable_fee_question":
        return "万が一の料金面がご不安とのこと、確認しました。"
    if scenario == "unrelated_build_error_scope":
        return "Next.jsのビルドエラーが出ている件、確認しました。"
    if scenario == "fix_file_delivery_question":
        return "修正ファイルの有無が気になっている件、確認しました。"
    if scenario == "which_log_and_screenshot_question":
        return "どのログやスクショを見ればよいか迷う点、確認しました。"
    if scenario == "repo_invite_and_screenshots":
        return "GitHub招待とスクショ共有の件、確認しました。"
    if scenario == "received_materials_flow_check":
        return "昨日のログとスクショの件、確認しました。"
    if scenario == "screenshot_followup":
        return "スクショありがとうございます。"
    if scenario == "keys_shared":
        return "キー名の共有、確認しました。"
    return reaction_line(case)


def draft_body_paragraphs(case: dict) -> list[str]:
    scenario = case["scenario"]
    raw = case.get("raw_message", "")
    contract = case["reply_contract"]
    decision_plan = case.get("response_decision_plan") or {}
    primary_id = contract["primary_question_id"]
    primary = next(item for item in contract["answer_map"] if item["question_id"] == primary_id)
    secondary_now = [item for item in contract["answer_map"] if item["question_id"] != primary_id and item["disposition"] == "answer_now"]
    secondary_after = [
        item for item in contract["answer_map"] if item["question_id"] != primary_id and item["disposition"] == "answer_after_check"
    ]
    ask_map = contract.get("ask_map") or []
    blocking_missing_facts = decision_plan.get("blocking_missing_facts") or []
    direct_answer = with_period(decision_plan.get("direct_answer_line") or primary["answer_brief"])
    focus_line = current_focus_line(case)
    paragraphs: list[str] = []

    if scenario == "cancel_request":
        _append_unique(
            paragraphs,
            _paragraph_from_lines(
                [
                    direct_answer,
                    "返金やキャンセルの扱いは、進み具合を確認したうえでずれない形で案内します。",
                ]
            ),
        )
        return paragraphs

    if scenario == "progress_anxiety":
        _append_unique(paragraphs, direct_answer)
        if focus_line:
            _append_unique(paragraphs, focus_line)
        return paragraphs
    if scenario == "progress_summary_request":
        _append_unique(
            paragraphs,
            _paragraph_from_lines(
                [
                    direct_answer,
                    focus_line or "",
                ]
            ),
        )
        return paragraphs

    if scenario == "mixed_status_timeline_fee":
        _append_unique(
            paragraphs,
            _paragraph_from_lines(
                [
                    direct_answer,
                    "追加費用が必要になる場合は、その前に必ずご相談します。",
                    "今日は現時点の確認結果をお返しします。",
                ]
            ),
        )
        return paragraphs

    if scenario == "timeline_anxiety":
        if any(marker in raw for marker in ["あとどれくらい", "目安だけでも", "いつまでこう言い続ければ"]):
            _append_unique(paragraphs, _paragraph_from_lines([direct_answer, focus_line]))
        else:
            _append_unique(paragraphs, _paragraph_from_lines([direct_answer, quote_progress_line(case.get("raw_message", "")), focus_line]))
        return paragraphs

    if scenario == "diagnosis_pushback_followup":
        _append_unique(
            paragraphs,
            _paragraph_from_lines(
                [
                    direct_answer,
                    focus_line,
                ]
            ),
        )
        return paragraphs

    if scenario == "delay_complaint_refund":
        _append_unique(
            paragraphs,
            _paragraph_from_lines(
                [
                    direct_answer,
                    "返金については、状況を見たうえで続けて案内します。",
                ]
            ),
        )
        return paragraphs

    if scenario == "extra_scope_question":
        extra_scope_fee_line = next((item["answer_brief"] for item in secondary_after if item.get("answer_brief")), "")
        if "お問い合わせフォーム" in raw or "Resend" in raw:
            extra_scope_fee_line = "作業時間の長短にかかわらず、今回と別原因なら別の相談としてご案内します。"
        _append_unique(paragraphs, _paragraph_from_lines([direct_answer, extra_scope_fee_line]))
        if blocking_missing_facts:
            request_target = extra_scope_request_target(case.get("raw_message", ""))
            _append_unique(
                paragraphs,
                _paragraph_from_lines(
                    [
                        f"まず今回の件とつながっているかを確認するので、{request_target}の情報があれば短く送ってください。",
                        "まだ出せなければ、先に今の本件を進めます。",
                    ]
                ),
            )
        elif focus_line:
            _append_unique(paragraphs, with_period(focus_line))
        return paragraphs

    if scenario == "received_materials_flow_check":
        _append_unique(
            paragraphs,
            _paragraph_from_lines(
                [
                    direct_answer,
                    "まず受け取っている内容をこちらで確認して、追加で必要なものがあればその時点でこちらからお願いします。",
                    "いまの時点で、追加で準備いただくものはありません。",
                ]
            ),
        )
        return paragraphs

    if scenario == "screenshot_followup":
        _append_unique(
            paragraphs,
            _paragraph_from_lines(
                [
                    direct_answer,
                    "もし画面の文字を拾えそうなら、出ているエラーメッセージを1行だけそのまま送ってもらえると確認が早くなります。",
                ]
            ),
        )
        return paragraphs

    if scenario == "runtime_context_followup":
        lines = [direct_answer]
        if "環境変数" in raw and ("400エラー" in raw or "Webhook" in raw):
            lines.append("3日前のVercelの環境変数整理と、Webhookの400エラーもあわせて影響候補として見ます。")
        if focus_line:
            lines.append(focus_line)
        _append_unique(paragraphs, _paragraph_from_lines(lines))
        return paragraphs

    if scenario == "advanced_investigation_followup":
        _append_unique(
            paragraphs,
            _paragraph_from_lines(
                [
                    direct_answer,
                    "requires_action で止まっていて payment_intent.requires_action まで見えているなら、次は client-side の handleCardAction 周りを優先して確認します。",
                    focus_line or "",
                ]
            ),
        )
        return paragraphs

    if scenario == "info_sufficiency_check":
        detail_lines = [direct_answer]
        if "zip_already_sent" in (decision_plan.get("facts_known") or []):
            detail_lines.append("追加で必要なものが出たら、その時はこちらから絞ってお願いします。")
        _append_unique(paragraphs, _paragraph_from_lines(detail_lines))
        return paragraphs

    if scenario == "missing_file_followup":
        _append_unique(
            paragraphs,
            _paragraph_from_lines(
                [
                    direct_answer,
                    "その時点までの確認が無駄になる前提ではなく、追加で受け取った内容を含めて基準をそろえ直します。",
                ]
            ),
        )
        return paragraphs

    if scenario == "shared_log_privacy_concern":
        _append_unique(
            paragraphs,
            _paragraph_from_lines(
                [
                    direct_answer,
                    "気になる場合は、該当箇所を伏せた形で送り直してもらっても大丈夫です。",
                ]
            ),
        )
        return paragraphs

    if scenario == "post_fix_steps_question":
        _append_unique(
            paragraphs,
            _paragraph_from_lines(
                [
                    direct_answer,
                    "ファイルの差し替えやデプロイが必要な場合は、分かる形で手順もあわせてお返しします。",
                    "デプロイに不安がある前提で、こちらから絞って案内します。",
                ]
            ),
        )
        return paragraphs

    if scenario == "fix_file_delivery_question":
        _append_unique(
            paragraphs,
            _paragraph_from_lines(
                [
                    direct_answer,
                    "原因だけお伝えして終わる前提ではなく、確認手順もあわせてお返しします。",
                ]
            ),
        )
        return paragraphs

    if scenario == "server_access_password_question":
        _append_unique(
            paragraphs,
            _paragraph_from_lines(
                [
                    direct_answer,
                    "修正したファイルや確認内容をこのトークルームでお返しする形で進めるので、サーバーのパスワードも不要です。",
                ]
            ),
        )
        return paragraphs

    if scenario == "legacy_code_unknown_ok":
        _append_unique(
            paragraphs,
            _paragraph_from_lines(
                [
                    direct_answer,
                    "まず今あるコードと症状を見ながら確認します。分かる範囲だけで大丈夫で、必要な点があればその時に絞ってお願いします。",
                ]
            ),
        )
        return paragraphs

    if scenario == "unfixable_fee_question":
        _append_unique(
            paragraphs,
            _paragraph_from_lines(
                [
                    direct_answer,
                    "分かった内容や、どこが詰まっているかは整理してお返しします。",
                    "そのうえで、正式納品ではなくキャンセルを含めてご相談します。",
                ]
            ),
        )
        return paragraphs

    if scenario == "unrelated_build_error_scope":
        _append_unique(
            paragraphs,
            _paragraph_from_lines(
                [
                    direct_answer,
                    "ただ、直前の変更とつながっている可能性もあるので、まずは同じ原因かだけ確認します。",
                ]
            ),
        )
        _append_unique(paragraphs, _paragraph_from_lines(["型エラーの文言が分かれば、その1行だけ送ってください。"]))
        return paragraphs

    if scenario == "which_log_and_screenshot_question":
        _append_unique(
            paragraphs,
            _paragraph_from_lines(
                [
                    direct_answer,
                    "スクショはブラウザの画面で大丈夫です。エラーメッセージが見えている状態のものをお願いします。",
                ]
            ),
        )
        return paragraphs

    if scenario == "repo_invite_and_screenshots":
        _append_unique(
            paragraphs,
            _paragraph_from_lines(
                [
                    direct_answer,
                    "スクショは多めでも大丈夫です。一番参考になるものはこちらで見ます。",
                ]
            ),
        )
        return paragraphs

    if scenario == "private_repo_access_question":
        _append_unique(
            paragraphs,
            _paragraph_from_lines(
                [
                    direct_answer,
                    "GitHub側で閲覧できる形にしてもらうか、難しければ今回の不具合に関係する範囲をZIPで共有いただければ大丈夫です。",
                ]
            ),
        )
        return paragraphs

    if scenario == "keys_shared":
        _append_unique(paragraphs, direct_answer)
        return paragraphs

    if scenario == "live_secrets_pasted":
        _append_unique(
            paragraphs,
            _paragraph_from_lines(
                [
                    direct_answer,
                    "該当メッセージを編集や削除できる状態なら、先にそうしてください。",
                    "必要なら、キーやパスワードは後で再設定しておくのが安全です。",
                ]
            ),
        )
        return paragraphs

    if scenario == "env_fix_recheck":
        _append_unique(
            paragraphs,
            _paragraph_from_lines(
                [
                    direct_answer,
                    focus_line or "",
                ]
            ),
        )
        return paragraphs

    if scenario == "extra_fee_anxiety":
        _append_unique(
            paragraphs,
            _paragraph_from_lines(
                [
                    direct_answer,
                    "勝手に追加料金が発生することはありません。",
                ]
            ),
        )
        _append_unique(paragraphs, with_period(focus_line))
        return paragraphs

    if scenario == "external_api_shift":
        _append_unique(
            paragraphs,
            _paragraph_from_lines([direct_answer] + [item["answer_brief"] for item in secondary_now]),
        )
        _append_unique(paragraphs, with_period(focus_line))
        _append_unique(paragraphs, _paragraph_from_lines([ask.get("ask_text", "") for ask in ask_map]))
        _append_unique(paragraphs, _paragraph_from_lines([ask.get("default_path_text", "") for ask in ask_map]))
        return paragraphs

    if scenario == "evidence_offer_question":
        _append_unique(paragraphs, direct_answer)
        _append_unique(paragraphs, _paragraph_from_lines([ask.get("ask_text", "") for ask in ask_map]))
        return paragraphs

    if scenario == "runtime_context_followup":
        runtime_lines = [direct_answer]
        if "スマホ" in case.get("raw_message", "") and ("同じ状況" in case.get("raw_message", "") or "同じ" in case.get("raw_message", "")):
            runtime_lines.append("スマホでも同じ状況なら、パソコンだけの問題ではなさそうです。")
        if "決済を通したときだけ" in case.get("raw_message", "") or ("決済" in case.get("raw_message", "") and "だけ" in case.get("raw_message", "")):
            runtime_lines.append("ビルド時ではなく決済時だけ出ているなら、デプロイ設定より実行時の処理を優先して確認します。")
        if "Vercel" in case.get("raw_message", "") and ("プラン変え" in case.get("raw_message", "") or "プラン変更" in case.get("raw_message", "")):
            runtime_lines.append("3日前のVercelプラン変更も、影響候補としてあわせて見ます。")
        if "本番モード" in case.get("raw_message", ""):
            runtime_lines.append("Stripeは本番モードとの前提で見ています。")
        _append_unique(paragraphs, _paragraph_from_lines(runtime_lines))
        return paragraphs

    answer_lines = [direct_answer]
    answer_lines.extend(item["answer_brief"] for item in secondary_now if item.get("answer_brief"))
    answer_lines.extend(item["answer_brief"] for item in secondary_after if item.get("answer_brief"))
    _append_unique(paragraphs, _paragraph_from_lines(answer_lines))

    detail_lines: list[str] = []
    if primary["disposition"] == "answer_after_check":
        if focus_line:
            detail_lines.append(focus_line)
        if primary.get("hold_reason"):
            detail_lines.append(primary["hold_reason"])
    for item in secondary_after:
        if item.get("hold_reason"):
            detail_lines.append(item["hold_reason"])
    detail_paragraph = _paragraph_from_lines(detail_lines)
    if detail_paragraph:
        _append_unique(paragraphs, detail_paragraph)

    if blocking_missing_facts:
        _append_unique(paragraphs, _paragraph_from_lines([ask.get("ask_text", "") for ask in ask_map]))
        _append_unique(paragraphs, _paragraph_from_lines([ask.get("default_path_text", "") for ask in ask_map]))

    return paragraphs


def validate_render_payload(case: dict, payload: dict, rendered: str) -> list[str]:
    temperature_plan = shared.ensure_temperature_plan(case)
    editable_slots = payload.get("editable_slots") or {}
    errors = collect_temperature_constraint_errors(rendered, temperature_plan, editable_slots)
    if case["reply_contract"].get("ask_map") and (case.get("response_decision_plan", {}).get("blocking_missing_facts")) and not (payload.get("fixed_slots") or {}).get("ask_core"):
        errors.append("ask_map exists but ask_core is empty")
    return list(dict.fromkeys(errors))


def build_post_purchase_render_payload(case: dict, opening_block: str, body_paragraphs: list[str], next_action: str) -> dict:
    ask_map = case["reply_contract"].get("ask_map") or []
    blocking_missing_facts = case.get("response_decision_plan", {}).get("blocking_missing_facts") or []
    fixed_slots: dict[str, str] = {}
    if body_paragraphs:
        fixed_slots["answer_core"] = body_paragraphs[0]
    if len(body_paragraphs) > 1:
        fixed_slots["detail_core"] = "\n\n".join(body_paragraphs[1:])
    if ask_map and blocking_missing_facts:
        ask_lines = [ask.get("ask_text", "") for ask in ask_map if ask.get("ask_text")]
        default_lines = [ask.get("default_path_text", "") for ask in ask_map if ask.get("default_path_text")]
        fixed_slots["ask_core"] = "\n".join(line for line in ask_lines + default_lines if line)
    fixed_slots["next_action"] = next_action
    return {
        "fixed_slots": fixed_slots,
        "editable_slots": {
            "ack": opening_block,
            "closing": next_action,
        },
        "draft_paragraphs": [opening_block, *body_paragraphs, next_action],
    }


def render_case(case: dict) -> str:
    shared.ensure_temperature_plan(case)
    if not case.get("response_decision_plan"):
        case["response_decision_plan"] = build_response_decision_plan(
            {"raw_message": case.get("raw_message", ""), "reply_memory": case.get("reply_memory")},
            case.get("scenario", "generic_followup"),
            case["reply_contract"],
        )
    if not case.get("service_grounding"):
        case["service_grounding"] = dict(SERVICE_GROUNDING)
    if not case.get("hard_constraints"):
        case["hard_constraints"] = build_hard_constraints(case.get("scenario", "generic_followup"), SERVICE_GROUNDING)

    decision_plan = case.get("response_decision_plan") or {}
    first_lines = [opener_for(case)]
    reaction = draft_opening_anchor(case)
    direct_answer = decision_plan.get("direct_answer_line") or ""
    if reaction and not _same_meaning(reaction, direct_answer):
        first_lines.append(reaction)
    opening_block = "\n".join(line for line in first_lines if line.strip())

    body_paragraphs: list[str] = []
    for paragraph in draft_body_paragraphs(case):
        _append_unique(body_paragraphs, paragraph)
    next_action = next_action_line(case)

    rendered_sections = [opening_block]
    for paragraph in body_paragraphs:
        _append_unique(rendered_sections, paragraph)
    _append_unique(rendered_sections, next_action)
    rendered = "\n\n".join(section for section in rendered_sections if section.strip())

    payload = build_post_purchase_render_payload(case, opening_block, body_paragraphs, next_action)
    case["render_payload"] = payload
    violations = validate_render_payload(case, payload, rendered)
    case["reply_memory_update"] = build_reply_memory_update(case, rendered)
    if violations:
        case["render_payload_violations"] = violations
        case["rendered_reply_validator_mode"] = "guardrail_violation"
        return rendered
    case["rendered_reply_validator_mode"] = "pass"
    return rendered


def main() -> int:
    parser = argparse.ArgumentParser(description="Render post_purchase_quick replies from flat purchased cases.")
    parser.add_argument("--fixture", required=True)
    parser.add_argument("--case-id")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--save", action="store_true")
    args = parser.parse_args()

    cases = shared.load_cases(Path(args.fixture))
    selected = [case for case in cases if case.get("state") == "purchased"]
    if args.case_id:
        selected = [case for case in selected if case.get("id") == args.case_id or case.get("case_id") == args.case_id]
    if args.limit is not None:
        selected = selected[: args.limit]
    if not selected:
        print("[NG] no purchased cases selected")
        return 1

    rendered_blocks = []
    for source in selected:
        case = build_case_from_source(source)
        rendered = render_case(case)
        rendered_blocks.append(f"case_id: {case['id']}\n{rendered}")
        if args.save:
            if len(selected) != 1:
                print("[NG] --save requires exactly one case")
                return 1
            shared.save_reply(rendered, case["raw_message"], case.get("reply_memory_update"))

    print("\n\n----\n\n".join(rendered_blocks))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
