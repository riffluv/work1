# 2026-04-02 bugfix 検証手順・原因記述・コメント境界調査（Agent-Reach）

## 目的
- `bugfix-15000` の納品物本丸を、共通の書き方の型より一段深く磨く。
- 特に以下の3テーマを外部公開情報から確認する。
  1. 確認手順と OK 条件の書き方
  2. 原因の書き方
  3. コードコメントと納品文書の境界

## 見たソース
- GitHub Docs: Syntax for issue forms
  - https://docs.github.com/en/enterprise-cloud@latest/communities/using-templates-to-encourage-useful-issues-and-pull-requests/syntax-for-issue-forms
- Google SRE: Example Postmortem
  - https://sre.google/sre-book/example-postmortem/
- Write the Docs: How to write software documentation
  - https://www.writethedocs.org/guide/writing/beginners-guide-to-docs/
- Refactoring.Guru: Comments
  - https://refactoring.guru/smells/comments

補足:
- Exa で候補探索も行ったが、最終判断は上記の公開ドキュメント寄りに置いた。
- QA 記事や個人ブログは補助的には見たが、今回のメモでは再発性の高い型だけ残した。

## 1. 確認手順と OK 条件の書き方

### 1-1. `操作 / 期待結果 / 補助情報` の3点が揃うと強い
- GitHub の bug issue form 例では、`Current Behavior / Expected Behavior / Steps To Reproduce / Environment / Logs` が分かれている。
- これを納品物の確認手順へ持ち込むと、`何をするか` と `何が見えれば OK か` を対で書くのが自然。

示唆:
- `bugfix` の確認手順は、各 step を
  - 操作
  - 期待結果
  - 必要なら補助確認
  の順で見ると安定する。

### 1-2. 依頼者が必ずできる確認と、可能ならやる確認を分ける方がよい
- GitHub issue form でも、環境やログは必須と任意が分かれている。
- これに近い考え方で、納品物の確認手順も
  - 画面で見える確認
  - 管理画面での確認
  - DB での確認
  を混ぜずに書く方が分かりやすい。

示唆:
- `bugfix-15000/00_結論と確認方法.md` の
  - Step 2: 画面
  - Step 3: Stripe ダッシュボード
  - Step 4: DB
  の分け方はかなり良い。
- 今後も、深い確認ほど「可能であれば」に逃がす方針でよい。

### 1-3. OK 条件は短い括弧書きで十分
- 期待結果を別段落で重く書く必要はない。
- 今の `bugfix` のように、各手順の末尾に `（...であれば OK です）` を足す程度がちょうどよい。

示唆:
- bugfix の確認手順は、今後も
  - `...を確認する（...であれば OK です）`
  の型を基本にしてよい。

## 2. 原因の書き方

### 2-1. 良い postmortem は `Impact` と `Root Cause` を分けている
- Google SRE の postmortem 例は、`Summary / Impact / Root Causes / Trigger / Resolution / Detection / Action Items` を分けている。
- これは、利用者が受けた現象と、技術的な原因を混ぜないため。

示唆:
- `bugfix` の納品物でも、
  - 依頼者が見た症状
  - 技術的な主原因
  を分けて書く方が読みやすい。
- 現行の `## 1. 今回の対象` と `## 2. 結論` と `## 4. 原因` の分担はかなり良い。

### 2-2. 原因は「1文の核 + 補足段落」が読みやすい
- Google SRE の `Root Causes` は、まず核になる1文があり、そのあと補足で条件や背景が続く。
- Write the Docs も、読み手が必要とする情報を出しすぎず、まず問題を明確にせよとしている。

示唆:
- `bugfix` の `主原因` は1文で言い切る。
- そのあと `## 4. 原因` で
  - どういう条件で起きたか
  - なぜ取りこぼしたか
  を短い段落で補う、今の形が良い。

### 2-3. 非エンジニア向けには「技術用語の置き場所」を工夫する
- `customer.subscription.created` のような固有名詞は必要だが、原因の1文に詰め込みすぎると硬くなる。

示唆:
- まずは症状とのつながりが分かる短い因果を書く。
- 固有名詞は補足段落や修正内容で回収する方が自然な場合がある。
- ただし現行の bugfix サンプルは、題材が Stripe webhook であり、固有名詞を隠す必要まではない。

## 3. コードコメントと納品文書の境界

### 3-1. コメントは `why`、文書は `what changed / how to verify`
- Write the Docs は、コードの背景や意図を文書で補う意義を書いている。
- Refactoring.Guru は、構造改善で消せるコメントは消し、必要なら `why` や複雑な事情だけ残すべきだとしている。

示唆:
- `bugfix` では
  - 修正理由の要点
  - 外部制約
  - 一時障害時の扱い
  だけコメントへ残す。
- 修正経緯、背景説明、依頼者への確認依頼は納品物へ出す。

### 3-2. `// Fixed bug ...` のような履歴コメントは残さない方がよい
- 外部の定番でも、修正履歴をコードへ残すことは勧められていない。
- そうした情報は version control や別文書で追う前提が強い。

示唆:
- 現行の `code-comment-style.ja.md` の方針どおり、修正履歴コメントは残さないでよい。
- bugfix の変更理由は `00_結論と確認方法.md` に逃がすのが正しい。

### 3-3. 命名や構造で消せるコメントは消す
- Refactoring.Guru は、コメントが必要なら先に `Extract Method` や命名改善を検討せよとしている。

示唆:
- 直近で追加した `構造改善や命名改善で消せるコメント` ルールは妥当。
- `bugfix` ではコメントを足す前に、分岐やエラーハンドリングの形で明瞭化できないかを見るのがよい。

## 4. 今回の調査から見た暫定判断

### 調査結果として使えるもの
- 確認手順は `操作 / 期待結果 / 補助確認` で見る
- OK 条件は各 step 末尾の短い括弧書きで十分
- 原因は `症状` と `技術的主原因` を分けて見せる
- コメントは `why / 制約 / 副作用 / 運用条件` だけ残し、履歴は納品物へ逃がす

### 今の bugfix 本丸で大きく変えなくてよいもの
- `## 2. 結論` の3行構成
- `## 5. 修正内容` の簡潔さ
- 修正済みコードのコメント量
- 正式納品メッセージ全体の構造

## 5. 落とし込み候補

### すぐ採る候補
- なし。今回の調査は、現行方針の裏付けが主。

### 実案件で効きそうな再利用ルール
- `bugfix` の確認手順は、各 step に期待結果を短く添える
- 深い確認（Stripe 管理画面 / DB）は `可能であれば` と明示する
- 原因は `症状` と `技術的主原因` を混ぜない
- `Fixed ...` のような履歴コメントはコードへ残さない

## 6. 次に見るなら
- 実案件を1件回したあとに、
  - Step 3 のような管理画面確認が依頼者に重かったか
  - DB 確認をどこまで求めると負荷が高いか
  を運用知見として戻すのが最も効果が高い。
