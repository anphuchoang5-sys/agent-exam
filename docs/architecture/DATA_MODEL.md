# 数据模型与制品布局

> 文档状态：Job/Run 架构已确认；字段契约 v0.3，尚未实现
>
> 最后更新：2026-09-05
> 权威范围：本文件维护 PostgreSQL 实体、运行状态持久化、队列领取规则和 MinIO 对象布局。领域词义见 [`CONTEXT.md`](../../CONTEXT.md)，模块输入输出见 [`MODULE_CONTRACTS.md`](./MODULE_CONTRACTS.md)。

## 1. 给初学者的解释

系统产生两种数据：

- PostgreSQL 像“目录和登记簿”：保存能查询、筛选、关联的短数据，例如某次运行是谁、什么状态、是否通过。
- MinIO 像“证据文件柜”：保存补丁、长日志、JSONL 轨迹和 Judge 原始响应等文件。

数据库只保存文件柜中的“档案号、大小和校验和”，不把所有大文件塞进表里。

## 2. 数据边界

| 数据 | PostgreSQL | MinIO | 原因 |
|---|---:|---:|---|
| 任务身份、仓库、固定提交、Issue 标准字段 | ✅ | ✅ 内容哈希固定的原始任务 JSON | 数据库负责查询，原始快照负责复现和审计 |
| gold patch、`test_patch`、隐藏测试 | 仅受限验证引用 | 可选受限制品 | 不得通过普通 API/Runner 泄漏 |
| Agent 配置身份、版本、模型、配置指纹 | ✅ | 可选配置快照 | 排行榜与复现需要 |
| P2 Agent 源码提交与审核状态 | P2 | P2 可选审核附件 | MVP 不建表/接口；未来审核前仍不得进入执行链路 |
| Job/运行状态、所有者批准/拒绝、时间、限制、Worker 租约 | ✅ | ❌ | Job 需要先审计所有者决定再事务领取，运行需要逐题追溯 |
| 最终 patch | 元数据/摘要 | ✅ | 文件证据，不可覆盖 |
| 原始 stdout/stderr、轨迹 JSONL | 索引/汇总 | ✅ | 体积大、适合流式读写 |
| Harness 报告摘要 | ✅ | ✅ 原始报告/测试输出 | 查询与原始证据都需要 |
| Judge 用途、状态及失败/质量摘要 | ✅ | ✅ 清洗后请求/原始响应 | 保留触发、模型和输入策略证据；不保存秘密 |
| 人工复核结论 | ✅ | 可选附件 | 需要版本化和审计 |

## 3. 实体关系

```mermaid
erDiagram
    AGENT_SOURCE_SUBMISSIONS ||--o| AGENT_CONFIGURATIONS : may_register_as
    EVALUATION_JOBS ||--o{ EVALUATION_RUNS : contains
    EVALUATION_TASKS ||--o{ EVALUATION_RUNS : selected_for
    AGENT_CONFIGURATIONS ||--o{ EVALUATION_RUNS : executed_by
    EVALUATION_JOBS ||--o{ JOB_STATE_EVENTS : records
    EVALUATION_RUNS ||--o{ RUN_STATE_EVENTS : records
    EVALUATION_RUNS ||--o| DETERMINISTIC_RESULTS : produces
    EVALUATION_JOBS ||--o{ JUDGE_ANALYSES : may_produce_quality
    EVALUATION_RUNS ||--o{ JUDGE_ANALYSES : may_produce_failure
    EVALUATION_JOBS ||--o{ HUMAN_REVIEWS : may_receive_quality_review
    EVALUATION_RUNS ||--o{ HUMAN_REVIEWS : may_receive_run_review
    EVALUATION_TASKS ||--o{ ARTIFACT_RECORDS : owns_snapshot
    EVALUATION_JOBS ||--o{ ARTIFACT_RECORDS : owns_job_evidence
    EVALUATION_RUNS ||--o{ ARTIFACT_RECORDS : owns_run_evidence
    JUDGE_ANALYSES ||--o{ HUMAN_REVIEWS : reviewed_by

    EVALUATION_TASKS {
      string task_id PK
      string dataset_id
      string dataset_revision
      string split
      string instance_id
      string repo
      string base_commit
      string problem_sha256
      string source_snapshot_ref
    }
    AGENT_CONFIGURATIONS {
      string agent_configuration_id PK
      string source_submission_id FK
      string agent_type
      string agent_version
      string model_provider
      string model
      string credential_profile_id
      string configuration_fingerprint
      boolean enabled
    }
    AGENT_SOURCE_SUBMISSIONS {
      string submission_id PK
      string git_url
      string commit_sha
      string manifest_sha256
      string status
      string submitted_by
      string reviewed_by
    }
    EVALUATION_JOBS {
      string job_id PK
      string evaluation_track
      string result_scope
      string status
      int trial_count
      int row_version
      string owner_decided_by
      datetime owner_decided_at
      string claimed_by
      datetime lease_expires_at
      datetime cancel_requested_at
    }
    EVALUATION_RUNS {
      string run_id PK
      string job_id FK
      string task_id FK
      string agent_configuration_id FK
      int attempt_index
      string status
      string backend_kind
      string backend_trial_ref
      boolean resolved_summary
    }
    JOB_STATE_EVENTS {
      string event_id PK
      string job_id FK
      string from_status
      string to_status
      string reason_code
      string actor_user_id
      datetime occurred_at
    }
    RUN_STATE_EVENTS {
      string event_id PK
      string run_id FK
      string from_status
      string to_status
      string reason_code
      datetime occurred_at
    }
    DETERMINISTIC_RESULTS {
      string run_id PK, FK
      boolean patch_exists
      boolean patch_applied
      boolean resolved
      string harness_revision
      string report_artifact_id
    }
    JUDGE_ANALYSES {
      string judge_analysis_id PK
      string run_id FK
      string job_id FK
      string judge_purpose
      string comparison_key
      string status
      string model
      string prompt_version
      string input_policy_version
      string failure_category
      string quality_result
      string raw_response_artifact_id
    }
    HUMAN_REVIEWS {
      string human_review_id PK
      string run_id FK
      string job_id FK
      string judge_analysis_id FK
      int version
      string assessment
      string reviewer_id
    }
    ARTIFACT_RECORDS {
      string artifact_id PK
      string run_id FK
      string job_id FK
      string task_id FK
      string artifact_type
      string object_key
      string sha256
      int size_bytes
      string retention_class
      datetime expires_at
      datetime deleted_at
    }
```

