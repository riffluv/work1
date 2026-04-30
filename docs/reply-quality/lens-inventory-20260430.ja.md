# 主要監査レンズ棚卸し 2026-04-30

## 位置づけ

このメモは、ココナラ返信OSの `#RE` / `#BR` / human audit で使う主要監査レンズを、現時点の正式度で整理するための正本メモ。

目的は、レンズを増やすことではなく、どの違和感をどこで見るかを分け、返信OSの骨格を壊さずに改善を戻すこと。

## 基本方針

- hard fail は deterministic な事故に限る。
- 日本語自然化系は原則 soft lens として扱う。
- `相談できます` / `確認できます` / `大丈夫です` / `はい` / `まずは` / 句点「。」は blanket NG にしない。
- 自然化のために、価格・scope・phase・secret・public/private・payment route・作業可否を変えない。
- 単発の好みは rule 化しない。再発性、実務ノイズ、既存ルールとの整合を見て戻す。

## Soft lens の適用停止条件

soft lens は、文面を自然にするための補助であり、契約・料金・phase・secret・公開状態を上書きしない。

各 soft lens を使う時は、必ず次を確認する。

- 修正案によって `15,000円`、不具合1件、購入後開始、secret 値不要、外部共有不可、closed 後の実作業境界が弱まらないか。
- 単語禁止として誤用されないか。
- buyer が聞いている論点を消していないか。
- 返金、無料対応、今日中対応、成功保証、修正済みファイル返却などの promise が強く読まれないか。
- 高リスク場面では、少し硬くても `acceptable_as_is` として残した方が安全ではないか。

監査では soft lens の結果を次の粒度で分ける。

- `hard_by_underlying_guard`: soft lens 由来の違和感に見えるが、実際には public/private、phase、secret、成功保証、closed 後作業 promise など deterministic guard が壊れている。
- `fix_recommended`: hard fail ではないが、実務上の誤読・AI感・buyer の停滞が出やすく、最小修正した方がよい。
- `acceptable_as_is`: より自然な言い換えはあるが、境界を分けるための硬さとして許容できる。
- `observe_only`: まだ再発性や副作用が見えないため、今回の修正に戻さず観察だけ残す。
- `overfire_risk`: 修正すると、必要な拒否、主質問、価格、scope、phase、secret、支払い導線のどれかを弱める可能性がある。

## 正式扱いに近い主力レンズ

| lens | 役割 | 現在の扱い | 主な戻し先 |
| --- | --- | --- | --- |
| `promise_consistency` | 前段の留保・不可・条件付き回答を、後段の成果物・納期・料金・次アクションが上書きして見えないかを見る | 正式主力 soft lens | reviewer prompt / Gold 37 / 専用メモ |
| `conversation_flow_naturalness` | 短い受け止め、主質問への直答、条件・理由、次アクションが自然につながっているかを見る | 正式主力 soft lens | reviewer prompt / Gold 36 / `japanese-chat-natural-ja` |
| `jp_business_native_naturalness` | 日本の実務チャットとして、内容が正しいだけでなく人間の担当者が書いたように読めるかを見る | 上位 umbrella soft lens | reviewer prompt / `japanese-chat-natural-ja` / `ng-expressions` |
| `agency_alignment` | 誰が何をするのか、誰に向けて許可・依頼・案内しているのかが buyer の主質問とズレていないかを見る | 正式 named soft lens | reviewer prompt / Gold 38 / skills |

### `promise_consistency`

代表例:

```text
必ず直せるとはお約束できません。
ただ、原因確認から修正済みファイルの返却まで進められます。
```

問題は「修正済みファイル」という語そのものではなく、成功保証を否定した直後に、未確認の成果物返却を無条件 promise に見せる接続。

望ましい方向:

```text
まず原因確認から進められます。
修正できる箇所が特定できた場合は、修正済みファイルをお返しします。
```

