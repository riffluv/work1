import type { Metadata } from "next";
import { Noto_Sans_JP, Plus_Jakarta_Sans } from "next/font/google";
import ThemeToggle from "./components/ThemeToggle";
import "./globals.css";

/* Impeccable: Poppinsは汎用すぎるため Plus Jakarta Sans に差替え */
/* 日本語ボディはNoto Sans JPを維持 */
const heading = Plus_Jakarta_Sans({
  variable: "--font-heading",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700", "800"],
});

const body = Noto_Sans_JP({
  variable: "--font-body",
  subsets: ["latin"],
  weight: ["400", "500", "700"],
});

export const metadata: Metadata = {
  title: "Stripe Showcase Demo",
  description:
    "Next.js + Stripe Checkout + Webhook reception demo for portfolio screenshots.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ja">
      <body className={`${heading.variable} ${body.variable} antialiased`}>
        <ThemeToggle />
        {children}
      </body>
    </html>
  );
}
