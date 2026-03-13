import { readWebhookEvents } from "@/lib/event-store";
import { formatYen } from "@/lib/stripe";
import Link from "next/link";

export const dynamic = "force-dynamic";

export default async function EventsPage() {
  const events = await readWebhookEvents();

  return (
    <main
      style={{
        maxWidth: "860px",
        margin: "0 auto",
        padding: "48px clamp(20px, 4vw, 40px)",
        minHeight: "100vh",
        color: "var(--foreground)",
      }}
    >
      {/* ヘッダー */}
      <header
        className="animate-in stagger-1"
        style={{
          display: "flex",
          flexWrap: "wrap",
          justifyContent: "space-between",
          alignItems: "flex-end",
          gap: "16px",
          marginBottom: "32px",
          paddingBottom: "16px",
          borderBottom: "1px solid var(--line)",
        }}
      >
        <div>
          <p
            style={{
              fontSize: "11px",
              fontWeight: 600,
              letterSpacing: "0.1em",
              textTransform: "uppercase",
              color: "var(--accent)",
              marginBottom: "4px",
            }}
          >
            Webhook Monitor
          </p>
          <h1
            style={{
              fontFamily: "var(--font-heading), sans-serif",
              fontSize: "clamp(1.3rem, 1.1rem + 1vw, 1.8rem)",
              fontWeight: 700,
              letterSpacing: "-0.02em",
              margin: 0,
            }}
          >
            受信イベント
          </h1>
          <p style={{ fontSize: "13px", color: "var(--muted)", marginTop: "4px" }}>
            Webhook受信イベント一覧です。
          </p>
        </div>
        <Link
          href="/"
          className="cta-btn-outline"
          style={{
            padding: "8px 16px",
            fontSize: "12px",
            fontFamily: "var(--font-heading), sans-serif",
            borderRadius: "6px",
            textDecoration: "none",
          }}
        >
          プランへ戻る
        </Link>
      </header>

      {/* イベント一覧 */}
      <section className="animate-in stagger-2">
        {events.length === 0 ? (
          <p style={{ fontSize: "13px", color: "var(--muted)", padding: "32px 0" }}>
            イベントはまだありません。
          </p>
        ) : (
          <div style={{ display: "flex", flexDirection: "column" }}>
            {events.map((event) => (
              <article
                key={event.id}
                style={{
                  padding: "20px 0",
                  borderBottom: "1px solid var(--line)",
                }}
              >
                <div
                  style={{
                    display: "flex",
                    flexWrap: "wrap",
                    justifyContent: "space-between",
                    alignItems: "baseline",
                    gap: "12px",
                    marginBottom: "12px",
                  }}
                >
                  <p
                    style={{
                      fontSize: "13px",
                      fontWeight: 700,
                      fontFamily: "var(--font-heading), sans-serif",
                      color: "var(--accent)",
                      margin: 0,
                    }}
                  >
                    {event.type}
                  </p>
                  <time
                    style={{
                      fontSize: "11px",
                      color: "var(--muted)",
                      fontVariantNumeric: "tabular-nums",
                    }}
                  >
                    {new Date(event.createdAt).toLocaleString("ja-JP")}
                  </time>
                </div>

                <dl
                  style={{
                    display: "grid",
                    gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))",
                    gap: "12px",
                    margin: 0,
                  }}
                >
                  <div>
                    <dt style={{ fontSize: "10px", color: "var(--muted)", letterSpacing: "0.04em", textTransform: "uppercase" }}>
                      Amount
                    </dt>
                    <dd style={{ fontSize: "13px", fontWeight: 600, margin: "2px 0 0", fontVariantNumeric: "tabular-nums" }}>
                      {formatYen(event.amountTotal)}
                    </dd>
                  </div>
                  <div>
                    <dt style={{ fontSize: "10px", color: "var(--muted)", letterSpacing: "0.04em", textTransform: "uppercase" }}>
                      Customer Email
                    </dt>
                    <dd style={{ fontSize: "13px", fontWeight: 600, margin: "2px 0 0" }}>
                      {event.customerEmail ?? "-"}
                    </dd>
                  </div>
                  <div>
                    <dt style={{ fontSize: "10px", color: "var(--muted)", letterSpacing: "0.04em", textTransform: "uppercase" }}>
                      Plan
                    </dt>
                    <dd style={{ fontSize: "13px", fontWeight: 600, margin: "2px 0 0" }}>
                      {event.metadata?.planName ?? event.metadata?.planId ?? "-"}
                    </dd>
                  </div>
                  <div>
                    <dt style={{ fontSize: "10px", color: "var(--muted)", letterSpacing: "0.04em", textTransform: "uppercase" }}>
                      Mode
                    </dt>
                    <dd style={{ fontSize: "13px", fontWeight: 600, margin: "2px 0 0" }}>
                      {event.metadata?.mode ?? "-"}
                    </dd>
                  </div>
                  <div style={{ gridColumn: "1 / -1" }}>
                    <dt style={{ fontSize: "10px", color: "var(--muted)", letterSpacing: "0.04em", textTransform: "uppercase" }}>
                      Session ID
                    </dt>
                    <dd style={{ fontSize: "11px", fontWeight: 500, margin: "2px 0 0", wordBreak: "break-all", color: "var(--muted)" }}>
                      {event.sessionId ?? "-"}
                    </dd>
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
