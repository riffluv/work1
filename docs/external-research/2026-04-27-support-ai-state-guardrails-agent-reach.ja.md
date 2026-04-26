# AI Support Agent / State Guardrails 外部調査メモ

日付: 2026-04-27  
調査レーン: Agent-Reach / web / Reddit / GitHub  
目的: ココナラ返信システムの `transaction_model_gap`、phase contract、監査ループを、英語圏の customer support AI / guardrails / QA loop の知見と照合する。

## 結論

英語圏でも、単に LLM に返信を書かせる方式は実務では不安定とされている。強い方向性は、LLM を中心に置くのではなく、状態・業務ルール・権限・ガードレール・QA スコアカード・継続改善ループを外側に置く設計。

現在の返信システムで育っている `phase contract`、`transaction_model_gap`、`closed 後の確認材料/実作業境界`、`#RE -> 監査 -> 再発だけ戻す` は、この方向と整合する。

ただし公開情報で見える多くの事例は、抽象度が高い。日本語の実務返信、ココナラの取引 phase、怒り気味 buyer、無料対応期待、正式納品/closed 後の導線まで具体化した完成パターンは確認できなかった。

## 使える知見

### 1. Generic LLM agent は実務では弱い

Salesforce の CRMArena-Pro では、generic LLM agent は single-turn で約58%、multi-turn で約35%まで成功率が落ちると報告されている。特に enterprise task では database / text / workflow / policy の4能力が必要で、単なる LLM 接続では不足する。

返信システムへの示唆:

- #RE で multi-turn / phase edge を回すのは正しい。
- 1回の返信が自然でも、phase をまたぐと破綻する可能性がある。
- `transaction_model_gap` は、generic LLM が落としやすい workflow / policy / state を見るためのレンズとして妥当。

参照:
- https://www.salesforce.com/blog/why-generic-llm-agents-fall-short/
- https://arxiv.org/abs/2505.18878

### 2. LLM は multi-turn で早い段階の誤解を引きずりやすい

Microsoft Research の `LLMs Get Lost In Multi-Turn Conversation` は、multi-turn で平均39%性能が落ち、初期の誤った仮定に依存して回復しにくいと報告している。

返信システムへの示唆:

- 「相手が何を聞いているか」を各 turn で再固定する必要がある。
- r0 で generic fallback が出ること自体は自然な失敗モード。監査で検知し、再発だけ guard へ戻すのが現実的。
- `primary_question / phase / transaction_model` を turn ごとに固定する設計は重要。

参照:
- https://www.microsoft.com/en-us/research/publication/llms-get-lost-in-multi-turn-conversation/
- https://arxiv.org/abs/2505.06120

### 3. ガードレールは prompt だけでは弱い

Replicant は「LLM に運転させたまま guardrails を足す」のではなく、決定的チェックポイント、必須データ収集、禁止アクション、ハードコードされた workflow を LLM の外側に置く考え方を示している。重要な原則は「LLM が判断しなくてよいことを LLM に判断させない」。

返信システムへの示唆:

- closed 後に実作業へ入れるか、入金前に原因確認できるか、秘密値を受け取るか、外部共有を使うか、などは LLM の文体判断ではなく deterministic guard に寄せるべき。
- `validator` は文章品質だけでなく、phase/action の不可侵条件を見る必要がある。
- Writer は自然文、Validator は取引構造と禁止事項、という分担は妥当。

参照:
- https://www.replicant.com/blog/ai-agent-guardrails-the-replicant-approach

### 4. AI support は living knowledge system が必要

Intercom は、AI support のためには help center だけでなく、product change、support teammate feedback、AI suggestions、outdated content audit、underperforming content optimization を継続的に回す knowledge management が必要と説明している。

返信システムへの示唆:

- `#RE` は単なる返信修正ではなく、knowledge / rule / gold / validator の継続更新ループとして機能している。
- `learning-log` と `gold candidate` の棚卸しは重要。
- 実ストックから出た「expected behavior / phase behavior」を正本に戻す運用は、英語圏の best practice と整合する。

参照:
- https://www.intercom.com/help/en/articles/11782981-mastering-knowledge-management-for-great-ai-support

### 5. QA scorecard は vibes ではなく次元別に見る

AI support QA の公開記事では、accuracy / policy compliance / completeness / tone / escalation / resolution / customer harm などを分けて評価する方向が多い。

返信システムへの示唆:

- 現在の監査軸 `直答 / scope順守 / 情報節約 / 自然さ / 次アクション` は妥当。
- 追加候補として `transaction clarity`、`phase route clarity`、`work/payment boundary clarity` を独立軸にできる。
- 怒り気味 buyer では tone だけでなく、無料期待・責任認定・支払い導線の誤読も評価する必要がある。

参考検索で確認した代表論点:
- missing steps
- incorrect claims
- policy/privacy violations
- robotic or defensive tone
- incomplete handoff / unclear next steps
- reopen / recontact risk

## 今の返信システムへ戻す候補

### 優先候補

1. `transaction_model_gap` を監査軸として維持  
   本文生成 rule ではなく、reviewer / validator / gold の判断軸として使う。

2. `phase/action deterministic guard` の強化  
   quote_sent 入金前作業、delivered 承諾/差し戻し、closed 実作業/材料確認、秘密情報、外部共有は validator 寄り。

3. `support QA scorecard` の拡張  
   既存5軸に加えて、必要に応じて `buyer_next_action_clear`、`payment/work_boundary_clear`、`phase_route_clear` を reviewer prompt に入れる。

4. `gold candidate` の定期棚卸し  
   Intercom 型の living knowledge system として、#RE で通過した良例を monthly / batch単位で整理する。

### まだ直接戻さないもの

- enterprise 向けの自動実行 agent / tool use / refund action などの設計。現在の返信システムは送信用文面が中心で、自動実行 agent ではない。
- resolution rate / CSAT / cost-per-resolution などの運用 KPI。SaaS 化フェーズでは必要だが、今の #RE には早い。
- human escalation の企業向け設計。ココナラ個人運用では、まず「見積り提案 / 新規依頼 / メッセージ確認」の導線へ置き換える。

## Deep Research に追加で聞くべき問い

1. customer support AI agent で、state / workflow / policy / action guardrails を実務に落とす公開事例はあるか。
2. support QA scorecard のうち、日本語実務返信システムに転用できる評価軸は何か。
3. AI support agent の失敗モードのうち、`transaction_model_gap` に近い既存概念はあるか。
4. closed ticket / reopen / post-resolution complaint / refund expectation の扱いで、AI応答設計上の best practice はあるか。
5. 日本語・高文脈コミュニケーションに転用する時、英語圏の guardrails をそのまま入れるとノイズになる要素は何か。

## 暫定判断

現在の返信システムは、英語圏の先端的な方向性とかなり整合している。特に「LLMの文章力を活かしつつ、取引状態・業務ルール・禁止事項・監査ループを外側に置く」構成は妥当。

一方、英語圏の公開事例は抽象度が高く、日本語のココナラ実務返信へそのまま使えるものではない。外部調査は、本文ルールとして直輸入するのではなく、監査軸・validator・gold候補の設計材料として使うのが安全。
