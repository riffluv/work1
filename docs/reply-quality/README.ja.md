# reply-quality（reply-only）

## 目的
- ココナラ返信の品質を、個別添削だけでなく仕組みで安定させる。
- 次の Codex でも、`どう育てるか` を迷わず再開できるようにする。
- 納品物本文ではなく、トークルーム返信の品質改善にだけ使う。

## この階層の役割
- `ng-expressions.ja.md`
  - 再発させたくない悪い言い回し
- `failure-taxonomy.ja.md`
  - 失敗を固定ラベルで戻すための QA分類表
- `guidance-scoping.ja.md`
  - 改善をどの route / state / service にだけ効かせるか決める表
- `forbidden-moves-matrix.ja.md`
  - `forbidden_moves` をどの場面で立てるか決める表
- `adoption-policy.ja.md`
  - 指摘をいつ恒久反映するか決める採用基準
- `prequote-compression-rules.ja.md`
  - 見積り相談で、主質問より先に説明しすぎないための圧縮ルール
- `writer-brief.ja.md`
  - Writer に渡す最小原則。`主質問に先に答える / buyer の語を拾う / 次の行動が分かる言葉で書く` を固定する
- `self-check-core-always-on.ja.md`
  - Reviewer が常時前面に置く 10 項目のコア。詳細は `coconala-reply-self-check.ja.md` へ降りる
- `scorecard.ja.md`
  - 返信品質を 10項目で軽く数値化する採点表
- `multi-turn-check.ja.md`
  - 連続3通で停滞や矛盾を見つけるためのチェック
- `state-schema-minimal-contract.ja.md`
  - multi-turn で最低限持つべき state 項目の契約
  - `routing-playbooks` に `state_contract` を持たせ、route ごとの secondary / promised action の初期値を決める前提も含む
- `service-facts-onboarding-template.ja.md`
  - 新しいサービスへ入れる時に、何を facts 化するかを揃える導入テンプレ
- `service-pack-source-of-truth-policy.ja.md`
  - service-pack の中で、何が公開契約の正本で、何が運用補助 / runtime asset かを分ける共通ポリシー
- `service-pack-runtime-interface.ja.md`
  - 共通 runtime が `facts / boundaries / decision / evidence / routing / state / seeds / tone` をどの順で読むかを固定する最小インターフェース
- `service-pack-v1-fixed-points.ja.md`
  - bugfix / handoff の service-pack で、v1 として固定してよい構成・優先順・未固定事項を短くまとめた基準点
- `productization-foundation-v1-closure.ja.md`
  - service-pack の商品化基盤フェーズを v1 close として閉じ、ここからは実運用モニタリングへ戻るための区切り文書
- `service-page-change-checklist.ja.md`
  - サービスページや内部共有認識を変えた時に、返信OSのどこへ落とすかを10行で確認するチェックリスト
- `external-research-observation-plan-20260425.ja.md`
  - Deep Research の外部調査結果を、`#RE` の観察候補と batch archetype へ変換したメモ。正本 rule ではなく、外部調査レーンからの材料として扱う
- `rehearsal-shelf-20260427-pro-r0-stabilization.ja.md`
  - Pro監査 `返信システム監査4-27.txt` を、r0 初手分岐安定化の実装棚卸しへ変換したメモ。Gold 追加ではなく、renderer / validator / platform contract へ戻す候補を整理する
- `seller-initiated-lane-minimal.ja.md`
  - buyer の文章への返信とは別に、こちら起点の進捗共有・補足・完了報告をどう最小構成で扱うかのメモ
- `self-check-layering-first-pass.ja.md`
  - `self-check` を `L1 / L2 / L3` に棚卸しし、runtime と service-pack を分けるための初期設計メモ
- `self-check-l3-extraction-map.ja.md`
  - `self-check` の L3 を、`facts / boundaries / routing / state / seeds / tone` のどこへ移すかを決める抽出マップ
- `self-check-l3-bugfix-candidates.ja.md`
  - `bugfix-15000` について、`self-check` から先に外へ出す L3 候補を 10〜15 個に具体化した抜き取り一覧
