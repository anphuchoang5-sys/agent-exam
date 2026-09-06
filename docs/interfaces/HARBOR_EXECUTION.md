# Harbor 执行后端接口

> 文档状态：架构已确认；固定提交接口、M0 配置/Task 契约、NOP Docker Trial/结果映射、四类非空 patch、有界日志和宿主进程树清理已核验；真实 Codex Trial 与 Harbor 超时后的 Compose 清理待验收
>
> 最后更新：2026-09-06
>
> Harbor 固定版本：以 [`DEPENDENCIES.md`](../dependencies/DEPENDENCIES.md) 中的完整提交为唯一事实源
> 权威范围：本文件维护 AgentExam `ExecutionBackend` 与 Harbor 之间的输入、输出、字段映射、错误和验收门槛。Harbor 来源与恢复方式见 [`DEPENDENCIES.md`](../dependencies/DEPENDENCIES.md)；Codex 与自研 Agent 的凭据所有权和秘密边界只在 [`CODEX_AUTHENTICATION.md`](./CODEX_AUTHENTICATION.md) 维护。

## 1. 先用小白能懂的话解释

一次用户操作可能选择 3 个 Agent 和 5 道题。AgentExam 把这次操作叫一个**评测 Job**；它在 PostgreSQL 排队。轮到它后，Harbor 收到一份执行计划，并把组合展开成 15 次独立尝试。Harbor 把每次尝试叫 **Trial**，AgentExam 把同一事实叫一条**评测运行**。

```text
1 个 AgentExam 评测 Job
    → 1 个 Harbor Job
        → N 个 Harbor Trial
            ↔ N 条 AgentExam 评测运行
```

Harbor 负责“让 Agent 做题并留下过程证据”，固定 SWE-Bench-Fork 负责“在干净环境判卷”。Harbor 自带的 reward 不能替代本项目最终判卷。

实现顺序固定为：先用本机脚本跑通一个 Codex 的真实 Harbor→patch→SWE-Bench-Fork 技术闭环；再接入 Web、PostgreSQL、所有者批准和正式报告，形成 Codex-only MVP；随后登记 Harbor 已有的 Aider、Claude Code；P2 最后才接自研 Agent。脚本原型不创建正式 Job、不进入排行榜，也不要求先实现 Web/数据库。

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

`ExecutionJobRequest` 已在 M0 后端实现为项目 Python 类型；下表仍是其权威语义：

| 字段 | 含义 | 约束 |
|---|---|---|
| `job_id` | 平台评测 Job ID | 全链路追溯；不可复用 |
| `runs[]` | 待执行的逐题运行 | 每项固定 `run_id`、一个任务、一个 Agent 配置和 `attempt_index=1` |
| `evaluation_policy` | 赛道、网络和工具策略 | MVP 固定 `closed_book`；`open_book_experimental` 只保留接缝且禁用；每条运行保存快照 |
| `limit_profile` | CPU、内存、超时、PID、输出限制模板 | 只能来自所有者登记模板，不能接受用户任意 Docker 参数 |
| `backend_revision` | Harbor 固定提交 | 必须等于依赖事实源中已允许版本 |
| `artifact_contract_version` | 必需制品约定版本 | 不支持时在启动前失败 |

公开 Job 请求、`ExecutionJobRequest` 和 PostgreSQL 只保存非秘密的模型提供方、认证类型与 Agent Configuration 身份；它们不接收 `auth.json`、DeepSeek/Kimi Key 内容，也不保存真实宿主路径。

`CODEX_AUTH_JSON_PATH` 只存在于执行节点本机、未跟踪的秘密配置中。执行节点在启动受控 Codex Trial 时解析它，路径和值都不进入上表的业务请求。

P2 自研 Agent 的 DeepSeek/Kimi 真实 Key 同样只存在于评测机所有者控制的本机可信秘密配置中，但与 Codex 不同：Key 不直接交给被测 Agent 容器。Agent 只能使用运行时受限、可撤销的模型访问能力；该能力由现有 Execution Backend/LLM Provider Implementation 提供，具体采用宿主进程还是可信侧车以及 Docker 网络怎样防绕过留到 P2 原型裁决，不阻塞 MVP。

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