## 4. 表级契约

字段是候选 v0.3 的最小集合；实现迁移文件前仍要确定数据库类型、索引名和长度限制。

应用身份已经收窄为 `collaborator` 与唯一 `owner`。所有 `created_by`、`actor_user_id`、`reviewer_id`、清理者和所有者决定字段都必须引用可信登录身份，不能由请求正文自报；所有者在评测机本地建立/恢复并邀请协作者。账号、密码哈希、邀请和 session 的物理存储尚未核验，本轮遵守最小修改原则，不预先增加用户表。

### 4.1 `evaluation_tasks`

用途：登记可评测的固定 SWE-Gym 任务身份。

| 字段 | 约束/含义 |
|---|---|
| `task_id` | 主键；由数据集 ID、固定 revision、split、instance 生成或映射为不透明 ID |
| `dataset_id` | 例如已登记的 SWE-Gym Hugging Face 数据集 ID |
| `dataset_revision` | 固定 revision/校验值；禁止用会漂移的 `latest` 进入正式运行 |
| `split` | 上游真实 split |
| `instance_id` | 上游任务 ID；与 dataset/revision/split 组成唯一约束 |
| `repo` / `base_commit` | 仓库和固定代码基线 |
| `problem_statement` | 供页面查询和 Agent 输入的标准 Issue 原文 |
| `problem_sha256` | 防止同 ID 内容漂移 |
| `source_snapshot_ref` | 必需的 MinIO 原始任务 JSON 引用，包含对象键、SHA-256、大小和数据集来源；与标准字段在同一同步动作中固定 |
| `validation_ref` | 只供 Evaluator 解析上游测试字段的受限引用；普通 API 不返回 |
| `created_at` | 登记时间 |

不直接允许 Web 修改任务内容；任务同步是项目组的受控维护动作。原始 JSON 可以包含仅供 Evaluator 的上游字段，但普通 API 和 Agent 可见视图只能读取允许字段，不能返回隐藏测试或参考答案。

### 4.2 `agent_configurations`

用途：登记排行榜和 Execution Backend 使用的完整可复现身份。

| 字段 | 约束/含义 |
|---|---|
| `agent_configuration_id` | 主键，不透明稳定 ID |
| `source_submission_id` | 可空外键；自研 Agent 来自哪条已批准源码提交，内置 Agent 可空 |
| `display_name` | 面向页面的名称，不参与唯一性判断 |
| `agent_type` | `custom`、`codex`、`aider`、`claude_code`；执行方式另由受控 Adapter 映射 |
| `agent_version` | 精确 Agent/CLI/代码 revision |
| `model_provider` | 精确提供方身份；MVP Codex 记录 `openai_chatgpt`；P2 自研 Agent 才只允许 `deepseek` 或 `kimi` |
| `model` | 精确模型身份；若无则明确 `none` |
| `credential_profile_id` | 执行节点可解析的非秘密逻辑引用；不得包含 Key、真实路径或 Token |
| `public_options` | JSONB；只含 Adapter schema 允许且可公开的行为配置 |
| `limit_profile_id` | 默认限制模板 |
| `configuration_fingerprint` | 规范化配置的 SHA-256；唯一约束候选 |
| `enabled` | 是否允许创建新运行；禁用不删除历史 |
| `created_at` / `disabled_at` | 审计时间 |

秘密、宿主机路径、任意启动命令、提供方 Base URL 和代理地址不能存入 `public_options`。MVP 只登记 Codex，随后登记 Harbor 已有 Aider/Claude Code；P2 同一自研 Agent 源码使用 DeepSeek 与 Kimi 时生成两个不同配置指纹和排行榜身份。真实 Key 不存 PostgreSQL；具体启动模板与受控模型访问部署属于评测机配置，并且同样要版本化。

### 4.3 `agent_source_submissions`（P2，MVP 不建表）

用途：未来保存协作者提交的固定自研 Agent 源码及所有者审核结果。提交记录不是可执行配置；MVP 不实现本表或相应接口。

