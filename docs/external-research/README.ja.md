# external-research

この階層は、**外部調査レーンのメモ置き場**です。

- `chatgptPro/`
  - ChatGPT Pro を主に使って集めた調査メモ
- `docs/external-research/`
  - Codex 主軸で、Agent-Reach などの外部調査ツールを使って集めた調査メモ
- `docs/external-research/prompts/`
  - Agent-Reach で再利用する調査 prompt の置き場

使い分け:
- ここに置くのは **外部情報の整理メモ** であり、サービスページや納品物の正本ではない
- 正本へ反映する前に、Codex が妥当性・再発性・実務ノイズ・既存ルールとの整合を判断する
- Claude / Gemini へ見せる場合は、この階層のメモを参照資料として使ってよい

注意:
- 外部調査の結果は、そのまま正本へ入れない
- 一次証跡がある場合は、外部調査メモより一次証跡を優先する

現在のメモ:
- `2026-04-02-handoff-pain-points-agent-reach.ja.md`
  - `handoff-25000` の買い手が実際にどう困っているかの外部調査
- `2026-04-02-delivery-docs-and-comments-agent-reach.ja.md`
  - 納品物構成・引き継ぎメモ・コードコメントの外部調査
- `2026-04-02-bugfix-verification-and-root-cause-patterns-agent-reach.ja.md`
  - `bugfix-15000` 向けの検証手順、原因記述、コメント境界の外部調査
- `2026-04-02-bugfix-demand-pain-points-agent-reach.ja.md`
  - `bugfix-15000` の需要・痛み表現・サービスページ訴求の外部調査
- `2026-04-02-reply-system-stability-patterns-agent-reach.ja.md`
  - 返信生成 system の安定化、gold replies、NG 表現、回帰監査の育て方に関する外部調査

現在の prompt:
- `prompts/2026-04-04-agent-reach-buyability-prompts.ja.md`
  - 売れやすさ改善向けの `#AR` 調査 prompt 集