- `self-check-l3-handoff-candidates.ja.md`
  - `handoff-25000` について、`self-check` から先に外へ出す L3 候補を facts / boundaries / routing / state / seeds に分けた抜き取り一覧
- `self-check-l1-minimal-universal.ja.md`
  - サービス固有知識を必要としない `L1: Universal` だけを抜いた最小 runtime check
- `self-check-l2-domain-minimal.ja.md`
  - 受託返信としての進め方だけを抜いた `L2: Domain` の最小チェック
- `self-check-recomposition-plan.ja.md`
  - 現行の巨大 `self-check` を、`L1 / L2 / L3` 前提でどう縮約し、最終的に compatibility layer へ寄せるかの再編方針
- `self-check-section-tag-map.ja.md`
  - 現行 `self-check` の章ごとに `L1 / L2 / L3 / compat-only` を振り、どこから薄くするかの順番を決めるタグ付け表
- `self-check-send-check-integration-map.ja.md`
  - `送信前チェック` を巨大ルール集ではなく `L1 / L2 / L3` の統合入口として再編するための入口設計図
- `self-check-compat-residual-l1-candidates.ja.md`
  - `compat-only residual` に残る項目のうち、実際には `L1: Universal` として戻せる候補を整理した抽出メモ
- `self-check-compat-residual-l2-candidates.ja.md`
  - `compat-only residual` に残る項目のうち、実際には `L2: Domain` として戻せる候補を整理した抽出メモ
- `self-check-compat-residual-final-split.ja.md`
  - `compat-only residual` に残る項目を、最終的に compatibility layer として残すものと、`L3 service-pack` へ再配置するものに二分した仕分け表
- `self-check-compat-residual-exit-criteria.ja.md`
  - `compat-only residual` のうち、最後まで残すものと、次の互換整理で消せるものを分けた出口条件メモ
- `acceptance-gate.ja.md`
  - 送る / 差し戻す / system に戻す の通過条件
- `onboarding-flow.ja.md`
  - 新しいサービスへ返信OSを導入する順番
- `coconala-handoff-prequote-mini-contract.ja.md`
  - `handoff prequote` の proposal first / ZIP optional を固定するサービス別契約
- `gold-replies/`
  - 温度感、情報量、質問数、次アクションの基準になる良い返信例

## 育成ループ（固定）
1. 返信を5件単位で作る
2. Claude などでまとめて監査する
3. 指摘を `QA分類` に落とす
4. 1件ごとに `learning-log` へ学習メモを残す
5. `どこにだけ効かせるか` を scoping で切る
6. `adoption-policy` で即反映か観察保留かを決める
7. `forbidden_moves` で止めるべき崩れかを確認する
8. `Writer / Reviewer / Router / Facts` のどこで壊れたかを切る
9. 再発癖だけを skill / facts / lint に戻す
10. 良い返信を `gold-replies/` に追加する
11. 悪い再発を `ng-expressions.ja.md` に追加する
12. 実案件の微修正も、月次で `good / bad` として戻す

## `#RE` の扱い

- `#RE` は、返信学習用 batch を current rules で更新するショートカット
- デフォルト対象は `bugfix-15000`
- `#RE handoff` のように補足がある時だけ `handoff-25000` を対象にする
- 出力は 1 ファイルだけに絞る
  - `bugfix`: `/home/hr-hm/Project/work/サービスページ/rehearsal/bugfix-15000-返信学習/返信監査_batch-01.md`
  - `handoff`: `/home/hr-hm/Project/work/サービスページ/rehearsal/handoff-25000-返信学習/返信監査_batch-01.md`
- `#RE` では生成本体の再設計を行わない
- 目的は「返信を書くこと」ではなく、「外部監査に回すための batch を current rules で組み直すこと」
- batch 冒頭には短い `batch_manifest` を置く
  - `batch_id / 目的 / 件数 / 選定 / state_mix / risk_axes / 今回の方針`
  - これは生成ルールではなく、何を検査した batch かを後から追うための記録
- `batch_manifest` には必要に応じて `主質問タイプ` と `最初に答えるべき問い` を短く添える
  - これは質問タイプ router ではなく、#RE の検査目的を明確にするための観察ラベル
  - 詳細は `question-type-batch-plan-20260425.ja.md` を参照する