| 字段 | 约束/含义 |
|---|---|
| `submission_id` | 主键，不透明 ID |
| `git_url` | 规范化仓库 URL；只允许所有者策略支持的协议/来源 |
| `commit_sha` | 完整不可变 commit；禁止分支名、tag 或 `latest` |
| `manifest_path` | 首版固定仓库根 `agent-exam.yaml` |
| `manifest_sha256` | 同一 commit 中 manifest 内容哈希 |
| `status` | `PENDING_REVIEW`、`APPROVED`、`REJECTED`、`WITHDRAWN` |
| `submitted_by` / `submitted_at` | 来自可信会话，不由正文伪造 |
| `reviewed_by` / `reviewed_at` | 所有者会话与时间；待审核时为空 |
| `review_notes` | 安全说明；不得写秘密 |

P2 审核前不得执行源码、构建镜像或生成 AgentConfiguration。自研接入首版 manifest 只接受 Python 进程 Interface 声明，不接收 shell、Key、自定义提供方/Base URL、代理或宿主路径；完整 schema、Python 版本和依赖锁格式到 P2 再核验。审核通过也不覆盖原提交；另建配置并通过 `source_submission_id` 关联。

### 4.4 `evaluation_jobs`

用途：用户一次提交的批次主记录，也是首版 PostgreSQL 重型工作队列。

| 字段 | 约束/含义 |
|---|---|
| `job_id` | 主键；批次、Job 事件和组合查询的追溯主线 |
| `evaluation_track` | 模型保留 `closed_book`/`open_book_experimental`；MVP 新 Job 只允许 `closed_book`，Job 内不可切换 |
| `result_scope` | `official`、`experimental` 或 `internal_test`；Mock 只能是 `internal_test` |
| `limit_profile_id` / `limit_snapshot` | 已登记限制模板和创建时快照 |
| `network_policy_id` / `network_policy_snapshot` | 实际网络规则的 ID 与不可变快照 |
| `tool_profile_id` / `tool_profile_snapshot` | 实际工具集合、版本和关键限制 |
| `harbor_revision` / `swe_gym_revision` / `swe_bench_fork_revision` | 本 Job 冻结的框架提交/数据版本 |
| `trial_count` | 创建事务中生成的运行总数；等于去重任务数×去重 Agent 数×尝试数 |
| `status` | 见第 5 节 Job 状态机 |
| `row_version` | 乐观并发控制；每次更新递增 |
| `owner_decided_by` / `owner_decided_at` | 评测机所有者的可信会话身份和最终决定时间；待批准时为空，不由请求正文填写 |
| `owner_decision_reason` | 可选安全说明；不得包含凭据、Token 或宿主秘密路径 |
| `claimed_by` / `claimed_at` | 当前 Worker 身份和领取时间 |
| `heartbeat_at` / `lease_expires_at` | Worker 存活与恢复判断 |
| `cancel_requested_by` / `cancel_requested_at` / `cancel_reason` | 执行中取消请求的可信身份、时间和安全说明；请求不表示当前 Trial 已被强杀 |
| `failure_code` / `failure_summary` | Job 级平台失败；部分 Trial 失败仍可保留完成证据 |
| `created_by` | 来自可信会话的用户身份 |
| `created_at` / `started_at` / `finished_at` | 生命周期时间 |
| `idempotency_key_hash` | 创建请求幂等；不保存原始敏感 header |

首版在同一事务创建 `AWAITING_OWNER_APPROVAL` Job 及全部 Agent×任务运行，避免待审记录已可见但组合缺失。批准事务只允许把状态推进到 `QUEUED` 并追加事件，不能修改已冻结组合；拒绝事务把 Job 改为 `REJECTED`，并把其全部 `PENDING` 运行改为 `CANCELED`。待批准/排队取消可直接进入 `CANCELED`；执行中取消写入请求字段并进入 `CANCEL_REQUESTED`，不再启动后续 Trial。Job 的进度计数从运行状态查询或受控同步得出，不能由前端任意写入。

### 4.5 `evaluation_runs`

用途：保存一个 Job 内，一个 Agent×一个任务×一次尝试的逐题事实；它不是独立 PostgreSQL 队列项。

| 字段 | 约束/含义 |
|---|---|
| `run_id` | 主键；所有逐运行制品和子记录的追溯主线；任务/Job 级制品分别使用自己的所有者字段 |
| `job_id` | 必需外键；所属平台评测 Job |
| `task_id` / `agent_configuration_id` | 外键；创建后不可更换 |
| `attempt_index` | 首版固定 `1`；`(job_id, task_id, agent_configuration_id, attempt_index)` 唯一 |
| `task_snapshot` / `agent_snapshot` | JSONB 公开快照；确保历史报告不随展示名修改而变化 |
| `execution_contract_version` | Execution Backend interface 版本；后备进程另记录 Runner 协议版本 |
| `backend_kind` / `backend_revision` | 首版 `harbor` 与固定 commit；内部测试可为 `mock` |
| `backend_job_ref` / `backend_trial_ref` | Harbor Job/Trial 审计引用；不能替代项目 ID |
| `status` | 见第 5 节状态机 |
| `stage` | 可选的安全阶段摘要；不能代替状态历史 |
| `row_version` | 乐观并发控制；每次更新递增 |
| `failure_code` / `failure_summary` | 仅平台失败时填写；不得写入秘密 |
| `resolved_summary` | 只在确定性结果产生后镜像其布尔值；允许 `null` |
| `created_at` / `started_at` / `finished_at` | 生命周期时间 |

