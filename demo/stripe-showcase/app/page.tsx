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
    <main className="mx-auto flex min-h-screen w-full max-w-6xl flex-col px-6 py-12 md:px-10 md:py-16">
      <section className="glass rounded-3xl p-5 md:p-7">
        <header className="mb-6">
          <h1 className="font-heading title-glow text-3xl font-black md:text-4xl">Choose your plan</h1>
        </header>

        <div className="grid gap-4 md:grid-cols-2">
          {plans.map((plan) => (
            <article
              key={plan.id}
              className="flex h-full flex-col rounded-2xl border border-cyan-200/20 bg-[#071325]/70 p-5 md:p-6"
            >
              <div className="mb-3 flex items-start justify-between gap-3">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.16em] text-cyan-300">
                    {plan.kicker}
                  </p>
                  <h2 className="font-heading mt-2 text-3xl font-black">{plan.title}</h2>
                </div>
                {plan.badge ? (
                  <span className="rounded-full border border-emerald-300/40 bg-emerald-300/10 px-3 py-1 text-[11px] font-bold uppercase tracking-[0.12em] text-emerald-100">
                    {plan.badge}
                  </span>
                ) : null}
              </div>

              <p className="mt-1 text-4xl font-black text-white">{plan.price}</p>
              <p className="fine mt-2 min-h-10 text-sm">{plan.note}</p>

              <ul className="mt-5 space-y-2 text-sm">
                {plan.points.map((point) => (
                  <li key={point} className="rounded-xl border border-sky-200/15 bg-[#081729]/70 px-3 py-2">
                    {point}
                  </li>
                ))}
              </ul>

              <form action="/api/checkout" method="post" className="mt-auto pt-6">
                <input type="hidden" name="planId" value={plan.id} />
                <button
                  type="submit"
                  className="w-full rounded-full bg-cyan-300 px-4 py-3 text-sm font-black text-[#032029] transition hover:bg-cyan-200"
                >
                  {plan.label}プランでテスト決済
                </button>
              </form>
            </article>
          ))}
        </div>
      </section>

      <footer className="mt-auto flex justify-center pb-4 pt-16 md:pt-20">
        <Link
          href="/events"
          className="text-[11px] font-medium tracking-[0.12em] text-slate-300/45 underline decoration-slate-300/20 underline-offset-4 transition hover:text-slate-200/70 hover:decoration-slate-200/40"
        >
          webhook logs
        </Link>
      </footer>
    </main>
  );
}
