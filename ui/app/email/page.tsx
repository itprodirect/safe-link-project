"use client";

import { FormEvent, useState } from "react";
import { ApiRequestError, ApiWrappedResponse, asPrettyJson, postApi } from "../../lib/api";

const DEFAULT_HEADERS =
  "Authentication-Results: mx.example; spf=pass; dkim=pass; dmarc=pass\n";

export default function EmailPage() {
  const [headers, setHeaders] = useState(DEFAULT_HEADERS);
  const [sourceLabel, setSourceLabel] = useState("inline headers");
  const [family, setFamily] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [response, setResponse] = useState<ApiWrappedResponse | null>(null);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    setResponse(null);
    try {
      const result = await postApi<ApiWrappedResponse>("/api/v1/email/check", {
        headers,
        source_label: sourceLabel,
        family
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
      <section className="card">
        <h1>Email Check</h1>
        <form onSubmit={onSubmit}>
          <label>
            Source label
            <input
              value={sourceLabel}
              onChange={(e) => setSourceLabel(e.target.value)}
              placeholder="inline headers"
            />
          </label>

          <label>
            Headers
            <textarea value={headers} onChange={(e) => setHeaders(e.target.value)} />
          </label>

          <label className="inline">
            <input
              type="checkbox"
              checked={family}
              onChange={(e) => setFamily(e.target.checked)}
              style={{ width: "auto" }}
            />
            Include family summary payload
          </label>

          <button type="submit" disabled={loading}>
            {loading ? "Checking..." : "Check email headers"}
          </button>
        </form>
      </section>

      {error ? (
        <section className="card">
          <h2>API Error</h2>
          <p>{error}</p>
        </section>
      ) : null}

      {response ? (
        <>
          <section className="card">
            <h2>Contract Summary</h2>
            <p>
              `schema_version`: <strong>{response.schema_version}</strong>
            </p>
            <p>
              `mode`: <strong>{response.mode}</strong>
            </p>
            <p>
              `item_count`: <strong>{response.item_count}</strong>
            </p>
          </section>
          <section className="card">
            <h2>Raw JSON</h2>
            <pre>{asPrettyJson(response)}</pre>
          </section>
        </>
      ) : null}
    </>
  );
}
