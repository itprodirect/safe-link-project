import { expect, test, type Page } from "@playwright/test";

type Severity = "INFO" | "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";

interface MockFinding {
  module: string;
  category: string;
  severity: Severity;
  confidence: "LOW" | "MEDIUM" | "HIGH";
  risk_score: number;
  title: string;
  explanation: string;
  family_explanation: string;
  evidence: Array<{ label: string; value: string }>;
  recommendations: string[];
}

interface MockResponseOptions {
  subject: string;
  riskScore: number;
  severity: Severity;
  summary: string;
  reasons?: string[];
  recommendations?: string[];
  findings?: MockFinding[];
  detailedAnalyst?: boolean;
}

const DETAILED_FINDINGS: MockFinding[] = [
  {
    module: "url_structure",
    category: "URL002_DECEPTIVE_SUBDOMAIN",
    severity: "HIGH",
    confidence: "HIGH",
    risk_score: 65,
    title: "Suspicious brand token appears in a subdomain",
    explanation: "A known brand token appears outside the registrable domain.",
    family_explanation: "This link places a familiar site name in the wrong part of the address.",
    evidence: [
      { label: "Hostname", value: "login.example.test" },
      { label: "Registrable Domain", value: "example.test" }
    ],
    recommendations: ["Verify the destination through a trusted bookmark."]
  },
  {
    module: "redirect",
    category: "RED002_CROSS_DOMAIN_REDIRECT",
    severity: "INFO",
    confidence: "MEDIUM",
    risk_score: 40,
    title: "Redirect chain changes registrable domain",
    explanation: "The redirect chain moves across different registrable domains.",
    family_explanation: "This link starts on one site name and ends on a different site name.",
    evidence: [
      {
        label: "Chain",
        value: "https://login.example.test -> https://redirect.gateway.test -> https://final.example.org"
      },
      { label: "Domain Path", value: "example.test -> gateway.test -> example.org" },
      { label: "Redirect Hops", value: "2" }
    ],
    recommendations: ["Verify that the final site name is expected and trusted."]
  }
];

function makeFinding(overrides: Partial<MockFinding> = {}): MockFinding {
  const riskScore = overrides.risk_score ?? 35;
  const severity = overrides.severity ?? "MEDIUM";

  return {
    module: "url_structure",
    category: "URL001_WARNING_SIGNAL",
    severity,
    confidence: "MEDIUM",
    risk_score: riskScore,
    title: "Warning signal found",
    explanation: "The submitted destination has a warning signal.",
    family_explanation: "This destination has a warning signal that deserves review.",
    evidence: [{ label: "Risk", value: String(riskScore) }],
    recommendations: ["Verify this destination through a trusted source."],
    ...overrides
  };
}

function makeResponse({
  subject,
  riskScore,
  severity,
  summary,
  reasons = [],
  recommendations = [],
  findings = [],
  detailedAnalyst = false
}: MockResponseOptions) {
  return {
    schema_version: "2.0",
    flow: "analyze",
    mode: "single",
    input_type: "url",
    item_count: 1,
    item: {
      subject,
      result: {
        input: {
          input_type: "url",
          content: subject,
          metadata: {}
        },
        findings,
        overall_risk: riskScore,
        overall_severity: severity,
        summary,
        analyzed_at: "2026-03-06T00:00:00Z"
      },
      family: {
        risk_score: riskScore,
        severity,
        summary,
        signal_confidence: riskScore > 0 ? "HIGH" : null,
        reasons,
        recommendations
      },
      ...(detailedAnalyst
        ? {
            analyst: {
              domain_anatomy: {
                submitted_url: subject,
                canonical_url: `${subject}/`,
                hostname: "login.example.test",
                canonical_hostname: "login.example.test",
                registrable_domain: "example.test",
                canonical_registrable_domain: "example.test",
                subdomain_labels: ["login"],
                registrable_labels: ["example", "test"],
                idna_ascii_hostname: "login.example.test",
                idna_unicode_hostname: "login.example.test",
                is_ip_literal: false,
                ip_literal: null,
                obfuscated_ipv4: null,
                obfuscated_ipv4_notes: [],
                ipv6_mapped_ipv4: null,
                normalization_notes: []
              },
              evidence_rows: DETAILED_FINDINGS.map((finding, index) => ({
                module: finding.module,
                category: finding.category,
                finding_key: `${finding.module}:${finding.category}`,
                compare_key: `${finding.module}:${finding.category}`,
                sort_index: index,
                severity: finding.severity,
                confidence: finding.confidence,
                cumulative_risk_score: finding.risk_score,
                risk_delta: null,
                title: finding.title,
                explanation: finding.explanation,
                family_explanation: finding.family_explanation,
                recommendations: finding.recommendations,
                evidence: finding.evidence.map((entry) => ({
                  key: entry.label.toLowerCase().replaceAll(" ", "_"),
                  label: entry.label,
                  value: entry.value
                })),
                evidence_map: Object.fromEntries(
                  finding.evidence.map((entry) => [
                    entry.label.toLowerCase().replaceAll(" ", "_"),
                    entry.value
                  ])
                )
              })),
              redirect_trace: {
                hops: [
                  "https://login.example.test",
                  "https://redirect.gateway.test",
                  "https://final.example.org"
                ],
                start_url: "https://login.example.test",
                final_url: "https://final.example.org",
                registrable_domain_path: ["example.test", "gateway.test", "example.org"],
                hop_count: 2,
                crosses_registrable_domain: true,
                max_hops_reached: false,
                timed_out: false,
                loop_target: null,
                request_error: null
              },
              suppression_trace: {
                hostname: "login.example.test",
                configured_allowlist_domains: ["example.test"],
                configured_allowlist_categories: ["URL"],
                configured_allowlist_findings: [],
                matched_allowlist_domains: ["example.test"],
                suppressed_count: 1,
                suppressed_rows: [
                  {
                    module: "url_structure",
                    category: "URL003_NESTED_URL_PARAMETER",
                    finding_key: "url_structure:URL003_NESTED_URL_PARAMETER",
                    compare_key: "url_structure:URL003_NESTED_URL_PARAMETER:category:url",
                    sort_index: 0,
                    hostname: "login.example.test",
                    matched_allowlist_domain: "example.test",
                    suppression_scope: "category",
                    matched_rule: "URL",
                    reason:
                      "Suppressed because the hostname matched an allowlist domain and category prefix URL was enabled."
                  }
                ]
              }
            }
          }
        : {})
    }
  };
}

