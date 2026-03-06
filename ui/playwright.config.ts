import { defineConfig } from "@playwright/test";

const uiOrigin = process.env.NEXT_PUBLIC_UI_ORIGIN ?? "http://127.0.0.1:3000";

export default defineConfig({
  testDir: "./e2e",
  timeout: 45_000,
  fullyParallel: false,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI
    ? [["list"], ["html", { open: "never" }]]
    : [["list"]],
  use: {
    baseURL: uiOrigin,
    headless: true,
    trace: "retain-on-failure"
  }
});
