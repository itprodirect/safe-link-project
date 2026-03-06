"use client";

import { FormEvent, useEffect, useState } from "react";
import {
  AnalyzeV2Request,
  ApiItem,
  ApiRequestError,
  ApiWrappedResponse,
  asPrettyJson,
  analyzeV2,
  getPrimaryItem,
  getResponseItems,
  scanQr
} from "../../lib/api";

type AnalyzeTab = "url" | "email" | "qr";
type WorkspaceMode = "quick" | "analyst";
type ConfidenceLevel = "LOW" | "MEDIUM" | "HIGH";
type ActionLevel = "safe" | "caution" | "avoid" | "block";

const DEFAULT_EMAIL_HEADERS =
  "Authentication-Results: mx.example; spf=pass; dkim=pass; dmarc=pass\n";
const MODE_STORAGE_KEY = "lsh.analyze.mode";
const ALLOWLIST_CATEGORY_OPTIONS = ["HMG", "ASCII", "URL", "NET", "ALL", "NONE"] as const;

type AllowlistCategory = (typeof ALLOWLIST_CATEGORY_OPTIONS)[number];

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
  analyst: "Analyst mode keeps contract details and raw JSON visible for deeper inspection."
};

const CONFIDENCE_RANK: Record<ConfidenceLevel, number> = {
  LOW: 1,
  MEDIUM: 2,
  HIGH: 3
};

const ACTION_COPY: Record<
  ActionLevel,
  {
    badge: string;
    title: string;
    detail: string;
    fallbackRecommendation: string;
  }
> = {
  safe: {
    badge: "Safe",
    title: "Safe to continue",
    detail: "No strong warning signals were returned for this result.",
    fallbackRecommendation:
      "Proceed only if you expected this item, and use trusted bookmarks for sensitive accounts."
  },
  caution: {
    badge: "Caution",
    title: "Pause and verify",
    detail: "A mild warning sign was found, so a quick verification step is still worth it.",
    fallbackRecommendation: "Pause and verify the destination or sender before taking action."
  },
  avoid: {
    badge: "Avoid",
    title: "Avoid interacting for now",
    detail: "This result shows strong warning signs that should stop a routine click-through.",
    fallbackRecommendation:
      "Avoid opening links, replying, or signing in until you verify the destination through a trusted path."
  },
  block: {
    badge: "Block",
    title: "Block and report",
    detail: "This result has high-risk signals and should be treated as unsafe by default.",
    fallbackRecommendation:
      "Do not open or reply. Report it and use an official contact path instead."
  }
};

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

interface VerdictContext {
  flow: string;
  inputType: string;
}

