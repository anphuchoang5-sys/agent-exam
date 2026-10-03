import assert from "node:assert/strict";
import test from "node:test";
import { deferred, find, flush, nodes, probe } from "../support/component-probe.mjs";

const page = { items: Array.from({ length: 20 }, (_, i) => ({ job_id: `job-${i}` })), next_cursor: "more" };
async function workspace(ids, detail) {
  const toggled = [];
  const view = probe("src/features/jobs/reporting/comparison.tsx", {
    ids, toggle: (id) => toggled.push(id), clearAll() {}, openJob() {},
  }, { "src/lib/job-client.ts": { jobs: async () => page, jobDetail: detail } });
  view.render(); await flush(); view.render();
  return { view, toggled, ApiError: view.getModule("src/lib/api-client.ts").ApiError };
}
const refresh = (view) => find(view.tree, "刷新可见批次").props.onClick();

test("refresh preserves a selected Job outside the first 20-item page", async () => {
  const checked = [];
  const { view, toggled } = await workspace(["job-20"], async (id) => { checked.push(id); return {}; });
  refresh(view); await flush(); view.render();
  assert.deepEqual(checked, ["job-20"]);
  assert.deepEqual(toggled, []);
});

test("only explicit JOB_NOT_FOUND removes a missing selected Job", async () => {
  let ApiError;
  const state = await workspace(["denied", "offline", "allowed"], async (id) => {
    if (id === "denied") throw new ApiError("JOB_NOT_FOUND");
    if (id === "offline") throw new ApiError("DEPENDENCY_UNAVAILABLE");
    return {};
  });
  ApiError = state.ApiError;
  refresh(state.view); await flush(); state.view.render();
  assert.deepEqual(state.toggled, ["denied"]);
  assert.equal(nodes(state.view.tree).some((node) => node.props?.role === "alert"), true);
});

for (const code of ["DEPENDENCY_UNAVAILABLE", "FORBIDDEN", "AUTHENTICATION_REQUIRED", "UNAVAILABLE"]) {
  test(`${code} never masquerades as proof of revoked Job access`, async () => {
    let ApiError;
    const state = await workspace(["job-20"], async () => { throw new ApiError(code); });
    ApiError = state.ApiError;
    refresh(state.view); await flush(); state.view.render();
    assert.deepEqual(state.toggled, []);
    assert.equal(nodes(state.view.tree).some((node) => node.props?.role === "alert"), true);
  });
}

for (const action of ["unmount", "clear"]) {
  test(`late denial after ${action} cannot toggle the parent's selection`, async () => {
    const pending = deferred();
    void pending.promise.catch(() => {}); // Baseline code does not request this detail.
    const { view, toggled, ApiError } = await workspace(["job-20"], () => pending.promise);
    refresh(view); await flush();
    if (action === "unmount") view.unmount();
    else find(view.tree, "清空选择").props.onClick();
    pending.reject(new ApiError("JOB_NOT_FOUND")); await flush();
    assert.deepEqual(toggled, []);
  });
}
