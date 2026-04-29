# bugfix-15000 返信監査 batch

## batch_manifest

- batch_id: RE-2026-04-29-bugfix-46-post-pro-review-lenses-r2-human-polish
- shortcut: `#RE`
- 対象サービス: `bugfix-15000` の通常 live 返信
- 状態: r2 human-polished
- 件数: 8件
- fixture: `/home/hr-hm/Project/work/ops/tests/quality-cases/active/post-pro-review-lenses-bugfix46.yaml`
- 生成: `python3 scripts/render-coconala-reply.py --fixture ops/tests/quality-cases/active/post-pro-review-lenses-bugfix46.yaml --lint`
- ローカル確認: unified reply lint OK / single-source regression OK / quote-sent lint OK / post-purchase lint OK / closed lint OK / role suites OK

## 目的

Pro後に監査プロンプトへ追加した5つの soft lens が、通常 live の `bugfix-15000` 監査でノイズにならず、実務上の違和感を拾えるか確認する。

今回の重点は次の5つ。

- `source_traceability`: 価格・scope・deliverable・禁止事項が正本から来ているように見えるか
- `commitment_budget`: 受領証拠量や phase に対して、約束が強すぎないか
- `semantic_grounding_drift`: service page / facts / renderer の意味がズレていないか
- `shadow_to_live_contamination`: buyer 文に 25,000円や整理語があっても、通常 live に private handoff 導線が漏れないか
- `evidence_minimality`: buyer が出した情報を聞き直さず、必要最小限の材料だけを依頼しているか

## local preflight

初回生成では、監査前に次の local lint fail を最小修正した。

- HRC46-001: 100%保証 / 直らなかった場合の質問で、追加料金や追加作業が勝手に進まない線が不足したため、保証質問 renderer に `勝手に料金が増えたり、そのまま追加作業へ進むことはありません` を追加した
- HRC46-004: quote_sent で `購入前にコード・ログ・原因を先に見る` 相談が generic quote に吸収されたため、quote_sent renderer の検知順を調整し、購入前材料送付を先に拾うようにした
- HRC46-005: purchased で `届いていますか` の表記揺れが `received_materials_flow_check` に入らず generic fallback になったため、検知語に `届いていますか` を追加した

## r0 外部監査の軽微反映

r0 は採用圏 / 必須修正なし。`handoff-25000` / 25,000円 / 主要1フロー整理の live 漏れもなし。

- B01: buyer が症状をすでに書いているため、最後の聞き直しをやめ、購入導線に締めた
- B03: 相手文にない `Webhookエラー` を足していたため、`Stripe決済後に注文が作られない件` へ戻した
- B07: buyer は補足説明を求めているため、追加質問を前提にせず、こちらで先に補足を整理する文へ寄せた

## r1 外部再監査 + human audit 反映

r1 は採用 / 必須修正なし。`handoff-25000` / 25,000円 / 主要1フロー整理の live 漏れもなし。

- B08: 外部再監査の preference として、`まず確認材料として見ます` を `まずは内容を確認します` へ自然化した
- B05: human audit で、`確認しました` 直後の `はい、確認できています` が bot 感のある二重受領として指摘されたため、`ログとスクショありがとうございます` -> `昨日のログとスクショは届いています` -> この後の流れ、の順へ修正した
- rule 戻し: `確認しました` / `受け取りました` の直後に `はい、〜確認できています` を重ねないルールを `japanese-chat-natural-ja` / `ng-expressions` / quality lint へ戻した

## service facts

- 現時点の外向け live は `bugfix-15000` のみ
- `bugfix-15000`: 15,000円 / Next.js・Stripe・API連携の不具合1件修正 / 原因確認から修正済みファイル返却まで進める前提
- `handoff-25000`: public:false。通常 live / #RE ではサービス名・25,000円・購入導線を出さない
- `.env` / APIキー / Webhook secret / DB接続文字列など、生の秘密情報は扱わない
- 通話、外部共有、外部決済、直接 push、本番デプロイ代行、新機能追加はしない

## 構成

- B01: prequote / guarantee and completion gate
- B02: prequote / raw secret inventory
- B03: prequote / shadow wording in buyer text + bugfix-first
- B04: quote_sent / prepayment materials before payment
- B05: purchased / received materials and evidence minimality
- B06: purchased / key names only and secret safety
- B07: delivered / light explanation after delivery
- B08: closed / relation check before new request

## 監査で見てほしい点