- reviewer の指摘では、必要な場合だけ次の4項目で学習判定を添える
  - `直す単位`: `case_fix / pattern_candidate / rule_return_candidate / preference / reject`
  - `再発根拠`: `なし / 同batch内 / 過去batch同型 / 既存rule未反映疑い`
  - `既存rule hit`: `あり / なし / 不明`
  - `戻し先候補`: `batch / reviewer_prompt / gold / rule / service_facts / validator / none`
- 必須修正は、そのまま rule 化候補とは扱わない
- rule に戻さなかった指摘も、再発しそうなら learning log に `戻さなかった理由` を1行で残す
- 次の重点観察は、buyer が不具合相談に見えて実際には価格・対象可否・納期・保証などのサービス仕様を聞いているケース
  - 汎用不具合テンプレへ逃げず、主質問に最初に答えられているかを見る
  - ただし、質問タイプ router の大規模追加や renderer 刷新はしない
- Deep Research など外部調査の結果は、`external-research-observation-plan-20260425.ja.md` のように観察メモへ分離し、次の `#RE` の stock / archetype / reviewer 観点として使う
  - 外部調査結果をそのまま rule / renderer / validator へ入れない

## 監査の固定 rubric
1. 相手の質問や不安に正面から返しているか
2. 次アクションが明確か
3. 既出情報を聞き直していないか
4. その上で、不自然さや AI 感を減らせているか

## 運用ルール
- 監査コメントは、まず `failure-taxonomy.ja.md` の主ラベル1つで整理する。
- 学習メモは `/home/hr-hm/Project/work/ops/tests/stock/learning-log/` に残す。
- 学習メモのひな形は `learning-log-template.yaml` を使う。
- 学習メモには、採用した修正だけでなく `rule に戻さなかった理由` も短く残す。
- 1件の違和感は、`現象 -> パターン -> 層` の3段で抽象化する。
- 恒久反映の前に、`guidance-scoping.ja.md` で `reply-only / route / state / service` を切る。
- 恒久反映の前に、`adoption-policy.ja.md` で `即反映 / 観察保留 / 却下` を判定する。
- 共通化可否は、`service facts` を入れ替えても再発するかで判断する。
- `gold replies` は最初から増やしすぎない。主要場面ごとに 3〜5 本ずつ増やす。
- `NG表現` は好みではなく、再発した崩れだけを足す。
- 監査では新案を広げすぎず、再発癖の指摘を優先する。
- スコアは `scorecard.ja.md` に分け、self-check に採点項目を足し込まない。
- 実案件の文面をそのまま保存する前に、秘密情報や個人情報が含まれていないか確認する。
- 返信OSの改善は `reply-only` として扱い、納品物本文へは自動波及させない。
- 現行ルールと矛盾する古い `gold replies` や test asset を放置しない。`主質問より先に価格を出す` のような旧パターンは、良い例として残さない。
- overlap 整理では、新ルールを足す前に `正本 / 良い例 / 契約テスト` の3層で競合がないかを先に見る。
- Writer に self-check 全文を読ませない。判定と lint は Reviewer で行い、本文生成は `writer-brief.ja.md` の最小原則へ圧縮する。
- Reviewer も毎回 `self-check` 全文を前面に置かず、まず `self-check-core-always-on.ja.md` を使い、必要時だけ詳細へ降りる。

## いま固定してよいこと
- prompt を増やすより、`gold replies + NG表現 + 仕上げ前チェック` を強くする
- 小さい curated set から始める
- 5件バッチ監査を回帰テスト代わりに使う
- 本番ログや実案件の微修正を、次の基準例に戻す

## まだ固定しないこと
- データ件数の厳密な上限/下限
- 重い自動評価基盤
- 監査項目の過剰な細分化

## 学習ループの目的
- `ここが変` で終わらせず、`どの相談タイプで / buyer がどの判断段階で / どの層が壊れたか` を残す
- 10件たまった時に、`failure_label` と `failure_layer` の頻度を見て、どの層を直すべきかを判断できる状態にする
- self-check に項目を足し続ける前に、上流の入力や facts packet を直せないかを先に見る
