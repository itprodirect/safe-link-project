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

export interface ApiItem {
  subject: string;
  result: Record<string, unknown>;
  family?: {
    risk_score: number;
    severity: string;
    summary: string;
    signal_confidence: string | null;
    reasons: string[];
    recommendations: string[];
  };
}

export type AnalyzeV2InputType = "url" | "email_headers" | "email_file";

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
  mode: "single" | "multi";
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

export function asPrettyJson(value: unknown): string {
  return JSON.stringify(value, null, 2);
}
