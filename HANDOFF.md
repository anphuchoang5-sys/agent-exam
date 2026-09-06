# AgentExam 架构讨论 Handoff

> 交接时间：2026-09-06
>
> 当前阶段：长期目标进行中。Harbor 结果映射、薄进程 Adapter、有界日志、宿主进程树、真实 collect-patch 四场景和外层超时后的精确 Compose 清理已通过无模型检查；固定 Fork 与真实 Codex Trial 尚未完成
>
> 用途：帮助从 `E:\9.1agent_exam` 打开的下一条 Codex 任务恢复上下文
>
> 重要限制：本文是持续更新的恢复入口，不替代各专题唯一事实源；本轮对账结果见第 6 节。

## 1. 为什么需要这份 Handoff

原任务正在用初学者能理解的方式讨论 AgentExam 的架构，并持续把确认结果同步到架构、依赖和接口文档。过程中 Codex 在含中文字符的工作区路径下出现 Windows 沙箱初始化错误，随后项目整体迁移：

```text
E:\9.1实训  →  E:\9.1agent_exam
```

文件系统迁移、Git 状态和远程仓库完整性已经验证，但 Windows 默认沙箱的 `setup refresh had errors` 后来在英文路径重新出现，因此不能再把迁移视为故障根治。Codex 认证与单机协作方式已在 2026-09-04 对账；2026-09-05 又确认“协作者远端提交 → 评测机所有者批准 → 本机 Worker 执行”，并明确评测机必须在线。同日已实测 Docker Desktop 内部代理经 FlClash 完成通用容器 HTTPS 和固定摘要镜像拉取；这不等于 Harbor/Codex Trial 或闭卷防绕过已通过。Tailscale Serve 已作为校园网/VPN 下的私有接入实施方案，仍须安装和双机实测。

最新范围收敛为：M0 先用本机脚本跑通 Codex→Harbor→patch→SWE-Bench-Fork 单题真实闭环，不先做 Web/数据库；M1 再接 Web、PostgreSQL、MinIO、两类角色和所有者批准，完成 Codex-only MVP；之后接 Aider、Claude Code；自研 Agent 降为 P2，只保留 Python 进程 Interface 和 DeepSeek/Kimi 安全接缝。Quality Judge 的触发、清洗、四项 rubric、匿名反序双评和循环赛已经固定；过程指标只展示；MVP 只闭卷；取消/中断不自动重试；任务原始 JSON、制品保留和大小上限也已确认。

2026-09-05 至 09-06 已按用户授权启动长期 M0 目标。已完成 Git/固定依赖核验、Harbor 安装、固定 SWE-Gym-Lite 数据与镜像、`apps/backend` 基础领域/Ports/Task Adapter、Harbor 配置、patch 契约、严格结果映射、有界进程执行与超时清理。生产执行器同时排空 stdout/stderr，每路最多持久化 50 MiB；日志线程有总收束期限，Windows 可定向取消仍阻塞的同步读，未完整收束会显式告警。交接前最新快速基线为 format/lint/strict mypy 全通过、unit + contract `44 passed, 7 deselected in 6.67s`；固定摘要、禁网的 collect-patch 四场景为 `4 passed in 5.91s`。真实阻塞 collect 探针先证明强杀会留下 1 个容器、1 个网络和 1 个本地镜像，修复后公开 Adapter 只按本 Job Trial 身份精确清理 project label，证据 `runtime/prototype/m0-harbor-timeout-green-20260906-02` 为 `1 passed in 49.47s`，前后 Docker 对象数均为 `18/5/15/21`；正常 NOP 与真实父子进程回归分别为 `1 passed in 18.87s`、`1 passed in 1.34s`。固定 Fork Evaluator、M0 Composition Root 和真实 Codex Trial 仍未完成。所有事实、失败和命令边界见当前行动记录 [`docs/actions/2026-09-05-m0-codex-harbor-implementation.md`](docs/actions/2026-09-05-m0-codex-harbor-implementation.md)。下一窗口不得重建 Harbor、重写现有执行器或重复已经通过的 NOP/patch/超时探针。

迁移证据见 [`docs/actions/2026-09-04-workspace-path-migration.md`](docs/actions/2026-09-04-workspace-path-migration.md)。

## 2. 恢复任务时先做什么

1. 确认工作区是 `E:\9.1agent_exam`，不要再使用旧路径。
2. 运行 `git status --short --branch` 和 `git log -3 --oneline`；第七个仅本地交接提交为 `aca01e7 docs: hand off verified patch scenarios`，其后的第八个本地提交主题为 `fix: clean up timed-out Harbor trials`。本次交接提交后工作区应当干净，本地预计比仍位于 `42484d8` 的 `origin/main` 领先 8、落后 0；若实际状态不同，必须先辨明后续修改，不得 reset/checkout/clean。不得自行 push，除非用户再次明确要求。
3. 按下面的层级阅读，不要只看总架构就开始修改。
4. 第 6 节所列业务规则已经同步；固定数据、镜像、Harbor 环境、结果映射、薄进程 Adapter、有界日志、宿主父子进程、collect-patch 四场景和 Harbor 外层超时精确清理已有相应证据。下一步建立固定 Fork Evaluator；不要重新下载 Harbor、重复已通过探针或重写现有模块。
5. 当前遗留项是技术核验，不得把已经确认的业务规则重新列成待决定；若实现发现必须新增顶层 Module、Interface、数据库表或目录，先说明现有职责为何不能承载并取得确认。

### 2.1 第一批：开始任何修改前必须完整阅读

