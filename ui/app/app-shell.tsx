"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  if (pathname?.startsWith("/analyze")) {
    return <>{children}</>;
  }

  return (
    <div className="shell">
      <nav className="topbar">
        <strong>Link Safety Hub UI</strong>
        <Link href="/">Overview</Link>
        <Link href="/analyze">Analyze (V2)</Link>
        <Link href="/url">URL Check</Link>
        <Link href="/email">Email Check</Link>
        <Link href="/qr">QR Scan</Link>
      </nav>
      {children}
    </div>
  );
}
