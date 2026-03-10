"use client";

import { useDeferredValue, useState } from "react";
import {
  ApiAnalystEvidenceRow,
  ApiDomainAnatomy,
  ApiFinding,
  ApiItem,
  ApiRedirectTrace,
  ApiSuppressionTrace,
  ApiWrappedResponse,
  asPrettyJson,
  getPrimaryItem,
  getResponseItems
} from "../../lib/api";

type ConfidenceLevel = "LOW" | "MEDIUM" | "HIGH";
type ActionLevel = "safe" | "caution" | "avoid" | "block";

interface VerdictContext {
  flow: string;
  inputType: string;
}

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

function getFindings(item: ApiItem): ApiFinding[] {
  return item.result.findings;
}

function getRankedFindings(item: ApiItem): ApiFinding[] {
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

function formatLabelList(values: string[]): string {
  return values.length > 0 ? values.join(" / ") : "-";
}

function metricValue(value: string | number | null | undefined): string {
  if (value === null || value === undefined) {
    return "-";
  }
  return String(value);
}

function rowMatchesSearch(row: ApiAnalystEvidenceRow, search: string): boolean {
  if (!search) {
    return true;
  }
  const haystack = [
    row.module,
    row.category,
    row.title,
    row.explanation,
    row.family_explanation,
    ...row.recommendations,
    ...row.evidence.map((entry) => `${entry.label} ${entry.value}`)
  ]
    .join(" ")
    .toLowerCase();
  return haystack.includes(search);
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
        <span className="badge">Confidence: {confidence ?? "Not provided"}</span>
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

function DomainAnatomy({ anatomy }: { anatomy: ApiDomainAnatomy }) {
  return (
    <section className="miniCard">
      <div className="panelHeaderRow">
        <div>
          <h3>Domain anatomy</h3>
          <p className="muted compactText">Normalized host and label breakdown for the submitted URL.</p>
        </div>
      </div>
      <div className="summaryGrid analystSummaryGrid">
        <MetricCard label="Submitted URL" value={anatomy.submitted_url} />
        <MetricCard label="Canonical URL" value={anatomy.canonical_url} />
        <MetricCard label="Hostname" value={metricValue(anatomy.hostname)} />
        <MetricCard label="Registrable domain" value={metricValue(anatomy.registrable_domain)} />
        <MetricCard label="Canonical host" value={metricValue(anatomy.canonical_hostname)} />
        <MetricCard
          label="Canonical registrable"
          value={metricValue(anatomy.canonical_registrable_domain)}
        />
        <MetricCard label="Subdomain labels" value={formatLabelList(anatomy.subdomain_labels)} />
        <MetricCard
          label="Registrable labels"
          value={formatLabelList(anatomy.registrable_labels)}
        />
        <MetricCard label="IDNA ASCII" value={metricValue(anatomy.idna_ascii_hostname)} />
        <MetricCard label="IDNA Unicode" value={metricValue(anatomy.idna_unicode_hostname)} />
        <MetricCard label="IP literal" value={anatomy.is_ip_literal ? "Yes" : "No"} />
        <MetricCard label="Literal value" value={metricValue(anatomy.ip_literal)} />
        <MetricCard label="Obfuscated IPv4" value={metricValue(anatomy.obfuscated_ipv4)} />
        <MetricCard label="IPv6 mapped IPv4" value={metricValue(anatomy.ipv6_mapped_ipv4)} />
      </div>
      {anatomy.obfuscated_ipv4_notes.length > 0 ? (
        <div className="anatomyNoteGroup">
          <strong>Obfuscation notes</strong>
          <ul className="cleanList">
            {anatomy.obfuscated_ipv4_notes.map((note) => (
              <li key={note}>{note}</li>
            ))}
          </ul>
        </div>
      ) : null}
      {anatomy.normalization_notes.length > 0 ? (
        <div className="anatomyNoteGroup">
          <strong>Normalization notes</strong>
          <ul className="cleanList">
            {anatomy.normalization_notes.map((note) => (
              <li key={note}>{note}</li>
            ))}
          </ul>
        </div>
      ) : null}
    </section>
  );
}

function RedirectPathView({ trace }: { trace: ApiRedirectTrace }) {
  const stateBadges = [
    trace.crosses_registrable_domain ? "Cross-domain redirect" : null,
    trace.max_hops_reached ? "Max hops reached" : null,
    trace.timed_out ? "Timed out" : null,
    trace.loop_target ? "Loop detected" : null,
    trace.request_error ? "Request error" : null
  ].filter((value): value is string => value !== null);

  return (
    <section className="miniCard">
      <div className="panelHeaderRow">
        <div>
          <h3>Redirect path</h3>
          <p className="muted compactText">Observed destination changes from the redirect analyzer.</p>
        </div>
        <span className="badge">Hops: {trace.hop_count}</span>
      </div>
      {stateBadges.length > 0 ? (
        <div className="badgeRow analystBadgeRow">
          {stateBadges.map((badge) => (
            <span className="badge" key={badge}>
              {badge}
            </span>
          ))}
        </div>
      ) : null}
      <div className="redirectTimeline" role="list">
        {trace.hops.map((hop, index) => (
          <div className="redirectHop" role="listitem" key={`${hop}-${index}`}>
            <span className="redirectStep">{index + 1}</span>
            <div>
              <strong>{hop}</strong>
              <p className="muted compactText">
                Registrable domain: {trace.registrable_domain_path[index] ?? "-"}
              </p>
            </div>
          </div>
        ))}
      </div>
      {trace.loop_target ? <p className="muted compactText">Loop target: {trace.loop_target}</p> : null}
      {trace.request_error ? <p className="muted compactText">Request error: {trace.request_error}</p> : null}
    </section>
  );
}

function SuppressionTracePanel({ trace }: { trace: ApiSuppressionTrace }) {
  return (
    <section className="miniCard">
      <div className="panelHeaderRow">
        <div>
          <h3>Suppression trace</h3>
          <p className="muted compactText">
            Allowlist rules that removed findings before the final analyst result was shaped.
          </p>
        </div>
        <span className="badge">Suppressed: {trace.suppressed_count}</span>
      </div>
      <div className="summaryGrid analystSummaryGrid">
        <MetricCard label="Hostname" value={metricValue(trace.hostname)} />
        <MetricCard
          label="Allowlist domains"
          value={formatLabelList(trace.configured_allowlist_domains)}
        />
        <MetricCard
          label="Category rules"
          value={formatLabelList(trace.configured_allowlist_categories)}
        />
        <MetricCard
          label="Finding rules"
          value={formatLabelList(trace.configured_allowlist_findings)}
        />
        <MetricCard
          label="Matched domains"
          value={formatLabelList(trace.matched_allowlist_domains)}
        />
      </div>
      {trace.suppressed_rows.length > 0 ? (
        <div className="resultListCompact">
          {trace.suppressed_rows.map((row) => (
            <article
              className="evidenceCard suppressionCard"
              key={`${row.module}-${row.category}-${row.matched_rule}`}
            >
              <div className="evidenceHeader">
                <div>
                  <h4>{row.category}</h4>
                  <p className="muted compactText">{row.reason}</p>
                </div>
                <div className="badgeRow analystBadgeRow">
                  <span className="badge">{row.module}</span>
                  <span className="badge">Scope: {row.suppression_scope}</span>
                  <span className="badge">Rule: {row.matched_rule}</span>
                </div>
              </div>
              <dl className="evidenceList">
                <div className="evidencePair">
                  <dt>Hostname</dt>
                  <dd>{row.hostname}</dd>
                </div>
                <div className="evidencePair">
                  <dt>Matched allowlist domain</dt>
                  <dd>{row.matched_allowlist_domain}</dd>
                </div>
              </dl>
            </article>
          ))}
        </div>
      ) : (
        <p className="muted">No findings were suppressed for the current allowlist inputs.</p>
      )}
    </section>
  );
}

function EvidencePanel({ rows }: { rows: ApiAnalystEvidenceRow[] }) {
  const [search, setSearch] = useState("");
  const [moduleFilter, setModuleFilter] = useState<string>("all");
  const deferredSearch = useDeferredValue(search.trim().toLowerCase());
  const modules = ["all", ...new Set(rows.map((row) => row.module))];
  const filteredRows = rows.filter((row) => {
    const matchesModule = moduleFilter === "all" || row.module === moduleFilter;
    return matchesModule && rowMatchesSearch(row, deferredSearch);
  });

  return (
    <section className="miniCard">
      <div className="panelHeaderRow">
        <div>
          <h3>Evidence panel</h3>
          <p className="muted compactText">Filter findings by detector module or free-text evidence.</p>
        </div>
        <span className="badge">Rows: {rows.length}</span>
      </div>
      <div className="evidenceToolbar">
        <label className="searchField">
          Search evidence
          <input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="hostname, redirect, punycode..."
          />
        </label>
        <div className="filterRow" aria-label="Filter evidence by module">
          {modules.map((moduleName) => {
            const active = moduleFilter === moduleName;
            const label = moduleName === "all" ? "All modules" : moduleName;
            return (
              <button
                key={moduleName}
                type="button"
                className={`chipButton${active ? " chipButtonActive" : ""}`}
                onClick={() => setModuleFilter(moduleName)}
              >
                {label}
              </button>
            );
          })}
        </div>
      </div>
      {filteredRows.length > 0 ? (
        <div className="resultListCompact">
          {filteredRows.map((row) => (
            <article className="evidenceCard" key={`${row.module}-${row.category}-${row.title}`}>
              <div className="evidenceHeader">
                <div>
                  <h4>{row.title}</h4>
                  <p className="muted compactText">{row.explanation}</p>
                </div>
                <div className="badgeRow analystBadgeRow">
                  <span className="badge">{row.module}</span>
                  <span className="badge">{row.category}</span>
                  <span className="badge">Risk: {row.cumulative_risk_score}</span>
                  <span className="badge">Confidence: {row.confidence}</span>
                </div>
              </div>
              <p className="compactText">{row.family_explanation}</p>
              {row.evidence.length > 0 ? (
                <dl className="evidenceList">
                  {row.evidence.map((entry) => (
                    <div className="evidencePair" key={`${row.category}-${entry.label}-${entry.value}`}>
                      <dt>{entry.label}</dt>
                      <dd>{entry.value}</dd>
                    </div>
                  ))}
                </dl>
              ) : null}
              {row.recommendations.length > 0 ? (
                <div className="anatomyNoteGroup">
                  <strong>Recommendations</strong>
                  <ul className="cleanList">
                    {row.recommendations.map((recommendation) => (
                      <li key={recommendation}>{recommendation}</li>
                    ))}
                  </ul>
                </div>
              ) : null}
            </article>
          ))}
        </div>
      ) : (
        <p className="muted">No evidence rows matched the current filters.</p>
      )}
    </section>
  );
}

function AnalystFallback({ response }: { response: ApiWrappedResponse }) {
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

export function QuickResult({ response }: { response: ApiWrappedResponse }) {
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

export function AnalystResult({ response }: { response: ApiWrappedResponse }) {
  const items = getResponseItems(response);
  const primaryItem = getPrimaryItem(response);
  const analyst = response.input_type === "url" ? primaryItem?.analyst : undefined;

  if (!primaryItem) {
    return <p className="muted">The API returned no items.</p>;
  }

  if (!analyst) {
    return <AnalystFallback response={response} />;
  }

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
          <MetricCard label="Primary subject" value={primaryItem.subject} />
        </div>
      </section>

      <section className="miniCard">
        <h3>Primary item snapshot</h3>
        <div className="summaryGrid">
          <MetricCard label="Severity" value={getSeverity(primaryItem)} />
          <MetricCard
            label="Risk"
            value={getRiskScore(primaryItem) !== null ? String(getRiskScore(primaryItem)) : "-"}
          />
          <MetricCard label="Findings" value={String(getFindingCount(primaryItem))} />
          <MetricCard label="Confidence" value={getConfidence(primaryItem) ?? "-"} />
        </div>
        <p className="compactText">{getSummary(primaryItem)}</p>
      </section>

      <DomainAnatomy anatomy={analyst.domain_anatomy} />
      {analyst.redirect_trace ? <RedirectPathView trace={analyst.redirect_trace} /> : null}
      {analyst.suppression_trace ? <SuppressionTracePanel trace={analyst.suppression_trace} /> : null}
      <EvidencePanel rows={analyst.evidence_rows} />

      {items.length > 1 ? (
        <section className="miniCard">
          <h3>Returned subjects</h3>
          <ul className="cleanList">
            {items.map((item) => (
              <li key={item.subject}>
                {item.subject} ({getSeverity(item)}, risk {getRiskScore(item) ?? "-"})
              </li>
            ))}
          </ul>
        </section>
      ) : null}
    </div>
  );
}

export function EmptyState() {
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



