# contract packet samples

## 目的

返信OSの `memory / phase / reply_contract / writer` の接続を、実装前に見える形で確認するためのサンプル置き場です。

ここに置くものは、送信用テンプレートではありません。Writer に自由に文章を書かせる前に、何を事実として渡し、何を禁止し、どの質問へ先に答えるかを固定するための最小 packet です。

## 現在のファイル

- `bugfix-15000-v1-samples.yaml`
  - `bugfix-15000` の v1 完成候補を前提にした、主要 phase 別の contract packet サンプル。
  - `prequote / quote_sent / delivered / closed` の基本形と、`purchased` の現在地・既存コミットメント・deadline・依頼済み追加材料受領・秘密値伏せ直し受領を収録。
  - `channel / transaction_state_evidence / service_truth_version / packet_source / source_type / redaction_policy / sendability` も含め、将来の runtime packet 化で必要になる最小メタ情報を保持する。
- `bugfix-15000-v1-fixtures.yaml`
  - 上記 packet sample が、どの入力相当の buyer message / phase / explicit question に紐づくかを固定する trace fixture。
  - 返信文の正解集ではなく、sample packet が空中に浮いていないかを見るための smoke test 用。

## 使い方

- #R / #RE の生成経路がズレた時に、まず packet のどこが違うかを見る。
- アプリ化する時に、画面入力から作るべき最小データ構造の参考にする。
- Pro に v1 completion review を依頼する時に、返信文そのものだけでなく、返信前の判断単位として見せる。
- 形の確認は `./scripts/check-contract-packets.py` を使う。
  - explicit questions が `answer_map` / `ask_map` で全て扱われているか。
  - `answer_after_check` に `hold_reason` / `revisit_trigger` があるか。
  - `ask_map` が `blocking_missing_facts` と対応しているか。
  - `required_moves` / `forbidden_moves` が `output-schema.yaml` の enum に収まるか。
  - 外向け判断文に private service / private price が混ざっていないか。
  - `writer_notes.use` がテンプレ圧になっていないかは warning として見る。
- 入力との追跡確認は `./scripts/check-contract-packet-fixtures.py` を使う。
  - fixture の phase / family / channel が packet と一致しているか。
  - fixture の buyer message が `memory_packet.buyer_latest_message` と一致しているか。
  - fixture の explicit questions が `reply_contract.explicit_questions` と一致しているか。
  - `handoff-25000` など hidden service が visible service に入っていないか。
  - これは runtime packet builder ではなく、まず sample packet の traceability を守るための最小ゲート。
- fixture からの最小生成確認は `./scripts/build-contract-packets.py --check-against-samples` を使う。
  - fixture と `phase-contract-schema.yaml` / `service-registry.yaml` から、最小 generated packet を作る。
  - sample packet とは全文一致ではなく、phase / family / channel / visible service / buyer latest message / explicit questions / redaction policy / answer_map / ask_map / issue_plan / required_moves / forbidden_moves / response_order / phase allowed・forbidden の重要項目だけを比較する。
  - `answer_map` は family ごとの最小 `answer_brief` まで生成する。
  - `ask_map` は現時点では closed の関係確認など、追加材料が明確に必要な family だけ生成する。
  - `response_decision_plan` は `primary_concern` / `facts_known` / `direct_answer_line` / `response_order` まで生成する。
  - 自然文の writer 判断や文体判断までは生成しない。そこは次段階の writer / renderer の責務として残す。
- generated packet と #R writer brief の同期確認は `./scripts/check-contract-packet-writer-brief-sync.py` を使う。
  - fixture から一時的な #R case を作り、`render-coconala-reply.py --writer-brief` の lane / scenario / buyer_message / service / answer_map / required_moves / response_decision_plan を確認する。
  - これは自然文の良し悪しを見る監査ではなく、packet と #R の意味契約が別ルートへ落ちていないかを見る smoke test。

## 注意

- Gold reply ではない。
- 文面テンプレートではない。
- runtime packet builder そのものではない。
- `build-contract-packets.py` は最小 builder smoke であり、production app の packet builder ではない。新 family を足す時は、blanket に全質問 answer_now にせず、追加確認が必要な質問は `ask_map` と `blocking_missing_facts` へ落とす。
- `check-contract-packet-writer-brief-sync.py` は #R 本文品質の監査ではない。#R の writer brief が packet と同じ phase / scenario / answer coverage に接続されているかだけを見る。
- `handoff-25000`、25,000円、主要1フロー整理は通常 live packet に入れない。
- `known_commitments` や `received_materials` にない事実を writer が補完してはいけない。