現在は hard validator 化しない。明確な成功保証、phase drift、secret 値要求、closed 後作業 promise など deterministic な事故に接続した場合だけ必須修正。

### `conversation_flow_naturalness`

見るもの:

- 短文断定が続き、マニュアル文に見えないか
- `確認します` / `確認結果` / `お返しします` が近距離で密集していないか
- buyer 固有の情報を1点拾えているか
- 受け止め、主回答、条件、次アクションがつながっているか
- buyer の文量・温度・質問数に対して、返信が契約説明化しすぎていないか

見ないもの:

- 句点の多さだけ
- やや硬いが意味と境界が明確な文
- 自然化すると価格・scope・phase が揺れそうな好み差

#### `block_rhythm_flow`

`conversation_flow_naturalness` 配下の named subtype として扱う。

見るものは、段落数や句点数ではなく、処理文・安全説明・条件文が同じリズムで並び、buyer にはチェックリストや契約説明のように見えていないか。

判定は3つに分ける。

- `fix_recommended`: buyer の質問量に対して返信が重く、主回答・条件・次アクションの順序調整で自然にできる。
- `acceptable_as_is`: やや硬いが、高リスク場面で境界を分けた方が誤読が少ない。
- `unsafe_to_smooth`: 滑らかにつなぐと、保証・返金・無料対応・closed 後作業・支払い導線などの promise が強く読まれる。

#### `safe_connection`

`block_rhythm_flow` の補助観点であり、自然化を適用する前の gate として扱う。

自然につなげてよいのは、同じ役割・同じ約束レベルの文だけ。

つないでよい例:

```text
届いている内容でこちらから確認に入ります。いま追加で準備いただくものはありません。
```

つなぐと危険な例:

```text
必ず直るとはお約束できません。ただ、ご購入後に修正済みファイルをお返しします。
```

後者は、`修正できる箇所が特定できた場合は` の条件を残す。

gate として止める例:

- 成功保証否定と成果物返却を、条件なしで一息につなげる。
- closed 後の関係確認と修正作業開始を、同じ流れに見せる。
- 返金未定と無料対応の可能性を、費用相談なしでつなげる。
- 支払い前不可と購入後材料共有をつなげる時に、購入前確認へ読める表現になる。

迷う場合は、自然な一文にまとめるより、約束レベルごとに分ける。

### `jp_business_native_naturalness`

上位 umbrella として扱う。

配下に置く主な観点:

- 二重受領: `確認しました` の直後に `はい、確認できています`
- 機械的な `はい、`
- 内部処理語: `確認材料`、`進め方になります`
- 近接反復: `確認します / 確認できます / 確認結果`
- 文面は正しいが担当者の実務チャットとして浮く表現

hard fail ではない。意味を変えない最小修正だけを提案する。

### `agency_alignment`

代表例:

```text
この状態でも15,000円で依頼できますか？
```

に対して、

```text
15,000円で相談できます。
```

だけだと、文法上は通るが、相談先・対応主体が薄くなりやすい。

標準:

- `依頼できますか` -> `ご依頼いただけます` / `対応できます`
- `お願いできますか` -> `お受けできます` / `対応できます`
- `見てもらえますか` -> `こちらで確認します` / `対応できます`
- `相談して大丈夫ですか` -> `ご相談いただけます`

注意:

- `相談できます` は blanket NG にしない。
- `確認できます` / `進められます` / `大丈夫です` も blanket NG にしない。
- 取引判断、料金、作業開始、材料共有、closed 後導線に関わる箇所で主体がズレる時だけ強く見る。

## 正式寄りの補助レンズ

