# 2026-04-02 返信生成 system 安定化パターン調査（Agent-Reach）

## 目的
- ココナラ受託システムの返信文生成を、個別添削ではなく仕組みで安定させる観点を外部情報から拾う。
- 特に
  - 直した NG 表現の再発
  - 温度感のブレ
  - 重複質問
  - 相手が既に答えた内容の再質問
  を減らす方法を見たい。

## 結論
- Claude の「外部調査は今すぐ必須ではない」という指摘は妥当。
- ただし外部調査からは、**内部改善4点を支持する設計パターン** は十分取れた。
- つまり、即効性は内部改善、外部調査はその改善を仕組みとして正当化する裏付けと考えるのがよい。

## 見たソース
- OpenAI Docs: Working with evals
  - https://platform.openai.com/docs/guides/evals
- OpenAI Docs: Evaluation best practices
  - https://developers.openai.com/api/docs/guides/evaluation-best-practices/
- LangSmith Docs: Evaluation concepts
  - https://docs.langchain.com/langsmith/evaluation-concepts
- Anthropic: Best practices for implementing AI
  - https://assets.anthropic.com/m/188122fea126a96b/original/Anthropic-Best-Practices-info-sheet.pdf
- Microsoft Promptflow Resource Hub: Producing Golden Datasets
  - https://aka.ms/copilot-golden-dataset-guide
- GitHub Docs: Syntax for issue forms
  - https://docs.github.com/en/enterprise-cloud@latest/communities/using-templates-to-encourage-useful-issues-and-pull-requests/syntax-for-issue-forms
- Voiceflow: intent classification prompt tips
  - https://www.voiceflow.com/pathways/5-tips-to-optimize-your-llm-intent-classification-prompts
- Vonage: intent classification hierarchy
  - https://developer.vonage.com/en/blog/how-to-build-an-intent-classification-hierarchy
- Exa で拾った補助候補
  - golden dataset / style guide / AI helpdesk triage 周辺記事

## 1. 外から見えた共通パターン

### 1-1. Prompt を増やすより、評価データセットを持つ方が効く
- OpenAI と LangSmith の docs は、良い出力を安定させるには
  - manually curated examples
  - offline eval
  - online eval
  - regression testing
  が重要だとしている。
- これは、今の「前に直した言い回しがまた出る」問題にそのまま対応している。

示唆:
- `良い返信例 / 悪い返信例` を構造化し、再発を評価できる形にするのが本筋。

### 1-2. 入力の意図分類と返信生成は分ける方が安定する
- OpenAI docs も intent classification を例にしており、まず入力を分類してから適切な出力形式へ回す発想が強い。
- Voiceflow / Vonage も、intent hierarchy を先に決めると downstream の返信品質が安定するとしている。

示唆:
- 今の OS でも、入口判定と返信文生成をもっと明確に分ける価値がある。
- `coconala-intake-router` 系の前段はかなり重要。

### 1-3. 本番ログから golden set を作るのが定番
- OpenAI / LangSmith ともに、production data や historical data から eval case を育てる流れを推している。
- Exa で拾った golden dataset 関連の記事も、real user logs を元に curated set を作る方針で一致していた。

示唆:
- あなたが毎回微修正している履歴こそ、最も価値の高いデータ。
- `過去の添削結果を生成時に見えていない` 問題は、golden set 不在の問題として整理できる。

### 1-4. 出力後チェックは別レイヤで持つ方がよい
- LangSmith は generation と evaluation を分けて扱う。
- OpenAI docs も、good looks like を定義して評価せよとしている。

示唆:
- `自然さ / 重複質問 / 相手が答えた内容の再質問 / NG表現` のチェックは、生成 prompt に全部埋めるより post-check として持つ方が安定する。

## 2. Claude 案との対応

### Claude 案 ① NG リスト正式化
- 外部の style guide / eval pattern と相性が良い。
- `NG表現` は、freeform な注意より reference file として分離した方が再利用しやすい。

### Claude 案 ② 仕上げ前チェック強化
- 外部の eval docs でいう、reference-based rubric を簡略化した形。
- 即効性が高い。

### Claude 案 ③ ゴールドリプライ蓄積
- これは外部の golden dataset / curated examples と完全に一致。
- 今回の調査で、最も強く裏付けられた案。

