# 模块职责与输入输出契约

> 文档状态：架构边界已确认；字段契约 v0.2，尚未实现
>
> 最后更新：2026-09-03
> 权威范围：本文件只维护项目内部模块的职责、输入、输出、错误、不变量和依赖。全局组成见 [`ARCHITECTURE.md`](./ARCHITECTURE.md)，字段级边界见 [`RUNNER_PROTOCOL.md`](../interfaces/RUNNER_PROTOCOL.md)、[`HTTP_API.md`](../interfaces/HTTP_API.md) 和 [`DATA_MODEL.md`](./DATA_MODEL.md)。

## 1. 先用小白能懂的话解释

一个“模块”可以理解成一个只开一个窗口的部门。调用者只需要知道：

1. 应该交给窗口什么材料（输入）；
2. 窗口会交回什么结果（输出）；
3. 哪些情况算业务上没成功，哪些情况是系统坏了（错误）；
4. 窗口永远不能破坏什么规则（不变量）。

例如 Execution Backend 只负责“让一批 Agent 工作并按逐题运行拿回补丁和证据”，不负责判断补丁对不对；Patch Evaluator 只负责“用测试判补丁”，不负责评价 Agent 是否积极。这样 Harbor Job/Trial 的复杂性不会污染业务模块。

## 2. 状态和命名规则

- **已确认**：用户已经决定的项目规则。
- **已核验**：从上游源码或官方文档查到的事实。
- **候选 v0.1**：本项目拟采用、等待继续讨论的内部契约。
- **待确认/待实测**：需要业务决定或真实运行证据。
- 本文中的类型名是为了讨论边界的概念名，不等于已经存在的 Python 类。
- 领域词义以 [`CONTEXT.md`](../../CONTEXT.md) 为唯一事实源，本文不重新定义同义词。

## 3. 模块依赖方向

```mermaid
flowchart LR
    WEB[Next.js Web] --> HTTP[HTTP Delivery]
    HTTP --> APP[Application Use Cases]
    WORKER[Worker Shell] --> APP
    APP --> DOMAIN[Domain Rules]
    APP --> PORTS[Ports / 内部接口]
    ADAPTERS[External Adapters] -. 实现 .-> PORTS
    ADAPTERS --> EXT[SWE-Gym / Harbor / SWE-Bench-Fork / Docker / PostgreSQL / MinIO / LLM]

    DOMAIN -. 不允许依赖 .-> EXT
```

硬规则：

- `domain` 不依赖 FastAPI、PostgreSQL、Docker、MinIO、SWE-Gym 或任何 Agent CLI。
- `application` 只依赖领域对象和小型 ports，不直接拼 CLI 命令或 SQL。
- `adapters` 可以依赖外部工具，但外部类型不能向内泄漏到所有模块。
- Web 不直接操作 Docker、数据库或 MinIO；Worker 不绕过状态机直接改运行状态。
- 模块之间不得循环依赖。

## 4. 公共输入输出对象

下表是模块之间传递的最小概念对象。字段的存储映射见 [`DATA_MODEL.md`](./DATA_MODEL.md)。

