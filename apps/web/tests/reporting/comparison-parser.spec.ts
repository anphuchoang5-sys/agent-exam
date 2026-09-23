import { expect, test } from "@playwright/test";
import { ApiError } from "../../src/lib/api-client";
import { comparisons } from "../../src/lib/job-client";
import { comparison } from "../../src/lib/reporting/comparison-client";
import { parseComparison } from "../../src/lib/reporting/comparison-shape";

function response() {
  return {
    columns: [{
      job_id: "00000000-0000-4000-8000-000000000041",
      agent_configuration_id: "agent-1", agent_display_name: "方案 1",
    }],
    rows: [
      { task_instance_id: "task-1", repo: "fixture/repo", cells: [{
        outcome: "resolved", resolved: true as boolean | null,
        run_id: "run-1", failure_code: null,
        report_path: "/api/v1/reports/runs/run-1" as string | null,
      }] },
      { task_instance_id: "task-2", repo: "fixture/repo", cells: [{
        outcome: "missing", resolved: null, run_id: "run-2",
        failure_code: null, report_path: null,
      }] },
    ],
    totals: [{ resolved: 1, unresolved: 0, infrastructure_error: 0,
      incomplete: 0, missing: 1, decided: 1, total: 2 }],
  };
}

test("a missing report keeps its Run identity and stays outside decided coverage", () => {
  const matrix = parseComparison(response());
  expect(matrix.rows[1].cells[0]).toMatchObject({
    outcome: "missing", run_id: "run-2", resolved: null, report_path: null,
  });
  expect(matrix.totals[0]).toMatchObject({ decided: 1, total: 2 });
});

test("contradictory completed results and absent report links fail closed", () => {
  const unresolvedTruth = response();
  unresolvedTruth.rows[0].cells[0].resolved = null;
  expect(() => parseComparison(unresolvedTruth)).toThrow(ApiError);

  const absentReport = response();
  absentReport.rows[0].cells[0].report_path = null;
  expect(() => parseComparison(absentReport)).toThrow(ApiError);
});

test("both comparison clients apply the same response check", async () => {
  let payload: unknown = response();
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async () => Response.json(payload);
  try {
    expect((await comparisons(["job-1"])).totals[0].total).toBe(2);
    expect((await comparison(["job-1"])).totals[0].total).toBe(2);

    const contradictory = response();
    contradictory.rows[0].cells[0].resolved = null;
    payload = contradictory;
    await expect(comparisons(["job-1"])).rejects.toThrow(ApiError);
    await expect(comparison(["job-1"])).rejects.toThrow(ApiError);
  } finally {
    globalThis.fetch = originalFetch;
  }
});
