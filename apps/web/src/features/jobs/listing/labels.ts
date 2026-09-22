import type { JobStatus } from "../../../lib/contracts";

// 批次 id 是 36 位 UUID，整串出现在列表与工作台的行里既长又难扫视。
// 这两处只呈现前 8 位短码；完整值由行本身的 title 承载（悬停可见），
// 需要逐字对账时还可以看详情页 URL 的 job 参数，或直接查 API。
export function shortJobId(jobId: string): string {
  return `${jobId.slice(0, 8)}…`;
}

export const JOB_STATUS_NAMES: Record<JobStatus, string> = {
  AWAITING_OWNER_APPROVAL: "等待所有者批准",
  QUEUED: "等待执行",
  PREPARING: "准备中",
  EXECUTING: "执行中",
  FINALIZING: "收束中",
  COMPLETED: "已完成",
  COMPLETED_WITH_ERRORS: "部分出错",
  FAILED: "失败",
  REJECTED: "已拒绝",
  CANCEL_REQUESTED: "取消请求中",
  CANCELED: "已取消",
};
