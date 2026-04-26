# 2026-04-26 返信システム引き継ぎサマリ

## 結論

現行の返信システム骨格は維持する。
今日の主な進化は、文章の違和感を単なる日本語問題ではなく、`phase / platform / transaction model` の欠落として扱えるようになったこと。

次の Codex は、広い再設計ではなく、引き続き `#RE -> 外部監査 -> 再発だけ rule / renderer / validator / gold へ戻す` を守る。

## 今日増えた重要レンズ

- `phase_answer_gap`
  - 文面は安全でも、今の phase で buyer が次に取れる行動が見えない時に拾う reviewer ラベル。
- `unnamed_discomfort`
  - まだ名前がない違和感を、最大1〜2件だけ拾う discovery ラベル。
  - 好み差では使わない。実務リスクを説明できる時だけ。
- `transaction_model_gap`
  - 日本語は自然でも、支払い状態、作業開始条件、見積り提案、購入、成果物返却の順序が曖昧でツギハギに見える時に拾う reviewer ラベル。
  - writer rule ではなく reviewer レンズ。validator に入れるのは deterministic に検出できる事故だけ。

## 今日の主な採用結果

### closed 後の確認材料と実作業境界

- closed 後でも、ログ・スクショ・最小限の関係ファイルは確認材料として見られる。
- ただし、コード修正、差し替えファイル作成、成果物返却、具体的な修正指示は実作業寄り。
- 実作業が必要な場合は、作業に入る前に、ココナラ上でどう進めるかと費用が発生するかを先に相談する。
- 0円実作業や無料修正を先に約束しない。
- 通常料金の新規依頼として、確認前に進めるようにも見せない。

### closed 後の怒り気味・無料対応要求

採用した方向:

```text
前回の修正後から同じようなエラーが残っていて、また費用がかかるのは納得できないとのこと、確認しました。

その場合は、まず前回の修正とつながる症状かを確認するのが先です。
確認しないまま、通常料金の新規依頼として進めることはしません。

恐れ入りますが、トークルームは閉じているため、この場でそのまま修正作業に入ることはできません。
まずはエラー内容やログ、スクショを見て、前回の修正とつながる内容か、別の原因として追加の作業が必要な内容かを確認します。

コード修正などの作業が必要になりそうな場合は、作業に入る前に、ココナラ上でどう進めるかと費用が発生するかを先にご相談します。
```

避ける表現:

- `放置するつもりはありません`
- `前回の修正で解決しているべき`
- `無料で対応します`
- `前回対応として確認できる内容`
- `確認前にまた15,000円`

## batch-11 の状態

`RE-2026-04-26-bugfix-11-transaction-model-gap-r2` は完了扱い。

更新先:

- `/home/hr-hm/Project/work/サービスページ/rehearsal/bugfix-15000-返信学習/返信監査_batch-01.md`
- `/home/hr-hm/Project/work/ops/tests/quality-cases/active/transaction-model-gap-bugfix11.yaml`

結果:

- r0 は Codex / Claude とも要修正。
- r1 は採用可、B06 の見積り重複だけ軽微。
- r2 で B06 を圧縮。
- 再監査は不要判断。

## 新規 gold / learning-log

- `docs/reply-quality/gold-replies/24_transaction-model-gap_edges.ja.md`
  - purchased 追加症状と追加料金不安
  - closed 購入なしコード修正助言
  - closed 次回相談導線
- `ops/tests/stock/learning-log/2026-04-26-transaction-model-gap-bugfix11.yaml`

既存の関連 gold:

- `docs/reply-quality/gold-replies/22_phase-contract-edge_next-path.ja.md`
- `docs/reply-quality/gold-replies/23_closed-materials-work-boundary.ja.md`

## validator / renderer 反映

今日追加・更新した主な guard:

- `scripts/render-closed-followup.py`
  - closed 後の確認材料 / 実作業境界の最小分岐
  - 怒り気味無料対応要求の文面改善
  - 時刻を15分単位に丸める
- `scripts/check-rendered-closed-followup.py`
  - generic closed fallback
  - 外部共有
  - 秘密情報
  - ZIP修正返却
  - 見積り前原因調査
  - 無料/追加料金不安
- `scripts/check-rendered-quote-sent-followup.py`
  - quote_sent で入金前にコード/ログ/原因確認へ進ませる事故を検出
- `scripts/check-rendered-post-purchase-quick.py`
  - purchased で追加症状の別料金不安に答えない事故を検出

## 監査プロンプト

更新済み:

- `サービスページ/rehearsal/bugfix-15000-返信学習/監査プロンプト_codex-xhigh.md`
- `サービスページ/rehearsal/bugfix-15000-返信学習/監査プロンプト_claude.md`

追加済みの観点:

- `phase_answer_gap`
- `unnamed_discomfort`
- `transaction_model_gap`

## 検証済み

直近確認:

- `python3 scripts/check-coconala-reply-role-suites.py --save-report` OK
- `./scripts/os-check.sh` OK
- `TMG-001` / `TMG-002` は新 validator guard で NG 検出されることを確認済み

既知の軽微警告:

- `CMP-002` の projection warning
  - `まず進み具合を整理してお返しします`
  - 今回の変更による新規失敗ではない。

## 次にやるなら

1. まずこのサマリと `docs/next-codex-prompt.txt` を読む。
2. `./scripts/os-check.sh` を実行する。
3. 続けるなら次の `#RE` を回す。
4. 次 batch は、実 stock か不足領域を選ぶ。
5. `handoff-25000` はまだ外向け live ではない。dual-public 系 stock を使う場合は、外向け導線を出さない leakage test として扱う。

## 絶対に避けること

- 骨格の広い再設計
- reviewer レンズを writer rule として常駐させること
- handoff-25000 の外向けサービス名・価格・購入導線の露出
- closed 後の無料実作業約束
- closed 後の確認材料受領と実作業の混同
- quote_sent で入金前に作業開始すること
