"use client";

import Link from "next/link";

type PlanId = "monthly" | "yearly";

const plans: {
  id: PlanId;
  title: string;
  price: string;
  note: string;
  points: string[];
}[] = [
  {
    id: "monthly",
    title: "Standard",
    price: "¥2,980",
    note: "標準金額の単発決済フローを確認できます。",
    points: [
      "Stripe Checkoutで単発決済を実行",
      "テストカードで決済フローを検証",
      "success / cancel画面の遷移を確認",
      "session_id付きで結果画面へ戻る",
      "Webhook受信イベントをサーバーへ記録",
      "イベントログ画面で受信結果を確認",
    ],
  },
  {
    id: "yearly",
    title: "Premium",
    price: "¥29,800",
    note: "高額決済パターンの挙動を確認できます。",
    points: [
      "高額金額でCheckout決済を実行",
      "metadata(planId / planName) を送信",
      "success / cancel画面の遷移を確認",
      "Webhook受信イベントをサーバーへ記録",
      "イベントログ画面で受信結果を確認",
      "高額決済時の表示と導線を確認",
    ],
  },
];

export default function HomePage() {
  return (
    <main className="mx-auto flex min-h-screen w-full max-w-5xl flex-col px-6 py-10 md:px-10 md:py-12">
      <header className="mb-8 text-center">
        <h1
          className="font-heading text-2xl font-semibold tracking-tight md:text-3xl"
          style={{ color: "var(--foreground)" }}
        >
          Checkout Patterns
        </h1>
        <p className="mt-2 text-xs" style={{ color: "var(--muted)" }}>
          Stripe Checkout → Webhook受信の動作確認
        </p>
      </header>

      <div className="mx-auto grid w-full max-w-[780px] gap-5 md:grid-cols-2">
        {plans.map((plan) => (
          <article
            key={plan.id}
            className="glass flex h-full w-full flex-col overflow-hidden"
          >
            {/* 上部ブロック: タイトル・価格・説明・CTA */}
            <div className="card-header flex flex-col px-5 pb-5 pt-5">
              <div className="mb-3">
                <h2
                  className="font-heading text-lg font-semibold"
                  style={{ color: "var(--foreground)" }}
                >
                  {plan.title}
                </h2>
              </div>

              <p
                className="mb-3 text-xs leading-relaxed"
                style={{ color: "var(--muted)" }}
              >
                {plan.note}
              </p>

              <p
                className="mb-4 text-2xl font-bold"
                style={{ color: "var(--foreground)" }}
              >
                {plan.price}
              </p>

              {/* CTA ボタン */}
              <form action="/api/checkout" method="post">
                <input type="hidden" name="planId" value={plan.id} />
                <button
                  type="submit"
                  className="cta-btn w-full rounded-xl px-4 py-2.5 text-sm font-semibold"
                >
                  決済を試す
                </button>
              </form>
            </div>

            {/* 下部ブロック: 機能リスト */}
            <ul className="flex-1 space-y-2 px-5 pb-5 pt-4 text-[13px]">
              {plan.points.map((point) => (
                <li
                  key={point}
                  className="flex items-start gap-2"
                  style={{ color: "var(--foreground)" }}
                >
                  <span
                    className="mt-[2px] flex h-4 w-4 shrink-0 items-center justify-center rounded text-[10px] font-bold"
                    style={{
                      background: "var(--feature-icon-bg)",
                      color: "var(--feature-icon-color)",
                    }}
                  >
                    ✓
                  </span>
                  {point}
                </li>
              ))}
            </ul>
          </article>
        ))}
      </div>

      {/* Webhookログリンク */}
      <footer className="mt-auto flex justify-center pb-4 pt-10 md:pt-12">
        <Link
          href="/events"
          className="cursor-pointer text-xs font-medium underline underline-offset-4 transition-colors"
          style={{
            color: "var(--muted)",
            textDecorationColor: "var(--line)",
          }}
        >
          webhook logs
        </Link>
      </footer>
    </main>
  );
}
