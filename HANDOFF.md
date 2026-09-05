# AgentExam 架构讨论 Handoff

> 交接时间：2026-09-05
>
> 当前阶段：架构讨论；远端提交、评测机所有者批准和私有接入候选已完成文档对账，尚未开始业务代码实现
>
> 用途：帮助从 `E:\9.1agent_exam` 打开的下一条 Codex 任务恢复上下文
>
> 重要限制：本文是持续更新的恢复入口，不替代各专题唯一事实源；本轮对账结果见第 6 节。

## 1. 为什么需要这份 Handoff

原任务正在用初学者能理解的方式讨论 AgentExam 的架构，并持续把确认结果同步到架构、依赖和接口文档。过程中 Codex 在含中文字符的工作区路径下出现 Windows 沙箱初始化错误，随后项目整体迁移：

```text
E:\9.1实训  →  E:\9.1agent_exam
```

文件系统迁移、Git 状态和远程仓库完整性已经验证，但 Windows 默认沙箱的 `setup refresh had errors` 后来在英文路径重新出现，因此不能再把迁移视为故障根治。Codex 认证与单机协作方式已在 2026-09-04 对账；2026-09-05 又确认“协作者远端提交 → 评测机所有者批准 → 本机 Worker 执行”，并明确评测机必须在线。Tailscale Serve 是校园网/VPN场景的推荐候选，尚未最终确认或双机实测。

迁移证据见 [`docs/actions/2026-09-04-workspace-path-migration.md`](docs/actions/2026-09-04-workspace-path-migration.md)。

## 2. 恢复任务时先做什么

1. 确认工作区是 `E:\9.1agent_exam`，不要再使用旧路径。
2. 运行 `git status --short`，保留 2026-09-05 的审批/远程接入文档改动，不得重置或覆盖。
3. 按下面的层级阅读，不要只看总架构就开始修改。
4. 第 6 节的认证与审批流程冲突已经同步；网络下一步只做 Tailscale + 现用 VPN 的无秘密双机连通实验，业务下一项技术核验仍是 SWE-Gym-Lite 的不可变 revision、真实 split 和候选任务。
5. 对仍需人类选择的架构问题，一次只和用户讨论一个；先用通俗语言解释，再给出专业名称和推荐方案。

### 2.1 第一批：开始任何修改前必须完整阅读

