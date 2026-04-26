# 2026-04-26 #RE 棚卸し bugfix-12〜17

## 結論

今回の棚卸しは `reply-only`。
納品物本文や service facts へは戻さない。

現行骨格は維持する。
batch-12〜17 の r0 で出た崩れは、単なるもぐらたたきではなく、危ない境界を意図的に当てた結果として見えている。
r1/r2 で採用可まで戻せているため、戻す対象は「同じ条件で再発した事故」だけに絞る。

## validator に戻すもの

### V1. 丸引用 + `とのことでした`

- 判定: validator 候補、優先度高
- 分類: `reply-only`
- failure_label: `template_quote_drift / ai_tone / nonanswer`
- evidence: batch-12 B07、batch-13 B07、batch-15 B01、batch-16 B03、batch-17 B02/B05
- 症状: buyer 文を長く引用して `とのことでした` で受け、主質問に答える前に基本テンプレートへ流れる
- 危険: 読んでいるようで読んでいない印象が出る。特に `1件で対応できますか` `値下げできますか` `対処法だけ教えて` のような直答質問で事故る
- 戻し先: validator + renderer wording guard
- 実装候補: reply に `とのことでした` があり、かつ buyer 文からの長い連続引用または `...` がある場合 warn
- renderer 方針: buyer 文の長い復唱ではなく、短い要約 + 主質問への直答にする

### V2. delivered generic fallback

- 判定: validator 候補、優先度高
- 分類: `reply-only`
- failure_label: `delivered_generic_fallback / phase_answer_gap / state_regression`
- evidence: batch-11、14、16、17 で delivered の承諾/差し戻し/将来サポートに汎用文が再発
- 症状: `まず前回対応の続きとして扱える話かを確認します` などで、承諾前/承諾後/closed 後の導線に答えない
- 危険: buyer が承諾してよいか、差し戻してよいか、承諾後にどうなるか分からない
- 戻し先: validator + delivered gold
- 実装候補: delivered で raw に `承諾` `差し戻し` `本番で確認` `承諾後` `月1回` があり、reply が承諾前/承諾後/closed 後の導線を含まない場合 warn

### V3. 購入前の解決策/対処法要求

- 判定: validator 候補
- 分類: `reply-only`
- failure_label: `actual_work_before_payment / nonanswer`
- evidence: batch-14 B03、batch-17 B05
- 症状: `対処法だけ教えて` `直し方だけ教えて` に対して、購入前に具体手順を渡すか、逆に可否へ答えず基本テンプレートへ流れる
- 危険: 有償作業の中身を購入前に渡す、または buyer の主質問を落とす
- 戻し先: validator + gold
- 実装候補: prequote/quote_sent で raw に `対処法` `直し方` `教えて` `自分で直せる` があり、reply に `購入前` と `具体的な修正手順/直し方までは` 相当がない場合 warn

### V4. cancel_word_misroute

- 判定: validator 候補、優先度高
- 分類: `reply-only`
- failure_label: `cancel_word_misroute / state_regression`
- evidence: batch-16 B06 で `定期課金のキャンセルフロー` を取引キャンセルとして処理
- 症状: Stripe/Customer Portal/subscription/cancelUrl/customer.subscription の技術文脈の `キャンセル` を、ココナラ取引キャンセル/返金として扱う
- 危険: buyer の技術質問へまったく違う取引回答を返す
- 戻し先: validator + gold
- 実装候補: raw に `Customer Portal` `subscription` `サブスク` `cancelUrl` `customer.subscription` `解約フロー` があり、reply に `返金` `途中キャンセル` `取引キャンセル` が出る場合 warn

### V5. quote_sent の追加料金/キャンセル不安

- 判定: validator 候補、優先度高
- 分類: `reply-only`
- failure_label: `completion_gate_gap / phase_answer_gap / transaction_model_gap / nonanswer`
- evidence: batch-17 B01
- 症状: `別原因が複数ならキャンセルできるか` `金額が増えるか` `支払いボタンを押すか迷う` に対して、返金保証やサービス説明へ逃げる
- 危険: quote_sent の購入判断に必要な情報が見えない。15,000円内で完了不能な時に、未完成のまま正式納品へ進むのか、追加費用になるのか、止められるのかが曖昧になる
- 戻し先: validator + gold + reviewer_prompt
- 実装候補: quote_sent で raw に `追加料金` `別原因` `キャンセル` `支払いボタン` `迷って` があり、reply に `勝手に金額が増えない` `追加作業前に相談` `15,000円内で修正完了まで進められない場合は止めて説明` `キャンセルは作業状況とココナラ手続きに沿う` がない場合 warn

