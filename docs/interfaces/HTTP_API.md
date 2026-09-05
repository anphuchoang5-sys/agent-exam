# Web 与后端 HTTP API 契约

> 文档状态：Job/Run 资源边界已确认；HTTP 契约 v0.3，尚未实现
>
> 最后更新：2026-09-05
> 权威范围：本文件只维护 Next.js Web 与 FastAPI 交付层之间的 HTTP 契约。内部模块行为见 [`MODULE_CONTRACTS.md`](../architecture/MODULE_CONTRACTS.md)，存储字段见 [`DATA_MODEL.md`](../architecture/DATA_MODEL.md)。

## 1. 给初学者的解释

浏览器不能直接碰 Docker、数据库和 Agent。它只能给 FastAPI 发 HTTP 请求。HTTP API 就像一张固定菜单：页面只能点菜单上已有的菜，不能把一条任意 shell 命令交给服务器执行。

## 2. 总体规则

| 项目 | 候选 v0.1 |
|---|---|
| 基础路径 | `/api/v1` |
| 内容类型 | JSON 接口使用 `application/json; charset=utf-8` |
| ID | 对外均为不透明字符串；前端不得从 ID 猜数据库结构 |
| 时间 | ISO 8601 UTC，例如 `2026-09-01T10:00:00Z` |
| 分页 | `limit` + 不透明 `cursor`；默认 20，候选上限 100 |
| 创建幂等 | 写请求支持 `Idempotency-Key`；相同键和相同请求不得创建两条记录 |
| 长任务 | `POST /jobs` 只创建待所有者批准的 Job 和逐题运行后立即返回 `202`；批准请求只排队，也不等待 Harbor/Agent 完成 |
| 状态刷新 | 首版候选用前端轮询；不先引入 WebSocket/SSE |
| 字段命名 | JSON 使用 `snake_case`，与后端 schema 保持一致 |
| 未知字段 | 写请求默认拒绝，防止拼写错误被静默忽略 |
| OpenAPI | FastAPI 生成的 schema 上线时必须与本文契约检查一致 |

## 3. 统一错误格式

```json
{
  "error": {
    "code": "RUN_STATE_CONFLICT",
    "message": "当前运行状态不允许执行此操作",
    "details": {
      "run_id": "01J...",
      "current_status": "VERIFYING"
    },
    "request_id": "req_01J..."
  }
}
```

| HTTP 状态 | 使用场景 | 示例 `error.code` |
|---:|---|---|
| `400` | 请求语义无效 | `INVALID_REQUEST`、`LIMIT_OUT_OF_RANGE` |
| `401` | 没有可信登录会话 | `AUTHENTICATION_REQUIRED` |
| `403` | 已登录但没有操作权限 | `OWNER_APPROVAL_REQUIRED`、`FORBIDDEN` |
| `404` | 资源不存在 | `TASK_NOT_FOUND`、`JOB_NOT_FOUND`、`RUN_NOT_FOUND` |
| `409` | 状态或幂等冲突 | `JOB_STATE_CONFLICT`、`RUN_STATE_CONFLICT`、`IDEMPOTENCY_CONFLICT` |
| `410` | 制品正文已按保留策略清理 | `ARTIFACT_CONTENT_DELETED` |
| `422` | JSON 字段/schema 不合格 | `VALIDATION_ERROR` |
| `503` | 数据库、对象存储等暂不可用 | `DEPENDENCY_UNAVAILABLE` |
| `500` | 未预期平台错误 | `INTERNAL_ERROR` |

错误 `message` 面向人类；前端分支判断只使用稳定的 `code`，不能解析中文文案。

### 3.1 身份与角色边界

平台没有公开注册，只存在两类应用角色：

| 角色 | 允许行为 | 明确禁止 |
|---|---|---|
| `collaborator`（协作者） | 登录、查看任务/已登记 Agent、提交 Job、查看自己有权访问的非秘密结果、取消自己提交的 Job | 批准/拒绝、成员和配置管理、清理制品、人工复核 |
| `owner`（评测所有者） | 协作者全部能力，以及批准/拒绝任意 Job、邀请协作者、成员/配置管理、清理制品和人工复核 | 把所有者权限委托给请求正文或网络设备身份 |

