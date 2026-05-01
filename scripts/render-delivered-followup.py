#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import re
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml
from reply_quality_lint_common import infer_buyer_emotion


ROOT_DIR = Path(__file__).resolve().parents[1]
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
        raise RuntimeError(f"missing public delivered service grounding: {PUBLIC_BUGFIX_SERVICE_ID}")
    if not service.get("public"):
        raise RuntimeError(f"delivered service is not public: {PUBLIC_BUGFIX_SERVICE_ID}")

    facts = shared.load_service_grounding()
    base_price = int(facts.get("base_price") or 15000)
    fee_text = f"{base_price:,}円"
    return {
        "service_id": service.get("service_id"),
        "public_service": bool(service.get("public")),
        "source_of_truth": service.get("source_of_truth"),
        "public_facts_file": facts.get("public_facts_file"),
        "runtime_capability_file": facts.get("runtime_capability_file"),
        "service_pack_root": facts.get("service_pack_root"),
        "display_name": facts.get("display_name") or "",
        "fee_text": fee_text,
        "base_price": base_price,
        "scope_unit": facts.get("scope_unit") or "",
        "talkroom_only_rule": "必要なやり取りはこのトークルーム内で進めます。",
        "same_cause_rule": "同じ原因なら差し戻しの続きとして見ます。別の原因なら、その時点で切り分けて案内します。",
        "deployment_boundary_rule": "本番反映は、ご自身で進めていただく形です。必要なら反映手順が分かる形で返します。",
        "support_window_rule": "補足で答えられる範囲ならこのまま返します。",
        "hard_no": facts.get("hard_no") or [],
    }


SERVICE_GROUNDING = load_service_grounding()


def time_commit(hours: int = 2) -> str:
    now = datetime.now(JST)
    target = now + timedelta(hours=hours)
    return f"{deadline_label(now, target)}{target:%H:%M}までに、確認結果をお返しします。"


def deadline_label(now: datetime, target: datetime) -> str:
    if target.date() == now.date():
        return "本日"
    if target.date() == (now + timedelta(days=1)).date():
        return "明日"
    return f"{target.month}月{target.day}日"


def time_commit_for_scenario(scenario: str, hours: int = 2) -> str:
    now = datetime.now(JST)
    target = now + timedelta(hours=hours)
    label = deadline_label(now, target)
    if scenario == "doc_explanation_request":
        return f"{label}{target:%H:%M}までに、補足説明をお送りします。"
    return f"{label}{target:%H:%M}までに、確認結果をお返しします。"


def is_complaint_like(source: dict, scenario: str | None = None) -> bool:
    raw = source.get("raw_message", "")
    tone = source.get("emotional_tone", "")
    if tone == "complaint_like":
        return True
    if scenario in {"price_complaint", "delivery_scope_mismatch"}:
        return True
    return any(marker in raw for marker in ["期待していた内容と違います", "高い気が", "高かったかも", "モヤモヤ"])


def build_temperature_plan_for_case(source: dict, scenario: str) -> dict:
    raw = source.get("raw_message", "")
    if scenario == "price_complaint":
        plan = shared.build_temperature_plan(source, case_type="after_close")
        plan["opening_move"] = "receive_and_own"
        plan["support_goal"] = "receive_feedback"
        return plan
    if scenario == "side_effect_question" and any(
        marker in raw for marker in ["修正前は問題なかった", "今回の修正が影響", "今回の修正の影響", "修正後に別の問題"]
    ):
        plan = shared.build_temperature_plan(source, case_type="boundary")
        plan["opening_move"] = "receive_and_own"
        plan["support_goal"] = "receive_and_stabilize"
        return plan
    if scenario in {
        "approval_ok",
        "approval_test_method",
        "approval_complete_thanks",
        "success_thanks_only",
        "formal_thanks_only",
        "deliverable_share_permission",
        "backup_diff_request",
        "generic_delivered",
        "delivery_scope_mismatch",
        "same_cause_check",
        "extra_scope_after_delivery",
        "secondary_question_before_acceptance",
        "approval_reassurance_request",
        "acceptance_after_support_question",
        "delivered_can_reject",
        "monthly_support_request",
        "future_breakage_reassurance",
        "cause_explanation_request",
        "doc_to_bugfix_addon",
        "doc_caution_followup",
        "deployment_help_request",
        "future_architecture_question",
        "doc_explanation_request",
        "postdelivery_question_window",
    }:
        return shared.build_temperature_plan(source, case_type="boundary")
    return shared.build_temperature_plan(source, case_type="bugfix")


def opener_for(source: dict) -> str:
    if is_complaint_like(source):
        return ""
    if source.get("scenario") == "secondary_question_before_acceptance":
        return "ご確認ありがとうございます。"
    if source.get("scenario") == "success_thanks_only":
        return ""
    if source.get("scenario") == "formal_thanks_only":
        return ""
    if source.get("scenario") == "dry_complete_close":
        return ""
    if source.get("scenario") == "approval_wait_request":
        return ""
    if source.get("scenario") == "pending_webhook_events":
        return ""
    return "ご連絡ありがとうございます。"


def detect_scenario(source: dict) -> str:
    raw = source.get("raw_message", "")
    note = source.get("note", "")
    service_hint = source.get("service_hint", "")
    combined = f"{raw}\n{note}"

    if "高い気が" in combined or "await が一つ" in combined or "1箇所の修正" in combined:
        return "price_complaint"
    if "価値があったのか" in combined or "モヤモヤ" in combined or "高かったかも" in combined:
        return "price_complaint"
    if "ビルドが通らなくなりました" in combined or "手順通りにやったつもり" in combined:
        return "apply_followup_issue"
    if (
        "承諾はもう少し待って" in combined
        or "正式な承諾" in combined
        or "待ってもらっていいですか" in combined
        or "待ってもらえますか" in combined
        or "確認してから承諾" in combined
        or "確認してからの承諾" in combined
        or "本番で1回だけ確認してから承諾" in combined
        or "考えさせてもらっていい" in combined
        or "少し考えさせて" in combined
        or "ちょっと考えさせて" in combined
    ):
        return "approval_wait_request"
    if (
        any(marker in combined for marker in ["追加料金", "追加がかかる", "発生しませんよね", "先に教えてほしい"])
        and any(marker in combined for marker in ["ちゃんと動いてます", "ちゃんと動いている", "動作確認できました", "修正確認しました"])
    ):
        return "extra_fee_reassurance"
    if (
        any(marker in combined for marker in ["まじで直ってる", "神です", "本当にありがとうございます", "嘘みたい"])
        and any(marker in combined for marker in ["直ってる", "直りました", "直った", "動きました"])
    ):
        return "success_thanks_only"
    if any(marker in combined for marker in ["問題ありません", "以上です"]) and "確認しました" in combined:
        return "dry_complete_close"
    if (
        any(marker in combined for marker in ["半信半疑", "安心しました", "重ねてお礼申し上げます", "ぜひお願いしたい"])
        and any(marker in combined for marker in ["ありがとうございました", "ありがとうございます", "修正していただけて", "ご対応いただき"])
    ):
        return "formal_thanks_only"
    if (
        any(marker in combined for marker in ["Webhookのログ", "Webhookログ"])
        and any(marker in combined for marker in ["自分で見る方法", "自分でも確認", "Stripeのダッシュボード", "ダッシュボード"])
    ):
        return "webhook_log_howto"
    if (
        any(marker in combined for marker in ["signing secret", "署名検証", "ローテーション"])
        and any(marker in combined for marker in ["再発", "再発する可能性", "同じことが再発", "また同じこと"])
    ):
        return "signing_secret_rotation_recurrence"
    if (
        any(marker in combined for marker in ["独学", "勉強するなら", "どのあたりから始める", "少しは直せるようになりたい"])
        and "Stripe" in combined
    ):
        return "light_learning_question"
    if (
        any(marker in combined for marker in ["星5", "レビュー", "レビュー書", "書いていい内容"])
        and any(marker in combined for marker in ["技術的な内容", "書いちゃっても大丈夫", "書いても大丈夫"])
    ):
        return "review_content_question"
    if (
        any(marker in combined for marker in ["問題なく動いています", "問題なく動いてる", "確認できました"])
        and any(marker in combined for marker in ["承諾のボタン", "承諾を押せ", "承諾のボタンを押せば"])
        and any(marker in combined for marker in ["今後また", "また何かあったとき", "またお願いできる", "お願いできるもの"])
    ):
        return "approval_ok_with_future_request"
    if (
        any(marker in combined for marker in ["承諾ボタン", "承諾のボタン", "承諾後", "承諾した後", "承諾を押した後", "承諾してしまって"])
        and any(marker in combined for marker in ["もう見てもらえない", "あとで同じ", "同じところに不具合", "同じ問題", "同じ症状", "不具合が残って"])
    ):
        return "acceptance_after_support_question"
    if "差し戻し" in combined and "承諾" in combined:
        return "delivered_can_reject"
    if any(marker in combined for marker in ["月に1回", "月1回", "定期確認", "継続確認"]):
        return "monthly_support_request"
    if (
        any(marker in combined for marker in ["承諾しておきます", "承諾しておきます。", "承諾します", "承諾しておきます。また"])
        and any(marker in combined for marker in ["ありがとうございました", "ありがとうございます", "また何かあれば", "よろしくお願いいたします"])
        and any(marker in combined for marker in ["問題なさそう", "決済テストも通って", "通って問題なさそう", "問題なく動いて"])
    ):
        return "approval_complete_thanks"
    if (
        any(marker in combined for marker in ["社内のエンジニア", "社内", "転送しちゃって", "そのまま転送", "共有したい"])
        and any(marker in combined for marker in ["納品物", "修正内容", "転送"])
    ):
        return "deliverable_share_permission"
    if (
        any(marker in combined for marker in ["判断がつかなく", "自分では判断がつかなく", "大丈夫だと思います"])
        and "テストデータ" in combined
        and "承諾" in combined
    ):
        return "approval_reassurance_request"
    if any(marker in combined for marker in ["レイアウト", "余白"]) and any(
        marker in combined for marker in ["気のせい", "微妙に変わ", "一見動いてる", "一見動いている"]
    ):
        return "layout_side_effect_probe"
    if (
        any(marker in combined for marker in ["少し遅くなった", "レスポンスが以前より", "一応動いてはいる"])
        and any(marker in combined for marker in ["許容範囲", "大丈夫です", "ありがとうございました"])
    ):
        return "tolerated_minor_concern_close"
    if "承諾に進んで大丈夫" in combined:
        return "approval_ok"
    if "期待していた内容と違います" in combined or "診断レポートだけ" in combined:
        return "delivery_scope_mismatch"
    if "バックアップ" in combined and ("差分" in combined or "取り忘れて" in combined):
        return "backup_diff_request"
    if (
        "承諾前" in combined
        and any(marker in combined for marker in ["別かもしれ", "別件", "別の件", "今回の修正とは別"])
        and any(marker in combined for marker in ["聞いていい", "聞いてもいい", "送ってもいい", "少し聞"])
    ):
        return "secondary_question_before_acceptance"
    if (
        any(marker in combined for marker in ["別の話", "ついでに", "Webhookとは関係ない", "関係ないと思う"])
        and any(marker in combined for marker in ["読み込み", "重い", "パフォーマンス", "軽く見てもら"])
    ):
        return "extra_scope_after_delivery"
    if "未確認" in combined and ("できなかった" in combined or "スコープ外" in combined):
        return "doc_status_question"
    if "そのまま追加でお願い" in combined or "修正依頼として別件への移行" in combined or "修正後の状態に合わせてもらう" in combined:
        return "doc_to_bugfix_addon"
    if "ここも危なそう" in combined or "予防的に知っておきたくて" in combined:
        return "future_risk_question"
    if (
        any(
            marker in combined
            for marker in ["仕様が変わったら", "また壊れたりしますか", "ちょっと心配", "また同じことが起きないか", "半年後", "アップデート", "保証"]
        )
        and any(
            marker in combined
            for marker in [
                "今はちゃんと動いています",
                "問題なく動いています",
                "確認完了",
                "エラーは出なくなった",
                "確かにエラーは出なくなった",
                "直してもらったところ",
            ]
        )
    ):
        return "future_breakage_reassurance"
    if (
        any(marker in combined for marker in ["1日に何件", "何件くらいまで", "アクセスが増えた時", "また止まるのかな"])
        and "Webhook" in combined
    ):
        return "future_risk_question"
    if (
        "本番に反映作業まで" in combined
        or "本番反映まで" in combined
        or "Vercelへの上げ方がわかりません" in combined
        or "本番反映は自分でやる形" in combined
        or "本番に出すのが少し怖い" in combined
        or "気をつけること" in combined
    ):
        return "deployment_help_request"
    if "全体の構成見直し" in combined or "おいくらくらい" in combined:
        return "future_architecture_question"
    if ("資料" in combined or "納品いただいた資料" in combined) and "環境変数" in combined and any(
        marker in combined for marker in ["設定順序", "デプロイし直す", "気をつけること", "あとで困りたくない"]
    ):
        return "doc_caution_followup"
    if (
        "もう少しかみ砕いた説明" in combined
        or (
            any(marker in combined for marker in ["分かりやすく説明", "わかりやすく説明", "専門用語"])
            and any(marker in combined for marker in ["修正ファイル", "確認手順", "説明"])
        )
        or (
            any(marker in combined for marker in ["どこを見れば", "どこを確認", "何を見れば"])
            and any(marker in combined for marker in ["直った", "判断", "確認でき"])
        )
        or (
            any(marker in combined for marker in ["どこを確認", "どこを見れば"])
            and any(marker in combined for marker in ["専門用語", "承諾前", "簡単に教えて"])
        )
        or (
            any(marker in combined for marker in ["どこを反映", "反映すれば", "反映箇所"])
            and "修正ファイル" in combined
        )
    ):
        return "doc_explanation_request"
    if "質問が出たら聞いてもいいですか" in combined:
        return "postdelivery_question_window"
    if "同じ原因ですか" in combined or "前と違う動き" in combined:
        return "same_cause_check"
    if "今後また同じことが起きる可能性" in combined or "予防できるなら" in combined:
        return "prevention_question"
    if (
        any(marker in combined for marker in ["送信テスト", "ダッシュボードから送信テスト", "本番で試すのが怖い"])
        and "承諾" in combined
    ):
        return "approval_test_method"
    if "保留中" in combined and any(marker in combined for marker in ["Webhook", "イベント", "開発者 > Webhook", "ダッシュボード"]):
        return "pending_webhook_events"
    if (
        any(marker in combined for marker in ["なんでこのバグ", "なんでこのバグが起き", "そもそもなんで", "自分のコードが悪かった", "Stripe側の仕様変更", "今後のために知っておきたくて"])
        and any(marker in combined for marker in ["教えてほしい", "知っておきたくて", "原因"])
    ):
        return "cause_explanation_request"
    if any(marker in combined for marker in ["どのくらいの作業量", "自分でも直せた可能性", "半年くらい悩んで", "今後の参考に"]) and any(
        marker in combined for marker in ["全部問題なく動きました", "問題なく動きました", "嘘みたい"]
    ):
        return "workload_reflection_question"
    if (
        "Vercelにデプロイすると500エラー" in combined
        or "差し戻しというか" in combined
        or "また違うエラー" in combined
        or ("Vercel" in combined and "ステータスが切り替わらない" in combined)
        or ("まだ同じ症状" in combined and "もう一度見てもらえますか" in combined)
        or (
            any(marker in combined for marker in ["承諾できない", "承諾できません"])
            and any(marker in combined for marker in ["まだ", "直っていない", "注文が作られていない", "作られていない"])
        )
        or (
            any(marker in combined for marker in ["承諾していい", "承諾してよい"])
            and any(marker in combined for marker in ["まだ", "直っていない", "注文が作られていない", "作られていない"])
        )
    ):
        return "redelivery_same_error"
    if (
        "影響ですか" in combined
        or "別の機能が動かなく" in combined
        or "せいじゃないですか" in combined
        or "何か変わった部分がある可能性" in combined
        or "修正後に別の問題が出ました" in combined
        or "修正前は問題なかった" in combined
        or "今回の修正が影響している可能性" in combined
        or ("メール" in combined and ("遅くなった" in combined or "タイミング" in combined))
    ):
        return "side_effect_question"
    if "テスト" in combined and "ダッシュボード" in combined:
        return "dashboard_test_label"
    if service_hint == "handoff" and "メモ" in combined and "わかりやすかった" in combined:
        return "postdelivery_question_window"
    return "generic_delivered"


