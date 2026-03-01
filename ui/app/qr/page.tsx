"use client";

import { FormEvent, useState } from "react";
import { ApiRequestError, ApiWrappedResponse, asPrettyJson, postApiForm } from "../../lib/api";

export default function QrPage() {
  const [imageFile, setImageFile] = useState<File | null>(null);
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
      if (!imageFile) {
        throw new Error("Please choose a QR image file first.");
      }
      const formData = new FormData();
      formData.append("file", imageFile);
      formData.append("analyze_all", String(analyzeAll));
      formData.append("family", String(family));
      const result = await postApiForm<ApiWrappedResponse>("/api/v1/qr/scan", formData);
      setResponse(result);
    } catch (err) {
      if (err instanceof ApiRequestError) {
        setError(`${err.message}${err.code ? ` (${err.code})` : ""}`);
      } else if (err instanceof Error) {
        setError(err.message);
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
          Upload a QR image and the API will decode payloads from the uploaded file bytes.
        </p>
        <form onSubmit={onSubmit}>
          <label>
            QR image file
            <input
              type="file"
              accept="image/*"
              onChange={(e) => setImageFile(e.target.files?.[0] ?? null)}
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