| 顺序 | 文档 | 下一窗口必须了解什么 | 阅读时的注意事项 |
|---:|---|---|---|
| 1 | 本文 `HANDOFF.md` | 中断原因、对话确认事实、文档滞后点、未决问题和安全红线 | 本文是交接快照，不替代专题事实源 |
| 2 | [`docs/actions/2026-09-05-m0-codex-harbor-implementation.md`](docs/actions/2026-09-05-m0-codex-harbor-implementation.md) | 本轮实际安装、代码、固定数据/镜像、测试、失败和下一步 | 当前 M0 唯一行动记录；状态已恢复为进行中，不是完成 |
| 3 | [`docs/actions/2026-09-05-mvp-priority-product-decisions.md`](docs/actions/2026-09-05-mvp-priority-product-decisions.md) | 已确认的 MVP 顺序、两角色、Judge、闭卷、取消/恢复、任务快照与制品规则 | 业务决策事实源；没有业务代码修改 |
| 4 | [`docs/actions/2026-09-04-architecture-document-reconciliation.md`](docs/actions/2026-09-04-architecture-document-reconciliation.md) | 架构对账的实际改动、CLI 探针、沙箱偏差和验证结果 | 原计划仍保存在 `2026-09-04-handoff-document.md` |
| 5 | [`CONTEXT.md`](CONTEXT.md) | AgentExam 的领域词汇及其统一含义 | 只维护领域语言，不应从这里推断框架接口 |
| 6 | [`docs/architecture/ARCHITECTURE.md`](docs/architecture/ARCHITECTURE.md) | 系统目标、模块边界、数据流、决定表、规划文件树和待讨论队列 | 业务规则已同步；模型和容器真实运行仍待实测 |
| 7 | [`docs/architecture/MODULE_CONTRACTS.md`](docs/architecture/MODULE_CONTRACTS.md) | M0 要实现的领域对象、Execution Backend 与 Patch Evaluator 边界 | 写代码前必须按此建立依赖方向 |
| 8 | [`docs/interfaces/CODEX_AUTHENTICATION.md`](docs/interfaces/CODEX_AUTHENTICATION.md) | ChatGPT Pro `auth.json` 方案、凭据所有权和安全边界 | 禁止读取或复制凭据内容 |
| 9 | [`docs/dependencies/DEPENDENCIES.md`](docs/dependencies/DEPENDENCIES.md) | 三个固定源码提交和本地恢复方式 | 当前动态安装结果以 M0 行动记录为准，收尾时同步本文件 |
| 10 | [`docs/interfaces/HARBOR_EXECUTION.md`](docs/interfaces/HARBOR_EXECUTION.md) | M0/M1、Harbor Trial、patch、轨迹和错误映射 | NOP/mapper/有界日志/外层超时清理已实测；Codex Token 与真实 Agent 仍未实测 |
| 11 | [`docs/interfaces/FRAMEWORK_INTERFACES.md`](docs/interfaces/FRAMEWORK_INTERFACES.md) | SWE-Gym 字段、固定 Fork CLI、Harbor 与 Agent CLI 入口 | NOP 已实测；固定 Fork/Codex 仍待核验 |
| 12 | [`docs/operations/LOCAL_DOCKER_ENVIRONMENT.md`](docs/operations/LOCAL_DOCKER_ENVIRONMENT.md) | Docker/WSL、FlClash/Docker 代理、磁盘和单机限制 | 当前 Windows 系统代理已被用户关掉；只在单次探针进程注入 7890 |
| 13 | [`docs/adr/0001-use-harbor-as-execution-backend.md`](docs/adr/0001-use-harbor-as-execution-backend.md) | Harbor 主 Adapter 和固定 Fork 判卷决定 | 只有真实原型触发退出条件时才讨论 Process 后备 |

### 2.2 第二批：修改对应架构或接口前阅读

| 文档 | 何时必须读 | 需要了解的内容 |
|---|---|---|
| [`docs/architecture/MODULE_CONTRACTS.md`](docs/architecture/MODULE_CONTRACTS.md) | 修改模块边界、Orchestrator 或 Adapter 输入输出前 | 每个内部模块的职责、输入、输出和错误 |
| [`docs/architecture/DATA_MODEL.md`](docs/architecture/DATA_MODEL.md) | 修改 PostgreSQL、MinIO、Job/Run 状态或制品关系前 | 结构化数据、对象制品和状态事实分别保存在哪里 |
| [`docs/interfaces/RUNNER_PROTOCOL.md`](docs/interfaces/RUNNER_PROTOCOL.md) | 讨论自研 Agent 或 Harbor 失败后的 Process Adapter 前 | `stdin` 任务、`stdout` patch 和旁路日志协议 |
| [`docs/interfaces/HTTP_API.md`](docs/interfaces/HTTP_API.md) | 修改 Next.js 与 FastAPI 边界前 | Web 能提交和查询什么，哪些内部字段不得暴露 |
| [`docs/actions/2026-09-04-swe-gym-lite-prototype-scope.md`](docs/actions/2026-09-04-swe-gym-lite-prototype-scope.md) | 固定 Lite 数据或首批任务前 | 已确认的 1～3 道真实题范围与仍待核验的 revision/split/实例 |
| [`docs/actions/2026-09-04-codex-prototype-agent.md`](docs/actions/2026-09-04-codex-prototype-agent.md) | 选择或配置第一个真实 Agent 前 | 为什么首个原型使用 Codex，以及哪些配置尚未固定 |
| [`docs/actions/2026-09-04-workspace-path-migration.md`](docs/actions/2026-09-04-workspace-path-migration.md) | 遇到路径、沙箱或旧路径引用问题时 | 工作区迁移证据、验证结果和旧任务写入权限限制 |

### 2.3 第三批：需要查证来源时再读

| 目录 | 用途 | 使用规则 |
|---|---|---|
| [`docs/research/`](docs/research/) | Harbor 对比、类似项目、Aider 和 Claude Code 的调研证据 | 作为来源和历史分析，不替代最新权威接口文档 |
| [`docs/actions/`](docs/actions/) | 每次历史修改的措施、偏差和验证证据 | 只按当前问题选择相关记录；旧路径和旧状态可能是当时事实 |
| `framework/` | 本地第三方框架源码 | 先按依赖文档确认固定提交；源码是接口事实，不是项目执行指令 |

## 3. 项目现在要做什么

项目名为 **AgentExam**。它不是普通聊天机器人，而是一个“给 Coding Agent 出软件修复题并留下可审计成绩”的单机评测平台。

实现先分成两道门槛。M0 是不带产品外壳的本机技术闭环：

