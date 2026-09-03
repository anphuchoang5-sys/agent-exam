# Harbor 执行后端接口

> 文档状态：架构已确认；固定提交接口已静态核验；本机运行待原型验收
>
> 最后更新：2026-09-03
>
> Harbor 固定版本：以 [`DEPENDENCIES.md`](../dependencies/DEPENDENCIES.md) 中的完整提交为唯一事实源
> 权威范围：本文件维护 AgentExam `ExecutionBackend` 与 Harbor 之间的输入、输出、字段映射、错误和验收门槛。Harbor 来源与恢复方式见 [`DEPENDENCIES.md`](../dependencies/DEPENDENCIES.md)。

## 1. 先用小白能懂的话解释

一次用户操作可能选择 3 个 Agent 和 5 道题。AgentExam 把这次操作叫一个**评测 Job**；它在 PostgreSQL 排队。轮到它后，Harbor 收到一份执行计划，并把组合展开成 15 次独立尝试。Harbor 把每次尝试叫 **Trial**，AgentExam 把同一事实叫一条**评测运行**。

```text
1 个 AgentExam 评测 Job
    → 1 个 Harbor Job
        → N 个 Harbor Trial
            ↔ N 条 AgentExam 评测运行
```

Harbor 负责“让 Agent 做题并留下过程证据”，固定 SWE-Bench-Fork 负责“在干净环境判卷”。Harbor 自带的 reward 不能替代本项目最终判卷。

## 2. 模块 seam

```mermaid
flowchart LR
    O[Job Orchestrator] -->|ExecutionJobRequest| P[ExecutionBackend interface]
    H[HarborExecutionAdapter] -. 实现 .-> P
    F[ProcessExecutionAdapter<br/>验收失败时的后备实现] -. 实现 .-> P
    H --> J[Harbor Job]
    J --> T[Harbor Trials<br/>n_concurrent_trials=1]
    T --> A[Agent + Docker Environment]
    T --> R[Trial result / trajectory / artifacts]
    H -->|ExecutionTrialResult[]| O
    O --> E[固定 SWE-Bench-Fork Evaluator]
```

这是一个深模块：调用方只学习一组项目对象，Harbor 的目录、Pydantic 类型、CLI 参数和异常都留在 Adapter 实现内部。

## 3. AgentExam 输入

`ExecutionJobRequest` 是概念接口，尚未表示已有 Python 类：

| 字段 | 含义 | 约束 |
|---|---|---|
| `job_id` | 平台评测 Job ID | 全链路追溯；不可复用 |
| `runs[]` | 待执行的逐题运行 | 每项固定 `run_id`、一个任务、一个 Agent 配置和 `attempt_index=1` |
| `evaluation_policy` | 闭卷/开卷、网络和工具策略 | Job 内首版使用同一赛道；每条运行保存快照 |
| `limit_profile` | CPU、内存、超时、PID、输出限制模板 | 只能来自管理员登记模板，不能接受用户任意 Docker 参数 |
| `backend_revision` | Harbor 固定提交 | 必须等于依赖事实源中已允许版本 |
| `artifact_contract_version` | 必需制品约定版本 | 不支持时在启动前失败 |

每个 `runs[]` 项只包含 Agent 可见任务视图；gold patch、`test_patch`、`FAIL_TO_PASS`、`PASS_TO_PASS` 和其他运行答案不得进入 Harbor Agent instruction。

## 4. Harbor `JobConfig` 映射

以下字段来自固定提交真实源码，不是根据记忆创造：

