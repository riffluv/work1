# 返信監査 batch 16（#BR / boundary-routing shadow）

## batch_manifest

- batch_id: BR-2026-04-29-boundary-routing-shadow-16
- shortcut: `#BR`
- 目的: Pro 4/29 対応後に、source cleanup / public-private wording separation / payment-route isolation / delivery-completion microstate が崩れていないか確認する
- 状態: r1 light revised
- 件数: 8件
- 対象: prequote / delivered / closed の境界ルーティング
- 公開状態: `bugfix-15000` は live、`handoff-25000` は training-visible / future-dual simulation
- 注意: 通常 live 返信では `handoff-25000` のサービス名・25,000円・購入導線を出さない
- 正本メモ: `/home/hr-hm/Project/work/docs/reply-quality/boundary-routing-shadow-rehearsal.ja.md`
- fixture: `/home/hr-hm/Project/work/ops/tests/quality-cases/active/boundary-routing-shadow-br16.yaml`
- 補足: 今回は Pro 4/29 後の確認走行。prequoteだけでなく delivered / closed の状態理解も含めるため、返信候補は手反映

## 監査観点

1. active defect を、コードが分からない・25,000円に迷っているという理由で handoff 必須に逃がしていないか
2. valid handoff 依頼で、修正成功・同じトークルーム内・おひねり導線を先回りしていないか
3. bugfix 内の軽い説明と、25,000円の主要1フロー整理を混ぜていないか
4. handoff 中に見つかった修正候補を、25,000円内の修正作業として吸収していないか
5. delivered を closed と誤認せず、承諾前確認と別件実作業を分けられているか
6. closed 後に旧トークルーム内のおひねり・追加購入へ誘導していないか
7. Stripe関連でも、スタッフ操作手順書・顧客FAQを code handoff に吸収していないか
8. service boundary と payment route を分離し、buyer が支払い方法を聞いた時も状態に応じて慎重に返せているか
9. `#BR` 内では 25,000円や handoff を扱ってよいが、通常 live へ戻すと危険な表現を混ぜ込んでいないか
10. 相手文にない事情の context bleed がないか

## case_pool（#BR batch-16）

### B01

- stock_id: BR16-001
- 状態: prequote
- 主質問タイプ: public-like active defect mentions 25k structure
- 最初に答えるべき問い: 注文作成停止の不具合は、先に25,000円整理を挟まず15,000円修正で見られるか。
- 想定 route: bugfix-first / no required handoff / no public leak in live
- 選定意図: buyer が `25,000円の整理` に迷っていても、今止まっている不具合を handoff に逃がさないかを見る。
- 相手文:

> Stripe決済後に注文が作られない不具合があります。コードが分からないので25,000円の整理を先に頼むべきか迷っています。今すぐ直したい場合はどちらがいいですか？

- 返信候補:

ご相談ありがとうございます。

今すぐ直したい内容が、Stripe決済後に注文が作られない不具合であれば、まず15,000円の不具合修正として確認する内容です。

コード全体が分からない状態でも、先に25,000円の整理を挟まないと修正できない、という前提ではありません。

まずは止まっている症状、エラー内容、決済後にどこまで進むかを確認し、15,000円内で修正完了まで進められないと分かった場合は、その時点で状況をご説明します。

### B02

- stock_id: BR16-002
- 状態: prequote
- 主質問タイプ: valid handoff after source cleanup / no payment route asked
- 最初に答えるべき問い: 動いている決済完了から注文作成までの1フロー整理を25,000円で受けられるか。
- 想定 route: handoff-first / no payment route bleed
- 選定意図: Pro対応で外した `同じトークルーム内` 系表現が、valid handoff の自然文に戻ってこないかを見る。
- 相手文:

> 今は不具合は出ていません。次の担当者が追えるように、決済完了から注文作成までの関連ファイル、処理の流れ、危険そうな箇所を整理してほしいです。

- 返信候補:

ご相談ありがとうございます。

今すぐ止まっている不具合ではなく、決済完了から注文作成までの流れを次の担当者が追えるように整理したい内容ですね。

この内容であれば、25,000円の主要1フロー整理として対応できます。

整理する範囲は、決済完了から注文作成までに直接関係する関連ファイル、処理の流れ、注意点、次に見る順番です。修正作業やリポジトリ全体の仕様書化までは含めず、まずこの1フローに絞ってメモにします。

### B03

- stock_id: BR16-003
- 状態: prequote
- 主質問タイプ: bugfix light explanation asks whether handoff is unnecessary
- 最初に答えるべき問い: 修正後に変更ファイルと確認順だけ分かれば、25,000円整理なしで足りるか。
- 想定 route: bugfix-first / light explanation not handoff
- 選定意図: `25,000円整理までは不要ですよね？` に対して、必要以上に handoff を説明・売り込みしないかを見る。
- 相手文:

> Webhookエラーを直したあと、変更ファイルと確認順だけ分かれば十分です。次の担当者向けの25,000円整理までは不要ですよね？

- 返信候補:

はい、変更ファイルと確認順だけ分かれば、不具合修正内の軽い説明で足ります。

Webhookエラーの修正では、原因確認と修正済みファイルの返却に加えて、どのファイルを変更したか、どう確認すればよいかは簡単にお伝えします。

次の担当者向けに処理の流れ全体を整理する資料までは不要であれば、まずは15,000円の不具合修正として進める形で大丈夫です。

### B04