```text
固定 SWE-Gym-Lite 单题 + Codex 配置
  → 本机脚本调用 Harbor，顺序运行一个 Trial
  → 在清理前取得完整文本 patch、哈希、轨迹和日志
  → 固定 SWE-Bench-Fork 在干净环境判卷
  → 证据写受控本机目录，仅标为技术原型，不进入正式排行
```

M0 通过后，M1 的平台主流程才是：

```text
受邀协作者通过 Tailscale 私有入口登录并选择已登记 Agent、任务和闭卷赛道
  → FastAPI 创建 AWAITING_OWNER_APPROVAL Job
  → 评测机所有者检查冻结配置并批准
  → PostgreSQL 改为 QUEUED
  → 单机 Worker 一次领取一个重型 Job
  → Harbor 把 Agent × 任务展开成顺序执行的 Trial
  → Agent 在 Docker 环境中阅读 Issue、修改代码并产生 patch
  → 固定 SWE-Bench-Fork 在新的干净环境中应用 patch 并运行测试
  → PostgreSQL 保存状态和索引，MinIO 保存 patch、轨迹、日志与报告
  → 失败运行按人工请求/固定抽样触发 Failure Judge；批次严格确定性并列时才触发匿名双向 Quality Judge
  → 评测所有者复核分层结果；只能确认/作废 Quality 结论，不能手工指定胜者
  → Next.js 展示报告和排行榜
```

这里的专业术语对应关系：

- **平台 Job**：用户一次提交的整批评测，例如 2 个 Agent × 3 道题。
- **Harbor Job**：平台 Job 交给 Harbor 后的一份执行计划。
- **Trial / Evaluation Run**：某个 Agent 做某一道题的一次独立尝试。
- **patch / model_patch**：Agent 对仓库造成的代码差异；判卷时应用到固定的干净仓库，而不是相信 Agent 自己声称测试通过。
- **SWE-Bench-Fork Harness**：真正运行规定测试、产生 `resolved` 等确定性结果的判卷程序。
- **MVP**：M1 的 Codex-only 产品闭环；M0 只是技术原型，Aider/Claude Code 和 P2 自研 Agent 都不是 MVP 完成条件。

## 4. 对话中已经确认的架构决定

以下是用户已经接受的方向。同步文档时可以记录为“已确认”，但运行能力仍必须通过真实实验验证。

### 4.1 核心框架和判卷

- SWE-Gym 是项目实际使用的核心任务框架，不是只供参考的示例。
- SWE-Gym 固定提交：`b681068ca20628c6987b7416cc4cf03f06b77ba5`。
- 配套 SWE-Bench-Fork 固定提交：`242429c188fcfd06aad13fce9a54d450470bf0ac`。
- 使用 SWE-Gym 的任务语义与字段，例如 `problem_statement`、`repo`、`base_commit`、`test_patch`、`FAIL_TO_PASS`、`PASS_TO_PASS`。
- 最终正确性由固定 SWE-Bench-Fork 的真实测试决定；Harbor reward、LLM Judge 和人工解释均不能覆盖原始测试事实。
- Agent 生成环境和最终验证环境是两个逻辑上独立的干净环境，不要求长期同时保留两个运行容器。

### 4.2 Harbor 的位置

- Harbor 固定提交：`6af8d6e31eced13b93849cdf80feeadf24603d15`。
- Harbor 是正式的 **Execution Backend（执行后端）**，负责 Agent、Docker 环境、Job/Trial、轨迹和制品收集。
- Harbor 不是课程业务数据库，也不是最终判卷器。
- 平台只依赖小型 `ExecutionBackend` 接口，由 `HarborExecutionAdapter` 隐藏 Harbor 的内部类型。
- 如果真实原型不能可靠取得 patch、控制资源/网络并清理凭据，只替换执行 Adapter，不重写上层 Job、报告和 HTTP 接口。

### 4.3 单机部署和调度

- 只有一台物理评测机，不设计 Kubernetes、多机调度或分布式存储。
- 后端采用 Python + FastAPI 的模块化单体；Next.js 15 + React 19 作为 Web。
- PostgreSQL 保存业务元数据并承担平台 Job 队列；不以 Harbor Job 代替平台队列。
- PostgreSQL 保存标准化任务字段；MinIO 还按内容 SHA-256 保存不可变的原始任务 JSON。两者在同一数据同步动作中冻结。
- MinIO 保存不可变的大文件制品，例如 patch、轨迹、stdout/stderr、测试日志和 Judge 原始响应。
- 一个平台 Job 对应一个 Harbor Job；一条平台运行对应一个 Harbor Trial。
- 同时只运行一个重型平台 Job，Harbor `n_concurrent_trials=1`，Trial 顺序执行。
- Docker/WSL 内存上限已调整到 10 GB，Docker 数据已经迁到 E 盘；真实任务仍需实测资源上限，不能直接照搬 Harbor 模板的 8192 MB。

### 4.4 真实性、赛道和证据

- 正式演示、报告和排行必须来自真实 Agent、真实 Docker 执行和真实 SWE-Bench-Fork 测试。
- Mock 只允许验证平台自身的状态与错误分支，并标为 `internal_test`；不得进入正式结果。
- MVP 只启用闭卷赛道 `closed_book`：只放行模型服务所需网络，不开放一般 Web 搜索。
- 数据模型保留 `open_book_experimental` 接缝，但 MVP 禁止创建；未来启用时只使用平台统一 Web 工具并与闭卷严格分榜。
- patch、轨迹、日志、测试和运行级 Failure Judge/复核关联同一 `run_id`；跨候选 Quality Judge/复核关联 `job_id` 与不可变比较键，并引用参与的运行证据。
- 工具调用、token、耗时等过程指标只展示、不参与排序；缺失显示未知，不能伪造为 0。
- patch 超过 256 KiB 警告；超过 1 MiB 或包含二进制变更时明确判为无效输出，不得静默截断。
- 单个大体积原始日志/轨迹/Judge 制品最多 50 MiB，每运行原始制品总额 200 MiB；核心结果长期保留，大体积原始证据保留 30 天后由所有者本机命令清理，删除后仍保留哈希、大小和审计。

