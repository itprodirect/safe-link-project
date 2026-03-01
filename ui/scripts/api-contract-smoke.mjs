const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";
const UI_ORIGIN = process.env.NEXT_PUBLIC_UI_ORIGIN ?? "http://127.0.0.1:3000";

async function check(condition, message) {
  if (!condition) {
    throw new Error(message);
  }
}

async function getJson(path) {
  const response = await fetch(`${API_BASE_URL}${path}`);
  const payload = await response.json();
  return { response, payload };
}

async function preflight(path, origin) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "OPTIONS",
    headers: {
      Origin: origin,
      "Access-Control-Request-Method": "POST",
      "Access-Control-Request-Headers": "content-type"
    }
  });
  return { response };
}

async function postJson(path, body) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body)
  });
  const payload = await response.json();
  return { response, payload };
}

async function postForm(path, formData) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    body: formData
  });
  const payload = await response.json();
  return { response, payload };
}

async function run() {
  console.log(`[smoke] API base: ${API_BASE_URL}`);
  console.log(`[smoke] UI origin: ${UI_ORIGIN}`);

  const health = await getJson("/health");
  await check(health.response.ok, "health check failed");
  await check(health.payload.status === "ok", "health payload missing status=ok");
  console.log("[smoke] health ok");

  const corsPreflight = await preflight("/api/v1/url/check", UI_ORIGIN);
  await check(corsPreflight.response.ok, "cors preflight failed");
  const allowOrigin = corsPreflight.response.headers.get("access-control-allow-origin");
  await check(
    allowOrigin === UI_ORIGIN || allowOrigin === "*",
    `cors allow-origin mismatch (${allowOrigin ?? "missing"})`
  );
  console.log("[smoke] cors preflight ok");

  const urlResult = await postJson("/api/v1/url/check", { url: "https://example.com" });
  await check(urlResult.response.ok, "url check failed");
  await check(urlResult.payload.schema_version === "1.0", "url schema_version mismatch");
  await check(urlResult.payload.mode === "single", "url mode should be single");
  await check(urlResult.payload.item_count === 1, "url item_count should be 1");
  console.log("[smoke] url check ok");

  const allowlistScopedResult = await postJson("/api/v1/url/check", {
    url: "https://xn--pple-43d.com",
    allowlist_domains: ["xn--pple-43d.com"],
    allowlist_categories: ["NONE"],
    allowlist_findings: ["HMG002_PUNYCODE_VISIBILITY"]
  });
  await check(allowlistScopedResult.response.ok, "url allowlist-finding check failed");
  const scopedFindings = allowlistScopedResult.payload?.item?.result?.findings ?? [];
  const scopedCategories = new Set(scopedFindings.map((finding) => finding.category));
  await check(
    !scopedCategories.has("HMG002_PUNYCODE_VISIBILITY"),
    "allowlist-finding did not suppress HMG002_PUNYCODE_VISIBILITY"
  );
  await check(
    scopedCategories.has("HMG003_MIXED_SCRIPT_HOSTNAME"),
    "allowlist-finding check should retain non-targeted HMG003"
  );
  console.log("[smoke] allowlist finding scope ok");

  const emailResult = await postJson("/api/v1/email/check", {
    headers: "Authentication-Results: mx; spf=pass; dkim=pass; dmarc=pass",
    source_label: "smoke"
  });
  await check(emailResult.response.ok, "email check failed");
  await check(emailResult.payload.flow === "email_check", "email flow mismatch");
  await check(emailResult.payload.mode === "single", "email mode should be single");
  console.log("[smoke] email check ok");

  const formData = new FormData();
  formData.append("file", new Blob(["not-a-valid-image"]), "smoke-invalid.png");
  formData.append("analyze_all", "false");
  const qrError = await postForm("/api/v1/qr/scan", formData);
  await check(
    qrError.response.status === 400 || qrError.response.status === 503,
    "qr expected 400/503 for invalid upload or decoder-unavailable"
  );
  const detail = qrError.payload?.detail ?? {};
  const error = detail?.error ?? {};
  await check(detail.schema_version === "1.0", "qr error schema_version mismatch");
  await check(
    error.code === "QRC_IMAGE_READ_ERROR" || error.code === "QRC_DECODER_UNAVAILABLE",
    "qr error code mismatch"
  );
  console.log("[smoke] qr error envelope ok");

  console.log("[smoke] all checks passed");
}

run().catch((error) => {
  console.error("[smoke] failure:", error.message);
  process.exit(1);
});
