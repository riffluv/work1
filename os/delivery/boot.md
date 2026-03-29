# Delivery OS Boot

この mode は、納品物と正式納品文を作る時だけ使います。
open case の phase は `./scripts/case-phase.sh --phase delivery` で切り替えます。

読む順:
1. `/home/hr-hm/Project/work/runtime/active-case.txt`
2. `ops/cases/open/{case_id}/README.md`
3. `delivery-pack-ja`
4. 必要なら `/home/hr-hm/Project/work/docs/coconala-guide-market-ops.ja.md`

原則:
- ここでは新しい実装判断を増やさない
- 合意済みスコープを再掲し、納品物を整える
- 外向け文面は送信前に毎回 `japanese-chat-natural-ja` を通す
- 正式納品後は `./scripts/case-close.sh` で記録を閉じる
