# 返信監査 batch 15（#BR / boundary-routing shadow）

## batch_manifest

- batch_id: BR-2026-04-29-boundary-routing-shadow-15
- shortcut: `#BR`
- 目的: `bugfix-15000` と `handoff-25000` の近縁境界で、service boundary と payment route を混ぜないか検査する
- 状態: r2 light revised
- 件数: 8件
- 対象: prequote / purchased / delivered / closed payment-route edge
- 公開状態: `bugfix-15000` は live、`handoff-25000` は training-visible / future-dual simulation
- 注意: 通常 live 返信では `handoff-25000` のサービス名・25,000円・購入導線を出さない
- 正本メモ: `/home/hr-hm/Project/work/docs/reply-quality/boundary-routing-shadow-rehearsal.ja.md`
- fixture: `/home/hr-hm/Project/work/ops/tests/quality-cases/active/boundary-routing-shadow-br15.yaml`
- 生成: `python3 scripts/render-prequote-estimate-initial.py --fixture ops/tests/quality-cases/active/boundary-routing-shadow-br15.yaml`
- 補足: renderer は prequote のみ出力。B05〜B08 は payment-route state edge として手反映

## 監査観点

1. service boundary と payment route を混ぜていないか
2. buyer が支払い方法を聞いていない時に、同じトークルーム内 / おひねり / 有料オプションを前面に出していないか
3. prequote で、まだ存在しないトークルーム内追加支払いを約束していないか
4. purchased / delivered で、buyer が追加支払い方法を明示した時だけ状態に応じて返せているか
5. closed で、旧トークルーム内のおひねりや追加購入へ誘導していないか
6. 15,000円修正と25,000円整理を、一括料金・セット割・同日保証へ寄せていないか
7. handoff 中の修正を吸収せず、修正は別対応として分けられているか
8. active defect を cheap trial や handoff 必須へ崩していないか
9. 相手文にない事情の context bleed がないか
10. 通常 live へ戻すと public:false 漏れになる表現を、#BR 専用として扱えているか

## case_pool（#BR batch-15）

### B01

- stock_id: BR15-001
- 状態: prequote
- 主質問タイプ: prequote / bugfix first plus later handoff payment-route pressure
- 最初に答えるべき問い: 決済後注文が作られない不具合を直した後、整理メモも同じ流れでおひねり追加できるか。
- 想定 route: bugfix-first / later handoff separate / no prequote ohineri promise
- r0_renderer_mode: default_bugfix
- r1_fix: active defect を bugfix-first にしつつ、購入前に同じトークルーム内・おひねり前提を約束しない
- 選定意図: buyer が支払い導線を先に聞いた時、サービス境界を崩さず、prequote でまだ存在しないトークルーム内導線を約束しないかを見る。
- 相手文:

> 決済後に注文が作られない不具合を直してほしいです。修正後に次の担当者向けの整理メモも必要になったら、そのまま同じトークルーム内でおひねり追加してお願いできますか？

- 返信候補:

ご相談ありがとうございます。

決済後に注文が作られない不具合は、まず15,000円の不具合修正として対応する内容です。

修正後に次の担当者向けの整理メモが必要になった場合は、不具合修正とは別の成果物として扱います。

購入前の段階では、同じトークルーム内でのおひねり追加を前提にして進めるとは約束せず、必要になった時点で取引状態に合わせて進め方と費用を先にご相談します。

### B02

- stock_id: BR15-002
- 状態: prequote
- 主質問タイプ: prequote / handoff first plus possible repair but no payment method asked
- 最初に答えるべき問い: 壊れていない決済フロー整理中に修正候補が見つかったら、どう扱うか。
- 想定 route: handoff-first / no repair absorption / no payment route
- r0_renderer_mode: default_bugfix
- r1_fix: handoff-first に戻し、修正候補はメモまで。支払い方法は聞かれていないため出さない
- 選定意図: `怪しい箇所` に反応して bugfix へ吸収したり、支払い導線を先回りしないかを見る。
- 相手文:

> 今は大きな不具合はありません。決済完了から注文作成までの流れを整理して、もし怪しい箇所があれば次にどう直すかも知りたいです。

