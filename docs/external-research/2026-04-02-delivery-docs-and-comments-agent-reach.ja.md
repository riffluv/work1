# 2026-04-02 納品物構成・コードコメント調査（Agent-Reach）

## 目的
- `docs/internal-quality-samples` を磨くため、納品物の構成とコードコメントの実務パターンを外部公開情報から拾う。
- `bugfix-15000` と `handoff-25000` の納品物に再発性のある改善だけを抽出する。
- `chatgptPro/納品物の構成.txt` と `chatgptPro/実務コードコメントの改善.txt` は、この調査では前提にせず後で突き合わせる。

## 調査メモ
- まず英語圏を広めに見た。構造の型は公開情報が多く、比較しやすいため。
- 日本語向けの温度感や見出し名は、構造抽出後にローカルで調整する方針。
- Exa は一部クエリで rate limit に当たったため、取得できた結果と公開 Web ドキュメントを中心に読んだ。

## 見たソース
- Divio Documentation System
  - https://documentation.divio.com/
- Write the Docs: How to write software documentation
  - https://www.writethedocs.org/guide/writing/beginners-guide-to-docs/
- Refactoring.Guru: Comments
  - https://refactoring.guru/smells/comments
- Google SRE: Example Postmortem
  - https://sre.google/sre-book/example-postmortem/
- Google SRE Workbook: Postmortem Culture
  - https://sre.google/workbook/postmortem-culture/
- Atlassian: Incident postmortems
  - https://www.atlassian.com/incident-management/handbook/postmortems
- Atlassian: Incident report template guide
  - https://www.atlassian.com/software/confluence/resources/guides/how-to/incident-report
- incident.io: Post-mortem templates
  - https://docs.incident.io/post-incident/postmortem-templates

## 1. 納品物構成で拾えた共通パターン

### 1-1. 先に読む人向けの要約ブロックが強い
- Google SRE の postmortem 例は `Summary / Impact / Root Causes / Trigger / Resolution / Detection / Action Items` の順で、最初に全体をつかめる。
- incident.io も `Summary` を常に先頭に置く形を推している。
- Atlassian も、影響・対応・根本原因・再発防止をテンプレ化している。

示唆:
- `bugfix` の `00_結論と確認方法.md` は、今の「結論先頭」方針をさらに強めてよい。
- `handoff` の `00_結論と要点.md` も、詳細前に「何が分かったか」「どこが危険か」「次に何をするか」を先に出すのが筋。

### 1-2. 詳細文書は「全部入り」ではなく役割分担がある
- Divio は文書を `tutorials / how-to / reference / explanation` に分けて扱う。
- Write the Docs も、読者ごとに必要情報を絞るべきで、FAQ に寄せすぎるなと書いている。
- incident.io も、重い RCA と軽い lessons learned を分け、重大度に応じてテンプレを変えている。

示唆:
- `handoff` の 2ファイル構成はかなり筋が良い。
- `00_結論と要点.md` は「要約と次の判断」へ寄せる。
- `01_[対象フロー名]_引き継ぎメモ.md` は「どこを見るか」「何が危険か」「どこまで確認済みか」の詳細へ寄せる。
- 1ファイル内にタイムライン・根拠・手順・設計意図を全部押し込まない方が読みやすい。

### 1-3. 読み手は「次に何をすればよいか」を早く知りたい
- Google SRE / Atlassian は、原因だけでなく follow-up や action items を明示している。
- Google SRE Workbook は、良い action item の条件として `owner / priority / measurable / preventative` を挙げている。

示唆:
- `handoff` の納品物では、「次の着手順」を単なる感想で終わらせず、順番付きで短く示すと強い。
- `bugfix` では、「何を確認すれば再発していないと言えるか」を手順化して示すのが強い。

## 2. `handoff-25000` に効く構成示唆

