# Gold Replies（reply-only）

## 目的
- 良い返信を「雰囲気で思い出す」のではなく、再利用できる基準として残す。
- 温度感、情報量、質問数、次アクションの出し方を安定させる。
- 個別案件の完全テンプレではなく、近いケースのアンカーとして使う。

## 使い方
- 新しく返信を作る前に、近い 1 本だけ見る。
- family / phase / lens から探す時は、上位 map の `docs/reply-quality/gold-reply-map.yaml` を先に見る。
- `status: current` 相当として扱えるものだけを few-shot に使う。古い比較用・監査用の例は `eval_only`、現行ルールと矛盾する例は `superseded` として扱い、送信用の基準にしない。
- 内容をそのまま流用するのではなく、
  - 書き出しの温度感
  - 依頼の数
  - 既出情報の受け方
  - 次アクションの置き方
  を合わせる。
- 返信後は `ng-expressions.ja.md` と仕上げ前チェックで再確認する。

## 運用ルール
- 3〜5本で始める。最初から増やしすぎない。
- 実案件で「ほぼそのまま送れた」「手修正が少なかった」返信だけ追加する。
- 1回限りの好みや偶然うまくいった文は入れない。
- 納品物本文には使わず、トークルーム返信だけで使う。
- 旧ルールと競合する例を見つけた場合は、削除より先に `superseded` として参照資格を落とす。

## 初期セット
- `01_bugfix_non_engineer_first-contact.ja.md`
- `02_bugfix_repeat-request_same-area.ja.md`
- `03_bugfix_scope-judge_separate-cause.ja.md`
- `04_bugfix_boundary_clear-symptom-first.ja.md`
- `05_handoff_private_quote-gate.ja.md`
- `06_purchased-closed_scope-continue.ja.md`
- `07_handoff_explanation_non_engineer.ja.md`
- `08_bugfix_scope-buyer-words.ja.md`
- `09_bugfix_setting-vs-code_self-fix-intent.ja.md`
- `10_delivered_value-doubt_light-fix.ja.md`
- `11_boundary_unknown-spec-vs-bug.ja.md`
- `12_boundary_refuse-external-share-and-push.ja.md`
- `13_bugfix_structured-intake_ack-then-ask-delta.ja.md`
- `14_quote-sent_refuse-zoom_with-anxiety.ja.md`
- `15_repeat-project_discount-firm-but-natural.ja.md`
- `16_handoff_followup_deeper-memo-paid-supplement.ja.md`
- `17_purchased_secret-value_and-share-split.ja.md`
- `18_purchased_deploy-anxiety_no-direct-deploy_but-guide.ja.md`
- `19_prequote_success-rate-fear_no-guarantee_but_clear_value.ja.md`
- `20_closed_repeat_with-refund-anxiety_scope-first.ja.md`
- `21_boundary_bugfix-vs-handoff_confused-route_bugfix-first.ja.md`
- `22_phase-contract-edge_next-path.ja.md`
- `23_closed-materials-work-boundary.ja.md`
- `24_transaction-model-gap_edges.ja.md`
- `25_pre-shelf-regression-boundaries.ja.md`
- `26_prequote-concrete-symptom-pickup.ja.md`
- `27_closed-general-check-method.ja.md`
- `28_prequote-price-scope-boundaries.ja.md`
- `29_price-guarantee-refund-risk.ja.md`
- `30_normal-boundary-routing.ja.md`
- `31_normal-scope-support.ja.md`
- `32_boundary-mixed-routing.ja.md`
- `33_boundary-transfer.ja.md`
- `34_post-chg068-near-miss.ja.md`
- `35_response-weight-mismatch.ja.md`
- `36_conversation-flow-naturalness.ja.md`
- `37_promise-consistency.ja.md`
- `38_agency-alignment.ja.md`
- `39_negative-frame-emotion-bridge.ja.md`
- `40_block-rhythm-flow.ja.md`
- `41_topic-label-distance.ja.md`
- `42_commitment-strength-calibration.ja.md`
- `43_buyer-burden-material-selection.ja.md`
- `44_quote-sent-purchase-cta-material-order.ja.md`
- `45_closed-relation-check-scope-clarity.ja.md`
- `46_context-anchor-granularity.ja.md`

