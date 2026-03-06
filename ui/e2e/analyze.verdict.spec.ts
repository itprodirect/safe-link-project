import { expect, test, type Page } from "@playwright/test";

const SAFE_URL_RESPONSE = {
  schema_version: "2.0",
  flow: "analyze",
  mode: "single",
  input_type: "url",
  item_count: 1,
  item: {
    subject: "https://example.com",
    result: {
      input: {
        input_type: "url",
        content: "https://example.com",
        metadata: {}
      },
      findings: [],
      overall_risk: 0,
      overall_severity: "INFO",
      summary:
        "No obvious lookalike-link warning signs found. For important accounts, type the website address yourself.",
      analyzed_at: "2026-03-06T00:00:00Z"
    },
    family: {
      risk_score: 0,
      severity: "INFO",
      summary:
        "No obvious lookalike-link warning signs found. For important accounts, type the website address yourself.",
      signal_confidence: null,
      reasons: [],
      recommendations: []
    }
  }
} as const;

const BLOCK_EMAIL_RESPONSE = {
  schema_version: "2.0",
  flow: "analyze",
  mode: "single",
  input_type: "email_headers",
  item_count: 1,
  item: {
    subject: "finance-alert",
    result: {
      input: {
        input_type: "email_headers",
        content: "Authentication-Results: mx; spf=fail; dkim=fail; dmarc=fail"
      },
      findings: [
        {
          module: "email_auth",
          category: "EML301_DMARC_FAIL",
          severity: "CRITICAL",
          confidence: "HIGH",
          risk_score: 95,
          title: "DMARC policy check failed",
          explanation: "DMARC status indicates a fail or policy error.",
          family_explanation: "The sender's domain policy check (DMARC) failed.",
          evidence: [],
          recommendations: ["Do not act on sensitive requests until verified independently."]
        },
        {
          module: "email_auth",
          category: "EML201_DKIM_FAIL",
          severity: "HIGH",
          confidence: "HIGH",
          risk_score: 80,
          title: "DKIM signature validation failed",
          explanation: "DKIM status indicates a failed or broken signature.",
          family_explanation: "The email's signed authenticity check (DKIM) did not pass.",
          evidence: [],
          recommendations: ["Treat the message as suspicious until independently verified."]
        }
      ],
      overall_risk: 95,
      overall_severity: "CRITICAL",
      summary:
        "High-risk email-authentication warning. Do not trust links or urgent requests until independently verified.",
      analyzed_at: "2026-03-06T00:00:00Z"
    },
    family: {
      risk_score: 95,
      severity: "CRITICAL",
      summary:
        "High-risk email-authentication warning. Do not trust links or urgent requests until independently verified.",
      signal_confidence: "HIGH",
      reasons: [
        "The sender's domain policy check (DMARC) failed.",
        "The email's signed authenticity check (DKIM) did not pass."
      ],
      recommendations: [
        "Do not act on sensitive requests until verified independently.",
        "Treat the message as suspicious until independently verified."
      ]
    }
  }
} as const;

async function gotoAnalyze(page: Page) {
  await page.addInitScript(() => {
    window.localStorage.clear();
  });
  await page.goto("/analyze");
  await expect(page.getByRole("heading", { name: "Unified Analyze Workspace" })).toBeVisible();
}

test("quick mode presents a safe decision without analyst-only details", async ({ page }) => {
  await page.route("**/api/v2/analyze", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(SAFE_URL_RESPONSE)
    });
  });

  await gotoAnalyze(page);
  await page.getByPlaceholder("https://example.com").fill("https://example.com");
  await page.getByRole("button", { name: "Analyze URL" }).click();

  await expect(page.getByText("Action: Safe")).toBeVisible();
  await expect(page.getByText("Safe to continue")).toBeVisible();
  await expect(
    page.getByText("This destination did not show strong warning signs in this scan.")
  ).toBeVisible();
  await expect(
    page.getByText(
      "Proceed only if you expected this item, and use trusted bookmarks for sensitive accounts."
    )
  ).toBeVisible();
  await expect(page.getByRole("heading", { name: "Raw JSON" })).toHaveCount(0);
});

test("quick mode rewrites technical email outcomes into plain-language decisions", async ({
  page
}) => {
  await page.route("**/api/v2/analyze", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(BLOCK_EMAIL_RESPONSE)
    });
  });

  await gotoAnalyze(page);
  await page.getByRole("tab", { name: "Email" }).click();
  await page.getByLabel("Source label").fill("finance-alert");
  await page
    .getByLabel("Email headers")
    .fill("Authentication-Results: mx; spf=fail; dkim=fail; dmarc=fail");
  await page.getByRole("button", { name: "Analyze email headers" }).click();

  await expect(page.getByText("Action: Block")).toBeVisible();
  await expect(page.getByText("Block and report")).toBeVisible();
  await expect(
    page.getByText("This message failed key trust checks and should be treated as suspicious.")
  ).toBeVisible();
  await expect(
    page.getByText(
      "The sender domain did not match its own policy, which is a strong warning sign."
    )
  ).toBeVisible();
  await expect(
    page.getByText("The message signature check failed, which can mean spoofing or tampering.")
  ).toBeVisible();
  await expect(
    page.getByText("Do not follow sensitive requests until you verify them another way.")
  ).toBeVisible();
  await expect(
    page.getByText("Treat this message as suspicious until you verify it another way.")
  ).toBeVisible();
});
