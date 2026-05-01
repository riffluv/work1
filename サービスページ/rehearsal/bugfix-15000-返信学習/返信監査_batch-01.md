# bugfix-15000 返信監査 batch

batch_id: `RE-2026-05-01-bugfix-95-post-gate-smoke-r0`
status: `r1 revised / post v1-gate smoke / external audit minor fixes / local validation OK`
fixture: `/home/hr-hm/Project/work/ops/tests/quality-cases/active/post-gate-smoke-bugfix95.yaml`
mode: `coconala`
service: `bugfix-15000`
candidate_source: `writer_candidate_manual`
audit_target: `writer_candidate`
contract_source: `deterministic_renderer`
writer_used: `true`
naturalizer: `manual_japanese_chat_natural`
writer_brief_command: `python3 scripts/render-coconala-reply.py --fixture ops/tests/quality-cases/active/post-gate-smoke-bugfix95.yaml --case-id <CASE_ID> --writer-brief`
writer_candidate_validation: `python3 scripts/render-coconala-reply.py --fixture ops/tests/quality-cases/active/post-gate-smoke-bugfix95.yaml --case-id <CASE_ID> --candidate-file <reply.txt> --lint`
writer_candidate_batch_validation: `python3 scripts/render-coconala-reply.py --fixture ops/tests/quality-cases/active/post-gate-smoke-bugfix95.yaml --candidate-batch-file サービスページ/rehearsal/bugfix-15000-返信学習/返信監査_batch-01.md --lint`

local_validation:
- writer_candidate_batch_validation: OK `8 case(s)`
- v1_completion_gate: OK `v1_completion_candidate with known gaps`
- git_diff_check: OK
- os_check: OK `mode=coconala`

## 前提

- 通常 live / #RE の監査です。
- 外向けに案内してよいサービスは `bugfix-15000` のみです。
- `handoff-25000` は public:false のため、返信候補内に `handoff-25000` / 25,000円 / 主要1フロー整理 / handoff 購入導線が出ていたら public leak として扱ってください。
- この batch の返信候補は `writer_candidate_manual` です。同じ fixture の意味契約をもとに、#R 相当の外向け返信候補として監査してください。
- 直近で `v1 completion gate` と `real stock intake gate` を追加した後の軽い smoke です。gate 追加は返信本文を変えるものではありませんが、現時点の #RE 用 writer candidate が壊れていないか確認します。
- 自然化のために、サービスの意味・価格・scope・phase・secret・payment route・closed 後の実作業境界を変えてはいけません。

## 監査で見てほしい点

1. `handoff-25000` / 25,000円 / 主要1フロー整理の live 漏れがないか
2. `bugfix-15000` の 15,000円・不具合1件・原因確認・修正可能時の修正済みファイル返却の軸に grounded しているか
3. `prequote / quote_sent / purchased / delivered / closed` の phase が崩れていないか
4. quote_sent で、軽い手順確認は通常フローを先に案内し、境界突破要求では支払い前作業・GitHub作業面化を止められているか
5. purchased で、相手文にない技術語・原因候補・作業状況を足していないか
6. delivered で、`補足できます` のような対応可否宣言で止まらず、こちらが返す内容へ進めているか
7. closed で、メッセージ上の関係確認と実作業前相談を分け、無料修正・返金・旧トークルーム継続を約束していないか
8. 低リスク場面で処理文・条件文が同じリズムで並びすぎていないか。ただし高リスク境界は必要な硬さを許容してください

---

## B01

stock_id: HRC95-001
状態: prequote
主質問タイプ: prequote_unknown_cause_can_consult
最初に答えるべき問い: 原因が分からない状態でも15,000円で依頼できるか知りたい。
選定意図: 依頼可否に `相談できます` だけで返さず、成功保証にも寄せない。
r0_local_lint: OK

相手文:

> Stripe決済後に注文が作られないのですが、原因がまったく分かっていません。この状態でも15,000円で依頼できますか？

返信候補:

> 原因が分からない状態でも、Stripe決済後に注文が作られない不具合として15,000円でご依頼いただけます。
>
> コードとエラー内容を見る前に、必ず直せるとまではお約束できません。ご購入後に原因確認から進め、修正できる箇所が特定できた場合は修正済みファイルをお返しします。
>
> この内容で問題なければ、そのままご購入ください。

---

## B02

stock_id: HRC95-002
状態: prequote
主質問タイプ: prequote_materials_after_purchase
最初に答えるべき問い: コードに詳しくなくても依頼できるか、購入後に何を送ればよいか知りたい。
選定意図: 非エンジニア不安。購入前に材料提出を求めすぎず、購入後トークルーム共有と secret 除外を自然に出す。
r0_local_lint: OK

相手文:

> コードに詳しくないので、どのファイルを送ればいいか分かりません。それでも依頼できますか？購入した後は何を送ればいいですか？

返信候補:

> コードの内容に詳しくなくてもご依頼いただけます。最初から必要なファイルをすべて選び切る必要はありません。
>
> ご購入後は、まずエラー内容や画面、分かる範囲の関係ファイルをトークルームで共有してください。こちらで必要な範囲を見ながら、不足があれば追加でお伝えします。
>
> APIキーや .env の値などの秘密情報は含めないでください。
>
> この内容で問題なければ、そのままご購入ください。

