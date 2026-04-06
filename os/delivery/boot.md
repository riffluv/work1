# Delivery OS Boot

この mode は、納品物と正式納品文を作る時だけ使います。
open case の phase は `./scripts/case-phase.sh --phase delivery` で切り替えます。

読む順:
1. `/home/hr-hm/Project/work/runtime/active-case.txt`
2. `ops/cases/open/{case_id}/README.md`
3. `/home/hr-hm/Project/work/os/coconala/platform-contract.yaml`
4. `delivery-pack-ja`
5. 必要なら `/home/hr-hm/Project/work/docs/coconala-guide-market-ops.ja.md`

原則:
- ここでは新しい実装判断を増やさない
- 合意済みスコープを再掲し、納品物を整える
- 正式な納品と通常メッセージの違いは `/home/hr-hm/Project/work/os/coconala/platform-contract.yaml` を正本にする
- 添付する納品物は完成品として閉じる。納品物本文で結果共有や追加情報送付を依頼しない
- 相違や不満は、正式納品メッセージ経由でトークルームの差し戻しへ受ける
- トークルームに送る外向け文面は送信前に毎回 `japanese-chat-natural-ja` を通す
- delivery で見つけた日本語改善は、`reply-only` / `common` / `delivery-only` を判定してから正本へ戻す
- 正式納品後は `./scripts/case-close.sh` で記録を閉じる