- 内置 Agent 依次接入：Codex MVP 完成后再接 Harbor 已有的 Aider、Claude Code；不为同一能力另写一套 Adapter。
- P2 自研 Agent 只支持 Python，并实现 [`RUNNER_PROTOCOL.md`](./RUNNER_PROTOCOL.md) 的固定进程 Interface；平台拥有的包装实现把审核后的模块映射为 Harbor Agent，普通用户不能直接提交 Harbor `import_path`、shell 命令或环境变量。完整 manifest 字段、Python 版本、依赖锁格式和包装 extension point 留待 P2 确认/实测。
- 公开 Job、数据库和对外接口只记录非秘密的认证类型，不接收凭据文件、内容或真实路径。
- 对首个 Codex 原型，执行节点从本机 `CODEX_AUTH_JSON_PATH` 解析机器所有者的凭据，只在受控 Trial 的最小生命周期内交给 Harbor Codex Agent；具体 Token 刷新与清理仍待实测。
- P2 自研 Agent 只允许登记 `deepseek` 或 `kimi` 提供方；同一源码切换提供方必须生成独立 Agent Configuration。真实提供方 Key 只由执行节点可信实现读取，不直接注入被测 Agent 容器；提交者只能选择已登记配置，不能提供 Key、Base URL 或代理。
- `n_concurrent` 不得超过 Job 的 `n_concurrent_trials=1`。

### 5.2 `TaskConfig`

Harbor 固定提交支持本地 `path`、Git 任务 `git_url + git_commit_id + path`，或包任务 `name + ref`。AgentExam 首版使用 SWE-Gym Adapter 生成的少量、固定、本地 Harbor Task，并把数据集 revision、split 和 `instance_id` 继续保存在自身任务快照中。

该映射不允许把用户提交的任意任务 Git URL 直接交给 Harbor，也不允许用 `latest` 代替固定 revision。

## 6. Harbor 输出与 AgentExam 输出

### 6.1 已核验的 Harbor 输出

固定提交的内存 `JobResult` 包含 Job ID、起止时间、总 Trial 数、聚合统计和 `trial_results`；真实 NOP 运行确认 Job 根目录落盘的 `result.json` 会排除 `trial_results`，每条完整结果只落在对应 Trial 子目录的 `result.json`。Adapter 因此必须枚举子目录并严格绑定身份，不能从 Job 根结果猜配。`TrialResult` 已核验包含：

- `id`、`task_name`、`trial_name`、`trial_uri`、`task_id`、`task_checksum`；
- 解析后的 `config` 与 `agent_info`；
- 可选 `agent_result`、`verifier_result`、`exception_info`；
- 环境准备、Agent 安装/执行和 Verifier 的时间数据。

Harbor Job 目录会保存 Job/Trial 的 `config.json`、`result.json`、Agent 日志、可用时的 `trajectory.json` 和收集的 artifacts。固定 `SingleStepTrial` 及真实 NOP 已确认顺序为：运行 Agent → 同步日志 → 执行任务 `verifier.collect` hook → 收集 artifacts → 可选运行 Verifier；`verifier.disable=true` 时仍执行前两类收集。

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

脱敏后的原始配置、结果、日志、轨迹和制品也必须明确排除 `auth.json`、`$CODEX_HOME`、Harbor secrets 目录、Token 和真实宿主凭据路径；MinIO 不得接收这些内容。

`ExecutionBackend` 不返回 `resolved`。补丁正确与否只由后续 `PatchEvaluator` 返回。

## 7. `model_patch` 缺口

Harbor 固定提交的 `TrialResult` 没有标准 `model_patch` 字段。Harbor 的 artifact 收集还是 best-effort：收集失败会进入 manifest，但不会自动让 Trial 失败。因此 AgentExam 必须额外执行以下强约束：

1. 在 Harbor 清理 Agent 环境前，由受控机制从固定 `base_commit` 的工作区提取 Git diff。
2. 把 diff 写入约定 artifact，并记录字节数与 SHA-256。
3. Harbor Adapter 读取后重新校验；制品缺失或哈希不一致时返回 `patch_extraction_failed`。超过 256 KiB 写警告；超过 1 MiB 返回 `PATCH_TOO_LARGE` 并拒绝进入 Harness，绝不截断。
4. 空补丁是合法执行结果，但也必须有一个 0 字节 patch 制品和对应哈希。
5. 二进制 patch 返回 `BINARY_PATCH_NOT_ALLOWED`，不进入 Harness；MVP 只接受文本统一 diff。
6. 同一字节内容保存到 MinIO，并作为 SWE-Bench-Fork prediction 的 `model_patch`。