| lens | 役割 | 現在の扱い | 主な戻し先 |
| --- | --- | --- | --- |
| `permission_benefit_alignment` | `大丈夫です` などの許可・安心表現が、buyer の負担軽減ではなく seller の許可調になっていないかを見る | named soft lens / 補助主力 | reviewer prompt / skills |
| `unnecessary_refusal_frame` | 協力的な buyer に、必要以上に拒否・否定から入って冷たくなっていないかを見る | named soft lens / 補助主力 | reviewer prompt / gold 候補 |
| `negative_frame_non_echo` | `責めたいわけではない` `苦情ではない` `返金してほしい` などのネガティブ/圧力語をそのまま復唱せず、実務目的へ要約できているかを見る | named soft lens / 補助主力 | reviewer prompt / Gold 39 / skills |

### `permission_benefit_alignment`

自然な用法:

```text
値そのものは送らなくて大丈夫です。
```

buyer の負担を実際に下げているため自然。

注意する用法:

```text
ログや関連コードは、お支払い完了後で大丈夫です。
```

支払い・購入・材料送付の導線では、seller が buyer の行動を許可しているように見えることがある。

望ましい方向:

```text
ログや関連コードは、お支払い完了後にトークルームで共有してください。
共有いただければ、そこから確認に入ります。
```

### `unnecessary_refusal_frame`

注意する用法:

```text
支払い前にスクショを送っていただいて、こちらで確認を先に始める形ではありません。
```

buyer が単に共有タイミングを確認しているだけなら、拒否先行で冷たく見える場合がある。

望ましい方向:

```text
スクショやログは、お支払い完了後にトークルームで共有いただければ進められます。
今の段階で先に送っていただく必要はありません。
```

注意:

- 支払い前作業、secret 値、外部共有、直接 push、本番反映、closed 後作業などの不可表明は消さない。
- 必要な境界を柔らかくするためのレンズではなく、不要な拒否フレームを手順案内へ戻すためのレンズ。

### `negative_frame_non_echo`

注意する用法:

```text
責めたいわけではなく、前回の修正との関係だけ確認したいということですね。
苦情とのことですね。
今日中に無料対応できるか、返金になるかは断定できません。
```

問題は、buyer が否定したネガティブ意図や、強く押してきた要求語をこちらが本文内で再提示し、対立感・防御感・責任認定リスクを強めること。

望ましい方向:

```text
似たStripeエラーが出ている件で、前回の修正との関係を確認したいということですね。
この時点では、前回の修正との関係、今日中の作業可否、費用や返金の扱いは断定できません。
```

下位観点:

- `responsibility_admission_guard`: closed 後や未確認状態で、こちらの過失・前回修正ミス・返金/無料対応を認めたように読めないかを見る。
- `pressure_word_summarization`: `今日中に無料で` `返金してほしい` `低評価前に` のような圧力語をそのまま復唱せず、`作業可否` `費用や返金の扱い` `前回修正との関係` へ要約する。
- `emotion_to_action_bridge`: 不安・不満・急ぎを受けたあと、共感や否定で止まらず、確認行動と次アクションへ自然につなげる。

注意:

- `ご不便をおかけしています` は blanket NG にしない。ただし closed 後の前回ミス疑いなど、原因未確認の場面では `ご不便な状況かと思います` `まずは状況を確認します` を優先する。
- 返金・無料・今日中対応の論点自体は消さない。要求語を実務判断へ要約するだけで、buyer の主質問を落とさない。
- hard fail ではない。責任認定、返金/無料保証、今日中保証、closed 後作業 promise に接続した場合だけ、実際に壊れた boundary 名で必須修正にする。

## 観察中の補助観点