### Claude 案 ④ TEMPLATES と SKILLS の一本化
- 外部 docs にそのままの表現は少ないが、context organization の問題として妥当。
- 少なくとも、参照先が散らばると generation の一貫性が落ちるという説明はしやすい。

## 3. 今回の調査で分かったこと

### 3-1. すぐ効くのはやはり内部改善
- 外から「魔法の prompt」は見つからない。
- 効くのは
  - NG リスト
  - gold replies
  - post-check
  - regression set
  のような、地味だが再発防止に効く構造。

### 3-2. `#AR` が役立つのは「設計パターンの裏付け」
- 今回の問題は、ココナラ固有の文体より
  - 回帰防止
  - 評価
  - パイプライン分離
  の設計問題。
- その意味で、外の AI eval / support automation の知見は使える。

### 3-3. ただし外から直接解は来ない
- 日本語の自然さ
- ココナラの温度感
- 購入前相談の空気感
は、外部記事から直接は取れない。

示唆:
- 設計は外で学ぶ
- 文面の最終最適化は内部の gold replies と Claude で詰める
が正しい。

## 4. 今回追加で見えた「育て方の型」

### 4-1. 小さい curated set から始めるのが定番
- LangSmith は、まず critical component ごとに `5〜10` の manually curated examples を作ることを勧めている。
- これは、今の `prequote-bulk-20` をいきなり全部 gold 化するより、まず再発しやすい場面ごとに少数の基準例を持つ方がよい、という示唆になる。

示唆:
- `gold replies` は最初から大量に作らず、
  - 非エンジニア初回
  - 緊急案件
  - 15,000円高確度
  - 確認だけしたい相談の切り返し
  のような主要場面ごとに 3〜5 本ずつ増やすのが効率的。

### 4-2. オフライン評価 -> 本番ログ -> オフラインへ戻すループが王道
- OpenAI は `Evaluate early and often`、`production data` や `historical data` の利用、`continuous evaluation` を推している。
- LangSmith も `offline evaluation` と `online evaluation` の往復を前提にしている。
- Anthropic も `start small, evaluate thoroughly, scale gradually` を明示している。

示唆:
- この system では
  1. リハーサル5件バッチ
  2. Claude監査
  3. skill へ反映
  4. 実案件の微修正を gold / NG へ戻す
  の循環が、そのまま正しい育て方になる。

### 4-3. 実例は必要だが、全部を「学習」させる必要はない
- Microsoft の golden dataset ガイドは、realistic customer questions と expert answers を QA 用に持つことを推している。
- これは、良い返信文をモデルに食べさせる話ではなく、評価・比較のための基準を持つ話。

示唆:
- 必要なのは
  - 全件の蓄積
  ではなく
  - 再発しやすい場面の基準例
  - NG 再発例
  - それを判定する rubric
  である。

### 4-4. 人手レビューは最後まで残る
- OpenAI は `Combine metrics with human judgment` と明示している。
- LangSmith も annotation / human feedback を評価の一部として扱っている。

示唆:
- Claude 監査は一時的な代替ではなく、返信OSの育成ループの一部として残してよい。
- ただし毎回広く感想を求めるのではなく、`再発癖の監査` に絞る方が効く。

## 5. 暫定判断

### 今すぐやるべきもの
- `references/ng-expressions.ja.md` の新設
- SKILL の仕上げ前チェックへ
  - NG 表現
  - 重複内容
  - 相手が既に答えたことの再質問
  の3行追加
- gold replies の蓄積開始

### 後で効くもの
- regression 用の小さな dataset
- 入口判定 -> 返信生成 -> 自然化 -> 最終チェック のレーン分離

### 今は要らないもの
- 外部の support prompt をそのまま輸入すること
- rubric や eval 項目を過剰に増やすこと
- skill の細分化しすぎ

## 6. 実務への落とし込み先
- `reply` 系 skill の references/
- 共通の NG 表現ファイル
- gold replies 置き場
- 返信保存後の軽い自己チェック項目

## 7. 今の system に対する実装順
1. `NG表現` と `gold replies` を増やしすぎず、主要場面ごとに増やす
2. 5件バッチ監査を続け、再発癖だけを skill に戻す
3. 実案件の微修正から、`good` と `bad` を月次で追加する
4. rubric を固定する
   - 相手の質問や不安に正面から返しているか
   - 次アクションが明確か
   - 既出情報を聞き直していないか
   - その上で、不自然さや AI 感を減らせているか
5. その後に必要なら、場面別 mini dataset を増やす