const SAFE_URL_RESPONSE = makeResponse({
  subject: "https://example.com",
  riskScore: 0,
  severity: "INFO",
  summary:
    "No obvious lookalike-link warning signs found. For important accounts, type the website address yourself."
});

const CAUTION_URL_RESPONSE = makeResponse({
  subject: "https://notice.example.com",
  riskScore: 35,
  severity: "MEDIUM",
  summary: "Some warning signs were found in this destination.",
  findings: [makeFinding()],
  reasons: ["This destination has a warning signal that deserves review."],
  recommendations: ["Verify this destination through a trusted source."]
});

const SUSPICIOUS_URL_RESPONSE = makeResponse({
  subject: "https://login.example.test",
  riskScore: 65,
  severity: "HIGH",
  summary: "Strong warning signs were found in this destination.",
  findings: DETAILED_FINDINGS,
  reasons: ["This link places a familiar site name in the wrong part of the address."],
  recommendations: ["Verify the destination through a trusted bookmark."],
  detailedAnalyst: true
});

const DANGEROUS_URL_RESPONSE = makeResponse({
  subject: "https://credential-theft.example.test",
  riskScore: 92,
  severity: "CRITICAL",
  summary: "Critical warning signs were found in this destination.",
  findings: [
    makeFinding({
      category: "URL999_CRITICAL_RISK",
      severity: "CRITICAL",
      confidence: "HIGH",
      risk_score: 92,
      family_explanation: "This destination has critical warning signals."
    })
  ],
  reasons: ["This destination has critical warning signals."],
  recommendations: ["Do not open the link or reply to the request."]
});

async function gotoAnalyze(page: Page) {
  await page.addInitScript(() => {
    window.localStorage.clear();
  });
  await page.goto("/analyze");
  await expect(
    page.getByRole("heading", { name: "Analyze a suspicious link or QR code" })
  ).toBeVisible();
}

async function mockAnalyzeResponse(page: Page, response: object, delayMs = 0) {
  await page.route("**/api/v2/analyze", async (route) => {
    if (delayMs > 0) {
      await new Promise((resolve) => setTimeout(resolve, delayMs));
    }
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(response)
    });
  });
}

async function mockAnalyzeFailure(page: Page) {
  await page.route("**/api/v2/analyze", async (route) => {
    await route.fulfill({
      status: 503,
      contentType: "application/json",
      body: JSON.stringify({
        detail: {
          schema_version: "1.0",
          error: {
            code: "API_UNAVAILABLE",
            message: "The analysis service is temporarily unavailable.",
            status: 503
          }
        }
      })
    });
  });
}

async function mockQrFailure(page: Page, code: string) {
  await page.route("**/api/v1/qr/scan", async (route) => {
    await route.fulfill({
      status: 422,
      contentType: "application/json",
      body: JSON.stringify({
        detail: {
          schema_version: "1.0",
          error: {
            code,
            message: "QR scan could not return a URL.",
            status: 422
          }
        }
      })
    });
  });
}

async function submitUrl(page: Page, url: string) {
  await page.getByLabel("URL").fill(url);
  await page.getByRole("button", { name: "Analyze" }).click();
}

