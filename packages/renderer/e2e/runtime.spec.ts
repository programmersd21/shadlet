import { expect, test } from "@playwright/test";

test("connects, loads packaged React extensions, and syncs URL state", async ({
  page,
}) => {
  await page.goto("http://127.0.0.1:8000/?page=1");
  await expect(page.getByText("count: 0")).toBeVisible();
  await expect(page).toHaveURL(/\/\?page=1$/);
  const initialUrl = page.url();
  const extension = page.getByTestId("extension");
  await expect(extension).toHaveText("extension ready");
  await expect(extension).toHaveCSS("color", "rgb(1, 2, 3)");

  await page.getByRole("button", { name: "increment" }).click();
  await expect(page.getByText("count: 1")).toBeVisible();

  await page.getByRole("button", { name: "next page" }).click();
  await expect(page).toHaveURL(/\/\?page=2$/);
  await expect(page.getByText("page: 2")).toBeVisible();

  await page.goBack();
  await expect(page).toHaveURL(initialUrl);
  await expect(page.getByText("page: 1")).toBeVisible();
});