### 4.5 第一个真实原型

- M0 使用 `SWE-Gym/SWE-Gym-Lite` 的 1 道真实任务起步；已固定 Hugging Face revision `61231f2c90b18985b42a1419738a240085a15107`、`train` split 和 230 条记录。
- 固定 Parquet 位于忽略路径 `runtime/cache/swe-gym-lite/61231f2c90b18985b42a1419738a240085a15107/train-0000.parquet`，大小 `931,193` bytes，SHA-256 `f3a7cd934e8cc523b6053298d0abb2c82fd7db2b83f9f2ccba5944545aaa4eb1`。
- 首题候选已经选为 `python__mypy-15413`，仓库 `python/mypy`，base commit `e7b917ec7532206b996542570f4b68a33c3ff771`。它是 Harbor 自带 SWE-Gym README 使用的单题示例，但尚未运行，故仍称候选。
- 候选镜像已固定并拉取为 `xingyaoww/sweb.eval.x86_64.python_s_mypy-15413@sha256:f069dfc74592d438ad870bbc6dfb369bff1b125d21237ead49190b414f5f3456`；本机镜像大小 `2,511,912,411` bytes。无网络探针确认 `/testbed` HEAD 正是固定 base commit，容器内有 bash/Git 但没有 Node/npm。
- 首个真实 Agent 使用 Codex，优先复用 Harbor 内置 Codex Adapter。
- M0 先用本机脚本跑通 Issue → Harbor → patch → 固定 SWE-Bench-Fork，不先实现 Web/PostgreSQL/MinIO/审批；M1 再完成 Codex 平台闭环，之后依次扩展 Aider、Claude Code，最后才是 P2 自研 Agent。
- 固定 Harbor 已安装成功并可执行 `harbor --version`，返回 `0.22.0`。宿主 Codex 当前为 `0.153.0`；项目配置映射要求显式提供 Codex 版本、模型和 reasoning effort，不存在生产默认值。把 `0.153.0` 固定为 M0 Agent 版本及选择实际模型仍需用户确认并通过容器实测。
- 固定 Harbor 自带 `adapters/swegym`，但它没有给 `load_dataset()` 传不可变 revision，还会把完整原始 datum 写到任务 `tests/config.json`。项目必须保留规划中的薄 `adapters/tasks/swe_gym.py`：复用镜像命名/任务约定，直接读已校验 Parquet，只向 Harbor 任务写公开字段；隐藏字段只交给固定 Fork Evaluator。
- 固定 Harbor 单步顺序已从源码确认：Agent → 日志同步 → `[[verifier.collect]]` → artifact 收集 → 可选 verifier。`verifier.disable=true` 时仍执行 collect/artifact，且任务可不包含 `tests/`。项目已实现 collect hook：先为未跟踪文件执行 intent-to-add，再相对固定 `base_commit` 导出完整 diff，并记录哈希、大小、二进制标志；真实 NOP 已覆盖空 patch，固定摘要、禁网容器已覆盖普通修改、新建、删除和 Agent 自行 commit。

### 4.6 Codex 认证与多人协作

这是用户已经确认并同步到权威文档的部分：

- 首个 Codex 原型优先使用评测机所有者本人通过 ChatGPT Pro 登录产生的 `auth.json`，暂不因为 OpenAI API 费用另购 OpenAI API 用量。
- `auth.json` 是密码级个人凭据，绝不能发给协作者、提交 Git、写入 PostgreSQL/MinIO，或进入日志和制品。
- 正式真实 Trial 默认只在用户这一台评测机上触发；协作者可以完整开发项目，但不需要取得用户凭据，也不必在各自电脑上运行真实 Codex Trial。
- 协作者可以远端创建 Job，但初始状态只能是 `AWAITING_OWNER_APPROVAL`；只有评测机所有者批准后才进入 `QUEUED`，本机 Worker 不得领取待批准/已拒绝 Job。
- 协作者使用平台时，评测机和本机平台必须在线；离线时当前架构不提供云端常驻入口。
- 平台只有 `collaborator` 与唯一 `owner` 两类人员角色；不开放公共注册，所有者通过评测机本地引导建立/恢复账号，再在应用内邀请协作者，不接入邮件服务。
- 协作者只能提交和查看非秘密结果；所有者兼任批准者、成员/配置管理员、制品清理者和人工复核者。角色来自应用可信会话，不来自请求正文或 Tailscale 设备身份。
- 私有远程入口只暴露 Web，不暴露 FastAPI 原始端口、PostgreSQL、MinIO、Docker、Worker 或凭据路径。Tailscale Serve 已选为实施方案，需与 FlClash/VPN 双机实测；评测机必须开代理上外网不会改变该拓扑。
- 如果协作者要在自己的机器做非正式开发/冒烟验证，必须使用自己的 ChatGPT 登录或自己获授权的 API Key；其结果不进入正式排行。
- P2 自研 Agent 的模型提供方只允许 DeepSeek 或 Kimi，二者必须形成独立 Agent Configuration；真实 Key 只由正式评测机所有者的本机可信配置持有，不进入被测 Agent，且不能在同一次 Trial 中作为 Codex/OpenAI 的静默回退。该路径不阻塞 MVP。
- 权威专题文档为 [`docs/interfaces/CODEX_AUTHENTICATION.md`](docs/interfaces/CODEX_AUTHENTICATION.md)。
- 远端接入权威运维文档为 [`docs/operations/REMOTE_TEAM_ACCESS.md`](docs/operations/REMOTE_TEAM_ACCESS.md)。

### 4.7 Judge、取消与恢复