| 顺序 | 文档 | 下一窗口必须了解什么 | 阅读时的注意事项 |
|---:|---|---|---|
| 1 | 本文 `HANDOFF.md` | 中断原因、对话确认事实、文档滞后点、未决问题和安全红线 | 本文是交接快照，不替代专题事实源 |
| 2 | [`docs/actions/2026-09-04-architecture-document-reconciliation.md`](docs/actions/2026-09-04-architecture-document-reconciliation.md) | 本轮对账的实际改动、CLI 探针、沙箱偏差和验证结果 | 这是当前结果记录；原计划仍保存在 `2026-09-04-handoff-document.md` |
| 3 | [`CONTEXT.md`](CONTEXT.md) | AgentExam 的领域词汇及其统一含义 | 只维护领域语言，不应从这里推断框架接口 |
| 4 | [`docs/architecture/ARCHITECTURE.md`](docs/architecture/ARCHITECTURE.md) | 系统目标、模块边界、数据流、决定表、规划文件树和待讨论队列 | 认证与单机评测节点已经同步；版本、模型和容器运行仍保持待实测 |
| 5 | [`docs/interfaces/CODEX_AUTHENTICATION.md`](docs/interfaces/CODEX_AUTHENTICATION.md) | 已确认的 ChatGPT Pro `auth.json` 方案、凭据所有权、协作方式和安全边界 | 认证政策已确认；容器运行、Token 刷新和清理仍未实测 |
| 6 | [`docs/dependencies/DEPENDENCIES.md`](docs/dependencies/DEPENDENCIES.md) | SWE-Gym、SWE-Bench-Fork、Harbor 的固定提交和本地恢复方式 | 认证政策已同步；宿主 `codex-cli 0.142.0` 只是探针，不是项目固定版本 |
| 7 | [`docs/interfaces/HARBOR_EXECUTION.md`](docs/interfaces/HARBOR_EXECUTION.md) | 平台 Job、Harbor Job、Trial、patch、轨迹和错误映射 | 认证输入/输出边界已同步；本机 Harbor、Token 生命周期和清理仍未实测 |
| 8 | [`docs/interfaces/FRAMEWORK_INTERFACES.md`](docs/interfaces/FRAMEWORK_INTERFACES.md) | SWE-Gym 字段、SWE-Bench-Fork Harness、Harbor 与 Agent CLI 的真实接口入口 | 旧失败已降为历史记录；宿主 CLI 探针成功不等于容器 E2E 通过 |
| 9 | [`docs/operations/LOCAL_DOCKER_ENVIRONMENT.md`](docs/operations/LOCAL_DOCKER_ENVIRONMENT.md) | 当前笔电的 Docker/WSL 内存、磁盘位置、容量和单机限制 | 数据是 2026-09-03 快照；磁盘余量等易变值引用前重查 |
| 10 | [`docs/adr/0001-use-harbor-as-execution-backend.md`](docs/adr/0001-use-harbor-as-execution-backend.md) | 为什么 PostgreSQL 管平台队列、Harbor 只管执行、固定 Fork 负责最终判卷 | 这是已接受的架构决定；只有 Harbor 原型触发退出条件时才重新讨论 |
| 11 | [`docs/actions/2026-09-04-codex-authentication-policy.md`](docs/actions/2026-09-04-codex-authentication-policy.md) | 认证决定产生的实际修改范围与验证结果 | 已收尾；未把宿主探针扩大为 Harbor 容器或真实 Trial 结论 |
| 12 | [`docs/actions/2026-09-05-remote-submission-owner-approval.md`](docs/actions/2026-09-05-remote-submission-owner-approval.md) | 远端提交、所有者批准和网络候选的实际修改与验证结果 | Tailscale 仍是候选；文档检查不等于双机连通 |
| 13 | [`docs/operations/REMOTE_TEAM_ACCESS.md`](docs/operations/REMOTE_TEAM_ACCESS.md) | 校园网/VPN下的推荐拓扑、最小暴露面、配置顺序和诊断 | 应用登录完成前不能把真实批准页面开放给协作者 |

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

当前认可的主流程是：

```text
协作者通过私有入口选择 Agent、任务和赛道
  → FastAPI 创建 AWAITING_OWNER_APPROVAL Job
  → 评测机所有者检查冻结配置并批准
  → PostgreSQL 改为 QUEUED
  → 单机 Worker 一次领取一个重型 Job
  → Harbor 把 Agent × 任务展开成顺序执行的 Trial
  → Agent 在 Docker 环境中阅读 Issue、修改代码并产生 patch
  → 固定 SWE-Bench-Fork 在新的干净环境中应用 patch 并运行测试
  → PostgreSQL 保存状态和索引，MinIO 保存 patch、轨迹、日志与报告
  → LLM Judge 只做失败归因，人工页面负责抽检
  → Next.js 展示报告和排行榜
```

这里的专业术语对应关系：

- **平台 Job**：用户一次提交的整批评测，例如 2 个 Agent × 3 道题。
- **Harbor Job**：平台 Job 交给 Harbor 后的一份执行计划。
- **Trial / Evaluation Run**：某个 Agent 做某一道题的一次独立尝试。
- **patch / model_patch**：Agent 对仓库造成的代码差异；判卷时应用到固定的干净仓库，而不是相信 Agent 自己声称测试通过。
- **SWE-Bench-Fork Harness**：真正运行规定测试、产生 `resolved` 等确定性结果的判卷程序。

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
- MinIO 保存不可变的大文件制品，例如 patch、轨迹、stdout/stderr、测试日志和 Judge 原始响应。
- 一个平台 Job 对应一个 Harbor Job；一条平台运行对应一个 Harbor Trial。
- 同时只运行一个重型平台 Job，Harbor `n_concurrent_trials=1`，Trial 顺序执行。
- Docker/WSL 内存上限已调整到 10 GB，Docker 数据已经迁到 E 盘；真实任务仍需实测资源上限，不能直接照搬 Harbor 模板的 8192 MB。

### 4.4 真实性、赛道和证据

