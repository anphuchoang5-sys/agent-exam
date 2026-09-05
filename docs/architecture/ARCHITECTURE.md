# AI Coding Agent 评测平台总架构

> 文档状态：总体方案已确认，细节持续讨论；尚无业务代码
> 最后更新：2026-09-05
> 权威范围：本文件只维护系统全局组成、依赖方向、已确认决定、规划文件树、风险和待讨论队列。字段级契约由第 1 节列出的专题文档维护。

## 1. 从哪里开始读

如果把整个系统理解成“给多个 Coding Agent 发同一张卷子，并保留完整阅卷证据”，文档分工如下：

| 想知道什么 | 唯一维护文档 |
|---|---|
| 项目里的词是什么意思 | [`CONTEXT.md`](../../CONTEXT.md) |
| 系统由什么组成、为什么这样分 | 本文 |
| 项目依赖什么、从哪里取得、固定到哪个版本 | [`DEPENDENCIES.md`](../dependencies/DEPENDENCIES.md) |
| 每个模块做什么、输入输出和错误是什么 | [`MODULE_CONTRACTS.md`](./MODULE_CONTRACTS.md) |
| 自研 Agent 或后备进程怎样接题并交 patch | [`RUNNER_PROTOCOL.md`](../interfaces/RUNNER_PROTOCOL.md) |
| AgentExam 怎样调用 Harbor、怎样取得 Trial 结果 | [`HARBOR_EXECUTION.md`](../interfaces/HARBOR_EXECUTION.md) |
| Next.js 怎样调用 FastAPI | [`HTTP_API.md`](../interfaces/HTTP_API.md) |
| PostgreSQL/MinIO 保存什么 | [`DATA_MODEL.md`](./DATA_MODEL.md) |
| SWE-Gym、SWE-Bench-Fork 和各 Agent 的真实接口 | [`FRAMEWORK_INTERFACES.md`](../interfaces/FRAMEWORK_INTERFACES.md) |
| Codex 怎样认证、凭据归谁以及协作时怎样隔离秘密 | [`CODEX_AUTHENTICATION.md`](../interfaces/CODEX_AUTHENTICATION.md) |
| 协作者怎样从校园网外提交、VPN 会不会冲突、哪些端口不能开放 | [`REMOTE_TEAM_ACCESS.md`](../operations/REMOTE_TEAM_ACCESS.md) |
| 外部事实如何查证 | [`docs/research`](../research/) |
| 每次修改的措施和验证证据 | [`docs/actions`](../actions/) |

状态词：

- **已确认**：用户已经决定，后续实现必须遵守。
- **已核验**：已从上游源码或官方文档查到。
- **候选 v0.x**：已经写成可讨论契约，但尚未实现或最终确认；具体版本以专题文档为准。
- **待确认/待实测**：需要人类决定或真实运行证据。
- **已实现**：代码存在且验证通过；当前没有业务代码，因此不能使用这个标签。

## 2. 项目要做什么

一次完整使用动线：

1. 可信协作者通过私有远程入口，从已登记列表选择一个或多个固定 Agent 配置、一个或多个 SWE-Gym 任务和一个评测赛道。
2. 平台创建 `AWAITING_OWNER_APPROVAL` Job，并预先冻结 Agent×任务组合对应的逐题评测运行；提交本身不启动真实评测。
3. 评测机所有者检查冻结配置并明确批准后，Job 才进入 PostgreSQL 的 `QUEUED` 队列；拒绝则终止，不交给 Worker。
4. 评测机本地的单机 Worker 一次只领取一个已批准 Job；Execution Backend Adapter 把它转换为一个 Harbor Job，并固定 `n_concurrent_trials=1`。
5. Harbor 把 Agent×任务展开为 Trial，运行真实 Agent、管理 Docker 环境并保存过程事件、原始输出和制品。
6. Adapter 为每个 Trial 校验并返回最终 patch；SWE-Bench-Fork 在新的干净验证环境中独立应用 patch 和执行测试。
7. 页面展示 Job 总进度，并对每条运行分别展示确定性结果、过程指标、LLM Judge 失败归因和人工复核。
8. 排行榜按完整的“Agent + 模型 + 关键配置”统计，原始证据能从 `job_id` 追溯到每个 `run_id`。

## 3. 已确认决定