def extract_facts_known(raw: str, scenario: str) -> list[str]:
    facts: list[str] = []
    if "納品" in raw or "承諾" in raw:
        facts.append("delivery_context_present")
    if "エラー" in raw or "止まって" in raw or "動いて" in raw or "ビルド" in raw:
        facts.append("symptom_surface_described")
    if "15,000" in raw or "15000" in raw or "高い" in raw:
        facts.append("price_context_present")
    if "メモ" in raw or "資料" in raw:
        facts.append("document_context_present")
    if scenario in {"deployment_help_request", "future_architecture_question"}:
        facts.append("scope_boundary_question_present")
    if "テスト" in raw and "ダッシュボード" in raw:
        facts.append("dashboard_test_label_present")
    if "メール送信" in raw:
        facts.append("mail_flow_mentioned")
    if "環境変数" in raw:
        facts.append("env_var_context_present")
    if "設定順序" in raw:
        facts.append("env_order_caution_present")
    if "デプロイし直す" in raw or "デプロイ" in raw:
        facts.append("redeploy_context_present")
    if "メール" in raw and ("遅く" in raw or "タイミング" in raw):
        facts.append("mail_timing_delay_present")
    if "Webhook" in raw and ("出なくなりました" in raw or "問題なく動" in raw):
        facts.append("webhook_issue_resolved_present")
    if any(marker in raw for marker in ["体感", "気のせい", "不具合ってほどではない"]):
        facts.append("soft_probe_present")
    if "診断レポートだけ" in raw:
        facts.append("report_only_named")
    if "修正ファイル" in raw:
        facts.append("fix_file_named")
    if "承諾" in raw:
        facts.append("approval_question_present")
    if "送信テスト" in raw:
        facts.append("dashboard_send_test_present")
    if "受信側" in raw:
        facts.append("receiver_side_scope_question_present")
    if "本番で試すのが怖" in raw or ("本番" in raw and "怖" in raw):
        facts.append("prod_test_fear_present")
    if any(marker in raw for marker in ["修正前は問題なかった", "今回の修正が影響", "今回の修正の影響", "修正後に別の問題"]):
        facts.append("post_fix_regression_reported")
    return facts


def build_primary_concern(source: dict, scenario: str, facts_known: list[str]) -> str:
    raw = source.get("raw_message", "")

    if scenario == "dashboard_test_label":
        return "ダッシュボードの「テスト」表示が異常か確認したい"
    if scenario == "side_effect_question":
        if "post_fix_regression_reported" in facts_known:
            return "修正後に別の問題が出たので、今回の修正の影響も含めて確認してほしい"
        if "mail_timing_delay_present" in facts_known and "approval_question_present" in facts_known:
            return "決済成功後のメールが少し遅く見える点が承諾前に気になっている"
        if "mail_timing_delay_present" in facts_known:
            return "決済成功後のメールが少し遅く見える点が今回の修正と関係あるか知りたい"
        return "別の機能停止が今回の修正の影響か知りたい"
    if scenario == "prevention_question":
        return "今後の再発可能性と予防の考え方を知りたい"
    if scenario == "approval_test_method":
        return "受信側の修正範囲と、本番で試さずに承諾前確認する方法を知りたい"
    if scenario == "redelivery_same_error":
        return "本番だけ残る同じエラーが修正不足か環境差か知りたい"
    if scenario == "approval_ok":
        return "問題なく動いたので承諾に進んでよいか確認したい"
    if scenario == "dry_complete_close":
        return "事務的に完了だけ伝えて、ここで区切りたい"
    if scenario == "success_thanks_only":
        return "まず一言返してほしいくらい、直ってほっとしている"
    if scenario == "formal_thanks_only":
        return "丁寧にお礼を伝えつつ、今後も相談したい気持ちを伝えている"
    if scenario == "approval_reassurance_request":
        return "承諾前に、大丈夫そうか一言ほしい"
    if scenario == "tolerated_minor_concern_close":
        return "少し気になる点はあるが、許容範囲としてここで区切ろうとしている"
    if scenario == "deliverable_share_permission":
        return "納品物を社内共有してよいか確認したい"
    if scenario == "signing_secret_rotation_recurrence":
        return "signing secret を変えた時に同じ問題が再発するか知りたい"
    if scenario == "extra_fee_reassurance":
        return "今回の対応で追加料金が発生しないか確認したい"
    if scenario == "pending_webhook_events":
        return "Webhook受信はできているが、保留中イベントが残っていて放置でよいか知りたい"
    if scenario == "layout_side_effect_probe":
        return "差し替え後の見た目が少し変わったように見える点が気になっている"
    if scenario == "approval_complete_thanks":
        return "確認が済んだので承諾して区切りたい"
    if scenario == "approval_ok_with_future_request":
        return "承諾してよいかと、今後また何かあった時に相談できるかを知りたい"
    if scenario == "acceptance_after_support_question":
        return "承諾後に同じ箇所の不具合が残っていた場合の相談導線を知りたい"
    if scenario == "delivered_can_reject":
        return "未確認箇所がある状態で、差し戻しや承諾の判断をどうすればよいか知りたい"
    if scenario == "monthly_support_request":
        return "納品後の継続対応や月1回確認が今回範囲に入るか知りたい"
    if scenario == "delivery_scope_mismatch":
        return "納品内容が期待とずれていた点をどう埋めるか確認したい"
    if scenario == "backup_diff_request":
        return "修正前のバックアップや差分を後から確認できるか知りたい"
    if scenario == "extra_scope_after_delivery":
        return "今回とは別の読み込みの重さもついでに見てもらえるか知りたい"
    if scenario == "secondary_question_before_acceptance":
        return "承諾前に、今回の修正と別かもしれない質問をどこまで聞けるか知りたい"
    if scenario == "apply_followup_issue":
        return "反映後のビルドエラーを今回の続きで見てもらいたい"
    if scenario == "doc_status_question":
        return "納品物の「未確認」の意味を知りたい"
    if scenario == "doc_caution_followup":
        return "納品資料の環境変数に関する注意書きが、今後の再デプロイ時にどう関係するか知りたい"
    if scenario == "doc_to_bugfix_addon":
        return "納品後の流れからそのまま修正相談に移れるか知りたい"
    if scenario == "future_risk_question":
        return "他に危なそうな箇所があるかを知りたい"
    if scenario == "future_breakage_reassurance":
        return "今は動いているので、このまま承諾してよいか安心したい"
    if scenario == "cause_explanation_request":
        return "今回のバグの原因がコード側かStripe側か知りたい"
    if scenario == "workload_reflection_question":
        return "今回の作業量と、自分でも直せた可能性があったのか知りたい"
    if scenario == "deployment_help_request":
        return "反映で止まっているので代替支援の範囲を知りたい"
    if scenario == "future_architecture_question":
        return "全体見直しの相談入口と範囲感を知りたい"
    if scenario == "doc_explanation_request":
        return "納品資料をもう少しかみ砕いて説明してほしい"
    if scenario == "postdelivery_question_window":
        return "後から出た質問をこのままここで聞いてよいか確認したい"
    if scenario == "same_cause_check":
        return "追加で出た症状が前回と同じ原因か知りたい"
    if scenario == "price_complaint":
        return "納品内容に対して料金が高く感じる"
    if scenario == "approval_wait_request":
        return "承諾を少し待ってほしい"
    if raw:
        return shared.summarize_raw_message(raw)
    return "納品後の追加連絡をどう進めるか確認したい"


