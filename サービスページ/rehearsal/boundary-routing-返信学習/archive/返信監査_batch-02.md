# 返信監査 batch 02（#BR / boundary-routing shadow）

## batch_manifest

- batch_id: BR-2026-04-28-boundary-routing-shadow-02
- shortcut: `#BR`
- 目的: `bugfix-15000` と `handoff-25000` の境界ルーティングを、future-dual simulation として検査する
- 状態: r0 current
- 件数: 7件
- 対象: prequote
- 公開状態: `bugfix-15000` は live、`handoff-25000` は training-visible / future-dual simulation
- 注意: 通常 live 返信では `handoff-25000` のサービス名・25,000円・購入導線を出さない
- 正本メモ: `/home/hr-hm/Project/work/docs/reply-quality/boundary-routing-shadow-rehearsal.ja.md`
- fixture: `/home/hr-hm/Project/work/ops/tests/quality-cases/active/boundary-routing-shadow-br02.yaml`
- 生成: `python3 scripts/render-prequote-estimate-initial.py --fixture ops/tests/quality-cases/active/boundary-routing-shadow-br02.yaml`

## 監査観点

1. buyer の主目的が「修正」か「把握/整理」かを先に見ているか
2. buyer に `bugfix / handoff のどちらを選ぶか` を丸投げしていないか
3. `15,000円の不具合1件修正` と `25,000円の主要1フロー整理` を混ぜていないか
4. 修正が主目的なのに、コードが分からないだけで handoff へ逃がしていないか
5. 整理が主目的なのに、無理に bugfix の購入へ寄せていないか
6. handoff で修正完了を約束していないか
7. 新機能追加を bugfix / handoff のどちらかへ吸収していないか
8. live 返信へ private service の名称・価格・購入導線が漏れていないか
9. buyer の次アクションが迷子になっていないか

## case_pool（#BR batch-02）

### B01

- stock_id: BR2-001
- 状態: prequote
- 主質問タイプ: bugfix-first / active defect with handoff anxiety
- 最初に答えるべき問い: 今は整理ではなく、checkout.session.completed 後の注文作成不具合を先に直すべきか。
- 想定 route: bugfix-first
- r0_renderer_mode: `pass` / scenario `default_bugfix`
- 相手文:

> Stripeのcheckout.session.completedは届いているのに、注文テーブルにinsertされません。前任者のコードが読みにくくて、次の人に渡す資料も欲しいのですが、まずは注文が作られない不具合を直す方をお願いできますか？

- 返信候補:

ご相談ありがとうございます。
まず状況を確認します。

この不具合なら15,000円で進められます。

まずはこの不具合がどこで止まっているかを確認します。

この内容で進める場合は、そのままご購入いただいて大丈夫です。必要情報がそろい次第、一次結果は48時間以内を目安にお返しします。

### B02

- stock_id: BR2-002
- 状態: prequote
- 主質問タイプ: handoff-first / no active defect, wants risk map
- 最初に答えるべき問い: 壊れていない現状で、次の担当者向けに危険箇所と関連ファイルを整理できるか。
- 想定 route: handoff-first
- r0_renderer_mode: `pass` / scenario `default_bugfix`
- 相手文:

> 今のところ決済は動いています。ただ、Stripeまわりを触るのが怖くて、次の担当者に渡す前にどのファイルが危ないかだけ整理しておきたいです。修正ではなく、危険箇所と関連ファイルのメモを作ってもらえますか？

- 返信候補:

ご相談ありがとうございます。
まず状況を確認します。

この不具合なら15,000円で進められます。

まずはこの不具合がどこで止まっているかを確認します。

この内容で進める場合は、そのままご購入いただいて大丈夫です。必要情報がそろい次第、一次結果は48時間以内を目安にお返しします。

### B03

- stock_id: BR2-003
- 状態: prequote
- 主質問タイプ: mixed / fix now, handoff later
- 最初に答えるべき問い: 今回の相談では、まず二重メール送信の不具合を直し、整理は後で分けるべきか。
- 想定 route: bugfix-first
- r0_renderer_mode: `fix_vs_structure_first`
- 相手文:

> Stripeのサブスク解約後メールが2通送られる不具合があります。これを直してもらったあと、同じ周辺の処理を次の担当者向けに整理してもらうこともできますか？まずはメール二重送信を止めたいです。