1. `handoff-25000` / 25,000円 / 主要1フロー整理の live 漏れがないか
2. `bugfix-15000` の 15,000円・不具合1件・修正済みファイル返却の軸に grounded しているか
3. Pro後5レンズが soft lens として機能しているか。hard fail 化しすぎていないか
4. 保証、追加料金、購入前原因確認、closed 後実作業などの約束が強すぎないか
5. buyer がすでに出した情報を聞き直していないか
6. quote_sent / purchased / delivered / closed の phase が崩れていないか
7. 相手文にない技術語・機能名・サービス導線・支払い導線を足していないか
8. 返信が重すぎたり、内部ルール説明になっていないか
9. 必須修正がある場合、`case_fix / pattern_candidate / rule_return_candidate / validator / renderer` のどこへ戻すべきか

---

## B01

stock_id: HRC46-001
状態: prequote
主質問タイプ: guarantee_or_refund_question
最初に答えるべき問い: 100%直せる保証や、直らなかった場合の扱いを事前に知りたい。
選定意図: commitment_budget。受注前に修正成功保証や返金保証を強く約束せず、原因確認から修正済みファイル返却までの成果単位を説明できるかを見る。
r2_local_lint: OK

相手文:

> Stripe決済後に注文が作られない不具合です。15,000円でお願いしたいのですが、100%直せる保証はありますか？直らなかった場合はどうなりますか？

返信候補:

> メッセージありがとうございます。
>
> 100%直せるとはお約束しておらず、案件ごとに環境やコードの状態が違うため、原因特定率を一律の数字でお伝えすることもしていません。
>
> 15,000円は、不具合1件について原因確認から修正、修正済みファイルの返却まで進める前提の料金です。
> 原因や修正方針につながらず、修正済みファイルを返せない状態のまま、一方的に正式納品へ進めることはありません。
>
> 確認中に別原因や別作業が必要だと分かった場合も、勝手に料金が増えたり、そのまま追加作業へ進むことはありません。
>
> この内容で進める場合は、そのままご購入ください。

---

## B02

stock_id: HRC46-002
状態: prequote
主質問タイプ: raw_secret_inventory
最初に答えるべき問い: APIキーやWebhook secretや.envの値そのものを一覧化して送ればよいか。
選定意図: evidence_minimality / secret safety。secret 生値を求めず、キー名・設定箇所・用途・エラー内容までに留めるかを見る。
r2_local_lint: OK

相手文:

> StripeのAPIキー、Webhook secret、.envの値、DATABASE_URLを全部一覧にして送った方が早いですか？不具合修正の範囲で確認してほしいです。

返信候補:

> ご相談ありがとうございます。
> APIキー、Webhook secret、.envの値、DB接続文字列などの値そのものを一覧化する作業は対応できません。
>
> 値をこちらへ送っていただく必要もありません。
>
> 不具合修正で設定まわりを確認する場合も、扱うのはキー名、設定箇所、用途、エラー内容までです。secret の値そのものは送らずに進めます。

---

## B03

stock_id: HRC46-003
状態: prequote
主質問タイプ: shadow_word_in_live_bugfix_first
最初に答えるべき問い: 25,000円の整理ではなく、まず今止まっている不具合から相談してよいか。
選定意図: shadow_to_live_contamination。buyer 文に 25,000円や整理が出ても、未公開 handoff 導線へ寄せず、active defect は bugfix-first で返せるかを見る。
r2_local_lint: OK

相手文:

> コード全体が分からないので、25,000円の整理を先にやった方がいいのか迷っています。ただ、今はStripe決済後に注文が作られないのを早く直したいです。まず15,000円の不具合修正で相談して大丈夫ですか？

返信候補:

> ご相談ありがとうございます。
> はい、Stripe決済後に注文が作られない件は、15,000円の不具合修正で確認できます。
>
> コード全体を整理し直す前提ではなく、不具合修正に必要な範囲を確認します。
>
> 今回の範囲だけでは修正完了まで進められないと分かった場合は、そこで止めてご説明します。
> 勝手に料金が増えたり、そのまま追加作業へ進むことはありません。
>
> この内容で進める場合は、ご購入後にエラー内容やログを送ってください。

---

## B04

stock_id: HRC46-004
状態: quote_sent
主質問タイプ: quote_sent_evidence_before_payment
最初に答えるべき問い: 見積り提案後、支払い前にEvent IDやログを送れば先に判断してもらえるか。
選定意図: commitment_budget / phase boundary。quote_sent で購入前作業開始へ滑らず、購入後に確認を始める線を返せるかを見る。
r2_local_lint: OK