唯一 `owner` 由评测机本地引导建立和恢复，之后由其邀请协作者；不接入邮件服务。每个请求先由登录中间件生成可信 `AuthenticatedActor`，route 不能接受 `role`、`owner_id`、`reviewer_id` 等正文提权字段。Tailscale/校园网/VPN只解决“能否到达页面”，不能代替应用登录。账户、密码哈希、邀请和会话的具体端点与存储要先核实现有实现；本文不凭空新增第三类角色或用户表。

## 4. 只读资源形状

### 4.1 `TaskSummary`

```json
{
  "task_id": "SWE-Gym/SWE-Gym@revision:train:instance-id",
  "instance_id": "instance-id",
  "dataset_id": "SWE-Gym/SWE-Gym",
  "dataset_revision": "fixed-revision",
  "split": "train",
  "repo": "owner/repo",
  "base_commit": "commit",
  "problem_statement_preview": "Issue 的截断预览"
}
```

不返回 gold patch、`test_patch`、`FAIL_TO_PASS` 或 `PASS_TO_PASS`。

### 4.2 `AgentConfigurationSummary`

```json
{
  "agent_configuration_id": "codex-model-config",
  "display_name": "Codex / fixed-model / fixed-config",
  "agent_type": "codex",
  "agent_version": "fixed-version",
  "model_provider": "openai_chatgpt",
  "model": "fixed-model",
  "configuration_fingerprint": "sha256-hex",
  "enabled": true
}
```

不返回 API key、凭据配置引用、命令模板、宿主路径或私有环境变量。MVP 先登记 Codex；闭环通过后登记 Aider、Claude Code。P2 同一自研 Agent 使用 DeepSeek 与 Kimi 时返回两个独立配置。

### 4.3 `JobSummary`

```json
{
  "job_id": "job_01J...",
  "evaluation_track": "closed_book",
  "result_scope": "official",
  "status": "EXECUTING",
  "owner_decision": "approved",
  "owner_decided_at": "2026-09-03T10:00:02Z",
  "trial_count": 15,
  "completed_count": 4,
  "failed_count": 0,
  "estimated_finish_at": null,
  "created_at": "2026-09-03T10:00:00Z",
  "started_at": "2026-09-03T10:00:03Z",
  "finished_at": null
}
```

`estimated_finish_at=null` 表示没有足够真实历史数据，不能理解成“马上完成”。`owner_decision` 是由 Job 状态/决定事件生成的安全视图，不在数据库另建一套可能冲突的状态；待批准时为 `pending`，批准后为 `approved`，拒绝后为 `rejected`。

### 4.4 `RunSummary`

```json
{
  "run_id": "01J...",
  "job_id": "job_01J...",
  "task_id": "opaque-task-id",
  "agent_configuration_id": "codex-model-config",
  "evaluation_track": "closed_book",
  "network_policy_id": "provider-only-v1",
  "tool_profile_id": "no-web-tools-v1",
  "status": "RUNNING_AGENT",
  "resolved": null,
  "termination_reason": null,
  "review_status": "NOT_REQUIRED",
  "created_at": "2026-09-01T10:00:00Z",
  "started_at": "2026-09-01T10:00:03Z",
  "finished_at": null
}
```

`resolved=null` 表示确定性验证尚未产生结果；不能解释为失败。超过 1 MiB 的文本 patch 或任何二进制 patch 不进入 Harness，分别以 `PATCH_TOO_LARGE` / `BINARY_PATCH_NOT_ALLOWED` 记录为明确的无效 Agent 输出；patch 不会被静默截断。

## 5. Task API

### 5.1 查询任务列表

`GET /api/v1/tasks`

