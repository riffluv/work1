# bugfix-15000 v1 Scope Seal

updated: 2026-05-01

## 位置づけ

`bugfix-15000` の返信OSは、現時点で `v1 completion candidate` として扱う。

これは「完成品として全領域に展開できる」という意味ではなく、ココナラ通常 live の `bugfix-15000` 返信について、主要な取引境界と日本語品質が実用圏に入ったという意味です。

## v1 candidate の範囲

- ココナラ通常 live 返信
- 外向け公開サービスは `bugfix-15000` のみ
- phase は `prequote / quote_sent / purchased / delivered / closed`
- 価格は 15,000円
- 作業単位は不具合1件
- 作業開始は購入 / 支払い完了後
- 成果物は、修正できる箇所が特定できた場合の修正済みファイル返却
- secret 値、外部連絡、外部決済、直接 push、本番反映は扱わない

## まだ seal しない範囲

- `handoff-25000` の通常 live 公開
- 複数サービス同時公開時の buyer 向け案内
- メール返信 channel
- アプリ UI 上の memory / phase 入力運用
- 完全自動送信
- 実案件 stock による未知ケースの飽和確認

## routine #RE を止める family

次の family は、合成 #RE では高飽和として routine 追加を止める。

- `purchased_current_status`
- `quote_sent_payment_after_share`
- `delivered_light_supplement`
- `closed_relation_check`

ただし `real_stock` はまだ低飽和です。

## resume triggers

次のどれかが起きたら、targeted #RE / Pro review / checker 更新の対象に戻す。

- 実案件 stock で未知の崩れが出た
- #R 実出力と #RE writer_candidate がズレた
- service registry / service-pack / phase contract / writer brief を変更した
- hidden service や 25,000円など public:false 情報が漏れた
- Pro / human audit が新しい failure family を指摘した
- contract packet checker が fail した

## service truth

外向け返信の公開事実正本:

- `/home/hr-hm/Project/work/ops/services/next-stripe-bugfix/service-pack/facts.yaml`
- `os/core/service-registry.yaml` の `public_facts_file`

実行時能力・既存互換:

- `/home/hr-hm/Project/work/ops/services/next-stripe-bugfix/service.yaml`
- `os/core/service-registry.yaml` の `runtime_capability_file`

`facts_file` は既存互換として残すが、外向け公開事実の正本としては使わない。

確認コマンド:

```bash
./scripts/check-service-truth-resolver.py
```

この checker は、`public_facts_file` が `service-pack/facts.yaml` に解決されること、`runtime_capability_file` が既存互換の `facts_file` と一致すること、価格・addon・scope・source refs が公開事実正本と runtime 能力参照でズレていないことを確認する。

## contract packet gate

`ops/tests/contract-packets/bugfix-15000-v1-samples.yaml` は、返信文テンプレートではなく、Writer が自然文を書く前の事実制約です。

最低限、次を満たすこと。

- memory / phase / reply_contract が一致している
- explicit questions が answer_map / ask_map で全て扱われている
- answer_after_check には hold_reason / revisit_trigger がある
- ask_map は blocking_missing_facts と対応している
- required_moves / forbidden_moves は output schema の enum に収まる
- hidden service や private price が外向け判断文へ混ざらない

確認コマンド:

```bash
./scripts/check-service-truth-resolver.py
./scripts/check-contract-packets.py
./scripts/check-contract-packet-fixtures.py
./scripts/build-contract-packets.py --check-against-samples --save-report
./scripts/check-contract-packet-writer-brief-sync.py
```

`check-contract-packet-fixtures.py` は、sample packet が実際の入力相当の phase / buyer message / explicit question と一致しているかを見る traceability smoke です。runtime packet builder そのものではありません。

`build-contract-packets.py --check-against-samples --save-report` は、fixture と schema / registry から最小 generated packet を作り、sample packet の重要項目と比較します。`--save-report` 付きでは `runtime/regression/coconala-reply/contract-packets/latest.generated.yaml` に生成 packet を保存し、runtime protocol に近い形で後から確認できます。現時点では family ごとの最小 `answer_brief`、closed 関係確認のような明確な追加材料の `ask_map`、`issue_plan`、`required_moves`、`forbidden_moves`、`response_order` まで生成します。writer 自然文判断や文体判断はまだ生成しません。

`check-contract-packet-writer-brief-sync.py` は、generated packet と #R の writer brief が同じ phase / scenario / answer coverage に接続されているかを見る同期 smoke です。返信本文の自然さを見る監査ではありません。

`check-coconala-reply-role-suites.py --save-report` は、通常の seed / edge / eval / holdout / renderer_seed に加えて、この同期 smoke も実行します。contract / #R 接続を変えた後は、個別 smoke だけでなく role suite 側でも確認してください。

## do not

- 同型の採用確認だけを有料 xhigh で回し続けない
- soft lens を hard rule 化しすぎない
- Gold をテンプレートとして丸写ししない
- naturalizer に service facts を決めさせない
- Writer に reviewer prompt 全文を背負わせない
- `handoff-25000` / 25,000円 / 主要1フロー整理を通常 live / #RE に戻さない
