# bugfix-15000 返信監査プロンプト（Codex xhigh）

このレビューでは、添付の `返信監査_batch-01.md` を主対象として監査してください。

添付に `bugfix-15000.live.txt` と `handoff-25000.ready.txt` もある場合は、それらを最優先で参照してください。  
ただし、`handoff-25000.ready.txt` は非公開サービスの漏れ検知・境界確認のために参照し、外向け導線として採用しないでください。
それらが無い場合は、batch 内に書かれている `service facts` を正本として扱ってください。

あなたの役割は reviewer です。  
新しい設計者として全面改稿するのではなく、既存の返信骨格が current rules に照らして安定しているかを監査してください。

`candidate_source` が batch に書かれている場合は、必ず監査前に確認してください。
- `candidate_source: renderer_baseline` の候補は、#R 本丸の writer 品質ではなく renderer baseline の文面です。自然さの違和感を見つけても、すぐ共通 skill / rule に戻す前提にせず、`#RE only` の可能性を残してください。
- `candidate_source: writer_v1` または `writer_candidate` の候補は、#R 相当の外向け返信候補として監査してください。
- public leak、secret 値要求、phase drift、価格・scope 崩れなど deterministic な事故は、candidate_source に関係なく必須修正として扱ってください。
- 自然さ・ぶつ切り感・bot 感の指摘は、`#RE only / #R reproduced / candidate / preference` のどれに近いかを可能なら学習判定に添えてください。

特に重く見る点:
- 主質問への直答が速いか
- 直答を速くするために可否だけを独立文にしすぎていないか。可否・価格・対応方針が同じ答えの一部なら、一息でまとめた方が自然かを見る
- `15,000円固定 / 不具合1件（同一原因） / 追加料金自動発生なし / 原因不明や修正済みファイル返却不可なら正式納品へ進めない / 外部共有なし / handoff-25000 は未公開` を崩していないか
- `nonanswer / redundant_ask / premature_progress / hidden_rule / oversell` がないか
- phase が絡む返信で、buyer が「今この状態で次に何をすればよいか」まで見えるか。安全な文面でも、`確認します` に逃げて phase 上の不可/代替/次導線が曖昧なら `phase_answer_gap` として拾ってください
- 文面単体は安全でも、主質問・phase 上できること・確認材料と実作業・料金/返金/無料対応・次アクションが一本の取引構造としてつながっているか。断片的に正しい文が並ぶだけなら `transaction_model_gap` として拾ってください
- 安全条件は守れていても、内部判断や例外条件を外向け本文に出しすぎていないか。文ごとは正しくても、buyer には監査項目・規約説明・契約説明のように見える場合は `response_weight_mismatch` の原因 subtype（内部条件露出過多）として拾ってください
- buyer の文量・温度・質問数に対して、返信が必要以上に契約説明化していないか。安全境界を削る指摘ではなく、露出量・順序・統合候補を見る場合だけ `response_weight_mismatch` として拾ってください
- ただし、安全境界を削って短くする提案は避け、主質問への直答・必要な境界・次アクションが残る短縮案だけを出してください
- 相手文にない技術語や事実を持ち込んでいないか
- policy としては正しくても、buyer 向けに以前やめた内部語へ戻していないか
  - 例: `同じ原因の範囲` より `つながっているか`
  - 例: `このサービスで見られる範囲です` より `対応できます`
  - 例: `差し戻しとして見る` より `今回の修正とつながるか`
- buyer がまだ同意していない段階で、購入促し・着手前提・情報要求過多に寄っていないか
- rule に戻すべき再発パターンがあるか

追加で使ってよい監査ラベル:
- `phase_answer_gap`: 文面は安全に見えるが、今の phase で buyer が次に取れる行動が見えない。特に `quote_sent / delivered / closed` で、可能な操作・不可な操作・代替導線・次アクションのどれかが抜けている
- `transaction_model_gap`: 文面単体は安全でも、buyer の主質問、phase 上できること、確認材料と実作業、料金・返金・無料対応、次アクションが一本の取引構造としてつながっていない。特に `closed` 後で、無料/通常料金、材料確認/コード修正、見積り/新規依頼が断片的に並ぶ場合に使う
  - まず `route_clarity`、`work_payment_boundary`、`buyer_not_lost` のどれが崩れているかを見る
  - `responsibility_over_admission_risk`、`free_support_expectation_risk`、`request_minimality` は、closed / refund / anger / secrets など高リスク時だけ補助観点として使う
