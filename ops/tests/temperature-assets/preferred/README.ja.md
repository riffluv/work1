# preferred rewrites

- `quality-audit-preferred.jsonl` は、quality-audit レポートから抽出した「最小修正版」の置き場。
- 現時点では `user_message + preferred_reply` までは保存できている。
- ただし初稿返信が workspace に残っていないため、full pair ではなく preferred rewrite の保存にとどめている。
- 次回以降は batch 初稿も保存し、`pairs/` に `draft_reply / preferred_reply` を並べる。
