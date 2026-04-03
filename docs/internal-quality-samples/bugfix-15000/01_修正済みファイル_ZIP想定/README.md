# 01_修正済みファイル_ZIP想定

実運用では、この中身を ZIP にして納品する想定です。

- 標準は修正済みファイルの差し替えです
- `02_修正差分.patch` は Git 運用者向けの任意添付です
- `.env*` `node_modules` `.git` は含めません

今回の題材は、`nextjs/saas-starter` の `app/api/stripe/webhook/route.ts` を修正した想定です。
ここではコメント品質も見られるよう、ZIP の中身を展開した状態で置いています。

※ `.md` ファイルは VS Code 等のエディタで開き、プレビュー表示（Ctrl+Shift+V）にすると見やすくなります。
