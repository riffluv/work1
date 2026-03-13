import Link from "next/link";

export default function CancelPage() {
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
          color: "var(--warning)",
          marginBottom: "8px",
        }}
      >
        Payment Canceled
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
        決済がキャンセルされました
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
        課金は発生していません。いつでも再開できます。
      </p>

      <div
        className="animate-in stagger-3"
        style={{ marginTop: "32px" }}
      >
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