## Gold 26-33 family index

Gold はテンプレートではなく、近い判断順序を思い出すための anchor として使う。
26 以降は件数が増えてきたため、個別ファイル名ではなく family で探す。

| family | gold | 使う場面 | 使わない場面 |
| --- | --- | --- | --- |
| concrete_prequote | 26 | 具体症状がある prequote で、buyer の語を拾ってから価格・購入導線へ進む時 | 価格・保証・返金・復旧時間など、主質問がサービス仕様の時 |
| closed_general_check | 27 | closed 後に一般的な確認方法だけを聞かれ、実作業に入らない時 | コード修正指示・成果物返却・返金要求が混ざる時 |
| price_scope_boundary | 28, 29 | 値引き、保証、返金、復旧時間、複数症状、追加料金不安など、料金・範囲の主質問に答える時 | 通常の症状受けだけで足りる時 |
| technical_boundary | 30, 31 | 非Stripe決済、ブラウザ依存、本番/preview差、秘密情報、外部共有、テスト追加など、技術境界を切る時 | provider 側の管理画面操作や外部共有を受ける時 |
| boundary_transfer | 32, 33, 34 | 仕様/不具合境界、quote_sent 語彙、closed 後の別件・割引・新規導線、怒り気味 buyer、複数質問混在への回収を扱う時 | phase が単純な通常 prequote の時 |
| response_weight | 35 | 安全境界は守れているが、buyer の文量・温度・質問数に対して返信が重い時。短くても安全な例と、重くても必要な例を比べる時 | 返金/保証/closed/秘密情報などの必要境界を削る理由にする時 |
| conversation_flow | 36 | 内容は正しいが、短文断定の連続・確認語密集・次アクション不足で会話の流れが切れている時 | 価格・scope・phase・secret・payment route を弱めて自然化する理由にする時 |
| promise_consistency | 37 | 先に置いた留保・不可・条件付き回答を、後段の成果物・納期・料金・次アクションが上書きして見える時 | 固定価格・対応可能範囲・修正済みファイル成果物を弱める理由にする時 |
| agency_alignment | 38 | `依頼できますか` `見てもらえますか` `支払い後に送ればいいですか` などで、相談先・対応主体・許可の向きがズレそうな時 | `相談できます` `確認できます` `大丈夫です` を blanket NG にする理由にする時 |
| negative_frame | 39 | `責めたいわけではない` `返金してほしい` などのネガティブ/圧力語を、実務目的・作業可否・費用扱いへ要約する時 | 謝罪・過失認定・無料対応・返金保証を強める理由にする時 |
| block_rhythm_flow | 40 | 処理文・安全説明・条件文が同じリズムで並び、契約説明の塊に見える時。`fix_recommended` / `acceptable_as_is` / `unsafe_to_smooth` を分けたい時 | 句点数・段落数を機械判定したり、高リスク境界を短文化のために削る時 |
| topic_label_distance | 41 | `〜の件ですね` が buyer の困りごとを遠い案件ラベルにしている時。自然な topic organizer と距離が出る表現を分けたい時 | `〜の件` を blanket NG にする理由にする時 |
| commitment_strength | 42 | phase・受領証拠・原因特定度に対して、約束の強さを合わせたい時。購入前/購入後/closed 後で promise level を分けたい時 | 依頼可否・固定価格・必要な次アクションまで弱める理由にする時 |
| buyer_burden_material_selection | 43 | コードに詳しくない、AI生成コード、どのファイルを送ればよいか分からない buyer に、材料選別負担を戻しすぎない時 | 毎回コード一式ZIPを hard rule にしたり、購入前コード確認へ滑る理由にする時 |
| quote_sent_purchase_cta_material_order | 44 | 見積り提案後や購入前に、buyer が `直りそうなら購入` `支払い前に少し見てほしい` と迷っている時。購入前境界、対応範囲、CTA、購入後材料案内の順序を合わせる時 | `ご購入ください` の blanket NG や、支払い前作業不可を消す理由にする時 |
| post_completion_followup_scope_clarity | 45 | closed 後に前回修正との関係確認を受ける時。ログ/スクショで何を確認するのか、実作業・成果物返却・費用相談とどう分けるかを明確にしたい時 | closed 後の実作業、無料対応、返金、旧トークルーム継続を約束する理由にする時 |
| context_anchor_granularity | 46 | 長い buyer 文で、冒頭が全文要約や分類ラベルのように見える時。主質問への直答と、必要な context anchor の粒度を合わせたい時 | 状況をまったく拾わない雑な直答にする理由や、`状態でも` `症状として` の blanket NG にする時 |