| 编号 | 决定 | 直接影响 |
|---|---|---|
| C-01 | 直接使用 SWE-Gym 与配套 SWE-Bench-Fork | 不重写任务语义和判卷核心；固定上游版本并通过 Adapter 调用 |
| C-02 | 只有一台物理计算机 | 不设计多机调度、Kubernetes 或分布式存储 |
| C-03 | 周期约一个月，实际开发力量约 2.5 人 | 优先最小完整闭环，控制并发和功能范围 |
| C-04 | Web 为 Next.js 15 + React 19 | 页面独立，不在前端直接驱动 Docker/Harness |
| C-05 | 后端为 Python + FastAPI，耗时任务由 Python Worker 执行 | 与 Python 版 SWE-Bench-Fork 同语言；HTTP 请求不等待评测完成 |
| C-06 | PostgreSQL 保存元数据并承担平台评测 Job 队列，MinIO 保存制品 | 首版不引入 Redis/Celery；不把 Harbor 本地目录当课程数据库；大日志不塞数据库 |
| C-07 | 单机模块化单体 | 代码按边界分模块，但不拆微服务；Web/API/Worker 为进程角色，不是独立业务微服务 |
| C-08 | Harbor 使用 Docker 运行 Agent；固定 SWE-Bench-Fork 使用独立干净验证环境 | 两阶段隔离；最终判卷不能受 Agent 工作区或 Harbor reward 影响 |
| C-09 | 全程证据可追溯 | patch、轨迹、原始输出、测试、Judge 和人工复核都关联同一 `run_id` |
| C-10 | 第一版只运行项目组审核、登记并固定版本的 Agent | 可信用户可提交固定 Git URL + commit + `agent-exam.yaml` 供审核；未审核仓库绝不执行，也不接受用户提交任意 shell 命令 |
| C-11 | 排行榜单位是 Agent + 模型 + 关键配置 | 不同模型/关键配置分行统计，不能混为同一 Agent 成绩 |
| C-12 | 第一版目标包含自研 Agent、Codex、Aider、Claude Code | 优先复用 Harbor 已有 Agent；Mock 仅用于内部软件测试，不属于正式接入成绩 |
| C-13 | 确定性测试、Judge 分析、人工复核分层保存 | LLM 或人工解释不能覆盖 SWE-Bench-Fork 原始测试事实 |
| C-14 | 架构、模块、接口、框架事实和行动记录分文档持续维护 | 同一事实只设一个权威来源；实现变化时同任务更新相关文档 |
| C-15 | 采用闭卷主排行榜（`closed_book`）+ 开卷实验榜（`open_book_experimental`） | 两条赛道使用相同确定性判卷，但按网络/工具配置严格分榜，不横向混分 |
| C-16 | Harbor 是带验收退出条件的正式 Execution Backend | 版本由依赖事实源固定；隐藏在 Adapter 后；原型失败时替换为轻量 Process Adapter，不改上层业务 |
| C-17 | 一个平台评测 Job 映射一个 Harbor Job，一条评测运行映射一个 Harbor Trial | 平台负责业务排队和长期事实；Harbor 负责 Job 内 Trial 执行 |
| C-18 | 单机同时只执行一个重型平台 Job，Harbor `n_concurrent_trials=1` | Job 中 Trial 顺序执行；不以增加并发换取演示速度 |
| C-19 | 一个 Job 可选择多个 Agent 和多个任务，首版每组合尝试一次 | 创建前展示 Trial 总数；预设规模为演示 1–3 题、快速 5 题、标准 10–20 题，Agent 首版最多约 3 个 |
| C-20 | 正式展示、报告和排行只接受真实执行证据 | Mock 结果必须隔离为 `internal_test`，不能冒充真实 Agent 或进入正式统计 |
| C-21 | 首个真实端到端原型使用 `SWE-Gym/SWE-Gym-Lite` 的 1～3 道真实任务 | 先验证小而真的闭环；不下载完整 2.4K 任务，也不把 Lite 冒充为最终正式题库范围 |
| C-22 | 首个真实原型 Agent 使用 Codex | 优先复用 Harbor 内置 Codex Adapter；先跑通一个 Agent，再扩展 Aider、Claude Code 和自研 Agent |
| C-23 | 首个 Codex 原型使用评测机所有者本人通过 ChatGPT Pro 登录产生的 `auth.json` | 认证政策已经确认；凭据只由执行节点临时注入，不得共享、提交或持久化；容器内运行仍待实测 |
| C-24 | 当前只有用户这一台笔电是正式真实评测节点 | 协作者可开发并远端提交；只有机器所有者批准后，本机 Worker 才能触发真实 Codex Trial；协作者不得取得所有者凭据 |
| C-25 | Kimi 与 DeepSeek 以后只作为独立 Agent Configuration | 一次 Trial 不得从 Codex/OpenAI 静默切换提供方；切换必须产生独立配置与运行证据 |
| C-26 | 协作者提交正式真实 Job 后必须等待评测机所有者批准 | 新 Job 初始为 `AWAITING_OWNER_APPROVAL`；只有所有者批准才能进入 `QUEUED`，Worker 不能领取待批准 Job |
| C-27 | 协作者使用平台时，评测机和本机平台必须在线 | 当前不增加云端常驻控制面或第二执行节点；评测机离线时私有远程入口不可用，恢复在线后继续接收请求 |

## 4. 总体架构