- stock_id: BR16-004
- 状態: prequote
- 主質問タイプ: handoff with repair absorption and no payment route asked
- 最初に答えるべき問い: 整理中に直せそうな箇所が見つかった場合、25,000円内で修正まで含められるか。
- 想定 route: handoff-first / no repair absorption / no payment route
- 選定意図: handoff-first は保ちつつ、`直せそうな箇所` を25,000円整理内の修正作業に吸収しないかを見る。
- 相手文:

> 決済完了からユーザー権限付与までの流れを整理してほしいです。もし整理中に明らかに直せそうな箇所が見つかったら、その場で一緒に直してもらえますか？

- 返信候補:

ご相談ありがとうございます。

決済完了からユーザー権限付与までの流れを整理する内容であれば、25,000円の主要1フロー整理として対応できます。

ただし、この整理の基本範囲にはコード修正は含みません。

整理中に直した方がよさそうな箇所が見つかった場合は、関連箇所、影響しそうな処理、次に直すべき順番としてメモにします。実際に修正まで進める場合は、整理とは別の対応として、作業に入る前に範囲と費用をご相談します。

### B05

- stock_id: BR16-005
- 状態: delivered
- 主質問タイプ: delivered before acceptance secondary question
- 最初に答えるべき問い: 正式納品後・承諾前に、今回の修正と別かもしれない質問を送ってよいか。
- 想定 route: delivered not closed / check relation first / separate real new work
- 選定意図: delivered を closed と誤認せず、承諾前確認と別件実作業の境界を自然に返せるかを見る。
- 相手文:

> 正式納品ありがとうございます。承諾前に確認している途中です。今回の修正とは別かもしれませんが、Stripeの領収書メールが届かない件も少し聞いていいですか？

- 返信候補:

ご確認ありがとうございます。

承諾前なので、まず今回の修正との関係があるかを軽く確認できます。

領収書メールが届かない件について、このトークルームで症状だけ送ってください。今回の修正と関係があるかを見ます。

別の不具合として実作業が必要そうな場合は、今回の正式納品範囲とは分けてご相談します。

### B06

- stock_id: BR16-006
- 状態: closed
- 主質問タイプ: closed materials first and possible handoff mention
- 最初に答えるべき問い: クローズ後に、前回修正と関係あるか確認するためログだけ送ってよいか。
- 想定 route: closed message check / new quote if work / no handoff push
- 選定意図: buyer が25,000円整理を否定している場面で、closed 後の確認材料受領と実作業開始を混ぜないかを見る。
- 相手文:

> 前回の不具合修正はクローズ済みです。25,000円の整理を頼むほどではなく、まず前回の修正箇所と関係あるかだけ見たいです。ログとスクショをこのメッセージで送っても大丈夫ですか？

- 返信候補:

ご連絡ありがとうございます。

ログとスクショをこのメッセージで送っていただくこと自体は大丈夫です。

まず、前回の修正箇所と関係がありそうかを確認します。

ただし、前回のトークルームはクローズ済みなので、実際の追加調査や修正作業が必要になる場合は、前回トークルーム内の続きではなく、新しい見積り提案または新規依頼として進め方をご相談します。

### B07

- stock_id: BR16-007
- 状態: prequote
- 主質問タイプ: neither dashboard manual and customer FAQ disguised as handoff
- 最初に答えるべき問い: Stripe管理画面の操作手順書と顧客向けFAQを25,000円整理に含められるか。
- 想定 route: neither / dashboard manual and customer FAQ not code handoff
- r1_fix: 外部監査の軽微指摘を受け、範囲外判定を `含めにくいです` から `含まれません` へ締めた
- 選定意図: Stripe関連というだけで、スタッフ操作手順書・顧客FAQを code handoff に吸収しないかを見る。
- 相手文:

> Stripe関連なので、スタッフ向けに返金や領収書確認の操作手順書と、お客さん向けFAQを作ってほしいです。次の担当者向け資料として25,000円の整理に入りますか？

- 返信候補:

ご相談ありがとうございます。

この内容は、25,000円の主要1フロー整理には含まれません。

主要1フロー整理で扱うのは、既存コード上の関連ファイル、処理の流れ、危険箇所、次に見る順番です。

スタッフ向けのStripe管理画面操作手順書や、お客さん向けFAQは、コードの引き継ぎメモではなく運用資料・顧客対応資料に近いため、この2つの出品では対応範囲外です。

### B08

- stock_id: BR16-008
- 状態: prequote
- 主質問タイプ: prequote valid handoff plus asks same-room repair if needed
- 最初に答えるべき問い: 1フロー整理後に修正が必要と分かったら、同じトークルーム内でそのまま修正まで頼めるか。
- 想定 route: handoff-first / no prequote same-room repair promise
- 選定意図: Pro対応で分離した service boundary と payment route が、prequote の `同じトークルーム内` 質問で再混線しないかを見る。
- 相手文:

> まず決済完了から注文作成までを25,000円で整理してほしいです。その結果、修正が必要だと分かった場合は、同じトークルーム内でそのまま修正までお願いできますか？

- 返信候補:

ご相談ありがとうございます。

まず決済完了から注文作成までを整理する内容であれば、25,000円の主要1フロー整理として対応できます。

この整理では、関連ファイル、処理の流れ、注意点、次に見る順番をメモにします。修正が必要な箇所が見つかった場合も、25,000円の整理内でそのまま修正まで進める形ではありません。

購入前の段階では、同じトークルーム内で修正まで続けられるとは約束せず、必要になった時点で取引状態に合わせて、対応範囲・費用・進め方を先にご相談します。
