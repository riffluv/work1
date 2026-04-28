# #BR 境界ルーティング監査プロンプト（Codex xhigh）

このレビューでは、添付の `返信監査_batch-current.md` を主対象として監査してください。
プロンプト本文や過去ログ上の batch 名と、実際に添付・指定された batch 名が食い違う場合は、添付・指定された実ファイルを優先し、対象名のズレを監査結果で指摘してください。

必ず次のファイルも参照してください。

- `/home/hr-hm/Project/work/サービスページ/bugfix-15000.live.txt`
- `/home/hr-hm/Project/work/サービスページ/handoff-25000.ready.txt`
- `/home/hr-hm/Project/work/docs/reply-quality/boundary-routing-shadow-rehearsal.ja.md`

## 前提

これは通常の live 返信監査ではありません。  
`#BR` は、将来 `bugfix-15000` と `handoff-25000` が両方公開された時の境界ルーティングを検査する `training-visible / future-dual simulation` です。

ただし、現時点の実運用では `handoff-25000` は `public:false` です。  
通常 live 返信では `handoff-25000` のサービス名・25,000円・購入導線を出してはいけません。

この監査では、次の2つを分けてください。

- `#BR 内の future-dual ルーティングとして妥当な handoff 言及`
- `通常 live に漏れたら危険な private service leakage`

## 役割

あなたは reviewer です。  
新しい設計者として全面改稿するのではなく、既存の返信骨格が `bugfix-15000 / handoff-25000` の境界に対して安定しているかを監査してください。

## 最重要観点

1. buyer の主目的は `修正` か `把握/整理` か
2. `bugfix-first` / `handoff-first` / `neither` の route が妥当か
3. buyer に「どちらを選べばいいですか？」を返していないか
4. buyer がすでに正しい route を選んでいる時に、`合っています` などの診断文を外向けに出していないか
5. buyer がズレた route を選んでいる時に、受け流さず正しい入口へ誘導できているか
6. `15,000円の不具合1件修正` と `25,000円の主要1フロー整理` を混ぜていないか
7. `handoff` で修正完了を約束していないか
8. `bugfix` に引き継ぎメモ・主要フロー整理・複数フロー調査を吸収していないか
9. `新機能追加` を bugfix / handoff のどちらかへ無理に吸収していないか
10. future-dual simulation としては自然でも、live へ戻すと public:false 漏れになる表現がないか
11. サービス境界と支払い導線を混ぜていないか
12. buyer の次アクションが迷子になっていないか

## service facts の要点

### bugfix-15000

- 15,000円
- Next.js / Stripe / API連携の不具合1件修正
- 成果は原因確認だけでなく、修正済みファイル返却まで進める前提
- 直し切れない、修正済みファイルを返せない、原因や修正方針につながらない場合は、一方的に正式納品へ進めない
- 新機能追加、直接 push、本番デプロイ代行、外部共有、外部連絡はしない

### handoff-25000

- 25,000円
- 主要1フローの現状整理・引き継ぎメモ作成
- 関連ファイル、処理の流れ、危険箇所、次に見る順番を整理する
- 修正成功を成果条件にしない
- コード修正、新機能開発、正式な仕様書作成、リポジトリ全体の網羅調査、テスト作成は含めない
- 主要1フローを超える場合は追加フロー扱い

### payment route separation

- `bugfix / handoff / neither` はサービス範囲・成果物・料金単位の判定
- `同じトークルーム内` / `おひねり` / `有料オプション` / `新規依頼` は取引状態に応じた支払い導線
- buyer が支払い方法を聞いていない時は、`別成果物` `別対応` `進め方と費用を先に相談` までで止める
- buyer が明示的に聞いた時だけ、state に合わせて支払い導線を出してよい
- prequote / quote_sent では、まだ存在しないトークルーム内追加支払いを約束しない
- purchased / delivered では、トークルームが開いている前提の追加支払い導線を条件付きで案内してよい
- closed では、旧トークルーム内のおひねりや追加購入へ誘導しない

## 追加で使ってよい監査ラベル

- `boundary_route_gap`: buyer の主目的に対して route が見えていない、または buyer に選択を丸投げしている
- `route_state_mismatch`: buyer が迷っていないのに適合診断を出している、またはズレた route 選択を受け流している
- `service_misroute`: bugfix にすべきものを handoff に送る、または handoff にすべきものを bugfix に吸収している
- `price_separation_gap`: 15,000円 / 25,000円 / 追加フロー / 別件の価格が混ざっている
- `scope_absorption`: bugfix に整理・新機能・複数フロー調査を吸収している
- `handoff_overpromise`: handoff で修正完了・不具合解消を約束している
- `public_leak`: public:false の handoff 名称・価格・購入導線が、通常 live 返信として出ている
- `payment_route_bleed`: buyer が支払い方法を聞いていないのに、おひねり・有料オプション・同じトークルーム内導線が前面に出ている
- `phase_payment_mismatch`: prequote / quote_sent / purchased / delivered / closed の状態に合わない支払い導線を出している
- `neither_route_miss`: 新機能追加など、どちらでもないものを bugfix / handoff へ無理に入れている
- `transaction_model_gap`: 文面単体は安全でも、取引構造・価格・作業開始条件・成果物導線が一本につながっていない
- `response_weight_mismatch`: 必要以上に契約説明化している。ただし安全境界を削るためには使わない
- `buyer_state_ack_gap`: buyer が不安・疲弊・不信を出しているのに状態シグナルを落としている
- `context_bleed`: buyer 文にない別シナリオの情報が混入している

## 注意

- `#BR` は通常 live 返信ではありません。25,000円や handoff の説明が出ただけで即 hard fail にしないでください。
- ただし、batch 内で `training-visible / future-dual simulation` として成立しているか、通常 live に戻した時に漏れない設計になっているかは見てください。
- `handoff` を出す場合も、buyer の主目的が整理・把握・引き継ぎである必要があります。
- buyer がすでに適切な route を明示している場合は、`その内容が合っています` と診断せず、依頼内容を受けて範囲・価格・次アクションへ進めてください。
- buyer の選んだ route が実際の主目的とズレている場合は、受け流さず、正しい入口へ短く誘導してください。
- 「コードが分からない」だけで handoff に逃がさないでください。今止まっている不具合を直したいなら bugfix-first です。
- 「とりあえず両方できます」のような曖昧回答は落としてください。
- 「15,000円の修正で軽い整理も全部見ます」「25,000円整理でバグも直します」は事故です。
- buyer が聞いていない内部条件を並べすぎる指摘は soft lens として扱い、必須修正は scope / route / price / public leak に絞ってください。

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