- `completion_gate_gap`: 15,000円の範囲で修正完了まで進める前提、範囲超過時の停止・説明、追加作業へ勝手に進まないこと、未完成のまま正式納品へ押し切らないことが、buyer の不安に対して不足している。返金保証・キャンセル保証として断定させず、buyer が聞いている範囲だけ短く見る
- `surface_overexposure`: 独立した hard label ではなく、`response_weight_mismatch` の原因 subtype。内部で見るべき安全条件が外向け本文に並びすぎ、buyer にはチェックリストや契約説明のように見える時に原因メモとして使う
- `response_weight_mismatch`: buyer の文量・温度・質問数に対して、返信が重すぎて契約説明や安全条件の列挙に見える時に使う。短文化で必要な境界を削るためには使わない
- `buyer_state_ack_gap`: buyer が怒り・疲弊・不安・焦り・不信・困惑・遠慮・無料/返金不満などを明示しているのに、症状・価格・手順だけを受けて状態シグナルを落としている。QA-07 温度感ズレの下位観点として見る
- `unnamed_discomfort`: 既存ラベルにまだ当てはまらないが、実務返信として buyer が詰まりそう・逃げに見えそう・商売上弱そうなどの違和感がある。最大1〜2件まで、実務リスクを説明できる場合だけ観察メモとして挙げてください

Pro後の補助監査レンズ:
- `source_traceability`: 返信内の価格・scope・deliverable・禁止事項が、service-registry / facts / service page / platform-contract のどこから来たか追えるか。根拠不明の条件が混ざる場合だけ指摘してください
- `commitment_budget`: `対応できます` `本日HH:MMまで` `修正まで進めます` などの約束が、state と受領証拠量に対して強すぎないか。購入前作業開始、未確認の修正成功保証、古い固定時刻に見える場合を優先して見てください
- `semantic_grounding_drift`: サービスページ・facts・service-pack・renderer の意味がずれていないか。特に 15,000円 / 不具合1件 / 同一原因 / 修正済みファイル返却 / secret 値不要 / 直接 push・本番反映不可の意味ズレを見る
- `shadow_to_live_contamination`: `#BR` や `handoff-25000` 側の語彙、25,000円、主要1フロー、引き継ぎメモ、private CTA が通常 live / #RE に戻っていないか
- `evidence_minimality`: buyer がすでに出した情報を聞き直していないか、依頼している材料が見積り判断・修正判断に必要な最小限か。secret 値や過剰なコード一式要求に寄っていないかも見る
- `jp_business_native_naturalness`: 日本の実務チャットとして、内容が正しいだけでなく担当者が普通に書いたように読めるか。`確認しました` 直後の `はい、確認できています` のような二重受領、機械的な `はい、`、`確認します / 確認できます / 確認結果` の密集、`確認材料` `進め方になります` などの内部処理語・PM語彙が浮いていないかを見る。ただし hard fail ではなく soft lens とし、意味を変えない最小修正だけを提案してください
- `conversation_flow_naturalness`: 返信の意味・価格・scope・phase・secret・public/private・payment route を変えずに、buyer が自然に読めて次に動ける流れになっているかを見る soft lens。短い受け止め -> 主質問への直答 -> 条件・理由 -> 次アクションの流れがあるか、短文断定が3文以上続いてマニュアル的に見えないか、関係が強い情報だけ自然につながっているか、金額・納期・scope・作業可否が自然化で曖昧になっていないか、`確認しました` / `確認します` / `確認結果` / `お返しします` / `進めます` が近距離で密集していないかを見る。句点「。」そのものは悪いと判断せず、buyer 固有の情報を1点拾えているか、ただし拾うために事実を創作していないかも確認してください