`resolved_summary` 是为了列表查询的受控冗余，权威值仍在 `deterministic_results.resolved`。写入必须在同一事务同步，不能各自更新。

### 4.6 `job_state_events`

用途：追加式记录 Job 从远端提交、所有者决定、排队、领取、执行、汇总到结束的状态变化。

字段：`event_id`、`job_id`、`sequence`、`from_status`、`to_status`、`reason_code`、安全说明、可选 `actor_user_id`、可选 `worker_id`、`occurred_at`。所有者批准/拒绝事件写 `actor_user_id`；Worker 生命周期事件写 `worker_id`。`(job_id, sequence)` 唯一。

### 4.7 `run_state_events`

用途：追加式记录每次状态变化，解决“现在是什么”和“怎样走到这里”两个问题。

字段：`event_id`、`run_id`、`sequence`、`from_status`、`to_status`、`reason_code`、安全说明、`worker_id`、`occurred_at`。`(run_id, sequence)` 唯一。

不变量：已经写入的状态事件不修改、不删除；错误更正通过新事件说明，当前状态由受控事务推进。

### 4.8 `deterministic_results`

用途：每次运行最多一条最终 SWE-Bench-Fork 判定摘要。

| 字段 | 来源 |
|---|---|
| `patch_exists` | Execution Backend patch 是否存在/非空 |
| `patch_successfully_applied` | Harness 报告 |
| `resolved` | Harness 报告；唯一确定性通过事实 |
| `tests_status_summary` | 从 `FAIL_TO_PASS`/`PASS_TO_PASS` 结果生成的可查询 JSONB 摘要 |
| `harness_revision` | 固定 SWE-Bench-Fork commit |
| `report_artifact_id` | 原始 `report.json` 制品 |
| `test_output_artifact_id` | 原始测试输出制品 |
| `duration_ms` | Harness 观察的验证耗时 |
| `created_at` | 结果落库时间 |

若 Harness 因基础设施错误没有形成可信结果，不创建伪造的 `resolved=false`；运行进入 `FAILED` 并保存错误制品。

### 4.9 `judge_analyses`

用途：在同一表保存 LLM 失败诊断或 Job 级质量并列比较。多条记录允许 Prompt、模型、rubric 或输入策略升级后保留旧证据；不新增独立质量表。

字段：`judge_analysis_id`、可空 `run_id`、`job_id`、`judge_purpose`（`failure_diagnosis`/`quality_tiebreak`）、可空 `comparison_key`、`status`、`schema_version`、`model`、`prompt_version`、`input_policy_version`、`rubric_version`、可空 `failure_category`、可空 `quality_result` JSONB、解释、证据引用列表、`input_artifact_id`、`raw_response_artifact_id`、`created_at`。

`failure_diagnosis` 逐运行保存，`run_id` 必需、`comparison_key` 与 `quality_result` 为空。`quality_tiebreak` 是 Job 级严格并列组分析，`job_id` 与不可变 `comparison_key` 必需、`run_id` 为空；`quality_result` 保存匿名候选映射、共同通过题、四维 rubric 观察、A/B 与 B/A 两次输出、每对最终胜/平/负以及循环积分。每对只有两次都选择同一赢家才记胜负，其余情况记平；积分为胜 1、平 0.5、负 0。同一用途、目标、rubric、模型、Prompt 和输入策略版本不得重复写入；任一版本升级时追加新记录，不覆盖旧分析。

不变量：Judge 不拥有 `resolved` 字段；输入必须是裁剪、脱敏、去重、限量后的版本；候选身份和 A/B 顺序映射不交给 Judge；结构化解析失败、任一反序结论冲突或分析被所有者作废时保持相应并列，不能强行生成胜者。

### 4.10 `human_reviews`

用途：保存所有者对证据和 Judge 分析的确认、修正或作废。

字段：`human_review_id`、可空 `run_id`、可空 `job_id`、可选 `judge_analysis_id`、`version`、`assessment`、可选修正失败分类、备注、`reviewer_id`、`created_at`。Failure 复核绑定 `run_id`；Quality 复核绑定 `job_id` 和具体 `judge_analysis_id`。复核者只能是 `owner`；Quality 允许确认或作废并恢复并列，不提供指定赢家/手填积分字段。

旧版本不覆盖；API 返回最高版本作为当前视图，同时允许查看历史。

### 4.11 `artifact_records`

用途：把 PostgreSQL 记录与 MinIO 对象可靠关联。