```mermaid
flowchart TB
    COLLAB[远端可信协作者] --> PRIVATE[私有远程入口\n具体产品待确认]
    OWNER[评测机所有者] --> WEB[Next.js 15 + React 19]

    subgraph HOST[单台物理计算机]
        PRIVATE --> WEB
        WEB --> API[FastAPI HTTP Delivery]
        API --> APP[应用用例 / 模块化单体]
        APP --> PG[(PostgreSQL\n元数据 + Job 队列)]
        APP --> MINIO[(MinIO\n不可变制品)]

        WORKER[Python Worker\n同时 1 个重型 Job] --> PG
        WORKER --> ORCH[Job Orchestrator]
        ORCH --> TASK[Task Catalog Adapter]
        ORCH --> EXEC[ExecutionBackend interface]
        ORCH --> EVAL[Patch Evaluator Adapter]
        ORCH --> JUDGE[Failure Judge Adapter]
        ORCH --> MINIO

        TASK --> SWEGYM[SWE-Gym 数据]
        EXEC --> HARBORADAPTER[Harbor Execution Adapter]
        HARBORADAPTER --> HJOB[Harbor Job]
        HJOB --> HTRIAL[Harbor Trial\n顺序执行]
        HTRIAL --> AGENTBOX[Docker Agent 生成环境]
        AGENTBOX --> AGENTS[自研 / Codex / Aider / Claude Code]
        HARBORADAPTER --> MINIO
        EVAL --> HARNESS[SWE-Bench-Fork Harness]
        HARNESS --> VERIFYBOX[Docker 干净验证沙箱]
    end
```

边界规则：

- 私有远程入口只把 Next.js Web 暴露给获准成员；FastAPI 绑定本机回环地址并由 Web 同源转发。PostgreSQL、MinIO、Docker、Worker 和宿主凭据路径不得成为远程入口。
- Web 只走 HTTP API，不直连 PostgreSQL、MinIO 或 Docker。
- FastAPI 负责短请求、校验和查询，不亲自等待 Agent/Harness。
- Job Submission 只创建 `AWAITING_OWNER_APPROVAL` Job；Owner Approval 以可信会话中的所有者身份批准或拒绝。只有批准事务写成 `QUEUED` 后，Worker 才能领取。
- Worker 只在正式评测机本地运行，原子领取 `QUEUED` Job，再调用一个深的 Job Orchestrator；Job 内的逐题运行由 Harbor Trial 顺序执行。
- Orchestrator 只依赖小型 `ExecutionBackend` interface，不直接理解 Harbor `JobConfig`、Trial 目录或异常。
- Harbor 负责 Agent 环境，不替代 PostgreSQL 业务队列、MinIO 长期制品、SWE-Bench-Fork 判卷、Judge 或人工复核。
- Web、公开 Job 请求、FastAPI、PostgreSQL 和 MinIO 不接收 `auth.json` 内容或真实宿主路径；只保存非秘密的认证类型和逻辑配置身份。执行节点仅在启动受控 Codex Trial 时，从本机秘密配置解析凭据引用；这条秘密路径不属于业务数据流，完整约束见 [`CODEX_AUTHENTICATION.md`](../interfaces/CODEX_AUTHENTICATION.md)。
- 闭卷 Agent 生成沙箱只允许模型调用所需端点，并禁用 Web 搜索/抓取工具；开卷实验运行允许已登记的联网工具。验证沙箱候选为断网干净环境。代理、端点白名单和工具公平性的精确实现仍待确认。

## 5. 一次运行的输入输出

```mermaid
sequenceDiagram
    actor C as 远端可信协作者
    actor O as 评测机所有者
    participant W as Next.js Web
    participant A as FastAPI
    participant D as PostgreSQL
    participant K as Worker/Job Orchestrator
    participant T as SWE-Gym Task Adapter
    participant H as Harbor Execution Backend
    participant S as MinIO
    participant E as SWE-Bench-Fork
    participant J as LLM Judge

    C->>W: 通过私有入口选择任务和 Agent 配置
    W->>A: POST /api/v1/jobs
    A->>D: 创建 AWAITING_OWNER_APPROVAL Job + PENDING runs
    A-->>W: 202 + job_id + trial_count + 待批准
    O->>W: 检查冻结配置并批准
    W->>A: POST /api/v1/jobs/{job_id}/approve
    A->>D: AWAITING_OWNER_APPROVAL → QUEUED + 审计事件
    A-->>W: 200 + QUEUED
    K->>D: 只原子领取 QUEUED Job
    K->>T: 读取 Job 中冻结的任务
    T-->>K: EvaluationTask[]
    K->>H: ExecutionJobRequest（不含隐藏答案）
    H->>H: 生成 1 个 Harbor Job，n_concurrent_trials=1
    loop 每个 Harbor Trial / Evaluation Run
        H->>S: 保存并校验 patch/轨迹/日志/原始结果
        H-->>K: run_id + 执行证据引用
        K->>S: 按 patch_ref 读取已校验 patch
        S-->>K: model_patch 字节
        K->>E: instance_id + model_patch + Agent 身份
        E-->>K: 确定性结果 + Harness 证据
        K->>S: 保存测试报告和输出
        opt 失败归因或抽检
            K->>J: 受控失败证据
            J-->>K: JudgeAnalysis
            K->>S: 保存原始 Judge 证据
        end
        K->>D: 更新逐题运行状态
    end
    K->>D: 汇总 Job 完成/部分失败/失败
    W->>A: 轮询报告和轨迹
    A-->>W: 分层结果与制品索引
```

