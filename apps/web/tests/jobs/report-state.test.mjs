import assert from "node:assert/strict";
import test from "node:test";
import { deferred, find, flush, nodes, probe, text } from "../support/component-probe.mjs";

const job = (id = "old") => ({ job_id: id, run_ids: ["A", "B"], status: "FAILED" });
const run = (id, jobId = "old") => ({ run: { run_id: id, job_id: jobId } });
const batch = { job_id: "old", runs: [] };
async function panel(api = {}) {
  const view = probe("src/features/jobs/submit.tsx", { owner: true, showWizard: false }, {
    "src/lib/job-client.ts": { jobDetail: async () => job(), jobReport: async () => batch, ...api },
  });
  view.render(); await flush(); view.render();
  await find(view.tree, "查看批次进度").props.onClick(); view.render();
  return view;
}
const open = (view, id) => find(view.tree, "BatchReportView").props.openRun(id);
const reports = (view) => nodes(view.tree).filter((node) =>
  ["RunReportView", "BatchReportView"].includes(node.type?.name));

test("last clicked Run wins even when the first response arrives last", async () => {
  const a = deferred(), b = deferred();
  const view = await panel({ runReport: (id) => id === "A" ? a.promise : b.promise });
  open(view, "A"); open(view, "B");
  b.resolve(run("B")); await flush(); view.render();
  a.resolve(run("A")); await flush(); view.render();
  assert.equal(find(view.tree, "RunReportView").props.report.run.run_id, "B");
});

test("stale Run error cannot overwrite the latest report or clear busy", async () => {
  const a = deferred(), b = deferred();
  const view = await panel({ runReport: (id) => id === "A" ? a.promise : b.promise });
  open(view, "A"); open(view, "B");
  a.reject(new Error("old failure")); await flush(); view.render();
  assert.equal(find(view.tree, "刷新当前批次").props.disabled, true);
  assert.equal(nodes(view.tree).filter((node) => node.props?.role === "alert").length, 0);
  b.resolve(run("B")); await flush(); view.render();
  assert.equal(find(view.tree, "RunReportView").props.report.run.run_id, "B");
});

test("retry Job clears both reports and rejects old in-flight Run results", async () => {
  const late = deferred(); let calls = 0;
  const view = await panel({ runReport: async () => ++calls === 1 ? run("A") : late.promise });
  open(view, "A"); await flush(); view.render();
  assert.equal(reports(view).length, 2);
  open(view, "B");
  find(view.tree, "RecoveryPanel").props.onChanged(job("new")); view.render();
  assert.equal(find(view.tree, "JobDetails").props.job.job_id, "new");
  assert.equal(reports(view).length, 0);
  late.resolve(run("B")); await flush(); view.render();
  assert.equal(reports(view).length, 0);
});

test("retry Job invalidates an old batch refresh and its Job detail", async () => {
  const pending = deferred(); let count = 0;
  const view = await panel({ jobReport: () => ++count === 1 ? Promise.resolve(batch) : pending.promise });
  const refresh = find(view.tree, "刷新当前批次").props.onClick(); await flush();
  find(view.tree, "RecoveryPanel").props.onChanged(job("new")); view.render();
  pending.resolve(batch); await refresh; view.render();
  assert.equal(find(view.tree, "JobDetails").props.job.job_id, "new");
  assert.equal(reports(view).length, 0);
});

test("Run response identity must match requested Job and Run", async () => {
  const view = await panel({ runReport: async () => run("B", "other") });
  open(view, "A"); await flush(); view.render();
  assert.equal(reports(view).length, 1);
  assert.equal(nodes(view.tree).some((node) => node.props?.role === "alert"), true);
});

function page(label, next = 1, complete = false) {
  return { items: [{ sequence: next, summary: label }], next_after_sequence: next, complete };
}
const artifacts = [{ artifact_type: "public_trajectory", warnings: [], artifact_id: "safe" }];