| 字段 | 约束/含义 |
|---|---|
| `artifact_id` | 主键；创建对象键前生成 |
| `run_id` / `job_id` / `task_id` | 三选一的所有者范围；运行证据、Job 级 Quality 证据和任务原始快照都复用本表，不伪造 run |
| `artifact_type` | 受控枚举，见第 7 节 |
| `object_key` | MinIO 对象键；唯一 |
| `original_filename` | 仅展示，必须去路径化和清理 |
| `content_type` | 受控 MIME type |
| `size_bytes` / `sha256` | 完整性校验 |
| `redaction_status` | `not_required`、`redacted`、`blocked` |
| `retention_class` / `expires_at` | `long_term` 或 `raw_30d`；后者创建时写 30 天后可清理时间，不表示届时已自动删除 |
| `truncated` / `original_size_bytes` | 日志被显式截断时保留事实；patch 绝不截断 |
| `deleted_at` / `deleted_by` / `deletion_reason` | 对象清理审计；正文删除后记录、哈希、大小和产生时间仍保留 |
| `created_at` | 写入完成时间 |

数据库记录只在对象成功写入并校验后标记可读；失败的半成品通过临时键清理，不能出现在正常报告中。三种所有者字段必须恰有一个非空；删除后的读取显式返回“已按保留策略清理”，不能伪装成对象从未存在。

## 5. Job 与运行状态机

### 5.1 评测 Job

```mermaid
stateDiagram-v2
    [*] --> AWAITING_OWNER_APPROVAL
    AWAITING_OWNER_APPROVAL --> QUEUED: 评测机所有者批准
    AWAITING_OWNER_APPROVAL --> REJECTED: 评测机所有者拒绝
    AWAITING_OWNER_APPROVAL --> CANCELED: 提交者或所有者取消
    QUEUED --> PREPARING: Worker 原子领取
    PREPARING --> EXECUTING: Harbor Job 已建立映射
    EXECUTING --> FINALIZING: 所有 Trial 已终止
    EXECUTING --> CANCEL_REQUESTED: 提交者或所有者请求取消
    CANCEL_REQUESTED --> FINALIZING: 当前 Trial 结束或达到冻结超时
    FINALIZING --> COMPLETED: 所有运行形成可信确定性结果
    FINALIZING --> COMPLETED_WITH_ERRORS: 部分运行基础设施失败
    FINALIZING --> CANCELED: 取消请求已收束

    QUEUED --> CANCELED
    PREPARING --> CANCELED: 尚未启动 Trial
    PREPARING --> FAILED
    EXECUTING --> FAILED: 无法继续且无可汇总 Job 结果
    FINALIZING --> FAILED

    COMPLETED --> [*]
    COMPLETED_WITH_ERRORS --> [*]
    FAILED --> [*]
    CANCELED --> [*]
    REJECTED --> [*]
```

`AWAITING_OWNER_APPROVAL` 不属于可执行队列，不能被 Worker 领取。`REJECTED` 是所有者作出的终态，不等同于平台失败；对应的 `PENDING` 运行在同一决定事务中改为 `CANCELED`，且不产生真实执行证据。`CANCEL_REQUESTED` 不是终态：它冻结后续 Trial，当前 Trial 仍可运行到原先冻结的超时上限，随后保存真实结果或基础设施失败证据；尚未开始的运行改为 `CANCELED`，Job 经 `FINALIZING` 收束为 `CANCELED`。`COMPLETED` 只表示重型执行和确定性判卷均已结束；其中的运行仍可以处于 `REVIEW_PENDING`，人工复核进度单独展示，不能因此长期占住单机重型队列。`COMPLETED_WITH_ERRORS` 允许保留已经完成的 Trial 证据，同时显式告诉用户有部分运行没有形成可信结果；它不能伪装成全部完成。

### 5.2 逐题评测运行

```mermaid
stateDiagram-v2
    [*] --> PENDING
    PENDING --> PREPARING: 对应 Harbor Trial 开始
    PREPARING --> RUNNING_AGENT: Harbor Agent 环境就绪
    RUNNING_AGENT --> VERIFYING: 补丁和执行证据已固定
    VERIFYING --> ANALYZING: 失败运行命中自动抽样
    VERIFYING --> REVIEW_PENDING: 确定性结果已固定且需人工复核
    VERIFYING --> COMPLETED: 确定性结果已固定且无需运行级分析
    ANALYZING --> REVIEW_PENDING: 命中抽检规则
    ANALYZING --> COMPLETED: 分析完成或不可用且不需人工复核
    REVIEW_PENDING --> COMPLETED: 人工复核完成

    PENDING --> CANCELED
    PREPARING --> CANCELED: 已安全停止
    PREPARING --> FAILED
    RUNNING_AGENT --> FAILED
    VERIFYING --> FAILED

    COMPLETED --> [*]
    FAILED --> [*]
    CANCELED --> [*]
```

状态规则：

- 只有列出的有向边允许执行；不允许 `COMPLETED → RUNNING_AGENT` 之类回退。
- Agent 正常产生空补丁或错误补丁，但 Harness 正常完成时，运行最终可为 `COMPLETED` 且 `resolved=false`。
- `FAILED` 表示平台链路没能形成可信最终结果，不是“题没做对”的同义词。
- 重跑创建新 Job 和新 `run_id`，通过 `rerun_of_job_id` / `rerun_of_run_id`（候选字段）关联旧记录，不覆盖历史。
- `review_status` 是 API 视图，可由当前状态与最高版本人工复核派生，不单独维护第二套冲突状态。
- Harbor `TrialResult`、reward 或异常不会直接改数据库状态；必须先经 Execution Backend 错误/结果映射。
- Job 进入 `CANCEL_REQUESTED` 后不再启动新的 `PENDING` 运行；当前活跃运行不强杀，按真实结果或冻结超时落盘。
- Worker、宿主机或 Harbor 中断后不自动续跑或重试；所有者若决定重试，创建带 `rerun_of_job_id` 的新 Job 和新证据链。
- 人工请求的 Failure Judge 可以在确定性结果形成后追加记录，不要求把终态运行重新打开；Quality Judge 在同一比较范围的全部确定性结果形成后追加，也不改变逐运行状态。
- Judge 模型不可用、证据不足或输出无效不是运行基础设施失败；保存分析失败状态后，运行仍按确定性结果完成，Quality 候选保持并列。