def build_hard_constraints(scenario: str, grounding: dict) -> dict:
    return {
        "service_id": grounding.get("service_id"),
        "public_service_only": bool(grounding.get("public_service")),
        "answer_before_procedure": True,
        "ask_only_if_blocking": True,
        "no_prod_deploy": scenario == "deployment_help_request",
        "no_external_contact": False,
        "same_cause_scope_rule": grounding.get("scope_unit") == "same_cause_and_same_flow_and_same_endpoint",
    }


def build_response_decision_plan(source: dict, scenario: str, contract: dict) -> dict:
    raw = source.get("raw_message", "")
    primary_id = contract["primary_question_id"]
    answer_map = contract["answer_map"]
    primary = next(item for item in answer_map if item["question_id"] == primary_id)
    facts_known = extract_facts_known(raw, scenario)
    blocking_missing_facts: list[str] = []
    direct_answer_line = primary["answer_brief"]

    if primary["disposition"] in {"answer_now", "decline"}:
        response_order = ["opening", "direct_answer", "answer_detail"]
    else:
        response_order = ["opening", "direct_answer", "answer_detail", "ask", "next_action"]

    if scenario == "dashboard_test_label":
        blocking_missing_facts = ["dashboard_mode_screen"]
        direct_answer_line = "修正した決済フローが動いているなら、その表示だけで異常とは限りません。"
    elif scenario == "approval_test_method":
        direct_answer_line = "はい、今回見ているのはWebhookの受信側です。"
        response_order = ["opening", "direct_answer", "answer_detail"]
    elif scenario == "approval_complete_thanks":
        direct_answer_line = "承諾の件もありがとうございます。また何かあれば、その時の状況を送ってください。"
        response_order = ["opening", "direct_answer"]
    elif scenario == "dry_complete_close":
        direct_answer_line = "ありがとうございます。承知しました。"
        response_order = ["opening", "direct_answer", "answer_detail"]
    elif scenario == "success_thanks_only":
        direct_answer_line = "そう言っていただけて何よりです。"
        response_order = ["opening", "direct_answer"]
    elif scenario == "formal_thanks_only":
        direct_answer_line = "ご丁寧にありがとうございます。そう言っていただけて何よりです。"
        response_order = ["opening", "direct_answer", "answer_detail"]
    elif scenario == "approval_reassurance_request":
        direct_answer_line = "現時点の確認材料を見る限り、こちらの確認範囲では大丈夫そうです。"
        response_order = ["opening", "direct_answer", "answer_detail"]
    elif scenario == "tolerated_minor_concern_close":
        direct_answer_line = "許容範囲とのことなら、今回はそのまま区切っていただいて大丈夫です。"
        response_order = ["opening", "direct_answer", "answer_detail"]
    elif scenario == "webhook_log_howto":
        direct_answer_line = "あります。Stripeダッシュボードの「開発者」→「Webhooks」から確認できます。"
        response_order = ["opening", "direct_answer", "answer_detail"]
    elif scenario == "light_learning_question":
        direct_answer_line = "まずは Stripe の公式ドキュメントで Checkout と Webhook の流れを見るところからが分かりやすいです。"
        response_order = ["opening", "direct_answer", "answer_detail"]
    elif scenario == "review_content_question":
        direct_answer_line = "はい、差し支えない範囲なら技術的な内容まで書いていただいて大丈夫です。"
        response_order = ["opening", "direct_answer"]
    elif scenario == "deliverable_share_permission":
        direct_answer_line = "はい、納品物の内容はそのまま社内共有いただいて大丈夫です。"
        response_order = ["opening", "direct_answer", "answer_detail"]
    elif scenario == "signing_secret_rotation_recurrence":
        direct_answer_line = "あります。本番の signing secret を変えたのに、受信側の参照先が古いままだと同じことは再発しえます。"
        response_order = ["opening", "direct_answer", "answer_detail"]
    elif scenario == "extra_fee_reassurance":
        direct_answer_line = "今回ここまでの対応で、追加料金は発生しません。"
        response_order = ["opening", "direct_answer", "answer_detail"]
    elif scenario == "pending_webhook_events":
        blocking_missing_facts = ["pending_event_detail"]
        direct_answer_line = "放置で大丈夫とはまだ言い切れません。まず保留中イベントの状態を確認します。"
        response_order = ["opening", "direct_answer", "answer_detail", "ask", "next_action"]
    elif scenario == "future_breakage_reassurance":
        direct_answer_line = "今の時点で、すぐまた壊れる前提ではありません。"
        response_order = ["opening", "direct_answer", "answer_detail"]
    elif scenario == "acceptance_after_support_question":
        direct_answer_line = "承諾前であれば、気になる点はこのトークルーム内でお伝えください。"
        response_order = ["opening", "direct_answer", "answer_detail"]
    elif scenario == "delivered_can_reject":
        direct_answer_line = "本番でまだ確認できていない箇所があるなら、無理に承諾しなくて大丈夫です。"
        response_order = ["opening", "direct_answer", "answer_detail", "next_action"]
    elif scenario == "monthly_support_request":
        direct_answer_line = "月1回の定期確認は、今回の修正範囲には含まれていません。"
        response_order = ["opening", "direct_answer", "answer_detail"]
    elif scenario == "cause_explanation_request":
        direct_answer_line = "今回の件は、Stripe側だけの問題というより、実装側とのつなぎ方にずれが出ていたのが原因です。"
        response_order = ["opening", "direct_answer", "answer_detail"]
    elif scenario == "workload_reflection_question":
        direct_answer_line = "今回の件は、すぐ一行で直る種類ではなく、原因の切り分けを含めて確認が必要な内容でした。"
        response_order = ["opening", "direct_answer", "answer_detail"]
    elif scenario == "layout_side_effect_probe":
        blocking_missing_facts = ["layout_change_screen"]
        direct_answer_line = "決済が問題なく動いているなら、急ぎの不具合とは考えにくいです。"
        response_order = ["opening", "direct_answer", "answer_detail", "ask", "next_action"]
    elif scenario == "side_effect_question":
        if "post_fix_regression_reported" in facts_known:
            blocking_missing_facts = ["mail_error_surface"]
            direct_answer_line = "今回の修正の影響も含めて確認します。"
            response_order = ["opening", "direct_answer", "answer_detail", "ask", "next_action"]
        elif {
            "mail_timing_delay_present",
            "soft_probe_present",
            "approval_question_present",
        }.issubset(set(facts_known)):
            blocking_missing_facts = []
            direct_answer_line = "体感で少し遅く感じる程度で、他に問題が出ていなければ大きな不具合とは考えにくいです。"
            response_order = ["opening", "direct_answer", "answer_detail"]
        else:
            blocking_missing_facts = ["mail_error_surface"]
            direct_answer_line = "今の時点では、今回の修正の影響かどうかはまだ言い切れません。"
    elif scenario == "redelivery_same_error":
        blocking_missing_facts = ["post_deploy_error_surface"]
        direct_answer_line = "今の時点では、修正が足りていないとはまだ言い切れません。"
    elif scenario == "delivery_scope_mismatch":
        if "report_only_named" in facts_known and "fix_file_named" in facts_known:
            direct_answer_line = "期待と違っていた点として、診断レポートだけで修正ファイルが入っていなかった点は確認しました。"
            response_order = ["opening", "direct_answer", "answer_detail", "next_action"]
        else:
            blocking_missing_facts = ["missing_points"]
            direct_answer_line = "期待と違っていた点は確認しました。"
    elif scenario == "extra_scope_after_delivery":
        direct_answer_line = "軽く確認することはできますが、Webhookとは別の話ならこの範囲とは分けて案内します。"
        response_order = ["opening", "direct_answer", "answer_detail"]
    elif scenario == "secondary_question_before_acceptance":
        direct_answer_line = "はい、承諾前なので、まず今回の修正とつながる内容かを軽く確認できます。"
        response_order = ["opening", "direct_answer", "answer_detail"]
    elif scenario == "backup_diff_request":
        direct_answer_line = "修正前のファイルは別途保管していませんでした。"
        response_order = ["opening", "direct_answer", "answer_detail"]
    elif scenario == "doc_caution_followup":
        direct_answer_line = "はい、今後ご自身でデプロイし直す時に気をつける点として書いています。"
        response_order = ["opening", "direct_answer", "answer_detail"]
    elif scenario == "apply_followup_issue":
        blocking_missing_facts = ["build_error_text"]
    elif scenario == "doc_to_bugfix_addon":
        blocking_missing_facts = ["target_fix_points"]
    elif scenario == "future_architecture_question":
        blocking_missing_facts = ["target_review_scope"]
    elif scenario == "doc_explanation_request":
        blocking_missing_facts = ["hard_sections"]
        response_order = ["opening", "direct_answer", "answer_detail", "ask", "next_action"]
    elif scenario == "same_cause_check":
        blocking_missing_facts = ["current_symptom"]
    elif scenario == "future_risk_question":
        if any(marker in raw for marker in ["1日に何件", "何件くらいまで", "アクセスが増えた時", "また止まるのかな"]):
            direct_answer_line = "件数だけで一律に決まるものではなく、今の処理内容や実行時間しだいです。"
            response_order = ["opening", "direct_answer", "answer_detail"]
        else:
            response_order = ["opening", "direct_answer", "answer_detail", "next_action"]
    elif scenario == "price_complaint":
        direct_answer_line = "ご指摘の通り、結果として小さく見える内容だったと思います。"
        response_order = ["opening", "direct_answer", "answer_detail"]
    elif scenario == "generic_delivered":
        response_order = ["opening", "direct_answer", "answer_detail", "next_action"]

    return {
        "primary_question_id": contract["primary_question_id"],
        "primary_concern": build_primary_concern(source, scenario, facts_known),
        "buyer_emotion": infer_buyer_emotion(raw),
        "facts_known": facts_known,
        "blocking_missing_facts": blocking_missing_facts,
        "direct_answer_line": direct_answer_line,
        "response_order": response_order,
    }