async function uploadQrImage(page: Page) {
  await page.getByLabel("QR image (optional)").setInputFiles({
    name: "qr.png",
    mimeType: "image/png",
    buffer: Buffer.from([0x89, 0x50, 0x4e, 0x47])
  });
}

test("URL analysis renders the simplified verdict hierarchy with keyboard-accessible evidence", async ({
  page
}) => {
  await mockAnalyzeResponse(page, SUSPICIOUS_URL_RESPONSE);
  await gotoAnalyze(page);
  await submitUrl(page, "https://login.example.test");

  const verdictCard = page.getByTestId("analyze-verdict-card");
  await expect(verdictCard).toBeVisible();
  await expect(verdictCard.getByRole("heading", { name: "Verdict" })).toBeVisible();
  await expect(verdictCard.getByText("Suspicious", { exact: true })).toBeVisible();

  const riskPill = page.getByTestId("analyze-risk-pill");
  await expect(riskPill).toHaveText("High");
  await expect(riskPill).toHaveAccessibleName("Risk level High");

  const keyReasons = page.getByTestId("analyze-key-reasons");
  await expect(keyReasons.getByRole("heading", { name: "Key reasons" })).toBeVisible();
  await expect(keyReasons.getByRole("listitem")).toHaveCount(1);

  const nextActions = page.getByTestId("analyze-next-actions");
  await expect(nextActions.getByRole("heading", { name: "What to do next" })).toBeVisible();
  await expect(nextActions.getByRole("listitem")).toHaveCount(3);

  const technicalDetails = page.getByTestId("analyze-technical-details");
  const technicalSummary = technicalDetails.locator("summary").first();
  await expect(technicalDetails).toBeVisible();
  await expect(technicalDetails).toHaveJSProperty("open", false);
  await expect(technicalDetails.locator("h3", { hasText: "Domain anatomy" })).toBeHidden();

  await technicalSummary.focus();
  await expect(technicalSummary).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(technicalDetails).toHaveJSProperty("open", true);
  await expect(technicalDetails.locator("h3", { hasText: "Domain anatomy" })).toBeVisible();
  await expect(technicalDetails.locator("h3", { hasText: "Redirect path" })).toBeVisible();
  await expect(technicalDetails.locator("h3", { hasText: "Suppression trace" })).toBeVisible();
  await expect(technicalDetails.locator("h3", { hasText: "Evidence panel" })).toBeVisible();
});

test("initial, validation, and focus states stay accessible", async ({ page }) => {
  await gotoAnalyze(page);

  await expect(page.getByLabel("URL")).toHaveValue("");
  await expect(page.getByRole("heading", { name: "Paste a link or upload a QR image" })).toBeVisible();
  await expect(page.getByTestId("analyze-verdict-card")).toHaveCount(0);

  await page.keyboard.press("Tab");
  await expect(page.getByRole("link", { name: "Analyze" })).toBeFocused();
  await page.keyboard.press("Tab");
  await expect(page.getByLabel("URL")).toBeFocused();
  await page.keyboard.press("Tab");
  await expect(page.getByLabel("QR image (optional)")).toBeFocused();
  await page.keyboard.press("Tab");
  await expect(page.getByRole("button", { name: "Analyze" })).toBeFocused();

  await page.getByRole("button", { name: "Analyze" }).click();
  const validationMessage = page.getByTestId("analyze-validation-message");
  await expect(validationMessage).toHaveText("Paste a URL or upload a QR image to analyze.");
  await expect(validationMessage).toHaveAttribute("role", "alert");
  await expect(page.getByLabel("URL")).toHaveAttribute("aria-invalid", "true");
});