## 6. PostgreSQL 队列领取

首版不引入 Redis/Celery，也不把每条运行单独排队。候选流程：

1. Worker 在短事务中选择最早的 `QUEUED` `evaluation_jobs` 记录，并使用 PostgreSQL 行锁跳过已锁记录。
2. 同一事务确认当前不存在其他活跃重型 Job，把选中 Job 改为 `PREPARING`，填写租约并追加 Job 状态事件。
3. 提交事务后才创建 Harbor Job 和执行 Trial，绝不在耗时 Docker/Agent 工作期间持有数据库锁。
4. Worker 定期更新心跳和租约，但每次更新检查 `row_version` 和 `claimed_by`。
5. 租约过期不直接重跑。恢复器检查容器和制品：能证明 Trial 已完成时只做幂等收束；否则把活跃运行记为明确的 `INFRASTRUCTURE_INTERRUPTED` 基础设施失败、取消未开始运行并终结旧 Job，绝不自动重新排队。

所有者批准与 Worker 领取是两个事务：批准只做 `AWAITING_OWNER_APPROVAL → QUEUED`，不创建 Harbor Job；Worker 查询条件只包含 `status = 'QUEUED'`。实现候选使用 `SELECT ... FOR UPDATE SKIP LOCKED`，并用 PostgreSQL 可验证约束或全局租约确保活跃重型 Job 不超过 1。精确 SQL、隔离级别、租约时长和崩溃后 Harbor Job 恢复方式必须通过双 Worker 集成测试后固定。

## 7. MinIO 制品

### 7.1 Bucket 和对象键

候选使用一个私有 bucket：`evaluation-artifacts`。

对象键：

```text
tasks/{dataset_id}/{dataset_revision}/{instance_id}/{sha256}/task.json
jobs/{job_id}/runs/{run_id}/{artifact_id}/{safe_filename}
```

例：

```text
tasks/SWE-Gym%2FSWE-Gym-Lite/fixed-revision/django__django-12345/9f.../task.json
jobs/job_01J.../runs/run_01J.../art_01J.../patch.diff
jobs/job_01J.../runs/run_01J.../art_02J.../trajectory.jsonl
jobs/job_01J.../runs/run_01J.../art_03J.../test-output.txt
```

任务快照键中的路径段先做固定安全编码（示例中的 `%2F`），`sha256` 由原始任务 JSON 字节计算，同一内容可复用而不可覆盖；运行制品使用 `artifact_id` 避免同名覆盖，`safe_filename` 只用于人类识别、不参与寻址。对象键中不包含 Agent prompt、仓库绝对路径、用户名或秘密。

### 7.2 制品类型

| `artifact_type` | 内容 | 默认可展示性 |
|---|---|---|
| `task_source_snapshot` | 与标准字段同时冻结的原始任务 JSON；由内容哈希寻址 | 仅评测端受限审计；不得向 Agent 暴露隐藏字段 |
| `execution_patch` | Execution Backend 返回并校验的最终统一 patch | 可展示，仍需文本安全处理 |
| `trajectory_normalized` | 脱敏 JSONL 轨迹 | 可展示/分页 |
| `agent_stdout_raw` | 上游原始 stdout | 受限，先脱敏 |
| `agent_stderr_raw` | 上游原始 stderr | 受限，先脱敏 |
| `execution_result` | 规范化 `ExecutionTrialResult` | 可展示摘要 |
| `harbor_job_config` | 脱敏后的 Harbor Job 配置/锁定输入 | 受限审计 |
| `harbor_trial_result` | 脱敏后的 Harbor Trial 原始结果 | 受限审计 |
| `harbor_artifact_manifest` | Harbor artifact 收集状态 | 受限审计；必需 patch 失败会阻止判卷 |
| `harness_report` | SWE-Bench-Fork `report.json` | 可展示 |
| `test_output` | 测试输出 | 可展示，限制大小 |
| `judge_input` | Judge 实际输入证据 | 受限审计 |
| `judge_response_raw` | LLM 原始响应 | 受限审计 |
| `review_attachment` | 所有者人工复核附件 | 仅所有者 |

### 7.3 大小、格式与保留策略