def build_case_from_source(source: dict) -> dict:
    raw = source.get("raw_message", "")
    scenario = detect_scenario(source)
    case = {
        "id": source.get("case_id") or source.get("id"),
        "src": source.get("route", "talkroom"),
        "state": "delivered",
        "emotional_tone": source.get("emotional_tone"),
        "raw_message": raw,
        "summary": shared.derive_summary(source),
        "known_facts": shared.extract_known_facts(source),
        "routing_meta": shared.build_routing_meta(source, scenario),
        "scenario": scenario,
        "service_grounding": dict(SERVICE_GROUNDING),
        "hard_constraints": build_hard_constraints(scenario, SERVICE_GROUNDING),
        "temperature_plan": build_temperature_plan_for_case(source, scenario),
        "reply_stance": {
            "burden_owner": "us",
            "empathy_first": source.get("emotional_tone") in {"anxious", "frustrated", "complaint_like"},
            "reply_skeleton": "delivery",
        },
    }

    if scenario == "dashboard_test_label":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [{"id": "q1", "text": "Stripeのダッシュボードにテストと出るのは正常か", "priority": "primary"}],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_after_check",
                    "answer_brief": "修正した決済フローが動いているなら、その表示だけで異常とは限りません。",
                    "hold_reason": "まずはStripeのテストモードと本番モードの見分けを確認します。",
                    "revisit_trigger": "画面を受領したあとに、見えているモードをお返しします。",
                }
            ],
            "ask_map": [
                {
                    "id": "a1",
                    "question_ids": ["q1"],
                    "ask_text": "Stripeダッシュボード上部のモード切り替えが見える画面を1枚送ってください。",
                    "why_needed": "テストモードを見ているだけかを先に切るため",
                }
            ],
            "required_moves": ["react_briefly_first", "defer_with_reason", "request_minimum_evidence", "commit_next_update_time"],
        }
        return case

    if scenario == "side_effect_question":
        has_mail_delay = "メール" in raw and ("遅く" in raw or "タイミング" in raw)
        has_approval_question = "承諾" in raw
        has_soft_probe = has_mail_delay and any(marker in raw for marker in ["体感", "気のせい", "不具合ってほどではない"])
        has_post_fix_regression = any(
            marker in raw for marker in ["修正前は問題なかった", "今回の修正が影響", "今回の修正の影響", "修正後に別の問題"]
        )
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [{"id": "q1", "text": "今回の修正の影響か", "priority": "primary"}]
            + ([{"id": "q2", "text": "関係なければ承諾してよいか", "priority": "secondary"}] if has_approval_question else []),
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_after_check"
                    if has_post_fix_regression
                    else ("answer_now" if has_soft_probe and has_approval_question else "answer_after_check"),
                    "answer_brief": "今回の修正の影響も含めて確認します。"
                    if has_post_fix_regression
                    else (
                        "体感で少し遅く感じる程度なら、今回の修正が直接影響している可能性は高くないです。"
                        if has_soft_probe and has_approval_question
                        else "今の時点では、今回の修正の影響かどうかはまだ言い切れません。"
                    ),
                    "hold_reason": "修正後の差分と、メール送信が止まった流れを先に確認します。"
                    if has_post_fix_regression and not has_mail_delay
                    else (
                        "修正箇所と、メールのタイミング変化に関係がありそうかを先に確認します。"
                        if has_post_fix_regression and has_mail_delay
                        else (
                        ""
                        if has_soft_probe and has_approval_question
                        else (
                            "修正箇所と、メールのタイミング変化に関係がありそうかを先に確認します。"
                            if has_mail_delay
                            else "修正箇所と、止まっているメール送信のつながりを先に確認します。"
                        )
                        )
                    ),
                    "revisit_trigger": "状況を受領したあとに、今回の修正との関係をお返しします。"
                    if has_post_fix_regression
                    else ("" if has_soft_probe and has_approval_question else "状況を受領したあとに、今回の修正との関係をお返しします。"),
                }
            ]
            + (
                [
                    {
                        "question_id": "q2",
                        "disposition": "answer_now",
                        "answer_brief": "今の挙動で問題なければ、そのまま承諾で大丈夫です。",
                    }
                ]
                if has_approval_question
                else []
            ),
            "ask_map": []
            if has_soft_probe and has_approval_question and not has_post_fix_regression
            else [
                {
                    "id": "a1",
                    "question_ids": ["q1"],
                    "ask_text": "メール送信が止まっていることが分かる画面か、操作手順を送ってください。"
                    if has_post_fix_regression and not has_mail_delay
                    else (
                        "前より遅く感じた場面か、どのタイミングでそう見えたかが分かるものをそのまま送ってください。"
                        if has_post_fix_regression and has_mail_delay
                        else (
                        "前より遅く感じた場面か、どのタイミングでそう見えたかが分かるものをそのまま送ってください。"
                        if has_mail_delay
                        else "メール送信が止まっていることが分かる画面か、操作手順を送ってください。"
                        )
                    ),
                    "why_needed": "今回の修正とのつながりが強いかを先に見るため",
                }
            ],
            "required_moves": ["react_briefly_first", "answer_directly_now"]
            if has_soft_probe and has_approval_question and not has_post_fix_regression
            else ["react_briefly_first", "defer_with_reason", "request_minimum_evidence", "commit_next_update_time"],
        }
        return case

    if scenario == "prevention_question":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "今後また同じことが起きる可能性はあるか", "priority": "primary"},
                {"id": "q2", "text": "承諾に進んでよいか", "priority": "secondary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "今回直した箇所が同じ原因なら、起きにくくはしています。ただ、別の変更が入ると再発の可能性はゼロとは言い切れません。",
                },
                {
                    "question_id": "q2",
                    "disposition": "answer_now",
                    "answer_brief": "今回の確認内容で問題なければ、このまま承諾に進んでいただいて大丈夫です。",
                },
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now"],
        }
        return case

    if scenario == "approval_test_method":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "今回修正したのはWebhookの受信側だけか", "priority": "primary"},
                {"id": "q2", "text": "本番で試さずに承諾前確認する方法はあるか", "priority": "secondary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "はい、今回見ているのはWebhookの受信側です。",
                },
                {
                    "question_id": "q2",
                    "disposition": "answer_now",
                    "answer_brief": "Stripeダッシュボードからの送信テストが成功しているなら、受信側の確認としてはそこまでで大丈夫です。",
                },
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now"],
        }
        return case

    if scenario == "redelivery_same_error":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [{"id": "q1", "text": "修正が足りていないのか", "priority": "primary"}],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_after_check",
                    "answer_brief": "今の時点では、修正が足りていないとはまだ言い切れません。",
                    "hold_reason": "ローカルでは直っているので、デプロイ後に変わる条件から見ます。",
                    "revisit_trigger": "本番の状況を受領したあとに、次に見る場所をお返しします。",
                }
            ],
            "ask_map": [
                {
                    "id": "a1",
                    "question_ids": ["q1"],
                    "ask_text": "デプロイ後に出ているエラーの画面かメッセージを送ってください。",
                    "why_needed": "ローカルとの差分を先に切るため",
                }
            ],
            "required_moves": ["react_briefly_first", "defer_with_reason", "request_minimum_evidence", "commit_next_update_time"],
        }
        return case

    if scenario == "approval_ok":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [{"id": "q1", "text": "承諾に進んでよいか", "priority": "primary"}],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "今回は問題なく動いているなら、このまま承諾に進んでいただいて大丈夫です。",
                }
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now"],
        }
        return case

    if scenario == "success_thanks_only":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [{"id": "q1", "text": "直ったのでまず一言返してほしい", "priority": "primary"}],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "そう言っていただけて何よりです。",
                }
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now"],
        }
        return case

    if scenario == "formal_thanks_only":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [{"id": "q1", "text": "丁寧なお礼に対して簡潔に返してほしい", "priority": "primary"}],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "ご丁寧にありがとうございます。そう言っていただけて何よりです。",
                }
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now"],
        }
        return case

    if scenario == "dry_complete_close":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [{"id": "q1", "text": "事務的な完了報告に短く返してほしい", "priority": "primary"}],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "ありがとうございます。承知しました。",
                }
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now"],
        }
        return case

    if scenario == "signing_secret_rotation_recurrence":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [{"id": "q1", "text": "signing secret をローテーションした時に再発する可能性があるか", "priority": "primary"}],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "あります。本番の signing secret を変えたのに、受信側の参照先が古いままだと同じことは再発しえます。",
                }
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now"],
        }
        return case

    if scenario == "approval_complete_thanks":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [{"id": "q1", "text": "確認が済んだので承諾して区切ってよいか", "priority": "primary"}],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "承諾の件もありがとうございます。また何かあれば、その時の状況を送ってください。",
                }
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now"],
        }
        return case

    if scenario == "approval_reassurance_request":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "大丈夫そうか", "priority": "primary"},
                {"id": "q2", "text": "承諾してよいか", "priority": "secondary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "テストデータで決済まで通っていて、他に気になる挙動がなければ、こちらの確認範囲では大丈夫そうです。",
                },
                {
                    "question_id": "q2",
                    "disposition": "answer_now",
                    "answer_brief": "その前提なら、承諾いただいて大丈夫です。",
                },
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now"],
        }
        return case

    if scenario == "tolerated_minor_concern_close":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "許容範囲ならここで区切ってよいか", "priority": "primary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "許容範囲とのことなら、今回はそのまま区切っていただいて大丈夫です。",
                }
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now"],
        }
        return case

    if scenario == "webhook_log_howto":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [{"id": "q1", "text": "StripeダッシュボードでWebhookログを自分で見る方法があるか", "priority": "primary"}],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "あります。Stripeダッシュボードの「開発者」→「Webhooks」から確認できます。",
                }
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now"],
        }
        return case

    if scenario == "light_learning_question":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [{"id": "q1", "text": "Stripe周りを独学するならどこから始めるとよいか", "priority": "primary"}],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "まずは Stripe の公式ドキュメントで Checkout と Webhook の流れを見るところからが分かりやすいです。",
                }
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now"],
        }
        return case

    if scenario == "review_content_question":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [{"id": "q1", "text": "レビューに技術的な内容まで書いてよいか", "priority": "primary"}],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "はい、差し支えない範囲なら技術的な内容まで書いていただいて大丈夫です。",
                }
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now"],
        }
        return case

    if scenario == "deliverable_share_permission":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [{"id": "q1", "text": "納品物の内容を社内へそのまま共有してよいか", "priority": "primary"}],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "はい、納品物の内容はそのまま社内共有いただいて大丈夫です。",
                }
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now"],
        }
        return case

    if scenario == "pending_webhook_events":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [{"id": "q1", "text": "Webhookの保留中イベントを放置してよいか", "priority": "primary"}],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_after_check",
                    "answer_brief": "放置で大丈夫とはまだ言い切れません。まず保留中イベントの状態を確認します。",
                    "hold_reason": "保留中のまま未処理なのか、表示だけ残っているのかで案内が変わります。",
                    "revisit_trigger": "イベント詳細を受領したあとに、何をすればよいかお返しします。",
                }
            ],
            "ask_map": [
                {
                    "id": "a1",
                    "question_ids": ["q1"],
                    "ask_text": "保留中になっているイベント詳細が見える画面があれば、そのまま送ってください。",
                    "why_needed": "未処理なのか表示だけ残っているのかを先に切るため",
                }
            ],
            "required_moves": ["react_briefly_first", "defer_with_reason", "request_minimum_evidence", "commit_next_update_time"],
        }
        return case

    if scenario == "approval_ok_with_future_request":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "承諾のボタンを押してよいか", "priority": "primary"},
                {"id": "q2", "text": "今後また何かあった時もお願いできるか", "priority": "secondary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "承諾のボタンを押していただいて大丈夫です。",
                },
                {
                    "question_id": "q2",
                    "disposition": "answer_now",
                    "answer_brief": "また何かあれば、その時点の内容を見て対応できるかご案内できます。",
                },
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now"],
        }
        return case

    if scenario == "acceptance_after_support_question":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "承諾後に同じ箇所の不具合が残っていた場合でも見てもらえるか", "priority": "primary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "承諾前であれば、気になる点はこのトークルーム内でお伝えください。",
                },
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now"],
        }
        return case

    if scenario == "delivered_can_reject":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "正式納品後に差し戻しできるか", "priority": "primary"},
                {"id": "q2", "text": "まだ確認できていなくても承諾しないといけないか", "priority": "secondary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "差し戻しで送っていただいて大丈夫です。",
                },
                {
                    "question_id": "q2",
                    "disposition": "answer_now",
                    "answer_brief": "本番で一部確認できていないなら、無理に承諾しなくて大丈夫です。",
                },
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now"],
        }
        return case

    if scenario == "monthly_support_request":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "今後の継続対応や月1回確認が今回範囲に入るか", "priority": "primary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "月1回の定期確認は、今回の修正範囲には含まれていません。",
                },
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now"],
        }
        return case

    if scenario == "extra_scope_after_delivery":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "今回とは別の読み込みの重さも見てもらえるか", "priority": "primary"},
                {"id": "q2", "text": "無理なら今回はそのままでよいか", "priority": "secondary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "軽く確認することはできますが、Webhookとは別の話ならこの範囲とは分けて案内します。",
                },
                {
                    "question_id": "q2",
                    "disposition": "answer_now",
                    "answer_brief": "今の修正が問題なく動いているなら、この件はそのまま区切っていただいて大丈夫です。",
                },
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now"],
        }
        return case

    if scenario == "secondary_question_before_acceptance":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "承諾前に別件かもしれない質問をしてよいか", "priority": "primary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "はい、承諾前なので、まず今回の修正とつながる内容かを軽く確認できます。",
                },
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now", "separate_followup_from_new_work"],
        }
        return case

    if scenario == "delivery_scope_mismatch":
        mismatch_is_specific = "診断レポートだけ" in raw and "修正ファイル" in raw
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [{"id": "q1", "text": "期待していた内容と違う", "priority": "primary"}],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_after_check",
                    "answer_brief": "期待と違っていた点として、診断レポートだけで修正ファイルが入っていなかった点は確認しました。"
                    if mismatch_is_specific
                    else "期待と違っていた点は確認しました。",
                    "hold_reason": "まず、『原因特定と修正』の認識だった点も含めて、納品内容とのずれを確認します。"
                    if mismatch_is_specific
                    else "まずは今回の認識差を確認して、差し戻しで埋める範囲かを切ります。",
                    "revisit_trigger": "今回の認識差を確認したうえで、どの形で対応するかをお伝えします。"
                    if mismatch_is_specific
                    else "足りなかった点を受領したあとに、どの形で対応するかをお伝えします。",
                }
            ],
            "ask_map": []
            if mismatch_is_specific
            else [
                {
                    "id": "a1",
                    "question_ids": ["q1"],
                    "ask_text": "足りないと感じた点を1〜2点だけそのまま送ってください。",
                    "why_needed": "差し戻しで埋める話か、認識差の整理が先かを切るため",
                }
            ],
            "required_moves": ["react_briefly_first", "defer_with_reason", "commit_next_update_time"]
            if mismatch_is_specific
            else ["react_briefly_first", "defer_with_reason", "request_minimum_evidence", "commit_next_update_time"],
        }
        return case

    if scenario == "backup_diff_request":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [{"id": "q1", "text": "修正前のバックアップや差分を見られるか", "priority": "primary"}],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "修正前のファイルは別途保管していませんでした。",
                }
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now"],
        }
        return case

    if scenario == "layout_side_effect_probe":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [{"id": "q1", "text": "見た目の変化が今回の修正の影響か", "priority": "primary"}],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_after_check",
                    "answer_brief": "決済が問題なく動いているなら、急ぎの不具合とは考えにくいです。",
                    "hold_reason": "ただ、今回の差分の影響かどうかは確認します。",
                    "revisit_trigger": "見た目が変わって見える画面を受領したあとに、今回の差分との関係をお返しします。",
                }
            ],
            "ask_map": [
                {
                    "id": "a1",
                    "question_ids": ["q1"],
                    "ask_text": "ヘッダーの余白が広がって見える画面があれば、そのまま送ってください。",
                    "why_needed": "今回の差分と見た目の変化がつながっているかを確認するため",
                }
            ],
            "required_moves": ["react_briefly_first", "defer_with_reason", "request_minimum_evidence", "commit_next_update_time"],
        }
        return case

    if scenario == "future_breakage_reassurance":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [{"id": "q1", "text": "このまま承諾して大丈夫そうか", "priority": "primary"}],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "今の時点で、すぐまた壊れる前提ではありません。",
                }
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now"],
        }
        return case

    if scenario == "cause_explanation_request":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [{"id": "q1", "text": "なぜこのバグが起きていたのか", "priority": "primary"}],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "今回の件は、Stripe側だけの問題というより、実装側とのつなぎ方にずれが出ていたのが原因です。",
                }
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now"],
        }
        return case

    if scenario == "workload_reflection_question":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [{"id": "q1", "text": "今回の作業量はどのくらいで、自分でも直せた可能性があったか", "priority": "primary"}],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "今回の件は、すぐ一行で直る種類ではなく、原因の切り分けを含めて確認が必要な内容でした。",
                }
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now"],
        }
        return case

    if scenario == "apply_followup_issue":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [{"id": "q1", "text": "反映後にビルドが通らない", "priority": "primary"}],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_after_check",
                    "answer_brief": "反映後にビルドが通らなくなった件、こちらでも一緒に確認します。",
                    "hold_reason": "手順の抜けか差分の反映違いかを先に切ります。",
                    "revisit_trigger": "エラー内容を受領したあとに、どこから確認するかをお返しします。",
                }
            ],
            "ask_map": [
                {
                    "id": "a1",
                    "question_ids": ["q1"],
                    "ask_text": "出ているエラー文が分かれば、そのまま送ってください。",
                    "why_needed": "反映漏れか別のビルド要因かを先に切るため",
                }
            ],
            "required_moves": ["react_briefly_first", "defer_with_reason", "request_minimum_evidence", "commit_next_update_time"],
        }
        return case

    if scenario == "doc_status_question":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [{"id": "q1", "text": "未確認の意味は何か", "priority": "primary"}],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "ここでの「未確認」は、今回の対象フローには含めず確認の範囲に入れていないという意味です。確認しようとしてできなかった、という意味ではありません。",
                }
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now"],
        }
        return case

    if scenario == "doc_caution_followup":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [{"id": "q1", "text": "資料の環境変数の注意は今後の再デプロイ時に気をつけることか", "priority": "primary"}],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "はい、今後ご自身でデプロイし直す時に気をつける点として書いています。",
                }
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now"],
        }
        return case

    if scenario == "doc_to_bugfix_addon":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [{"id": "q1", "text": "このまま修正相談へ移れるか", "priority": "primary"}],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_after_check",
                    "answer_brief": "修正の相談には移れます。まず今の依頼の補足で足りるか、別の修正相談として切るかを確認します。",
                    "hold_reason": "納品後なので、そのまま続きとして扱う前に今回見たい内容を先に切ります。",
                    "revisit_trigger": "直したい点を受領したあとに、次の入口をお返しします。",
                }
            ],
            "ask_map": [
                {
                    "id": "a1",
                    "question_ids": ["q1"],
                    "ask_text": "直したい箇所か、修正後に合わせたい部分をそのまま送ってください。",
                    "why_needed": "補足で足りるか、修正相談に切るかを先に判断するため",
                }
            ],
            "required_moves": ["react_briefly_first", "defer_with_reason", "request_minimum_evidence", "commit_next_update_time"],
        }
        return case

    if scenario == "future_risk_question":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [{"id": "q1", "text": "他に危なそうな箇所があるか", "priority": "primary"}],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_after_check",
                    "answer_brief": "気になる箇所があればお伝えできます。まず今回の修正範囲の近くで見えているものがあるかを確認します。",
                    "hold_reason": "納品時に確定していない点を、その場で言い切るより確認してから返した方がずれません。",
                    "revisit_trigger": "確認できたところまでをお返しします。",
                }
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "defer_with_reason", "commit_next_update_time"],
        }
        return case

    if scenario == "deployment_help_request":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "本番反映は自分でやる形か", "priority": "primary"},
                {"id": "q2", "text": "反映前に気をつけることはあるか", "priority": "secondary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "本番反映は、ご自身で進めていただく形です。",
                },
                {
                    "question_id": "q2",
                    "disposition": "answer_now",
                    "answer_brief": "気をつける点としては、反映前に環境変数の差分がないかを先に確認するのが大事です。必要なら、このトークルーム内で反映手順が分かる形にして返します。",
                },
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now"],
        }
        return case

    if scenario == "future_architecture_question":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [{"id": "q1", "text": "全体の見直しを相談するとしたらどうなるか", "priority": "primary"}],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_after_check",
                    "answer_brief": "全体の見直し相談としては受けられます。まず今回どこまで見たいかを確認してから入口をご案内します。",
                    "hold_reason": "納品後の追加相談なので、いきなり金額を決めるより内容を先に切った方がずれません。",
                    "revisit_trigger": "見たい範囲を受領したあとに、今回の入口をお返しします。",
                }
            ],
            "ask_map": [
                {
                    "id": "a1",
                    "question_ids": ["q1"],
                    "ask_text": "見直したい範囲が分かれば、そのまま送ってください。",
                    "why_needed": "相談の入口を先に切るため",
                }
            ],
            "required_moves": ["react_briefly_first", "defer_with_reason", "request_minimum_evidence", "commit_next_update_time"],
        }
        return case

    if scenario == "doc_explanation_request":
        asks_fee = any(marker in raw for marker in ["追加料金", "費用", "料金", "別料金"])
        asks_screenshot_need = "スクショ" in raw and any(marker in raw for marker in ["送った方", "送るべき", "必要", "要りますか", "いりますか"])
        explicit_questions = [{"id": "q1", "text": "もう少しかみ砕いた説明をお願いできるか", "priority": "primary"}]
        answer_map = [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "承諾前に、確認するポイントをもう少し分かりやすく補足できます。",
            }
        ]
        question_ids = ["q1"]
        required_moves = ["react_briefly_first", "answer_directly_now", "request_minimum_evidence", "commit_next_update_time"]
        if asks_screenshot_need:
            explicit_questions.append({"id": "q2", "text": "画面スクショも送った方がよいか", "priority": "secondary"})
            answer_map.append(
                {
                    "question_id": "q2",
                    "disposition": "answer_now",
                    "answer_brief": "画面スクショは、必要になった場合だけこちらからお願いします。",
                }
            )
        if asks_fee:
            next_id = f"q{len(explicit_questions) + 1}"
            explicit_questions.append({"id": next_id, "text": "追加料金がかかるか", "priority": "secondary"})
            answer_map.append(
                {
                    "question_id": next_id,
                    "disposition": "answer_after_check",
                    "answer_brief": "料金は、補足で足りる範囲かを見てからお伝えします。",
                    "hold_reason": "まずはどの部分が難しかったかを見て、補足で足りるかを先に切ります。",
                    "revisit_trigger": "分かりにくかった箇所を受領したあとにお返しします。",
                }
            )
            question_ids.append(next_id)
            required_moves.insert(2, "defer_with_reason")
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": explicit_questions,
            "answer_map": answer_map,
            "ask_map": [
                {
                    "id": "a1",
                    "question_ids": question_ids,
                    "ask_text": "専門用語を減らしてこちらで整理します。追加で特に知りたい箇所があれば、そのまま送ってください。",
                    "why_needed": "補足の範囲で足りるかを判断するため",
                }
            ],
            "required_moves": required_moves,
        }
        return case

    if scenario == "postdelivery_question_window":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [{"id": "q1", "text": "後から出た質問をここで聞いてよいか", "priority": "primary"}],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "ここで聞いてもらって大丈夫です。補足で答えられる範囲ならそのまま返します。",
                }
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now"],
        }
        return case

    if scenario == "same_cause_check":
        same_cause_brief = "同じ原因かどうかは、まず今回の症状を見てからお返しします。"
        same_cause_hold = "納品後の追加確認なので、前回と同じ流れかを先に切ります。"
        same_cause_ask = "気になっている画面か、前と違って見える点をそのまま送ってください。"
        if "サンクスページ" in raw and any(marker in raw for marker in ["崩れ", "表示が崩れ", "表示崩れ"]):
            same_cause_brief = "同じ原因かどうかは、サンクスページの表示崩れも含めて見てからお返しします。"
            same_cause_hold = "前回の修正と同じ流れにつながるか、サンクスページ側も含めて確認します。"
            same_cause_ask = "サンクスページが崩れて見える画面か、前と違って見える点をそのまま送ってください。"
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [{"id": "q1", "text": "これも同じ原因か", "priority": "primary"}],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_after_check",
                    "answer_brief": same_cause_brief,
                    "hold_reason": same_cause_hold,
                    "revisit_trigger": "症状が分かるものを受領したあとに、前回とのつながりをお返しします。",
                }
            ],
            "ask_map": [
                {
                    "id": "a1",
                    "question_ids": ["q1"],
                    "ask_text": same_cause_ask,
                    "why_needed": "同じ原因かを先に切るため",
                }
            ],
            "required_moves": ["react_briefly_first", "defer_with_reason", "request_minimum_evidence", "commit_next_update_time"],
        }
        return case

    if scenario == "price_complaint":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "修正量に対して高く感じる", "priority": "primary"},
                {"id": "q2", "text": "料金の考え方", "priority": "secondary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "高く感じられたことは受け止めています。ご指摘の通り、結果として小さく見える内容だったと思います。",
                },
                {
                    "question_id": "q2",
                    "disposition": "answer_now",
                    "answer_brief": "料金は調査と切り分け、確認を含めた1件分です。",
                },
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now"],
        }
        return case

    if scenario == "approval_wait_request":
        answer_brief = "はい、確認してからの承諾で大丈夫です。"
        if any(marker in source.get("raw_message", "") for marker in ["明日の朝", "本番"]):
            answer_brief = "はい、明日の朝に確認してからの承諾で大丈夫です。"
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [{"id": "q1", "text": "正式な承諾を待ってほしい", "priority": "primary"}],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": answer_brief,
                },
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now"],
        }
        return case

    case["reply_contract"] = {
        "primary_question_id": "q1",
        "explicit_questions": [{"id": "q1", "text": "今回どう進めるか", "priority": "primary"}],
        "answer_map": [
            {
                "question_id": "q1",
                "disposition": "answer_after_check",
                "answer_brief": "はい、確認します。まず前回対応の続きとして扱える話かを確認します。",
                "hold_reason": "納品後のご相談なので、今の確認ポイントを整理してからお返しします。",
                "revisit_trigger": "必要な情報を受領したあとに、どの形で進めるかをお伝えします。",
            }
        ],
        "ask_map": [],
        "required_moves": ["react_briefly_first", "defer_with_reason", "commit_next_update_time"],
    }
    return case


