# 返信OS v1 完成棚卸し 2026-05-01

## 位置づけ

この棚卸しは、ココナラ返信OSを「さらに #RE を回すか」ではなく、「どこまで完成圏に入っていて、次に何を検証すべきか」で判断するための短期正本です。

参照元:

- `chatgptPro/返信SYSTEM設計図への道5-01.txt`
- `docs/reply-quality/core-completion-checklist.ja.md`
- `docs/reply-quality/rehearsal-operating-policy.ja.md`
- `ops/tests/fixture-coverage-map.yaml`

## 現在の結論

`bugfix-15000` の返信コアは、`v1 完成候補 / 機能コア完成圏` と見てよい。

ただし、これは「あらゆる業種・メール・複数サービスまで自動対応できる完成品」ではない。現時点で完成圏に入っているのは、次の範囲です。

- ココナラ通常 live の `bugfix-15000`
- 見積り前、見積り提案後、購入後、納品後、クローズ後の主要 phase
- Next.js / Stripe / API 不具合修正の相談返信
- 人間または Codex が最終送信判断をする前提の返信候補生成

## 安定しているもの

次の領域は、通常の同型 #RE を追加で回すより、変更時・実案件 stock 時だけ再確認する扱いでよい。

- `bugfix-15000` の 15,000円、不具合1件、購入後の原因確認、修正可能時の修正済みファイル返却
- `handoff-25000 public:false` の live / #RE 非漏洩
- `prequote / quote_sent / purchased / delivered / closed` の phase 境界
- 支払い前の原因確認・コード確認・ログ確認の防止
- `.env` / APIキー / Webhook secret / DB接続文字列などの秘密値を扱わない境界
- GitHub招待、外部共有、直接 push、本番反映へ流さない境界
- closed 後の関係確認と実作業の分離
- 成功保証、無料修正、返金、今日中修正完了の未断定
- `promise_consistency`、`agency_alignment`、`permission_benefit_alignment`、`positive_flow_before_refusal` などの主要 soft lens

## 高飽和として止める family

`ops/tests/fixture-coverage-map.yaml` 上で、次の family は `saturation: high` と扱う。

- `purchased_current_status`
- `quote_sent_payment_after_share`
- `delivered_light_supplement`
- `closed_relation_check`

これらは、次のどれかが出るまで routine #RE を止める。

- 実案件 stock で未知の崩れが出る
- #R 実出力で再現する違和感が出る
- service pack / phase contract / writer brief / validator を変更した
- Pro / human audit が未検証領域を指定した

## まだ薄いもの

次は未完成または未検証として残す。

- `real_stock`: 実案件文の stock がまだ少ない
- `app_memory`: previous commitments / materials / deadlines / phase を持つアプリ用 memory schema の実例検証がまだ薄い
- `multi_service`: `handoff-25000` は public:false のため、通常 live では未公開。#BR でのみ future-dual として扱う
- `email_channel`: ココナラチャット優先。メール展開は今は未着手
- `generic_* fallback`: blanket NG ではないが、#RE で鍛えた family が汎用分岐へ落ちていないかだけ targeted に見る

## 次にやること

1. 同型 #RE を routine で回さない。
2. `reply-memory-schema.yaml` と `phase-contract-schema.yaml` に沿った contract packet sample を、`ops/tests/contract-packets/bugfix-15000-v1-samples.yaml` に保持する。
3. contract packet の形は `./scripts/check-contract-packets.py` で確認する。
4. #R 実出力で違和感が出たら、まず writer brief / scenario routing / contract packet のズレを確認する。
5. 実案件 stock が来たら、`ops/tests/stock/inbox` に入れて、既存 family にないものだけ eval へ接続する。
6. Pro へ投げる場合は、batch 採点ではなく、`v1 completion review` として「何が未完成か / 何を止めるか / 何を次に作るか」を聞く。

## やらないこと

- 同じ family の採用確認だけを有料 xhigh で繰り返さない。
- `できます`、`ではありません`、`大丈夫です`、`〜の件`、`相談できます` を blanket NG にしない。
- 自然化のために、価格、scope、phase、secret、payment route、closed 後実作業境界を弱めない。
- Gold をテンプレートとして大量投入しない。
- Writer に監査プロンプト全文を背負わせない。
- `handoff-25000`、25,000円、主要1フロー整理、未公開購入導線を通常 live / #RE に戻さない。

## Pro に聞く次の論点

次に Pro を使うなら、次の形がよい。

- 現在の `bugfix-15000` 返信コアは v1 completion candidate と言えるか
- 高飽和 family を止める判断は妥当か
- 次に埋めるべき coverage gap は `real_stock` / `app_memory` / `multi_service` / `email_channel` のどれか
- ココナラ固有コアから、将来アプリ化できる汎用返信コアへ切り出す時の最小 contract packet は何か
- これ以上 #RE を回すより、どの設計物を作るべきか

## 判断

現時点の最優先は、#RE の量ではなく、完成判定・coverage・memory / phase contract を固めること。

したがって、次の通常アクションは `#RE` ではなく、v1 completion review に向けた棚卸しと contract packet 整備です。
