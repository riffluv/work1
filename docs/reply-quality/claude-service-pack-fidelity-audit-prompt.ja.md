# Claude Service-Pack Fidelity Audit Prompt

```text
あなたは設計レビュー担当です。新しい設計案を作る役ではなく、監査だけをしてください。
主軸は Codex で、採用判断と正本反映は Codex が行います。

今回は `bugfix-15000` の service-pack について、
「公開サービスページの意味が、service-pack にちゃんと落ちているか」
を監査してください。

目的:
- 単発返信の日本語ではなく、サービス理解 fidelity を見ること
- `service page -> service-pack -> reply` の意味落ちが減っているかを確認すること
- 特に、先日追加した `decision-contract` / `evidence-contract` / `source-of-truth policy` が効いているかを見ること

前回までの主な懸念:
- service-pack は「何を売るか」は保持できているが、「どう判断するか」「どこで止まるか」が弱い
- seeds / tone が source-of-truth 側に近すぎて、service 理解と style が混ざっていた
- FAQ / 回答例の意味が、service-owned な回帰源として固定されていなかった

今回反映した変更:
1. `decision-contract.yaml` を追加
   - same-cause / different / undecidable
   - 原因不明時の formal delivery gate
   - final confirmation owner
   - same-cause adjustment window
2. `evidence-contract.yaml` を追加
   - phase 別 minimum ask
   - symptom only okay
   - `.env はキー名のみ`
   - Stripe first-class evidence（evt_... など）
3. `routing-playbooks` に `state_contract` を追加
   - promised next action
   - secondary thread の disposition / return timing / required input
4. 公開ページの FAQ / 回答例を regression source として追加
5. `service-pack-source-of-truth-policy.ja.md` を追加
   - public contract
   - decision / evidence
   - routing / state
   - seeds / tone
   の責務分離を明示

今回見てほしいファイル:

公開サービスページ:
- /home/hr-hm/Project/work/サービスページ/bugfix-15000.live.txt

bugfix service-pack:
- /home/hr-hm/Project/work/ops/services/next-stripe-bugfix/service-pack/README.ja.md
- /home/hr-hm/Project/work/ops/services/next-stripe-bugfix/service-pack/facts.yaml
- /home/hr-hm/Project/work/ops/services/next-stripe-bugfix/service-pack/boundaries.yaml
- /home/hr-hm/Project/work/ops/services/next-stripe-bugfix/service-pack/decision-contract.yaml
- /home/hr-hm/Project/work/ops/services/next-stripe-bugfix/service-pack/evidence-contract.yaml
- /home/hr-hm/Project/work/ops/services/next-stripe-bugfix/service-pack/routing-playbooks.yaml
- /home/hr-hm/Project/work/ops/services/next-stripe-bugfix/service-pack/state-schema.yaml
- /home/hr-hm/Project/work/ops/services/next-stripe-bugfix/service-pack/seeds.yaml
- /home/hr-hm/Project/work/ops/services/next-stripe-bugfix/service-pack/tone-profile.yaml

回帰源:
- /home/hr-hm/Project/work/ops/tests/regression/service_pack_fidelity_bugfix/cases.yaml

共通ポリシー:
- /home/hr-hm/Project/work/docs/reply-quality/service-pack-source-of-truth-policy.ja.md

監査してほしい論点:
1. 前回の懸念だった
   - 「どう判断するか」
   - 「どこで止まるか」
   - 「何を最低限聞くか」
   は今回の追加で改善されたか
2. `decision-contract` と `evidence-contract` は、公開ページ・FAQ・回答例の意味を十分保持できているか
3. `routing / state` と `seeds / tone` を source-of-truth から一段下げた設計は妥当か
4. まだ `service 理解` と `reply スタイル` が混ざっている箇所はあるか
5. まだ足りない項目があるなら、それは
   - facts / boundaries
   - decision / evidence
   - routing / state
   - seeds / tone
   のどこに属するか
6. 今回の変更で、service-pack fidelity は
   - 以前より上がったか
   - まだ中くらいか
   - source-of-truth として危ないままか
を率直に判定してほしい

出力形式:
次の順で簡潔に答えてください。

1. 総評
- 今回の変更で fidelity は上がったか
- 一言でいうと、今の状態は「かなり良い / まだ中くらい / まだ危ない」のどれか

2. 改善された点
- 前回弱かったが、今回よくなった点を 3〜6 個

3. まだ弱い点
- まだ意味落ちが残っている点を 3〜6 個
- それぞれ、どの層の問題かも書く
  - facts / boundaries
  - decision / evidence
  - routing / state
  - seeds / tone

4. ノイズ
- まだ source-of-truth 側に残っていて危ないもの
- 逆に削りすぎて危ないもの

5. Codex への推奨
- 今すぐやるべき修正を最大 5 個
- 優先順位つきで
- `今やる / 後でよい / まだやらない` の区別が分かるように

重要:
- 新しい大設計を広げることが目的ではありません
- 今回の差分が、前回の意味落ち懸念に本当に効いているかだけを見てください
- 日本語返信の wording ではなく、service-pack fidelity を監査してください
```
