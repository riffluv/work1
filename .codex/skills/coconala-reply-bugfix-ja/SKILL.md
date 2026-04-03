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
- 価格・追加料金・公開状態・基本範囲は hardcode せず、毎回 `service-registry.yaml` で `bugfix-15000` を解決して `facts_file` を正本にする
- 確認範囲の説明は `estimate-decision.yaml` と `source_of_truth` を正本にする
- 公開中サービスに確認専用の別料金プランはない
- 不具合1件の扱いは `同一原因 / 1フロー / 1エンドポイント` を基準にする
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

## required_facts
- bugfix の hard facts は、毎回 `/home/hr-hm/Project/work/os/core/service-registry.yaml` と、そこから辿る `facts_file` を正本として読む。
- 現在の公開 bugfix サービスは `bugfix-15000` のみで、価格・追加料金・公開状態・範囲は `service-registry.yaml` で `bugfix-15000` を解決し、その `facts_file` を正本にする。
- 公開状態と外向け自然文の参照は、`service-registry.yaml` の `public` と `source_of_truth` を使う。
- サービスページ本文は外向け自然文の正本として参照してよいが、価格・追加料金・公開状態の機械判定は `service.yaml` を優先する。
- 古いテンプレや過去の返信例に旧確認プラン前提の文面が残っていても、外向け bugfix では採用しない。

## 先に見るファイル
- `/home/hr-hm/Project/work/os/core/service-registry.yaml`
- `/home/hr-hm/Project/work/ops/common/coconala-rule-guard.md`
- `/home/hr-hm/Project/work/ops/common/output-schema.yaml`
- `service-registry.yaml` の `bugfix-15000` から辿る `facts_file`
- `/home/hr-hm/Project/work/ops/services/next-stripe-bugfix/evidence-minimum.yaml`
- `/home/hr-hm/Project/work/ops/services/next-stripe-bugfix/scope-matrix.md`
- `/home/hr-hm/Project/work/docs/coconala-japanese-banlist.ja.md`
- `/home/hr-hm/Project/work/docs/coconala-japanese-must-rules.ja.md`
- `/home/hr-hm/Project/work/docs/reply-quality/README.ja.md`
- `/home/hr-hm/Project/work/docs/reply-quality/ng-expressions.ja.md`
- `/home/hr-hm/Project/work/docs/coconala-golden-replies.ja.md`
- `/home/hr-hm/Project/work/docs/coconala-reply-self-check.ja.md`

## 標準ルート
1. 可能なら先に `coconala-intake-router-ja` を使い、経路・状態・`case_type`・`certainty`・`reply_stance`・`reply_contract` を確定する。
2. モードを判定する。
   - UI進行タグ（`#$0` / `#$1` / `#$2` / `#$3`）があるか
   - 文末タグ（`#R` / `#A` / `#D` / `#P`）があるか
   - `#R 受領返信` などのショート指示があるか
3. `reply_contract.issue_plan` がある場合は、明示質問や別論点を `今答える / 確認後に返す / 相手に依頼する / 断る` へ先に割り付ける。
4. `reply_skeleton` に沿って section order を固定し、各 section に必要な論点だけを入れる。
5. 先頭1〜2行で受領 + 要点復唱、または短い反応を入れる。相手が書いた情報を一度拾ってから進める。
6. `required_moves` を落とさず、`forbidden_moves` を踏まない範囲で本文を埋める。
7. 重複質問を避けながら、不足情報だけを最大2〜3点で依頼する。
8. 追加質問の前に、現時点の見立てまたは確認観点を1文だけ入れる。
9. 次回報告時刻を入れる。購入後の調査 / 判定フェーズでは `本日[時刻]まで` と `48時間以内` の二段構成を基本にする。
10. `/home/hr-hm/Project/work/docs/reply-quality/ng-expressions.ja.md` で再発しやすい NG 表現を落とす。
11. 近い場面があれば `/home/hr-hm/Project/work/docs/coconala-golden-replies.ja.md` と `/home/hr-hm/Project/work/docs/reply-quality/gold-replies/README.ja.md` を見て、温度感と依頼数の基準を合わせる。
12. 送信用文面は、毎回 `japanese-chat-natural-ja` で最終自然化する。
13. 自然化後も section order と `required_moves / forbidden_moves` を崩していないか確認する。
14. 送信用文面モードでは `/home/hr-hm/Project/work/runtime/replies/latest.txt` に保存する。相手文が明確なときは `/home/hr-hm/Project/work/runtime/replies/latest-source.txt` にも保存する。

## `reply_contract` の使い方
- `reply_contract` はヒントではなく、下流が守る実行契約として扱う。
- `issue_plan` は、明示質問や実質別論点をどう処理するかの割り付けとして使う。
- `answer_now` の論点だけを即答し、`answer_after_check` の論点は理由つきで保留する。
- `ask_client` は、相手にしか出せない最小証跡だけを依頼する。
- `decline` は、規約・公開状態・範囲の理由がある時だけ使う。
- `required_moves` にある動きは必ず文面へ反映する。
- `forbidden_moves` にある動きは、理由が分かっていても本文へ出さない。

## skeleton ごとの固定骨格
- `estimate_initial`: 受け止め -> 結論 -> 価格/購入導線 or 最小質問
- `estimate_followup`: 結論 -> 追加情報 -> 次アクション
- `post_purchase_receipt`: 受領確認 -> 確認対象 -> 時刻コミット
- `post_purchase_quick`: 短い反応 -> 今答えること -> 確認後に返すこと -> 最小依頼 -> 時刻
- `post_purchase_report`: 現状 -> 判明事項 -> 次ステップ -> 時刻コミット
- `delivery`: 確認依頼 -> 確認ポイント -> 次ステップ