- 正式演示、报告和排行必须来自真实 Agent、真实 Docker 执行和真实 SWE-Bench-Fork 测试。
- Mock 只允许验证平台自身的状态与错误分支，并标为 `internal_test`；不得进入正式结果。
- 主榜为闭卷赛道 `closed_book`：只放行模型服务所需网络，不开放一般 Web 搜索。
- 实验榜为开卷赛道 `open_book_experimental`：允许登记过的网络/搜索能力，但与闭卷严格分榜。
- patch、轨迹、日志、测试、Judge 与人工复核均需关联同一 `run_id`。
- 工具调用次数可以作为过程证据，但是否参与评分尚未决定；缺失数据不能伪造为 0。

### 4.5 第一个真实原型

- 使用 `SWE-Gym/SWE-Gym-Lite` 的 1～3 道真实任务。
- 首个真实 Agent 使用 Codex，优先复用 Harbor 内置 Codex Adapter。
- 先跑通 Issue → Harbor → patch → 固定 SWE-Bench-Fork 的单题闭环，再扩展 Aider、Claude Code 和自研 Agent。
- Lite 的不可变 revision、真实 split 和具体 `instance_id` 尚未核验，不能猜。

### 4.6 Codex 认证与多人协作

这是用户已经确认并同步到权威文档的部分：

- 首个 Codex 原型优先使用评测机所有者本人通过 ChatGPT Pro 登录产生的 `auth.json`，暂不因为 OpenAI API 费用另购 OpenAI API 用量。
- `auth.json` 是密码级个人凭据，绝不能发给协作者、提交 Git、写入 PostgreSQL/MinIO，或进入日志和制品。
- 正式真实 Trial 默认只在用户这一台评测机上触发；协作者可以完整开发项目，但不需要取得用户凭据，也不必在各自电脑上运行真实 Codex Trial。
- 协作者可以远端创建 Job，但初始状态只能是 `AWAITING_OWNER_APPROVAL`；只有评测机所有者批准后才进入 `QUEUED`，本机 Worker 不得领取待批准/已拒绝 Job。
- 协作者使用平台时，评测机和本机平台必须在线；离线时当前架构不提供云端常驻入口。
- 私有远程入口只暴露 Web，不暴露 FastAPI 原始端口、PostgreSQL、MinIO、Docker、Worker 或凭据路径。Tailscale Serve 是推荐候选，需与现用 VPN 双机实测后再确认。
- 如果协作者要在自己的机器运行，必须使用自己的 ChatGPT 登录或自己获授权的 API Key。
- 用户持有的 Kimi、DeepSeek API 可以在以后作为独立 Agent Configuration 接入；不能在同一次 Trial 中作为 Codex/OpenAI 的静默回退。
- 权威专题文档为 [`docs/interfaces/CODEX_AUTHENTICATION.md`](docs/interfaces/CODEX_AUTHENTICATION.md)。
- 远端接入权威运维文档为 [`docs/operations/REMOTE_TEAM_ACCESS.md`](docs/operations/REMOTE_TEAM_ACCESS.md)。

## 5. 已验证的本机和仓库事实

- 当前工作区：`E:\9.1agent_exam`。
- 旧工作区 `E:\9.1实训` 已不存在。
- Git 分支：`main`。
- 当前 HEAD：`a2e85bb docs: reconcile evaluation architecture records`；这是用户要求在本轮更新前创建的本地检查点，未推送。
- 远程仓库：`https://github.com/anphuchoang5-sys/agent-exam.git`。
- 工作区迁移后默认沙箱曾短暂通过，但本窗口在英文路径连续重现 `setup refresh had errors`；路径迁移不能视为根治，详见路径迁移行动记录的后续复核。
- 同一窗口提升权限后的只读探针中，`codex --version` 返回 `codex-cli 0.142.0`，`codex exec --help` 退出码为 0；这只证明当前宿主 CLI 能启动，不代表项目版本已固定或 Harbor 容器已可用。
- Docker/WSL 的 2026-09-03 实测事实见 [`docs/operations/LOCAL_DOCKER_ENVIRONMENT.md`](docs/operations/LOCAL_DOCKER_ENVIRONMENT.md)；其中磁盘余量等数值会变化，引用前应重新检查。
- 截至交接时，尚未在本机下载/安装/运行 Harbor，尚未运行真实 SWE-Gym Trial，也尚未运行固定 SWE-Bench-Fork 判卷。