| 对象 | 必需内容 | 明确不包含 | 主要生产者 → 消费者 |
|---|---|---|---|
| `EvaluationTask` | `instance_id`、数据集身份/版本、`repo`、`base_commit`、`problem_statement`、验证引用 | 不向 Agent 暴露 gold `patch`、`test_patch`、隐藏测试答案 | Task Catalog → Job Submission、Job Orchestrator、Patch Evaluator |
| `AgentConfiguration` | 登记 ID、Agent 类型/版本、模型、关键配置、Adapter 类型、配置指纹 | 明文 API key、临时登录 token | Agent Registry → Job Submission、Job Orchestrator、Execution Backend |
| `EvaluationJobSpec` | `job_id`、选中的任务/Agent 配置、赛道、限制模板、预计运行数、结果范围 | Harbor `JobConfig`、用户任意命令/路径 | Job Submission → Job Repository、Job Orchestrator |
| `EvaluationPolicy` | `evaluation_track`（`closed_book`/`open_book_experimental`）、已登记网络策略、已登记工具配置及其版本 | 按模型国别猜测的能力、用户任意代理/网址配置 | Job Submission → Job Orchestrator、Execution Backend、Reporting |
| `RunLimits` | 墙钟超时、CPU、内存、PID、输出大小、Agent 特有限制 | 用户可随意提交的宿主机权限 | Job Submission → Job Orchestrator、Execution Backend |
| `ExecutionJobRequest` | Job 身份、逐题 `run_id` 映射、任务、Agent 配置、策略、限制、后端版本 | 判分答案、gold patch、Harbor 外的任意执行命令 | Job Orchestrator → Execution Backend |
| `ExecutionTrialResult` | `run_id`、后端 Job/Trial 引用、终止原因、补丁/轨迹/原始结果引用、资源汇总 | `resolved` 或“补丁是否修好”的结论 | Execution Backend → Job Orchestrator |
| `EvaluationRequest` | `run_id`、`instance_id`、`model_patch`、可追溯的 Agent 身份 | Agent 的自然语言自评 | Job Orchestrator → Patch Evaluator |
| `DeterministicResult` | `resolved`、补丁应用情况、测试分类、Harness 报告/日志引用、基础设施错误 | LLM 主观评分 | Patch Evaluator → Job Orchestrator、Reporting、Judge |
| `TraceEvent` | 时间、序号、事件类型、来源、公开载荷、原始事件引用 | 思维链、秘密、未脱敏环境变量 | Adapter/Recorder → Artifact Store、Reporting |
| `JudgeRequest` | 已裁剪的任务、补丁、确定性结果、允许的轨迹摘要、Prompt 版本 | 凭据、隐藏答案、无关宿主信息 | Job Orchestrator → Failure Judge |
| `JudgeAnalysis` | 分类、解释、证据引用、模型/Prompt 版本、原始响应引用 | 对 `resolved` 的覆盖权 | Failure Judge → Review、Reporting |
| `HumanReviewRecord` | 运行、复核结论、对 Judge 的确认/修正、备注、复核者、时间 | 对原始制品的覆写 | Review → Run Repository |
| `ArtifactRef` | 对象键、类型、大小、SHA-256、内容类型、创建时间 | 制品正文 | Artifact Store → 其他所有模块 |

## 5. 模块总表

| 模块 | 大致做什么 | 主要输入 | 主要输出 | 不负责 |
|---|---|---|---|---|
| HTTP Delivery | 把浏览器请求翻译为应用用例 | HTTP 请求 | HTTP 响应/错误 | 运行 Agent、写 SQL |
| Task Catalog | 从固定 SWE-Gym 数据取得任务 | 数据集版本 + `instance_id` | `EvaluationTask` | 运行或判题 |
| Agent Registry | 只提供已审核 Agent 配置 | 配置 ID/筛选条件 | `AgentConfiguration` | 下载任意仓库 |
| Job Submission | 校验矩阵并创建排队 Job | 任务 ID[] + Agent 配置 ID[] + 赛道/限制模板 | `job_id`、`run_id[]`、Trial 数和初始状态 | 执行评测 |
| Job/Run Repository | 保存、领取、推进和查询 Job/运行 | Job/运行状态命令 | 持久化结果/查询视图 | 保存大制品正文、调度 Harbor Trial |
| Job Orchestrator | 编排一个 Job 的执行和逐题判卷 | 已领取 Job | Job 汇总与逐题完整结果 | 理解 Harbor 类型或具体 CLI |
| Execution Backend | 执行一批 Agent×任务并返回逐题补丁/证据 | `ExecutionJobRequest` | `ExecutionTrialResult[]` | 判断补丁正确性、管理业务队列 |
| Agent Source Review | 审核源码提交并登记可执行配置 | Git URL + commit + manifest + 审核决定 | 已登记/拒绝的 Agent 配置 | 审核前执行仓库代码 |
| Patch Evaluator | 调用 SWE-Bench-Fork 判卷 | `EvaluationRequest` | `DeterministicResult` | LLM 评分 |
| Trajectory Recorder | 规范化并保存可公开过程证据 | 原始 CLI/进程事件 | JSONL 轨迹引用 + 汇总 | 保存思维链或秘密 |
| Artifact Store | 保存不可变文件证据 | 字节流 + 元数据 | `ArtifactRef` | 决定运行状态 |
| Failure Judge | 对失败证据分类解释 | `JudgeRequest` | `JudgeAnalysis` | 修改确定性事实 |
| Human Review | 领取抽检并保存人工结论 | 待复核运行 + 人工输入 | `HumanReviewRecord` | 重跑 Agent |
| Reporting | 组合只读报告和排行榜 | 查询条件 | 报告/排行视图 | 改写原始结果 |
| Worker Shell | 原子领取平台 Job 并调用 Job Orchestrator | Worker 身份 + 轮询配置 | 心跳/Job 执行结果 | 包含业务判定规则 |