| 输入 | 类型 | 说明 |
|---|---|---|
| `dataset_id` | query string，可选 | 只接受已登记数据集 |
| `split` | query string，可选 | 真实可用 split 由 Task Catalog 返回 |
| `repo` | query string，可选 | 精确筛选仓库 |
| `cursor` | query string，可选 | 下一页游标 |
| `limit` | query integer，可选 | 1–100 |

成功 `200`：

```json
{
  "items": [],
  "next_cursor": null
}
```

### 5.2 查询任务详情

`GET /api/v1/tasks/{task_id}`

- 输入：不透明 `task_id`。
- 成功 `200`：`TaskSummary` 加完整 `problem_statement`。
- 错误：`404 TASK_NOT_FOUND`。
- 保密：仍不返回 gold patch 和判分测试答案。

## 6. Agent Configuration API

### 6.1 查询已登记配置

`GET /api/v1/agent-configurations`

| 输入 | 类型 | 说明 |
|---|---|---|
| `agent_type` | query，可选 | MVP 为 `codex`；后续加入 `aider`、`claude_code`；P2 才启用 `custom`。`custom_process` 是 Adapter 类型，不是 Agent 类型 |
| `enabled` | query boolean，可选 | 页面发起评测默认只查 `true` |
| `cursor` / `limit` | query，可选 | 通用分页 |

成功 `200`：分页的 `AgentConfigurationSummary[]`。

### 6.2 查询配置详情

`GET /api/v1/agent-configurations/{agent_configuration_id}`

- 成功 `200`：公开配置、版本、模型、限制模板和指纹。
- 错误：`404 AGENT_CONFIGURATION_NOT_FOUND`。
- MVP 不提供上传压缩包、源码仓库、shell 命令或未审核代码运行接口。

登记/修改 Agent 配置属于 `owner` 流程；协作者只能选择项目已经登记并启用的配置。

### 6.3 P2：提交 Agent 源码供审核（MVP 不开放）

以下契约只保留扩展接缝，不注册为 MVP 路由；浏览器和 OpenAPI 都不应在 MVP 中出现这些入口。

`POST /api/v1/agent-submissions`

P2 请求需要可信登录会话。请求：

```json
{
  "git_url": "https://example.com/group/agent.git",
  "commit_sha": "40-character-full-commit-sha",
  "display_name": "My Agent",
  "description": "供组内评测的固定版本"
}
```

仓库根必须存在同一 commit 中的 `agent-exam.yaml`。成功 `202`：

```json
{
  "submission_id": "submission_01J...",
  "status": "PENDING_REVIEW",
  "created_at": "2026-09-03T10:00:00Z"
}
```

提交成功不会启动 Harbor、构建镜像或执行仓库代码。分支、tag、`latest`、请求内 `import_path`、环境变量或 shell 命令均拒绝。

评测所有者审核候选接口：

- `GET /api/v1/agent-submissions`：提交者看自己的记录，所有者看待审列表；
- `GET /api/v1/agent-submissions/{submission_id}`：查看安全元数据和审核状态；
- `POST /api/v1/agent-submissions/{submission_id}/approve`：所有者批准并生成新的已登记 Agent 配置；
- `POST /api/v1/agent-submissions/{submission_id}/reject`：所有者拒绝并记录原因。

P2 自研 Agent 只支持 Python 固定进程 Interface；`agent-exam.yaml` 不得接收 shell、API Key、自定义模型提供方/Base URL、代理或宿主路径。完整字段、Python 版本和依赖锁格式尚未验证，因此不能在 schema 未确定时实现猜测式解析。审核通过后，所有者只能从平台登记的 DeepSeek/Kimi 模型配置中生成自研 `AgentConfiguration`；提交者不填写凭据。这一节不阻塞 Codex MVP。

## 7. Job API

### 7.1 创建评测 Job

`POST /api/v1/jobs`

Header：`Idempotency-Key: <客户端生成的不透明值>`。

请求：

```json
{
  "task_ids": ["task-1", "task-2", "task-3"],
  "agent_configuration_ids": ["codex-config", "aider-config"],
  "evaluation_track": "closed_book",
  "batch_preset": "demo",
  "limit_profile_id": "default-single-host-v1"
}
```

