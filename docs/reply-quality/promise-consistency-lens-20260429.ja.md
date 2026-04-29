# Promise Consistency Lens

## 位置づけ

`promise_consistency` は、返信内の約束レベルが前後で整合しているかを見る reply-only の soft lens。

1文ごとの事実が正しくても、前段の留保・不可・条件付き回答を、後段の成果物・納期・料金・次アクションが上書きして見える場合に使う。

正式 hard validator や renderer rule ではない。まず #RE / #BR の外部監査プロンプトと gold で運用し、再発した subtype だけを狭い guard / ng / warning lint へ戻す。

## 定義

1通の返信内、または直近の会話文脈内で、先に明示した「未確定・不可・条件付き・購入後・値不要・範囲外・先に相談」と、後段の「対応します・進めます・直します・返します・確認します・送ってください・追加なし・原因です」などの promise-bearing 表現が、buyer にとって同じ約束レベルとして整合して読めるかを見る。

目的は、固定事実を弱めることではない。

- 強く言ってよいものは強く言う。
- 未確認の成果だけ条件を付ける。
- 約束していない成果を、接続のせいで約束したように見せない。

## subtype

- `success_guarantee_shadow`: 成功保証を否定した直後に、無条件で直す・解消するように見える。
- `deliverable_promise_shadow`: 成果物説明が、未確認の修正完了 promise に見える。
- `diagnosis_assertion_drift`: 原因未確定と言った直後に、原因を断定しているように見える。
- `phase_promise_drift`: 購入後開始と言った直後に、購入前の確認開始を約束しているように見える。
- `secret_request_contradiction`: secret 値不要と言った直後に、値を含む `.env` や APIキー送付を求めているように見える。
- `closed_work_promise`: closed 後は作業しないと言った直後に、この場で直すように見える。
- `scope_bundle_promise`: 条件付きの複数症状・複数作業を、無条件にまとめて受けるように見える。
- `payment_scope_promise`: 追加料金は先に相談すると言った直後に、そのまま追加対応するように見える。
- `production_action_shadow`: 本番反映・直接 push はしないと言った直後に、こちらが反映・push するように見える。

## severity

### hard fail

deterministic な事故に昇格する場合だけ。

- public/private 事故
- phase drift
- secret 値要求
- 成功保証・返金保証・無料対応の断定
- scope / price / payment route の事実変更
- 外部共有、直接 push、本番デプロイ誘導
- closed 後の旧トークルーム継続作業の約束

### fix recommended

明示断定ではないが、buyer には未約束の約束として読める場合。

例:

```text
確実に直ることまではお約束できません。
ただ、原因確認から修正済みファイルの返却まで進められます。
```

修正:

```text
まず原因確認から進められます。
修正できる箇所が特定できた場合は、修正済みファイルをお返しします。
```

### preference

条件・約束レベルは明確で、順序や語感を整える程度のもの。

句点の有無、やや硬い言い回し、より自然な接続語だけでは `promise_consistency` の修正対象にしない。

## human audit 記録

再発性を見る時は、次の形式で残す。

```yaml
lens: promise_consistency
subtype: success_guarantee_shadow
denied_or_limited_promise: 確実に直ることは約束できない
later_promise_phrase: 修正済みファイルの返却まで進められます
buyer_risk: 直して返す保証に見える
severity: fix_recommended
fix: まず原因確認 / 特定できた場合は返却
return_candidate: reviewer_prompt + gold
```

## 戻し先基準

| 条件 | 戻し先 |
| --- | --- |
| 1回のみ | batch 修正 + gold 候補 |
| 同 batch で2回 | ng-expressions 候補 |
| 2 batch 連続 | `coconala-reply-bugfix-ja` Gotcha 候補 |
| 3 subtype 以上 | reviewer prompt の正式 lens として固定 |
| lint で拾える同型が2回以上 | warning lint 候補 |
| false positive が多い | lint 化しない / prompt のみに戻す |

## まだやらないこと

- hard validator 化
- renderer template への全面実装
- `進められます` / `対応できます` / `修正済みファイル` の blanket lint
- `local_semantic_contradiction` という広い名前で正式化
- 1回の違和感を `japanese-chat-natural-ja` の common rule へ戻す