M0 已选择固定 Harbor 支持的任务级 `verifier.collect` hook：在容器销毁前相对任务 `base_commit` 生成 `model.patch`、SHA-256、字节数和二进制标志，再把整个 `/logs/artifacts` 目录收集到宿主 `artifacts/agentexam`。真实 NOP 已验证空 patch 与元数据、Verifier 关闭、UTF-8 CLI 退出和 Compose 资源清理；固定摘要、禁网容器测试又验证了跟踪文件修改、新文件、删除和 Agent 自行 commit 四种非空结果都能相对固定 `base_commit` 生成完整 patch，并通过宿主强校验。真实 Codex 仍须继续实测。

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
| 文本 patch 超过 1 MiB | `PATCH_TOO_LARGE` 无效 Agent 输出 | ❌ |
| 二进制 patch | `BINARY_PATCH_NOT_ALLOWED` 无效 Agent 输出 | ❌ |
| Trial 身份无法映射到 `run_id` | `backend_protocol_error` | ❌ |
| Harbor Job 进程异常退出 | 未完成运行标记明确失败；保留已完成 Trial | 仅已取得可信 patch 的运行继续 |
| Harbor reward/Verifier 输出 | 仅保存为调试证据或完全禁用 | ❌，不能作为最终事实 |

平台 Job 可以“部分完成”：已经形成可信逐题结果的运行保留，其余运行明确失败；不得为了让 Job 看起来整齐而丢弃已完成证据或伪造结果。

执行中收到取消请求时，Adapter 不再启动新的 Trial；当前 Trial 不强杀，只运行到 Job 创建时冻结的超时并保存真实结果。宿主机、Worker 或 Harbor 中断不能触发自动续跑或自动重试；可证明已经完成的 Trial 只做幂等收束，否则记录 `INFRASTRUCTURE_INTERRUPTED`，新尝试必须由所有者创建新 Job。

## 10. P2 Agent 源码提交入口（MVP 禁用）

本节只保存未来扩展接缝。MVP 的 Web、HTTP API 和 Agent Registry 不公开源码提交入口，只能选择项目预登记 Agent。

可信参与者可以提交：

- Git 仓库 URL；
- 完整 commit SHA；
- 仓库根目录中的 `agent-exam.yaml`；
- 面向审核者的名称与说明。

P2 提交只创建 `PENDING_REVIEW` 记录，不会触发 Harbor、Docker build 或任意仓库代码执行。所有者审核来源、commit、manifest、依赖与权限后，才生成已登记 Agent 配置。分支名、`latest`、请求正文中的 shell 命令和未经审核的 `import_path` 均不能进入执行链路。

已确认 `agent-exam.yaml` 的 P2 首版只描述 Python 固定进程 Interface，并且必须存在、固定在同一 commit、由平台静态解析并经所有者审核。它不能携带 shell、API Key、自定义提供方/Base URL、代理、宿主路径或 Harbor 原生配置。完整字段、Python 版本和依赖锁格式留到 P2，不臆造尚未讨论的启动字段。

## 11. Mock 与正式结果

- Mock Adapter 只用于应用用例、错误分支、状态机和 HTTP contract 测试。
- Mock 产生的 Job/运行必须带 `result_scope=internal_test`，并使用独立测试数据库或明确测试标记。
- 报告、演示、正式榜和实验榜查询必须排除 `internal_test`。
- 正式结果必须来自真实 Agent + 真实 Harbor/Docker 执行 + 固定 SWE-Bench-Fork；不能用预制 patch 冒充 Agent 输出。

## 12. 单机资源规则

- PostgreSQL 同时只允许一个平台重型 Job 处于执行状态。
- Harbor `n_concurrent_trials` 固定为 `1`；不得因为 Job 中任务多就自动提高。
- 具体 Trial 内存、CPU、磁盘和超时模板必须根据真实单题峰值确定。本机事实只在 [`LOCAL_DOCKER_ENVIRONMENT.md`](../operations/LOCAL_DOCKER_ENVIRONMENT.md) 维护。
- 单个轨迹、stdout、stderr 或 Judge 原始制品最多 50 MiB，超过只能显式标记截断；每运行原始制品总额最多 200 MiB。核心配置、确定性结果、最终 patch 和测试摘要优先完整保存，不能用静默丢失伪装证据完整。
- Web 创建 Job 时必须显示组合产生的 Trial 数；耗时只能基于真实历史数据估算，没有历史数据时显示“未知”，不能承诺完成时间。

## 13. 分阶段验收

### 13.1 M0：本机 Codex 技术原型

从固定 revision 的 `SWE-Gym/SWE-Gym-Lite` 先选择 1 道真实任务，必要时扩至 3 道，并使用 Harbor 内置 Codex Agent 验证。认证政策已确认为评测机所有者的 ChatGPT Pro `auth.json`；Codex CLI 项目固定版本、模型 ID、端点白名单、Token 刷新、脱敏和清理仍须在运行前固定或实测，当前不能写成容器内已可用。

M0 用本机脚本编排，不实现 Web、PostgreSQL、MinIO、登录或审批；证据写入受控本机临时目录，标为技术原型，不进入正式排行。验收项：

