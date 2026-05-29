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

const QR_ERROR_MESSAGES: Record<string, string> = {
  QRC_DECODER_UNAVAILABLE:
    "QR scanning is not available in this environment. Paste the URL from the QR code instead.",
  QRC_MULTIPART_UNAVAILABLE:
    "QR image uploads are not available in this environment. Paste the URL from the QR code instead.",
  QRC_NO_URL_PAYLOADS:
    "The QR image was read, but it did not contain a web URL. Upload a QR code with an http or https link, or paste the URL."
};

function formatRequestError(error: unknown): string {
  if (error instanceof ApiRequestError) {
    if (error.code && QR_ERROR_MESSAGES[error.code]) {
      return `${QR_ERROR_MESSAGES[error.code]} (${error.code})`;
    }
    return `${error.message}${error.code ? ` (${error.code})` : ""}`;
  }
  if (error instanceof Error) {
    if (error.name === "TypeError") {
      return "Could not reach the analysis API. Confirm it is running and try again.";
    }
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
  const urlInputId = useId();
  const qrInputId = useId();
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
    setRunState((current) => ({
      loading: true,
      error: null,
      response: current.response,
      lastSubmission: submission
    }));

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
      setRunState((current) => ({
        loading: false,
        error: formatRequestError(error),
        response: current.response,
        lastSubmission: submission
      }));
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

  function onUrlChange(event: ChangeEvent<HTMLInputElement>) {
    setUrl(event.target.value);
    if (validationMessage) {
      setValidationMessage(null);
    }
  }

  function onQrFileChange(event: ChangeEvent<HTMLInputElement>) {
    setQrFile(event.target.files?.[0] ?? null);
    if (validationMessage) {
      setValidationMessage(null);
    }
  }

  const endpoint = endpointLabel(runState.lastSubmission);
  const validationState = validationMessage ? "true" : undefined;

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
          <label className="analyzeUrlField" htmlFor={urlInputId}>
            URL
            <input
              id={urlInputId}
              value={url}
              onChange={onUrlChange}
              placeholder="https://example.com"
              disabled={runState.loading}
              aria-invalid={validationState}
              aria-describedby={validationMessage ? validationMessageId : undefined}
            />
          </label>

          <label className="qrUploadField" htmlFor={qrInputId}>
            QR image (optional)
            <span className="qrUploadDropzone">
              <span className="qrUploadIcon" aria-hidden="true">
                QR
              </span>
              <span>
                {qrFile ? qrFile.name : "Click to upload QR image"}
                <small>PNG, JPG, WEBP up to 5MB</small>
              </span>
              <input
                id={qrInputId}
                type="file"
                accept="image/*"
                onChange={onQrFileChange}
                disabled={runState.loading}
                aria-invalid={validationState}
                aria-describedby={validationMessage ? validationMessageId : undefined}
              />
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

        <section
          className="analyzeResultArea"
          data-testid="analyze-result-area"
          aria-label="Analysis result"
          aria-busy={runState.loading}
        >
          {endpoint ? <p className="muted compactText">Latest endpoint: {endpoint}</p> : null}

          {runState.loading ? (
            <section className="statusPanel" role="status" aria-live="polite">
              <p className="eyebrow">In progress</p>
              <h2>Analyzing this submission</h2>
              <p className="muted">
                A fresh result will appear here when analysis finishes.
                {runState.response ? " The previous result remains below." : ""}
              </p>
            </section>
          ) : null}

          {!runState.loading && runState.error ? (
            <section className="statusPanel statusPanelError" role="alert" aria-live="assertive">
              <p className="eyebrow">Error</p>
              <h2>Request failed</h2>
              <p>{runState.error}</p>
              {runState.response ? <p className="muted">The previous successful result is still shown below.</p> : null}
            </section>
          ) : null}

          {runState.response ? <QuickResult response={runState.response} /> : null}

          {!runState.loading && !runState.error && !runState.response ? <EmptyState /> : null}
        </section>
      </main>
    </div>
  );
}
