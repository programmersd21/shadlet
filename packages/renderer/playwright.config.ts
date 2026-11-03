import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  retries: 0,
  reporter: "line",
  use: {
    browserName: "chromium",
    headless: true,
  },
  webServer: {
    command: "uv run --project ../.. python ../../tests/e2e/server.py",
    url: "http://127.0.0.1:8000",
    reuseExistingServer: false,
    timeout: 60_000,
  },
});