## 条件付きで読む references
- UI進行タグや `#R` / `#P` ショート指示を使うとき:
  - `references/ui-progress-tags.ja.md`
- 受領後 / 納品前後 / クローズ前後の購入後フェーズ:
  - `references/post-purchase-stages.ja.md`
- `emotional_caution: true` または苦情寄りの文面:
  - `references/emotional-caution-mode.ja.md`
- 値引き、`quote_sent`、`closed` 後などの例外運用:
  - `references/edge-cases.ja.md`
- 複数症状、対象外懸念共有、技術的には可能な別件案内:
  - `references/scope-boundary-phrases.ja.md`
- 文体、Ban表現、Stripe導線、出力ルールの詳細:
  - `references/style-rules.ja.md`
- 参考テンプレが必要なときだけ:
  - `references/scene-templates.ja.md`

## Gotchas
- `reply_contract` があるのに、本文生成側で再解釈しない。特に `issue_plan` の `answer_after_check` を、良かれと思って即答へ変えない。
- `prequote` で `#R / #A` を作る時は、先に `coconala-prequote-ops-ja` を使う。金額分岐をこのskillで抱え込まない。
- `scope_judgement: undecidable` のまま、追加料金や無料対応を断定しない。
- Webhookの複数イベント失敗でも、同一原因なら `bugfix-15000` の守備範囲に残す。
- 複数症状が並ぶ時は、こちらで勝手に「1件目」を決めない。優先順位を確認する。
- `closed` 後の再相談では、最初の返信で `新規依頼` や `規約上は` を前面に出さない。
- `handoff-25000` で修正依頼が出た場合は吸収せず、`bugfix-15000` または別見積りへ切り分ける。
- Stripe確認は `/home/hr-hm/Project/work/stripe日本語UI案内` を最優先参照し、`sk_...` や `whsec_...` の値は求めない。
- 購入後の継続会話では、初回ヒアリングや受付窓口の文面に戻らない。相手の追加報告へ一度反応してから、不足分だけを軽く頼む。
- 購入後の追加報告に対して、`次の2点だけお願いします` の番号リストを機械適用しない。2点程度なら文中にさらっと混ぜる形を優先する。
- 購入後の継続会話では、`同一原因` `別原因` の内部寄りの言い方を避け、`同じ原因` `別の話` `別の原因かもしれない` など会話の言い方を優先する。

## 出力ルール
- 行頭に不要な空白を入れない。
- 基本は `です・ます`。
- 結論 -> 理由 -> 次アクション の順に書く。
- `reply_skeleton` で決めた section order を崩さない。
- 箇条書きは3点以内を優先する。
- 見積り初回は質問票に見せず、質問前に受領した事実か確認観点を1文入れる。
- `2時間以内` は受領確認または一次報告を指す。一次結果は別時刻で明記する。
- 非エンジニア向けでは `ログ` 単語を単独要求しない。
- エラー文やログは、コピーできるならテキスト貼り付けを優先する。コピーしにくい場合だけ画面スクショを代替にする。
- UI状態や見え方の確認では、画面スクショを優先してよい。
- 送信用文面は、保存前に毎回 `japanese-chat-natural-ja` を通す。
- 最終自然化では、結論・質問項目数・価格・禁止事項・次アクション・section order・required_moves を増減させない。
- `〜する形が安全です` のような提案書寄りの言い方は避け、`〜するのがよさそうです` を優先する。
- 条件がそろうと判断しやすくなる場面では、`出しやすいです` より `出しやすくなります` を優先する。
- 前段で挙げた項目を受ける依頼は、`上の3点を` のように対象を明示して省略しすぎない。
- 送信用文面を作ったときは `/home/hr-hm/Project/work/runtime/replies/latest.txt` に保存する。相手文があるときは `latest-source.txt` も更新する。
- 購入後の継続会話では、相手の追加報告に短く反応してから本題へ入る。`別のページでもですか。` `ログイン画面も崩れていますか。` のような一言で十分。
- 購入後の継続会話では、情報依頼を文中に混ぜる形を優先する。番号リストは3点以上、または取りこぼしが起きやすい時だけ使う。
- 購入後の継続会話では、`いただければ、共有します` のSLA文より `もらえると助かります` `本日[時刻]までに共有しますね` のようなチャット口調を優先する。
- purchased で `issue_plan` が混在する時は、即答できるものだけ答え、残りは `確認してから返す` と分けて書く。

## 仕上げ前チェック
- 相手の質問に直接答えているか
- `issue_plan` の各論点が、`今答える / 確認後に返す / 依頼する / 断る` のどれかへ過不足なく落ちているか
- `reply_skeleton` と最終文面の骨格が一致しているか
- `required_moves` が落ちていないか / `forbidden_moves` を踏んでいないか
- 既出情報を聞き直していないか
- 固定条件（価格 / 範囲）を崩していないか
- 外部誘導や秘密情報要求がないか
- 追加質問の前に、受領確認か見立ての1文を入れたか
- 本番での再実行（再決済 / 再課金 / Webhook再送）を促していないか
- 次アクションと時刻が明確か
- 結語が抜け落ちていないか（`.env` 注意文で終わっていないか）
- non_engineer 向けで内部語や強すぎる技術語が混ざっていないか
- `/home/hr-hm/Project/work/docs/reply-quality/ng-expressions.ja.md` の NG 表現が残っていないか
- Ban表現ヒット0件を確認したか
- `prequote` で本来 `coconala-prequote-ops-ja` に寄せるべき場面を、このskillで無理に処理していないか
- テンプレを使った場合でも、相手の文脈に合わせて調整したか
- 公開 bugfix で確認専用の別料金案内が再発していないか