| 観点 | 役割 | 現在の扱い |
| --- | --- | --- |
| `conditional_scope_clarity` | 同一原因なら範囲内、別原因なら相談、修正可能時だけ返却などの条件を明瞭に出せているか | `promise_consistency` 近接の補助観点 |
| `ack_to_answer_bridge` | 状況受けから主回答へ急に飛ばず、短い橋を置けているか | `conversation_flow_naturalness` 配下の観察項目 |
| `responsibility_admission_guard` | closed 後や未確認状態で、こちらの過失・前回修正ミス・返金/無料対応を認めたように読めないか | `negative_frame_non_echo` 配下の観察項目 |
| `pressure_word_summarization` | `今日中に無料で` `返金してほしい` などの圧力語を、作業可否・費用や返金の扱いへ要約できているか | `negative_frame_non_echo` 配下の観察項目 |
| `block_rhythm_flow` | 処理文・安全説明・条件文が同じリズムで並び、契約説明化していないか | `conversation_flow_naturalness` 配下の named subtype |
| `safe_connection` | 会話の流れを作る時に、同じ役割・同じ約束レベルの文だけをつなげているか | 自然化適用前の gate / `block_rhythm_flow` の補助観点 |
| `response_weight_mismatch` | buyer の文量・温度・質問数に対して、返信が重すぎる/軽すぎる/拒否が先に出すぎていないか | formal soft lens 候補 / Gold 35 配下 |
| `commitment_strength_calibration` | phase・受領証拠・原因特定度に対して、約束の強さが合っているか | formal soft lens 候補 / `promise_consistency` 近接 |
| `topic_label_distance` / `issue_proximity` | buyer の困りごとを受付票のような案件ラベルにせず、直接やり取りの距離で受けられているか | `case_label_distance` の上位候補 / observation |
| `buyer_burden_alignment` | buyer に不要な判断・材料選別を押し戻していないか | observation。secret / 過剰材料要求に接続した時だけ hard guard 側で見る |
| `answer_order_calibration` | buyer が最初に聞いている問いへ、最初に必要な粒度で答えているか | observation / `response_weight_mismatch` 近接 |
| voice ownership | FAQ や窓口案内ではなく、この場の担当者が返している文に見えるか | 観察中。強めすぎると過約束に接続するため soft lens |
| certainty calibration | 情報量に応じて、断定・留保・条件付き回答の強さが合っているか | `commitment_strength_calibration` へ統合候補 |
| explicit symptom coverage | buyer が書いた明示症状・材料・質問を片方だけ落としていないか | case_fix / gold 候補 |
| next action clarity | buyer が次に何をすればよいかが見えるか | phase / conversation flow の補助 |
| fixed time sanity | `本日HH:MMまで` が送信時刻と矛盾しないか | 運用チェック |

これらは現時点で独立レンズ化しすぎない。再発が複数 batch で確認できた場合だけ、named soft lens か既存レンズの subtype として検討する。

### `commitment_strength_calibration`

`promise_consistency` が文中の前後矛盾を見るのに対し、こちらは phase・受領証拠・原因特定度に対して、約束の強さが合っているかを見る。

例:

- prequote / quote_sent: 原因確認、修正完了、修正済みファイル返却を開始済みのように言わない。
- purchased / 原因未特定: 現在見ている箇所、次に返せる見通し、追加で必要な材料を言う。修正完了は約束しない。
- 原因特定後: 修正済みファイル返却や確認手順の promise を出せる。
- closed: このメッセージ上の関係確認と、実作業・費用相談を分ける。

停止条件:

- 成功保証回避のために、15,000円で依頼できる入口まで曖昧にしない。
- 時刻 promise を削るだけで buyer が次に動けなくなる場合は、送信時刻と作業量の整合を見た上で残す。

### `response_weight_mismatch`

buyer の軽い質問に対して、返信が契約説明・拒否説明・内部条件列挙に寄りすぎていないかを見る。

見る例:

- buyer が「購入後はどこまで見てもらえるか」を聞いているだけなのに、支払い前確認不可から入る。
- buyer が「送ってよいか」を聞いているだけなのに、外部共有・secret・直接push・本番反映の禁止をまとめて並べる。
- buyer が短く進捗を聞いているのに、長いルール説明で返す。

停止条件:

- 返金、無料対応、closed 後実作業、secret、外部共有、購入前確認など高リスク境界は、少し重くても残す。
- 軽くするために主質問・価格・scope・次アクションを消さない。

### `topic_label_distance` / `issue_proximity`

