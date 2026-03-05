"use client";

import { useState } from "react";

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
          First E2 slice: one workspace route with URL, email, and QR tabs. Submission wiring to
          `/api/v2/analyze` will follow in the next increment.
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
        {activeTab === "url" ? <UrlPlaceholder /> : null}
        {activeTab === "email" ? <EmailPlaceholder /> : null}
        {activeTab === "qr" ? <QrPlaceholder /> : null}
      </section>
    </>
  );
}

function UrlPlaceholder() {
  return (
    <>
      <h2>URL Analyze</h2>
      <label>
        URL
        <input placeholder="https://example.com" disabled />
      </label>
      <label className="inline">
        <input type="checkbox" style={{ width: "auto" }} disabled />
        Include family summary payload
      </label>
      <button type="button" disabled>
        Analyze URL (coming soon)
      </button>
      <p className="placeholderNote">Target contract: `POST /api/v2/analyze` (`input_type=url`).</p>
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
        Target contract: `POST /api/v2/analyze` (`input_type=email_headers`).
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