图中没有画出 `auth.json`，因为它不是 Job 输入或业务制品：只有执行节点能从本机秘密配置中解析它，并在受控 Codex Trial 的最小生命周期内临时使用。远端协作者只提交冻结的公开评测选择，批准接口也不能读取或返回凭据。

关键输入输出的字段、错误和保密边界不在本文重复，分别见：

- 内部模块：[`MODULE_CONTRACTS.md`](./MODULE_CONTRACTS.md)
- Runner 进程：[`RUNNER_PROTOCOL.md`](../interfaces/RUNNER_PROTOCOL.md)
- Harbor 执行：[`HARBOR_EXECUTION.md`](../interfaces/HARBOR_EXECUTION.md)
- HTTP：[`HTTP_API.md`](../interfaces/HTTP_API.md)
- 依赖来源、固定版本与恢复方式：[`DEPENDENCIES.md`](../dependencies/DEPENDENCIES.md)
- 上游框架/CLI：[`FRAMEWORK_INTERFACES.md`](../interfaces/FRAMEWORK_INTERFACES.md)

## 6. 运行结果怎样理解

| 层 | 回答的问题 | 是否为最终测试事实 |
|---|---|---:|
| Execution Backend 结果 | Agent 是否正常运行、产生了什么 patch/轨迹 | ❌ |
| 确定性验证 | patch 是否应用、规定测试是否通过、`resolved` 是否为真 | ✅ |
| 过程指标 | 调用了哪些可观察工具、耗时/token/资源怎样 | ❌ |
| Judge 分析 | 为什么失败、过程可能有什么问题 | ❌ |
| 人工复核 | 人类是否同意/修正 Judge 解释 | ❌，但属于审计事实 |

必须区分：

- Agent 正常结束但没有修好：运行可以 `COMPLETED`，`resolved=false`。
- Agent/Harness/存储链路没能形成可信结果：运行 `FAILED`，`resolved` 应为空，而不是伪造 false。
- 工具调用次数是可观察过程指标。Aider 当前没有官方结构化工具事件流，因此缺失值不能写 0；是否计分仍待确认。

评测赛道也必须区分：

- **闭卷主排行榜（`closed_book`）**：Agent 使用题目、仓库和本地工具做题；只保留模型服务所需网络，不开放一般 Web 查询。
- **开卷实验榜（`open_book_experimental`）**：允许已登记的 Web/网络工具，更接近真实用户使用，但必须保存工具与访问证据。
- 两条赛道继续使用同一个 SWE-Bench-Fork 结果作为正确性事实；同一 Agent 配置跨赛道的成绩也不能合并。
- “所有 Agent 使用同一套平台 Web 工具”与“允许各自原生搜索工具”仍是待确认的开卷公平标准。

## 7. 为什么选择这个架构

### 7.1 模块化单体，而不是微服务

- 一台机器、一个月、2.5 人不值得承担服务发现、跨服务鉴权、网络重试和分布式一致性。
- 模块仍通过 ports 隔离；以后真有多机需要，可以优先把 Worker 边界外移。
- Web、API、Worker 是不同进程职责，但共享一个后端领域/应用代码库，不把它们误称为三套微服务。

### 7.2 PostgreSQL 管平台 Job 队列，而不是让 Harbor 代替业务数据库

- PostgreSQL 已经是题目要求，可信用户、审核、排队、取消、报告和长期状态必须有业务事实源。
- Harbor Job 目录是执行产物，不负责课程用户、权限和长期查询；PostgreSQL 只领取平台 Job，不逐条与 Harbor 抢调度权。
- 候选使用短事务和 `FOR UPDATE SKIP LOCKED`，并额外保证只有一个重型 Job 活跃；精确 SQL 和崩溃恢复要通过双 Worker 实测。

### 7.3 深的 Execution Backend，而不是把 Harbor 类型传播到全项目

- Harbor 已经处理多种 Agent、Docker 环境、Job/Trial 和轨迹；重复自研会增加一个月项目的风险。
- `HarborExecutionAdapter` 把差异翻译成一个项目 interface；Job Orchestrator 永远只理解“批次进去，逐题 patch/证据出来”。
- Harbor 原型若失败，只新增后备 `ProcessExecutionAdapter`；调用方、数据库和 HTTP 不跟着重写。

### 7.4 两阶段沙箱

- Agent 生成环境允许修改仓库、运行获准工具，并记录轨迹。
- Patch Evaluator 重新从固定任务环境开始，只应用最终 patch，再执行真实测试。
- 这样 Agent 修改测试、留下缓存或声称“我测试通过”都不能替代最终判卷。

### 7.5 Harbor Job 不是最终判卷

- 固定提交允许 `verifier.disable=true`；Harbor 仍先同步 Agent 日志并收集 artifacts。
- Harbor `TrialResult` 没有标准 `model_patch` 字段，补丁出口必须通过真实原型验收。
- 只有固定 SWE-Bench-Fork 的完整报告能写入 `DeterministicResult.resolved`；Harbor reward 只可作为调试证据或直接禁用。

## 8. 候选项目文件树

以下是规划，不表示路径已经创建。源代码实施时继续遵守：动态语言单文件默认不超过 200 行、每层默认不超过 8 个文件；确需超过先在行动文档说明并取得确认。