---

## B03

stock_id: HRC95-003
状態: quote_sent
主質問タイプ: quote_sent_file_share_timing
最初に答えるべき問い: 見積り提案後、支払い後にスクショやログをまとめて送ればよいか、追加準備が必要か知りたい。
選定意図: 軽い手順確認。拒否先行ではなく通常フローを先に案内する。
r0_local_lint: OK

相手文:

> 見積り提案ありがとうございます。支払い後にスクショとログをまとめて送る流れで問題ありませんか？追加で準備するものがあれば教えてください。

返信候補:

> お支払い完了後に、スクショとログをトークルームでまとめて共有してください。
>
> 追加で必要なものがあれば、共有いただいた内容を見たうえでこちらからお伝えします。その内容をもとに、原因確認から進めます。
>
> 見積り提案の内容で問題なければ、そのままご購入手続きへ進んでください。

---

## B04

stock_id: HRC95-004
状態: quote_sent
主質問タイプ: quote_sent_cause_only_before_payment
最初に答えるべき問い: 支払い前にGitHub招待で原因だけ確認してもらえるか知りたい。
選定意図: 境界突破要求。GitHub作業面化と支払い前診断を止め、購入後トークルーム内共有へ戻す。
r0_local_lint: OK

相手文:

> 見積り提案ありがとうございます。支払い前にGitHubへ招待するので、原因だけ先に確認してもらえますか？直りそうなら購入します。

返信候補:

> 支払い前にGitHub上でコードを確認し、原因だけ先に見る形では進めていません。
>
> 原因確認や修正作業は、お支払い完了後にトークルームで共有いただいた内容をもとに始めます。GitHub招待ではなく、関係ファイルやログをZIPまたは添付で送ってください。
>
> 見積り提案の内容で問題なければ、そのままご購入手続きへ進んでください。

---

## B05

stock_id: HRC95-005
状態: purchased
主質問タイプ: purchased_progress_brief_update
最初に答えるべき問い: 購入後、送ったログとスクショは届いているか、追加準備の有無を知りたい。
選定意図: 二重受領や `はい、確認できています` に戻らず、材料ベースで次の流れを返す。
r0_local_lint: OK

相手文:

> 購入後です。昨日ログとスクショを送りました。届いていますか？この後の流れと、追加で用意した方がいいものがあるかだけ教えてください。

返信候補:

> ログとスクショありがとうございます。
>
> 昨日のログとスクショは届いています。まず受け取っている内容を確認し、追加で必要なものが出た場合は、その時点でこちらからお伝えします。
>
> いまの時点で、追加で準備いただくものはありません。
>
> 本日18:00までに、現時点の確認結果をお返しします。

---

## B06

stock_id: HRC95-006
状態: purchased
主質問タイプ: purchased_progress_deadline_followup
最初に答えるべき問い: 購入後、急ぎでどこまで見通しが出るか知りたい。
選定意図: 修正完了時刻を保証せず、材料がそろった後の見通し返答へ調整する。
r0_local_lint: OK

相手文:

> 購入後です。本番が止まっているので急いでいます。原因や修正の見通しだけでも早めに出せそうですか？

返信候補:

> 急ぎの状況、承知しました。
>
> 修正完了の時刻まではお約束できませんが、必要な材料がそろっている範囲で、原因の方向性や次に見る箇所を確認します。
>
> 現時点で見えている範囲と次の見通しは、まず本日18:00までにお返しします。

---

## B07

stock_id: HRC95-007
状態: delivered
主質問タイプ: delivered_light_explanation
最初に答えるべき問い: 納品後・承諾前に、どの修正ファイルを反映すればよいか短く知りたい。
選定意図: 対応可否宣言で止まらず、こちらが短く整理して返す。
r0_local_lint: OK

相手文:

> 納品ありがとうございます。修正ファイルは受け取りました。承諾前に、どの修正ファイルを反映すればいいかだけもう一度短く教えてください。

返信候補:

> 反映する修正ファイルだけ、こちらで短く整理します。
>
> 承諾前に必要な範囲に絞って、どの修正ファイルを反映すればよいか分かりやすくお伝えします。
>
> 短く整理して、補足説明をお送りします。

---

## B08

stock_id: HRC95-008
状態: closed
主質問タイプ: closed_relation_check_before_new_request
最初に答えるべき問い: クローズ後、似たStripeエラーが前回修正と関係あるかだけ見てもらえるか知りたい。
選定意図: closed 後の関係確認と実作業前相談を分ける。無料・返金・旧トークルーム継続を約束しない。
r0_local_lint: OK

相手文:

> クローズ後ですみません。似たStripeエラーが出ています。ログとスクショをこのメッセージで送れば、前回の修正と関係あるかだけ見てもらえますか？必要なら新規で相談します。

返信候補:

> ログとスクショは、このメッセージ上で送っていただいて大丈夫です。届いた範囲で、前回の修正と関係がありそうかを確認します。
>
> 前回トークルームは閉じているため、この場で修正作業や修正済みファイルの返却までは進めません。
>
> 実作業が必要そうな場合は、対応方法と費用を先にご相談します。