成功 `202`：

```json
{
  "job_id": "job_01J...",
  "status": "AWAITING_OWNER_APPROVAL",
  "evaluation_track": "closed_book",
  "trial_count": 6,
  "run_ids": ["run_01J1...", "run_01J2...", "run_01J3...", "run_01J4...", "run_01J5...", "run_01J6..."],
  "estimated_finish_at": null,
  "created_at": "2026-09-05T10:00:00Z"
}
```

错误：

- `404 TASK_NOT_FOUND`；
- `404 AGENT_CONFIGURATION_NOT_FOUND`；
- `409 AGENT_CONFIGURATION_DISABLED`；
- `409 IDEMPOTENCY_CONFLICT`；
- `400 EMPTY_JOB_SELECTION`；
- `400 BATCH_PRESET_EXCEEDED`；
- `400 LIMIT_PROFILE_NOT_ALLOWED`；
- `400 EVALUATION_TRACK_NOT_ENABLED`。

任务和 Agent 列表必须非空、去重，并且所有 Agent 已登记启用。MVP 只接受 `closed_book`；`open_book_experimental` 仅保留 schema 接缝，请求时返回 `400 EVALUATION_TRACK_NOT_ENABLED`。每个组合只尝试一次，所以 `trial_count = task 数 × Agent 数`。预设规模：`demo` 为 1–3 题、`quick` 为 5 题、`standard` 为 10–20 题；Agent 选择上限约 3 个，精确校验值实现前再锁定为配置。

创建事务会冻结配置并生成 `PENDING` runs，但初始 Job 必须是 `AWAITING_OWNER_APPROVAL`。这一步既不创建 Harbor Job，也不唤起 Codex。协作者能通过远程入口到达页面，不代表拥有批准权限；网络准入与应用授权是两层不同控制，远程拓扑见 [`REMOTE_TEAM_ACCESS.md`](../operations/REMOTE_TEAM_ACCESS.md)。

前端不能提交任意 CPU/内存/网络值、Harbor 并发数、代理地址、工具命令或启动命令。后端固定单机 `n_concurrent_trials=1`，根据赛道与登记配置冻结网络策略和工具配置。

### 7.2 查询 Job 列表

`GET /api/v1/jobs`

筛选：`status`、`created_by`、`evaluation_track`、`result_scope`、`cursor`、`limit`。成功 `200` 返回分页 `JobSummary[]`。

### 7.3 查询 Job 详情

`GET /api/v1/jobs/{job_id}`

成功 `200` 至少返回：

- `JobSummary`；
- 冻结的任务 ID 和 Agent 配置 ID 列表；
- Job limits；
- 评测赛道、网络策略和工具配置的安全快照；
- 所有者决定状态和时间；只有有权查看审计信息的角色才返回决定者身份；
- 当前阶段、最近一次 Job 状态说明和 Harbor 后端安全摘要；
- 分页的 `RunSummary` 或运行列表链接；
- 完成、失败、待运行、已解决等聚合计数。

错误：`404 JOB_NOT_FOUND`。

### 7.4 评测机所有者批准 Job

`POST /api/v1/jobs/{job_id}/approve`

Header：`Idempotency-Key: <客户端生成的不透明值>`。请求：

```json
{"reason":"已检查任务、Agent、赛道和运行数量"}
```

- 只接受可信登录会话中的评测机所有者；`owner_id` 不得放在请求正文中。
- 只有 `AWAITING_OWNER_APPROVAL` 可批准。成功 `200` 在一个短事务中写入 `QUEUED`、决定者、决定时间和状态事件，然后立即返回更新后的 `JobSummary`。
- 批准只开放排队资格，不读取 `auth.json`、不启动 Docker/Harbor，也不等待 Worker。评测机本地 Worker 下一次轮询时才可能领取。
- 非所有者返回 `403 OWNER_APPROVAL_REQUIRED`；Job 已被批准、拒绝或取消返回 `409 JOB_STATE_CONFLICT`；相同幂等键和相同决定返回同一结果。

