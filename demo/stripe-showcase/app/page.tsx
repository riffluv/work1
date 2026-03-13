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
    <main
      style={{
        maxWidth: "960px",
        margin: "0 auto",
        padding: "48px clamp(20px, 4vw, 40px)",
        minHeight: "100vh",
        display: "flex",
        flexDirection: "column",
      }}
    >
      {/* ── ヘッダー ── */}
      <header className="animate-in stagger-1" style={{ marginBottom: "48px" }}>
        <h1
          style={{
            fontFamily: "var(--font-heading), sans-serif",
            fontSize: "clamp(1.5rem, 1.3rem + 1vw, 2rem)",
            fontWeight: 700,
            letterSpacing: "-0.02em",
            color: "var(--foreground)",
            margin: 0,
          }}
        >
          {header.title}
        </h1>

        <p
          style={{
            fontSize: "13px",
            color: "var(--muted)",
            marginTop: "8px",
            lineHeight: 1.6,
          }}
        >
          {header.subtitle}
        </p>

        {/* モード切替 — テキストタブ */}
        <nav
          className="animate-in stagger-2"
          style={{
            display: "flex",
            gap: "24px",
            marginTop: "28px",
            borderBottom: "1px solid var(--line)",
            paddingBottom: "0",
          }}
        >
          {(["payment", "subscription"] as CheckoutMode[]).map((m) => (
            <button
              key={m}
              type="button"
              onClick={() => handleModeChange(m)}
              style={{
                background: "none",
                border: "none",
                padding: "8px 0",
                fontSize: "13px",
                fontWeight: mode === m ? 700 : 500,
                color: mode === m ? "var(--foreground)" : "var(--muted)",
                borderBottom: mode === m
                  ? "2px solid var(--foreground)"
                  : "2px solid transparent",
                marginBottom: "-1px",
                transition: "color 0.2s var(--ease-out-quart), border-color 0.2s var(--ease-out-quart)",
                cursor: "pointer",
                fontFamily: "var(--font-heading), sans-serif",
              }}
            >
              {m === "payment" ? "One-time" : "Subscription"}
            </button>
          ))}
        </nav>
      </header>

      {/* ── プラン一覧 ── */}
      <div
        className="animate-in stagger-3"
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 360px), 1fr))",
          gap: "40px",
          flex: 1,
        }}
      >
        {plans.map((plan) => {
          const [amount, period] = plan.price.split(" / ");
          return (
            <article
              key={plan.id}
              style={{ display: "flex", flexDirection: "column" }}
            >
              {/* バッジ行 — 高さを常に確保して段ズレを防ぐ */}
              <div style={{ minHeight: "28px", marginBottom: "8px" }}>
                {plan.isPopular && (
                  <span className="badge-pill">
                    Popular
                  </span>
                )}
              </div>

              {/* プランタイトル */}
              <h2
                style={{
                  fontFamily: "var(--font-heading), sans-serif",
                  fontSize: "18px",
                  fontWeight: 700,
                  color: "var(--foreground)",
                  letterSpacing: "-0.01em",
                  margin: 0,
                }}
              >
                {plan.title}
              </h2>

              {/* 説明 */}
              <p
                style={{
                  fontSize: "12px",
                  color: "var(--muted)",
                  lineHeight: 1.7,
                  marginTop: "8px",
                }}
              >
                {plan.note}
              </p>

              {/* 金額 */}
              <div
                className="price-display"
                style={{
                  display: "flex",
                  alignItems: "baseline",
                  gap: "4px",
                  marginTop: "16px",
                }}
              >
                <span
                  style={{
                    fontFamily: "var(--font-heading), sans-serif",
                    fontSize: "clamp(1.6rem, 1.4rem + 1vw, 2.2rem)",
                    fontWeight: 800,
                    color: "var(--foreground)",
                    letterSpacing: "-0.02em",
                    lineHeight: 1,
                  }}
                >
                  {amount}
                </span>
                {period && (
                  <span
                    style={{
                      fontSize: "13px",
                      fontWeight: 500,
                      color: "var(--muted)",
                    }}
                  >
                    / {period}
                  </span>
                )}
              </div>

              {/* CTA */}
              <div style={{ marginTop: "20px" }}>
                <form action="/api/checkout" method="post">
                  <input type="hidden" name="planId" value={plan.id} />
                  <input type="hidden" name="mode" value={mode} />
                  <button
                    type="submit"
                    className="cta-btn"
                    style={{
                      width: "100%",
                      padding: "12px 20px",
                      fontSize: "13px",
                      fontFamily: "var(--font-heading), sans-serif",
                      borderRadius: "8px",
                    }}
                  >
                    決済へ進む
                  </button>
                </form>
              </div>

              {/* 区切り線 */}
              <hr className="editorial-divider" style={{ margin: "24px 0" }} />

              {/* 含まれる機能 */}
              <div
                style={{
                  fontSize: "10px",
                  fontWeight: 700,
                  textTransform: "uppercase",
                  letterSpacing: "0.08em",
                  color: "var(--foreground)",
                  marginBottom: "14px",
                }}
              >
                含まれる機能
              </div>

              <ul
                style={{
                  listStyle: "none",
                  padding: 0,
                  margin: 0,
                  display: "flex",
                  flexDirection: "column",
                  gap: "10px",
                  flex: 1,
                }}
              >
                {plan.points.map((point) => (
                  <li
                    key={point}
                    style={{
                      display: "flex",
                      alignItems: "flex-start",
                      gap: "10px",
                      fontSize: "12px",
                      color: "var(--foreground)",
                      lineHeight: 1.6,
                    }}
                  >
                    <span
                      style={{
                        display: "inline-flex",
                        alignItems: "center",
                        justifyContent: "center",
                        width: "16px",
                        height: "16px",
                        borderRadius: "50%",
                        fontSize: "9px",
                        fontWeight: 700,
                        marginTop: "2px",
                        flexShrink: 0,
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
          );
        })}
      </div>

      {/* ── フッター ── */}
      <footer
        className="animate-in stagger-4"
        style={{
          marginTop: "56px",
          paddingTop: "20px",
          borderTop: "1px solid var(--line)",
          textAlign: "center",
        }}
      >
        <Link
          href="/events"
          style={{
            fontSize: "12px",
            fontWeight: 500,
            color: "var(--muted)",
            textDecoration: "underline",
            textUnderlineOffset: "4px",
            textDecorationColor: "var(--line)",
            transition: "color 0.2s var(--ease-out-quart)",
          }}
          onMouseEnter={(e) => (e.currentTarget.style.color = "var(--foreground)")}
          onMouseLeave={(e) => (e.currentTarget.style.color = "var(--muted)")}
        >
          webhook logs
        </Link>
      </footer>
    </main>
  );
}
