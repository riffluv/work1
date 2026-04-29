# skill / docs noise audit 2026-04-29

## 目的

古い返信補助ルールが、現在の `service boundary vs payment route` 分離や `handoff-25000 public:false` ルールを邪魔していないか確認する。

対象は、通常 live / #RE / #BR の生成に影響しやすい `skills`、返信品質 docs、汎用テンプレ、判断フロー、renderer の一部。過去の外部調査メモ、Pro 出力アーカイブ、service-pack fidelity fixture は記録資料として扱い、正本ノイズとは判定しない。

## 見つかった古いノイズ

### 1. 支払い導線の固定化

古い文面に、次のような固定が残っていた。

- 見積り中 / 取引中なら同じトークルーム内で追加料金対応へ続けられる
- 正式納品後、クローズ前ならおひねりで案内する
- 見積り経路では有料オプションを追加できないので別の追加支払いへ進める

現在の正本では、これは支払い導線の先回りになりやすい。修正後は、サービス境界と支払い導線を分け、buyer が支払い方法を聞いていて、取引状態が分かる場合だけ条件付きで案内する。

### 2. 未公開 handoff の live 漏れ候補

`coconala-reply-ja` 系の古い reference に、`25,000円`、`主要1フロー整理`、handoff 購入導線を通常外向けに使えそうな記述が残っていた。

修正後は、`#BR` または `service-registry.yaml` で `public: true` の時だけ使うと明記した。通常 live / #RE では、未公開サービスの価格・サービス名・購入導線は出さない。

### 3. 最終自然化 layer の越権

`japanese-chat-natural-ja` に、追加支払いの案内で状態語を補うルールがあり、自然化 layer が支払い導線を新しく決める余地があった。

修正後は、自然化では元の判断を変えず、支払い導線が未確定なら `進め方と費用を先にご相談します` 程度に留める。

### 4. quote_sent handoff の同一トークルーム表現

`render-quote-sent-followup.py` の handoff 分岐に、修正が必要な場合は同じトークルーム内で別対応できる、という旧表現が残っていた。

修正後は、修正は別対応として進め方と費用を先に相談する表現へ戻した。

## 修正したファイル

- `.codex/skills/coconala-listing-ja/references/fixed-facts.ja.md`
- `.codex/skills/coconala-reply-ja/SKILL.md`
- `.codex/skills/coconala-reply-ja/references/estimate-reply-flow.ja.md`
- `.codex/skills/coconala-reply-ja/references/message-patterns.ja.md`
- `.codex/skills/coconala-reply-ja/references/consistency-guard.ja.md`
- `.codex/skills/coconala-reply-ja/references/style-rules.ja.md`
- `.codex/skills/coconala-reply-bugfix-ja/SKILL.md`
- `.codex/skills/coconala-reply-bugfix-ja/references/style-rules.ja.md`
- `.codex/skills/coconala-reply-bugfix-ja/references/edge-cases.ja.md`
- `.codex/skills/japanese-chat-natural-ja/SKILL.md`
- `docs/reply-quality/ng-expressions.ja.md`
- `docs/coconala-message-templates-short.ja.md`
- `docs/coconala-reply-self-check.ja.md`
- `scripts/render-quote-sent-followup.py`

補足: `coconala-reply-judgment-flow`、`coconala-prequote-review-patterns`、旧 `service-plan` などの初期 docs は、現行正本から外したため削除済み。

## 触らなかったもの

- `chatgptPro/` 以下の過去分析
- `ops/tests/regression/service_pack_fidelity_handoff/` の fixture
- `docs/reply-quality/boundary-routing-shadow-rehearsal.ja.md` の BR 履歴

これらは履歴・検査 fixture であり、通常 live の生成正本ではない。古い語が残っていても、現在の runtime へ戻す材料として直接扱わない。

## 現状判断

古いノイズは残っていたが、通常 live / #RE に直接混ざりやすい箇所は修正済み。

特に、支払い導線を skill / naturalizer / docs が勝手に決める余地を削り、`#BR` の shadow 語彙と通常 live の公開語彙を再分離した。

今後 Pro に見るなら、論点は `BR 用 shadow asset と live 用 core skill を物理的にさらに分けるべきか`。ただし現時点では、runtime の public leak gate と今回の skill/doc 修正で急ぎの Pro 相談は不要。