- 返信候補:

ご相談ありがとうございます。
この場合は、まず全体整理よりいま出ている不具合から先に対応するのがよさそうです。

コード全体を先に整理し直す前提ではなく、修正に必要な範囲を確認します。

15,000円内で直し切れないと分かった場合は、追加作業へ進まず、そこでご説明します。

この内容で進める場合は、ご購入後に発生時のログや関係ファイルを送ってください。

### B04

- stock_id: BR2-004
- 状態: prequote
- 主質問タイプ: handoff-first / wants non-engineer readable map
- 最初に答えるべき問い: 非エンジニアでも追えるように、主要1フローの整理として対応できるか。
- 想定 route: handoff-first
- r0_renderer_mode: `pass` / scenario `default_bugfix`
- 相手文:

> Stripeの決済からユーザー権限が付くまでの流れを、非エンジニアの私でも次の人に説明できるように整理したいです。今壊れているわけではありません。こういう整理だけお願いできますか？

- 返信候補:

ご相談ありがとうございます。

この不具合なら15,000円で進められます。

まずはこの不具合がどこで止まっているかを確認します。

この内容で進める場合は、そのままご購入いただいて大丈夫です。必要情報がそろい次第、一次結果は48時間以内を目安にお返しします。

### B05

- stock_id: BR2-005
- 状態: prequote
- 主質問タイプ: price separation / bugfix plus small map
- 最初に答えるべき問い: 不具合修正に、関連ファイル一覧や変更箇所説明をどこまで含められるか。
- 想定 route: bugfix-first + scope boundary
- r0_renderer_mode: `code_handoff_bugfix_scope`
- 相手文:

> Stripe Checkout後に会員プランが更新されない不具合を15,000円で直してほしいです。納品時に、どのファイルを見たかと変更した場所だけ軽く教えてもらうことはできますか？引き継ぎメモほどの整理は不要です。

- 返信候補:

ご相談ありがとうございます。

外注先と連絡が取れず、決済まわりの不具合が残っていて、コードの中身も追いにくい状態ですね。

決済まわりの不具合修正として見る場合は、15,000円で対応できます。
コード全体の引き継ぎ整理を前提ではなく、修正に必要な範囲をこちらで確認します。

まずは決済で起きている症状と、関連しそうなファイルを送ってください。必要情報がそろい次第、一次結果は48時間以内を目安にお返しします。

### B06

- stock_id: BR2-006
- 状態: prequote
- 主質問タイプ: handoff scope / one main flow vs whole repository
- 最初に答えるべき問い: 25,000円の整理でリポジトリ全体とStripe全処理を網羅できるか。
- 想定 route: handoff-first + scope boundary
- r0_renderer_mode: `pass` / scenario `default_bugfix`
- 相手文:

> 次の担当者に渡すために、Stripe関連の全処理とリポジトリ全体の構造をまとめてほしいです。25,000円の整理で全部見てもらえるのでしょうか？

- 返信候補:

ご相談ありがとうございます。

今の症状なら、まずこの不具合対応から入るのが近いです。

まずはこの不具合がどこで止まっているかを確認します。

この内容で進める場合は、そのままご購入いただいて大丈夫です。必要情報がそろい次第、一次結果は48時間以内を目安にお返しします。

### B07

- stock_id: BR2-007
- 状態: prequote
- 主質問タイプ: neither / new feature plus handoff request
- 最初に答えるべき問い: 新しい管理画面機能追加は bugfix / handoff のどちらにも吸収しないべきか。
- 想定 route: neither / scope out
- r0_renderer_mode: `public_structure_scope_boundary`
- 相手文:

> Stripe決済は問題なく動いています。管理画面に返金ボタンを新しく追加して、その流れもメモにしてほしいです。15,000円の修正か25,000円の整理のどちらで頼めますか？

- 返信候補:

ご相談ありがとうございます。
まずは、実際に止まっている不具合を起点にするのが安全です。

コード全体を整理し直す前提ではなく、不具合修正に必要な範囲を確認します。

15,000円内で修正完了まで進められない、または全体整理が必要だと分かった場合は、そこで止めてご説明します。
勝手に料金が増えたり、そのまま追加作業へ進むことはありません。

この内容で進める場合は、ご購入後にエラー内容やログを送ってください。