- 最终 patch 按抽取后的统一 diff 字节计数：超过 256 KiB 写警告；超过 1 MiB 以 `PATCH_TOO_LARGE` 明确判为无效 Agent 输出，不调用 Harness、不登记为 `execution_patch`，也不截断或伪造小 patch；错误记录至少保留观察到的大小和原因。
- 二进制 patch 直接以 `BINARY_PATCH_NOT_ALLOWED` 判为无效 Agent 输出。MVP 只接受可审计的文本统一 diff。
- 单个轨迹、stdout、stderr 或 Judge 原始制品上限 50 MiB；超过时只允许保留头尾等明确策略生成的版本，必须设置 `truncated=true` 和 `original_size_bytes`，正文中也写可见截断标记。
- 每个运行的原始制品总额上限 200 MiB。核心配置快照、确定性结果、最终 patch 和测试摘要优先完整保存；达到上限时必须写明确的制品限额错误，不能静默丢失后仍声称证据完整。
- `long_term`：核心配置快照、任务来源引用、确定性结果、最终 patch 和测试摘要，长期保留。
- `raw_30d`：大体积轨迹、原始 stdout/stderr、Judge 原始输入/响应，创建时写 `expires_at=created_at+30 days`。
- MVP 不运行定时删除服务。只有所有者可执行本机维护命令清理到期 `raw_30d` 对象；删除后 PostgreSQL 永久保留哈希、大小、创建时间、删除时间、操作者和原因。

### 7.4 不可变和一致性

- 正式对象不覆盖；同一 `artifact_id` 二次写入必须失败。
- 写入完成后计算 SHA-256 和大小，再在 PostgreSQL 事务中登记可读记录。
- 读取时可按风险抽样或总是校验大小/校验和；具体成本策略待实测。
- MinIO 写入成功但数据库失败时产生孤儿对象；后台清理只删除超过安全时间且数据库无引用的临时/孤儿对象。
- PostgreSQL 记录存在但对象缺失时，API 返回显式制品错误，不能返回空内容冒充成功。

## 8. 索引和约束候选

- `evaluation_tasks(dataset_id, dataset_revision, split, instance_id)` 唯一。
- `agent_source_submissions(git_url, commit_sha)` 唯一候选；这是 P2 自研 Agent 能力，MVP 不建表。
- `agent_configurations(configuration_fingerprint)` 唯一。
- `evaluation_jobs(status, created_at)`：Worker 领取；活跃重型 Job 数必须受约束为 1。
- `evaluation_runs(job_id, task_id, agent_configuration_id, attempt_index)` 唯一。
- `evaluation_runs(agent_configuration_id, task_id, finished_at)`：与 Job 的赛道/策略联表生成报告和排行榜。
- `job_state_events(job_id, sequence)` 唯一。
- `run_state_events(run_id, sequence)` 唯一。
- `judge_analyses(run_id, judge_purpose, created_at)` 用于 Failure；Quality 使用 `(job_id, comparison_key, rubric_version, input_policy_version, created_at)` 查询。实现时再用真实重判版本语义固定唯一约束。
- `human_reviews(run_id, version)` 与 `human_reviews(job_id, version)` 分别覆盖运行级 Failure 和 Job 级 Quality 复核。
- `artifact_records(run_id, artifact_type, created_at)`、`artifact_records(job_id, artifact_type, created_at)`、`artifact_records(task_id, artifact_type, created_at)`；`object_key` 唯一，并为 `retention_class, expires_at, deleted_at` 建清理查询索引。

索引必须由真实查询和 `EXPLAIN` 验证；本文不要求把所有字段都建索引。

## 9. 数据写入顺序

数据集导入时，平台先把原始任务 JSON 写入内容寻址的临时对象、计算并核对 SHA-256，再在同一同步动作中写标准化 `evaluation_tasks` 字段和 `source_snapshot_ref`；任何一侧失败都不得发布半个任务版本。

### 9.1 远端提交与所有者决定

```mermaid
sequenceDiagram
    participant C as 远端协作者
    participant API as FastAPI/Application
    participant DB as PostgreSQL
    participant O as 评测机所有者
    participant W as 本机 Worker

    C->>API: 提交冻结的 Job 选择
    API->>DB: 事务创建 AWAITING_OWNER_APPROVAL Job + PENDING runs + 事件
    O->>API: 以可信会话批准或拒绝
    alt 批准
        API->>DB: 事务写 QUEUED + 所有者决定字段 + 事件
        W->>DB: 原子领取最早 QUEUED Job
    else 拒绝
        API->>DB: 事务写 REJECTED + CANCELED runs + 所有者决定字段 + 事件
    end
```

### 9.2 执行制品与结果

```mermaid
sequenceDiagram
    participant W as Worker/Job Orchestrator
    participant DB as PostgreSQL
    participant OBJ as MinIO

    W->>DB: 领取/推进 Job 与逐题运行状态
    W->>OBJ: 写临时对象并计算 SHA-256
    OBJ-->>W: 写入成功
    W->>DB: 登记 artifact_record
    W->>OBJ: 固定为正式不可变对象
    W->>DB: 在事务中写结果摘要并推进状态
```

精确的临时对象命名和“先登记还是先固定”要在 MinIO Adapter 实现时选择一种可补偿流程；无论选择哪种，报告只能引用同时存在于数据库和 MinIO 的已完成对象。

## 10. 数据验证

实现后至少验证：

