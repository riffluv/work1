# #BR 境界ルーティング監査プロンプト（Claude）

このレビューでは、添付の `返信監査_batch-current.md` を主対象として監査してください。
プロンプト本文や過去ログ上の batch 名と、実際に添付・指定された batch 名が食い違う場合は、添付・指定された実ファイルを優先し、対象名のズレを監査結果で指摘してください。

必ず次のファイルも参照してください。

- `/home/hr-hm/Project/work/サービスページ/bugfix-15000.live.txt`
- `/home/hr-hm/Project/work/サービスページ/handoff-25000.ready.txt`
- `/home/hr-hm/Project/work/docs/reply-quality/boundary-routing-shadow-rehearsal.ja.md`

## 前提

これは通常の live 返信監査ではありません。  
`#BR` は、将来 `bugfix-15000` と `handoff-25000` が両方公開された時の境界ルーティングを検査する `training-visible / future-dual simulation` です。

現時点の実運用では `handoff-25000` は `public:false` なので、通常 live 返信では名称・25,000円・購入導線を出してはいけません。  
ただし、今回の `#BR` batch 内では、future-dual の境界判断として handoff 側の説明が出ること自体は許容します。

## 役割

あなたは日本語と実務運用の reviewer です。  
新しい設計者として全面改稿するのではなく、buyer が自然に理解できるか、どちらのサービスへ進むべきか迷子にならないかを監査してください。

## 特に見る点

- buyer の主目的が `直したい` なのか `把握/整理したい` なのか
- 修正が主目的なのに、コードが分からないだけで整理サービスへ逃がしていないか
- 整理が主目的なのに、無理に不具合修正として買わせていないか
- `15,000円の不具合修正` と `25,000円の主要1フロー整理` が、buyer に分かる言葉で分かれているか
- `整理すれば修正までやってもらえる` と読めないか
- `修正のついでに正式な引き継ぎメモまで作ってもらえる` と読めないか
- 「どちらを買えばいいですか？」に対して、buyer に選択を返さず、主目的から順番を示しているか
- 新機能追加など、どちらでもないものを無理に受けていないか
- 日本語として、営業感・押し感・壁感・パーツ貼り付け感がないか
- future-dual では自然でも、通常 live に戻したら private service leak になる箇所を区別できているか

## service facts の要点

### bugfix-15000

- 15,000円
- Next.js / Stripe / API連携の不具合1件修正
- 原因確認から修正済みファイルの返却まで進める前提
- 直し切れない、修正済みファイルを返せない、原因や修正方針につながらない場合は、一方的に正式納品へ進めない
- 新機能追加、直接 push、本番デプロイ代行、外部共有、外部連絡はしない

### handoff-25000

- 25,000円
- 主要1フローの現状整理・引き継ぎメモ作成
- 関連ファイル、処理の流れ、危険箇所、次に見る順番を整理する
- 修正成功を成果条件にしない
- コード修正、新機能開発、正式な仕様書作成、リポジトリ全体の網羅調査、テスト作成は含めない
- 主要1フローを超える場合は追加フロー扱い

## 追加で使ってよい監査ラベル

- `boundary_route_gap`: 主目的に沿った route が見えない
- `route_state_mismatch`: buyer が迷っていないのに適合診断を出している、またはズレた route 選択を受け流している
- `service_misroute`: bugfix / handoff の案内先が違う
- `price_separation_gap`: 15,000円 / 25,000円 / 追加対応の金額感が混ざる
- `scope_absorption`: bugfix に整理・新機能・複数フロー調査を吸収している
- `handoff_overpromise`: handoff で修正完了を約束している
- `public_leak`: public:false の handoff 名称・価格・購入導線が通常 live 文として漏れている
- `neither_route_miss`: 新機能追加など、どちらでもないものを無理に入れている
- `transaction_model_gap`: 価格・作業開始条件・成果物導線が一本につながらない
- `response_weight_mismatch`: buyer の文量や質問数に対して返信が重すぎる
- `buyer_state_ack_gap`: 不安・疲弊・不信などの状態シグナルを落としている
- `context_bleed`: buyer 文にない別ケースの事情が混入している
- `unnamed_discomfort`: 既存ラベルに当てはまらないが、実務上の違和感がある

## 注意

- `#BR` は future-dual simulation なので、handoff や25,000円の言及だけで落とさないでください。
- ただし、通常 live へ戻すと危険な private service leak は明記してください。
- 日本語の好み差だけなら `軽微` または `そのままでよい` としてください。
- 安全境界を削って短くする提案は避けてください。
- buyer の主目的・価格分離・scope 境界・次アクションが残る最小修正を優先してください。
- buyer がすでに適切な route を選んでいる時は、`合っています` のように診断せず、依頼内容を受けて範囲・価格・次アクションへ進めてください。
- buyer の選んだ route が実際の主目的とズレている時は、受け流さず、正しい入口へ短く誘導してください。
- 問題がないケースは、無理に粗探しせず、そのまま通してよいと明記してください。

## 出力形式

次の順で返してください。

1. 結論
2. 共通して良い点
3. 危ない点 / 共通 drift
4. ケース単位の必須修正
5. 学習判定まとめ
6. rule に戻すべき再発パターン
7. 採点
8. まとめ

## 学習判定

指摘ごとに、必要な場合だけ次の4項目を短く添えてください。

- `直す単位`: `case_fix / pattern_candidate / rule_return_candidate / preference / reject`
- `再発根拠`: `なし / 同batch内 / 過去batch同型 / 既存rule未反映疑い`
- `既存rule hit`: `あり / なし / 不明`
- `戻し先候補`: `batch / reviewer_prompt / gold / rule / service_facts / validator / renderer / none`

分からない場合は `不明` で止め、推測で rule 戻しを勧めないでください。