```text
E:\9.1agent_exam\
├─ AGENTS.md
│  # Codex 协作、文档唯一事实源、验证和代码架构规则
├─ CONTEXT.md
│  # 项目领域术语唯一事实源；不记录框架和部署细节
├─ framework\
│  # 本地恢复的第三方上游依赖；不进入 AgentExam 主仓库，来源与版本见依赖文档
│  ├─ swe-gym\
│  │  # 固定提交的 SWE-Gym 数据/实验框架源码
│  ├─ swe-bench-fork\
│  │  # 固定提交的 Docker 环境与确定性 Harness
│  └─ harbor\
│     # 未来按依赖文档恢复的 Harbor 固定源码；当前尚未下载
├─ apps\
│  ├─ backend\
│  │  # FastAPI 与 Worker 共享的 Python 模块化单体
│  │  ├─ pyproject.toml
│  │  │  # Python 依赖、测试、格式和命令入口
│  │  ├─ src\eval_platform\
│  │  │  ├─ domain\
│  │  │  │  # 纯领域规则，不依赖框架/数据库/Docker
│  │  │  │  ├─ task.py       # EvaluationTask 与 Agent 可见/验证视图边界
│  │  │  │  ├─ agent.py      # AgentConfiguration 与配置指纹规则
│  │  │  │  ├─ job.py        # EvaluationJob、组合规模和 Job 状态规则
│  │  │  │  ├─ run.py        # EvaluationRun：逐 Trial 状态和合法迁移
│  │  │  │  └─ result.py     # 确定性、Judge、人工复核的分层结果
│  │  │  ├─ application\
│  │  │  │  # 用例层，只依赖 domain 与 ports
│  │  │  │  ├─ ports\
│  │  │  │  │  # 外部能力的小接口；Adapter 的替换 seam
│  │  │  │  │  ├─ task_source.py  # Task Catalog port
│  │  │  │  │  ├─ execution.py    # 深 ExecutionBackend port；隐藏 Harbor 类型
│  │  │  │  │  ├─ evaluator.py    # Patch Evaluator port
│  │  │  │  │  ├─ repositories.py # PostgreSQL Repository ports
│  │  │  │  │  ├─ artifacts.py    # MinIO Artifact Store port
│  │  │  │  │  └─ judge.py        # Failure Judge port
│  │  │  │  ├─ submit_job.py  # 校验矩阵并创建待所有者批准 Job + PENDING runs
│  │  │  │  ├─ approve_job.py # 所有者批准/拒绝待审 Job；批准后才进入 QUEUED
│  │  │  │  ├─ execute_job.py # 深模块：Harbor 执行、逐题判卷和 Job 汇总
│  │  │  │  └─ review_run.py  # 人工抽检与版本化复核流程
│  │  │  ├─ adapters\
│  │  │  │  # 把真实上游接口翻译为 application ports
│  │  │  │  ├─ tasks\swe_gym.py
│  │  │  │  │  # Adapter：SWE-Gym 字段 → EvaluationTask
│  │  │  │  ├─ agents\
│  │  │  │  │  # 已审核 Agent 配置与提交 manifest 的安全转换
│  │  │  │  │  ├─ registry.py # 已登记配置 → Harbor AgentConfig；不接收任意命令
│  │  │  │  │  └─ manifest.py # 静态解析 agent-exam.yaml；审核前不执行仓库代码
│  │  │  │  ├─ execution\
│  │  │  │  │  ├─ harbor\
│  │  │  │  │  │  # HarborExecutionAdapter 内部实现；外部只见 ExecutionBackend
│  │  │  │  │  │  ├─ adapter.py       # Job 生命周期与项目结果汇总
│  │  │  │  │  │  ├─ config_mapper.py # 项目 Job → Harbor JobConfig
│  │  │  │  │  │  ├─ result_mapper.py # TrialResult/异常 → ExecutionTrialResult
│  │  │  │  │  │  └─ artifacts.py     # patch/ATIF/原始结果校验和导入
│  │  │  │  │  └─ process.py
│  │  │  │  │     # 后备 Adapter：只在 Harbor 原型未过门槛时实现统一进程协议
│  │  │  │  ├─ evaluation\swe_bench.py
│  │  │  │  │  # Adapter：prediction JSONL → 固定 Fork CLI → 规范化结果
│  │  │  │  ├─ persistence\postgres.py
│  │  │  │  │  # Repository Adapter：状态事务、领取、查询和审计事件
│  │  │  │  ├─ artifacts\minio.py
│  │  │  │  │  # Artifact Adapter：不可变写入、校验和与流式读取
│  │  │  │  └─ judge\llm_judge.py
│  │  │  │     # Judge Adapter：版本化 prompt、结构化输出与原始响应
│  │  │  ├─ delivery\http\
│  │  │  │  # FastAPI 交付层；只做 schema、状态码和用例调用
│  │  │  │  ├─ app.py         # Composition Root：组装 ports/adapters 和生命周期
│  │  │  │  └─ routes\
│  │  │  │     ├─ tasks.py    # Task API
│  │  │  │     ├─ agents.py   # Agent Configuration API
│  │  │  │     ├─ jobs.py      # Job 创建、所有者批准/拒绝、列表、详情和取消 API
│  │  │  │     ├─ runs.py      # Job 内逐题运行只读 API
│  │  │  │     ├─ artifacts.py # Trajectory/Artifact API
│  │  │  │     ├─ reviews.py  # Human Review API
│  │  │  │     └─ reports.py  # Report/Leaderboard API
│  │  │  └─ worker\main.py
│  │  │     # 单机 Worker Shell：领取、心跳、停止和调用 Orchestrator
│  │  └─ tests\
│  │     ├─ unit\         # 领域状态和应用分支的快速测试
│  │     ├─ contract\     # Fake/真实 Adapter 共用的契约测试
│  │     └─ integration\  # PostgreSQL、MinIO、Docker、Harness 集成测试
│  └─ web\
│     # Next.js 15 + React 19 展示应用
│     ├─ package.json      # 固定前端依赖与命令
│     ├─ next.config.ts    # Next.js 构建配置；候选同源转发到回环 FastAPI
│     └─ src\
│        ├─ app\
│        │  # App Router 页面/布局，不直接实现后端业务
│        │  ├─ layout.tsx       # 全站布局和导航
│        │  ├─ page.tsx         # Job 概览
│        │  ├─ tasks\           # 任务浏览与选择
│        │  ├─ jobs\            # 发起 Job、待所有者批准队列、总进度和组合结果
│        │  ├─ runs\            # 运行、轨迹和证据详情
│        │  ├─ leaderboard\     # Agent 配置排行
│        │  └─ reviews\         # 人工抽检工作台
│        ├─ features\
│        │  # 与路由解耦的视图模型和交互
│        │  ├─ tasks\
│        │  ├─ jobs\
│        │  ├─ runs\
│        │  ├─ leaderboard\
│        │  └─ reviews\
│        └─ lib\
│           ├─ api-client.ts # 唯一 FastAPI 客户端
│           └─ contracts.ts  # 从 OpenAPI 生成/同步的前端类型
├─ infra\
│  # 单机部署和无秘密配置
│  ├─ compose.yaml         # Web/API/PostgreSQL/MinIO；Worker 载体待实测
│  ├─ .env.example        # 配置名和说明，不含秘密值
│  └─ containers\
│     ├─ backend.Dockerfile # FastAPI 镜像
│     ├─ worker.Dockerfile  # Worker 镜像候选
│     └─ web.Dockerfile     # Next.js 镜像
├─ tests\e2e\
│  # 从创建 Job 到逐题报告展示的单机端到端测试
└─ docs\
   ├─ dependencies\
   │  └─ DEPENDENCIES.md       # 依赖来源、固定版本、恢复方式与入库策略的唯一事实源
   ├─ architecture\
   │  ├─ ARCHITECTURE.md      # 本总架构/规划树
   │  ├─ MODULE_CONTRACTS.md  # 内部模块输入输出
   │  └─ DATA_MODEL.md        # PostgreSQL/MinIO
   ├─ interfaces\
   │  ├─ HARBOR_EXECUTION.md      # ExecutionBackend 与 Harbor Job/Trial 映射
   │  ├─ CODEX_AUTHENTICATION.md  # Codex 认证、凭据所有权和秘密边界的唯一事实源
   │  ├─ RUNNER_PROTOCOL.md       # 自研 Agent/后备进程协议
   │  ├─ HTTP_API.md              # Web/API 契约
   │  └─ FRAMEWORK_INTERFACES.md  # 真实上游接口映射
   ├─ research\  # 官方资料和相似项目的查证记录
   ├─ operations\
   │  ├─ LOCAL_DOCKER_ENVIRONMENT.md # 本机 Docker/WSL 的已测环境事实
   │  └─ REMOTE_TEAM_ACCESS.md       # 私有远程入口、校园网/VPN共存和最小暴露面
   ├─ actions\   # 每次修改的行动和验证记录
   └─ adr\       # 仅记录难以逆转且已作出的架构决定
```

