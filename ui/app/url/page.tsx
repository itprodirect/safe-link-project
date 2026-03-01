"use client";

import { FormEvent, useState } from "react";
import { ApiRequestError, ApiWrappedResponse, asPrettyJson, postApi } from "../../lib/api";

const ALLOWLIST_CATEGORY_OPTIONS = ["HMG", "ASCII", "URL", "NET", "ALL", "NONE"] as const;
type AllowlistCategory = (typeof ALLOWLIST_CATEGORY_OPTIONS)[number];

function parseTokenList(raw: string): string[] {
  return raw
    .split(/[\s,]+/)
    .map((item) => item.trim())
    .filter(Boolean);
}

export default function UrlPage() {
  const [url, setUrl] = useState("https://example.com");
  const [family, setFamily] = useState(false);
  const [allowlistDomains, setAllowlistDomains] = useState("");
  const [allowlistFindings, setAllowlistFindings] = useState("");
  const [allowlistCategories, setAllowlistCategories] = useState<AllowlistCategory[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [response, setResponse] = useState<ApiWrappedResponse | null>(null);

  function toggleCategory(category: AllowlistCategory) {
    setAllowlistCategories((current) => {
      const selected = new Set(current);
      if (selected.has(category)) {
        selected.delete(category);
        return [...selected] as AllowlistCategory[];
      }
      if (category === "NONE") {
        return ["NONE"];
      }
      selected.delete("NONE");
      selected.add(category);
      return [...selected] as AllowlistCategory[];
    });
  }

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    setResponse(null);
    try {
      const requestBody: Record<string, unknown> = { url, family };
      const parsedDomains = parseTokenList(allowlistDomains);
      const parsedFindings = parseTokenList(allowlistFindings).map((finding) =>
        finding.toUpperCase()
      );

      if (parsedDomains.length > 0) {
        requestBody.allowlist_domains = parsedDomains;
      }
      if (allowlistCategories.length > 0) {
        requestBody.allowlist_categories = allowlistCategories;
      }
      if (parsedFindings.length > 0) {
        requestBody.allowlist_findings = parsedFindings;
      }

      const result = await postApi<ApiWrappedResponse>("/api/v1/url/check", requestBody);
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

          <h2>False-Positive Controls</h2>
          <p className="muted">
            These controls apply only when the hostname matches an allowlisted domain.
          </p>

          <label>
            Allowlist Domains (comma or whitespace separated)
            <textarea
              value={allowlistDomains}
              onChange={(e) => setAllowlistDomains(e.target.value)}
              placeholder="example.com trusted.example"
            />
          </label>

          <label>
            Allowlist Categories
            <div className="optionGrid">
              {ALLOWLIST_CATEGORY_OPTIONS.map((category) => (
                <label className="inline" key={category}>
                  <input
                    type="checkbox"
                    checked={allowlistCategories.includes(category)}
                    onChange={() => toggleCategory(category)}
                    style={{ width: "auto" }}
                  />
                  {category}
                </label>
              ))}
            </div>
          </label>
          <p className="muted">
            `NONE` disables broad category suppression so only specific finding codes apply.
          </p>

          <label>
            Allowlist Findings (exact code, stem, or wildcard prefix)
            <textarea
              value={allowlistFindings}
              onChange={(e) => setAllowlistFindings(e.target.value)}
              placeholder="HMG002_PUNYCODE_VISIBILITY HMG004*"
            />
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
