import { expect, test } from "@playwright/test";

test("task page loads", async ({ page }) => {
  await page.goto("http://localhost:5173");
  await expect(page.getByRole("heading", { name: "Bootstrap App" })).toBeVisible();
});
