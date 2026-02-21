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
    <main className="mx-auto min-h-screen w-full max-w-4xl px-6 py-12 md:px-10">
      <section className="glass p-6 md:p-8">
        <p className="mb-2 text-xs font-semibold uppercase tracking-widest"
           style={{ color: "var(--success)" }}>
          Payment Complete
        </p>
        <h1 className="font-heading text-3xl font-semibold md:text-4xl"
            style={{ color: "var(--foreground)" }}>
          決済が完了しました
        </h1>
        <p className="fine mt-3 text-sm md:text-base">
          決済情報を確認しました。詳細を確認してください。
        </p>

        <div className="mt-6 grid gap-3 rounded-lg p-4 text-sm"
             style={{
               background: "var(--feature-icon-bg)",
               border: "1px solid var(--line)",
             }}>
          {errorMessage ? (
            <p style={{ color: "var(--warning)" }}>{errorMessage}</p>
          ) : (
            <>
              <p><span className="fine">Session ID:</span> {summary?.id ?? sessionId ?? "-"}</p>
              <p><span className="fine">Plan:</span> {summary?.planName ?? "-"}</p>
              <p><span className="fine">Mode:</span> {summary?.mode ?? "-"}</p>
              <p><span className="fine">Amount:</span> {formatYen(summary?.amountTotal)}</p>
              <p><span className="fine">Email:</span> {summary?.email ?? "-"}</p>
              <p><span className="fine">Status:</span> {summary?.status ?? "unknown"}</p>
            </>
          )}
        </div>

        <div className="mt-6 flex flex-wrap gap-3">
          {summary?.mode === "subscription" && sessionId ? (
            <form action="/api/portal" method="post">
              <input type="hidden" name="sessionId" value={sessionId} />
              <button
                type="submit"
                className="cta-btn cursor-pointer rounded-lg px-5 py-2.5 text-sm font-semibold"
              >
                契約を管理
              </button>
            </form>
          ) : null}
          <Link href="/events" className="cta-btn cursor-pointer rounded-lg px-5 py-2.5 text-sm font-semibold">
            Webhookログ
          </Link>
          <Link
            href="/"
            className="cursor-pointer rounded-lg px-5 py-2.5 text-sm font-semibold transition-colors"
            style={{ border: "1px solid var(--line)", color: "var(--foreground)" }}
          >
            プランへ戻る
          </Link>
        </div>
      </section>
    </main>
  );
}
