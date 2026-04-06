# Coconala OS Reply Lane

購入後や返信文作成では、返信レイヤーだけを一時的に呼びます。

優先:
1. `/home/hr-hm/Project/work/os/coconala/platform-contract.yaml`
2. `coconala-intake-router-ja`
3. `coconala-reply-bugfix-ja`
4. 送信用返信は毎回 `japanese-chat-natural-ja`
5. 必要に応じて `docs/coconala-reply-self-check.ja.md`
6. 必要に応じて `docs/writing-guideline.ja.md`
7. Stripe案内がある場合は `/home/hr-hm/Project/work/stripe日本語UI案内`

保存:
- 返信保存先の正本は `/home/hr-hm/Project/work/os/core/policy.yaml`
- 送信用返信は `/home/hr-hm/Project/work/runtime/replies/latest.txt`

注意:
- 実装中は返信 docs を主文脈に常駐させない
- 返信が必要な時だけ、この lane に戻る
- 公開状態の正本は `/home/hr-hm/Project/work/os/core/service-registry.yaml`
- ココナラ共通の取引仕様は `/home/hr-hm/Project/work/os/coconala/platform-contract.yaml` を正本にする
- 返信の優先順位は `相手への正確な応答 -> スコープ・価格・規約の維持 -> 自然な日本語`
- `#R` と `#P` と納品前後の外向け文面は、最後に必ず自然化してから返す
- 自然化では、結論・質問項目数・価格・禁止事項・次アクションを増減させない
- Yes/No 質問には、手続き説明より先に結論を返す
- 購入前の返信で、まだ開いていない `トークルーム添付` を前提に書かない
- 購入前の添付依頼は `ファイル添付でお送りください` または `ご購入後にコード一式をお送りください` を使う
- 質問数は 0〜3 点に抑え、相手がすでに書いた情報を聞き直さない
- `#P` を購入後途中報告の正本にし、`#R 進捗返信` は旧互換としてのみ扱う
- 未公開サービス `handoff-25000` を外向け返信の根拠にしない