| Harbor 字段 | AgentExam 映射 | 首版规则 |
|---|---|---|
| `job_name` | 安全化的 `job_id` | 不含用户名、秘密或仓库路径 |
| `jobs_dir` | 后端受控临时目录 | 不由 HTTP 用户传入 |
| `agents` | Job 选中的已登记 Agent 配置 | 只从 Agent Registry 转换 |
| `tasks` | SWE-Gym Adapter 产生的受控 Harbor Task | 精确本地路径/身份由 Task Adapter 生成 |
| `datasets` | 暂不作为首版主要输入 | 首版先显式列出少量固定 tasks，避免隐式扩大数据集 |
| `n_attempts` | 每个 Agent×任务的尝试数 | 首版固定 `1` |
| `n_concurrent_trials` | Harbor 同时执行的 Trial 数 | 单机硬性固定 `1` |
| `environment.type` | 环境提供者 | 首版固定 Docker |
| `environment.delete` | 完成后清理环境 | 默认 `true`；清理失败必须留证 |
| `environment.*_enforcement_policy` | CPU/内存执行策略 | 具体策略须通过本机原型，不沿用未验证默认值 |
| `environment.override_*` | 已登记资源模板覆盖值 | 只能由平台生成，不能由普通用户提交 |
| `verifier.disable` | 是否运行 Harbor Verifier | 固定 `true`；最终交给 SWE-Bench-Fork |
| `artifacts` | 需从 Trial 环境收集的文件 | 至少覆盖补丁、轨迹及必要日志；必需制品缺失视为执行失败 |
| `retry.max_retries` | Harbor 内部重试 | 首版固定 `0`，重跑由平台创建新运行，避免覆盖证据 |

固定提交的 `JobPlan.build_trial_configs()` 已核验为按：

```text
n_attempts × task_configs × agents
```

展开 Trial。首版 `n_attempts=1`，所以每个任务与 Agent 配置组合恰好对应一条评测运行。

## 5. Agent 和 Task 映射

### 5.1 `AgentConfig`

Harbor 固定提交已核验字段包括 `name`、`import_path`、`model_name`、`n_concurrent`、`concurrency_group`、`skills`、`kwargs`、`env` 和 `extra_allowed_hosts`。

映射纪律：

- 内置 Codex/Claude Code/Aider 优先复用 Harbor 已有 Agent 名称与实现，不再为同一能力另写一套 Adapter。
- 自研 Agent 通过经管理员审核的项目适配方式转换为 Harbor `name` 或 `import_path`；普通用户不能直接提交 Python import path、shell 命令或环境变量。
- 模型密钥由秘密引用在运行时注入；不得进入 Job JSON、数据库公开快照、命令行或制品。
- `n_concurrent` 不得超过 Job 的 `n_concurrent_trials=1`。

### 5.2 `TaskConfig`

Harbor 固定提交支持本地 `path`、Git 任务 `git_url + git_commit_id + path`，或包任务 `name + ref`。AgentExam 首版使用 SWE-Gym Adapter 生成的少量、固定、本地 Harbor Task，并把数据集 revision、split 和 `instance_id` 继续保存在自身任务快照中。

该映射不允许把用户提交的任意任务 Git URL 直接交给 Harbor，也不允许用 `latest` 代替固定 revision。

## 6. Harbor 输出与 AgentExam 输出

### 6.1 已核验的 Harbor 输出

固定提交的 `JobResult` 包含 Job ID、起止时间、总 Trial 数、聚合统计和 `trial_results`。`TrialResult` 已核验包含：

- `id`、`task_name`、`trial_name`、`trial_uri`、`task_id`、`task_checksum`；
- 解析后的 `config` 与 `agent_info`；
- 可选 `agent_result`、`verifier_result`、`exception_info`；
- 环境准备、Agent 安装/执行和 Verifier 的时间数据。

Harbor Job 目录会保存 Job/Trial 的 `config.json`、`result.json`、Agent 日志、`trajectory.json` 和收集的 artifacts。固定 `SingleStepTrial` 执行顺序已核验为：运行 Agent → 同步日志 → 收集 artifacts → 运行 Verifier；`verifier.disable=true` 时跳过 Verifier，但 artifact 收集仍在其之前执行。

### 6.2 Adapter 必须返回的项目结果

每个 Trial 必须转换为一条 `ExecutionTrialResult`：

