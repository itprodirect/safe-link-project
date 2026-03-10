"use client";

import { FormEvent, useEffect, useState } from "react";

import {
  AnalyzeV2Request,
  ApiRequestError,
  ApiWrappedResponse,
  analyzeV2,
  scanQr
} from "../../lib/api";
import { AnalystResult, EmptyState, QuickResult } from "./result-panels";

type AnalyzeTab = "url" | "email" | "qr";
type WorkspaceMode = "quick" | "analyst";

const DEFAULT_EMAIL_HEADERS =
  "Authentication-Results: mx.example; spf=pass; dkim=pass; dmarc=pass\n";
const MODE_STORAGE_KEY = "lsh.analyze.mode";
const ALLOWLIST_CATEGORY_OPTIONS = ["HMG", "ASCII", "URL", "NET", "ALL", "NONE"] as const;

type AllowlistCategory = (typeof ALLOWLIST_CATEGORY_OPTIONS)[number];

interface UrlFormState {
  url: string;
  allowlistDomains: string;
  allowlistFindings: string;
  allowlistCategories: AllowlistCategory[];
  networkEnabled: boolean;
  networkMaxHops: number;
  networkTimeout: number;
}

interface EmailFormState {
  sourceLabel: string;
  headers: string;
}

interface QrFormState {
  imageFile: File | null;
  analyzeAll: boolean;
}

type Submission =
  | {
      kind: "url";
      request: AnalyzeV2Request;
    }
  | {
      kind: "email";
      request: AnalyzeV2Request;
    }
  | {
      kind: "qr";
      file: File;
      analyzeAll: boolean;
      family: boolean;
    };

interface RunState {
  loading: boolean;
  error: string | null;
  response: ApiWrappedResponse | null;
  lastSubmission: Submission | null;
}

const TAB_LABELS: Record<AnalyzeTab, string> = {
  url: "URL",
  email: "Email",
  qr: "QR"
};

const TAB_HELP: Record<AnalyzeTab, string> = {
  url: "Paste a destination, tune false-positive controls, and optionally enable redirect analysis.",
  email: "Paste raw email authentication headers and send them through the shared v2 analyze contract.",
  qr: "Upload a QR image from the same workspace. QR still uses the v1 upload route until v2 adds file inputs."
};

const MODE_COPY: Record<WorkspaceMode, string> = {
  quick: "Quick mode keeps the first verdict, top reasons, and next actions in view.",
  analyst: "Analyst mode keeps contract details, domain anatomy, redirect path, suppression trace, and evidence in view."
};

function readStoredMode(): WorkspaceMode {
  if (typeof window === "undefined") {
    return "quick";
  }
  const storedMode = window.localStorage.getItem(MODE_STORAGE_KEY);
  return storedMode === "quick" || storedMode === "analyst" ? storedMode : "quick";
}