## 9. 设计模式关系

| 模式 | 参与路径 | 角色关系 | 目的 |
|---|---|---|---|
| Adapter | `ports/execution.py` + `adapters/execution/harbor/**` + `adapters/execution/process.py` | `ExecutionBackend` 定义小 interface；Harbor 为主 Adapter，Process 为验收失败时的替代 Adapter | Harbor 复杂性只集中在一个 seam，替换不波及业务 |
| Factory/Registry | `adapters/agents/registry.py` + `adapters/agents/manifest.py` | Registry 只把审核通过的配置转换为 Harbor AgentConfig；manifest 解析不执行代码 | 避免任意命令执行和 Orchestrator 条件分支 |
| Repository | `ports/repositories.py` + `adapters/persistence/postgres.py` | 应用层依赖持久化接口；PostgreSQL 实现事务和领取 | 测试可用 Fake，SQL 不散落 |
| State | `domain/job.py` + `domain/run.py` + PostgreSQL 状态约束 | 统一规定允许的 Job/运行迁移；API/Worker/数据库复用 | 防止各层对状态各自解释 |
| Command | `application/submit_job.py` + `application/approve_job.py` | 提交命令只冻结请求；批准命令只作所有者决定并排队；两者都不执行 Harbor | 权限决定和重型执行之间有明确 seam，Worker 无法绕过批准 |
| Composition Root | `delivery/http/app.py` | 唯一位置组装 ports 与生产 Adapters | 依赖构造不散落在业务逻辑 |

