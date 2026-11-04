import { expect, test } from "@playwright/test";
import axe from "axe-core";

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

test("server-side table search sends the query to Python", async ({ page }) => {
  const sentFrames: string[] = [];
  const receivedFrames: string[] = [];
  page.on("websocket", (socket) => {
    socket.on("framesent", (frame) => sentFrames.push(String(frame.payload)));
    socket.on("framereceived", (frame) =>
      receivedFrames.push(String(frame.payload)),
    );
  });
  await page.goto("http://127.0.0.1:8000/");
  await expect(page.getByRole("cell", { name: "Ruby" })).toBeVisible();
  const initMessage = receivedFrames
    .map(
      (frame) =>
        JSON.parse(frame) as {
          type?: string;
          tree?: {
            children?: Array<{
              type: string;
              props: Record<string, unknown>;
              events: Record<string, string>;
            }>;
          };
        },
    )
    .find((message) => message.type === "init");
  expect(initMessage).toBeDefined();
  const tableNode = initMessage?.tree?.children?.find(
    (child) => child.type === "DataTable",
  );
  expect(tableNode?.props.serverSide).toBe(true);
  expect(tableNode?.events.query_change).toBeDefined();

  await page.getByRole("button", { name: "increment" }).click();
  await expect(page.getByText("count: 1")).toBeVisible();
  await page.getByRole("textbox", { name: "filter rows" }).fill("rust");
  await expect(
    sentFrames.map((frame) => JSON.parse(frame) as { type?: string }),
  ).toEqual(
    expect.arrayContaining([expect.objectContaining({ type: "event" })]),
  );
  await expect
    .poll(() =>
      sentFrames.some((frame) => {
        const message = JSON.parse(frame) as {
          type?: string;
          payload?: { values?: { search?: string } };
        };
        return (
          message.type === "event" && message.payload?.values?.search === "rust"
        );
      }),
    )
    .toBe(true);

  await expect(page.getByRole("cell", { name: "Rust" })).toBeVisible();
  await expect(page.getByRole("cell", { name: "Ruby" })).toHaveCount(0);
});

test("representative component families pass axe WCAG 2.1 A/AA checks", async ({
  page,
}) => {
  await page.route("**/axe.min.js", async (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/javascript",
      body: axe.source,
    }),
  );
  await page.goto("http://127.0.0.1:8000/accessibility");
  await expect(
    page.getByRole("heading", { name: "accessibility test page" }),
  ).toBeVisible();
  await expect(page.getByRole("textbox", { name: "email address" })).toBeVisible();
  await expect(
    page.getByRole("textbox", { name: "profile biography" }),
  ).toBeVisible();
  await expect(page.getByRole("slider", { name: "volume" })).toBeVisible();
  await page.addScriptTag({ url: "/axe.min.js" });
  const violations = await page.evaluate(async () => {
    const axeApi = (
      window as Window & {
        axe?: {
          run: (
            context: Document,
            options: { runOnly: { type: "tag"; values: string[] } },
          ) => Promise<{
            violations: Array<{
              id: string;
              nodes: Array<{ target: string[]; html: string }>;
            }>;
          }>;
        };
      }
    ).axe;
    if (!axeApi) throw new Error("axe-core did not load");
    const results = await axeApi.run(document, {
      runOnly: {
        type: "tag",
        values: ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"],
      },
    });
    return results.violations.map(({ id, nodes }) => ({
      id,
      nodes: nodes.map((node) => ({
        target: node.target,
        html: node.html,
      })),
    }));
  });
  expect(violations).toEqual([]);
});
