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
    },
    analyst: {
      domain_anatomy: {
        submitted_url: "https://example.com",
        canonical_url: "https://example.com/",
        hostname: "example.com",
        canonical_hostname: "example.com",
        registrable_domain: "example.com",
        canonical_registrable_domain: "example.com",
        subdomain_labels: [],
        registrable_labels: ["example", "com"],
        idna_ascii_hostname: "example.com",
        idna_unicode_hostname: "example.com",
        is_ip_literal: false,
        ip_literal: null,
        obfuscated_ipv4: null,
        obfuscated_ipv4_notes: [],
        ipv6_mapped_ipv4: null,
        normalization_notes: []
      },
      evidence_rows: [],
      redirect_trace: null,
      suppression_trace: null
    }
  }
} as const;

const ANALYST_URL_RESPONSE = {
  schema_version: "2.0",
  flow: "analyze",
  mode: "single",
  input_type: "url",
  item_count: 1,
  item: {
    subject: "https://login.example.test",
    result: {
      input: {
        input_type: "url",
        content: "https://login.example.test",
        metadata: { network_enabled: true }
      },
      findings: [
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
              value:
                "https://login.example.test -> https://redirect.gateway.test -> https://final.example.org"
            },
            { label: "Domain Path", value: "example.test -> gateway.test -> example.org" },
            { label: "Redirect Hops", value: "2" }
          ],
          recommendations: ["Verify that the final site name is expected and trusted."]
        }
      ],
      overall_risk: 65,
      overall_severity: "HIGH",
      summary: "Strong warning signs were found in this destination.",
      analyzed_at: "2026-03-06T00:00:00Z"
    },
    family: {
      risk_score: 65,
      severity: "HIGH",
      summary: "Strong warning signs were found in this destination.",
      signal_confidence: "HIGH",
      reasons: ["This link places a familiar site name in the wrong part of the address."],
      recommendations: ["Verify the destination through a trusted bookmark."]
    },
    analyst: {
      domain_anatomy: {
        submitted_url: "https://login.example.test",
        canonical_url: "https://login.example.test/",
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
      evidence_rows: [
        {
          module: "url_structure",
          category: "URL002_DECEPTIVE_SUBDOMAIN",
          finding_key: "url_structure:URL002_DECEPTIVE_SUBDOMAIN",
          compare_key: "url_structure:URL002_DECEPTIVE_SUBDOMAIN",
          sort_index: 0,
          severity: "HIGH",
          confidence: "HIGH",
          cumulative_risk_score: 65,
          risk_delta: null,
          title: "Suspicious brand token appears in a subdomain",
          explanation: "A known brand token appears outside the registrable domain.",
          family_explanation: "This link places a familiar site name in the wrong part of the address.",
          recommendations: ["Verify the destination through a trusted bookmark."],
          evidence: [
            { key: "hostname", label: "Hostname", value: "login.example.test" },
            { key: "registrable_domain", label: "Registrable Domain", value: "example.test" }
          ],
          evidence_map: {
            hostname: "login.example.test",
            registrable_domain: "example.test"
          }
        },
        {
          module: "redirect",
          category: "RED002_CROSS_DOMAIN_REDIRECT",
          finding_key: "redirect:RED002_CROSS_DOMAIN_REDIRECT",
          compare_key: "redirect:RED002_CROSS_DOMAIN_REDIRECT",
          sort_index: 1,
          severity: "INFO",
          confidence: "MEDIUM",
          cumulative_risk_score: 40,
          risk_delta: null,
          title: "Redirect chain changes registrable domain",
          explanation: "The redirect chain moves across different registrable domains.",
          family_explanation: "This link starts on one site name and ends on a different site name.",
          recommendations: ["Verify that the final site name is expected and trusted."],
          evidence: [
            {
              key: "chain",
              label: "Chain",
              value:
                "https://login.example.test -> https://redirect.gateway.test -> https://final.example.org"
            },
            {
              key: "domain_path",
              label: "Domain Path",
              value: "example.test -> gateway.test -> example.org"
            }
          ],
          evidence_map: {
            chain:
              "https://login.example.test -> https://redirect.gateway.test -> https://final.example.org",
            domain_path: "example.test -> gateway.test -> example.org"
          }
        }
      ],
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
        content: "Authentication-Results: mx; spf=fail; dkim=fail; dmarc=fail",
        metadata: {}
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
  await expect(page.getByRole("heading", { name: "Domain anatomy" })).toHaveCount(0);
  await expect(page.getByRole("heading", { name: "Raw JSON" })).toHaveCount(0);
});

test("analyst mode renders URL-specific panels from structured v2 payloads", async ({ page }) => {
  await page.route("**/api/v2/analyze", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(ANALYST_URL_RESPONSE)
    });
  });

  await gotoAnalyze(page);
  await page.getByPlaceholder("https://example.com").fill("https://login.example.test");
  await page.getByRole("button", { name: "Analyze URL" }).click();
  await page.getByRole("tab", { name: "Analyst" }).click();

  await expect(page.getByRole("heading", { name: "Contract summary" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Domain anatomy" })).toBeVisible();
  await expect(page.getByText("login.example.test")).toBeVisible();
  await expect(page.getByRole("heading", { name: "Redirect path" })).toBeVisible();
  await expect(page.getByText("Cross-domain redirect")).toBeVisible();
  await expect(page.getByRole("heading", { name: "Suppression trace" })).toBeVisible();
  await expect(page.getByText("Suppressed: 1")).toBeVisible();
  await expect(page.getByRole("heading", { name: "Evidence panel" })).toBeVisible();
  await expect(page.getByText("Suspicious brand token appears in a subdomain")).toBeVisible();
  await expect(page.getByRole("button", { name: "redirect" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Raw JSON" })).toHaveCount(0);
});

test("analyst mode keeps email on the raw-details fallback", async ({ page }) => {
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
  await page.getByRole("tab", { name: "Analyst" }).click();
  await expect(page.getByRole("heading", { name: "Contract summary" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Raw JSON" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Domain anatomy" })).toHaveCount(0);
});
