# CodexローカルSkills運用（work専用）

## 目的
- `/home/hr-hm/Project/work` でのみココナラ用skillsを使う。
- カードゲームなど他プロジェクトへ影響を出さない。

## 現在の配置
- ローカルskills: `/home/hr-hm/Project/work/.codex/skills`
- 起動スクリプト: `/home/hr-hm/Project/work/scripts/start-codex-work.sh`
- 重複global skillsの退避: `/home/hr-hm/Project/work/scripts/archive-global-work-skills.sh`

## 使い方
1. `cd /home/hr-hm/Project/work`
2. `./scripts/archive-global-work-skills.sh`
3. `./scripts/check-work-skills.sh`
4. `./scripts/start-codex-work.sh`

上記で起動すると、`CODEX_HOME=/home/hr-hm/Project/work/.codex` が有効になります。

## 補足
- ココナラ運用の custom skill は workspace 正本です。`/home/hr-hm/.codex/skills` 側に同名 skill を残さないでください。
- `./scripts/check-work-skills.sh` は、local skill の存在に加えて global 側の重複 custom skill も検知します。
- `start-codex-work.sh` を使わず起動した場合や、global 側に重複 skill が残っている場合は、想定外に global skill が見えることがあります。
- `~/.codex/skills/.system` は Codex の built-in 系として残ります。