内部判断モデル:

- 15,000円で修正完了まで進める前提で受ける
- 別原因・別フロー・重い修正が見つかったら、勝手に追加作業へ進まない
- 15,000円内で完了できないと分かったら、そこで止めて説明する
- buyer が追加費用を望まないなら、未完成のまま正式納品へ押し切らない
- キャンセル/返金は断定せず、作業状況とココナラ上の手続きに沿って相談する
- 軽微で吸収できるなら、内部判断で基本料金内対応にする余地は残す

外向け返信では、この6点を全部説明しない。
`15,000円の範囲で進める前提`、`超える場合は止めて説明`、`勝手に追加作業へ進まない` を中心に圧縮する。

### V6. prequote の修正/整理どちらが先か

- 判定: validator 候補、優先度中
- 分類: `reply-only`
- failure_label: `fix_vs_structure_first / nonanswer / transaction_model_gap`
- evidence: batch-15 B03、batch-18 B08
- 症状: buyer が `修正と整理、どちらを先に頼むべきか` を聞いているのに、`この不具合なら15,000円で進められます` の基本テンプレートへ戻る
- 危険: 主質問に答えないまま購入導線へ進む。逆に `整理` に引っ張られて、非公開サービス名・25,000円導線が外向けに漏れる可能性もある
- 戻し先: validator + gold + renderer_minimal
- 実装候補: prequote で raw に `修正` と `整理/コード全体/把握/リファクタ` があり、`どっち/どちら/先に/先か/まず` を含む場合、reply に `まず不具合修正から見る` と `コード全体の整理は範囲と分ける` がない場合 warn
- renderer 方針: `まず直したい不具合から見るのが近い` を直答し、購入後は修正に必要な範囲だけ確認する。大きな整理や別処理修正が必要なら止めて説明し、勝手に追加作業へ進まない

## gold に残すもの

今回、新規 gold として残す優先度が高いのは次の5型。

- `quote_sent` 追加料金/キャンセル不安
- 技術的な `キャンセル` 語を含む prequote の1件可否
- 購入前の対処法要求への拒否 + 見立て導線
- delivered の承諾後不安
- prequote の `修正と整理、どちらを先に頼むべきか`

保存先:

- `docs/reply-quality/gold-replies/25_pre-shelf-regression-boundaries.ja.md`

gold 化しないが、近い将来の候補として残すもの:

- NDA 要求への、個別NDA安請け合いなし + 最小共有 + 秘密値禁止
- 値下げ要求への、15,000円固定 + scope 説明
- Zoom/Google Meet 直接説明拒否 + トークルーム内テキスト代替
- 外部決済拒否
- 秘密値のコード直書き拒否
- seller 側の報告時刻遅延 complaint
- 性能問題の scope 判定保留

これらは有効だが、全部を一度に gold へ増やすと参照ノイズが増える。
今回の gold は、batch-17 で全 state が r1/r2 安定した4型に絞る。

## reviewer_prompt にだけ足すもの

### transaction_model_gap

- writer rule にはしない
- reviewer レンズとして維持
- deterministic な事故だけ validator 化する
- 例: 見積り前原因調査、closed 後コード修正助言、作業前に費用導線なし

### 怒り気味 buyer の慰撫語

- validator ではなく gold/reviewer_prompt 向き
- `放置しません` `前回の修正で解決しているべき` `無料で対応します` は避ける
- 安定型は `納得できないとのこと、確認しました` くらいの事実受け
- case ごとの温度調整は case_fix/preference 止まり

### one_breath_failure

- 監査観点として維持
- `可否・価格・方針` を不自然に分断した時だけ拾う
- 機械的にすべて結合する rule にはしない

### 時刻コミット

- validator 候補は限定的
- 未来時刻でない、相手文の時刻より過去、情報未受領なのに確認結果時刻を置く場合だけ warn 候補
- 文体としての時刻の硬さは preference

