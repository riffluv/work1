# 2026-04-19 Live Reply Review Session Summary

## 概要
- 対象: `bugfix-15000` live 前提の stateless 返信
- 監査件数: 55件
- 監査バッチ: 11
- 監査方法:
  - live 寄り 5件バッチを review md へ集約
  - Claude に日本語品質 + 送信可否 + 再発タグで監査
  - 必要時のみ reply-only / archetype fix を実施

## 最終状態
- 直近バッチは安定して `5/5 = 送信可`
- 大きい構造問題はかなり減少
- 監査の主眼は、主質問未回答のような大失点から、軽微だが再発性のある違和感の固定へ移行

## 今回確認できたこと
### 1. 骨格は維持でよい
- `AI の思考を早く潰さない`
- `freeform に流しすぎない`
- `reply_contract / decision / validator / eval で支える`
- この骨格自体は維持でよい

### 1.5. 両公開前提の boundary rehearsal も通過した
- `bugfix-15000` と `handoff-25000` をどちらも公開している前提の shadow batch を実施した
- mixed / boundary ケースで
  - `buyer の主目的` に沿った route 判定
  - `service_mismatch` の不発
  - 価格分離
  - handoff -> bugfix 接続
  - handoff 進行中の bugfix 切替
  が成立することを確認した
- これは `handoff-25000` を public にする前の公開判断の証跡として扱ってよい

### 2. 返信システム本体は「広く作り直す」段階ではない
- 新しい層追加
- scenario 増殖
- renderer 増殖
- これはやらない方がよい

### 3. 有効だったのは「監査観点の強化」
- 日本語の微妙なズレ
- buyer 事実とのずれ
- 不安相手への着地の弱さ
- 内部語・手続き語の露出
- 技術説明の言いすぎ
- これらを監査観点として固定したことで、見逃しが大きく減った

## 今回の主要な再発タグと扱い
### 恒久観点として採用済み
- `fact_alignment`
  - buyer が書いていない事実や症状名にすり替わっていないか
- `semantic_echo`
  - 隣り合う文が意味重複していないか
- `closing_complete`
  - 最後に次の入口や次アクションがあるか
- `urgency_symmetry`
  - 急ぎ・不安・過去の嫌な経験に冒頭で触れているか
- `direct_answer_first`
  - 主質問に先に答えているか
- `unanswered_secondary`
  - 副質問が欠落していないか
- `internal_process_exposure`
  - buyer 向けに内部プロセス語を見せていないか
- `technical_explanation_safety`
  - 原因推定より、確認方針・確認箇所・未断定を優先しているか

### 今回消せたもの
- 主質問スルー
- テンプレ使い回し
- オウム返し
- 同一文重複
- `出方`
- `前提です`
- `ご相談ください` のズレ
- `bugfix` など内部ラベル漏れ
- `fact_drift`
- `scenario_misroute`

## 今回の構造修正で効いた archetype
以下は case fix ではなく archetype fix として扱った。

1. `service_selection_uncertainty`
- どちらのサービスが合うか
- bugfix 入口へ自然に寄せる

2. `guarantee_or_refund_prequote`
- 15,000円で確実に直る保証
- 直らなかった場合どうなるか

3. `progress_status_request`
- 進捗どうなっているか
- 今どこまで見ているか

4. `delivered_self_deploy_anxiety`
- 本番反映は自分でやるのか
- 気をつける点は何か

## 技術説明の安全性
### 確認できた安全側の原則
- buyer に出す技術説明は `原因推定` ではなく `確認方針` に寄せる
- `可能性が高い / おそらく / 思われます` のような推定語は warn-only で監視
- 相手の事実から自然に言える範囲だけを書く

### 今回追加したもの
- `scripts/reply_quality_lint_common.py`
  - 技術推定語の warn-only lint
- `scripts/check-technical-explanation-safety.py`
- `ops/tests/regression/technical_explanation_safety/cases.yaml`

## 監査プロンプト側の成果
### 8 -> 14 観点へ拡張
追加して有効だったもの:
- 参照語の着地
- 不安明示時の行動コミット
- 責任主体と締め文の一致
- 外部向け語彙への変換
- 技術説明の断定制御
- 事実引用精度
- 意味重複
- 閉じの完全性
- 緊急度の応答対称性

### 運用ルール
- 単語NGリスト化はしない
- 監査は「語彙」ではなく「受け手への作用」で見る
- 各指摘は
  - 該当箇所
  - なぜズレるか
  - 最小修正案
  - 恒久観点か / 好み差か
  をセットで扱う

## 進め方で正しかったこと
- 壊れた時に rollback した
- rollback 後に「大改修」ではなく、監査観点を強化した
- ランダムバッチで悪化が見えた時、case fix ではなく archetype fix に切り替えた

## 今後やってはいけないこと
- random 5件で荒れたからといって、その case 文面だけ直す
- scenario を都度増やす
- renderer を都度増やす
- 学習バッチを live 判定と同じ重さで扱う
- 単語レベルで NG 語を増やす

## 次セッションへの引き継ぎ
### 基本方針
- 返信システム本体は「広く触らない」
- まず live 寄り 5件で確認
- 問題が出たら
  - case fix か
  - archetype fix か
  を先に切る

### 優先順位
1. live 5件バッチ監査
2. 再発タグの整理
3. archetype fix が必要な場合のみ code 側修正
4. docs / skill へ恒久観点反映

### 今の判断
- 現在の reply system は、破壊前より「監査精度」と「再発防止」の面で強い
- ただし土台の良さは元の骨格に依存しており、今後も「広げるより締める」を優先する
- `handoff-25000` は internal learning として十分安定しており、both-public rehearsal も通過したため、公開判断は routing 不安ではなく運用タイミングの問題として扱える