- Failure Judge 只解释失败证据，不参与排名，也不改变 `resolved`。
- Quality Judge 只有在完整可比条件一致、逐题 `resolved` 向量完全相同，并且至少存在一道共同通过且有有效 patch 的题时才触发。
- Quality 输入只取共同通过题的任务需求、最终 patch、测试摘要和必要轨迹摘要，并先裁剪、脱敏、去重、限量；不向 Judge 暴露 Agent 身份或 A/B 映射。
- 每对候选按任务匹配与最小修改、可读性与可维护性、稳健性、副作用风险四项比较；A/B 与 B/A 各跑一次，两次一致才有胜者，否则该对并列。多 Agent 循环赛胜 1、平 0.5、负 0。
- 所有者可确认或作废 Quality 结论；作废恢复并列，不能手工选择胜者。
- `AWAITING_OWNER_APPROVAL`/`QUEUED` 可直接取消；执行中进入 `CANCEL_REQUESTED`，停止后续 Trial，当前 Trial 最多运行到冻结超时。Worker、宿主或 Harbor 中断不自动续跑/重试；重试创建新 Job 和新证据链。

## 5. 已验证的本机和仓库事实

- 当前工作区：`E:\9.1agent_exam`。
- 旧工作区 `E:\9.1实训` 已不存在。
- Git 分支：`main`。
- 本轮原始基线：本地 `main` 与 `origin/main` 均为 `42484d8472b3a258c49ca22d85a7b8a8b5166de2`（`docs: finalize evaluation MVP architecture`）。第一次交接创建了本地提交 `0caedda`；恢复时再次 `git fetch origin --prune`，本地/远端领先落后为 `1/0` 且工作区干净。
- 第二次交接把第一批 M0 代码、同步文档和锁文件创建为本地提交 `37f04d2`；第三次交接把 NOP 探针、artifact/config 变更和当时尚未完成的结果映射草稿创建为本地提交 `8e53f47`；第四次交接把 mapper 修复、映射后 NOP 和薄进程 Adapter 创建为本地提交 `40c6f6c`；第五次交接把有界日志、进程树清理和真实有界 NOP 创建为本地提交 `e629eda`；第六次交接把 collect-patch 四场景测试和交接文档创建为 `a9306b7`。本轮已从 `a9306b7` 恢复、取得四场景真实通过证据并同步 8 份权威/交接文档，将以主题 `docs: hand off verified patch scenarios` 创建第七个本地提交；这些提交均未 push。新窗口必须以实际 `git log` 和 `git status` 为准。
- 远程仓库：`https://github.com/anphuchoang5-sys/agent-exam.git`。
- 工作区迁移后默认沙箱曾短暂通过，但本窗口在英文路径连续重现 `setup refresh had errors`；路径迁移不能视为根治，详见路径迁移行动记录的后续复核。
- 本轮 `codex --version` 返回 `codex-cli 0.153.0`；这只证明当前宿主 CLI 能启动，不代表 Harbor 容器认证、模型或 E2E 已通过。旧文档中的 `0.142.0` 是 2026-09-04 当时的动态探针。
- Docker/WSL 的 2026-09-03 实测事实见 [`docs/operations/LOCAL_DOCKER_ENVIRONMENT.md`](docs/operations/LOCAL_DOCKER_ENVIRONMENT.md)；其中磁盘余量等数值会变化，引用前应重新检查。
- Docker Desktop `4.38.0` / Client、Server `27.5.1` 当前可响应，Docker 可见内存 `10,429,505,536` bytes；第五次恢复时 E 盘可用 `19,594,498,048` bytes。当前 Windows `ProxyEnable=0` 且 `ProxyServer` 为空，FlClash 进程仍运行；Docker manifest/镜像拉取和项目 `uv` 网络步骤仅对单次进程注入 `HTTP_PROXY/HTTPS_PROXY=http://127.0.0.1:7890` 后成功。不要擅自重新开启用户的系统代理。
- `framework/swe-gym`、`framework/swe-bench-fork`、`framework/harbor` 都已恢复到依赖事实源固定提交并保持干净；它们与 `runtime/` 都被主仓库忽略。
- Harbor 根 `.venv` 已按其 `uv.lock` 和 `huggingface` extra 安装成功。由于 `litellm==1.93.0` 在该锁中没有 Windows wheel，使用项目内隔离 `rustc/cargo 1.98.1` 加 Visual Studio 2022 C++ 环境源码编译，单次实际耗时 275 分 06 秒；不要删除或无理由重建 `framework/harbor/.venv`、`runtime/tools`、`runtime/cache/uv`。
- `apps/backend` 已建立 Python 3.13 项目，`uv.lock` 已生成；固定 Task Adapter、领域对象、两个 Ports、Harbor 配置/结果映射、collect hook、patch 校验、薄进程 Adapter、有界双流日志、宿主进程树和超时后的精确 Compose 清理均已实现。最新 `ruff check`、严格 `mypy` 均通过；unit + contract 为 `44 passed in 6.60s`，所有项目 Python 文件不超过 200 行、每层目录不超过 8 个文件。`tests/integration/test_collect_patch_scenarios.py` 已在固定摘要、`--network none` 容器中真实得到 `4 passed in 5.91s`，专用容器无残留。
- 固定 Harbor NOP Docker Trial 已真实通过：原始链路证据 `runtime/prototype/m0-harbor-nop-20260906-04` 为 `1 passed in 18.40s`；正式 mapper 接入后的证据 `runtime/prototype/m0-harbor-nop-20260906-05` 为 `1 passed in 20.56s`。后者把真实 Job/Trial 严格映射为 `COMPLETED` 与可信 0-byte patch。两者都只是无模型 NOP，不代表真实 Codex 或 SWE-Bench-Fork E2E 通过。
- `result_mapper.py` 已拆分为不超过 200 行的流程映射与 `result_values.py` 纯值转换，修复 `slots=True` 运行时缺陷并覆盖成功、缺失、异常、非零进程保留完成 Trial、usage/时间等分支。
- `HarborExecutionAdapter` 已实现；内部 `process_runner.py`/`process_evidence.py` 使用 `Popen` 并发排空双流、每路 50 MiB 硬上限、显式截断 manifest 和结构化告警。日志收束不再使用无限 `join()`；后代保持管道开放时会在固定期限返回 `HARBOR_LOG_CAPTURE_INCOMPLETE`。公开 Adapter 的真实 NOP 阻塞 collect 探针已复现并修复强杀后的 Compose 残留；清理只接受本 Job 下目录名与 `trial_name` 一致的身份，按 Harbor 相同净化规则生成精确 project label，不执行全局 prune。正常 NOP 与父子进程回归也已通过。
- 截至交接时，没有读取 `auth.json` 内容，也没有发起真实模型调用或运行固定 SWE-Bench-Fork 判卷。固定 Fork Evaluator 与 M0 Composition Root 尚未实现。