test("loading state disables inputs and announces progress", async ({ page }) => {
  await mockAnalyzeResponse(page, SAFE_URL_RESPONSE, 500);
  await gotoAnalyze(page);
  await submitUrl(page, "https://example.com");

  await expect(page.getByRole("heading", { name: "Analyzing this submission" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Analyzing..." })).toBeDisabled();
  await expect(page.getByLabel("URL")).toBeDisabled();
  await expect(page.getByLabel("QR image (optional)")).toBeDisabled();
  await expect(page.getByTestId("analyze-result-area")).toHaveAttribute("aria-busy", "true");

  await expect(page.getByTestId("analyze-verdict-card")).toBeVisible();
});

test("URL API failure is plain-English and does not replace a prior success", async ({ page }) => {
  await mockAnalyzeResponse(page, SAFE_URL_RESPONSE);
  await gotoAnalyze(page);
  await submitUrl(page, "https://example.com");
  await expect(page.getByTestId("analyze-verdict-card").getByText("Safe", { exact: true })).toBeVisible();

  await page.unroute("**/api/v2/analyze");
  await mockAnalyzeFailure(page);
  await submitUrl(page, "https://offline.example.test");

  await expect(page.getByRole("heading", { name: "Request failed" })).toBeVisible();
  await expect(page.getByText("The analysis service is temporarily unavailable.")).toBeVisible();
  await expect(page.getByText("The previous successful result is still shown below.")).toBeVisible();
  await expect(page.getByTestId("analyze-verdict-card").getByText("Safe", { exact: true })).toBeVisible();
});

test("validation does not clear previous results for mixed or invalid QR inputs", async ({ page }) => {
  await mockAnalyzeResponse(page, SAFE_URL_RESPONSE);
  await gotoAnalyze(page);
  await submitUrl(page, "https://example.com");
  await expect(page.getByTestId("analyze-verdict-card")).toBeVisible();

  await uploadQrImage(page);
  await page.getByRole("button", { name: "Analyze" }).click();
  await expect(page.getByTestId("analyze-validation-message")).toHaveText(
    "Choose either a URL or a QR image, not both."
  );
  await expect(page.getByTestId("analyze-verdict-card")).toBeVisible();

  await page.getByLabel("URL").fill("");
  await page.getByLabel("QR image (optional)").setInputFiles({
    name: "not-a-qr.txt",
    mimeType: "text/plain",
    buffer: Buffer.from("not a qr image")
  });
  await page.getByRole("button", { name: "Analyze" }).click();
  await expect(page.getByTestId("analyze-validation-message")).toHaveText(
    "Upload an image file for QR scanning."
  );
  await expect(page.getByTestId("analyze-verdict-card")).toBeVisible();
});

for (const code of [
  "QRC_DECODER_UNAVAILABLE",
  "QRC_MULTIPART_UNAVAILABLE",
  "QRC_NO_URL_PAYLOADS"
]) {
  test(`QR error ${code} is readable and actionable`, async ({ page }) => {
    await mockQrFailure(page, code);
    await gotoAnalyze(page);
    await uploadQrImage(page);
    await page.getByRole("button", { name: "Analyze" }).click();

    await expect(page.getByRole("heading", { name: "Request failed" })).toBeVisible();
    await expect(page.getByText(code)).toBeVisible();
    await expect(page.getByText(/paste the URL|Upload a QR code/i)).toBeVisible();
  });
}

test.describe("display mapping", () => {
  const variants = [
    {
      name: "safe / Low",
      response: SAFE_URL_RESPONSE,
      url: "https://example.com",
      verdict: "Safe",
      risk: "Low"
    },
    {
      name: "caution / Medium",
      response: CAUTION_URL_RESPONSE,
      url: "https://notice.example.com",
      verdict: "Caution",
      risk: "Medium"
    },
    {
      name: "avoid / Suspicious / High",
      response: SUSPICIOUS_URL_RESPONSE,
      url: "https://login.example.test",
      verdict: "Suspicious",
      risk: "High"
    },
    {
      name: "block / Dangerous / Critical",
      response: DANGEROUS_URL_RESPONSE,
      url: "https://credential-theft.example.test",
      verdict: "Dangerous",
      risk: "Critical"
    }
  ];

  for (const variant of variants) {
    test(`${variant.name} result renders expected labels`, async ({ page }) => {
      await mockAnalyzeResponse(page, variant.response);
      await gotoAnalyze(page);
      await submitUrl(page, variant.url);

      const verdictCard = page.getByTestId("analyze-verdict-card");
      await expect(verdictCard.getByText(variant.verdict, { exact: true })).toBeVisible();
      const riskPill = page.getByTestId("analyze-risk-pill");
      await expect(riskPill).toHaveText(variant.risk);
      await expect(riskPill).toHaveAccessibleName(`Risk level ${variant.risk}`);
    });
  }
});

test("mobile viewport keeps the input and result cards usable", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await mockAnalyzeResponse(page, SUSPICIOUS_URL_RESPONSE);
  await gotoAnalyze(page);

  await expect(page.getByTestId("analyze-input-card")).toBeVisible();
  await expect(page.getByLabel("URL")).toBeVisible();
  await expect(page.getByRole("button", { name: "Analyze" })).toBeVisible();

  await submitUrl(page, "https://login.example.test");
  await expect(page.getByTestId("analyze-verdict-card")).toBeVisible();
  await expect(page.getByTestId("analyze-key-reasons")).toBeVisible();
  await expect(page.getByTestId("analyze-next-actions")).toBeVisible();

  const reasonsBox = await page.getByTestId("analyze-key-reasons").boundingBox();
  const actionsBox = await page.getByTestId("analyze-next-actions").boundingBox();
  expect(reasonsBox).not.toBeNull();
  expect(actionsBox).not.toBeNull();
  expect(actionsBox!.y).toBeGreaterThan(reasonsBox!.y);
});
