# Implementation OS テスト

## 目的
- 購入後の実装で、返信系 docs を主文脈に常駐させずに進められるか確認する
- case README とコードとログが判断の正本になっているか確認する

## 最低確認
1. `./scripts/case-open.sh --service-id bugfix-15000 --route talkroom` で case を開始する
2. `runtime/mode.txt` が `implementation` になることを確認する
3. `ops/cases/open/{case_id}/README.md` に `service_id` / `phase` / `next_action` が入っていることを確認する
4. 実装中は `os/implementation/boot.md` と `os/implementation/protocol.md` を主参照にする
5. 返信が必要な時だけ `os/coconala/reply.md` へ戻る

## 合格条件
- `implementation` mode 中に、返信テンプレを常時読まなくても作業を進められる
- case README を見れば、現在判断と次アクションが追える