## 6. 文档对账完成状态

2026-09-04 已完成认证对账，实际过程见 [`docs/actions/2026-09-04-architecture-document-reconciliation.md`](docs/actions/2026-09-04-architecture-document-reconciliation.md)。2026-09-05 的审批与远程接入对账见 [`docs/actions/2026-09-05-remote-submission-owner-approval.md`](docs/actions/2026-09-05-remote-submission-owner-approval.md)；Judge、自研 Agent 与凭据形成过程见 [`docs/actions/2026-09-05-judge-custom-agent-credential-decisions.md`](docs/actions/2026-09-05-judge-custom-agent-credential-decisions.md)；本轮最终收敛与全量同步见 [`docs/actions/2026-09-05-mvp-priority-product-decisions.md`](docs/actions/2026-09-05-mvp-priority-product-decisions.md)。后者优先于历史行动记录中的旧“首版/待确认”措辞。

| 文件 | 已完成的同步 | 仍保留的边界 |
|---|---|---|
| [`docs/actions/2026-09-05-m0-codex-harbor-implementation.md`](docs/actions/2026-09-05-m0-codex-harbor-implementation.md) | 记录 Git 基线、固定数据/镜像、Harbor 安装、NOP 探针、mapper/进程 Adapter、collect-patch 实测和当前措施 | 已恢复为进行中；四场景通过仍不等于 M0 完成 |
| [`CONTEXT.md`](CONTEXT.md) | 新增协作者、评测所有者、MVP 和取消请求；保留 Agent Configuration 与 Failure/Quality Judge 词义 | 不承载实现和部署细节 |
| [`docs/architecture/ARCHITECTURE.md`](docs/architecture/ARCHITECTURE.md) | 已固定 M0→M1→Aider/Claude→P2、自研降级、两角色、闭卷、Judge、任务快照、取消/恢复与制品策略 | CLI/模型版本、Harbor/Codex Trial 及 Tailscale/VPN 仍待技术实测 |
| [`docs/dependencies/DEPENDENCIES.md`](docs/dependencies/DEPENDENCIES.md) | 依赖恢复按 M0/M1/后续/P2 分层，并同步固定数据、Harbor 安装、Python 项目锁和摘要镜像状态 | 模型 ID、Codex 容器安装和固定 Fork 运行兼容性未验证 |
| [`docs/interfaces/HARBOR_EXECUTION.md`](docs/interfaces/HARBOR_EXECUTION.md) | M0/M1 验收、patch/制品上限、NOP/mapper、有界日志、外层超时清理、取消/中断和 P2 接缝已写明 | Codex Token、脱敏与真实 Agent/判卷未验证 |
| [`docs/interfaces/RUNNER_PROTOCOL.md`](docs/interfaces/RUNNER_PROTOCOL.md) | 明确是 P2/后备协议；固定文本 patch、二进制拒绝、大小和日志限额 | P2 完整 schema、Python/依赖锁和包装不阻塞 MVP |
| [`docs/interfaces/FRAMEWORK_INTERFACES.md`](docs/interfaces/FRAMEWORK_INTERFACES.md) | 已记录真实上游入口、任务双层存储、M0/M1 顺序，并同步真实 Harbor NOP/mapper/有界执行与超时清理状态 | Codex 容器与固定 Fork 仍未验证 |
| [`docs/interfaces/CODEX_AUTHENTICATION.md`](docs/interfaces/CODEX_AUTHENTICATION.md) | 凭据事实源区分 M0/M1 Codex `auth.json` 与 P2 自研受控访问 | 不记录真实凭据路径、内容或 Token；P2 宿主/侧车不阻塞 MVP |
| [`docs/actions/2026-09-04-codex-authentication-policy.md`](docs/actions/2026-09-04-codex-authentication-policy.md) | 实际文件树和验证结果已补齐 | 历史行动记录只说明本次政策落盘，不替代认证事实源 |
| [`docs/architecture/MODULE_CONTRACTS.md`](docs/architecture/MODULE_CONTRACTS.md) | 两角色、双用途 Judge、取消/恢复、制品策略、闭卷 MVP 和 P2 自研职责已同步 | 登录技术落点、Judge 模型/Prompt 与 P2 访问部署仍待实测 |
| [`docs/architecture/DATA_MODEL.md`](docs/architecture/DATA_MODEL.md) | 任务原始快照、审批/取消状态、Job 级 Quality、保留/删除审计和大小规则已同步 | 账户现有承载点、精确 SQL/索引/租约仍待实现验证 |
| [`docs/interfaces/HTTP_API.md`](docs/interfaces/HTTP_API.md) | 两角色权限、MVP 禁用自研/开卷、取消、Judge、指标和制品删除语义已同步 | 账户/会话的精确路由和现有承载位置仍待核验，接口尚未实现 |
| [`docs/operations/LOCAL_DOCKER_ENVIRONMENT.md`](docs/operations/LOCAL_DOCKER_ENVIRONMENT.md) | 通用 Docker/FlClash 出站、当前资源、固定摘要镜像、Harbor NOP、宿主进程树与超时 Compose 清理已记录 | Codex Trial 与闭卷阻断未实测；P2 受控访问不阻塞 MVP |
| [`docs/operations/REMOTE_TEAM_ACCESS.md`](docs/operations/REMOTE_TEAM_ACCESS.md) | Tailscale 实施方案、FlClash/VPN 共存、两角色和双层账户标识已记录 | Tailscale 尚未安装/双机实测；应用登录未实现，真实页面不能开放 |
| [`docs/actions/2026-09-05-remote-submission-owner-approval.md`](docs/actions/2026-09-05-remote-submission-owner-approval.md) | 记录本轮范围、实际变更和文档验证证据 | 不把文档验证写成网络或真实 Trial 已通过 |
| [`docs/actions/2026-09-05-judge-custom-agent-credential-decisions.md`](docs/actions/2026-09-05-judge-custom-agent-credential-decisions.md) | 记录本次同步范围、文件树、偏差和验证证据 | 不替代各专题权威事实源 |
| [`docs/actions/2026-09-05-mvp-priority-product-decisions.md`](docs/actions/2026-09-05-mvp-priority-product-decisions.md) | 记录本轮最终决策、最小修改范围和验证结果 | 本轮最新行动记录；不把文档同步写成代码或真实 Trial 已完成 |
| 根目录 `AGENTS.md` | 已加入最小修改原则和新增顶层架构元素前的确认纪律 | 后续若用户要求删除、清空或重写，必须作为单独选择处理 |
| 2026-09-04/05 的已提交审批与远程接入文档 | 已包含在 `a2e85bb` 与 `ef6f22e` | 两个提交已推送到 `origin/main`；本轮同步仍是新的本地可审阅 diff |

