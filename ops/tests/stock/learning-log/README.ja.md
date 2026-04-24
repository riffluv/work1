# learning-log

目的:
- 監査で見つかった違和感を、単発の文面修正で終わらせず記録する
- `現象 -> パターン -> 層` の3段で残し、再発性と戻し先を判断できるようにする

使い方:
- 1件の指摘ごとに、`docs/reply-quality/learning-log-template.yaml` を元に1ファイル作る
- ファイル名は `YYYY-MM-DD-<short-topic>.yaml` を基本にする
- `adopt / observe / reject` の判定も残す
- rule に戻さなかった指摘も、再発しそうなら `not_returned_reason` に1行で理由を残す

見るポイント:
- `consultation_type`
- `buyer_decision_stage`
- `failure_label`
- `failure_layer`
- `generalizability`
- `return_target`
- `fix_unit`
- `recurrence_evidence`
- `existing_rule_hit`
- `not_returned_reason`

判断基準:
- 共通化できるかは、`service facts` を入れ替えても再発するかで切る
- Reviewer に項目を足す前に、Router / Contract / Facts の入力で防げないかを見る