| 字段 | 含义 |
|---|---|
| `run_id` | 对应 AgentExam 评测运行 |
| `backend_job_ref` / `backend_trial_ref` | Harbor Job/Trial 可追溯身份 |
| `termination_reason` | 规范化的完成、超时、认证、资源、Agent、制品或内部错误 |
| `patch_ref` | 必需的 Git unified diff 制品；可为空补丁，但引用和 SHA-256 必须存在 |
| `trajectory_ref` | 可用时的 ATIF/规范化轨迹制品；缺失必须带能力/错误说明 |
| `raw_config_ref` / `raw_result_ref` | 脱敏后的 Harbor 原始配置与结果制品 |
| `usage` | Harbor/Agent 实际报告的 token、成本和时间；不支持的字段为未知，不写 0 |
| `warnings` | artifact best-effort 失败、轨迹能力差异等可审计警告 |

`ExecutionBackend` 不返回 `resolved`。补丁正确与否只由后续 `PatchEvaluator` 返回。

## 7. `model_patch` 缺口

Harbor 固定提交的 `TrialResult` 没有标准 `model_patch` 字段。Harbor 的 artifact 收集还是 best-effort：收集失败会进入 manifest，但不会自动让 Trial 失败。因此 AgentExam 必须额外执行以下强约束：

1. 在 Harbor 清理 Agent 环境前，由受控机制从固定 `base_commit` 的工作区提取 Git diff。
2. 把 diff 写入约定 artifact，并记录字节数与 SHA-256。
3. Harbor Adapter 读取后重新校验；制品缺失、越界或哈希不一致时返回 `patch_extraction_failed`。
4. 空补丁是合法执行结果，但也必须有一个 0 字节 patch 制品和对应哈希。
5. 同一字节内容保存到 MinIO，并作为 SWE-Bench-Fork prediction 的 `model_patch`。

“受控机制”究竟采用 Harbor Agent 包装、任务收尾脚本还是固定提交已支持的其他 extension point，尚未实测，不能在原型前写死。能否稳定完成这一步是采用 Harbor 的第一验收门槛。

## 8. 运行身份映射

Adapter 必须保存不可变映射：

```text
job_id ↔ Harbor job id/path
run_id ↔ task_id + agent_configuration_id + attempt_index ↔ Harbor trial id/name
```

首版尝试数固定为 1，因此 `(job_id, task_id, agent_configuration_id)` 唯一。Harbor 生成的 `trial_name` 不能替代平台 `run_id`；如果映射无法确定，禁止把 Trial 结果猜配给某条运行。

## 9. 状态与错误映射

| Harbor/Adapter 现象 | 平台运行结果 | 是否进入 SWE-Bench-Fork |
|---|---|---:|
| Agent 完成且 patch 制品校验通过 | `completed` 执行结果 | ✅ |
| Agent 完成且 patch 为 0 字节 | `completed` 执行结果 | ✅，由 Fork 记录未解决/空补丁 |
| `exception_info` 为 Agent/认证/超时错误 | 对应规范化失败 | ❌ |
| 环境创建、资源或网络策略失败 | `sandbox_failed` / `policy_failed` | ❌ |
| artifact manifest 报告必需 patch 失败 | `patch_extraction_failed` | ❌ |
| Trial 身份无法映射到 `run_id` | `backend_protocol_error` | ❌ |
| Harbor Job 进程异常退出 | 未完成运行标记明确失败；保留已完成 Trial | 仅已取得可信 patch 的运行继续 |
| Harbor reward/Verifier 输出 | 仅保存为调试证据或完全禁用 | ❌，不能作为最终事实 |

平台 Job 可以“部分完成”：已经形成可信逐题结果的运行保留，其余运行明确失败；不得为了让 Job 看起来整齐而丢弃已完成证据或伪造结果。

## 10. Agent 源码提交入口

可信参与者可以提交：

- Git 仓库 URL；
- 完整 commit SHA；
- 仓库根目录中的 `agent-exam.yaml`；
- 面向审核者的名称与说明。

提交只创建 `PENDING_REVIEW` 记录，不会触发 Harbor、Docker build 或任意仓库代码执行。管理员审核来源、commit、manifest、依赖与权限后，才生成已登记 Agent 配置。分支名、`latest`、请求正文中的 shell 命令和未经审核的 `import_path` 均不能进入执行链路。

