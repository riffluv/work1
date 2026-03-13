import { formatYen, getStripe } from "@/lib/stripe";
import Link from "next/link";

type SuccessPageProps = {
  searchParams: Promise<{ session_id?: string }>;
};

async function fetchSessionSummary(sessionId: string) {
  const stripe = getStripe();
  const session = await stripe.checkout.sessions.retrieve(sessionId);

  return {
    id: session.id,
    amountTotal: session.amount_total,
    currency: session.currency,
    email: session.customer_details?.email ?? session.customer_email ?? null,
    status: session.payment_status,
    mode: session.metadata?.mode ?? "-",
    planName: session.metadata?.planName ?? "-",
  };
}

/* ラベル+値 行 */
function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div
      style={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "baseline",
        padding: "12px 0",
        borderBottom: "1px solid var(--line)",
        gap: "16px",
      }}
    >
      <dt
        style={{
          fontSize: "11px",
          fontWeight: 500,
          color: "var(--muted)",
          letterSpacing: "0.04em",
          textTransform: "uppercase",
          flexShrink: 0,
        }}
      >
        {label}
      </dt>
      <dd
        style={{
          fontSize: "13px",
          fontWeight: 600,
          color: "var(--foreground)",
          margin: 0,
          textAlign: "right",
          wordBreak: "break-all",
        }}
      >
        {value}
      </dd>
    </div>
  );
}

export default async function SuccessPage({ searchParams }: SuccessPageProps) {
  const { session_id: sessionId } = await searchParams;
  let summary: Awaited<ReturnType<typeof fetchSessionSummary>> | null = null;
  let errorMessage: string | null = null;

  if (sessionId) {
    try {
      summary = await fetchSessionSummary(sessionId);
    } catch {
      errorMessage = "セッション情報の取得に失敗しました。キー設定を確認してください。";
    }
  }

  return (
    <main
      style={{
        maxWidth: "640px",
        margin: "0 auto",
        padding: "clamp(40px, 6vw, 72px) clamp(20px, 4vw, 40px)",
        minHeight: "100vh",
      }}
    >
      <p
        className="animate-in stagger-1"
        style={{
          fontSize: "11px",
          fontWeight: 600,
          letterSpacing: "0.1em",
          textTransform: "uppercase",
          color: "var(--success)",
          marginBottom: "8px",
        }}
      >
        Payment Complete
      </p>

      <h1
        className="animate-in stagger-1"
        style={{
          fontFamily: "var(--font-heading), sans-serif",
          fontSize: "clamp(1.3rem, 1.1rem + 1vw, 1.8rem)",
          fontWeight: 700,
          letterSpacing: "-0.02em",
          color: "var(--foreground)",
          margin: 0,
        }}
      >
        決済が完了しました
      </h1>

      <p
        className="animate-in stagger-2"
        style={{
          fontSize: "13px",
          color: "var(--muted)",
          marginTop: "8px",
          lineHeight: 1.6,
        }}
      >
        決済情報を確認しました。詳細を確認してください。
      </p>

      <dl
        className="animate-in stagger-3"
        style={{
          marginTop: "32px",
          borderTop: "1px solid var(--line)",
        }}
      >
        {errorMessage ? (
          <p style={{ color: "var(--warning)", fontSize: "13px", padding: "12px 0" }}>
            {errorMessage}
          </p>
        ) : (
          <>
            <InfoRow label="Session ID" value={summary?.id ?? sessionId ?? "-"} />
            <InfoRow label="Plan" value={summary?.planName ?? "-"} />
            <InfoRow label="Mode" value={summary?.mode ?? "-"} />
            <InfoRow label="Amount" value={formatYen(summary?.amountTotal)} />
            <InfoRow label="Email" value={summary?.email ?? "-"} />
            <InfoRow label="Status" value={summary?.status ?? "unknown"} />
          </>
        )}
      </dl>

      <div
        className="animate-in stagger-4"
        style={{
          display: "flex",
          flexWrap: "wrap",
          gap: "10px",
          marginTop: "32px",
        }}
      >
        {summary?.mode === "subscription" && sessionId ? (
          <form action="/api/portal" method="post">
            <input type="hidden" name="sessionId" value={sessionId} />
            <button
              type="submit"
              className="cta-btn"
              style={{
                padding: "10px 20px",
                fontSize: "13px",
                fontFamily: "var(--font-heading), sans-serif",
                borderRadius: "8px",
              }}
            >
              契約を管理
            </button>
          </form>
        ) : null}
        <Link
          href="/events"
          className="cta-btn"
          style={{
            padding: "10px 20px",
            fontSize: "13px",
            fontFamily: "var(--font-heading), sans-serif",
            borderRadius: "8px",
            textDecoration: "none",
          }}
        >
          Webhookログ
        </Link>
        <Link
          href="/"
          className="cta-btn-outline"
          style={{
            padding: "10px 20px",
            fontSize: "13px",
            fontFamily: "var(--font-heading), sans-serif",
            borderRadius: "8px",
            textDecoration: "none",
          }}
        >
          プランへ戻る
        </Link>
      </div>
    </main>
  );
}