### 7.5 评测机所有者拒绝 Job

`POST /api/v1/jobs/{job_id}/reject`

Header：`Idempotency-Key: <客户端生成的不透明值>`。请求：

```json
{"reason":"当前不批准本次真实资源消耗"}
```

- 只接受可信登录会话中的评测机所有者；只有 `AWAITING_OWNER_APPROVAL` 可拒绝。
- 成功 `200` 在同一事务中把 Job 写为 `REJECTED`、把其 `PENDING` runs 写为 `CANCELED`，并保存决定者、时间和状态事件。
- `REJECTED` 是授权决定，不是 Agent 失败或平台故障，不能进入 Worker 队列，也不能产生正式运行证据。
- 权限、状态冲突和幂等规则与批准接口相同。

### 7.6 取消 Job

`POST /api/v1/jobs/{job_id}/cancel`

请求：

```json
{"reason":"用户请求取消"}
```

- 成功 `202`：返回更新后的 `JobSummary`。
- 协作者只能取消自己提交的 Job；`owner` 可取消任意 Job。权限来自可信会话，不接受正文中的用户或角色字段。
- `AWAITING_OWNER_APPROVAL`、`QUEUED` 以及尚未启动 Trial 的 `PREPARING` 可直接变为 `CANCELED`。
- `EXECUTING` 时成功响应把 Job 置为 `CANCEL_REQUESTED`：不再启动后续 Trial，当前 Trial 不强杀，只运行到创建 Job 时冻结的超时上限并保存真实证据；随后剩余 `PENDING` runs 变为 `CANCELED`，Job 经 `FINALIZING` 收束为 `CANCELED`。
- Worker、宿主机或 Harbor 中断时不自动续跑或重试；若所有者决定重试，必须创建有 `rerun_of_job_id` 的新 Job 和新证据链。
- 已完成、已失败或已取消时返回 `409 JOB_STATE_CONFLICT`。

## 8. Run API（逐题只读）

`GET /api/v1/runs`

筛选：`job_id`、`status`、`task_id`、`agent_configuration_id`、`resolved`、`review_status`、`cursor`、`limit`。成功 `200` 返回分页 `RunSummary[]`。

`GET /api/v1/runs/{run_id}`

成功 `200` 至少返回：`RunSummary`、冻结任务/Agent 快照、后端 Job/Trial 安全引用、限制、确定性结果、版本化 Judge 分析列表、人工复核和制品链接。错误：`404 RUN_NOT_FOUND`。

普通用户不能直接 `POST /runs`。运行只能由创建 Job 的同一事务按任务×Agent 组合生成，避免绕过规模、赛道和并发规则。

## 9. Trajectory 与 Artifact API

### 9.1 分页读取规范化轨迹

`GET /api/v1/runs/{run_id}/trajectory`

输入：`after_sequence`（可选，默认 0）、`limit`（1–500）、`type`（可选）。

成功 `200`：

```json
{
  "items": [
    {
      "sequence": 1,
      "occurred_at": "2026-09-01T10:00:01Z",
      "source": "codex",
      "type": "tool_call",
      "summary": "执行仓库搜索",
      "payload": {}
    }
  ],
  "next_after_sequence": 1,
  "complete": false
}
```

页面展示的是已脱敏规范化事件，不直接返回思维链或未经审查的原始日志。

### 9.2 查询制品索引

`GET /api/v1/runs/{run_id}/artifacts`

输入：可选 `artifact_type`、`cursor`、`limit`。成功 `200` 返回：`artifact_id`、类型、文件名、内容类型、大小、SHA-256、创建时间、`retention_class`、`expires_at`、`truncated`、`original_size_bytes` 和可空 `deleted_at`；不返回 MinIO secret。

### 9.3 下载制品

`GET /api/v1/artifacts/{artifact_id}/content`