暂不引入装饰器、事件总线、CQRS、微服务或 Kubernetes。若未来出现真实变化点，再通过 ADR 和行动文档讨论。

## 10. 当前风险和控制

| 风险 | 影响 | 当前控制 |
|---|---|---|
| SWE-Gym 是数据、环境和多仓库材料，不是单一应用包 | 初学者容易寻找不存在的一键接口 | [`DEPENDENCIES.md`](../dependencies/DEPENDENCIES.md) 固定来源与版本；[`FRAMEWORK_INTERFACES.md`](../interfaces/FRAMEWORK_INTERFACES.md) 固定真实数据/Harness seam |
| Windows + Docker Desktop 与上游 Linux 代码差异 | Fork 使用 Linux `resource`、Docker 等能力 | Worker 运行载体先做 gold patch 最小实验，不先宣称跑通 |
| 任务镜像占磁盘、构建慢 | 一次加载大题库不可行 | 首月只登记少量任务，显式缓存策略和磁盘证据 |
| 云端 Agent 必须联网，而公开题目的原 PR 也可能在线 | 闭卷可能被运行时查答案，开卷工具能力也可能不等价 | 闭卷仅放行模型端点并禁用 Web 工具；开卷单列实验榜并记录网络/工具配置，精确代理待实测 |
| 不可信仓库和 Agent 代码 | 主机与凭据泄漏 | 固定登记 Agent、双沙箱、最小挂载、秘密脱敏，不接受任意仓库执行 |
| Codex 个人登录凭据进入临时 Trial、日志、轨迹或制品 | 个人账号被盗用，且评测证据不再适合共享 | 执行节点最小临时注入；日志脱敏；明确排除 `auth.json`、`$CODEX_HOME` 和秘密目录；成功、失败、超时路径都销毁容器与可写层 |
| Harbor `TrialResult` 没有标准 `model_patch` | 无法把 Agent 结果交给固定 Fork | 原型必须在清理前提取并校验 patch artifact；缺失即失败，不猜补丁 |
| Harbor 接口升级或 Job 目录格式变化 | Adapter 漂移、历史不可复现 | 固定完整 commit；原始 config/result 入 MinIO；升级重跑契约测试 |
| 多 Agent×多任务导致 Job 很长 | 笔电运行数小时且磁盘增长 | 创建前显示 Trial 数；预设小批量；并发 1；耗时只按真实历史估计 |
| Aider 无结构化工具事件 | 过程指标不能完全同口径 | 缺失标为“不支持/未知”，不伪造 0 |
| Codex/Claude/Aider 外部接口和许可会更新 | Adapter 漂移、费用或认证变化 | 固定版本、官方核验、四层测试、历史配置不覆盖 |
| LLM Judge 随机和有偏 | 归因不可当测试事实 | 保存模型/Prompt/证据/原始响应，人工抽检，分层展示 |
| 范围仍偏大 | 一个月可能闭环不足 | Mock 只测软件分支；交付闭环优先一条真实任务 + 一个真实 Agent + 固定 Fork，再扩展 Agent |
| 校园网 CGNAT/防火墙不允许入站端口 | 协作者无法通过公网地址稳定访问评测机 | 不做路由器端口映射；采用只需出站连接的私有覆盖网络候选，入口只到 Web，实测直连/中继 |
| 现有外网 VPN 与私有覆盖网络冲突 | Tailscale 地址或流量被全隧道、kill switch、防火墙拦截 | 不启用 Tailscale exit node；优先让现有 VPN 排除 Tailscale 应用/`100.64.0.0/10`，用 `tailscale netcheck/status` 双机实测；不兼容才评估 Cloudflare Tunnel |
| 远端成员越权批准或直接触发 Worker | 消耗所有者账号、费用和本机资源 | 网络准入不代替应用授权；只有所有者角色能批准，Job 审计记录决定者和时间，Worker 仅领取 `QUEUED` |

## 11. 当前验证策略

实现阶段按以下门槛推进：