test("report keys evidence by Run and a new trajectory starts at cursor zero", async () => {
  const report = (id) => ({ ...run(id), process_metrics: { usage: {}, resources: {} },
    run: { ...run(id).run, warnings: [] }, artifact_links: artifacts });
  const view = probe("src/features/jobs/report.tsx", { report: report("A") });
  const a = find(view.render(), "EvidenceView");
  const b = find(view.render({ report: report("B") }), "EvidenceView");
  assert.notEqual(a.key, b.key);
  const calls = [];
  const evidence = probe("src/features/jobs/evidence.tsx", b.props, {
    "src/lib/job-client.ts": { runTrajectory: async (...args) => { calls.push(args); return page("B evidence"); } },
  });
  evidence.render(); find(evidence.tree, "查看安全轨迹").props.onClick(); await flush(); evidence.render();
  assert.deepEqual(calls, [["B", 0]]);
  assert.match(text(evidence.tree), /B evidence/);
  assert.doesNotMatch(text(evidence.tree), /A evidence/);
});

test("trajectory rejects reentry before rerender and ignores unmounted responses", async () => {
  const late = deferred(); const calls = [];
  const view = probe("src/features/jobs/evidence.tsx", { runId: "A", artifacts }, {
    "src/lib/job-client.ts": { runTrajectory: (...args) => { calls.push(args); return late.promise; } },
  });
  view.render(); const click = find(view.tree, "查看安全轨迹").props.onClick;
  click(); click(); view.render();
  assert.equal(calls.length, 1);
  assert.equal(find(view.tree, "查看安全轨迹").props.disabled, true);
  view.unmount(); late.resolve(page("stale")); await flush(); view.render();
  assert.doesNotMatch(text(view.tree), /stale/);
});

test("trajectory pagination appends each page once", async () => {
  const late = deferred(); const calls = [];
  const view = probe("src/features/jobs/evidence.tsx", { runId: "A", artifacts }, {
    "src/lib/job-client.ts": { runTrajectory: async (...args) => {
      calls.push(args); return args[1] === 0 ? page("first") : late.promise;
    } },
  });
  view.render(); find(view.tree, "查看安全轨迹").props.onClick(); await flush(); view.render();
  const click = find(view.tree, "加载更多轨迹").props.onClick; click(); click();
  late.resolve(page("second", 2, true)); await flush(); view.render();
  assert.deepEqual(calls, [["A", 0], ["A", 1]]);
  assert.equal(nodes(view.tree).filter((node) => node.type === "li").length, 3);
  assert.match(text(view.tree), /first.*second/);
});

for (const outcome of ["unmount", "detail-failure"]) {
  test(`retry ${outcome} cannot redirect URL or replace the active Job`, async () => {
    const detail = deferred(); const changes = [];
    const view = probe("src/features/jobs/lifecycle/recovery.tsx", {
      job: { ...job(), runs: [], job_state_events: [{ reason_code: "INTERRUPTION_RECOVERED" }] },
      owner: true, onChanged: (value) => changes.push(value),
    }, { "src/lib/job-client.ts": {
      retryJob: async () => ({ job_id: "new" }), jobDetail: () => detail.promise,
    } });
    view.render(); const retry = find(view.tree, "新建重试批次").props.onClick(); await flush();
    if (outcome === "unmount") { view.unmount(); detail.resolve(job("new")); }
    else detail.reject(new Error("offline"));
    await retry;
    assert.match(view.window.location.href, /job=old/);
    assert.deepEqual(changes, []);
  });
}

test("trajectory failure releases the request lock for a successful retry", async () => {
  let calls = 0;
  const view = probe("src/features/jobs/evidence.tsx", { runId: "A", artifacts }, {
    "src/lib/job-client.ts": { runTrajectory: async () => {
      if (++calls === 1) throw new Error("offline");
      return page("recovered", 1, true);
    } },
  });
  view.render(); find(view.tree, "查看安全轨迹").props.onClick(); await flush(); view.render();
  assert.notEqual(find(view.tree, "查看安全轨迹").props.disabled, true);
  assert.equal(nodes(view.tree).some((node) => node.props?.role === "alert"), true);
  find(view.tree, "查看安全轨迹").props.onClick(); await flush(); view.render();
  assert.match(text(view.tree), /recovered/);
  assert.equal(nodes(view.tree).some((node) => node.props?.role === "alert"), false);
});