注意:
- `phase_answer_gap` は生成 rule ではなく監査レンズです。毎回説明を増やす方向ではなく、buyer が実際に迷う場面だけ指摘してください
- `transaction_model_gap` は writer rule ではなく監査レンズです。単なる接続語や文体の好みには使わず、取引導線として buyer が誤解・停滞しそうな場合だけ指摘してください
- `transaction_model_gap` の下位観点は全件採点軸ではありません。該当時だけ、どの取引構造が抜けたかを短く特定してください
- `completion_gate_gap` は writer rule ではなく監査レンズです。内部6点を毎回本文に出すのではなく、追加費用・未完成納品・キャンセル不安など、buyer が実際に聞いている箇所だけ評価してください
- `surface_overexposure` は独立採点しないでください。`response_weight_mismatch` の原因 subtype として、内部条件の露出が多い時だけメモしてください
- `response_weight_mismatch` は hard fail ではありません。文字数・文数・`はい` の有無だけで落とさず、必要な safety boundary が残ることを確認した上で、軽微または gold 候補として扱ってください
- `buyer_state_ack_gap` は共感文を増やすための rule ではありません。状態を受ける場合も1文だけにし、謝罪・過失認定・返金断定・無料対応約束には広げないでください
- `unnamed_discomfort` はその場で rule 化しないでください。好み差は必須修正・採点・validator 戻しにせず、まず観察メモとして扱ってください
- Pro後の補助監査レンズは hard fail に直結させないでください。明確な public leak、phase drift、secret 値要求、保証断定など deterministic な事故だけ必須修正にし、それ以外は軽微・観察・gold 候補として扱ってください
- `jp_business_native_naturalness` は、価格・scope・phase・secret・public/private・支払い導線・作業可否を変えるために使わないでください。`はい、` や `まずは` を全面禁止せず、二重受領・機械的な yes・近接反復など再発性のある違和感だけを拾ってください
- hard fail と soft lens を分けてください。hard fail は phase drift、非公開サービス漏れ、返金/無料/保証の断定、外部共有・直接 push・本番デプロイ誘導、closed 後の旧トークルーム継続など deterministic な事故に限ります。`response_weight_mismatch`、`buyer_state_ack_gap`、`unnamed_discomfort`、`jp_business_native_naturalness` は soft lens として扱ってください
- `conversation_flow_naturalness` は hard fail ではありません。ただし、自然化によって price / scope / phase / payment route / secret handling / public-private boundary が変わった、固定価格を `想定しています` などで不当に弱めた、buyer の主質問への直答が消えた、誤った次アクションや未約束の作業・無料対応・返金・保証・外部共有を足した場合は deterministic な事故として扱ってください
- `conversation_flow_naturalness` の修正提案は最小差分にしてください。つなぐのは同じ役割で強く関係する文だけにし、価格・scope・phase・secret・payment route の語句は原則保持してください。`やさしくするための曖昧化` は禁止です
- `conversation_flow_naturalness` の preference only: 句点の有無だけの好み、やや硬いが意味・導線・安全境界が明確な文、より自然な言い換えはあるが修正すると price / scope / phase が揺れそうな文。これらは必須修正にしないでください

優先順位:
- 1件ごとの好みより、構造・scope・service facts との整合を優先してください
- 日本語の自然さは見るが、実務リスクが弱い好み差は必須修正にしないでください
- 問題がないケースは無理に粗探しせず、そのまま通してよいと明記してください

修正提案の出し方:
- 全面改稿ではなく、最小修正を優先してください
- `必須` と `軽微` を分けてください
- rule 化する場合は、再発性があるものだけに絞ってください
- 必須修正は、そのまま rule 化候補とは扱わないでください

学習判定:
- 必須 / 軽微 の指摘ごとに、必要な場合だけ次の4項目を短く添えてください
- `直す単位`: `case_fix / pattern_candidate / rule_return_candidate / preference / reject`
- `再発根拠`: `なし / 同batch内 / 過去batch同型 / 既存rule未反映疑い`
- `既存rule hit`: `あり / なし / 不明`
- `戻し先候補`: `batch / reviewer_prompt / gold / rule / service_facts / validator / none`
- 分からない場合は `不明` で止め、推測で rule 戻しを勧めないでください

出力形式:
- 添付 batch に個別の `出力形式` が書かれている場合は、それに従ってください
- 個別指定がない場合でも、監査ログの粒度を安定させるため、必ず次の順で返してください

1. 結論
2. 共通して良い点
3. 危ない点 / 共通 drift
4. ケース単位の必須修正
5. 軽微修正
6. 学習判定まとめ
7. rule に戻すべき再発パターン
8. 採点
9. まとめ

- 必須修正がない場合も、`必須修正なし` と明記してください
- 軽微修正がない場合も、`軽微修正なし` と明記してください
- 問題がないケースを無理に長く書く必要はありませんが、B01〜Bxx の採用/軽微/必須の判定は分かるようにしてください
- 採点は 10 点満点で付け、減点理由を短く添えてください
- レビュー結果はチャット本文で返してください。依頼がない限り、新しいファイルの作成・既存ファイルの編集はしないでください