### 強めてよいもの
- 先頭で `対象フロー` を1行で特定する
- `確認できたこと / 推定 / 未確認` を分ける
- `まず見るファイル` を先に出す
- `危険箇所` は箇条書きで短く切る
- `次の1手` は優先順で出す

### 抑えた方がよいもの
- 長い背景説明
- タイムライン風の調査ログ
- コード断片の貼りすぎ
- FAQ 的な枝葉説明の増殖

### 今の本丸との整合
- `00_結論と要点.md` と `01_[対象フロー名]_引き継ぎメモ.md` の2段構成は維持でよい。
- さらに磨くなら、`01_...` の冒頭に `まず見る場所 / 危険箇所 / 次の1手` をもう少し前に寄せる価値がある。

## 3. `bugfix-15000` に効く構成示唆

### 強めてよいもの
- `何が壊れていたか`
- `何を変更したか`
- `どう確認するか`
- `依頼者環境で最終確認してほしい点`

### 補強できる観点
- `Impact` 相当: どの症状が止まっていたか
- `Root cause` 相当: なぜ起きていたか
- `Resolution` 相当: どの変更で直したか
- `Verification` 相当: どの観点で確認すればよいか

### 今の本丸との整合
- 現行の `00_結論と確認方法.md` の方向は合っている。
- 再発性のある改善としては、変更内容の列挙より `確認手順の分かりやすさ` を優先して磨く方が効きそう。

## 4. コードコメントで拾えた共通パターン

### 4-1. `what` より `why`
- Write the Docs は、コードコメントは `why` を伝えるものだとしている。
- Refactoring.Guru も、説明コメントだらけのコードは code smell で、構造改善で消せるコメントは消すべきだとしている。
- ただし、`why` や複雑なアルゴリズム説明は有効だとしている。

### 4-2. コメントを増やす前にコードを良くする
- Refactoring.Guru は、式分割・メソッド抽出・命名改善で不要コメントを減らせと明示している。

示唆:
- `docs/code-comment-style.ja.md` の
  - WHY
  - 制約
  - 副作用
  - 運用条件
  だけを書く方針は、かなり外部のベストプラクティスと整合している。

### 4-3. コメントは保守者の判断補助に寄せる
- 外部ソースは、将来の読み手が「なぜこの実装なのか」「どこが危ないのか」を理解できることを重視している。

示唆:
- `bugfix` では納品物で説明できることをコードに残しすぎない、今の方針が妥当。
- `handoff` では入口・危険箇所・境界条件を一段厚めに残し、全体説明はメモへ逃がす、今の方針が妥当。

## 5. 今回の調査から見た暫定判断

### 採用寄り
- `handoff` は 2ファイル構成のまま磨く
- `00` は要約、`01` は引き継ぎ詳細として役割分担をさらに明確にする
- `bugfix` は `原因 / 変更 / 確認` の3点をさらに読みやすく固定する
- コメントは今の `why / 制約 / 副作用 / 運用条件` 方針を維持する

### 追加で見たいもの
- 公開 repo の実際の `handoff / runbook / architecture` 文書で、見出し順の当たり例
- bugfix レポートに近い、顧客向けまたは社内向け RCA / verification 文書の軽量版

### 今は採らないもの
- 重いタイムライン中心の文書
- FAQ 的な何でも箱
- コメントでコードの動きを実況する書き方

## 6. 次にやると効くこと
- `docs/internal-quality-samples/handoff-25000/00_結論と要点.md`
  - 「次に何をするか」の見せ方を再点検
- `docs/internal-quality-samples/handoff-25000/01_..._引き継ぎメモ.md`
  - 入口ファイル / 危険箇所 / 次の着手順の並びを再点検
- `docs/internal-quality-samples/bugfix-15000/00_結論と確認方法.md`
  - 確認手順の見せ方を再点検
- `docs/code-comment-style.ja.md`
  - 大きな方針変更は不要。実例テンプレを少し増やす余地はある