1. Harbor 固定提交可在本机安装并创建 Docker Trial。
2. `n_concurrent_trials=1` 与资源/网络策略实际生效。
3. Agent 看不到 gold patch 和判分字段。
4. 自动取得 patch（含新建/修改/删除文件和空补丁）、校验 SHA-256，并验证 256 KiB 警告、1 MiB/二进制拒绝且不截断。
5. ATIF/原始轨迹、Harbor config/result、stdout/stderr 可追溯到同一次原型运行；日志限额有显式标记。
6. `verifier.disable=true` 时 Harbor 不产生最终判卷，但 artifacts 仍可取得。
7. 同一 patch 交给固定 SWE-Bench-Fork 后得到可信 `resolved` 和原始测试证据。
8. 超时、认证失败、patch 缺失和清理失败均映射为明确错误；脚本失败不伪装成正式结果。
9. Trial 前后人工检查容器、可写层、日志、轨迹和本机证据目录；成功、失败、超时三条路径均不得遗留凭据内容、真实秘密路径或可复用 Token。

任何一项失败都必须先诊断；如果补丁出口、资源治理或轨迹在限定验证周期内无法稳定满足，则按 ADR 回退到 `ProcessExecutionAdapter`。

当前实施状态（2026-09-06）：固定公开 Task 渲染、隐藏字段隔离、Harbor 配置/运行身份映射、collect hook、宿主 patch 强校验、Trial 结果映射和薄 `HarborExecutionAdapter` 已实现。stdout/stderr 由生产有界执行器同时排空，每路最多持久化 50 MiB，超限与进程树清理失败都写入 manifest 并传播为运行告警。unit/contract 共 42 项通过；生产有界执行器接真实 Harbor CLI 和正式 mapper 的 NOP 路径也通过，证明无模型路径、空 patch、关闭 Verifier 后的 artifact、UTF-8 CLI 和正常 Compose 清理。固定摘要、禁网容器中的修改/新建/删除/Agent commit 四类非空 patch 集成测试为 `4 passed in 5.91s`，测试专用容器无残留。公开 `HarborExecutionAdapter.execute()` 的编排仍由受控替身单测覆盖；真实父子进程超时探针只证明宿主进程树终止，不证明外层杀死 Harbor 后 Compose 子资源必然清理。真实 Codex、网络/凭据/轨迹、Harbor 超时后的 Compose 清理和固定 Fork 仍未完成，不能据此把 M0 标记完成。

### 13.2 M1：Codex 平台 MVP

M0 通过后才接 Web、PostgreSQL 和 MinIO，并验证协作者提交 → 所有者批准 → 本机 Worker → Harbor → patch → SWE-Bench-Fork → 报告的完整真实闭环。还必须覆盖两类角色、无公开注册、任务原始快照、取消/中断不自动重试、制品保留/清理审计和确定性结果报告。只有 M1 通过才称为 MVP 完成。

### 13.3 后续 Agent

M1 通过后，先使用相同契约登记并验证 Harbor 已有的 Aider、Claude Code。P2 自研 Agent 再追加验证：固定 Python 进程 Interface 能由平台包装为 Harbor Agent；DeepSeek 与 Kimi 分别形成独立配置；被测容器、环境快照、日志、轨迹和制品均不出现真实提供方 Key；受控模型访问失败只影响该运行并留下明确错误。P2 未完成不阻塞 MVP，也不得提前把自研 Agent 写成已支持。

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
- 2026-09-04：确认首个原型数据集为 `SWE-Gym/SWE-Gym-Lite`，范围为 1～3 道真实任务；revision、split 和具体实例保持待核验。
- 2026-09-04：确认首个真实原型 Agent 为 Codex；认证采用评测机所有者的 ChatGPT Pro `auth.json`，个人凭据不得进入公共输入、数据库或制品。
- 2026-09-04：Codex CLI 项目版本、模型、端点、Token 刷新、脱敏、清理和 Harbor 容器运行仍待固定或实测。
- 2026-09-05：确认首版自研 Agent 为 Python 固定进程 Interface，由平台包装进 Harbor；只允许 DeepSeek/Kimi 独立配置，真实 Key 不直接进入被测容器，具体受控访问部署与网络隔离仍待原型。
- 2026-09-05：固定 M0 本机 Codex 脚本原型、M1 Codex 平台 MVP、Aider/Claude Code、P2 自研 Agent 的顺序；补充闭卷限制、取消/中断不自动重试和 patch/原始制品限额。
- 2026-09-06：真实 Harbor NOP Docker Trial 与项目结果映射通过；薄进程 Adapter、有界双流日志和宿主进程树超时终止完成测试；记录落盘 Job 结果不含 `trial_results`、Windows CLI UTF-8 要求、任务 collect hook/单目录 artifact 契约，以及仍未通过的真实 Codex、Harbor 超时后 Compose 清理和固定 Fork 门槛。