## 6. 文档对账完成状态

2026-09-04 已完成认证对账，实际过程见 [`docs/actions/2026-09-04-architecture-document-reconciliation.md`](docs/actions/2026-09-04-architecture-document-reconciliation.md)。2026-09-05 的审批与远程接入对账见 [`docs/actions/2026-09-05-remote-submission-owner-approval.md`](docs/actions/2026-09-05-remote-submission-owner-approval.md)。

| 文件 | 已完成的同步 | 仍保留的边界 |
|---|---|---|
| [`docs/architecture/ARCHITECTURE.md`](docs/architecture/ARCHITECTURE.md) | 已有认证 C-23～C-25，并新增 C-26～C-27、所有者批准流、私有入口、风险和验证门槛 | CLI 项目版本、模型、端点、容器运行及 Tailscale/VPN共存仍待固定或实测 |
| [`docs/dependencies/DEPENDENCIES.md`](docs/dependencies/DEPENDENCIES.md) | Codex 行区分已确认认证政策与宿主 CLI 探针 | `0.142.0` 不是项目基线；Harbor 容器兼容性未验证 |
| [`docs/interfaces/HARBOR_EXECUTION.md`](docs/interfaces/HARBOR_EXECUTION.md) | 公共输入、执行节点解析、制品排除和首次 Trial 安全检查已写明 | Token 刷新、脱敏、清理、patch 和 Trial E2E 未验证 |
| [`docs/interfaces/FRAMEWORK_INTERFACES.md`](docs/interfaces/FRAMEWORK_INTERFACES.md) | 旧 CLI 启动失败降为历史；记录新路径宿主探针和退出码 | 默认沙箱仍故障；真实账号和 Harbor 容器运行未验证 |
| [`docs/interfaces/CODEX_AUTHENTICATION.md`](docs/interfaces/CODEX_AUTHENTICATION.md) | 保持为认证唯一事实源，并明确远端提交/批准不携带凭据，只有本机 Trial 解析 | 不记录真实凭据路径、内容或 Token |
| [`docs/actions/2026-09-04-codex-authentication-policy.md`](docs/actions/2026-09-04-codex-authentication-policy.md) | 实际文件树和验证结果已补齐 | 历史行动记录只说明本次政策落盘，不替代认证事实源 |
| [`docs/architecture/MODULE_CONTRACTS.md`](docs/architecture/MODULE_CONTRACTS.md) | Job Submission 与 Owner Approval 分开；Worker 只领取 `QUEUED` | 可信登录及所有者账户绑定仍待设计 |
| [`docs/architecture/DATA_MODEL.md`](docs/architecture/DATA_MODEL.md) | 新增 `AWAITING_OWNER_APPROVAL`、`REJECTED`、决定审计字段与领取约束 | 精确 SQL、并发事务和恢复策略仍待实现验证 |
| [`docs/interfaces/HTTP_API.md`](docs/interfaces/HTTP_API.md) | 创建 Job 返回待批准；新增所有者批准/拒绝契约 | 应用登录未实现，接口尚不能安全远程开放 |
| [`docs/operations/REMOTE_TEAM_ACCESS.md`](docs/operations/REMOTE_TEAM_ACCESS.md) | 记录校园网/VPN下的最小暴露面、Tailscale 推荐配置和验收清单 | VPN 产品未知；Tailscale/Cloudflare 都未安装、确认或双机实测 |
| [`docs/actions/2026-09-05-remote-submission-owner-approval.md`](docs/actions/2026-09-05-remote-submission-owner-approval.md) | 记录本轮范围、实际变更和文档验证证据 | 不把文档验证写成网络或真实 Trial 已通过 |
| 根目录 `AGENTS.md` | 本轮未修改；当前任务上下文明确把它作为项目协作规则提供 | 后续若用户要求删除、清空或重写，必须作为单独选择处理 |
| 2026-09-04 的若干文档 | 已包含在本地检查点提交 `a2e85bb` | 该提交未推送；2026-09-05 新改动继续保留为可审阅 diff |