`case_label_distance` の上位候補。相手の困りごとを、目の前の会話ではなく受付票の案件ラベルのように扱っていないかを見る。

注意する例:

```text
しばらく問題なかった後に、似たStripeエラーが出ている件ですね。
```

望ましい例:

```text
しばらく問題なかった後に似たStripeエラーが出ているとのこと、承知しました。
```

OK 例:

```text
ログの件、ありがとうございます。届いています。
反映箇所の件であれば、承諾前の確認として短く補足できます。
```

停止条件:

- `〜の件` を blanket NG にしない。
- ログ、請求書、反映箇所など、自然な topic organizer まで消さない。
- buyer の困りごとや不満を遠い案件ラベルにしている時だけ見る。

## 土台ガード

自然化レンズより優先する deterministic guard。

| guard | 見ること |
| --- | --- |
| `public/private boundary` | 通常 live / #RE に `handoff-25000`、25,000円、主要1フロー整理、private CTA が漏れていないか |
| `phase_boundary` | prequote / quote_sent / purchased / delivered / closed を混ぜていないか |
| `secret_safety` | `.env`、APIキー、Webhook secret、DB接続文字列の値を求めていないか |
| `external_work_surface` | GitHub招待、PRコメント、Drive共有、外部作業面、直接 push、本番反映へ寄っていないか |
| `closed_transaction_model` | closed 後に旧トークルーム継続、無料修正、おひねり追加、返金断定へ滑っていないか |
| `service_grounding` | 15,000円、不具合1件、原因確認、修正可能時の修正済みファイル返却が正本とズレていないか |

## 現在の分類

### 正式主力

- `promise_consistency`
- `conversation_flow_naturalness`
- `jp_business_native_naturalness`
- `agency_alignment`

### 補助主力

- `permission_benefit_alignment`
- `unnecessary_refusal_frame`
- `negative_frame_non_echo`

### 観察中

- `conditional_scope_clarity`
- `ack_to_answer_bridge`
- `responsibility_admission_guard`
- `pressure_word_summarization`
- `block_rhythm_flow`
- `safe_connection`
- response_weight calibration
- voice ownership
- certainty calibration
- burden alignment
- explicit symptom coverage
- next action clarity
- fixed time sanity

### hard guard

- public/private
- phase
- secret
- external work surface
- closed transaction
- service grounding

## Pro に見せるなら聞くこと

次に Pro へ聞くなら、この棚卸しを前提に以下を確認する。

1. `正式主力 / 補助主力 / 観察中 / hard guard` の分類は妥当か。
2. `agency_alignment`、`permission_benefit_alignment`、`unnecessary_refusal_frame` は `jp_business_native_naturalness` 配下の named soft lens として十分か、それとも独立レンズにすべきか。
3. `negative_frame_non_echo` を補助主力に置く判断は妥当か。`responsibility_admission_guard` と `pressure_word_summarization` は独立レンズにせず subtype に留めるべきか。
4. `promise_consistency` と `conditional_scope_clarity` の境界は分けるべきか、subtype として統合すべきか。
5. lint 化してよいものと、gold / reviewer prompt / human audit に留めるべきものの線引き。
6. 将来の返信OSコアとして、このレンズ体系は他サービス・他媒体に拡張しやすいか。

## 直近の運用方針

- `negative_frame_non_echo` は bugfix64〜66 で採用圏が続いたため、次に Pro へ投げる価値は出ている。
- ただし今すぐではなく、次に `#RE` を1〜2本回し、`responsibility_admission_guard` / `pressure_word_summarization` が別パターンでも過剰反応しないことを確認してからが理想。
- Pro に投げる場合は、この棚卸しメモ、Gold 39、bugfix64〜66 の r0/r1 差分、監査プロンプトをセットで見せる。
- #RE の候補は `writer_candidate_manual` / #R 相当を維持し、renderer 固有のぶつ切り癖を本丸の品質問題と誤認しない。
