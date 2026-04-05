# 2026-04-05 Next Codex Handoff: 返信システム

## 現在地
- mode は `coconala`
- active case は空
- role suites は全通
- 公開 live は `bugfix-15000` のみ
- 返信システムは `routing / scenario selection / response_decision_plan / validator` までは前進している
- ただし文面品質は、特に `quote_sent` でまだ unstable

## Keep するもの
- `routing / scenario selection`
- `response_decision_plan` の最小 5 field
  - `primary_concern`
  - `facts_known`
  - `blocking_missing_facts`
  - `direct_answer_line`
  - `response_order`
- `facts_known + blocking_missing_facts` による ask gating
- narrow validator / checker / regression
- Pro / #AR の方向性そのもの

## 捨てるべきもの
- `slot-filling renderer` を文面生成の主役として延命すること
- `reaction_line()` や `answer_brief` のハードコード文を増やして patch で耐えること
- `direct_answer_line` と `answer_brief` を独立ソースのまま並べて出力すること

## いまの主 failure
- `renderer-first / template-first` の残留
- とくに `direct_answer_line` と `answer_brief` の 2 ソース問題
- buyer の主訴より scenario ラベルや手続き文が前に出る
- lane は合っていても Codex reasoning が prose に届く前に圧縮される

## batch9 で確認されたこと
- `QST-003` は良好。短く直接で、freeform 的に成功
- `QST-001` は全9バッチ最悪級。`進められるか / いけるか / 進めるか` の 3 重同義反復
- `QST-002` は同一文の完全重複
- `PRC-004` / `QST-004` は後半がほぼ同一で、入力差より template が勝っている
- 結論: `quote_sent` は部分的前進だが、複雑ケースではまだ renderer-first

## Pro / Claude / #AR で固まっている判断
- Pro の設計は正しい
- 間違っていたのは heavy renderer 実装
- missing piece は `thought-preserving design` / `response_decision_plan`
- ただし plan を入れただけでは不十分で、文章生成はより freeform drafting に寄せる必要がある
- skill は捨てない。`writer` から `guardrail` へ役割変更する

## 次の Codex が最初に読むべきファイル
- `/home/hr-hm/Project/work/chatgptPro/返信システム完全性レビュー_思考保存設計.txt`
- `/home/hr-hm/.gemini/antigravity/brain/608b17fa-52b1-4eaa-9bab-46ff53df30cd/artifacts/architecture-review-pro-alignment-check.md.resolved`
- `/home/hr-hm/.gemini/antigravity/brain/608b17fa-52b1-4eaa-9bab-46ff53df30cd/artifacts/quality-audit-batch9.md.resolved`
- `/home/hr-hm/Project/work/docs/external-research/2026-04-05-thought-preserving-design-agent-reach.ja.md`

## 次の single next step
- `quote_sent` を題材に、`renderer-first` の延命ではなく
  - `service grounding + hard constraints + response_decision_plan + Codex freer drafting + validator`
 へ寄せる実装判断をすること
- 以後は `reaction_line` や `answer_brief` を増やす patch ループに戻らない

## 明確な禁止
- `quote_sent` に対してさらに slot を足して直そうとしない
- `purchased` や `closed` に同じ heavy renderer パターンを横展開しない
- batch9 の問題を「文面調整だけ」で閉じない