def reaction_line(case: dict) -> str:
    scenario = case["scenario"]
    temperature_plan = case.get("temperature_plan") or {}
    opening_move = temperature_plan.get("opening_move")
    user_signal = temperature_plan.get("user_signal")
    if scenario == "price_complaint":
        return "率直に伝えていただいてありがとうございます。高く感じられた点は受け止めています。"
    if scenario == "redelivery_same_error":
        if "Vercel" in raw and "ステータス" in raw and "切り替わら" in raw:
            return "Vercelのプレビュー環境でステータスが切り替わらないとのこと、確認しました。"
        return "デプロイ後に別のエラーが出ているとのこと、確認しました。"
    if opening_move == "action_first":
        if scenario in {"redelivery_same_error", "side_effect_question"}:
            return "まず今の状況から確認します。"
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
    if scenario == "dashboard_test_label":
        return "納品後の確認ありがとうございます。Stripe画面の表示で気になっている点、確認しました。"
    if scenario == "side_effect_question":
        return "確認ありがとうございます。別の機能で気になる点が出ている件、確認しました。"
    if scenario == "prevention_question":
        return "動作確認ありがとうございます。再発予防についてのご質問、確認しました。"
    if scenario == "redelivery_same_error":
        return "デプロイ後に別のエラーが出ているとのこと、確認しました。"
    if scenario == "approval_ok":
        return "再確認ありがとうございます。今回は問題なく動いているとのこと、確認しました。"
    if scenario == "success_thanks_only":
        return "よかったです。"
    if scenario == "formal_thanks_only":
        return "ご丁寧にありがとうございます。"
    if scenario == "dry_complete_close":
        return ""
    if scenario == "signing_secret_rotation_recurrence":
        return "signing secret を変えた時の再発ですね。"
    if scenario == "delivery_scope_mismatch":
        return "納品内容が期待と違っていたとのこと、確認しました。"
    if scenario == "apply_followup_issue":
        return "反映後にビルドが通らなくなった件、確認しました。"
    if scenario == "doc_status_question":
        return "納品物の表記についての確認ありがとうございます。"
    if scenario == "doc_caution_followup":
        return "決済後の処理が正常に動くようになったとのこと、よかったです。"
    if scenario == "doc_to_bugfix_addon":
        return "追加で修正も相談したいとのこと、確認しました。"
    if scenario == "future_risk_question":
        if any(marker in raw for marker in ["1日に何件", "何件くらいまで", "アクセスが増えた時", "また止まるのかな"]):
            return "動作確認ありがとうございます。"
        return "予防的に見ておきたい点があるとのこと、確認しました。"
    if scenario == "deployment_help_request":
        return "反映のところで止まっている件、確認しました。"
    if scenario == "future_architecture_question":
        return "次のご相談も考えていただいている件、ありがとうございます。"
    if scenario == "doc_explanation_request":
        return "確認手順が少し分かりにくかったとのこと、承知しました。"
    if scenario == "postdelivery_question_window":
        return "後から出た質問の扱いについての確認ありがとうございます。"
    if scenario == "same_cause_check":
        if "サンクスページ" in raw and any(marker in raw for marker in ["崩れ", "表示が崩れ", "表示崩れ"]):
            return "サンクスページの表示が崩れているとのこと、確認しました。"
        return "追加で気になる点が出ている件、確認しました。"
    if scenario == "price_complaint":
        return "率直に伝えていただいてありがとうございます。"
    if scenario == "approval_wait_request":
        if any(marker in raw for marker in ["考えさせてもらって", "考えさせて", "ちょっと考え"]):
            return "もちろん大丈夫です。"
        return "ご連絡ありがとうございます。"
    return "納品後のご連絡、確認しました。"


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


