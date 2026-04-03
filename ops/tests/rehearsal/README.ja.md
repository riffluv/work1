# 返信文リハーサル運用

## 目的
- `prequote-test-cases.txt` を使って、実案件前に返信文の温度感をまとめて整える。
- 1件ずつ場当たりで直すのではなく、カテゴリ単位で AI感・硬さ・言い回しの癖を洗い出す。
- 修正結果を skill とテンプレへ戻して、全体の自然さを底上げする。

## 基本方針
- 80件を一気に見ない。
- まずは 1カテゴリ 5件ずつ、または 5〜10件単位で回す。
- 各ケースで `#A -> #R` を作り、返信文だけをまとめて Claude に監査させる。
- Claude には「個別の添削」より「共通するAI感の癖」を抜かせる。
- `ops/tests/rehearsal` は curated な監査メモと回帰確認メモだけを置く。
- raw の `batch-*.txt` はここに常置しない。作業中は `runtime/rehearsal/` を使い、保存が必要なら圧縮して `archive/` へ退避する。

## おすすめ順
1. `EST`
   - 通常の見積り相談
   - 基本の温度感を整える
2. `CHK`
   - 確認だけしたい相談でも 15,000円 案内を崩さないケース
   - 曖昧さと押し売り感のバランスを見る
3. `PRC`
   - 値引き交渉
   - 冷たさや機械感を確認する
4. `CMP`
   - 苦情寄り
   - 感情注意モードの自然さを見る
5. `CLS`
   - closed後再発
   - 一番事故りやすい文面の確認

## 1バッチの回し方
1. `prequote-test-cases.txt` から同カテゴリを 5件選ぶ
2. Codex に `#R` で返信文を作らせる
3. 返信文だけを `runtime/rehearsal/batch-*.txt` にまとめる
4. Claude にまとめて監査させる
5. 共通の癖を rule / skill に戻す
6. 長期保存が必要なら、raw batch は plain text のまま残さず `archive/*.tar.gz` に固める

## 保存先の例
- 入力ケース: `/home/hr-hm/Project/work/ops/tests/prequote-test-cases.txt`
- 一時 batch: `/home/hr-hm/Project/work/runtime/rehearsal/batch-*.txt`
- raw batch の圧縮退避: `/home/hr-hm/Project/work/ops/tests/rehearsal/archive/raw-batches-YYYY-MM-DD.tar.gz`
- Claude 監査メモ: `/home/hr-hm/Project/work/ops/tests/rehearsal/review-*.md`
- 回帰確認メモ: `/home/hr-hm/Project/work/ops/tests/rehearsal/regression-pass-*.md`

## 特に見る点
- `お気持ちももっともです` のような過剰な感情要約が入っていないか
- `〜したうえで整理します` のような説明的な言い回しが多すぎないか
- 文が長すぎないか
- 1通目で聞きすぎていないか
- 直接的に短く言えるところを、回りくどくしていないか
- 出品ページ・プロフィールの人物像とズレていないか

## 判断基準
- 「丁寧」より「自然」を優先する
- 「共感」より「事実の受領と不便の認知」を優先する
- 「きれいな文」より「同じ人が返している感じ」を優先する

## 運用メモ
- 個別ケースの直しだけで終わらせない。
- Claude 監査後は、必ず `どの表現を禁止するか / どう置き換えるか` を skill に戻す。
- 3バッチくらい回したら、ワークスペース全体の日本語品質はかなり安定する。
- raw の `batch-*.txt` は一時生成物として扱う。現行の正本は skill / rule / golden / test YAML を優先し、raw batch はそのまま最新の模範文として再利用しない。
- 履歴として残すのは、監査メモ・回帰確認メモ・圧縮退避した archive だけに寄せる。
- `handoff` が未公開の間は、handoff 前提の履歴バッチを外向け canonical として更新しない。必要な現行文面は `golden replies` 側を優先する。