1. **本机门槛**：Docker/WSL 环境事实见 [`LOCAL_DOCKER_ENVIRONMENT.md`](../operations/LOCAL_DOCKER_ENVIRONMENT.md)；真实任务继续并发 1。
2. **Harbor 门槛**：从固定 revision 的 `SWE-Gym/SWE-Gym-Lite` 选择 1～3 道真实任务运行 Trial，验证 patch、轨迹、资源/网络和清理；未通过则触发后备 Adapter 决策。
3. **框架门槛**：同一 SWE-Gym 任务由固定 Fork 验证 gold、空和错误 patch；Harbor reward 不参与结论。
4. **真实 Agent 门槛**：首先由真实 Codex 完成 Issue→Harbor→patch→固定 Fork 的 E2E；Mock 结果不得进入交付证据，其他 Agent 在此后扩展。
5. **隔离门槛**：验证 CPU/内存/PID/超时/网络/挂载/清理和秘密不泄漏；首次真实 Codex Trial 前后人工检查容器、可写层、日志、轨迹、MinIO 和 PostgreSQL 均无凭据内容或真实路径。
6. **持久化门槛**：双 Worker 不重复领取同一 Job，单机不同时执行两个重型 Job，部分 Trial 完成时证据不丢失。
7. **产品门槛**：远端可信协作者创建 Job 后只能看到 `AWAITING_OWNER_APPROVAL`；所有者拒绝后不能执行，批准后才进入 `QUEUED`；随后能按 `job_id` 看总进度，并按 `run_id` 看 patch、轨迹、测试、Judge 和人工复核。
8. **赛道门槛**：闭卷/开卷、网络策略和工具配置不会跨赛道混分；`internal_test` 不进入任何正式排行。
9. **远程接入门槛**：在评测机 VPN 开启和关闭两种情况下做双机测试；确认获准成员只能访问 Web，同源 API 可用，非成员以及 PostgreSQL、MinIO、Docker/Worker 端口不可达；记录连接是 direct 还是 relay。

每次实际实现前使用 `action-document`；实际检查结果必须写回行动文档，不把“计划测试”描述成“已经通过”。

## 12. 下一轮讨论队列

按架构影响排序，一次讨论一个：

1. 固定 Codex CLI 项目版本、模型 ID 和端点白名单，并实测 Harbor 容器内 ChatGPT 登录 Token 刷新、日志脱敏及成功/失败/超时清理路径。
2. 读取并固定 `SWE-Gym/SWE-Gym-Lite` 的不可变 revision、真实 split 和 1～3 个具体任务；这是技术核验，不让用户猜字段。
3. 定义 `agent-exam.yaml` 的最小字段，确保提交者不必直接编写 Harbor 配置。
4. Harbor/Worker 作为宿主 Python 进程还是挂载 Docker Socket 的容器；用本机原型裁决。
5. 可信用户的最小登录实现，以及提交者、评测机所有者、管理员、评审者的角色权限；尤其要固定所有者身份怎样绑定和恢复。
6. Judge 是否进入总分，还是只做失败归因。
7. 工具调用、token、耗时只展示，还是形成独立效率分；缺失口径怎样公平展示。
8. 开卷实验榜采用统一的平台 Web 工具，还是允许各 Agent 原生搜索工具。
9. 私有远程入口是否最终采用 Tailscale Serve；先取得现用 VPN 产品/模式并完成校园网双机共存测试，失败时再评估 Cloudflare Tunnel + Access。

## 13. 变更记录

- 2026-09-01：创建初版，记录单机、SWE-Gym/SWE-Bench-Fork、双沙箱和候选文件树。
- 2026-09-01：确认固定登记 Agent、排行榜按完整 Agent 配置、四类 Adapter 目标和 Claude Code 黑盒接入边界。
- 2026-09-01：用户接受单机模块化单体总体方案；确认 FastAPI、Python Worker、PostgreSQL 队列和不引入首版微服务/Redis/Celery。
- 2026-09-01：重构为清晰总览；把模块、Runner、HTTP、数据和真实上游接口拆为各自唯一事实源，并更新规划文件树和文档导航。
- 2026-09-02：确认闭卷主排行榜和开卷实验榜；两者使用相同确定性判卷，但按赛道、网络和工具配置严格分开。
- 2026-09-02：新增依赖唯一事实源；确认本地 `framework/` 不进入 AgentExam 主仓库，公开接口证据改用固定提交链接。
- 2026-09-03：确认 PostgreSQL 平台 Job 队列 + Harbor Execution Backend + 固定 SWE-Bench-Fork 判卷；一个 Job 可含多 Agent×多任务，单机 Trial 并发固定 1，Mock 仅限内部测试，并记录 Harbor 原型退出条件。
- 2026-09-04：确认首个真实原型使用 `SWE-Gym/SWE-Gym-Lite` 的 1～3 道任务；revision、split 和具体实例仍须读取真实元数据后固定。
- 2026-09-04：确认 Codex 为首个真实原型 Agent；认证采用评测机所有者的 ChatGPT Pro `auth.json`，当前仅该笔电作为正式真实评测节点；CLI 项目版本、模型、端点和容器运行仍待固定或实测。
- 2026-09-04：确认个人凭据不得共享、进入业务请求、数据库或制品；Kimi/DeepSeek 只作为独立 Agent Configuration，不得在 Trial 内静默回退。
- 2026-09-04：工作区由含中文路径迁移至 `E:\9.1agent_exam`；项目内容、Git 状态和远程仓库保持不变。
- 2026-09-05：确认远端协作者提交的正式真实 Job 必须先处于 `AWAITING_OWNER_APPROVAL`，只有评测机所有者批准才能进入 `QUEUED`；当前单机平台只在评测机在线时可用，并新增校园网/VPN私有接入候选与验证门槛。