def current_focus_line(case: dict) -> str | None:
    scenario = case["scenario"]
    raw = case.get("raw_message", "")
    if scenario == "dashboard_test_label":
        return "まず、Stripeの表示がテストモードを見ているだけか確認します。"
    if scenario == "approval_test_method":
        return "無理に本番で決済を試さなくても、承諾前の確認としては十分です。"
    if scenario == "pending_webhook_events":
        return "まず、保留中のまま未処理なのか、表示だけ残っているのかを確認します。"
    if scenario == "side_effect_question":
        if "メール" in raw and any(marker in raw for marker in ["体感", "気のせい", "不具合ってほどではない"]) and "承諾" in raw:
            return "もし今後も気になる場面があれば、その時にまた送ってください。"
        if any(marker in raw for marker in ["修正前は問題なかった", "今回の修正が影響", "今回の修正の影響", "修正後に別の問題"]):
            return "まず修正後の差分とメール送信の流れを先に見ます。"
        return "そこを見て、今回の修正とのつながりを確認します。"
    if scenario == "redelivery_same_error":
        return "ローカルでは直っているので、デプロイ後に変わる条件から見ます。"
    if scenario == "delivery_scope_mismatch":
        return "まず、『原因特定と修正』の認識だった点も含めて、納品内容とのずれを確認します。"
    if scenario == "apply_followup_issue":
        return "まず手順の抜けか差分の反映違いかを切り分けます。"
    if scenario == "doc_to_bugfix_addon":
        return "まず今回の補足で足りるか、別の修正相談として切るかを確認します。"
    if scenario == "future_risk_question":
        return "まず今回の修正範囲の近くで気になる点があるかを見ます。"
    if scenario == "future_architecture_question":
        return "まず今回どこまで見直したいかが分かると、入口を整理しやすいです。"
    if scenario == "doc_explanation_request":
        return "まず分かりにくかった箇所を見て、補足で足りるかを確認します。"
    if scenario == "same_cause_check":
        if "サンクスページ" in raw and any(marker in raw for marker in ["崩れ", "表示が崩れ", "表示崩れ"]):
            return "まず前回の修正が反映されている状態かと、サンクスページ側だけで崩れが出ていないかを確認します。"
        return "まず前回と同じ流れの話かを確認します。"
    if scenario == "generic_delivered":
        return None
    return None


