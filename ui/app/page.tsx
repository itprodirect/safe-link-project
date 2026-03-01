import Link from "next/link";

export default function HomePage() {
  return (
    <>
      <section className="card">
        <h1>UI Contract Validation Surface</h1>
        <p className="muted">
          This minimal Next.js app validates Link Safety Hub API wrapper behavior for URL, email,
          and QR flows.
        </p>
      </section>

      <section className="card">
        <h2>Contract Targets</h2>
        <ul>
          <li>`schema_version = 1.0`</li>
          <li>wrapped `single` and `multi` response modes</li>
          <li>structured error envelopes for explicit QR endpoint failures</li>
        </ul>
      </section>

      <section className="card">
        <h2>Quick Actions</h2>
        <p>
          <Link href="/url">Run URL check</Link>
        </p>
        <p>
          <Link href="/email">Run email check</Link>
        </p>
        <p>
          <Link href="/qr">Run QR scan request</Link>
        </p>
      </section>
    </>
  );
}
