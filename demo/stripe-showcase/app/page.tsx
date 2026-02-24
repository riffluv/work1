"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

type CheckoutMode = "payment" | "subscription";
type PlanId = "standard" | "premium" | "monthly" | "yearly";

type Plan = {
  id: PlanId;
  title: string;
  price: string;
  note: string;
  points: string[];
  isPopular?: boolean;
};

const modeMeta: Record<CheckoutMode, { title: string; subtitle: string }> = {
  payment: {
    title: "Checkout Patterns",
    subtitle: "Stripe Checkout（単発決済）→ Webhook受信の動作確認",
  },
  subscription: {
    title: "Subscription Patterns",
    subtitle: "Stripe Checkout（定期決済）→ Webhook受信の動作確認",
  },
};

const paymentPlans: Plan[] = [
  {
    id: "standard",
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
    id: "premium",
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
    isPopular: true,
  },
];

const subscriptionPlans: Plan[] = [
  {
    id: "monthly",
    title: "Monthly",
    price: "¥2,980 / 月",
    note: "月額サブスクの初回決済フローを確認できます。",
    points: [
      "Checkoutでサブスクを開始",
      "Webhookで課金イベントを受信",
      "success画面で契約状態を確認",
      "同一プランの再購入導線を確認",
      "イベントログ画面で受信結果を確認",
      "運用時の確認手順をテンプレ化",
    ],
  },
  {
    id: "yearly",
    title: "Yearly",
    price: "¥29,800 / 年",
    note: "年額サブスクの決済パターンを確認できます。",
    points: [
      "Checkoutで年額サブスクを開始",
      "Webhookで課金イベントを受信",
      "metadata(planId / planName) を送信",
      "success / cancel画面の遷移を確認",
      "イベントログ画面で受信結果を確認",
      "年額プランの導線表示を確認",
    ],
    isPopular: true,
  },
];

function resolveMode(rawMode: string | null): CheckoutMode {
  return rawMode === "subscription" ? "subscription" : "payment";
}

export default function HomePage() {
  const [mode, setMode] = useState<CheckoutMode>("payment");
  const plans = mode === "subscription" ? subscriptionPlans : paymentPlans;
  const header = modeMeta[mode];

  useEffect(() => {
    if (typeof window === "undefined") return;
    const params = new URLSearchParams(window.location.search);
    setMode(resolveMode(params.get("mode")));
  }, []);

  const handleModeChange = (nextMode: CheckoutMode) => {
    if (nextMode === mode) return;
    setMode(nextMode);
    const params = new URLSearchParams(window.location.search);
    params.set("mode", nextMode);
    const query = params.toString();
    const nextUrl = query ? `/?${query}` : "/";
    window.history.replaceState(null, "", nextUrl);
  };

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-5xl flex-col px-6 py-8 md:px-10 md:py-10">
      <header className="mb-8 text-center md:mb-10">
        <h1
          className="font-heading text-2xl font-bold tracking-tight md:text-3xl"
          style={{ color: "var(--foreground)" }}
        >
          {header.title}
        </h1>
        <p className="mt-2 text-xs font-medium md:text-sm" style={{ color: "var(--muted)" }}>
          {header.subtitle}
        </p>

        <div 
          className="mt-5 mx-auto inline-flex rounded-full border p-1" 
          style={{ borderColor: "var(--line)", background: "var(--card-header)" }}
        >
          <button
            type="button"
            onClick={() => handleModeChange("payment")}
            className="rounded-full px-4 py-1.5 text-xs font-semibold transition-all duration-200 md:px-5 md:py-2 md:text-sm"
            style={{
              background: mode === "payment" ? "var(--btn-bg)" : "transparent",
              color: mode === "payment" ? "var(--btn-text)" : "var(--muted)",
              boxShadow: mode === "payment" ? "0 2px 4px rgba(0,0,0,0.1)" : "none",
            }}
          >
            One-time
          </button>
          <button
            type="button"
            onClick={() => handleModeChange("subscription")}
            className="rounded-full px-4 py-1.5 text-xs font-semibold transition-all duration-200 md:px-5 md:py-2 md:text-sm"
            style={{
              background: mode === "subscription" ? "var(--btn-bg)" : "transparent",
              color: mode === "subscription" ? "var(--btn-text)" : "var(--muted)",
              boxShadow: mode === "subscription" ? "0 2px 4px rgba(0,0,0,0.1)" : "none",
            }}
          >
            Subscription
          </button>
        </div>
      </header>

      <div className="mx-auto grid w-full max-w-[900px] gap-5 md:grid-cols-2 md:gap-6">
        {plans.map((plan) => (
          <article
            key={plan.id}
            className="glass relative flex h-full w-full flex-col overflow-hidden border transition-all duration-300 hover:-translate-y-1 hover:shadow-2xl"
            style={{ borderColor: "var(--line)" }}
          >
            <div className="card-header flex flex-col px-6 py-6 md:px-7 md:py-7">
              <h2
                className="font-heading text-lg font-bold tracking-tight md:text-xl"
                style={{ color: "var(--foreground)" }}
              >
                {plan.title}
              </h2>

              <p
                className="mt-2 min-h-[38px] text-[12px] leading-relaxed md:text-[13px]"
                style={{ color: "var(--muted)" }}
              >
                {plan.note}
              </p>

              <div className="mt-5 flex items-baseline gap-1">
                {(() => {
                  const [amount, period] = plan.price.split(" / ");
                  return (
                    <>
                      <span
                        className="text-3xl font-extrabold tracking-tight md:text-4xl"
                        style={{ color: "var(--foreground)" }}
                      >
                        {amount}
                      </span>
                      {period && (
                        <span
                          className="ml-1 text-xs font-medium md:text-sm"
                          style={{ color: "var(--muted)" }}
                        >
                          / {period}
                        </span>
                      )}
                    </>
                  );
                })()}
              </div>
            </div>

            <div className="flex flex-1 flex-col p-6 md:p-7">
              <div
                className="mb-4 text-[10px] font-bold uppercase tracking-wider"
                style={{ color: "var(--foreground)" }}
              >
                含まれる機能
              </div>

              <ul className="flex-1 space-y-2.5 md:space-y-3">
                {plan.points.map((point) => (
                  <li
                    key={point}
                    className="flex items-start gap-3"
                    style={{ color: "var(--foreground)" }}
                  >
                    <span
                      className="mt-[1px] flex h-[18px] w-[18px] shrink-0 items-center justify-center rounded-full text-[10px] font-bold"
                      style={{
                        background: plan.isPopular ? "var(--btn-bg)" : "var(--feature-icon-bg)",
                        color: plan.isPopular ? "var(--btn-text)" : "var(--feature-icon-color)",
                      }}
                    >
                      ✓
                    </span>
                    <span className="text-[12px] leading-relaxed md:text-[13px]">{point}</span>
                  </li>
                ))}
              </ul>

              <div className="mt-6 pt-2">
                <form action="/api/checkout" method="post" className="w-full">
                  <input type="hidden" name="planId" value={plan.id} />
                  <input type="hidden" name="mode" value={mode} />
                  <button
                    type="submit"
                    className="w-full rounded-xl px-4 py-3 text-sm font-bold transition-all cta-btn"
                  >
                    決済へ進む
                  </button>
                </form>
              </div>
            </div>
          </article>
        ))}
      </div>

      <footer className="mt-8 flex justify-center pb-3 md:pb-4">
        <Link
          href="/events"
          className="cursor-pointer text-xs font-medium underline underline-offset-4 transition-colors hover:opacity-70"
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