历史行动文档中的 `E:\9.1实训` 是当时真实路径，不应为了表面一致而批量改写。只有描述“当前工作区”的活动文档需要使用新路径。

## 7. 当前 Git 工作区，禁止误删

本轮开始前的七次本地提交为：

- `0caedda docs: hand off M0 implementation progress`
- `37f04d2 feat: add M0 evaluation foundations and handoff`
- `8e53f47 wip: hand off Harbor result mapping progress`
- `40c6f6c wip: hand off Harbor adapter progress`
- `e629eda wip: hand off bounded Harbor process progress`
- `a9306b7 wip: hand off collect patch scenarios`
- `aca01e7 docs: hand off verified patch scenarios`

本轮恢复时的基线为：

```text
## main...origin/main [ahead 7]
```

`aca01e7` 后长期目标曾恢复，本轮完成日志有界收束、精确 Compose 超时清理、相应单元/真实集成测试和权威文档同步。上述内容与本 Handoff 以主题 `fix: clean up timed-out Harbor trials` 创建第八个本地提交；提交后工作区应干净，本地预计为 `main...origin/main [ahead 8]`。如果实际状态不同，先查 `git log -3 --oneline` 与 status，区分用户或其他窗口的后续修改；不得使用 `git reset --hard`、`git checkout --` 或清理未跟踪文件。当前没有 push；远端停在 `42484d8`，除非用户或其他窗口后来明确推送。

## 8. 待技术核验

业务范围和产品行为已经确认。以下只能用查代码/配置、原型和测试补齐，不能重新解释成业务待决定：

1. 建立固定 Fork 的独立、锁定环境和 `adapters/evaluation/swe_bench.py`；在同一候选题上先跑 gold、空、错误 patch。固定 Fork 顶层 `run_evaluation.py` 无条件导入 Linux `resource`，Windows 宿主直接运行的兼容性仍须实测，或用不修改上游源码的受控 Linux 载体解决。
2. 补齐 M0 Composition Root/脚本与受控证据 manifest；先让上述无模型路径全部通过，并复核容器、网络、资源和清理。
3. 真实 Trial 前按 `AGENTS.md` 一次只向用户确认一个会影响评测身份的选择：先确认 Codex CLI 固定版本，再确认当前可用模型与 reasoning effort。不得沿用旧记忆或把测试占位符 `model-must-be-confirmed` 当生产默认值。
4. 容器内验证 Codex 安装、端点白名单以及 `auth.json` Token 刷新、脱敏和成功/失败/超时销毁路径。任何时候只检查凭据文件存在性/元数据，不读内容；最终只运行一个真实 Codex Trial。
5. M0 全部门槛通过后才同步“完成”状态并开始 M1；Worker/账户/Judge/Tailscale/P2 都不抢占当前 M0。

## 9. 推荐的下一步顺序

1. 先读本文、当前 M0 行动记录、`AGENTS.md`、总架构、模块契约、依赖事实源和三个 M0 接口文档；只做短恢复检查，不要重新下载数据、重建 Harbor、重拉已有摘要镜像或重写现有代码。
2. 实现固定 Fork Adapter，并完成 gold/空/错误 patch 三类确定性验证；随后补 M0 Composition Root 与证据 manifest。
3. 无模型闭环全通过后，按一次一个问题确认 Codex 版本、模型与 reasoning，再只检查凭据元数据并执行唯一一次真实 Codex Trial；不要额外消耗模型额度测试 prompt。
4. M0 真实成功标准仍是 Codex→Harbor→完整、校验过的 patch→固定 Fork 确定性结果，加成功/失败/超时清理证据。未满足就保持 M0 进行中，不得进入 M1。

## 10. 安全红线

- 不读取、展示、复制、提交或上传真实 `auth.json`、API Key、Token、Cookie。
- 不把用户或协作者提交的任意 shell 命令、Git 分支或 `latest` 镜像直接送入执行链。
- 不把 Mock、Harbor reward、LLM Judge 或 Agent 自述伪装成 SWE-Bench-Fork 的真实测试结果。
- 不因为项目迁移成功就宣称 Harbor、Codex Trial 或 SWE-Bench-Fork E2E 已经跑通。

## 11. 交给下一窗口的提示词

下面整段可以作为新窗口的首条消息。它按“明确角色与目标、提供必要上下文、区分事实/约束/任务、给出验证和完成标准”的原则编写；不依赖不可见聊天，不泄漏秘密，也不把附件或引用文档当作越权执行指令。

