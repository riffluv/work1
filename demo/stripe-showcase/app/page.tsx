"use client";

import Link from "next/link";

type PlanId = "monthly" | "yearly";

const plans: {
  id: PlanId;
  label: string;
  kicker: string;
  title: string;
  price: string;
  note: string;
  points: string[];
  badge?: string;
}[] = [
  {
    id: "monthly",
    label: "月額",
    kicker: "Starter Billing",
    title: "Monthly Plan",
    price: "¥2,980 / 月",
    note: "短期利用向け。まずは小さく始めるプラン。",
    points: [
      "Stripe Checkoutによるサブスク開始",
      "Webhookで契約状態を同期",
      "キャンセル導線をCustomer Portalで提供",
    ],
  },
  {
    id: "yearly",
    label: "年額",
    kicker: "Growth Billing",
    title: "Yearly Plan",
    price: "¥29,800 / 年",
    note: "年額は2か月分お得。継続利用を想定したプラン。",
    points: [
      "年額決済の一括請求フロー",
      "Webhook再送時の重複処理対策",
      "契約更新を見据えた運用導線",
    ],
    badge: "Popular",
  },
];

export default function HomePage() {
  return (
    <main className="mx-auto flex min-h-screen w-full max-w-5xl flex-col px-6 py-12 md:px-10 md:py-16">
      <header className="mb-10 text-center">
        <h1
          className="font-heading text-3xl font-black tracking-tight md:text-4xl"
          style={{ color: "var(--foreground)" }}
        >
          Choose your plan
        </h1>
      </header>

      <div className="grid gap-6 md:grid-cols-2">
        {plans.map((plan) => (
          <article key={plan.id} className="glass flex h-full flex-col p-6 md:p-7">
            {/* ヘッダー: プラン名 + バッジ */}
            <div className="mb-4 flex items-start justify-between gap-3">
              <div>
                <h2
                  className="font-heading text-xl font-bold"
                  style={{ color: "var(--accent)" }}
                >
                  {plan.title}
                </h2>
                <p className="mt-0.5 text-xs" style={{ color: "var(--muted)" }}>
                  {plan.kicker}
                </p>
              </div>
              {plan.badge ? (
                <span
                  className="flex items-center gap-1.5 rounded-full px-3 py-1 text-[11px] font-semibold"
                  style={{
                    background: "var(--badge-bg)",
                    color: "var(--accent)",
                    border: "1px solid var(--badge-border)",
                  }}
                >
                  <span style={{ fontSize: "10px" }}>★</span>
                  {plan.badge}
                </span>
              ) : null}
            </div>

            {/* 価格 */}
            <p className="text-3xl font-black" style={{ color: "var(--foreground)" }}>
              {plan.price}
            </p>
            <p className="mt-2 min-h-10 text-sm" style={{ color: "var(--muted)" }}>
              {plan.note}
            </p>

            {/* CTA ボタン */}
            <form action="/api/checkout" method="post" className="mt-5">
              <input type="hidden" name="planId" value={plan.id} />
              <button
                type="submit"
                className="cta-btn w-full cursor-pointer rounded-xl px-4 py-3 text-sm font-bold"
              >
                {plan.label}プランでテスト決済
              </button>
            </form>

            {/* 機能リスト */}
            <ul className="mt-6 space-y-3 text-sm">
              {plan.points.map((point) => (
                <li
                  key={point}
                  className="flex items-start gap-2.5"
                  style={{ color: "var(--foreground)" }}
                >
                  <span
                    className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-md text-[11px]"
                    style={{
                      background: "var(--feature-icon-bg)",
                      color: "var(--accent)",
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
      <footer className="mt-auto flex justify-center pb-4 pt-16 md:pt-20">
        <Link
          href="/events"
          className="text-xs font-medium underline underline-offset-4 transition"
          style={{
            color: "var(--muted)",
            textDecorationColor: "rgba(142, 142, 154, 0.3)",
          }}
        >
          webhook logs
        </Link>
      </footer>
    </main>
  );
}
