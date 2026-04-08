# Claude 版: bugfix-15000 サムネイル生成プロンプト

## 1. 画像生成プロンプト（英語）

```
Create a square service listing thumbnail image (1220x1240 pixels) for a Japanese freelance marketplace.

LAYOUT:
- All text is vertically centered in the image (not pushed to the top half)
- Left-aligned text with generous left margin (about 12% from edge)
- Right side has subtle decorative space

TEXT (must be rendered exactly as written, in Japanese):
- Line 1 (small, above main text): "Next.js / Stripe"
  → Font: thin-weight sans-serif, tracking slightly wide, white with 70% opacity
  → Size: roughly 1/3 of the main text height

- Line 2 (main, largest): "不具合診断・修正"
  → Font: heavy-weight Japanese gothic (sans-serif), pure white, full opacity
  → This text must occupy approximately 45-50% of the image width
  → This is the most important element — it must be readable even when the image is shrunk to 150px wide

- Line 3 (small, below main text): "原因不明でも対応"
  → Font: medium-weight sans-serif, a muted soft teal/cyan color (#6BBFB0 or similar)
  → Size: roughly 1/3 of the main text height
  → Subtle but readable

BACKGROUND:
- Deep charcoal-navy gradient, slightly lighter at the center-left where text sits, darker at edges
- NOT pure black. NOT bright blue. Think: #1a1f2e to #0d1117 range
- Very subtle, barely visible geometric pattern on the right side only:
  thin-line hexagonal grid or circuit-board traces, in slightly lighter shade (#ffffff at 4-6% opacity)
- The pattern should NOT compete with the text — it's atmospheric texture only

VISUAL ACCENT:
- A single thin horizontal line or subtle divider between Line 1 and Line 2
  (very faint, white at 15-20% opacity, about 40% of image width)
- This creates visual breathing room and sophistication

OVERALL FEEL:
- Premium, understated, trustworthy
- Like a high-end SaaS product page, not a marketplace ad
- Clean negative space on the right and bottom-right, balanced by the faint geometric pattern
- The viewer's eye should go: Line 2 (main) → Line 1 (context) → Line 3 (reassurance)

DO NOT INCLUDE:
- Any photos, people, illustrations, icons, or emoji
- Any badges, stars, rankings, or decorative borders
- Any price information
- Any text other than the three lines specified above
- Any bright or saturated accent colors
```

## 2. ネガティブプロンプト

```
photo, photograph, person, face, hand, illustration, icon, emoji, badge, star, ranking, border, frame, watermark, price, yen symbol, bright colors, neon, gradient rainbow, 3D render, cartoon, clipart, stock photo, busy background, cluttered, text shadow glow effect, lens flare, bokeh
```

## 3. なぜこの設計にしたか

```
設計判断の理由:

  背景: ダークネイビーは維持するが、微妙なグラデーションを入れた
    → 理由: 調査で「IT系は暗い画像だらけ」と分かった
    → 完全に色を変えると Quiet Luxury を壊す
    → グラデーション（中央が少し明るい）で「同じダークでも少し違う」を作る
    → テキスト周辺がわずかに明るくなることで可読性も向上する

  テキスト配置: 垂直方向で中央寄せ
    → 理由: 現画像の最大の問題は「下半分が空白」
    → 中央配置にすることで、150px幅に縮小しても
      テキストが画像の「真ん中」に来て目に入りやすい

  行2のサイズ: 画像幅の45-50%
    → 理由: 調査の「テキストが画像の40-60%を占めるべき」に準拠
    → 現画像は20-25%しかない → ほぼ2倍に拡大

  行3の色: ティール/シアン系（#6BBFB0）
    → 理由: 現画像の行3は青で背景に溶けていた
    → ティールは「解決」「安心」のイメージを持つ（色彩心理学）
    → ダークネイビー背景に対してティールは自然にコントラストが取れる
    → 派手ではないが、150px幅でも色の存在として認識できる

  幾何学パターン: 右側にのみ配置、極めて薄く
    → 理由: 現画像の六角形パターンは「技術系」の暗示として有効
    → ただし目立ちすぎるとテキストと競合する
    → 4-6% opacity まで下げてテクスチャとして扱う

  アクセントライン: 行1と行2の間に薄い水平線
    → 理由: Quiet Luxury の典型的なデザイン要素
    → 「区切り」ではなく「呼吸」を作る
    → 高級ブランドのカードや名刺で使われるテクニック
```

## 4. Codex 案との違い（予想）

```
おそらく Codex 案と異なるポイント:

  1. グラデーション背景
     → Codex はフラットな単色背景にしている可能性が高い
     → Claude 版は微妙なグラデーションで「同じダークでも少し上質」を狙った

  2. アクセントライン（水平線の区切り）
     → Codex は入れていない可能性が高い
     → Claude 版は Quiet Luxury のディテールとして追加

  3. 行3の色
     → Codex は白 or 現画像と同じ青の可能性
     → Claude 版はティール/シアン系で「安心」の暗示 + コントラスト確保

  4. 幾何学パターンの扱い
     → Codex はパターンを残す or 削除のどちらか
     → Claude 版は「残すが極限まで薄くする」（4-6% opacity）

  共通しているはずのポイント:
     - テキストの垂直中央配置
     - テキストサイズの大幅拡大
     - ダークカラー基調の維持
     - 3行構成の維持
```
