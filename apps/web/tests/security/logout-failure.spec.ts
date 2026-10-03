import { expect, test } from "@playwright/test";
import { loginOwner, navigation } from "../support/workbench";

for (const failure of ["503", "network"]) {
  test(`logout ${failure} is visible and a successful retry clears private state`, async ({ page }) => {
    await loginOwner(page);
    await navigation(page).getByRole("button", { name: "评测", exact: true }).click();
    await page.route("**/api/v1/auth/logout", (route) => failure === "network"
      ? route.abort("failed") : route.fulfill({ status: 503, json: {
        error: { code: "DEPENDENCY_UNAVAILABLE" },
      } }));
    await page.getByRole("button", { name: "退出登录" }).click();
    await expect(page.getByRole("alert")).toContainText("退出未完成");
    await expect(page.getByText("已登录：owner")).toBeVisible();
    await expect(page.getByRole("button", { name: "退出登录" })).toBeEnabled();
    await expect(page).toHaveURL(/view=jobs/);
    expect((await page.request.get("/api/v1/auth/me")).status()).toBe(200);
    await page.unroute("**/api/v1/auth/logout");
    await page.getByRole("button", { name: "退出登录" }).click();
    await expect(page.getByLabel("账号", { exact: true })).toBeVisible();
    await expect(page.getByRole("alert")).toHaveCount(0);
    expect(new URL(page.url()).search).toBe("");
    expect((await page.request.get("/api/v1/auth/me")).status()).toBe(401);
  });
}
