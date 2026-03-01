"use client";

import { FormEvent, useState } from "react";
import { ApiRequestError, ApiWrappedResponse, asPrettyJson, postApi } from "../../lib/api";

export default function QrPage() {
  const [imagePath, setImagePath] = useState("C:/tmp/code.png");
  const [analyzeAll, setAnalyzeAll] = useState(false);
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
      const result = await postApi<ApiWrappedResponse>("/api/v1/qr/scan", {
        image_path: imagePath,
        analyze_all: analyzeAll,
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

  const subjects =
    response?.mode === "multi"
      ? response.items?.map((item) => item.subject) ?? []
      : response?.item
        ? [response.item.subject]
        : [];

  return (
    <>
      <section className="card">
        <h1>QR Scan</h1>
        <p className="muted">
          Current backend contract accepts a local filesystem path visible to the API runtime.
        </p>
        <form onSubmit={onSubmit}>
          <label>
            Image path
            <input
              value={imagePath}
              onChange={(e) => setImagePath(e.target.value)}
              placeholder="C:/tmp/code.png"
            />
          </label>

          <label className="inline">
            <input
              type="checkbox"
              checked={analyzeAll}
              onChange={(e) => setAnalyzeAll(e.target.checked)}
              style={{ width: "auto" }}
            />
            Analyze all decoded URL payloads
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
            {loading ? "Scanning..." : "Scan QR"}
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
              Subjects: <strong>{subjects.join(", ") || "-"}</strong>
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