def draft_opening_anchor(case: dict) -> str:
    scenario = case["scenario"]
    raw = case.get("raw_message", "")
    if scenario == "success_thanks_only":
        return "よかったです。"
    if scenario == "formal_thanks_only":
        return "ご丁寧にありがとうございます。"
    if scenario == "dashboard_test_label":
        return "Stripeダッシュボードの「テスト」表示が気になっているとのこと、確認しました。"
    if scenario == "approval_test_method":
        return "送信テストまで確認いただいているとのこと、ありがとうございます。"
    if scenario == "side_effect_question":
        if "Webhook" in raw and ("出なくなりました" in raw or "問題なく動" in raw):
            return "Webhookのエラーが出なくなったとのこと、よかったです。"
        if "メール" in raw and ("遅く" in raw or "タイミング" in raw):
            return "決済の件は直っていたとのこと、確認しました。"
        if any(marker in raw for marker in ["修正前は問題なかった", "今回の修正が影響", "今回の修正の影響", "修正後に別の問題"]):
            if "Webhook" in raw:
                return "Webhookの受信は直ったとのこと、確認しました。"
            if any(marker in raw for marker in ["修正いただいた箇所は動いて", "修正した箇所は動いて", "修正箇所は動いて"]):
                return "修正した箇所は動いているとのこと、確認しました。"
            return "修正後に別の機能が気になっている件ですね。"
        if "メール" in raw:
            return "まずメール送信の件から見ます。"
        return "まず別の機能で出ている症状から確認します。"
    if scenario == "prevention_question":
        return "動作確認ありがとうございます。再発予防についてのご質問、確認しました。"
    if scenario == "redelivery_same_error":
        if "Vercel" in raw and "ステータス" in raw and "切り替わら" in raw:
            return "Vercelのプレビュー環境でステータスが切り替わらないとのこと、確認しました。"
        if "Vercel" in raw:
            return "Vercelにデプロイすると500エラーが残るとのこと、確認しました。"
        return "まずデプロイ後に変わる条件から確認します。"
    if scenario == "approval_ok":
        return "今回は問題なく動いているとのこと、確認しました。"
    if scenario == "approval_complete_thanks":
        return "決済テストも通って問題なさそうとのこと、ありがとうございます。"
    if scenario == "approval_ok_with_future_request":
        return "問題なく動いているとのこと、よかったです。"
    if scenario == "approval_reassurance_request":
        return "テストデータで決済までは通っているとのこと、ありがとうございます。"
    if scenario == "tolerated_minor_concern_close":
        return "少し気になる点はあるものの、今は動いているとのことですね。"
    if scenario == "webhook_log_howto":
        return "無事直ったとのこと、よかったです。"
    if scenario == "light_learning_question":
        return "無事直ったとのこと、よかったです。"
    if scenario == "review_content_question":
        return "星5レビューのお気持ち、ありがとうございます。"
    if scenario == "deliverable_share_permission":
        return "動作確認ありがとうございます。"
    if scenario == "extra_fee_reassurance":
        return "ちゃんと動いているとのこと、よかったです。"
    if scenario == "pending_webhook_events":
        return "Webhookの受信は確認できていて、保留中イベントが残っているとのこと、確認しました。"
    if scenario == "future_breakage_reassurance":
        return "今はちゃんと動いているとのこと、よかったです。"
    if scenario == "acceptance_after_support_question":
        return "軽く見た範囲では大丈夫そうとのこと、確認しました。"
    if scenario == "delivered_can_reject":
        return "本番で一部確認できていないとのこと、確認しました。"
    if scenario == "monthly_support_request":
        return "一応動いているとのこと、確認しました。"
    if scenario == "cause_explanation_request":
        return "動作確認ありがとうございます。原因の件、確認しました。"
    if scenario == "workload_reflection_question":
        return "全部問題なく動いたとのこと、よかったです。"
    if scenario == "layout_side_effect_probe":
        return "見た目が少し変わったように見える件、確認しました。"
    if scenario == "extra_scope_after_delivery":
        return "無事動いたとのこと、よかったです。"
    if scenario == "secondary_question_before_acceptance":
        return ""
    if scenario == "backup_diff_request":
        return "Webhookは動いているとのこと、よかったです。"
    if scenario == "delivery_scope_mismatch":
        if "診断レポートだけ" in raw and "修正ファイル" in raw:
            return "納品内容にずれがあったとのこと、確認しました。"
        return "納品内容が期待と違っていたとのこと、確認しました。"
    if scenario == "apply_followup_issue":
        return "まず反映後のビルドエラーから確認します。"
    if scenario == "doc_status_question":
        return "納品物の表記についての確認、ありがとうございます。"
    if scenario == "doc_caution_followup":
        return "決済後の処理が正常に動くようになったとのこと、よかったです。"
    if scenario == "doc_to_bugfix_addon":
        return "追加で修正も相談したいとのこと、確認しました。"
    if scenario == "future_risk_question":
        return "予防的に見ておきたい点があるとのこと、確認しました。"
    if scenario == "deployment_help_request":
        return "本番反映のところで不安がある件、確認しました。"
    if scenario == "future_architecture_question":
        return "次のご相談も考えていただいている件、ありがとうございます。"
    if scenario == "doc_explanation_request":
        return "確認手順が少し分かりにくかったとのこと、承知しました。"
    if scenario == "postdelivery_question_window":
        return "後から出た質問の扱いについての確認、ありがとうございます。"
    if scenario == "same_cause_check":
        return "追加で気になる点が出ている件、確認しました。"
    if scenario == "price_complaint":
        return "率直に伝えていただいてありがとうございます。高く感じられた点は受け止めています。"
    if scenario == "approval_wait_request":
        if any(marker in raw for marker in ["考えさせてもらって", "考えさせて", "ちょっと考え"]):
            return "少し考えたいとのこと、承知しました。"
        return ""
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

    if scenario == "dashboard_test_label":
        _append_unique(paragraphs, direct_answer)
        _append_unique(
            paragraphs,
            _paragraph_from_lines(
                [
                    focus_line or "",
                    "Stripeダッシュボード上部のモード切り替えが見える画面を1枚送ってください。",
                ]
            ),
        )
        return paragraphs

    if scenario == "approval_test_method":
        _append_unique(
            paragraphs,
            _paragraph_from_lines(
                [
                    direct_answer,
                    "Stripeダッシュボードからの送信テストが成功しているなら、受信側の確認としてはそこまでで大丈夫です。",
                    "無理に本番で決済を試さなくても、承諾前の確認としては十分です。",
                ]
            ),
        )
        return paragraphs

    if scenario == "approval_reassurance_request":
        _append_unique(
            paragraphs,
            _paragraph_from_lines(
                [
                    direct_answer,
                    "その前提なら、承諾いただいて大丈夫です。",
                ]
            ),
        )
        return paragraphs

    if scenario == "tolerated_minor_concern_close":
        _append_unique(
            paragraphs,
            _paragraph_from_lines(
                [
                    direct_answer,
                    "もし後でやはり気になるようなら、その時点の状況を送ってください。",
                ]
            ),
        )
        return paragraphs

    if scenario == "webhook_log_howto":
        _append_unique(
            paragraphs,
            _paragraph_from_lines(
                [
                    direct_answer,
                    "対象のWebhookエンドポイントを開くと、イベントごとの送信結果やレスポンスも確認できます。",
                ]
            ),
        )
        return paragraphs

    if scenario == "doc_explanation_request":
        _append_unique(
            paragraphs,
            (
                f"{direct_answer}専門用語を減らしてこちらで整理します。\n"
                "追加で特に知りたい箇所があれば、そのまま送ってください。"
            ),
        )
        return paragraphs

    if scenario == "signing_secret_rotation_recurrence":
        _append_unique(
            paragraphs,
            _paragraph_from_lines(
                [
                    direct_answer,
                    "ローテーションする場合は、Stripe 側の Webhook 設定と受信側で参照している secret を同じ新しいものにそろえれば大丈夫です。",
                ]
            ),
        )
        return paragraphs

    if scenario == "light_learning_question":
        _append_unique(
            paragraphs,
            _paragraph_from_lines(
                [
                    direct_answer,
                    "次に Checkout から Webhook までの流れを一度追ってみると、かなり掴みやすくなります。",
                ]
            ),
        )
        return paragraphs

    if scenario == "review_content_question":
        _append_unique(
            paragraphs,
            _paragraph_from_lines(
                [
                    direct_answer,
                    "公開したくない情報だけ避けてもらえれば問題ありません。",
                ]
            ),
        )
        return paragraphs

    if scenario == "deliverable_share_permission":
        _append_unique(
            paragraphs,
            _paragraph_from_lines(
                [
                    direct_answer,
                    "必要なら、該当箇所だけ抜き出して共有していただいても問題ありません。",
                ]
            ),
        )
        return paragraphs

    if scenario == "extra_fee_reassurance":
        _append_unique(
            paragraphs,
            _paragraph_from_lines(
                [
                    direct_answer,
                    "追加が必要になる場合は、先にこちらからご相談する形なので、そのままご安心ください。",
                ]
            ),
        )
        return paragraphs

    if scenario == "success_thanks_only":
        _append_unique(paragraphs, direct_answer)
        return paragraphs

    if scenario == "formal_thanks_only":
        _append_unique(
            paragraphs,
            _paragraph_from_lines(
                [
                    direct_answer,
                    "また何かあれば、その時の状況を送ってください。",
                ]
            ),
        )
        return paragraphs
    if scenario == "dry_complete_close":
        _append_unique(
            paragraphs,
            _paragraph_from_lines(
                [
                    direct_answer,
                    "また何かあれば、その時の状況を送ってください。",
                ]
            ),
        )
        return paragraphs

    if scenario == "pending_webhook_events":
        _append_unique(paragraphs, direct_answer)
        _append_unique(
            paragraphs,
            _paragraph_from_lines(
                [
                    focus_line or "",
                    "保留中になっているイベント詳細が見える画面があれば、そのまま送ってください。",
                ]
            ),
        )
        return paragraphs

    if scenario == "future_breakage_reassurance":
        _append_unique(
            paragraphs,
            _paragraph_from_lines(
                [
                    direct_answer,
                    "将来の仕様変更まではここで言い切れませんが、現状が安定しているなら承諾いただいて大丈夫です。",
                    "固定の保証期間としてはお伝えしていませんが、今回の動作が安定しているかを基準に見てもらえれば大丈夫です。",
                ]
            ),
        )
        return paragraphs

    if scenario == "approval_wait_request":
        if any(marker in raw for marker in ["本番", "明日の朝"]):
            direct_answer = "はい、明日の朝に確認してからの承諾で大丈夫です。"
        _append_unique(
            paragraphs,
            _paragraph_from_lines(
                [
                    direct_answer,
                    "確認中に気になる点が出てきた場合は、承諾前にこのトークルームで送ってください。",
                ]
            ),
        )
        return paragraphs

    if scenario == "acceptance_after_support_question":
        _append_unique(
            paragraphs,
            _paragraph_from_lines(
                [
                    direct_answer,
                    "まだ確認できていない箇所がある場合は、無理に承諾しなくて大丈夫です。",
                    "承諾後もメッセージで状況確認はできますが、トークルームは閉じるため、そのまま修正作業を続ける前提にはなりません。",
                    "同じ箇所に不具合が残っている可能性がある場合は、内容を確認したうえで対応方法をご相談します。",
                ]
            ),
        )
        return paragraphs

    if scenario == "delivered_can_reject":
        _append_unique(
            paragraphs,
            _paragraph_from_lines(
                [
                    direct_answer,
                    "確認できていない箇所がある場合は、承諾前にこのトークルーム内でお伝えください。",
                    "こちらで確認して、承諾いただいて問題ないかをお返しします。",
                    "承諾後に同じ問題が出た場合は、まずメッセージ上で前回の修正とのつながりを確認します。",
                ]
            ),
        )
        return paragraphs

    if scenario == "monthly_support_request":
        _append_unique(
            paragraphs,
            _paragraph_from_lines(
                [
                    direct_answer,
                    "今回の件で気になる点が残っている場合は、承諾前にこのトークルーム内でお伝えください。",
                    "承諾後に同じ箇所で問題が出た場合は、まずメッセージで状況を確認し、実作業が必要な場合は作業前に対応方法をご相談します。",
                ]
            ),
        )
        return paragraphs

    if scenario == "cause_explanation_request":
        _append_unique(
            paragraphs,
            _paragraph_from_lines(
                [
                    direct_answer,
                    "「自分のコードが全部悪かった」というより、実装側で前提がそろっていなかったイメージです。",
                ]
            ),
        )
        return paragraphs

    if scenario == "workload_reflection_question":
        _append_unique(
            paragraphs,
            _paragraph_from_lines(
                [
                    direct_answer,
                    "Webhookや処理のつながりを見ながら確認する必要があったので、ご自身だけで詰まりやすい内容でした。",
                ]
            ),
        )
        return paragraphs

    if scenario == "layout_side_effect_probe":
        _append_unique(
            paragraphs,
            _paragraph_from_lines(
                [
                    direct_answer,
                    "ただ、今回の差分の影響かどうかは確認します。",
                ]
            ),
        )
        _append_unique(
            paragraphs,
            _paragraph_from_lines(
                [
                    "ヘッダーの余白が広がって見える画面があれば、そのまま送ってください。",
                ]
            ),
        )
        return paragraphs

    if scenario == "approval_complete_thanks":
        _append_unique(paragraphs, direct_answer)
        return paragraphs

    if scenario == "side_effect_question":
        raw = case.get("raw_message", "")
        is_soft_timing_probe = "メール" in raw and any(marker in raw for marker in ["体感", "気のせい", "不具合ってほどではない"]) and "承諾" in raw
        is_post_fix_regression = any(
            marker in raw for marker in ["修正前は問題なかった", "今回の修正が影響", "今回の修正の影響", "修正後に別の問題"]
        )
        if is_soft_timing_probe:
            _append_unique(
                paragraphs,
                _paragraph_from_lines(
                    [direct_answer] + [item["answer_brief"] for item in secondary_now if item.get("answer_brief")]
                ),
            )
            _append_unique(
                paragraphs,
                _paragraph_from_lines(
                    [
                        "もし今後も気になる場面があれば、その時の状況だけ送ってください。",
                    ]
                ),
            )
            return paragraphs
        if is_post_fix_regression:
            _append_unique(paragraphs, direct_answer)
            _append_unique(
                paragraphs,
                _paragraph_from_lines(
                    [
                        focus_line or "",
                        (
                            "前より遅く感じた場面か、どのタイミングでそう見えたかが分かるものをそのまま送ってください。"
                            if ("メール" in raw and ("遅く" in raw or "タイミング" in raw))
                            else "メール送信が止まっていることが分かる画面か、操作手順を送ってください。"
                        ),
                    ]
                ),
            )
            return paragraphs
        _append_unique(
            paragraphs,
            _paragraph_from_lines(
                [direct_answer] + [item["answer_brief"] for item in secondary_now if item.get("answer_brief")]
            ),
        )
        _append_unique(
            paragraphs,
            _paragraph_from_lines(
                [
                    "前より遅く感じた場面か、どのタイミングでそう見えたかが分かるものをそのまま送ってください。"
                    if ("メール" in raw and ("遅く" in raw or "タイミング" in raw))
                    else "メール送信が止まっていることが分かる画面か、操作手順を送ってください。",
                    focus_line or "",
                ]
            ),
        )
        return paragraphs

    if scenario == "delivery_scope_mismatch":
        _append_unique(paragraphs, direct_answer)
        if blocking_missing_facts:
            _append_unique(
                paragraphs,
                _paragraph_from_lines(
                    [
                        "足りないと感じた点を1〜2点だけそのまま送ってください。",
                        "その内容を見て、差し戻しで埋める範囲かをこちらで確認します。",
                    ]
                ),
            )
        else:
            _append_unique(
                paragraphs,
                _paragraph_from_lines(
                    [
                        "ご期待に沿えていない点、すみません。",
                        focus_line or "",
                    ]
                ),
            )
        return paragraphs

    if scenario == "extra_scope_after_delivery":
        _append_unique(
            paragraphs,
            _paragraph_from_lines(
                [
                    direct_answer,
                    "必要なら、読み込みが重いページや気になる場面を見て、別の相談としてご案内できます。",
                    "今の修正が問題なく動いているなら、今回はそのまま区切っていただいて大丈夫です。",
                ]
            ),
        )
        return paragraphs

    if scenario == "secondary_question_before_acceptance":
        _append_unique(
            paragraphs,
            _paragraph_from_lines(
                [
                    direct_answer,
                    "領収書メールが届かない件について、このトークルームで症状だけ送ってください。",
                    "別の不具合として実作業が必要そうな場合は、今回の修正範囲とは分けてご相談します。",
                ]
            ),
        )
        return paragraphs

    if scenario == "backup_diff_request":
        _append_unique(
            paragraphs,
            _paragraph_from_lines(
                [
                    direct_answer,
                    "必要なら、今回変更したファイルや変更点は整理してお伝えできます。",
                ]
            ),
        )
        return paragraphs

    if scenario == "doc_caution_followup":
        _append_unique(
            paragraphs,
            _paragraph_from_lines(
                [
                    direct_answer,
                    "今のところ正常に動いているなら、急ぎで何か変更する必要はありません。",
                    "今後デプロイし直す時に環境変数を入れ直す場合は、その注意点を見ながら進めてもらえれば大丈夫です。",
                ]
            ),
        )
        return paragraphs

    if scenario == "redelivery_same_error":
        _append_unique(paragraphs, direct_answer)
        _append_unique(
            paragraphs,
            _paragraph_from_lines(
                [
                    focus_line or "",
                    (
                        "前回の修正が反映されている状態かと、Vercelのプレビュー環境だけで差が出ていないかを確認します。"
                        if ("Vercel" in raw and "ステータス" in raw and "切り替わら" in raw)
                        else ""
                    ),
                    (
                        "ステータスが切り替わらない場面のスクショがあれば、そのまま送ってください。"
                        if ("Vercel" in raw and "ステータス" in raw and "切り替わら" in raw)
                        else "デプロイ後に出ているエラーの画面かメッセージを送ってください。"
                    ),
                ]
            ),
        )
        return paragraphs

    if scenario == "apply_followup_issue":
        _append_unique(paragraphs, direct_answer)
        _append_unique(
            paragraphs,
            _paragraph_from_lines(
                [
                    focus_line or "",
                    "出ているエラー文が分かれば、そのまま送ってください。",
                ]
            ),
        )
        return paragraphs

    if scenario == "price_complaint":
        _append_unique(
            paragraphs,
            _paragraph_from_lines(
                [direct_answer] + [item["answer_brief"] for item in secondary_now if item.get("answer_brief")]
            ),
        )
        if any(marker in raw for marker in ["価値があったのか", "モヤモヤ", "高い気が", "高かったかも"]):
            _append_unique(
                paragraphs,
                "結果として軽微に見える内容だったからこそ、そう感じさせてしまった点はすみません。",
            )
        return paragraphs

    answer_lines = [direct_answer]
    answer_lines.extend(item["answer_brief"] for item in secondary_now if item.get("answer_brief"))
    _append_unique(paragraphs, _paragraph_from_lines(answer_lines))

    detail_lines: list[str] = []
    if primary["disposition"] == "answer_after_check":
        if focus_line:
            detail_lines.append(focus_line)
        elif primary.get("hold_reason"):
            detail_lines.append(primary["hold_reason"])
    for item in secondary_after:
        if item.get("answer_brief"):
            detail_lines.append(item["answer_brief"])
        if item.get("hold_reason"):
            detail_lines.append(item["hold_reason"])
    detail_paragraph = _paragraph_from_lines(detail_lines)
    if detail_paragraph:
        _append_unique(paragraphs, detail_paragraph)

    if blocking_missing_facts:
        _append_unique(paragraphs, _paragraph_from_lines([ask.get("ask_text", "") for ask in ask_map]))

    return paragraphs


