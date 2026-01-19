import { test, expect } from "@playwright/test";
import path from "path";

const fixtureFile = path.join(process.cwd(), "tests", "fixtures", "sample.txt");

test("upload flow routes to dashboard", async ({ page }) => {
  await page.goto("/");

  const fileInput = page.locator('input[type="file"][name="file"]');
  await fileInput.setInputFiles(fixtureFile);

  await page.getByRole("button", { name: "Upload & Start" }).click();

  await expect(page).toHaveURL(/\/dashboard/);
  await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
});