### 抽出して validator / renderer へ戻す候補

- Gold 26: `内容ありがとうございます -> この不具合なら15,000円 -> どこで止まっているか確認` の旧三点セット検出。
- Gold 29: 復旧時間・保証期間・返金/キャンセル質問で、通常の不具合受付テンプレに流さない direct answer。
- Gold 30/31: 非Stripe名が出た時に、決済サービス全体ではなく `Next.js側のWebhook/API受信処理` へ scope を閉じる。
- Gold 32/33: `quote_sent` / `closed` の phase 語彙と導線。`quote_sent` で現在の作業場所として `トークルーム内` と書く事故や、closed 後の旧トークルーム継続を validator 候補にする。入金完了後の未来手順としての `トークルームで共有` は blanket NG にしない。
- Gold 34: 複合質問で、返金・料金・Slack・秘密情報・closed 後導線など事故りやすい明示質問を落とさない。
- Gold 35: `response_weight_mismatch` は validator 化せず、短くても安全 / 重くても必要の対比 anchor として使う。
- Gold 36: `conversation_flow_naturalness` は hard validator 化せず、固定価格・scope・phase を保ったまま、短文断定の連続、確認語密集、次アクション不足を最小差分で整える anchor として使う。
- Gold 37: `promise_consistency` は hard validator 化せず、成功保証・原因未確定・購入前着手・closed 後作業などの留保と、後段の成果物・作業 promise の約束レベルを分ける anchor として使う。
- Gold 38: `agency_alignment` は hard validator 化せず、buyer の主質問の動詞に合わせて、依頼先・対応主体・材料共有の手順がズレない表現へ戻す anchor として使う。
- Gold 39: `negative_frame_non_echo` は hard validator 化せず、否定されたネガティブ意図や圧力語を、前回修正との関係・作業可否・費用や返金の扱いへ要約する anchor として使う。
- Gold 40: `block_rhythm_flow` は hard validator 化せず、段落の塊感を `fix_recommended` / `acceptable_as_is` / `unsafe_to_smooth` に分ける anchor として使う。自然化してよいのは同じ役割・同じ約束レベルの文だけ。
- Gold 41: `topic_label_distance` は hard validator 化せず、buyer の困りごとを受付票のような案件ラベルにしていないかを見る anchor として使う。`〜の件` の blanket NG にはしない。
- Gold 42: `commitment_strength_calibration` は hard validator 化せず、phase・証拠量・原因特定度に合わせて promise level を調整する anchor として使う。依頼可否や固定価格まで弱めない。
- Gold 43: `material_selection_burden` は hard validator 化せず、buyer が判断できない領域を buyer に戻しすぎていないかを見る anchor として使う。safe default input と secret 除外をセットにし、prequote でコード確認へ滑らない。
- Gold 44: `purchase_cta_strength_calibration` / `purchase_before_materials_order` は hard validator 化せず、buyer がまだ購入判断中の時に、購入後材料案内が買う前提として先行していないかを見る anchor として使う。
- Gold 45: `post_completion_followup_scope_clarity` は hard validator 化せず、closed 後の関係確認が「何を見てくれるのか」と「どこから実作業なのか」を buyer に見せる anchor として使う。closed 後作業 promise が出た場合は既存 hard guard で扱う。
- Gold 46: `context_anchor_granularity` は hard validator 化せず、冒頭で buyer 文の背景・症状・不安・作成経緯を全文要約していないかを見る anchor として使う。直答を先に置き、scope に必要な anchor だけ残す。状況を拾わない雑な直答や、`状態でも` `症状として` の blanket NG にはしない。