- 成功 `200`：由后端流式返回内容，并设置正确 `Content-Type`/`Content-Disposition`。
- 错误：`404 ARTIFACT_NOT_FOUND`、`409 ARTIFACT_NOT_READY`；对象正文已由所有者按保留策略清理时返回 `410 ARTIFACT_CONTENT_DELETED`，并在详情中保留哈希、大小、创建/删除时间和原因。
- 候选 v0.1 不把 MinIO 管理凭据交给浏览器；未来若改为短时预签名 URL，需要单独记录安全决定。
- HTTP API 不提供制品删除入口；MVP 仅允许 `owner` 在评测机执行本机维护命令清理到期原始制品。

## 10. Report 与 Leaderboard API

### 10.1 Job 报告

`GET /api/v1/reports/jobs/{job_id}`

成功 `200` 返回 Job 总进度、任务×Agent 结果矩阵、完成/失败/未解决计数和逐题报告链接。矩阵中的每个格子只引用对应 `run_id`，不把部分失败隐藏成零分。

### 10.2 单次运行报告

`GET /api/v1/reports/runs/{run_id}`

成功 `200` 分层返回：

```json
{
  "run": {},
  "deterministic_result": {},
  "process_metrics": {},
  "judge_analyses": [],
  "human_review": null,
  "artifact_links": []
}
```

`judge_analyses` 中每项显式区分 `failure_diagnosis` 与 `quality_tiebreak`，并返回状态、模型/Prompt/输入策略版本和证据引用。规则：`deterministic_result`、`process_metrics`、`judge_analyses`、`human_review` 不合并为一个模糊的“总评价”；确定性结果是第一排序事实，Quality 只作为严格并列次序，Failure 不参与排名。

### 10.3 排行榜

`GET /api/v1/leaderboard`

输入：必需的 `evaluation_track`，以及 `dataset_id`、`dataset_revision`、`split`、可选 `repo`、`tool_profile_id`、`cursor`、`limit`。查询固定排除 `result_scope=internal_test`。

每行至少包含：

- `agent_configuration_id` 和公开配置快照；
- `evaluation_track`、`network_policy_id`、`tool_profile_id`；
- 已完成任务数；
- `resolved_count` 和 `resolved_rate`；
- 基础设施错误数，不能算成普通未解决而隐藏；
- 可空 `quality_tiebreak`：只在严格可比且逐题 `resolved` 向量完全相同的并列组中返回；包含匿名比较映射的安全摘要、四项 rubric、A/B 与 B/A 两次结论、胜/平/负和循环赛积分、版本与状态；不适用或 Judge 不可用时为 `null` 并保持并列；
- 过程指标摘要，仅展示，不参与排序；缺失值返回 `null`/`unknown`，不得当成 0；
- 数据集 revision 和统计生成时间。

同一 Agent 使用不同模型提供方、模型或关键配置时必须分行。

Quality Judge 的触发由后端判定，浏览器不能通过 query 强迫运行。严格可比要求数据集/版本、题目集合、赛道、Harness、尝试数和限制一致；候选 Agent 的逐题 `resolved` 向量完全相同，并且至少存在一道共同通过且有有效 patch 的题。仅总通过率相同但失败题不同，不触发 Quality Judge。输入只包含共同通过题上经过裁剪、脱敏、去重和限量的任务需求、最终 patch、确定性测试摘要与必要轨迹摘要；不把候选身份或顺序映射交给 Judge。

每对候选按“任务匹配与最小修改、可读性与可维护性、稳健性、副作用风险”四项 rubric 比较，并以 A/B 和 B/A 反序各运行一次；两次都指向同一候选才产生胜者，否则该对并列。三个及以上候选采用循环赛，胜 1 分、平 0.5 分、负 0 分。证据清洗失败、模型超时或输出无效时不产生并列次序。

MVP 排行榜只接受 `evaluation_track=closed_book`。数据模型保留 `open_book_experimental`，但创建和查询均返回未启用；未来启用时只允许平台统一 Web 工具并与闭卷严格分榜，不使用各 Agent 各自的原生搜索工具。

