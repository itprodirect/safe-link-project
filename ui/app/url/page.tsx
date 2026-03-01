"use client";

import { FormEvent, useState } from "react";
import { ApiRequestError, ApiWrappedResponse, asPrettyJson, postApi } from "../../lib/api";

export default function UrlPage() {
  const [url, setUrl] = useState("https://example.com");
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
      const result = await postApi<ApiWrappedResponse>("/api/v1/url/check", { url, family });
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
        <h1>URL Check</h1>
        <form onSubmit={onSubmit}>
          <label>
            URL
            <input value={url} onChange={(e) => setUrl(e.target.value)} placeholder="https://..." />
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
            {loading ? "Checking..." : "Check URL"}
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
            <p>
              `overall_risk`:{" "}
              <strong>{String((response.item?.result?.overall_risk as number | undefined) ?? "-")}</strong>
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
