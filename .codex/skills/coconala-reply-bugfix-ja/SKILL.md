---
name: coconala-reply-bugfix-ja
description: "ココナラのNext.js/Stripe/API不具合修正サービス専用。重複質問を避け、自然な日本語で、スコープ事故と規約事故を防ぐ返信を作る。"
---

# ココナラ返信（不具合修正 特化版 v1）

## 目的
- Next.js / Stripe / API連携の不具合修正案件で、送信用返信を短く自然に作る。
- 重複質問を減らし、購入者の不信感を防ぐ。
- 固定条件（価格 / 範囲 / 規約）を崩さない。

## 固定条件（変更禁止）
- 基本料金: 15,000円
- 追加修正1件: 15,000円
- 追加調査30分: 5,000円
- 不具合1件: 同一原因 / 1フロー / 1エンドポイント
- 範囲外: 通話、直接push、本番デプロイ、新機能開発
- セキュリティ: `.env` はキー名のみ（値は不要）
- 禁止: 外部連絡、外部共有、外部決済への誘導
- 禁止: 本番環境での再実行を促すこと（再決済 / 再課金 / Webhook再送 / データ削除など）

## このskillを使う場面
- ユーザーが「返信文作って」「そのまま送れる文面」と依頼したとき
- 購入後のトークルーム初回、追加確認、スコープ判定、納品前後の案内
- `coconala-intake-router-ja` で入口判定を済ませたあと、送信用文面が必要なとき

## このskillを使わない場面
- `state: prequote` の見積り相談で、`#R / #A` 判定から金額分岐まで必要なとき
  - この場合は `coconala-prequote-ops-ja` を優先する
- 相手文の貼り付けだけで、送信用文面の明示依頼がないとき
  - この場合は分析のみを返す

## 先に見るファイル
- `/home/hr-hm/Project/work/ops/common/coconala-rule-guard.md`
- `/home/hr-hm/Project/work/ops/common/output-schema.yaml`
- `/home/hr-hm/Project/work/ops/services/next-stripe-bugfix/service.yaml`
- `/home/hr-hm/Project/work/ops/services/next-stripe-bugfix/evidence-minimum.yaml`
- `/home/hr-hm/Project/work/ops/services/next-stripe-bugfix/scope-matrix.md`
- `/home/hr-hm/Project/work/docs/coconala-japanese-banlist.ja.md`
- `/home/hr-hm/Project/work/docs/coconala-japanese-must-rules.ja.md`
- `/home/hr-hm/Project/work/docs/coconala-golden-replies.ja.md`
- `/home/hr-hm/Project/work/docs/coconala-reply-self-check.ja.md`

## 標準ルート
1. 可能なら先に `coconala-intake-router-ja` を使い、経路・状態・リスク・不足情報を確定する。
2. モードを判定する。
   - UI進行タグ（`#$0` / `#$1` / `#$2` / `#$3`）があるか
   - 文末タグ（`#R` / `#A` / `#D`）があるか
   - `#R 受領返信` などのショート指示があるか
3. 購入者文の既出情報を抽出する（環境 / 症状 / 時期 / エラー / スタック）。
4. 先頭1〜2行で受領 + 要点復唱を入れる。相手が書いた情報を一度拾ってから進める。
5. 重複質問を避けながら、不足情報だけを最大2〜3点で依頼する。
6. 追加質問の前に、現時点の見立てまたは確認観点を1文だけ入れる。
7. 次回報告時刻を入れる。購入後の調査 / 判定フェーズでは `本日[時刻]まで` と `48時間以内` の二段構成を基本にする。
8. 送信用文面モードでは `/home/hr-hm/Project/work/返信文_latest.txt` に保存する。

## 条件付きで読む references
- UI進行タグや `#R` ショート指示を使うとき:
  - `references/ui-progress-tags.ja.md`
- 受領後 / 納品前後 / クローズ前後の購入後フェーズ:
  - `references/post-purchase-stages.ja.md`
- `emotional_caution: true` または苦情寄りの文面:
  - `references/emotional-caution-mode.ja.md`
- 値引き、5,000円、`quote_sent`、`closed` 後などの例外運用:
  - `references/edge-cases.ja.md`
- 複数症状、対象外懸念共有、技術的には可能な別件案内:
  - `references/scope-boundary-phrases.ja.md`
- 文体、Ban表現、Stripe導線、出力ルールの詳細:
  - `references/style-rules.ja.md`
- 参考テンプレが必要なときだけ:
  - `references/scene-templates.ja.md`

## Gotchas
- `prequote` で `#R / #A` を作る時は、先に `coconala-prequote-ops-ja` を使う。金額分岐をこのskillで抱え込まない。
- 5,000円の確認だけ相談は、`/home/hr-hm/Project/work/docs/coconala-golden-replies.ja.md` の §2 を基準にする。`確認案件` `30分の範囲` などの内部向け表現を外向け本文へ出さない。
- `scope_judgement: undecidable` のまま、追加料金や無料対応を断定しない。
- Webhookの複数イベント失敗でも、同一原因なら `bugfix-15000` の守備範囲に残す。
- 複数症状が並ぶ時は、こちらで勝手に「1件目」を決めない。優先順位を確認する。
- `closed` 後の再相談では、最初の返信で `新規依頼` や `規約上は` を前面に出さない。
- `handoff-25000` で修正依頼が出た場合は吸収せず、`bugfix-15000` または別見積りへ切り分ける。
- Stripe確認は `/home/hr-hm/Project/work/stripe日本語UI案内` を最優先参照し、`sk_...` や `whsec_...` の値は求めない。

## 出力ルール
- 行頭に不要な空白を入れない。
- 基本は `です・ます`。
- 結論 -> 理由 -> 次アクション の順に書く。
- 箇条書きは3点以内を優先する。
- 見積り初回は質問票に見せず、質問前に受領した事実か確認観点を1文入れる。
- `2時間以内` は受領確認または一次報告を指す。一次結果は別時刻で明記する。
- 非エンジニア向けでは `ログ` 単語を単独要求しない。
- エラー文やログは、コピーできるならテキスト貼り付けを優先する。コピーしにくい場合だけ画面スクショを代替にする。
- UI状態や見え方の確認では、画面スクショを優先してよい。
- 送信用文面を作ったときは `/home/hr-hm/Project/work/返信文_latest.txt` に保存する。

## 仕上げ前チェック
- 相手の質問に直接答えているか
- 既出情報を聞き直していないか
- 固定条件（価格 / 範囲）を崩していないか
- 外部誘導や秘密情報要求がないか
- 追加質問の前に、受領確認か見立ての1文を入れたか
- 本番での再実行（再決済 / 再課金 / Webhook再送）を促していないか
- 次アクションと時刻が明確か
- 結語が抜け落ちていないか（`.env` 注意文で終わっていないか）
- non_engineer 向けで内部語や強すぎる技術語が混ざっていないか
- Ban表現ヒット0件を確認したか
- `prequote` で本来 `coconala-prequote-ops-ja` に寄せるべき場面を、このskillで無理に処理していないか
- テンプレを使った場合でも、相手の文脈に合わせて調整したか
