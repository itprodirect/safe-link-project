export interface ApiErrorEnvelope {
  detail?: {
    schema_version?: string;
    error?: {
      code?: string;
      message?: string;
      status?: number;
    };
  };
}

export interface ApiEvidence {
  key: string;
  label: string;
  value: string;
}

export interface ApiFinding {
  module: string;
  category: string;
  severity: string;
  confidence: string;
  risk_score: number;
  title: string;
  explanation: string;
  family_explanation: string;
  evidence: ApiEvidence[];
  recommendations: string[];
}

export interface ApiAnalysisResult {
  input: {
    input_type: string;
    content: string;
    metadata: Record<string, unknown>;
  };
  findings: ApiFinding[];
  overall_risk: number;
  overall_severity: string;
  summary: string;
  analyzed_at: string;
}

export interface ApiFamilyPayload {
  risk_score: number;
  severity: string;
  summary: string;
  signal_confidence: string | null;
  reasons: string[];
  recommendations: string[];
}

export interface ApiAnalystEvidenceRow {
  module: string;
  category: string;
  finding_key: string;
  compare_key: string;
  sort_index: number;
  severity: string;
  confidence: string;
  cumulative_risk_score: number;
  risk_delta: number | null;
  title: string;
  explanation: string;
  family_explanation: string;
  recommendations: string[];
  evidence: ApiEvidence[];
  evidence_map: Record<string, string>;
}

export interface ApiDomainAnatomy {
  submitted_url: string;
  canonical_url: string;
  hostname: string | null;
  canonical_hostname: string | null;
  registrable_domain: string | null;
  canonical_registrable_domain: string | null;
  subdomain_labels: string[];
  registrable_labels: string[];
  idna_ascii_hostname: string | null;
  idna_unicode_hostname: string | null;
  is_ip_literal: boolean;
  ip_literal: string | null;
  obfuscated_ipv4: string | null;
  obfuscated_ipv4_notes: string[];
  ipv6_mapped_ipv4: string | null;
  normalization_notes: string[];
}

export interface ApiRedirectTrace {
  hops: string[];
  start_url: string;
  final_url: string;
  registrable_domain_path: string[];
  hop_count: number;
  crosses_registrable_domain: boolean;
  max_hops_reached: boolean;
  timed_out: boolean;
  loop_target: string | null;
  request_error: string | null;
}

export interface ApiSuppressionTraceRow {
  module: string;
  category: string;
  finding_key: string;
  compare_key: string;
  sort_index: number;
  hostname: string;
  matched_allowlist_domain: string;
  suppression_scope: "category" | "finding";
  matched_rule: string;
  reason: string;
}

export interface ApiSuppressionTrace {
  hostname: string | null;
  configured_allowlist_domains: string[];
  configured_allowlist_categories: string[];
  configured_allowlist_findings: string[];
  matched_allowlist_domains: string[];
  suppressed_count: number;
  suppressed_rows: ApiSuppressionTraceRow[];
}

export interface ApiUrlAnalystPayload {
  domain_anatomy: ApiDomainAnatomy;
  evidence_rows: ApiAnalystEvidenceRow[];
  redirect_trace?: ApiRedirectTrace | null;
  suppression_trace?: ApiSuppressionTrace | null;
}

export interface ApiItem {
  subject: string;
  result: ApiAnalysisResult;
  family?: ApiFamilyPayload;
  analyst?: ApiUrlAnalystPayload;
}

export type AnalyzeV2InputType = "url" | "email_headers" | "email_file";
export type ApiWrappedMode = "single" | "multi";

export interface AnalyzeV2Request {
  input_type: AnalyzeV2InputType;
  content: string;
  subject?: string;
  family?: boolean;
  allowlist_domains?: string[];
  allowlist_categories?: string[];
  allowlist_findings?: string[];
  network_enabled?: boolean;
  network_max_hops?: number;
  network_timeout?: number;
}

export interface ApiWrappedResponse {
  schema_version: string;
  flow: string;
  mode: ApiWrappedMode;
  input_type: string;
  item_count: number;
  item?: ApiItem;
  items?: ApiItem[];
  [key: string]: unknown;
}

export interface AnalyzeV2Response extends ApiWrappedResponse {
  schema_version: "2.0";
  flow: "analyze";
  mode: "single";
  input_type: AnalyzeV2InputType;
  item: ApiItem;
}

export interface QrScanResponse extends ApiWrappedResponse {
  schema_version: "1.0";
  flow: "qr_scan";
  input_type: "url";
}

const DEFAULT_BASE_URL = "http://127.0.0.1:8000";
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? DEFAULT_BASE_URL;

export class ApiRequestError extends Error {
  code?: string;
  status: number;

  constructor(message: string, status: number, code?: string) {
    super(message);
    this.status = status;
    this.code = code;
  }
}

async function parseApiResponse<T>(response: Response): Promise<T> {
  let payload: unknown = null;
  try {
    payload = await response.json();
  } catch {
    payload = null;
  }

  if (!response.ok) {
    const errorPayload = (payload as ApiErrorEnvelope) ?? {};
    const code = errorPayload.detail?.error?.code;
    const message = errorPayload.detail?.error?.message ?? `API request failed (${response.status})`;
    throw new ApiRequestError(message, response.status, code);
  }

  return payload as T;
}

export async function postApi<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    cache: "no-store"
  });
  return parseApiResponse<T>(response);
}

export async function postApiForm<T>(path: string, body: FormData): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    body,
    cache: "no-store"
  });
  return parseApiResponse<T>(response);
}

export async function analyzeV2(request: AnalyzeV2Request): Promise<AnalyzeV2Response> {
  return postApi<AnalyzeV2Response>("/api/v2/analyze", request);
}

export async function scanQr(body: FormData): Promise<QrScanResponse> {
  return postApiForm<QrScanResponse>("/api/v1/qr/scan", body);
}

export function getResponseItems(response: ApiWrappedResponse): ApiItem[] {
  if (response.mode === "multi") {
    return response.items ?? [];
  }
  return response.item ? [response.item] : [];
}

export function getPrimaryItem(response: ApiWrappedResponse): ApiItem | null {
  return getResponseItems(response)[0] ?? null;
}

export function asPrettyJson(value: unknown): string {
  return JSON.stringify(value, null, 2);
}
