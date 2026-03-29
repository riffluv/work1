#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
LIVE_FILE="$ROOT_DIR/サービスページ/bugfix-15000.live.txt"
DOC_FILE="$ROOT_DIR/docs/coconala-listing-final.ja.md"

if [ ! -f "$LIVE_FILE" ]; then
  echo "[NG] 一次ソースが見つかりません: $LIVE_FILE"
  exit 1
fi

if [ ! -f "$DOC_FILE" ]; then
  echo "[NG] 同期ミラーが見つかりません: $DOC_FILE"
  exit 1
fi

extract_listing_payload() {
  sed -n '/^現在のサービス商品ページ$/,$p' "$1"
}

normalize_payload() {
  sed -e 's/[[:space:]]\+$//' \
    | awk 'NF { print; blank = 0; next } !NF { if (blank == 0) print ""; blank = 1 }'
}

live_tmp="$(mktemp)"
doc_tmp="$(mktemp)"
trap 'rm -f "$live_tmp" "$doc_tmp"' EXIT

extract_listing_payload "$LIVE_FILE" | normalize_payload > "$live_tmp"
extract_listing_payload "$DOC_FILE" | normalize_payload > "$doc_tmp"

if diff -u "$live_tmp" "$doc_tmp" > /dev/null; then
  echo "[OK] 同期一致: docs/coconala-listing-final.ja.md"
else
  echo "[NG] 同期不一致: 一次ソースと docs/coconala-listing-final.ja.md に差分があります"
  diff -u "$live_tmp" "$doc_tmp" || true
  exit 1
fi

service_chars="$({
  # ココナラUIの体感値に合わせ、末尾の空行/改行はカウントから除外する。
  awk 'BEGIN{flag=0} /^サービス内容$/{flag=1;next} /^予想お届け日数/{flag=0} flag{print}' "$LIVE_FILE" \
    | perl -0777 -pe 's/(?:\n[ \t]*)+\z//' \
    | wc -m
} | awk '{print $1}')"

if [ -z "$service_chars" ]; then
  echo "[NG] サービス内容の文字数を取得できませんでした"
  exit 1
fi

echo "[INFO] サービス内容文字数: ${service_chars} / 1000"
if [ "$service_chars" -gt 1000 ]; then
  echo "[NG] サービス内容が1000文字を超えています"
  exit 1
fi

if grep -q '^見積りにあたってのお願い※任意 (200字以内)$' "$LIVE_FILE"; then
  estimate_chars="$({
    awk 'BEGIN{flag=0} /^見積りにあたってのお願い※任意 \(200字以内\)$/{flag=1; next} /^[[:space:]]*【トークルーム回答例1】$/{flag=0} flag{print}' "$LIVE_FILE" \
      | sed '/^$/d' | tr -d '\n' | wc -m
  } | awk '{print $1}')"

  echo "[INFO] 見積り任意欄文字数: ${estimate_chars} / 200"
  if [ "$estimate_chars" -gt 200 ]; then
    echo "[NG] 見積り任意欄が200文字を超えています"
    exit 1
  fi
fi

echo "[OK] チェック完了"