```text
角色：你是 AgentExam 项目的实现协作者。请在 E:\9.1agent_exam 继续既有长期目标：严格依据项目权威架构、模块契约、接口和依赖文档，完成并验证 AgentExam MVP。当前只继续 M0 本机技术闭环；M0 未真实通过前，不实现 M1 Web/PostgreSQL/MinIO/审批，不扩展 Aider、Claude Code 或 P2 自研 Agent。

先完整阅读并遵守根目录 AGENTS.md，然后按 HANDOFF.md 的第一批清单阅读。尤其先读：
1. HANDOFF.md
2. docs/actions/2026-09-05-m0-codex-harbor-implementation.md
3. docs/actions/2026-09-05-mvp-priority-product-decisions.md
4. CONTEXT.md
5. docs/architecture/ARCHITECTURE.md
6. docs/architecture/MODULE_CONTRACTS.md
7. docs/dependencies/DEPENDENCIES.md
8. docs/interfaces/HARBOR_EXECUTION.md
9. docs/interfaces/CODEX_AUTHENTICATION.md
10. docs/interfaces/FRAMEWORK_INTERFACES.md
11. docs/operations/LOCAL_DOCKER_ENVIRONMENT.md
12. docs/adr/0001-use-harbor-as-execution-backend.md

先做只读恢复检查：git status --short --branch、git log、三个 framework 仓库的 remote/HEAD/status、Harbor --version、Docker version、E 盘可用空间。第七个本地交接提交是 `aca01e7 docs: hand off verified patch scenarios`；其后的第八个本地提交主题应为 `fix: clean up timed-out Harbor trials`，包含日志有界收束、精确 Compose 超时清理、测试与同步文档。提交后工作区应干净，本地 main 预计比 origin/main 领先 8、落后 0，origin/main 为 42484d8。Harbor 固定提交是 6af8d6e31eced13b93849cdf80feeadf24603d15，版本 0.22.0。若状态不符，保留并先辨明所有后续改动，禁止 reset/checkout/clean。除非用户明确要求，不 push。

不要重复构建 Harbor：framework/harbor/.venv 已按固定 uv.lock 安装，Windows 上 litellm 源码构建曾耗时 275 分钟；runtime/tools 和 runtime/cache/uv 也是已忽略但有价值的本机缓存。固定 SWE-Gym-Lite Parquet 和固定摘要镜像都已在本机，镜像 `/testbed` HEAD 已核验。

继续更新同一份 M0 行动记录，不新建重复记录。交接前最新快速无模型绿色基线是：ruff format/check、strict mypy 全通过，unit + contract `44 passed, 7 deselected in 6.67s`。正常 Harbor NOP 回归是 `runtime/prototype/m0-harbor-timeout-regression-20260906-01`（`1 passed in 18.87s`）；真实 Windows 父子进程回归是 `runtime/prototype/m0-process-tree-timeout-20260906-02`（`1 passed in 1.34s`）。不要重新构建 Harbor，也不要重复这些旧探针。

`apps/backend/tests/integration/test_collect_patch_scenarios.py` 已在固定摘要镜像和 `--network none` 下真实运行：tracked modification、新文件、删除与容器内 Git commit 为 `4 passed in 5.91s`，生产 hook/校验器均通过，测试前后 Docker 对象计数一致且 `agentexam-patch-*` 无残留。证据目录是 `runtime/prototype/m0-collect-patch-scenarios-20260906-01`。不要重复这组探针，也不要把它扩大解释为 Harbor Compose 超时清理已通过。

结果映射已完成：`result_mapper.py` 负责枚举子 Trial 结果并按 task path + agent config 严格绑定，`result_values.py` 负责制品/usage/时间和启动失败的纯结果转换。薄 `HarborExecutionAdapter` 已实现；`process_runner.py` 管 `Popen` 生命周期、Windows 进程树/POSIX 进程组终止，`process_evidence.py` 并发排空 stdout/stderr、每路最多持久化 50 MiB，并在总收束期限后用 `HARBOR_LOG_CAPTURE_INCOMPLETE` 明示不完整。真实阻塞 collect 红灯先留下 1 个容器、1 个网络和 1 个本地镜像；修复后 Adapter 只从本 Job 路径名一致的 Trial 配置推导 Harbor 规则的 project name，按精确 label 删除并复核四类资源，不使用 prune。绿灯证据 `runtime/prototype/m0-harbor-timeout-green-20260906-02` 为 `1 passed in 49.47s`，前后 Docker 对象数均为 `18/5/15/21`。不要重写这些模块，也不要新增第二套执行路径或重复该探针。

必须固定：SWE-Gym revision/split/instance、镜像 digest、Harbor commit、Codex CLI 版本、模型和配置身份；Harbor n_attempts=1、n_concurrent_trials=1、max_retries=0、verifier.disable=true。Harbor reward 不得成为 resolved。Patch 必须来自容器最终 Git 工作区相对固定 base_commit 的完整 diff，覆盖未跟踪、删除、空 patch 和 Agent 自行 commit；256 KiB 警告，超过 1 MiB 或含二进制明确拒绝，不得截断。

接下来依次做：建立固定 Fork 的独立锁定环境和 `adapters/evaluation/swe_bench.py`，对固定题运行 gold/空/错误 patch；再补 M0 Composition Root 和 manifest。无模型链路全部通过后，按 AGENTS.md 一次只问一个问题，向用户确认会进入评测身份的 Codex CLI 版本、当前可用模型和 reasoning effort；测试中的 `model-must-be-confirmed` 不是默认值。之后只执行唯一一次真实 Codex Trial，不额外消耗模型额度。

安全约束：不得读取、打印、复制、提交或上传 auth.json 内容/API Key/Token/Cookie；真实秘密路径也不得进入配置快照、日志、轨迹、patch 或 manifest。当前 Windows 系统代理关闭、FlClash 运行；不要擅自开启系统代理、修改 VPN 或把代理连通写成闭卷隔离已通过。需要改变用户系统网络状态时，先给只读证据并请求明确授权。

执行纪律：修改前继续维护现有行动记录；最小修改，复用既有 Ports/Adapter seam；新增顶层 Module、Interface、表或目录前必须说明理由并取得用户确认。Python 文件默认不超过 200 行、每层目录默认不超过 8 个文件。所有运行结果必须附实际命令和证据，不得把未运行、失败或跳过写成通过。

完成标准：M0 只有在真实 Codex → 固定 Harbor → 完整且校验过的 patch → 固定 SWE-Bench-Fork 单题确定性结果，以及秘密、资源、成功/失败/超时清理证据全部成立时才可标记完成。否则保持 M0 进行中，如实记录具体阻塞，不进入 M1，也不宣称 MVP 已完成。
```