相手文:

> 見積り提案ありがとうございます。購入前ですが、先にコードとStripeのEvent ID、Vercelログを送れば、原因だけ先に見てもらえますか？それで問題なければ購入します。

返信候補:

> ご連絡ありがとうございます。
> 提案内容と、支払い前に原因だけ見てもらえるかの件ですね。
>
> 支払い前にコードやログを受け取って原因確認を進めることはしていません。
> 原因確認や作業は、ご購入後に始めます。
>
> ご購入後にコードやログを送ってください。受領後、原因確認から進めます。
>
> この内容で問題なければ、お支払い完了後にトークルームで必要情報を送ってください。

---

## B05

stock_id: HRC46-005
状態: purchased
主質問タイプ: purchased_materials_received_flow
最初に答えるべき問い: 昨日送ったログとスクショは届いているか、追加で用意するものがあるか。
選定意図: evidence_minimality。既出材料を聞き直さず、追加で必要なものがなければ増やさないかを見る。
r2_local_lint: OK

相手文:

> 昨日、StripeのEvent IDが分かるログとスクショを送りました。届いていますか？この後の流れと、追加で用意した方がいいものがあるかだけ教えてください。

返信候補:

> ログとスクショありがとうございます。
>
> 昨日のログとスクショは届いています。
> まず受け取っている内容をこちらで確認して、追加で必要なものがあればその時点でこちらからお願いします。
> いまの時点で、追加で準備いただくものはありません。
>
> 本日18:21までに、現時点の確認結果をお返しします。

---

## B06

stock_id: HRC46-006
状態: purchased
主質問タイプ: purchased_key_names_only
最初に答えるべき問い: Stripe関連のキー名だけ共有した状態で足りるか、値も必要か。
選定意図: evidence_minimality / secret safety。キー名で足りる場合に、値の共有を求めずに進められるかを見る。
r2_local_lint: OK

相手文:

> Stripe関連のキー名だけ共有しました。STRIPE_SECRET_KEY と STRIPE_WEBHOOK_SECRET の値そのものはまだ送っていません。このままで確認できますか？

返信候補:

> ありがとうございます。
> キー名の共有、確認しました。
>
> この情報で確認を進めます。値の方は引き続き送らなくて大丈夫です。
>
> 本日18:21までに、現時点の確認結果をお返しします。

---

## B07

stock_id: HRC46-007
状態: delivered
主質問タイプ: delivered_light_explanation
最初に答えるべき問い: 納品後、修正ファイルと確認手順をもう少し分かりやすく補足してもらえるか。
選定意図: commitment_budget。軽い補足説明は受けつつ、本格資料作成や別サービス導線へ広げないかを見る。
r2_local_lint: OK

相手文:

> 納品ありがとうございます。修正ファイルと確認手順は受け取りましたが、専門用語が少し難しいです。承諾前に、どこを確認すればいいかもう少し分かりやすく説明してもらえますか？

返信候補:

> ご連絡ありがとうございます。
> 資料が少し難しかったとのこと、確認しました。
>
> はい、修正ファイルと確認手順を、もう少し分かりやすく補足できます。
>
> 補足はこちらで先に整理します。追加で特に知りたい箇所があれば、そのまま送ってください。
>
> 本日18:21までに、補足説明をお送りします。

---

## B08

stock_id: HRC46-008
状態: closed
主質問タイプ: closed_relation_check_before_new_request
最初に答えるべき問い: クローズ後、ログやスクショをこのメッセージで送れば前回修正との関係だけ見てもらえるか。
選定意図: closed boundary / evidence_minimality。材料確認と実作業開始を分け、旧トークルーム継続や無料修正を約束しないかを見る。
r2_local_lint: OK

相手文:

> クローズ後ですみません。似たStripeエラーが出ています。ログとスクショをこのメッセージで送れば、前回の修正と関係あるかだけ見てもらえますか？実際に直す必要がありそうなら新規で相談します。

返信候補:

> ご連絡ありがとうございます。
> まずは内容を確認します。
>
> はい、ログやスクショで、前回の修正と関係があるかをこのメッセージ上で確認します。
>
> トークルームは閉じているため、ここで修正作業や修正済みファイルの返却までは進めません。
> ログやスクショを送ってください。
> 実作業が必要と分かった場合は、見積り提案または新規依頼としてご案内します。
>
> 送っていただいた範囲で、見立てを短くお返しします。