## 6. 逐模块契约

### 6.1 HTTP Delivery

| 项目 | 候选 v0.1 契约 |
|---|---|
| 调用方 | Next.js Web；首版不允许 Web 直接访问存储 |
| 输入 | 经过版本化的 HTTP 请求、路径参数和查询参数 |
| 输出 | 稳定的 JSON 成功响应，或统一 `ApiError` |
| 错误 | 请求格式错误、资源不存在、状态冲突、服务暂不可用 |
| 不变量 | 只调用 application 用例；不执行 Agent、不拼 SQL、不返回 MinIO 密钥 |
| 依赖 | Job Submission、Review、Reporting 等应用入口 |
| 验证 | OpenAPI schema 检查；请求/响应契约测试；错误码测试 |

详细端点只在 [`HTTP_API.md`](../interfaces/HTTP_API.md) 维护。

### 6.2 Task Catalog

| 项目 | 候选 v0.1 契约 |
|---|---|
| 调用方 | Job Submission、Job Orchestrator、Reporting |
| 输入 | `dataset_id`、`dataset_revision`、`split`、`instance_id` |
| 输出 | 规范化 `EvaluationTask`，以及仅供 Evaluator 使用的验证引用 |
| 错误 | 数据集不存在、任务不存在、字段缺失、固定版本校验不一致 |
| 不变量 | 同一数据集版本和任务 ID 必须返回相同任务；Agent 可见视图不得包含 gold patch/测试答案 |
| 依赖 | SWE-Gym 数据；SWE-Bench-Fork 的任务字段约定 |
| 验证 | 用固定样例检查字段映射；测试秘密字段不会进入 Runner 输入 |

### 6.3 Agent Registry

| 项目 | 候选 v0.1 契约 |
|---|---|
| 调用方 | Job Submission、Job Orchestrator、Execution Backend、Reporting |
| 输入 | 登记配置 ID，或只读筛选条件 |
| 输出 | 固定版本的 `AgentConfiguration`；可展示列表 |
| 错误 | 未登记、已禁用、版本/镜像不存在、配置指纹不匹配 |
| 不变量 | 只返回项目组审核的允许列表；Agent + 模型 + 关键配置共同构成排行榜身份 |
| 依赖 | PostgreSQL 配置记录；项目内 Adapter Factory |
| 验证 | 未登记命令不能运行；相同配置生成相同指纹；秘密不进入查询结果 |

### 6.4 Job Submission

| 项目 | 候选 v0.1 契约 |
|---|---|
| 调用方 | HTTP Delivery |
| 输入 | `task_ids[]`、`agent_configuration_ids[]`、`evaluation_track`、登记的规模预设与 `limit_profile_id` |
| 输出 | 新 `job_id`、`QUEUED` Job、交叉组合产生的 `run_id[]`、`trial_count`、创建时间 |
| 错误 | 任务/Agent 不存在、配置禁用、限制越界、重复幂等键冲突 |
| 不变量 | 任务与 Agent 列表非空且去重；首版每组合尝试一次；创建时冻结任务/Agent/后端/策略/限制；不接收任意 shell 命令或资源值；Mock Job 必须隔离为 `internal_test` |
| 依赖 | Task Catalog、Agent Registry、Job/Run Repository |
| 验证 | 合法矩阵生成正确数量的运行；越权限制被拒绝；重复幂等请求不产生两个 Job；超出规模预设在执行前拒绝 |