- 返信候補:

ご相談ありがとうございます。

今すぐ止まっている不具合ではなく、決済完了から注文作成までの流れを整理したい内容ですね。

この内容であれば、25,000円の主要1フロー整理として対応できます。

整理では、関連ファイル、処理の流れ、危険箇所、次に見る順番をメモにします。怪しい箇所が見つかった場合も、その場で修正作業まで含めるのではなく、次に直すべき候補として整理します。

### B03

- stock_id: BR15-003
- 状態: prequote
- 主質問タイプ: prequote / cheap-first pressure and future handoff
- 最初に答えるべき問い: まず安い方で試し、必要なら整理メモへ進む流れにできるか。
- 想定 route: bugfix-first if active defect / no cheap trial / no payment route
- r0_renderer_mode: default_bugfix
- r1_fix: active defect は bugfix-first。ただし15,000円を安い試し枠や25,000円整理への自動逃げ先にしない
- 選定意図: `安い方で試す` に引っ張られて、bugfix を diagnosis-only / cheap trial に崩さないかを見る。
- 相手文:

> 注文が作られない不具合があります。まず安い15,000円の方で試して、ダメなら25,000円の整理に回す感じでできますか？

- 返信候補:

ご相談ありがとうございます。

注文が作られない不具合が出ているなら、まず15,000円の不具合修正として確認する内容です。

ただし、15,000円は「安く試すだけ」の診断枠ではなく、原因確認から修正済みファイルの返却まで進める前提の料金です。

15,000円の範囲で修正完了まで進められない、または整理の方が必要だと分かった場合は、その時点で止めて状況をご説明します。25,000円の整理へ自動で切り替える形ではありません。

### B04

- stock_id: BR15-004
- 状態: prequote
- 主質問タイプ: prequote / explicit bundle and one-room pressure
- 最初に答えるべき問い: 修正と整理を同じトークルームで一気に進め、合計を安くできるか。
- 想定 route: split bugfix and handoff / no bundle / no one-room promise
- r0_renderer_mode: code_handoff_bugfix_scope
- r1_fix: active defect を bugfix-first とし、同じトークルームや一括化を理由に成果物・価格を混ぜない
- 選定意図: `同じトークルームで一気に` に引っ張られて、支払い導線をサービス境界の根拠にしないかを見る。
- 相手文:

> 決済後に注文が作られない不具合修正と、次の外注先向けの整理メモを同じトークルームで一気にお願いしたいです。まとめるので合計を少し安くできますか？

- 返信候補:

ご相談ありがとうございます。

決済後に注文が作られない不具合は、まず15,000円の不具合修正として対応する内容です。

次の外注先向けの整理メモは、修正とは別の成果物になります。トークルームを同じにできるかどうかとは別に、15,000円修正と25,000円整理を一括料金やセット割としてまとめる形ではありません。

まずは止まっている不具合の修正を優先し、整理メモが必要な場合は別対応として進め方と費用を先にご相談します。

### B05

- stock_id: BR15-005
- 状態: purchased
- 主質問タイプ: purchased bugfix / later handoff payment-route explicitly asked
- 最初に答えるべき問い: 購入中の不具合修正後に、同じトークルーム内の追加支払いで整理メモも頼めるか。
- 想定 route: bugfix current scope then possible separate handoff / state-allowed payment route
- r0_renderer_mode: skipped_non_prequote
- r1_fix: 現在の bugfix を先に完了。handoff は別成果物。buyer が支払い方法を聞いているため、取引中の追加支払い導線を条件付きで出す
- 選定意図: 支払い導線を完全に消すのではなく、state と buyer質問が合う時だけ出せるかを見る。
- 相手文:

> 修正ありがとうございます。もしこの不具合が直ったあとに、次の担当者向けの整理メモもお願いしたくなった場合、このトークルーム内で追加支払いして続けられますか？

- 返信候補:

ご確認ありがとうございます。

まずは、今進めている不具合修正を現在の範囲として完了させます。

その後に次の担当者向けの整理メモが必要になった場合は、不具合修正とは別の成果物として扱います。