function parseTokenList(raw: string): string[] {
  return raw
    .split(/[\s,]+/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function formatRequestError(error: unknown): string {
  if (error instanceof ApiRequestError) {
    return `${error.message}${error.code ? ` (${error.code})` : ""}`;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return "Unexpected error while calling API.";
}

function validateUrlForm(form: UrlFormState): string | null {
  const trimmedUrl = form.url.trim();
  if (!trimmedUrl) {
    return "Enter a URL to analyze.";
  }

  try {
    const parsed = new URL(trimmedUrl);
    if (parsed.protocol !== "http:" && parsed.protocol !== "https:") {
      return "Only http:// and https:// URLs are supported.";
    }
  } catch {
    return "Enter a full URL including http:// or https://.";
  }

  if (!Number.isInteger(form.networkMaxHops) || form.networkMaxHops < 1 || form.networkMaxHops > 15) {
    return "Network max hops must be between 1 and 15.";
  }

  if (!Number.isFinite(form.networkTimeout) || form.networkTimeout < 0.1) {
    return "Network timeout must be at least 0.1 seconds.";
  }

  return null;
}

function validateEmailForm(form: EmailFormState): string | null {
  const trimmedHeaders = form.headers.trim();
  if (!trimmedHeaders) {
    return "Paste email headers to analyze.";
  }
  if (!trimmedHeaders.includes(":")) {
    return "Email headers should include at least one header line like 'Authentication-Results: ...'.";
  }
  return null;
}

function validateQrForm(form: QrFormState): string | null {
  if (!form.imageFile) {
    return "Choose a QR image file first.";
  }
  if (form.imageFile.type && !form.imageFile.type.startsWith("image/")) {
    return "QR uploads must be image files.";
  }
  return null;
}

function endpointLabel(submission: Submission | null): string | null {
  if (!submission) {
    return null;
  }
  if (submission.kind === "qr") {
    return "POST /api/v1/qr/scan";
  }
  return "POST /api/v2/analyze";
}

export default function AnalyzePage() {
  const [activeTab, setActiveTab] = useState<AnalyzeTab>("url");
  const [mode, setMode] = useState<WorkspaceMode>(() => readStoredMode());
  const [urlForm, setUrlForm] = useState<UrlFormState>({
    url: "https://example.com",
    allowlistDomains: "",
    allowlistFindings: "",
    allowlistCategories: [],
    networkEnabled: false,
    networkMaxHops: 5,
    networkTimeout: 3.0
  });
  const [emailForm, setEmailForm] = useState<EmailFormState>({
    sourceLabel: "inline headers",
    headers: DEFAULT_EMAIL_HEADERS
  });
  const [qrForm, setQrForm] = useState<QrFormState>({
    imageFile: null,
    analyzeAll: false
  });
  const [runState, setRunState] = useState<RunState>({
    loading: false,
    error: null,
    response: null,
    lastSubmission: null
  });

  useEffect(() => {
    window.localStorage.setItem(MODE_STORAGE_KEY, mode);
  }, [mode]);

  function toggleCategory(category: AllowlistCategory) {
    setUrlForm((current) => {
      const selected = new Set(current.allowlistCategories);
      if (selected.has(category)) {
        selected.delete(category);
        return { ...current, allowlistCategories: [...selected] as AllowlistCategory[] };
      }
      if (category === "NONE") {
        return { ...current, allowlistCategories: ["NONE"] };
      }
      selected.delete("NONE");
      selected.add(category);
      return { ...current, allowlistCategories: [...selected] as AllowlistCategory[] };
    });
  }

  async function executeSubmission(submission: Submission): Promise<void> {
    setRunState({
      loading: true,
      error: null,
      response: null,
      lastSubmission: submission
    });

    try {
      let response: ApiWrappedResponse;
      if (submission.kind === "qr") {
        const formData = new FormData();
        formData.append("file", submission.file);
        formData.append("analyze_all", String(submission.analyzeAll));
        formData.append("family", String(submission.family));
        response = await scanQr(formData);
      } else {
        response = await analyzeV2(submission.request);
      }

      setRunState({
        loading: false,
        error: null,
        response,
        lastSubmission: submission
      });
    } catch (error) {
      setRunState({
        loading: false,
        error: formatRequestError(error),
        response: null,
        lastSubmission: submission
      });
    }
  }

  async function onUrlSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const validationError = validateUrlForm(urlForm);
    if (validationError) {
      setRunState((current) => ({
        ...current,
        error: validationError,
        response: null
      }));
      return;
    }

    const trimmedUrl = urlForm.url.trim();
    const request: AnalyzeV2Request = {
      input_type: "url",
      content: trimmedUrl,
      subject: trimmedUrl,
      family: true,
      allowlist_domains: parseTokenList(urlForm.allowlistDomains),
      allowlist_categories: urlForm.allowlistCategories,
      allowlist_findings: parseTokenList(urlForm.allowlistFindings).map((item) => item.toUpperCase()),
      network_enabled: urlForm.networkEnabled,
      network_max_hops: urlForm.networkMaxHops,
      network_timeout: urlForm.networkTimeout
    };

    await executeSubmission({ kind: "url", request });
  }

  async function onEmailSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const validationError = validateEmailForm(emailForm);
    if (validationError) {
      setRunState((current) => ({
        ...current,
        error: validationError,
        response: null
      }));
      return;
    }

    const request: AnalyzeV2Request = {
      input_type: "email_headers",
      content: emailForm.headers.trim(),
      subject: emailForm.sourceLabel.trim() || "inline headers",
      family: true
    };

    await executeSubmission({ kind: "email", request });
  }

  async function onQrSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const validationError = validateQrForm(qrForm);
    if (validationError) {
      setRunState((current) => ({
        ...current,
        error: validationError,
        response: null
      }));
      return;
    }

    await executeSubmission({
      kind: "qr",
      file: qrForm.imageFile as File,
      analyzeAll: qrForm.analyzeAll,
      family: true
    });
  }

  const endpoint = endpointLabel(runState.lastSubmission);

  return (
    <>
      <section className="card workspaceHero">
        <div>
          <p className="eyebrow">V2 phase 2</p>
          <h1>Unified Analyze Workspace</h1>
          <p className="muted">
            URL and email now submit through <code>POST /api/v2/analyze</code>. QR still uses the
            existing upload route from this page until the v2 contract grows file input support.
          </p>
        </div>

        <div className="modeRail">
          <p className="eyebrow">View mode</p>
          <div className="modeToggle" role="tablist" aria-label="Analyze workspace mode">
            {(["quick", "analyst"] as WorkspaceMode[]).map((nextMode) => {
              const active = mode === nextMode;
              return (
                <button
                  key={nextMode}
                  type="button"
                  role="tab"
                  aria-selected={active}
                  className={`modeButton${active ? " modeButtonActive" : ""}`}
                  onClick={() => setMode(nextMode)}
                >
                  {nextMode === "quick" ? "Quick" : "Analyst"}
                </button>
              );
            })}
          </div>
          <p className="muted compactText">{MODE_COPY[mode]}</p>
        </div>
      </section>

      <div className="workspaceGrid">
        <section className="card">
          <div className="workspaceSectionTitle">
            <div>
              <h2>Input</h2>
              <p className="muted compactText">{TAB_HELP[activeTab]}</p>
            </div>
            <span className="badge">Family summaries enabled</span>
          </div>

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

          {activeTab === "url" ? (
            <form onSubmit={onUrlSubmit} className="formStack">
              <label>
                URL
                <input
                  value={urlForm.url}
                  onChange={(event) =>
                    setUrlForm((current) => ({ ...current, url: event.target.value }))
                  }
                  placeholder="https://example.com"
                />
              </label>

              <label className="inline">
                <input
                  type="checkbox"
                  checked={urlForm.networkEnabled}
                  onChange={(event) =>
                    setUrlForm((current) => ({ ...current, networkEnabled: event.target.checked }))
                  }
                  style={{ width: "auto" }}
                />
                Enable redirect-chain network checks
              </label>

              <div className="fieldGrid">
                <label>
                  Max hops
                  <input
                    type="number"
                    min={1}
                    max={15}
                    value={urlForm.networkMaxHops}
                    disabled={!urlForm.networkEnabled}
                    onChange={(event) =>
                      setUrlForm((current) => ({
                        ...current,
                        networkMaxHops: Number(event.target.value)
                      }))
                    }
                  />
                </label>

                <label>
                  Timeout (seconds)
                  <input
                    type="number"
                    min={0.1}
                    step={0.1}
                    value={urlForm.networkTimeout}
                    disabled={!urlForm.networkEnabled}
                    onChange={(event) =>
                      setUrlForm((current) => ({
                        ...current,
                        networkTimeout: Number(event.target.value)
                      }))
                    }
                  />
                </label>
              </div>

              <label>
                Allowlist domains
                <textarea
                  className="textareaCompact"
                  value={urlForm.allowlistDomains}
                  onChange={(event) =>
                    setUrlForm((current) => ({ ...current, allowlistDomains: event.target.value }))
                  }
                  placeholder="example.com trusted.example"
                />
              </label>

              <label>
                Allowlist categories
                <div className="optionGrid">
                  {ALLOWLIST_CATEGORY_OPTIONS.map((category) => (
                    <label className="inline" key={category}>
                      <input
                        type="checkbox"
                        checked={urlForm.allowlistCategories.includes(category)}
                        onChange={() => toggleCategory(category)}
                        style={{ width: "auto" }}
                      />
                      {category}
                    </label>
                  ))}
                </div>
              </label>
              <p className="muted compactText">
                Select <code>NONE</code> if you only want exact finding-token suppression.
              </p>

              <label>
                Allowlist findings
                <textarea
                  className="textareaCompact"
                  value={urlForm.allowlistFindings}
                  onChange={(event) =>
                    setUrlForm((current) => ({ ...current, allowlistFindings: event.target.value }))
                  }
                  placeholder="HMG002_PUNYCODE_VISIBILITY HMG004*"
                />
              </label>

              <button type="submit" disabled={runState.loading}>
                {runState.loading ? "Analyzing..." : "Analyze URL"}
              </button>
            </form>
          ) : null}

          {activeTab === "email" ? (
            <form onSubmit={onEmailSubmit} className="formStack">
              <label>
                Source label
                <input
                  value={emailForm.sourceLabel}
                  onChange={(event) =>
                    setEmailForm((current) => ({ ...current, sourceLabel: event.target.value }))
                  }
                  placeholder="inline headers"
                />
              </label>

              <label>
                Email headers
                <textarea
                  value={emailForm.headers}
                  onChange={(event) =>
                    setEmailForm((current) => ({ ...current, headers: event.target.value }))
                  }
                  placeholder="Authentication-Results: ..."
                />
              </label>

              <button type="submit" disabled={runState.loading}>
                {runState.loading ? "Analyzing..." : "Analyze email headers"}
              </button>
            </form>
          ) : null}

          {activeTab === "qr" ? (
            <form onSubmit={onQrSubmit} className="formStack">
              <label>
                QR image file
                <input
                  type="file"
                  accept="image/*"
                  onChange={(event) =>
                    setQrForm((current) => ({
                      ...current,
                      imageFile: event.target.files?.[0] ?? null
                    }))
                  }
                />
              </label>

              <label className="inline">
                <input
                  type="checkbox"
                  checked={qrForm.analyzeAll}
                  onChange={(event) =>
                    setQrForm((current) => ({ ...current, analyzeAll: event.target.checked }))
                  }
                  style={{ width: "auto" }}
                />
                Analyze all decoded URL payloads
              </label>

              <p className="muted compactText">
                This tab uses <code>POST /api/v1/qr/scan</code> today so the workspace can cover QR
                uploads before file support lands in v2.
              </p>

              <button type="submit" disabled={runState.loading}>
                {runState.loading ? "Scanning..." : "Scan QR"}
              </button>
            </form>
          ) : null}
        </section>

        <section className="card">
          <div className="workspaceSectionTitle">
            <div>
              <h2>{mode === "quick" ? "Verdict" : "Analysis details"}</h2>
              <p className="muted compactText">
                {endpoint ? `Latest endpoint: ${endpoint}` : "No request sent yet."}
              </p>
            </div>
            {runState.lastSubmission ? (
              <button
                type="button"
                className="secondaryButton"
                disabled={runState.loading}
                onClick={() => {
                  if (runState.lastSubmission) {
                    void executeSubmission(runState.lastSubmission);
                  }
                }}
              >
                Retry last request
              </button>
            ) : null}
          </div>

          {runState.loading ? (
            <section className="statusPanel">
              <p className="eyebrow">In progress</p>
              <h3>Waiting on the API</h3>
              <p className="muted">The workspace clears stale output while a fresh result is loading.</p>
            </section>
          ) : null}

          {!runState.loading && runState.error ? (
            <section className="statusPanel statusPanelError">
              <p className="eyebrow">Error</p>
              <h3>Request failed</h3>
              <p>{runState.error}</p>
            </section>
          ) : null}

          {!runState.loading && !runState.error && runState.response ? (
            mode === "quick" ? (
              <QuickResult response={runState.response} />
            ) : (
              <AnalystResult response={runState.response} />
            )
          ) : null}

          {!runState.loading && !runState.error && !runState.response ? <EmptyState /> : null}
        </section>
      </div>
    </>
  );
}