1. 同一任务版本和 Agent 配置可重复定位，配置修改会产生新指纹/新记录。
2. 一个 Job 的 Agent×任务矩阵生成正确数量且无重复的运行；首版 `attempt_index=1`。
3. 两个 Worker 并发时，同一 Job 只有一个领取成功，而且全局最多一个重型 Job 活跃。
4. 非法 Job/运行状态迁移、错误 `row_version` 和错误 Worker 租约更新被拒绝。
5. `resolved=false`、运行 `FAILED`、Job `COMPLETED_WITH_ERRORS` 的查询/统计分开。
6. 不同 Agent 配置在排行榜中分开聚合；MVP 只接受 `closed_book`，预留的 `open_book_experimental` 不能创建 Job；P2 同一自研源码的 DeepSeek/Kimi 配置不得混分。
7. 制品覆盖被拒绝；对象键、大小和 SHA-256 可核对；Harbor 必需 patch 收集失败不能进入 Evaluator。
8. MinIO 或 PostgreSQL 任一侧故障不会让 API 返回一份假完整报告。
9. 普通 Task/Job/Run API 无法读取 gold patch、隐藏测试、秘密和未脱敏日志。
10. MVP 的 Agent Registry 只接受项目预登记 Agent；不存在公开的自研 Agent 提交入口。P2 启用自研 Agent 后，未审核源码提交仍不能创建 Agent 配置或 Job，审核事件必须可追溯。
11. Judge 和人工复核新增记录不修改确定性结果和旧版本证据；Failure 不进入排名；Quality 只命中严格确定性并列组，以匿名 A/B 和 B/A 各运行一次，两个方向一致才产生胜者，否则保持并列；多 Agent 用胜 1、平 0.5、负 0 的循环赛积分。
12. 创建 Job 后状态必为 `AWAITING_OWNER_APPROVAL`；提交者不能批准；所有者批准/拒绝并发时只有一个决定成功，决定者和时间可审计。
13. Worker 对 `AWAITING_OWNER_APPROVAL` 和 `REJECTED` 的 Job 永远领取不到；只有批准产生的 `QUEUED` Job 可以进入 `PREPARING`。
14. 两类角色权限可验证：协作者只能提交和读取非秘密结果；唯一评测所有者可审批、成员/配置管理、制品清理和人工复核；客户端提交的角色字段不能提权，且没有公开注册路径。
15. `CANCEL_REQUESTED` 不启动后续 Trial，当前 Trial 只运行到冻结超时；Worker/Harbor 中断不自动续跑或重试，新尝试使用新 Job 和新证据链。
16. patch 警告、1 MiB 拒绝、二进制拒绝、50 MiB 单原始制品和 200 MiB 每运行上限均有边界测试；patch 不会被截断。
17. 到期原始制品只有所有者本机维护命令可清理；对象删除后哈希、大小、创建与删除审计仍可查询。
18. P2 自研 Agent 的提交、Job、运行、制品和可查询配置均不含 DeepSeek/Kimi 真实 Key；被测容器的环境/文件扫描也不得发现提供方 Key。

## 11. 待技术核验

业务规则已经确认；以下只允许通过实现和测试补齐技术参数，不能借机改变规则：

1. PostgreSQL/MinIO 的具体版本与本机 Docker 磁盘余量。
2. 账户、密码哈希、邀请和会话的现有承载位置；若现有表/模块不能承载，先说明理由并取得确认后再新增。
3. Job 租约时长、心跳间隔和 `INFRASTRUCTURE_INTERRUPTED` 的精确收束 SQL；行为仍固定为不自动续跑或重试。
4. 256 KiB/1 MiB/50 MiB/200 MiB 阈值在真实 Harbor 制品上的边界测试，以及所有者本机清理命令的参数设计。
5. Quality Judge 使用的具体模型、Prompt 模板和结构化响应 Schema；触发条件、四项 rubric、反序一致性和积分规则已固定。
6. P2 自研 Agent 的受控模型访问实现，以及 DeepSeek/Kimi Key 不进入容器的证明方法；该项不阻塞 MVP。

## 12. 变更记录

- 2026-09-01：创建候选 v0.1；定义 8 张核心表、运行状态、PostgreSQL 队列领取、MinIO 对象键、不可变制品和验证规则。
- 2026-09-02：在运行记录中冻结评测赛道、网络策略和工具配置，支持闭卷主榜与开卷实验榜严格分组。
- 2026-09-03：新增 Agent 源码提交、平台评测 Job 和 Job 状态事件；PostgreSQL 只领取 Job，逐题运行映射 Harbor Trial，并新增 Harbor 制品和 `internal_test` 隔离规则。
- 2026-09-05：新增 `AWAITING_OWNER_APPROVAL` 与 `REJECTED`、所有者决定审计字段和事务；Worker 只领取经所有者批准后形成的 `QUEUED` Job。
- 2026-09-05：在现有 `judge_analyses` 中区分 Failure/Quality 用途和清洗策略版本，保持逐运行制品布局；Agent 配置增加非秘密模型提供方/凭据配置身份，并禁止自研 Agent 的 DeepSeek/Kimi Key 进入业务存储或被测容器。
- 2026-09-05：固定本机 Codex 技术原型→Codex 平台 MVP→Aider/Claude Code→P2 自研 Agent 的优先级；补充两类角色、任务原始快照、关闭开卷入口、取消/中断不自动重试、Quality 双向匿名比较、制品大小上限和 30 天原始证据清理规则。