### 6.5 Job/Run Repository

| 项目 | 候选 v0.1 契约 |
|---|---|
| 调用方 | Job Submission、Worker Shell、Job Orchestrator、Review、Reporting |
| 输入 | 创建 Job/运行、原子领取一个 Job、合法状态迁移、附加结果、查询命令 |
| 输出 | 当前 Job/运行、领取结果、版本号或只读查询视图 |
| 错误 | 状态冲突、并发版本冲突、记录不存在、数据库暂不可用 |
| 不变量 | 状态迁移只按 `DATA_MODEL.md`；一个排队 Job 只被一个 Worker 领取；单机最多一个重型 Job 活跃；运行不独立从 PostgreSQL 抢队；大制品只存引用 |
| 依赖 | PostgreSQL Adapter |
| 验证 | 并发领取测试；非法回退状态测试；事务回滚测试 |

### 6.6 Job Orchestrator

| 项目 | 候选 v0.1 契约 |
|---|---|
| 调用方 | Worker Shell |
| 输入 | 已领取且处于 `PREPARING` 的 Job 及其 `PENDING` 运行快照 |
| 输出 | Job 汇总、逐题运行结果，或明确的部分/整体基础设施失败记录 |
| 错误 | 任务准备、Agent、补丁提取、Evaluator、存储或 Judge 阶段错误；错误必须带阶段和证据引用 |
| 不变量 | 每条运行顺序固定为 Harbor 执行 → 保存证据 → 固定 Fork 干净验证 → 分析/复核；Harbor reward 不能写入确定性结果；已完成 Trial 的证据不因后续 Trial 失败而丢失 |
| 依赖 | Task Catalog、Execution Backend、Patch Evaluator、Artifact Store、Failure Judge、Job/Run Repository |
| 验证 | 用 Fake ports 覆盖每个分支；任一步骤失败都不会伪装成完成；重试不覆盖旧制品 |

这是一个“深模块”：对外只有“执行一个 Job”，内部隐藏逐 Trial 判卷、部分失败、证据保存和汇总，不让 Worker 参与编排细节。

### 6.7 Execution Backend

| 项目 | 候选 v0.1 契约 |
|---|---|
| 调用方 | Job Orchestrator |
| 输入 | `ExecutionJobRequest`；只含已登记任务/Agent、冻结策略、限制和 `run_id` 映射 |
| 输出 | 与请求逐项对应的 `ExecutionTrialResult[]`；补丁、轨迹和原始输出均通过 `ArtifactRef` 关联 |
| 错误 | 后端版本不符、配置映射失败、认证、环境、超时、Agent、补丁提取、Trial 身份或制品错误 |
| 不变量 | 不能宣判 `resolved`；不能把自然语言回答当补丁；不能运行未审核配置；Harbor `TrialResult` 不向调用方泄漏；并发固定 1 |
| 依赖 | Agent Registry、Harbor 固定提交、Docker、Trajectory Normalizer、Artifact Store |
| 验证 | Harbor/Fake Backend 共用同一 interface contract；空补丁与失败分开；真实 SWE-Gym 单题原型覆盖补丁、轨迹、资源和清理 |

Harbor 映射见 [`HARBOR_EXECUTION.md`](../interfaces/HARBOR_EXECUTION.md)；自研/后备进程边界见 [`RUNNER_PROTOCOL.md`](../interfaces/RUNNER_PROTOCOL.md)。

### 6.8 Agent Source Review

| 项目 | 候选 v0.1 契约 |
|---|---|
| 调用方 | 可信用户提交入口、管理员审核界面 |
| 输入 | 固定 Git URL、完整 commit SHA、`agent-exam.yaml`、说明和审核决定 |
| 输出 | `PENDING_REVIEW` 提交记录，或审核通过后新 `AgentConfiguration` |
| 错误 | URL/commit/manifest 无效、来源不可访问、危险声明、重复提交、权限不足 |
| 不变量 | 审核前不执行仓库代码、不构建镜像、不把提交者输入直接变成 Harbor `import_path`/命令；禁用不删除历史配置 |
| 依赖 | Agent Registry、PostgreSQL；manifest schema 待下一轮确认 |
| 验证 | 未审核提交无法创建 Job；分支/`latest` 被拒绝；审核事件可追溯；秘密和任意命令不进入公开配置 |

