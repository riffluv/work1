# サービスカタログ（運用台帳）

更新日: 2026-03-02

## 目的
- 複数サービスを運用しても、サービス定義と案件の紐付けを崩さない。
- セッションが切れても、次のCodexがすぐに「どのサービスで進めるか」を判別できるようにする。

## Service ID 一覧（正本）

| Service ID | ステータス | サービス名 | 役割 | 価格モデル | 正本 |
| --- | --- | --- | --- | --- | --- |
| `bugfix-15000` | 運用中 | Next.js/Stripe不具合診断・修正 | 入口サービス（現行） | 基本15,000円 + 追加修正15,000円 + 追加調査30分5,000円 | 一次: `サービスページ/bugfix-15000.live.txt` / 同期: `docs/coconala-listing-final.ja.md` |
| `premium-bugfix-draft` | 将来案 | 不具合修正プレミアム | 上位派生（複数修正/再発防止） | 30,000〜60,000円想定（未公開） | `docs/coconala-premium-roadmap.ja.md` |
| `stripe-impl-draft` | 将来案 | Stripe実装（既存Next.js向け・UIデザイン除く） | 単価向上用の別サービス | 見積り前提（未確定） | `docs/coconala-stripe-implementation-listing-draft.ja.md` |

## 運用ルール（固定）
- 新しいサービスを追加したら、この台帳に `Service ID` を先に追加する。
- 新規案件の `CASE.md` には必ず `Service ID` を記入する。
- 価格や範囲を変更した場合は、台帳と該当正本を同時更新する。
- `bugfix-15000` は「一次ソース更新 -> docs同期」の順で更新する。
- 「運用中 / 将来案 / 廃止」を明示し、混在させない。

## 引き継ぎルール
- セッション開始時は `HANDOFF_NEXT_CODEX.ja.md` → `docs/README.ja.md` → 本台帳の順で読む。
- 案件対応時は、`Service ID` から参照すべき正本を決めてから返信・実装する。
