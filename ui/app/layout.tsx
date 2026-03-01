import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "Link Safety Hub UI",
  description: "Minimal UI validation surface for Link Safety Hub API contract."
};

export default function RootLayout({
  children
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <div className="shell">
          <nav className="topbar">
            <strong>Link Safety Hub UI</strong>
            <Link href="/">Overview</Link>
            <Link href="/url">URL Check</Link>
            <Link href="/email">Email Check</Link>
            <Link href="/qr">QR Scan</Link>
          </nav>
          {children}
        </div>
      </body>
    </html>
  );
}
