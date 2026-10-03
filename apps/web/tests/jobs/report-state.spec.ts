import { expect, test, type Page } from "@playwright/test";
import { loginOwner, openWizard, registerCatalog, reviewSelection } from "../support/workbench";

async function completedBatch(page: Page) {
  await loginOwner(page);
  await registerCatalog(page, true);
  const jobs = await openWizard(page);
  await reviewSelection(jobs, ["example__repo-1", "example__repo-2"]);
  await jobs.getByRole("button", { name: "提交并等待批准" }).click();
  await jobs.getByRole("button", { name: "批准并排队" }).click();
  await expect.poll(async () => {
    await jobs.getByRole("button", { name: "刷新当前批次" }).click();
    return jobs.getByText("执行完成", { exact: true }).count();
  }).toBe(1);
  const result = page.waitForResponse((response) => /\/reports\/jobs\//.test(response.url()));
  await jobs.getByRole("button", { name: "查看批次进度" }).click();
  const batch = await (await result).json();
  return { jobs, ids: batch.runs.map((run: { run_id: string }) => run.run_id) as string[],
    buttons: jobs.getByRole("region", { name: "批次进度" }).getByRole("button") };
}

function deferred() {
  let resolve!: () => void;
  const promise = new Promise<void>((done) => { resolve = done; });
  return { promise, resolve };
}

test("switching runs resets evidence cursor and suppresses duplicate page requests", async ({ page }) => {
  const { jobs, ids, buttons } = await completedBatch(page);
  const seen: string[] = []; const more = deferred(); const started = deferred();
  await page.route("**/api/v1/runs/*/trajectory?*", async (route) => {
    const url = new URL(route.request().url());
    const id = url.pathname.split("/").at(-2)!;
    const after = Number(url.searchParams.get("after_sequence"));
    seen.push(`${id}/${after}`);
    if (after > 0) { started.resolve(); await more.promise; }
    await route.fulfill({ json: {
      items: [{ sequence: after + 1, occurred_at: "2026-10-03T00:00:00Z", source: "agent",
        type: "tool", summary: `evidence-${id}-${after}`, payload: {} }],
      next_after_sequence: after + 1, complete: after > 0,
    } });
  });
  await buttons.first().click();
  let evidence = jobs.getByRole("region", { name: "安全证据" });
  await evidence.getByRole("button", { name: "查看安全轨迹" }).click();
  await expect(evidence).toContainText(`evidence-${ids[0]}-0`);
  await buttons.nth(1).click();
  evidence = jobs.getByRole("region", { name: "安全证据" });
  await expect(evidence).not.toContainText(`evidence-${ids[0]}`);
  await evidence.getByRole("button", { name: "查看安全轨迹" }).click();
  await expect(evidence).toContainText(`evidence-${ids[1]}-0`);
  const load = evidence.getByRole("button", { name: "加载更多轨迹" });
  await load.evaluate((button: HTMLButtonElement) => { button.click(); button.click(); });
  await started.promise; await expect(load).toBeDisabled(); more.resolve();
  await expect(evidence).toContainText(`evidence-${ids[1]}-1`);
  expect(seen).toEqual([`${ids[0]}/0`, `${ids[1]}/0`, `${ids[1]}/1`]);
  await expect(evidence.getByRole("listitem").filter({ hasText: `evidence-${ids[1]}-1` })).toHaveCount(1);
});

test("a slow first report cannot replace the most recently clicked Run", async ({ page }) => {
  const { jobs, ids, buttons } = await completedBatch(page);
  const started = deferred(), release = deferred();
  await page.route(`**/api/v1/reports/runs/${ids[0]}`, async (route) => {
    const response = await route.fetch(); started.resolve(); await release.promise;
    await route.fulfill({ response });
  });
  await buttons.first().click(); await started.promise;
  await buttons.nth(1).click();
  const report = jobs.getByRole("region", { name: "单题运行报告" });
  await expect(report).toContainText(`Run：${ids[1]}`);
  const returned = page.waitForResponse((response) => response.url().endsWith(`/reports/runs/${ids[0]}`));
  release.resolve(); await (await returned).finished();
  await page.evaluate(() => new Promise<void>((resolve) =>
    requestAnimationFrame(() => requestAnimationFrame(() => resolve()))));
  await expect(report).toContainText(`Run：${ids[1]}`);
  await expect(report).not.toContainText(`Run：${ids[0]}`);
});