### 6.9 Patch Evaluator

| 项目 | 候选 v0.1 契约 |
|---|---|
| 调用方 | Job Orchestrator |
| 输入 | `EvaluationRequest` |
| 输出 | `DeterministicResult` 和 Harness 制品引用 |
| 错误 | prediction 格式错误、镜像构建失败、补丁无法应用、测试超时、Harness 异常 |
| 不变量 | 直接调用固定版本 SWE-Bench-Fork；Agent 生成环境的残留不得进入验证；Judge 不能改写输出 |
| 依赖 | SWE-Bench-Fork、SWE-Gym 数据/环境、Fork 自身 Docker Harness、Artifact Store |
| 验证 | gold patch、空 patch、错误 patch、不可应用 patch、测试超时五类样例 |

注意：补丁“可应用但测试未通过”是一次正常完成的确定性评测；Harness 无法完成才是基础设施错误。

### 6.10 Trajectory Recorder

| 项目 | 候选 v0.1 契约 |
|---|---|
| 调用方 | Execution Backend Adapter 内部实现 |
| 输入 | Codex/Claude/Aider/自研 Agent 的原始事件，外加统一时间和来源信息 |
| 输出 | 按序 JSONL 轨迹 `ArtifactRef`，以及工具调用数、耗时、token 等可用汇总 |
| 错误 | 事件无法解析、序号断裂、大小超限、写入失败 |
| 不变量 | 保存可观察事件，不要求或保存私密思维链；保留 `raw_type` 以便审计；任何秘密先脱敏 |
| 依赖 | Artifact Store；各 CLI 的官方事件格式 |
| 验证 | 预制事件样本契约测试；坏行容错；脱敏、顺序和汇总一致性检查 |

### 6.11 Artifact Store

| 项目 | 候选 v0.1 契约 |
|---|---|
| 调用方 | Job Orchestrator、Execution Backend、Recorder、Evaluator、Judge、Reporting |
| 输入 | `run_id`、制品类型、文件名、内容流、内容类型 |
| 输出 | 带 SHA-256、大小和对象键的 `ArtifactRef` |
| 错误 | 写入/读取失败、校验和不一致、对象不存在、类型不允许 |
| 不变量 | 制品写入后不可覆盖；重跑创建新 `run_id`；对象键不包含秘密或用户路径 |
| 依赖 | MinIO；PostgreSQL 中的 `artifact_records` 索引 |
| 验证 | 同内容校验、覆盖拒绝、断流、缺失对象和大文件流式测试 |

### 6.12 Failure Judge

| 项目 | 候选 v0.1 契约 |
|---|---|
| 调用方 | Job Orchestrator；只在确定性结果产生后运行 |
| 输入 | `JudgeRequest` |
| 输出 | `JudgeAnalysis` 和原始响应 `ArtifactRef` |
| 错误 | 模型不可用、超时、schema 不合格、证据不足、内容被拒绝 |
| 不变量 | 输出是分析而非测试事实；必须保存模型、Prompt 版本和输入证据引用；不能接收秘密 |
| 依赖 | LLM Provider Adapter、Artifact Store |
| 验证 | 固定证据集上的 schema/分类测试；模型失败不丢失确定性结果；Prompt 版本可追溯 |

### 6.13 Human Review

| 项目 | 候选 v0.1 契约 |
|---|---|
| 调用方 | HTTP Delivery、抽检规则 |
| 输入 | 待复核运行、复核者提交的分类/结论/备注、幂等键 |
| 输出 | `HumanReviewRecord` 和更新后的复核状态 |
| 错误 | 非待复核状态、重复提交冲突、运行不存在、必需证据缺失 |
| 不变量 | 人工记录只能追加或版本化修订，不覆盖确定性结果、Judge 原始响应或旧复核证据 |
| 依赖 | Run Repository、Reporting |
| 验证 | 领取冲突、重复提交、修正 Judge 而不改测试事实、审计字段完整性测试 |