このトークルームが開いている間であれば、内容と金額を先に確認したうえで、ココナラ上の追加支払いとして続けられる場合があります。自動で追加になるわけではないので、必要になった時点で対象フローと費用を先にご相談します。

### B06

- stock_id: BR15-006
- 状態: purchased
- 主質問タイプ: purchased handoff / repair emergency and additional fee question
- 最初に答えるべき問い: 整理中に決済が止まったため、先に修正へ切り替えられるか。追加料金はかかるか。
- 想定 route: handoff pause or split / repair as additional / no repair absorption
- r0_renderer_mode: skipped_non_prequote
- r1_fix: handoff 中の active defect を修正として別threadに分け、追加料金自動発生なしを明示する
- 選定意図: handoff中に緊急修正が発生した時、整理の範囲へ修正を吸収しないか、逆に買い直し感を強く出しすぎないかを見る。
- 相手文:

> 引き継ぎメモの整理をお願いしている途中ですが、今朝から決済が止まってしまいました。整理はいったん止めて、先に修正へ切り替えられますか？追加料金はかかりますか？

- 返信候補:

状況ありがとうございます。

決済が止まっているなら、整理メモとは分けて不具合修正として扱う内容です。

整理をいったん止めて、先に修正が必要かを確認することはできます。ただし、修正作業そのものは25,000円の整理には含まれません。

追加料金が自動で発生することはありません。まず、今出ている症状、エラーやログ、いつから止まったかを確認し、修正として進める必要がある場合は、作業に入る前に進め方と費用をお伝えします。

### B07

- stock_id: BR15-007
- 状態: delivered
- 主質問タイプ: delivered before close / additional handoff after bugfix
- 最初に答えるべき問い: 正式納品後・クローズ前に、追加の整理メモをおひねりで頼めるか。
- 想定 route: delivered not closed / payment possible but not default / separate handoff
- r0_renderer_mode: skipped_non_prequote
- r1_fix: delivered と closed を混同せず、追加相談は可能だが今回納品とは別成果物として分ける
- r2_fix: `おひねり等の追加支払いで進める形になります` を `進められる場合があります` へ弱め、支払い導線の断定を避ける
- 選定意図: 正式納品後の支払い導線を、closed 後不可と混同せず、かつ追加対応前提にしすぎないかを見る。
- 相手文:

> 正式納品ありがとうございます。承諾前に確認しているところです。追加で決済フローの整理メモもお願いしたい場合、おひねりでこのトークルーム内に追加できますか？

- 返信候補:

ご確認ありがとうございます。

クローズ前であれば、このトークルーム内で追加のご相談自体はできます。

ただし、決済フローの整理メモは今回の不具合修正とは別の成果物になります。追加で進める場合は、対象フローと金額を先に確認し、合意後におひねり等の追加支払いで進められる場合があります。

まずは今回の正式納品内容を確認いただき、整理メモも必要そうであれば、どの流れを整理したいかを1つ送ってください。

### B08

- stock_id: BR15-008
- 状態: closed
- 主質問タイプ: closed / ohineri request for follow-up handoff
- 最初に答えるべき問い: クローズ後に、前回トークルームのおひねりで整理メモを追加できるか。
- 想定 route: closed no old talkroom ohineri / new quote or request
- r0_renderer_mode: skipped_non_prequote
- r1_fix: closed 後は旧トークルーム内のおひねり・追加購入へ誘導しない
- 選定意図: `おひねり` と言われても、closed 後に旧トークルーム継続へ誤誘導しないかを見る。
- 相手文:

> 前回の不具合修正はクローズ済みです。追加で整理メモも欲しくなったのですが、前回のトークルームにおひねりで追加してお願いできますか？

- 返信候補:

ご連絡ありがとうございます。

前回のトークルームがクローズ済みの場合、そのトークルーム内でおひねりを追加して進めることはできません。

整理メモが必要な場合は、まずこのメッセージ上で、どの流れを整理したいかを確認します。

そのうえで実作業として進める場合は、前回トークルームの続きではなく、ココナラ上で新しい見積り提案または新規依頼としてご案内します。
