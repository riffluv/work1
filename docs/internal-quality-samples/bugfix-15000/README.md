# bugfix-15000 内部品質見本

題材:
- 公開リポジトリ `nextjs/saas-starter`
- Stripe Checkout 完了後に `/dashboard` の `Current Plan` が `Free` のまま残る不具合

この見本の役割:
- `00_結論と確認方法.md` の書き方を揃える
- 修正済みファイル内コメントの濃さを揃える
- patch の粒度を揃える

実案件で参照する時の原則:
- 見本の文言をそのまま流用しない
- 実案件の症状・原因・実ファイル名・一次証跡を優先する
- コメントは `docs/code-comment-style.ja.md` を前提に、WHY / 制約 / 副作用 / 運用条件だけを最小限残す
