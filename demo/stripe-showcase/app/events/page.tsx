import { readWebhookEvents } from "@/lib/event-store";
import { formatYen } from "@/lib/stripe";
import Link from "next/link";

export const dynamic = "force-dynamic";

export default async function EventsPage() {
  const events = await readWebhookEvents();

  return (
    <main className="mx-auto min-h-screen w-full max-w-6xl px-6 py-12 md:px-10"
          style={{ color: "var(--foreground)" }}>
      <header className="mb-8 flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-widest"
             style={{ color: "var(--accent-gold)" }}>
            Webhook Monitor
          </p>
          <h1 className="font-heading text-3xl font-semibold md:text-4xl">受信イベントログ</h1>
          <p className="fine mt-2 text-sm">Stripe CLIから転送されたイベントを時系列で確認できます。</p>
        </div>
        <Link
          href="/"
          className="cursor-pointer rounded-lg px-4 py-2 text-sm font-semibold transition-colors"
          style={{ border: "1px solid var(--line)", color: "var(--foreground)" }}
        >
          トップへ戻る
        </Link>
      </header>

      <section className="glass p-5 md:p-7">
        {events.length === 0 ? (
          <p className="fine text-sm">
            まだイベントはありません。`stripe listen --forward-to localhost:3000/api/webhook` を起動してからテスト決済を実行してください。
          </p>
        ) : (
          <div className="space-y-4">
            {events.map((event) => (
              <article key={event.id} className="rounded-lg p-4"
                       style={{ background: "var(--feature-icon-bg)", border: "1px solid var(--line)" }}>
                <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
                  <p className="font-mono text-sm font-medium"
                     style={{ color: "var(--accent-gold)" }}>
                    {event.type}
                  </p>
                  <time className="fine text-xs">
                    {new Date(event.createdAt).toLocaleString("ja-JP")}
                  </time>
                </div>
                <dl className="grid grid-cols-1 gap-2 text-sm md:grid-cols-2">
                  <div>
                    <dt className="fine text-xs">Amount</dt>
                    <dd className="font-semibold">{formatYen(event.amountTotal)}</dd>
                  </div>
                  <div>
                    <dt className="fine text-xs">Customer Email</dt>
                    <dd className="font-semibold">{event.customerEmail ?? "-"}</dd>
                  </div>
                  <div>
                    <dt className="fine text-xs">Session ID</dt>
                    <dd className="break-all font-mono text-xs">{event.sessionId ?? "-"}</dd>
                  </div>
                  <div>
                    <dt className="fine text-xs">Event ID</dt>
                    <dd className="break-all font-mono text-xs">{event.id}</dd>
                  </div>
                </dl>
              </article>
            ))}
          </div>
        )}
      </section>
    </main>
  );
}
