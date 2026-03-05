"use client";

import { FormEvent, useState } from "react";
import {
  AnalyzeV2Response,
  ApiRequestError,
  asPrettyJson,
  analyzeV2
} from "../../lib/api";

type AnalyzeTab = "url" | "email" | "qr";

const TAB_LABELS: Record<AnalyzeTab, string> = {
  url: "URL",
  email: "Email",
  qr: "QR"
};

export default function AnalyzePage() {
  const [activeTab, setActiveTab] = useState<AnalyzeTab>("url");

  return (
    <>
      <section className="card">
        <h1>Unified Analyze (V2 Shell)</h1>
        <p className="muted">
          E2 foundation slice: one workspace route with URL, email, and QR tabs. URL is now wired
          to `POST /api/v2/analyze`; email and QR tab flows are staged next.
        </p>
        <div className="tabRow" role="tablist" aria-label="Analyze input type tabs">
          {(Object.keys(TAB_LABELS) as AnalyzeTab[]).map((tab) => {
            const active = activeTab === tab;
            return (
              <button
                key={tab}
                type="button"
                role="tab"
                aria-selected={active}
                className={`tabButton${active ? " tabButtonActive" : ""}`}
                onClick={() => setActiveTab(tab)}
              >
                {TAB_LABELS[tab]}
              </button>
            );
          })}
        </div>
      </section>

      <section className="card placeholderPanel">
        {activeTab === "url" ? <UrlAnalyzePanel /> : null}
        {activeTab === "email" ? <EmailPlaceholder /> : null}
        {activeTab === "qr" ? <QrPlaceholder /> : null}
      </section>
    </>
  );
}

function UrlAnalyzePanel() {
  const [url, setUrl] = useState("https://example.com");
  const [family, setFamily] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [response, setResponse] = useState<AnalyzeV2Response | null>(null);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    setResponse(null);
    try {
      const result = await analyzeV2({
        input_type: "url",
        content: url,
        subject: url,
        family,
        network_enabled: false,
        network_max_hops: 5,
        network_timeout: 3.0
      });
      setResponse(result);
    } catch (err) {
      if (err instanceof ApiRequestError) {
        setError(`${err.message}${err.code ? ` (${err.code})` : ""}`);
      } else {
        setError("Unexpected error while calling API.");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <h2>URL Analyze</h2>
      <form onSubmit={onSubmit}>
        <label>
          URL
          <input value={url} onChange={(event) => setUrl(event.target.value)} />
        </label>
        <label className="inline">
          <input
            type="checkbox"
            checked={family}
            onChange={(event) => setFamily(event.target.checked)}
            style={{ width: "auto" }}
          />
          Include family summary payload
        </label>
        <button type="submit" disabled={loading}>
          {loading ? "Analyzing..." : "Analyze URL"}
        </button>
      </form>

      {error ? (
        <section className="card">
          <h3>API Error</h3>
          <p>{error}</p>
        </section>
      ) : null}

      {response ? (
        <>
          <section className="card">
            <h3>Contract Summary</h3>
            <p>
              `schema_version`: <strong>{response.schema_version}</strong>
            </p>
            <p>
              `flow`: <strong>{response.flow}</strong>
            </p>
            <p>
              `mode`: <strong>{response.mode}</strong>
            </p>
            <p>
              `item_count`: <strong>{response.item_count}</strong>
            </p>
          </section>
          <section className="card">
            <h3>Raw JSON</h3>
            <pre>{asPrettyJson(response)}</pre>
          </section>
        </>
      ) : null}

      <p className="placeholderNote">Active contract target: `POST /api/v2/analyze` (`input_type=url`).</p>
    </>
  );
}

function EmailPlaceholder() {
  return (
    <>
      <h2>Email Analyze</h2>
      <label>
        Source label
        <input placeholder="inline headers" disabled />
      </label>
      <label>
        Email headers
        <textarea placeholder="Authentication-Results: ..." disabled />
      </label>
      <button type="button" disabled>
        Analyze Email (coming soon)
      </button>
      <p className="placeholderNote">
        Next target: `POST /api/v2/analyze` (`input_type=email_headers`).
      </p>
    </>
  );
}

function QrPlaceholder() {
  return (
    <>
      <h2>QR Analyze</h2>
      <label>
        QR image file
        <input type="file" disabled />
      </label>
      <label className="inline">
        <input type="checkbox" style={{ width: "auto" }} disabled />
        Analyze all decoded URL payloads
      </label>
      <button type="button" disabled>
        Analyze QR (coming soon)
      </button>
      <p className="placeholderNote">
        QR input in the unified v2 flow will map to `input_type` once that contract expands.
      </p>
    </>
  );
}
