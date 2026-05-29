"use client";

import { ChangeEvent, FormEvent, useId, useState } from "react";

import {
  AnalyzeV2Request,
  ApiRequestError,
  ApiWrappedResponse,
  analyzeV2,
  scanQr
} from "../../lib/api";
import { EmptyState, QuickResult } from "./result-panels";

type Submission =
  | {
      kind: "url";
      request: AnalyzeV2Request;
    }
  | {
      kind: "qr";
      file: File;
      family: boolean;
    };

interface RunState {
  loading: boolean;
  error: string | null;
  response: ApiWrappedResponse | null;
  lastSubmission: Submission | null;
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

function validateUrl(url: string): string | null {
  try {
    const parsed = new URL(url);
    if (parsed.protocol !== "http:" && parsed.protocol !== "https:") {
      return "Use a URL that starts with http:// or https://.";
    }
  } catch {
    return "Enter a full URL that starts with http:// or https://.";
  }

  return null;
}

function validateQrFile(file: File): string | null {
  if (file.type && !file.type.startsWith("image/")) {
    return "Upload an image file for QR scanning.";
  }

  return null;
}

function endpointLabel(submission: Submission | null): string | null {
  if (!submission) {
    return null;
  }

  return submission.kind === "qr" ? "POST /api/v1/qr/scan" : "POST /api/v2/analyze";
}

export default function AnalyzePage() {
  const validationMessageId = useId();
  const [url, setUrl] = useState("");
  const [qrFile, setQrFile] = useState<File | null>(null);
  const [validationMessage, setValidationMessage] = useState<string | null>(null);
  const [runState, setRunState] = useState<RunState>({
    loading: false,
    error: null,
    response: null,
    lastSubmission: null
  });

  async function executeSubmission(submission: Submission): Promise<void> {
    setValidationMessage(null);
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
        formData.append("analyze_all", "false");
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

  async function onAnalyzeSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const trimmedUrl = url.trim();
    const hasUrl = trimmedUrl.length > 0;
    const hasQrFile = qrFile !== null;

    if (!hasUrl && !hasQrFile) {
      setValidationMessage("Paste a URL or upload a QR image to analyze.");
      return;
    }

    if (hasUrl && hasQrFile) {
      setValidationMessage("Choose either a URL or a QR image, not both.");
      return;
    }

    if (hasQrFile && qrFile) {
      const qrValidationError = validateQrFile(qrFile);
      if (qrValidationError) {
        setValidationMessage(qrValidationError);
        return;
      }

      await executeSubmission({
        kind: "qr",
        file: qrFile,
        family: true
      });
      return;
    }

    const urlValidationError = validateUrl(trimmedUrl);
    if (urlValidationError) {
      setValidationMessage(urlValidationError);
      return;
    }

    await executeSubmission({
      kind: "url",
      request: {
        input_type: "url",
        content: trimmedUrl,
        subject: trimmedUrl,
        family: true
      }
    });
  }

  function onQrFileChange(event: ChangeEvent<HTMLInputElement>) {
    setQrFile(event.target.files?.[0] ?? null);
  }

  const endpoint = endpointLabel(runState.lastSubmission);

  return (
    <div className="analyzeShell" data-testid="analyze-shell">
      <aside className="analyzeSidebar" aria-label="Safe Link Analyst navigation">
        <div className="analyzeBrand" aria-label="Safe Link Analyst">
          <span className="brandMark" aria-hidden="true">
            S
          </span>
          <strong>
            Safe Link
            <span>Analyst</span>
          </strong>
        </div>

        <nav className="analyzeNav" aria-label="Analyze sections">
          <a className="analyzeNavItem analyzeNavItemActive" href="/analyze" aria-current="page">
            <span aria-hidden="true">A</span>
            Analyze
          </a>
          <button type="button" className="analyzeNavItem" disabled>
            <span aria-hidden="true">P</span>
            Policies
          </button>
          <button type="button" className="analyzeNavItem" disabled>
            <span aria-hidden="true">H</span>
            History
          </button>
        </nav>
      </aside>

      <main className="analyzeMain">
        <header className="analyzeHeader">
          <h1>Analyze a suspicious link or QR code</h1>
          <p>Paste a link or upload a QR image to get a clear verdict.</p>
        </header>

        <form
          className="analyzeInputCard"
          data-testid="analyze-input-card"
          onSubmit={onAnalyzeSubmit}
          aria-describedby={validationMessage ? validationMessageId : undefined}
        >
          <label className="analyzeUrlField">
            URL
            <input
              value={url}
              onChange={(event) => setUrl(event.target.value)}
              placeholder="https://example.com"
              aria-invalid={validationMessage ? "true" : undefined}
            />
          </label>

          <label className="qrUploadField">
            QR image (optional)
            <span className="qrUploadDropzone">
              <span className="qrUploadIcon" aria-hidden="true">
                QR
              </span>
              <span>
                {qrFile ? qrFile.name : "Click to upload QR image"}
                <small>PNG, JPG, WEBP up to 5MB</small>
              </span>
              <input type="file" accept="image/*" onChange={onQrFileChange} />
            </span>
          </label>

          <button type="submit" className="analyzePrimaryButton" disabled={runState.loading}>
            {runState.loading ? "Analyzing..." : "Analyze"}
          </button>

          {validationMessage ? (
            <p
              id={validationMessageId}
              className="analyzeValidationMessage"
              data-testid="analyze-validation-message"
              role="alert"
              aria-live="polite"
            >
              {validationMessage}
            </p>
          ) : null}
        </form>

        <section className="analyzeResultArea" aria-label="Analysis result">
          {endpoint ? <p className="muted compactText">Latest endpoint: {endpoint}</p> : null}

          {runState.loading ? (
            <section className="statusPanel">
              <p className="eyebrow">In progress</p>
              <h2>Waiting on the API</h2>
              <p className="muted">A fresh result will appear here when analysis finishes.</p>
            </section>
          ) : null}

          {!runState.loading && runState.error ? (
            <section className="statusPanel statusPanelError">
              <p className="eyebrow">Error</p>
              <h2>Request failed</h2>
              <p>{runState.error}</p>
            </section>
          ) : null}

          {!runState.loading && !runState.error && runState.response ? (
            <QuickResult response={runState.response} />
          ) : null}

          {!runState.loading && !runState.error && !runState.response ? <EmptyState /> : null}
        </section>
      </main>
    </div>
  );
}
