# Web 与后端 HTTP API 契约

> 文档状态：候选 v0.1，讨论中，尚未实现  
> 最后更新：2026-09-01  
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
| 长任务 | `POST /runs` 只入队并立即返回 `202`，不等待 Agent 完成 |
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
| `404` | 资源不存在 | `TASK_NOT_FOUND`、`RUN_NOT_FOUND` |
| `409` | 状态或幂等冲突 | `RUN_STATE_CONFLICT`、`IDEMPOTENCY_CONFLICT` |
| `422` | JSON 字段/schema 不合格 | `VALIDATION_ERROR` |
| `503` | 数据库、对象存储等暂不可用 | `DEPENDENCY_UNAVAILABLE` |
| `500` | 未预期平台错误 | `INTERNAL_ERROR` |

错误 `message` 面向人类；前端分支判断只使用稳定的 `code`，不能解析中文文案。

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
  "model": "fixed-model",
  "configuration_fingerprint": "sha256-hex",
  "enabled": true
}
```

不返回 API key、命令模板、宿主路径或私有环境变量。

### 4.3 `RunSummary`

```json
{
  "run_id": "01J...",
  "task_id": "opaque-task-id",
  "agent_configuration_id": "codex-model-config",
  "evaluation_track": "closed_book",
  "network_policy_id": "provider-only-v1",
  "tool_profile_id": "no-web-tools-v1",
  "status": "RUNNING_AGENT",
  "resolved": null,
  "review_status": "NOT_REQUIRED",
  "created_at": "2026-09-01T10:00:00Z",
  "started_at": "2026-09-01T10:00:03Z",
  "finished_at": null
}
```

`resolved=null` 表示确定性验证尚未产生结果；不能解释为失败。

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
| `agent_type` | query，可选 | `custom_process`、`codex`、`aider`、`claude_code` |
| `enabled` | query boolean，可选 | 页面发起评测默认只查 `true` |
| `cursor` / `limit` | query，可选 | 通用分页 |

成功 `200`：分页的 `AgentConfigurationSummary[]`。

### 6.2 查询配置详情

`GET /api/v1/agent-configurations/{agent_configuration_id}`

- 成功 `200`：公开配置、版本、模型、限制模板和指纹。
- 错误：`404 AGENT_CONFIGURATION_NOT_FOUND`。
- 首版不提供“上传任意 Agent”“提交 GitHub URL”或“提交 shell 命令”接口。

登记/修改 Agent 配置属于项目组管理流程。身份与权限规则尚未确认，因此不在 v0.1 对普通 Web 用户开放写接口。

## 7. Run API

### 7.1 创建评测运行

`POST /api/v1/runs`

Header：`Idempotency-Key: <客户端生成的不透明值>`。

请求：

```json
{
  "task_id": "opaque-task-id",
  "agent_configuration_id": "codex-model-config",
  "evaluation_track": "closed_book",
  "limit_profile_id": "default-single-host-v1"
}
```

成功 `202`：

```json
{
  "run_id": "01J...",
  "status": "QUEUED",
  "evaluation_track": "closed_book",
  "created_at": "2026-09-01T10:00:00Z"
}
```

错误：

- `404 TASK_NOT_FOUND`；
- `404 AGENT_CONFIGURATION_NOT_FOUND`；
- `409 AGENT_CONFIGURATION_DISABLED`；
- `409 IDEMPOTENCY_CONFLICT`；
- `400 LIMIT_PROFILE_NOT_ALLOWED`。
- `400 EVALUATION_TRACK_NOT_ALLOWED`。

前端不能提交任意 CPU/内存/网络值、代理地址、工具命令或启动命令，只能选择 `closed_book`/`open_book_experimental` 赛道和平台登记的限制模板。后端根据赛道与 Agent 配置解析并冻结网络策略和工具配置。

### 7.2 查询运行列表

`GET /api/v1/runs`

筛选：`status`、`task_id`、`agent_configuration_id`、`evaluation_track`、`resolved`、`review_status`、`cursor`、`limit`。成功 `200` 返回分页 `RunSummary[]`。

### 7.3 查询运行详情

`GET /api/v1/runs/{run_id}`

成功 `200` 至少返回：

- `RunSummary`；
- 冻结的任务和 Agent 配置快照；
- Run limits；
- 评测赛道、网络策略和工具配置的安全快照；
- 当前阶段和最近一次安全状态说明；
- 确定性结果摘要（若已有）；
- Judge 分析摘要（若已有）；
- 人工复核摘要（若已有）；
- 制品数量与相应查询链接。

错误：`404 RUN_NOT_FOUND`。

### 7.4 取消运行

`POST /api/v1/runs/{run_id}/cancel`

请求：

```json
{"reason":"用户请求取消"}
```

- 成功 `202`：返回更新后的 `RunSummary`。
- 只允许 `QUEUED` 或能安全停止的早期状态；精确范围待 Worker 最小实验确认。
- 已完成、验证中或已失败时返回 `409 RUN_STATE_CONFLICT`。
- 这是候选能力；如果一个月范围需要缩减，可以先只支持取消 `QUEUED`。

## 8. Trajectory 与 Artifact API

### 8.1 分页读取规范化轨迹

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

### 8.2 查询制品索引

`GET /api/v1/runs/{run_id}/artifacts`

输入：可选 `artifact_type`、`cursor`、`limit`。成功 `200` 返回：`artifact_id`、类型、文件名、内容类型、大小、SHA-256、创建时间；不返回 MinIO secret。

### 8.3 下载制品

`GET /api/v1/artifacts/{artifact_id}/content`

- 成功 `200`：由后端流式返回内容，并设置正确 `Content-Type`/`Content-Disposition`。
- 错误：`404 ARTIFACT_NOT_FOUND`、`409 ARTIFACT_NOT_READY`。
- 候选 v0.1 不把 MinIO 管理凭据交给浏览器；未来若改为短时预签名 URL，需要单独记录安全决定。

## 9. Report 与 Leaderboard API

### 9.1 单次运行报告

`GET /api/v1/reports/runs/{run_id}`

成功 `200` 分层返回：

```json
{
  "run": {},
  "deterministic_result": {},
  "process_metrics": {},
  "judge_analysis": null,
  "human_review": null,
  "artifact_links": []
}
```

规则：`deterministic_result`、`process_metrics`、`judge_analysis`、`human_review` 不合并为一个模糊的“总评价”。总分规则仍待确认。

### 9.2 排行榜

`GET /api/v1/leaderboard`

输入：必需的 `evaluation_track`，以及 `dataset_id`、`dataset_revision`、`split`、可选 `repo`、`tool_profile_id`、`cursor`、`limit`。

每行至少包含：

- `agent_configuration_id` 和公开配置快照；
- `evaluation_track`、`network_policy_id`、`tool_profile_id`；
- 已完成任务数；
- `resolved_count` 和 `resolved_rate`；
- 基础设施错误数，不能算成普通未解决而隐藏；
- 过程指标摘要（只展示，是否计分待确认）；
- 数据集 revision 和统计生成时间。

同一 Agent 使用不同模型或关键配置时必须分行。

闭卷主排行榜与开卷实验榜必须通过必需的 `evaluation_track` 分开查询；不同网络策略或工具配置也不得被聚合成同一行。开卷依旧使用同一 `resolved` 判卷标准，但页面要显著标注其允许联网，不能与闭卷成功率直接混排。

## 10. Human Review API

### 10.1 查询待复核队列

`GET /api/v1/reviews`

输入：`status`、`cursor`、`limit`。成功 `200` 返回待复核运行摘要和证据链接。

### 10.2 提交或修订人工复核

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

身份认证尚未确定，因此 `reviewer_id` 不允许由请求正文随意填写；未来应从可信会话取得。没有认证前，只能在本机受控演示环境使用该接口。

## 11. API 到内部模块的映射

| HTTP 资源 | 只允许调用的应用模块 |
|---|---|
| `/tasks` | Task Catalog 查询 |
| `/agent-configurations` | Agent Registry 查询 |
| `POST /runs` | Run Submission |
| `GET /runs*` | Reporting / Run Repository 只读查询 |
| `POST /runs/{id}/cancel` | Run lifecycle 用例 |
| `/trajectory`、`/artifacts` | Reporting + Artifact Store 只读读取 |
| `/reports`、`/leaderboard` | Reporting |
| `/reviews` | Human Review |

FastAPI route 文件只做 schema、HTTP 状态和用例调用，不能直接启动 Docker 或调用 SWE-Bench-Fork。

## 12. 接口验证

实现后至少执行：

1. OpenAPI schema 快照检查；本文示例与 schema 的字段/状态码对照。
2. Next.js 使用由 OpenAPI 生成或同步的 TypeScript 类型，避免手写两套字段。
3. 每个端点覆盖成功、资源不存在、schema 错误和状态冲突。
4. 确认 Task/Agent API 不泄漏 gold patch、隐藏测试、启动命令和秘密。
5. 创建运行响应不等待 Worker；轮询能观察合法状态迁移。
6. 排行榜按完整 Agent 配置分组，并单列基础设施错误。
7. 原始制品下载不暴露 MinIO 管理凭据，轨迹默认已脱敏。
8. 创建运行冻结赛道/网络/工具配置；闭卷和开卷查询不会跨赛道混分。

## 13. 仍待确认

1. 是否需要登录、学生/教师/管理员角色，以及谁能发起、取消、复核运行。
2. v0.1 是否保留取消接口，还是只支持查看。
3. Judge 和过程指标的最终计分规则，决定报告是否增加独立评分字段。
4. 开卷实验榜使用平台统一 Web 工具，还是允许 Agent 原生搜索工具。
5. 轨迹刷新是否在数据量证明轮询不足后升级 SSE；当前不提前引入。
6. 最大分页、日志下载和保留期限的具体值。

## 14. 变更记录

- 2026-09-01：创建候选 v0.1；定义任务、Agent 配置、运行、轨迹、制品、报告、排行榜和人工复核接口，并明确错误、幂等、防泄漏和模块映射。
- 2026-09-02：创建运行与排行榜加入评测赛道；闭卷主榜、开卷实验榜及不同网络/工具配置禁止混合聚合。
