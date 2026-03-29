# Core OS Boot

この内部OSでは、常時前面に出してよいのは Core OS だけです。
最初に次の3点だけ確認します。

1. `./scripts/os-check.sh` が通ること
2. 公開状態は `/home/hr-hm/Project/work/os/core/service-registry.yaml` を正本にすること
3. mode は `/home/hr-hm/Project/work/runtime/mode.txt` を見ること

Core OS で毎回読むもの:
- `/home/hr-hm/Project/work/os/core/policy.yaml`
- `/home/hr-hm/Project/work/os/core/service-registry.yaml`
- `/home/hr-hm/Project/work/docs/code-comment-style.ja.md`

mode ごとの分岐:
- `coconala`: `/home/hr-hm/Project/work/os/coconala/boot.md`
- `implementation`: `/home/hr-hm/Project/work/os/implementation/boot.md`
- `delivery`: `/home/hr-hm/Project/work/os/delivery/boot.md`

最重要ルール:
- 公開中サービスの案内は `service-registry.yaml` で `public: true` のものだけ
- 購入後の実装では、返信系 docs を主文脈に常駐させない
- 送信用返信の保存先は `/home/hr-hm/Project/work/runtime/replies/latest.txt`
- active case は `/home/hr-hm/Project/work/runtime/active-case.txt`