## case_fix / preference で終わらせるもの

- `signingSecret の箇所で使っている前提は確認しました` のような軽い誤読防止
- `動いているとのこと` を `軽く見た範囲では大丈夫そう` に弱める調整
- `必要情報がそろい次第` の自然化
- `件の件`、`本日XX:XX` の硬さ
- `同じ原因として見られる内容か` を `今回の修正とつながる内容か` にする語感調整
- `必要なら` の多用

これらは自然さには効くが、骨格や validator を増やす優先対象ではない。

## reject / 今は戻さないもの

- `transaction_model_gap` を writer rule として常時本文へ入れること
- batch-12〜17 の全採用文をすべて gold 化すること
- renderer/scenario を広く増殖させること
- closed 後の怒り対応を、重い謝罪テンプレへ固定すること
- 外部監査の文案を、要約・選別なしに rule へ直投入すること

## 次の進め方

1. まず Gold 25 とこの棚卸しメモで運用する。
2. 次に validator 実装するなら、順番は V1 -> V2 -> V4 -> V3 -> V5。
3. validator 実装時は、既存 renderer の文面を大きく変えず、warn で止めるところから始める。
4. 実装後は `check-coconala-reply-role-suites.py --save-report` と targeted fixture で確認する。
5. その後に #RE を再開する。

## 2026-04-26 反映状況

- V1 `template_quote_drift`: prequote validator に追加。prequote renderer の長い fallback 復唱は `内容ありがとうございます。` へ最小変更
- V2 `delivered_generic_fallback`: delivered validator を強化。`承諾後` `月1回` などの具体 follow-up で汎用 fallback に戻らないよう、delivered renderer に承諾後不安 / 月次確認要求の最小分岐を追加
- V3 `購入前の解決策/対処法要求`: prequote validator と最小 renderer 対応を追加。`対処法だけ` `どうやって直す` は、購入前の見立て / 購入後の具体修正へ切り分ける
- V4 `cancel_word_misroute`: prequote / purchased validator に追加。purchased renderer では技術的な `キャンセルフロー` を取引キャンセルへ誤分類しない最小分岐を追加
- V5 `quote_sent の追加料金/キャンセル不安`: ユーザー監査で `completion_gate_gap` として格上げ。15,000円内で完了不能な時に未完成納品へ進めないこと、追加作業前に止めること、キャンセル扱いは作業状況とココナラ手続きに沿って相談することを renderer / validator / gold に反映
- V5 追加調整: `購入前なので、迷いがあれば支払いボタンを押さなくて大丈夫` は buyer を足踏みさせるため標準文から外す。`追加対応として進めるか` も seller 側の都合語として避け、`15,000円の範囲で進める前提 / 超えるなら止めて説明 / 勝手に追加作業へ進まない / キャンセル扱いは手続きに沿って相談` に圧縮
- V6 `prequote の修正/整理どちらが先か`: batch-18 B08 で旧テンプレート回帰を確認。`fix_vs_structure_first` として taxonomy / Gold 25 / prequote renderer / validator / active fixture に反映
- V7 `surface_overexposure`: batch-19 と Pro 監査で、安全条件が正しくても本文に並びすぎると、buyer には監査項目・規約説明・契約説明のように見えることを確認。`transaction_model_gap` / `completion_gate_gap` は内部 lens として残し、外向け本文は `直答 1〜2文 -> 必要な境界 1〜2文 -> 次アクション 1文` に圧縮する。まずは writer-brief / compression-rules / gold / batch case_fix へ反映し、renderer / validator の大きな変更は次の #RE で再発を見てから判断する

確認:
- targeted fixture: `ops/tests/quality-cases/active/pre-shelf-validator-bugfix12-17.yaml` OK
- `python3 scripts/check-coconala-reply-role-suites.py --save-report` OK
- `./scripts/os-check.sh` OK

## 判断メモ

batch-17 r0 で B03 と B07 がそのまま通ったのは重要。
GitHub直接push拒否と closed 見積り前原因確認は、現行骨格が効き始めている。
一方で、丸引用、delivered 汎用 fallback、購入前対処法要求は r0 でまだ落ちる。

したがって今は、返信システムを広く作り替える段階ではない。
高リスクの再発だけを validator/gold に戻し、骨格は維持する。