历史行动文档中的 `E:\9.1实训` 是当时真实路径，不应为了表面一致而批量改写。只有描述“当前工作区”的活动文档需要使用新路径。

## 7. 当前 Git 工作区，禁止误删

交接时本地 HEAD 为 `a2e85bb`，本轮以下审批/远程接入文档仍保留为尚未提交的可审阅修改：

```text
 M HANDOFF.md
 M docs/architecture/ARCHITECTURE.md
 M docs/architecture/DATA_MODEL.md
 M docs/architecture/MODULE_CONTRACTS.md
 M docs/interfaces/CODEX_AUTHENTICATION.md
 M docs/interfaces/HTTP_API.md
?? docs/actions/2026-09-05-remote-submission-owner-approval.md
?? docs/operations/REMOTE_TEAM_ACCESS.md
```

列表应在交接前用实际 `git status --short` 复核；这些文件都是本轮架构对账和恢复上下文所需内容。不得使用 `git reset --hard`、`git checkout --` 或清理未跟踪文件。

## 8. 仍未决定或尚未实测

以下不能因为 Handoff 存在就擅自定稿：

1. SWE-Gym-Lite 的不可变 revision、真实 split、首批 1～3 个任务及镜像 digest。
2. Harbor 在本机的实际安装与运行方式，以及 patch 在环境清理前的可靠提取方式。
3. Worker 作为 Windows/WSL 宿主进程运行，还是作为挂载 Docker Socket 的容器运行。
4. 单 Trial 的 CPU、内存、PID、磁盘和超时限制。
5. 容器内 Codex CLI 固定版本、模型 ID、端点白名单以及 `auth.json` Token 刷新和销毁路径。
6. `agent-exam.yaml` 的最小提交字段。
7. 可信用户的登录方式、评测机所有者账户绑定/恢复，以及提交者、管理员、评审者的其余权限。
8. LLM Judge 是否进入总分；当前只确认它不能覆盖确定性测试结果。
9. 工具调用、token、耗时是否计分，以及不同 Agent 缺失指标的公平处理。
10. 开卷实验榜统一平台 Web 工具，还是允许 Agent 各自的原生搜索工具。
11. 已知现用代理客户端是 FlClash，且用户确认虚拟网卡/TUN 当前关闭；仍需确认版本、系统代理状态、Docker/Codex 外网路径，并实测 Tailscale 在校园网下是直连还是中继。未双机实测前不能宣称远程入口已可用。
12. 私有入口是否最终确认 Tailscale Serve；只有共存实验失败时才评估 Cloudflare Tunnel + Access。

## 9. 推荐的下一步顺序

1. 先读本 Handoff 与本轮 [`远端提交/所有者审批行动记录`](docs/actions/2026-09-05-remote-submission-owner-approval.md)，不要把已经确认的等待批准状态改回直接排队。
2. 以 [`CODEX_AUTHENTICATION.md`](docs/interfaces/CODEX_AUTHENTICATION.md) 为认证唯一事实源，不从历史行动记录推断当前政策。
3. 远程连通下一步先取得用户现用 VPN 产品和模式，再按 [`REMOTE_TEAM_ACCESS.md`](docs/operations/REMOTE_TEAM_ACCESS.md) 用无秘密测试页执行“VPN 关/开”双机验收；应用登录未实现前不开放真实批准页面。
4. 业务下一步由 Codex 自行核验 SWE-Gym-Lite 的真实 revision、split 和候选任务，再让用户决定需要业务判断的部分。
5. 只有用户明确结束讨论并授权原型实现后，才安装 Harbor、下载任务或编写业务代码。

## 10. 安全红线

- 不读取、展示、复制、提交或上传真实 `auth.json`、API Key、Token、Cookie。
- 不把用户或协作者提交的任意 shell 命令、Git 分支或 `latest` 镜像直接送入执行链。
- 不把 Mock、Harbor reward、LLM Judge 或 Agent 自述伪装成 SWE-Bench-Fork 的真实测试结果。
- 不因为项目迁移成功就宣称 Harbor、Codex Trial 或 SWE-Bench-Fork E2E 已经跑通。
