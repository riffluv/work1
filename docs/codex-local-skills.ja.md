# CodexローカルSkills運用（work専用）

## 目的
- `/home/hr-hm/Project/work` でのみココナラ用skillsを使う。
- カードゲームなど他プロジェクトへ影響を出さない。

## 現在の配置
- ローカルskills: `/home/hr-hm/Project/work/.codex/skills`
- 起動スクリプト: `/home/hr-hm/Project/work/scripts/start-codex-work.sh`

## 使い方
1. `cd /home/hr-hm/Project/work`
2. `./scripts/check-work-skills.sh`
3. `./scripts/start-codex-work.sh`

上記で起動すると、`CODEX_HOME=/home/hr-hm/Project/work/.codex` が有効になります。

## 補足
- 既存のグローバルskills（`/home/hr-hm/.codex/skills`）は残しています。
- `start-codex-work.sh` を使わず起動した場合は、従来どおりグローバルskillsが使われます。