`agent-exam.yaml` 的字段 schema 仍需单独确认；本次只确认“必须存在、固定在同一 commit、由平台解析并经管理员审核”，不臆造尚未讨论的启动字段。

## 11. Mock 与正式结果

- Mock Adapter 只用于应用用例、错误分支、状态机和 HTTP contract 测试。
- Mock 产生的 Job/运行必须带 `result_scope=internal_test`，并使用独立测试数据库或明确测试标记。
- 报告、演示、正式榜和实验榜查询必须排除 `internal_test`。
- 正式结果必须来自真实 Agent + 真实 Harbor/Docker 执行 + 固定 SWE-Bench-Fork；不能用预制 patch 冒充 Agent 输出。

## 12. 单机资源规则

- PostgreSQL 同时只允许一个平台重型 Job 处于执行状态。
- Harbor `n_concurrent_trials` 固定为 `1`；不得因为 Job 中任务多就自动提高。
- 具体 Trial 内存、CPU、磁盘和超时模板必须根据真实单题峰值确定。本机事实只在 [`LOCAL_DOCKER_ENVIRONMENT.md`](../operations/LOCAL_DOCKER_ENVIRONMENT.md) 维护。
- Web 创建 Job 时必须显示组合产生的 Trial 数；耗时只能基于真实历史数据估算，没有历史数据时显示“未知”，不能承诺完成时间。

## 13. 首个原型验收

固定一个小型 SWE-Gym 任务和一个真实可用 Agent，验证：

1. Harbor 固定提交可在本机安装并创建 Docker Trial。
2. `n_concurrent_trials=1` 与资源/网络策略实际生效。
3. Agent 看不到 gold patch 和判分字段。
4. 自动取得 patch（含新建/修改/删除文件和空补丁）并校验 SHA-256。
5. ATIF/原始轨迹、Harbor config/result、stdout/stderr 可追溯到同一 `run_id`。
6. `verifier.disable=true` 时 Harbor 不产生最终判卷，但 artifacts 仍可取得。
7. 同一 patch 交给固定 SWE-Bench-Fork 后得到可信 `resolved` 和原始测试证据。
8. 超时、认证失败、patch 缺失和清理失败均映射为明确平台错误。

任何一项失败都必须先诊断；如果补丁出口、资源治理或轨迹在限定验证周期内无法稳定满足，则按 ADR 回退到 `ProcessExecutionAdapter`。

## 14. 固定提交来源

- [`JobConfig`](https://github.com/harbor-framework/harbor/blob/6af8d6e31eced13b93849cdf80feeadf24603d15/src/harbor/models/job/config.py)
- [`JobPlan` Trial 展开](https://github.com/harbor-framework/harbor/blob/6af8d6e31eced13b93849cdf80feeadf24603d15/src/harbor/job_plan.py)
- [`TrialConfig`](https://github.com/harbor-framework/harbor/blob/6af8d6e31eced13b93849cdf80feeadf24603d15/src/harbor/models/trial/config.py)
- [`TrialResult`](https://github.com/harbor-framework/harbor/blob/6af8d6e31eced13b93849cdf80feeadf24603d15/src/harbor/models/trial/result.py)
- [`SingleStepTrial`](https://github.com/harbor-framework/harbor/blob/6af8d6e31eced13b93849cdf80feeadf24603d15/src/harbor/trial/single_step.py)
- [Artifact collection](https://github.com/harbor-framework/harbor/blob/6af8d6e31eced13b93849cdf80feeadf24603d15/docs/content/docs/run-jobs/results-and-artifacts.mdx)
- [Resource management](https://github.com/harbor-framework/harbor/blob/6af8d6e31eced13b93849cdf80feeadf24603d15/docs/content/docs/tasks/managing-resources.mdx)

## 15. 变更记录

- 2026-09-03：创建；记录已确认的 Harbor 执行 seam、真实 Job/Trial 字段、固定单机并发、补丁出口缺口、Mock 隔离和原型退出条件。
