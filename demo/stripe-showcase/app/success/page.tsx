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
      <section className="glass rounded-2xl p-6 md:p-8">
        <p className="mb-3 text-xs font-semibold uppercase tracking-[0.2em]"
           style={{ color: "var(--success)" }}>
          Payment Success
        </p>
        <h1 className="font-heading text-3xl font-extrabold md:text-4xl"
            style={{ color: "var(--foreground)" }}>
          決済が完了しました
        </h1>
        <p className="fine mt-3 text-sm md:text-base">
          ここで「決済成功」の証跡を撮影できます。Webhook到達はイベントログ画面で確認してください。
        </p>

        <div className="mt-6 grid gap-3 rounded-xl p-4 text-sm"
             style={{
               background: "rgba(39, 174, 96, 0.04)",
               border: "1px solid rgba(39, 174, 96, 0.15)",
             }}>
          {errorMessage ? (
            <p style={{ color: "var(--warning)" }}>{errorMessage}</p>
          ) : (
            <>
              <p>
                <span className="fine">Session ID:</span> {summary?.id ?? sessionId ?? "-"}
              </p>
              <p>
                <span className="fine">Plan:</span> {summary?.planName ?? "-"}
              </p>
              <p>
                <span className="fine">Amount:</span> {formatYen(summary?.amountTotal)}
              </p>
              <p>
                <span className="fine">Email:</span> {summary?.email ?? "-"}
              </p>
              <p>
                <span className="fine">Status:</span> {summary?.status ?? "unknown"}
              </p>
            </>
          )}
        </div>

        <div className="mt-6 flex flex-wrap gap-3">
          <Link
            href="/events"
            className="cta-btn rounded-xl px-5 py-2.5 text-sm font-bold"
          >
            Webhookログを確認
          </Link>
          <Link
            href="/"
            className="rounded-xl px-5 py-2.5 text-sm font-bold transition"
            style={{ border: "1px solid var(--line)", color: "var(--foreground)" }}
          >
            トップに戻る
          </Link>
        </div>
      </section>
    </main>
  );
}
