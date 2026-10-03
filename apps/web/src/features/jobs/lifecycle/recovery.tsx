"use client";

import { useEffect, useRef, useState } from "react";
import { ApiError } from "../../../lib/api-client";
import type { JobDetail } from "../../../lib/contracts";
import { jobDetail, recoverJob, retryJob } from "../../../lib/job-client";

const active = ["PREPARING", "EXECUTING", "CANCEL_REQUESTED", "FINALIZING"];
const retryable = ["FAILED", "COMPLETED_WITH_ERRORS", "CANCELED"];

export default function RecoveryPanel({
  job, owner, onChanged,
}: {
  job: JobDetail; owner: boolean; onChanged: (job: JobDetail) => void;
}) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const retryKey = useRef<string | null>(null);
  const activeRequest = useRef(0);
  useEffect(() => () => { activeRequest.current += 1; }, []);
  const expired = active.includes(job.status) && job.lease_expires_at !== null &&
    Date.parse(job.lease_expires_at) <= Date.now();
  const recovered = job.job_state_events.some(
    (event) => event.reason_code === "INTERRUPTION_RECOVERED",
  );
  if (!expired && !recovered) return null;

  function explain(value: unknown) {
    setError(value instanceof ApiError ? value.message : "暂时无法处理执行中断。");
  }
  async function recover() {
    const request = ++activeRequest.current;
    setBusy(true); setError("");
    try {
      await recoverJob(job.job_id);
      const next = await jobDetail(job.job_id);
      if (request === activeRequest.current) onChanged(next);
    } catch (value) { if (request === activeRequest.current) explain(value); }
    finally { if (request === activeRequest.current) setBusy(false); }
  }
  async function retry() {
    const request = ++activeRequest.current;
    setBusy(true); setError("");
    retryKey.current ??= crypto.randomUUID();
    try {
      const created = await retryJob(job.job_id, retryKey.current);
      const next = await jobDetail(created.job_id);
      if (request !== activeRequest.current) return;
      const url = new URL(window.location.href);
      url.searchParams.set("job", created.job_id);
      window.history.replaceState(null, "", url);
      onChanged(next);
      retryKey.current = null;
    } catch (value) { if (request === activeRequest.current) explain(value); }
    finally { if (request === activeRequest.current) setBusy(false); }
  }
  return <section aria-label="中断恢复">
    <h4>执行中断处理</h4>
    {expired && <p>执行租约已过期，系统不会自动续跑。请由所有者按已保存证据收束。</p>}
    {recovered && <p>旧批次已安全收束。已完成 Run 的结果保持不变；未完成 Run
      已记录为基础设施中断，系统没有自动续跑。</p>}
    {recovered && <ul>{job.runs.map((run, index) => <li key={run.run_id}>
      Run {index + 1}：{run.status === "COMPLETED" ? "已完成结果已保留" :
        run.failure_summary ?? "未开始，已取消"}
    </li>)}</ul>}
    {job.failure_summary && <p>安全原因：{job.failure_summary}</p>}
    {error && <p role="alert">{error}</p>}
    {owner && expired && <button disabled={busy} onClick={recover}>检查并收束中断</button>}
    {owner && recovered && retryable.includes(job.status) &&
      <button disabled={busy} onClick={retry}>新建重试批次</button>}
  </section>;
}
