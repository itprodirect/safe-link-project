import path from "path";

import { expect, test } from "@playwright/test";

const QR_FIXTURE = path.resolve(process.cwd(), "..", "tests", "fixtures", "qr", "qrcode_text.png");

test.beforeEach(async ({ page }) => {
  await page.addInitScript(() => {
    window.localStorage.clear();
  });

  await page.goto("/analyze");
  await expect(page.getByRole("heading", { name: "Unified Analyze Workspace" })).toBeVisible();
});

test("runs the URL flow and exposes analyst details", async ({ page }) => {
  await page.getByPlaceholder("https://example.com").fill("https://example.com");
  await page.getByRole("button", { name: "Analyze URL" }).click();

  await expect(page.getByText("Primary verdict")).toBeVisible();
  await expect(page.getByText("Subject: https://example.com")).toBeVisible();
  await expect(page.getByText("Flow: analyze")).toBeVisible();

  await page.getByRole("tab", { name: "Analyst" }).click();
  await expect(page.getByRole("heading", { name: "Contract summary" })).toBeVisible();
  await expect(page.getByText("Primary subject")).toBeVisible();
});

test("runs the email-header flow from the same workspace", async ({ page }) => {
  await page.getByRole("tab", { name: "Email" }).click();
  await page.getByLabel("Source label").fill("smoke-email");
  await page
    .getByLabel("Email headers")
    .fill("Authentication-Results: mx.example; spf=fail; dkim=fail; dmarc=fail");
  await page.getByRole("button", { name: "Analyze email headers" }).click();

  await expect(page.getByText("Primary verdict")).toBeVisible();
  await expect(page.getByText("Subject: smoke-email")).toBeVisible();
  await expect(page.getByText("Flow: analyze")).toBeVisible();
});

test("surfaces structured QR upload errors from the unified page", async ({ page }) => {
  await page.getByRole("tab", { name: "QR" }).click();
  await page.getByLabel("QR image file").setInputFiles(QR_FIXTURE);
  await page.getByRole("button", { name: "Scan QR" }).click();

  await expect(page.getByRole("heading", { name: "Request failed" })).toBeVisible();
  await expect(
    page.getByText(/QRC_(NO_URL_PAYLOADS|DECODER_UNAVAILABLE|MULTIPART_UNAVAILABLE)/)
  ).toBeVisible();
  await expect(page.getByText("Latest endpoint: POST /api/v1/qr/scan")).toBeVisible();
});