def build_delivered_render_payload(case: dict, opening_block: str, body_paragraphs: list[str], next_action: str) -> dict:
    fixed_slots: dict[str, str] = {}
    if body_paragraphs:
        fixed_slots["answer_core"] = body_paragraphs[0]
    if len(body_paragraphs) > 1:
        fixed_slots["detail_core"] = "\n\n".join(body_paragraphs[1:])
    if next_action:
        fixed_slots["next_action"] = next_action
    return {
        "fixed_slots": fixed_slots,
        "editable_slots": {
            "ack": opening_block,
            "closing": next_action,
        },
        "draft_paragraphs": [opening_block, *body_paragraphs, next_action],
    }


def render_future_architecture_question_case(case: dict) -> str:
    contract = case.get("reply_contract") or {}
    for answer in contract.get("answer_map") or []:
        if answer.get("question_id") == contract.get("primary_question_id"):
            answer["disposition"] = "answer_now"
            answer["answer_brief"] = "全体の構成見直しは、今回の不具合修正とは分けて考えます。"
    case["response_decision_plan"] = build_response_decision_plan(
        {"raw_message": case.get("raw_message", "")},
        case.get("scenario", "generic_delivered"),
        contract,
    )
    case["service_grounding"] = dict(SERVICE_GROUNDING)
    case["hard_constraints"] = build_hard_constraints(case.get("scenario", "generic_delivered"), SERVICE_GROUNDING)
    paragraphs = [
        "ご連絡ありがとうございます。\n無事に動いたとのこと、確認ありがとうございます。\n全体の構成見直しは、今回の不具合修正とは分けて考えます。",
        "今回見た範囲では、不具合の原因になっていた箇所を修正しました。\nリポジトリ全体が悪かった、とまでは断定していません。",
        "金額は見直す範囲によって変わるため、範囲を確認してから個別にご相談します。",
        "ご希望であれば、見直したい範囲を送ってください。",
    ]
    case["render_payload"] = build_delivered_render_payload(case, paragraphs[0], paragraphs[1:], "")
    return "\n\n".join(paragraphs)


def render_case(case: dict) -> str:
    if case.get("scenario") == "future_architecture_question":
        return render_future_architecture_question_case(case)

    if not case.get("response_decision_plan"):
        case["response_decision_plan"] = build_response_decision_plan(
            {"raw_message": case.get("raw_message", "")},
            case.get("scenario", "generic_delivered"),
            case["reply_contract"],
        )
    if not case.get("service_grounding"):
        case["service_grounding"] = dict(SERVICE_GROUNDING)
    if not case.get("hard_constraints"):
        case["hard_constraints"] = build_hard_constraints(case.get("scenario", "generic_delivered"), SERVICE_GROUNDING)

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

    contract = case["reply_contract"]
    primary_id = contract["primary_question_id"]
    primary = next(item for item in contract["answer_map"] if item["question_id"] == primary_id)
    next_action = (
        time_commit_for_scenario(case.get("scenario", "generic_delivered"))
        if (primary["disposition"] == "answer_after_check" or decision_plan.get("blocking_missing_facts"))
        else ""
    )

    sections: list[str] = []
    _append_unique(sections, opening_block)
    for paragraph in body_paragraphs:
        _append_unique(sections, paragraph)
    if next_action:
        _append_unique(sections, next_action)

    case["render_payload"] = build_delivered_render_payload(case, opening_block, body_paragraphs, next_action)
    return "\n\n".join(section for section in sections if section.strip())


def main() -> int:
    parser = argparse.ArgumentParser(description="Render delivered follow-up replies from flat delivered cases.")
    parser.add_argument("--fixture", required=True)
    parser.add_argument("--case-id")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--save", action="store_true")
    args = parser.parse_args()

    cases = shared.load_cases(Path(args.fixture))
    selected = [case for case in cases if case.get("state") == "delivered"]
    if args.case_id:
        selected = [case for case in selected if case.get("case_id") == args.case_id or case.get("id") == args.case_id]
    if args.limit is not None:
        selected = selected[: args.limit]
    if not selected:
        print("[NG] no delivered cases selected")
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
            shared.save_reply(rendered, case["raw_message"])

    print("\n\n----\n\n".join(rendered_blocks))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
