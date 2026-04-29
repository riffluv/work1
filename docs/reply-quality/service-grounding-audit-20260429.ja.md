# 2026-04-29 service-grounding audit

## 結論

判定: 採用圏。

`bugfix-15000` のサービス本丸は、`service-registry.yaml`、`service.yaml`、`service-pack`、renderer / validator / regression に落ちている。
ココナラ仕様も `platform-contract.yaml` と各 state renderer に接続されている。

ただし、購入前相談を扱う `estimate_initial` renderer は、購入後 / delivered / closed の renderer に比べて `service_grounding` の明示接続が浅かった。
今回、prequote でも registry から public service facts を読み込み、case に `service_grounding` を持たせるように補強した。

## 監査対象

- `/home/hr-hm/Project/work/サービスページ/bugfix-15000.live.txt`
- `/home/hr-hm/Project/work/os/core/service-registry.yaml`
- `/home/hr-hm/Project/work/os/coconala/platform-contract.yaml`
- `/home/hr-hm/Project/work/ops/services/next-stripe-bugfix/service.yaml`
- `/home/hr-hm/Project/work/ops/services/next-stripe-bugfix/service-pack/*.yaml`
- `scripts/render-prequote-estimate-initial.py`
- `scripts/render-quote-sent-followup.py`
- `scripts/render-post-purchase-quick.py`
- `scripts/render-delivered-followup.py`
- `scripts/render-closed-followup.py`
- `scripts/render-coconala-reply.py`
- `scripts/check-rendered-*.py`
- `ops/tests/regression/service_pack_fidelity_*`

## 接続マップ

1. `service-registry.yaml`
   - `bugfix-15000`: `public: true`
   - `handoff-25000`: `public: false`
   - `source_of_truth` と `service_pack_root` を保持
2. `bugfix-15000.live.txt`
   - buyer 向け公開契約の正本
   - 価格、範囲、納品物、FAQ、回答例、禁止事項を保持
3. `service.yaml` / `service-pack`
   - 価格、scope unit、hard no、same / different、unknown cause gate、evidence minimum を構造化
4. renderer
   - prequote / quote_sent / purchased / delivered / closed の各 state で service facts と platform state を使う
5. validator / regression
   - public/private leak、service grounding、state boundary、service-pack fidelity を検査

## 本丸から落ちている主要項目

| 公開ページの核 | 落とし込み先 | 状態 |
| --- | --- | --- |
| 15,000円 | `service.yaml`, `facts.yaml`, renderer, validator | OK |
| 不具合1件 = 同一原因 | `decision-contract.scope_unit`, `facts.scope_unit` | OK |
| 原因確認 / 修正 / 確認手順 / 修正済みファイル返却 | `facts.public_facts.includes`, `deliverables` | OK |
| 追加料金は自動発生しない | `decision-contract.additional_work_policy` | OK |
| 原因不明のまま正式納品しない | `decision-contract.unknown_cause_gate` | OK |
| 最終確認と本番反映は依頼者側 | `decision-contract.final_confirmation` | OK |
| `.env` / APIキー / Webhook secret の値は扱わない | `boundaries.hard_no`, `evidence-contract`, renderer guard | OK |
| 通話 / 外部連絡 / 外部決済 / 直接 push / 本番デプロイをしない | `boundaries.hard_no`, `service.yaml.hard_no`, validators | OK |
| 購入前は見立てと必要情報整理まで | `facts.phase_rules.prequote`, prequote renderer | OK |
| handoff は public:false | `service-registry.yaml`, unified public leak gate | OK |

## ココナラ仕様の接続

`platform-contract.yaml` に次が分離されている。

- prequote / quote_sent / purchased / delivered / closed の内部 state
- メッセージとトークルームの違い
- closed 後のトークルーム投稿 / ファイル投稿 / おひねり不可
- 見積り提案と購入後トークルームの違い
- 正式納品とクローズ前後の違い
- サービス境界と支払い導線を混ぜないこと
- 返金 / キャンセルをこの場で断定しないこと

このため、サービス範囲は service registry / service pack、取引状態は platform contract という分離になっている。

## 今回補強した点

### prequote service_grounding

`render-prequote-estimate-initial.py` に `load_service_grounding()` を追加した。
これにより、購入前相談でも次を registry / facts / pack から読み込む。

- service_id
- public_service
- source_of_truth
- facts_file
- service_pack_root
- display_name
- base_price / fee_text
- scope_unit
- hard_no
- out_of_scope

`check-rendered-prequote-estimate.py` でも、public bugfix の prequote case に `service_grounding` があることを検査するようにした。

## 残る注意点

1. renderer 文面には `15,000円` のリテラルがまだ多い。
   現在の価格が固定なので問題ではないが、将来価格を変える場合は renderer / regression の価格表現も一括確認が必要。
2. `service-pack fidelity` は「期待 ref が存在するか」の検査であり、公開ページ全文との完全な意味一致を自動証明するものではない。
   サービスページを大きく直した時は、人間の semantic review が必要。
3. `check-coconala-reply-role-suites.py` は role ごとに full regression を回すため、`regression_seed` の service-pack fidelity は role suite 内では選ばれない。
   grounding 確認では `python3 scripts/check-service-pack-fidelity.py --save-report --show-passes` を別途回す。

## 検証結果

- `./scripts/os-check.sh`: OK / `mode=coconala`
- `python3 scripts/check-service-pack-fidelity.py --save-report --show-passes`: pass 19 / fail 0
- `python3 scripts/check-rendered-prequote-estimate.py --fixture ops/tests/quality-cases/active/post-br-live-boundary-bugfix41.yaml`: OK
- `python3 scripts/check-rendered-prequote-estimate.py --fixture ops/tests/prequote-contract-v2-top5.yaml`: OK
- `python3 scripts/render-coconala-reply.py --fixture ops/tests/quality-cases/active/post-br-live-boundary-bugfix41.yaml --lint`: OK

## Pro に聞くなら

今すぐ必須ではない。

次に Pro を使うなら、論点は `返信品質` より `service-grounding architecture` がよい。

- service page -> service-pack -> renderer / validator の責務分離は、将来の複数サービス展開に耐えるか
- 価格・範囲・hard no を renderer 内リテラルで持つ部分を、どこまで動的化すべきか
- `service-pack fidelity` を ref 存在チェックから semantic diff 監査へ進めるべきタイミング
- `platform-contract` と service boundary の分離は、ココナラ以外の販売面へ展開しても崩れにくいか