## 11. Human Review API

### 11.1 查询待复核队列

`GET /api/v1/reviews`

输入：`status`、`review_kind=failure|quality`、`cursor`、`limit`。成功 `200` 返回待复核运行或 Job 级质量比较摘要和证据链接。

### 11.2 提交或修订人工复核

`PUT /api/v1/reviews/{run_id}`

Header：`Idempotency-Key`。

请求：

```json
{
  "judge_assessment": "CONFIRMED",
  "corrected_failure_category": null,
  "notes": "确定性测试和轨迹证据一致",
  "expected_version": 1
}
```

成功 `200` 返回版本化 `HumanReviewRecord`。错误包括：

- `404 RUN_NOT_FOUND`；
- `409 REVIEW_NOT_PENDING`；
- `409 REVIEW_VERSION_CONFLICT`；
- `422 VALIDATION_ERROR`。

上例只覆盖 `failure_diagnosis` 的复核。只有 `owner` 可以人工复核；`reviewer_id` 来自可信会话。

Quality Judge 使用 Job 级接口 `PUT /api/v1/reviews/jobs/{job_id}/quality/{comparison_key}`，请求只允许 `judge_assessment=CONFIRMED|INVALIDATED`、`notes` 和 `expected_version`。`CONFIRMED` 保留自动结论；`INVALIDATED` 把该比较恢复为并列并保留原始 Judge 证据。所有者不能手工指定胜者、修改循环赛分数或把 Failure 字段复用于质量比较。

账户与会话的精确实现尚待核实现有代码；在登录和两类角色授权完成前，这些接口只能在本机受控演示环境使用。

## 12. HTTP interface 到内部模块的映射

| HTTP 资源 | 只允许调用的应用模块 |
|---|---|
| `/tasks` | Task Catalog 查询 |
| `/agent-configurations` | Agent Registry 查询 |
| `/agent-submissions` | P2 Agent Source Review；MVP 不注册路由，P2 批准/拒绝只允许所有者 |
| `POST /jobs` | Job Submission |
| `GET /jobs*` | Reporting / Job Repository 只读查询 |
| `POST /jobs/{id}/approve`、`POST /jobs/{id}/reject` | Owner Approval；只允许评测机所有者 |
| `POST /jobs/{id}/cancel` | Job lifecycle 用例 |
| `GET /runs*` | Reporting / Run Repository 只读查询；不存在普通用户创建接口 |
| `/trajectory`、`/artifacts` | Reporting + Artifact Store 只读读取 |
| `/reports`、`/leaderboard` | Reporting |
| `/reviews` | Human Review；只允许所有者 |

FastAPI route 文件只做 schema、HTTP 状态和用例调用，不能直接启动 Docker 或调用 SWE-Bench-Fork。

## 13. 接口验证

实现后至少执行：

