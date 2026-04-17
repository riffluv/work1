# Service-Pack v1 Fixed Points

## 目的
- `bugfix-15000` と `handoff-25000` の service-pack で、v1 として固定してよい構成を短く明示する
- 次の Codex や将来の移植時に、何が確定済みで何が未確定かを迷わないようにする

## v1 で固定してよいもの

### 1. 8ファイル構成
- `facts.yaml`
- `boundaries.yaml`
- `decision-contract.yaml`
- `evidence-contract.yaml`
- `routing-playbooks.yaml`
- `state-schema.yaml`
- `seeds.yaml`
- `tone-profile.yaml`

補足:
- `facts / boundaries / decision / evidence` が service理解の核
- `routing / state` は会話運用の補助
- `seeds / tone` は runtime asset

### 2. source-of-truth の優先順
1. 公開サービスページ
2. `facts.yaml` / `boundaries.yaml`
3. `decision-contract.yaml` / `evidence-contract.yaml`
4. `routing-playbooks.yaml` / `state-schema.yaml`
5. `seeds.yaml` / `tone-profile.yaml`

### 3. runtime の読む順
1. `facts / boundaries`
2. `decision / evidence`
3. `routing-playbooks`
4. `state-schema`
5. `seeds / tone`

### 4. first-class に持つべき契約
- `what it sells`
- `what it does not sell`
- `how it decides`
- `where it stops`
- `what minimum evidence it asks for`
- `how secondary thread is carried`

### 5. fidelity の回帰源
- 公開サービスページ
- FAQ
- 回答例
- `ops/tests/regression/service_pack_fidelity_*/cases.yaml`

## bugfix-15000 で v1 固定してよい点
- `same / different / undecidable`
- `unknown cause gate`
- `additional work is not automatic`
- `final confirmation owner`
- Stripe 系 first-class evidence
- secondary symptom の `return_timing / required_input`

## handoff-25000 で v1 固定してよい点
- `one_flow / extra_flow / repair / undecidable`
- `handoff first / bugfix first`
- `整理だけで止める / 修正は別対応`
- `most_troubling_operation` 起点で相談可
- `intended_reader` を first-class evidence に置く
- private / ready を service-pack 側で保持し、外向け導線へ漏らさない

## v1 ではまだ固定しないもの
- `cases.yaml` の網羅性
- `decision-contract` の細粒度な clause 拡張
- `state-schema` の追加項目
- `routing-playbooks` の細かい wording
- `seeds` の本数
- `tone-profile` の細密化

## v1 の完了条件
- bugfix / handoff の両方で fidelity 監査が `かなり良い`
- `decision / evidence` が first-class で存在する
- `service理解` と `reply スタイル` が分離されている
- runtime の読む順が固定されている
- regression source が各サービスに最低1本ある

## v1 後の運用
- 実運用のズレは、まず
  - page
  - facts / boundaries
  - decision / evidence
  - routing / state
  - seeds / tone
  のどこで起きたかを切る
- 追加改善は v1 を壊さず、漸進的に足す
- 新サービスへ移植する時は、まずこの v1 骨格で作る
