const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

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

async function postJson(path, body) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body)
  });
  const payload = await response.json();
  return { response, payload };
}

async function run() {
  console.log(`[smoke] API base: ${API_BASE_URL}`);

  const health = await getJson("/health");
  await check(health.response.ok, "health check failed");
  await check(health.payload.status === "ok", "health payload missing status=ok");
  console.log("[smoke] health ok");

  const urlResult = await postJson("/api/v1/url/check", { url: "https://example.com" });
  await check(urlResult.response.ok, "url check failed");
  await check(urlResult.payload.schema_version === "1.0", "url schema_version mismatch");
  await check(urlResult.payload.mode === "single", "url mode should be single");
  await check(urlResult.payload.item_count === 1, "url item_count should be 1");
  console.log("[smoke] url check ok");

  const emailResult = await postJson("/api/v1/email/check", {
    headers: "Authentication-Results: mx; spf=pass; dkim=pass; dmarc=pass",
    source_label: "smoke"
  });
  await check(emailResult.response.ok, "email check failed");
  await check(emailResult.payload.flow === "email_check", "email flow mismatch");
  await check(emailResult.payload.mode === "single", "email mode should be single");
  console.log("[smoke] email check ok");

  const qrError = await postJson("/api/v1/qr/scan", {
    image_path: "C:/tmp/non-existent-smoke-qr.png",
    analyze_all: false
  });
  await check(qrError.response.status === 400, "qr expected 400 for missing image");
  const detail = qrError.payload?.detail ?? {};
  const error = detail?.error ?? {};
  await check(detail.schema_version === "1.0", "qr error schema_version mismatch");
  await check(error.code === "QRC_IMAGE_READ_ERROR", "qr error code mismatch");
  console.log("[smoke] qr error envelope ok");

  console.log("[smoke] all checks passed");
}

run().catch((error) => {
  console.error("[smoke] failure:", error.message);
  process.exit(1);
});