1. OpenAPI schema 快照检查；本文示例与 schema 的字段/状态码对照。
2. Next.js 使用由 OpenAPI 生成或同步的 TypeScript 类型，避免手写两套字段。
3. 每个端点覆盖成功、资源不存在、schema 错误和状态冲突。
4. 确认 Task/Agent 接口不泄漏 gold patch、隐藏测试、任务原始快照中的评测专用字段、启动命令和秘密；MVP 的 OpenAPI 不出现 `/agent-submissions`，只能选择项目已登记 Agent。
5. 创建 Job 响应不等待 Worker；任务×Agent 生成正确 `trial_count` 和 `run_id`，初始状态只能是 `AWAITING_OWNER_APPROVAL`。
6. 排行榜按完整 Agent 配置分组并单列基础设施错误；`internal_test` 永远被排除。
7. 原始制品下载不暴露 MinIO 管理凭据，轨迹默认已脱敏。
8. 创建 Job 冻结赛道/网络/工具/Harbor/Fork 版本；MVP 只允许 `closed_book`，`open_book_experimental` 创建和查询均明确返回未启用。
9. 普通用户无法 `POST /runs`、设置 Harbor 并发或提交任意资源值；单机并发 1 由后端配置。
10. 没有公开注册；协作者不能批准自己的正式真实 Job、管理成员/配置、清理制品或人工复核；只有绑定的唯一评测所有者会话能执行这些操作，并发决定只有一个成功，决定者和时间可审计。
11. 批准只产生 `QUEUED`，不会在 HTTP 请求中运行 Harbor；拒绝后 Worker 永远领取不到，批准后轮询可观察后续状态。
12. Job 请求不能携带模型 Key、任意提供方/Base URL 或 shell；MVP 不提供自研源码提交路由。P2 自研配置只由所有者登记为 DeepSeek/Kimi，二者分别排行。
13. Quality Judge 只出现在严格确定性并列组；四项 rubric、匿名 A/B+B/A、两次一致才胜出和胜 1/平 0.5/负 0 的循环赛可重放；Failure Judge 不进入排行榜；Judge 失败或证据不足时 `quality_tiebreak=null` 且保持并列。
14. 过程指标永不参与排序，缺失显示未知而不是 0；所有者可作废 Quality 结论并恢复并列，但不能指定胜者。
15. 执行中取消进入 `CANCEL_REQUESTED`、不再启动新 Trial，当前 Trial 只到冻结超时；宿主/Worker/Harbor 中断不自动续跑或重试。
16. patch 超过 256 KiB 有警告、超过 1 MiB 或为二进制时明确拒绝且不截断；原始日志 50 MiB、每运行原始制品 200 MiB 的边界和截断标记可由接口观察。
17. 到期原始制品只能由所有者本机清理；正文删除返回 `410`，索引仍保留哈希、大小与删除审计。

## 14. 待技术核验

1. 账户、密码哈希、无邮件邀请、本地所有者恢复和会话的精确 HTTP 路径与现有代码承载位置；若必须新增顶层模块、接口或表，另行说明并取得确认。
2. `CANCEL_REQUESTED` 对不同 Harbor 阶段的适配细节，以及当前 Trial 到冻结超时后如何幂等收束；业务行为不改为强杀或自动重试。
3. Quality Judge 的具体模型、Prompt 和结构化响应 Schema；触发、rubric、双向一致性、循环赛及复核权限已确认。
4. 轨迹刷新是否在数据量证明轮询不足后升级 SSE；当前不提前引入。
5. 已确认的 patch/日志/运行制品限额在真实响应与下载上的边界行为，以及所有者本机清理命令的名称与参数。
6. P2 自研 Agent 提交 schema 和受控 DeepSeek/Kimi 访问；不阻塞 MVP。

## 15. 变更记录

- 2026-09-01：创建候选 v0.1；定义任务、Agent 配置、运行、轨迹、制品、报告、排行榜和人工复核接口，并明确错误、幂等、防泄漏和模块映射。
- 2026-09-02：创建运行与排行榜加入评测赛道；闭卷主榜、开卷实验榜及不同网络/工具配置禁止混合聚合。
- 2026-09-03：以 `/jobs` 作为批量提交与排队主资源，`/runs` 改为逐题只读资源；加入可信 Agent 源码提交审核、Job 报告、组合规模与 `internal_test` 隔离规则。
- 2026-09-05：远端提交改为创建 `AWAITING_OWNER_APPROVAL`；新增评测机所有者批准/拒绝接口，只有批准才进入 `QUEUED`，网络成员身份不替代应用授权。
- 2026-09-05：Agent 提交收窄为首版 Python 进程 Interface，自研配置只允许 DeepSeek/Kimi 且不接收 Key；报告与排行榜区分 Failure/Quality Judge，并固定严格并列触发和 Judge 失败保持并列。
- 2026-09-05：MVP 收窄为 Codex 闭卷平台闭环；固定协作者/唯一评测所有者两类角色、执行中取消与不自动重试、Quality 匿名反序比较、过程指标仅展示、制品限额/保留和 P2 自研 Agent 接缝。
