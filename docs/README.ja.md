# docs 目次（現行運用用）

この `docs/` は、今の Codex が起動・返信・実装・納品で参照するものだけを置く場所です。
過去の調査ログや初期設計メモは正本扱いにしません。

## 起動と Core OS
- `docs/next-codex-prompt.txt`
  - 次の Codex 起動時の単一正本。
- `AGENTS.md`
  - workspace 全体の固定ルール。
- `os/core/service-registry.yaml`
  - サービス公開状態と service page 正本の台帳。
- `runtime/mode.txt`
  - 現在の mode 正本。
- `runtime/active-case.txt`
  - active case 正本。

## サービスページ正本
- `bugfix-15000`
  - `/home/hr-hm/Project/work/サービスページ/bugfix-15000.live.txt`
- `handoff-25000`
  - `/home/hr-hm/Project/work/サービスページ/handoff-25000.ready.txt`
- `docs/coconala-listing-final.ja.md`
  - 同期ミラー。公開判断や文言監査の基準にはしない。

外向けに案内してよいかは、必ず `os/core/service-registry.yaml` の `public` を見る。

## ココナラ返信
- `docs/reply-quality/README.ja.md`
  - `#RE` / `#BR` / 学習ループ / 直近棚卸しの入口。
- `docs/coconala-reply-self-check.ja.md`
  - 送信前チェックの詳細。
- `docs/coconala-prequote-commitment-policy.ja.md`
  - 購入前見積りで約束しすぎないための固定ルール。
- `docs/coconala-handoff-prequote-mini-contract.ja.md`
  - `handoff-25000` の購入前案内を扱う時の内部契約。
- `docs/coconala-special-case-policy.ja.md`
  - 特例対応の判断基準。
- `docs/coconala-golden-replies.ja.md`
  - 良い返信例の補助資料。
- `docs/coconala-message-templates-short.ja.md`
  - 短文テンプレ。必要時だけ参照する。

送信用返信の最終自然化は、毎回 `japanese-chat-natural-ja` を使う。

## 日本語品質
- `docs/writing-guideline.ja.md`
  - トークルーム文面の文体ルール。
- `docs/coconala-japanese-banlist.ja.md`
  - 使わない表現。
- `docs/coconala-japanese-must-rules.ja.md`
  - 必ず守る日本語ルール。

## 実装と納品
- `docs/code-comment-style.ja.md`
  - 実装時のコードコメント規約。
- `docs/coconala-guide-market-ops.ja.md`
  - 購入時挨拶、滞留時連絡、正式納品まわりの運用メモ。
- `docs/handoff-delivery-template.ja.md`
  - handoff 系納品物のテンプレ。
- `docs/internal-quality-samples/`
  - 納品物サンプル。納品 mode / delivery skill から参照する。

bugfix の標準納品物は `00_結論と確認方法.md` とコード納品物。

## 原則
- 古い調査メモや初期設計メモを、現行判断の正本に戻さない。
- 外部調査はユーザーが明示した時だけ使う。
- `handoff-25000` は `service-registry.yaml` で `public: true` になるまで、通常 live / #RE に出さない。