### 6.14 Reporting

| 项目 | 候选 v0.1 契约 |
|---|---|
| 调用方 | HTTP Delivery |
| 输入 | 运行 ID，或排行榜的数据集/Agent 配置/评测赛道/时间筛选 |
| 输出 | 运行详情、证据索引、轨迹分页、排行榜聚合和抽检视图 |
| 错误 | 资源不存在、筛选无效、制品暂不可用 |
| 不变量 | 只读；确定性、过程指标、Judge、人工复核分层展示；不同 Agent 配置不混分；闭卷主榜与开卷实验榜不混分 |
| 依赖 | Run Repository、Artifact Store |
| 验证 | 聚合样例测试；同 Agent 不同模型分行；缺失 Judge 时仍能展示确定性结果 |

### 6.15 Worker Shell

| 项目 | 候选 v0.1 契约 |
|---|---|
| 调用方 | 单机进程管理器/容器启动命令 |
| 输入 | `worker_id`、轮询间隔、固定重型 Job 并发 1、优雅停止信号 |
| 输出 | 心跳、Job 领取记录、一次 Job Orchestrator 调用结果 |
| 错误 | 数据库不可用、失去租约、进程停止 |
| 不变量 | 只负责循环和进程生命周期；业务流程只调用 Job Orchestrator；任何配置下都不得同时执行两个重型 Job |
| 依赖 | Job/Run Repository、Job Orchestrator |
| 验证 | 双 Worker 不重复领取同一 Job且不产生两个活跃 Job；停止时不误报完成；超期租约由明确恢复流程处理 |

## 7. 必须跨模块保持的规则

1. `job_id` 是批次主线，`run_id` 是每个 Agent×任务尝试及其制品的追溯主线；二者不可互相替代。
2. Job 创建时冻结数据集版本、Harbor/Fork 提交、Agent 配置指纹、执行协议和限制。
3. Agent 只看到 Issue 与仓库快照，不看到 gold patch、`test_patch` 或隐藏判分答案。
4. Agent 原始 stdout 和 Harbor `TrialResult` 都不是最终补丁；Execution Backend 必须从受控 Git 工作区提取并校验 diff。
5. 确定性结果、Judge 分析和人工复核是三类不同事实，任何一层不得覆写上一层原始证据。
6. 工具调用次数是过程指标；是否计分仍待确认，当前不能用“调用越多越积极”作为既定规则。
7. 未登记 Agent、未固定版本或携带任意 shell 命令的请求不得进入执行链路。
8. 每次运行冻结 `evaluation_track`、网络策略和工具配置；闭卷与开卷使用相同确定性判卷，但成绩严格分榜。
9. 模型来源国家不能推导网络能力；只以该次运行实际登记并验证的工具和网络策略为准。
10. Mock 只允许 `internal_test`，报告和排行榜必须从查询层排除。

## 8. 尚待继续讨论

1. Judge 是否进入总分，还是只做失败归因。
2. 工具调用、token、耗时等过程指标只展示，还是形成单独效率分。
3. 开卷实验榜使用统一的平台 Web 工具，还是各 Agent 原生搜索工具；以及相应的公平性标注。
4. Harbor/Worker 是宿主机进程还是挂载 Docker Socket 的容器；必须先做本机最小实验。
5. `agent-exam.yaml` 的最小字段和自研 Agent 到 Harbor 的转换方式。
6. 已确认只允许可信用户，但具体登录方案和提交者/管理员/评审者权限仍待确定。

## 9. 变更记录

- 2026-09-01：创建候选 v0.1；明确公共对象、15 个模块的职责/输入/输出/错误/不变量/依赖/验证，以及跨模块保密和证据规则。
- 2026-09-02：同步闭卷主榜/开卷实验榜决定；新增评测策略对象，并要求 Run、Runner、Sandbox 和 Reporting 冻结赛道、网络及工具配置。
- 2026-09-03：用 Job Submission、Job Orchestrator 和深 `ExecutionBackend` 取代逐运行自研 Runner/Sandbox 主路径；Harbor 为主 Adapter，固定 Fork 独立判卷，并新增受控 Agent 源码审核模块。