function parseTokenList(raw: string): string[] {
  return raw
    .split(/[\s,]+/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function getString(value: unknown): string | null {
  return typeof value === "string" && value.trim().length > 0 ? value : null;
}

function getNumber(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function getConfidenceLevel(value: unknown): ConfidenceLevel | null {
  if (value === "LOW" || value === "MEDIUM" || value === "HIGH") {
    return value;
  }
  return null;
}

function getFindings(item: ApiItem): Record<string, unknown>[] {
  const findings = item.result.findings;
  if (!Array.isArray(findings)) {
    return [];
  }
  return findings.filter(isRecord);
}

function getRankedFindings(item: ApiItem): Record<string, unknown>[] {
  return [...getFindings(item)].sort((left, right) => {
    const riskDelta = (getNumber(right.risk_score) ?? 0) - (getNumber(left.risk_score) ?? 0);
    if (riskDelta !== 0) {
      return riskDelta;
    }

    const confidenceDelta =
      (CONFIDENCE_RANK[getConfidenceLevel(right.confidence) ?? "LOW"] ?? 0) -
      (CONFIDENCE_RANK[getConfidenceLevel(left.confidence) ?? "LOW"] ?? 0);
    if (confidenceDelta !== 0) {
      return confidenceDelta;
    }

    return (getString(left.title) ?? "").localeCompare(getString(right.title) ?? "");
  });
}

function dedupeStrings(values: string[]): string[] {
  return [...new Set(values)];
}

function isEmailContext(context: VerdictContext): boolean {
  return context.inputType === "email_headers" || context.inputType === "email_file";
}

function isQrContext(context: VerdictContext): boolean {
  return context.flow === "qr_scan";
}

function rewriteReason(reason: string, context: VerdictContext): string {
  if (isEmailContext(context)) {
    if (/sender server did not pass.*SPF/i.test(reason)) {
      return "The sender check failed, so this message may not be from who it claims.";
    }
    if (/signed authenticity check \(DKIM\) did not pass/i.test(reason)) {
      return "The message signature check failed, which can mean spoofing or tampering.";
    }
    if (/domain policy check \(DMARC\) failed/i.test(reason)) {
      return "The sender domain did not match its own policy, which is a strong warning sign.";
    }
    if (/weak or missing SPF/i.test(reason)) {
      return "A sender check is weak or missing, so trust is lower than normal.";
    }
    if (/weak or missing DKIM/i.test(reason)) {
      return "A message signature check is weak or missing, so trust is lower than normal.";
    }
    if (/weak or missing DMARC/i.test(reason)) {
      return "A sender-domain policy check is weak or missing, so this message deserves extra caution.";
    }
    if (/did not include standard authentication results/i.test(reason)) {
      return "Standard sender-verification results are missing, so trust checks are limited.";
    }
  }

  if (/hidden technical form \(`xn--\.\.\.`\)/i.test(reason)) {
    return "Part of this link is encoded in a way often used by lookalike domains.";
  }

  return reason;
}

function rewriteRecommendation(recommendation: string, context: VerdictContext): string {
  if (isEmailContext(context)) {
    if (/Treat the message as suspicious until independently verified\./i.test(recommendation)) {
      return "Treat this message as suspicious until you verify it another way.";
    }
    if (/Do not act on sensitive requests until verified independently\./i.test(recommendation)) {
      return "Do not follow sensitive requests until you verify them another way.";
    }
    if (/Use caution before trusting links or requests in this message\./i.test(recommendation)) {
      return "Be careful with links or requests in this message until you verify the sender.";
    }
  }

  return recommendation;
}

function getReasons(item: ApiItem, context: VerdictContext): string[] {
  if (item.family?.reasons?.length) {
    return dedupeStrings(item.family.reasons.map((reason) => rewriteReason(reason, context))).slice(
      0,
      3
    );
  }

  const reasons = getRankedFindings(item)
    .map((finding) => getString(finding.family_explanation) ?? getString(finding.explanation))
    .filter((reason): reason is string => reason !== null)
    .map((reason) => rewriteReason(reason, context));

  return dedupeStrings(reasons).slice(0, 3);
}

function getRecommendations(item: ApiItem, context: VerdictContext): string[] {
  if (item.family?.recommendations?.length) {
    return dedupeStrings(
      item.family.recommendations.map((recommendation) =>
        rewriteRecommendation(recommendation, context)
      )
    ).slice(0, 3);
  }

  const recommendations = new Set<string>();
  for (const finding of getRankedFindings(item)) {
    const rawRecommendations = finding.recommendations;
    if (!Array.isArray(rawRecommendations)) {
      continue;
    }
    for (const recommendation of rawRecommendations) {
      const parsedRecommendation = getString(recommendation);
      if (parsedRecommendation) {
        recommendations.add(rewriteRecommendation(parsedRecommendation, context));
      }
    }
  }

  return [...recommendations].slice(0, 3);
}

function getSeverity(item: ApiItem): string {
  return getString(item.family?.severity) ?? getString(item.result.overall_severity) ?? "UNKNOWN";
}

function getConfidence(item: ApiItem): ConfidenceLevel | null {
  const familyConfidence = getConfidenceLevel(item.family?.signal_confidence);
  if (familyConfidence) {
    return familyConfidence;
  }

  const findingConfidence = getRankedFindings(item)
    .map((finding) => getConfidenceLevel(finding.confidence))
    .find((confidence): confidence is ConfidenceLevel => confidence !== null);

  return findingConfidence ?? null;
}

function getSummary(item: ApiItem): string {
  return getString(item.family?.summary) ?? getString(item.result.summary) ?? "Analysis completed.";
}

function getRiskScore(item: ApiItem): number | null {
  return getNumber(item.family?.risk_score) ?? getNumber(item.result.overall_risk);
}

function getFindingCount(item: ApiItem): number {
  return getFindings(item).length;
}

function getActionLevel(item: ApiItem): ActionLevel {
  const riskScore = getRiskScore(item) ?? 0;
  const severity = getSeverity(item);

  if (riskScore >= 81 || severity === "CRITICAL") {
    return "block";
  }
  if (riskScore >= 61 || severity === "HIGH") {
    return "avoid";
  }
  if (riskScore >= 21 || severity === "MEDIUM" || severity === "LOW" || getFindingCount(item) > 0) {
    return "caution";
  }
  return "safe";
}

function getPrimaryRecommendation(
  item: ApiItem,
  actionLevel: ActionLevel,
  context: VerdictContext
): string {
  return getRecommendations(item, context)[0] ?? ACTION_COPY[actionLevel].fallbackRecommendation;
}

function getConfidenceNote(confidence: ConfidenceLevel | null): string {
  if (confidence === "HIGH") {
    return "High-confidence signals support this verdict.";
  }
  if (confidence === "MEDIUM") {
    return "Signal confidence is moderate, so context still matters.";
  }
  if (confidence === "LOW") {
    return "Signals are limited, so verify before acting.";
  }
  return "No confidence label was returned for this result.";
}

function getPlainLanguageSummary(item: ApiItem, context: VerdictContext): string {
  const actionLevel = getActionLevel(item);

  if (isEmailContext(context)) {
    if (actionLevel === "safe") {
      return "No major trust problems were found in these email headers.";
    }
    if (actionLevel === "caution") {
      return "This message is missing some trust signals, so verify it before acting.";
    }
    if (actionLevel === "avoid") {
      return "This message shows strong signs that it may not be trustworthy.";
    }
    return "This message failed key trust checks and should be treated as suspicious.";
  }

  if (isQrContext(context)) {
    if (actionLevel === "safe") {
      return "The QR code was read and the selected destination did not show strong warning signs.";
    }
    if (actionLevel === "caution") {
      return "The QR code leads to a destination with some warning signs, so verify it before opening.";
    }
    if (actionLevel === "avoid") {
      return "The QR code leads to a destination that should be avoided for now.";
    }
    return "The QR code leads to a destination that looks unsafe.";
  }

  if (actionLevel === "safe") {
    return "This destination did not show strong warning signs in this scan.";
  }
  if (actionLevel === "caution") {
    return "This destination has some warning signs, so verify it before opening.";
  }
  if (actionLevel === "avoid") {
    return "This destination shows strong warning signs and should be avoided for now.";
  }
  return "This destination looks unsafe and should be blocked or reported.";
}

function getVerdictDetail(actionLevel: ActionLevel, context: VerdictContext): string {
  if (isEmailContext(context)) {
    if (actionLevel === "safe") {
      return "The visible sender checks look normal enough that this message does not need an immediate block.";
    }
    if (actionLevel === "caution") {
      return "Some sender checks are missing or weak, so this message deserves a second look.";
    }
    if (actionLevel === "avoid") {
      return "Several sender checks failed or degraded, which raises spoofing risk.";
    }
    return "Multiple sender checks failed, which is common in spoofed or malicious messages.";
  }

  if (isQrContext(context)) {
    if (actionLevel === "safe") {
      return "The QR code resolved cleanly and the visible destination did not trigger major warnings.";
    }
    if (actionLevel === "caution") {
      return "The QR code resolved, but the destination still deserves a quick verification step.";
    }
    if (actionLevel === "avoid") {
      return "The QR code resolves to a destination that should not be trusted casually.";
    }
    return "The QR code resolves to a destination with high-risk signals.";
  }

  return ACTION_COPY[actionLevel].detail;
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

function MetricCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="metricCard">
      <span className="metricLabel">{label}</span>
      <span className="metricValue">{value}</span>
    </div>
  );
}

function VerdictCard({ item, context }: { item: ApiItem; context: VerdictContext }) {
  const riskScore = getRiskScore(item);
  const confidence = getConfidence(item);
  const actionLevel = getActionLevel(item);
  const primaryRecommendation = getPrimaryRecommendation(item, actionLevel, context);
  const actionCopy = ACTION_COPY[actionLevel];

  return (
    <section className={`verdictCard verdictCard-${actionLevel}`}>
      <div className="verdictHeader">
        <div>
          <p className="eyebrow">Primary verdict</p>
          <h3>{actionCopy.title}</h3>
        </div>
        <span className={`actionPill actionPill-${actionLevel}`}>Action: {actionCopy.badge}</span>
      </div>

      <p className="verdictSummary">{getPlainLanguageSummary(item, context)}</p>
      <p className="muted compactText">{getVerdictDetail(actionLevel, context)}</p>

      <div className="verdictPrimaryAction">
        <span className="metricLabel">Recommended next step</span>
        <strong>{primaryRecommendation}</strong>
      </div>

      <div className="badgeRow">
        <span className="badge">Subject: {item.subject}</span>
        <span className="badge">Risk: {riskScore !== null ? String(riskScore) : "-"}</span>
        <span className="badge">Findings: {String(getFindingCount(item))}</span>
        <span className="badge">Flow: {context.flow}</span>
        <span className="badge">
          Confidence: {confidence ?? "Not provided"}
        </span>
      </div>

      <p className="verdictConfidence">{getConfidenceNote(confidence)}</p>
    </section>
  );
}

function WhyPanel({ item, context }: { item: ApiItem; context: VerdictContext }) {
  const actionLevel = getActionLevel(item);
  const reasons = getReasons(item, context);
  const recommendations = getRecommendations(item, context);
  const nextSteps =
    recommendations.length > 0
      ? recommendations
      : [ACTION_COPY[actionLevel].fallbackRecommendation];

  return (
    <div className="resultList">
      <section className="miniCard">
        <h3>Why this verdict</h3>
        {reasons.length > 0 ? (
          <ol className="rankedList">
            {reasons.map((reason) => (
              <li key={reason}>{reason}</li>
            ))}
          </ol>
        ) : (
          <p className="muted">No reason strings were returned for this item.</p>
        )}
      </section>

      <section className="miniCard">
        <h3>Next actions</h3>
        <ul className="cleanList">
          {nextSteps.map((recommendation) => (
            <li key={recommendation}>{recommendation}</li>
          ))}
        </ul>
      </section>
    </div>
  );
}

function QuickResult({ response }: { response: ApiWrappedResponse }) {
  const primaryItem = getPrimaryItem(response);
  if (!primaryItem) {
    return <p className="muted">The API returned no items.</p>;
  }

  const items = getResponseItems(response);
  const context: VerdictContext = {
    flow: response.flow,
    inputType: response.input_type
  };

  return (
    <>
      <VerdictCard item={primaryItem} context={context} />
      <WhyPanel item={primaryItem} context={context} />

      {items.length > 1 ? (
        <section className="miniCard">
          <h3>Additional decoded items</h3>
          <div className="resultListCompact">
            {items.slice(1).map((item) => (
              <article className="miniCard insetCard" key={item.subject}>
                <strong>{item.subject}</strong>
                <p className="muted compactText">{getSummary(item)}</p>
                <div className="badgeRow">
                  <span className="badge">Action: {ACTION_COPY[getActionLevel(item)].badge}</span>
                  <span className="badge">
                    Risk: {getRiskScore(item) !== null ? String(getRiskScore(item)) : "-"}
                  </span>
                </div>
              </article>
            ))}
          </div>
        </section>
      ) : null}
    </>
  );
}

function AnalystResult({ response }: { response: ApiWrappedResponse }) {
  const items = getResponseItems(response);
  const primaryItem = getPrimaryItem(response);

  return (
    <div className="resultList">
      <section className="miniCard">
        <h3>Contract summary</h3>
        <div className="summaryGrid">
          <MetricCard label="Schema" value={response.schema_version} />
          <MetricCard label="Flow" value={response.flow} />
          <MetricCard label="Mode" value={response.mode} />
          <MetricCard label="Items" value={String(response.item_count)} />
          <MetricCard label="Input type" value={response.input_type} />
          <MetricCard label="Primary subject" value={primaryItem?.subject ?? "-"} />
        </div>
      </section>

      {primaryItem ? (
        <section className="miniCard">
          <h3>Primary item snapshot</h3>
          <div className="summaryGrid">
            <MetricCard label="Severity" value={getSeverity(primaryItem)} />
            <MetricCard
              label="Risk"
              value={getRiskScore(primaryItem) !== null ? String(getRiskScore(primaryItem)) : "-"}
            />
            <MetricCard label="Findings" value={String(getFindingCount(primaryItem))} />
            <MetricCard
              label="Confidence"
              value={getString(primaryItem.family?.signal_confidence) ?? "-"}
            />
          </div>
          <p className="compactText">{getSummary(primaryItem)}</p>
        </section>
      ) : null}

      <section className="miniCard">
        <h3>Returned subjects</h3>
        {items.length > 0 ? (
          <ul className="cleanList">
            {items.map((item) => (
              <li key={item.subject}>
                {item.subject} ({getSeverity(item)}, risk {getRiskScore(item) ?? "-"})
              </li>
            ))}
          </ul>
        ) : (
          <p className="muted">No item subjects were returned.</p>
        )}
      </section>

      <section className="miniCard">
        <h3>Raw JSON</h3>
        <pre>{asPrettyJson(response)}</pre>
      </section>
    </div>
  );
}

function EmptyState() {
  return (
    <section className="statusPanel">
      <p className="eyebrow">Ready</p>
      <h3>Run an analysis from the left panel</h3>
      <p className="muted">
        This workspace always asks the API for family summaries so Quick mode can render a verdict
        without falling back to raw JSON.
      </p>
    </section>
  );
}

export default function AnalyzePage() {
  const [activeTab, setActiveTab] = useState<AnalyzeTab>("url");
  const [mode, setMode] = useState<WorkspaceMode>("quick");
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
    const storedMode = window.localStorage.getItem(MODE_STORAGE_KEY);
    if (storedMode === "quick" || storedMode === "analyst") {
      setMode(storedMode);
    }
  }, []);

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
