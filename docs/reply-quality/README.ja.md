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
- `scorecard.ja.md`
  - 返信品質を 10項目で軽く数値化する採点表
- `multi-turn-check.ja.md`
  - 連続3通で停滞や矛盾を見つけるためのチェック
- `service-facts-onboarding-template.ja.md`
  - 新しいサービスへ入れる時に、何を facts 化するかを揃える導入テンプレ
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

## 監査の固定 rubric
1. 相手の質問や不安に正面から返しているか
2. 次アクションが明確か
3. 既出情報を聞き直していないか
4. その上で、不自然さや AI 感を減らせているか

## 運用ルール
- 監査コメントは、まず `failure-taxonomy.ja.md` の主ラベル1つで整理する。
- 学習メモは `/home/hr-hm/Project/work/ops/tests/stock/learning-log/` に残す。
- 学習メモのひな形は `learning-log-template.yaml` を使う。
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
