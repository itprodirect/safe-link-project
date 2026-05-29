import path from "path";

import { expect, test } from "@playwright/test";

const QR_FIXTURE = path.resolve(process.cwd(), "..", "tests", "fixtures", "qr", "qrcode_text.png");

test.beforeEach(async ({ page }) => {
  await page.goto("/analyze");
});

test("shows the simplified analyze shell and blank input card", async ({ page }) => {
  await expect(
    page.getByRole("heading", { name: "Analyze a suspicious link or QR code" })
  ).toBeVisible();
  await expect(page.getByText("Paste a link or upload a QR image to get a clear verdict.")).toBeVisible();
  await expect(page.getByTestId("analyze-shell")).toBeVisible();
  await expect(page.getByTestId("analyze-input-card")).toBeVisible();

  const urlInput = page.getByLabel("URL");
  await expect(urlInput).toBeVisible();
  await expect(urlInput).toHaveValue("");
  await expect(page.getByLabel("QR image (optional)")).toBeVisible();
  await expect(page.getByRole("button", { name: "Analyze" })).toBeVisible();

  await expect(page.getByRole("tab", { name: "URL" })).toHaveCount(0);
  await expect(page.getByRole("tab", { name: "Email" })).toHaveCount(0);
  await expect(page.getByRole("tab", { name: "QR" })).toHaveCount(0);
  await expect(page.getByRole("tab", { name: "Analyst" })).toHaveCount(0);
  await expect(page.getByLabel("Email headers")).toHaveCount(0);
});

test("validates empty and mixed input without clearing a successful URL result", async ({ page }) => {
  await page.getByRole("button", { name: "Analyze" }).click();
  await expect(page.getByTestId("analyze-validation-message")).toHaveText(
    "Paste a URL or upload a QR image to analyze."
  );

  await page.getByLabel("URL").fill("https://example.com");
  await page.getByRole("button", { name: "Analyze" }).click();
  await expect(page.getByTestId("analyze-verdict-card")).toBeVisible();
  await expect(page.getByTestId("analyze-risk-pill")).toBeVisible();
  await expect(page.getByTestId("analyze-key-reasons")).toBeVisible();
  await expect(page.getByTestId("analyze-next-actions")).toBeVisible();
  await expect(page.getByTestId("analyze-technical-details")).toHaveJSProperty("open", false);

  await page.getByLabel("QR image (optional)").setInputFiles(QR_FIXTURE);
  await page.getByRole("button", { name: "Analyze" }).click();
  await expect(page.getByTestId("analyze-validation-message")).toHaveText(
    "Choose either a URL or a QR image, not both."
  );
  await expect(page.getByTestId("analyze-verdict-card")).toBeVisible();
});

test("surfaces structured QR upload errors from the simplified page", async ({ page }) => {
  await page.getByLabel("QR image (optional)").setInputFiles(QR_FIXTURE);
  await page.getByRole("button", { name: "Analyze" }).click();

  await expect(page.getByRole("heading", { name: "Request failed" })).toBeVisible();
  await expect(
    page.getByText(/QRC_(NO_URL_PAYLOADS|DECODER_UNAVAILABLE|MULTIPART_UNAVAILABLE)/)
  ).toBeVisible();
  await expect(page.getByText("Latest endpoint: POST /api/v1/qr/scan")).toBeVisible();
});
