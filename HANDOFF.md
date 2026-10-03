# AgentExam 当前接续交接

> 更新：2026-09-30（本次仅文档对账）；工作区：`E:\9.1agent_exam`；当前分支：`main`，提交基线 `a550eb6`。本地 `main` 已快进包含 `agent+api` 的全部成果，包括 `origin/main@f1f97b5` 的任务 05 S9–S11、三项生产 Codex 配置、Harbor 清理超时和 Docker 迁移增量；旧 `main-t2-verify` worktree 已退役。本地记录的 `origin/main` 仍为 `f1f97b5`；本次未 fetch、提交或推送。
>
> 本文是新窗口的恢复入口，不替代架构、接口、运维、任务和行动文档。若本文与当前代码或专题权威文档冲突，先核对 Git 与现实实现并同步当前状态型文档；`docs/actions/` 中已结束的记录是历史档案，不反向改写。
>
> 任务 05 的受控假提供方路径已完成 S3–S11：T1/T2、Worker 按 Run 选绑定、双网络代理生命周期、短令牌注入、两个并发固定 Harbor Trial、五组正反对照、独立判卷和隔离存储回归均有证据，任务单为 `ready-for-human`。这只验收 `internal_test` 假身份；真实 DeepSeek/Kimi 身份、Key、协议兼容和账单仍未实现或运行。

## 1. 目标与当前阶段

项目目标仍是完成 Codex-only MVP（最小可用平台）：协作者提交评测 Job，owner 批准，所有者机器上的 Worker 使用固定执行链运行，保存确定性判卷与证据，并通过 Web 查看结果。M0 技术原型已经跑通；M1 任务 01–13 已完成，任务 14 有正向证据但远程负向/VPN/离线项尚未全部关单，因此整个 MVP 仍不能宣布完成。

当前扩展阶段以现实代码和任务验收为准：

2026-09-30 已静态修正模块索引、接口与运维文档的过期状态，并补齐 provider 上游失败码；过程见[文档对账与审查资料行动](docs/actions/2026-09-30-document-alignment-and-review-research.md)。本次没有启动服务或运行评测，运行状态仍只引用 2026-09-29 的历史记录。M1 早期任务标签不代表未完成：任务 01 已明确不增设完成标签，以勾选项和验收证据判断；本次未改任务状态。

- P1–P4 最小本地持久化已完成；备份恢复已明确移出课设范围。
- 任务 01–02 已完成；任务 03 的跨批次对比 Web 已实现并验证，任务单保持 `ready-for-human` 等待最终人工确认。
- 任务 04 的六题受控目录、五道新题三补丁门禁、`continuous(1–20)`、六题向导与暴露面检查已经落地；2026-09-22 当前 owner 运行目录也已登记全部六题并完成网页选择核对，证据见[本机登记行动](docs/actions/2026-09-22-register-five-verified-tasks.md)。任务单保持 `ready-for-human` 等待最终人工确认。
- 生产代码已有 Terra/medium、Luna/low、Sol/medium 三种固定 Codex/ChatGPT 配置，Web 可选择，Harbor 入口按同一预置精确校验。两项新配置各自在隔离原型中完成六题固定 CLI/Fork 试跑：Luna/low 解出 3/6，Sol/medium 解出 6/6；当前 owner 目录已登记两项新配置并按 UUID 回查，PostgreSQL 三项配置均启用。真实 Web 目录和新建评测第二步已实际选中 Luna 与 Sol，结果为 `registered=2 selectable=2 selected=2 submitted=0`，没有提交正式 Job。证据与轨迹缺失限制见[本次 Agent 配置行动](docs/actions/2026-09-22-expand-codex-agent-configurations.md)。
- 任务 05 的 9 项验收已在主线逐项对账通过，任务单为 `ready-for-human`。S9–S11 已把 `internal_test` 假提供方接到正式 Registry → 批准 → Worker → Harbor 接缝，并完成双 Trial 隔离、秘密外表面、失败关闭、独立判卷和隔离存储回归；全程未读取真实 Key、未调用真实供应商、未充值。真实 DeepSeek/Kimi/ChatGPT API 身份与协议仍属于后续任务 06/07，不得从假链结论外推。
- 任务 06–08 未实施；不得因 04 完成、Worker 曾在线或 05 决策已确认而自动开始真实供应商调用、充值或冻结矩阵。

### 1.1 上一窗口的开发历程索引

只按当前任务读取对应记录，不从头重跑历史实验：

- `fengyy-fixweb` 合并、两轮远端并发整合、测试与推送：[合并行动](docs/actions/2026-09-21-merge-fengyy-into-main.md)。
- 任务 03 Web 对比页：[任务 03 行动](docs/actions/2026-09-21-ui-comparison-report.md)与[任务单](.scratch/ui-catalog-providers/issues/03-comparison-report-and-evidence.md)。
- 任务 04 六题、规模与资格门禁：[任务 04 行动](docs/actions/2026-09-19-task-04-catalog-candidates-and-scale.md)与[任务单](.scratch/ui-catalog-providers/issues/04-five-new-tasks-and-continuous-scale.md)。已结束行动记录中的早期“未授权/未运行”段落是当时事实，当前结论看任务单、现实代码和当前架构文档。
- 2026-09-22 owner 在当前运行目录登记五道新题并核对网页选择：[本机登记行动](docs/actions/2026-09-22-register-five-verified-tasks.md)。
- 任务 05 当前决定与授权边界：[负责人回执](docs/LLY/01-plan/TASK05_OWNER_ACTION_REQUIRED.md)与[代码事实填充版](docs/LLY/01-plan/TASK05_OWNER_DELIVERY_FILLED.md)。
- 任务 05 T2、S9、S10、S11 的最终证据分别见[活体网络替身](docs/actions/2026-09-22-task05-t2-live-other-trial.md)、[Run 绑定](docs/actions/2026-09-22-task05-s9-run-bindings.md)、[网络接线](docs/actions/2026-09-22-task05-s10-network-wiring.md)和[双 Trial 集成](docs/actions/2026-09-23-task05-s11-integration.md)。
- 九 Run 卡死根因与有界清理修复见[Harbor 清理行动](docs/actions/runtime/2026-09-23-harbor-trial-cleanup-timeout.md)；Docker 数据盘和 WSL 启动盘迁到 D 盘的证据见[第一阶段](docs/actions/runtime/2026-09-23-docker-data-migration.md)与[第二阶段](docs/actions/runtime/2026-09-23-docker-wsl-runtime-move.md)。
- 2026-09-21 17:43 的 Web/Worker/Job 运行事实：[运行交接行动](docs/actions/2026-09-21-live-runtime-handoff.md)。它是时点证据，不代表当前进程仍在线。
- 核心代码诊断与修复：[诊断报告](docs/reviews/2026-09-21-core-code-diagnostic-report.md)及[修复行动](docs/actions/2026-09-21-core-diagnostic-remediation.md)。相关修复已包含在当前 `main` 基线；托管 CI 工作流未进入当前基线，是否引入属独立后续决定。当前分支后续变更见[文档对账行动](docs/actions/2026-09-22-code-documentation-alignment.md)和[Web 比较解析器统一行动](docs/actions/2026-09-22-web-comparison-parser-unification.md)。

## 2. 当前阻塞与授权边界

| 范围 | 当前事实 | 接续边界 |
|---|---|---|
| M1 任务 14 | 已有 HTTPS 双角色正向流程；远程负向、VPN/离线等未全部完成 | 只有用户重新安排任务 14 时才继续，不自动改网络、代理、防火墙或 Tailscale |
| 任务 03 | Web 对比页、五结果矩阵、按需指标和证据钻取已落地 | 只剩人工确认与独立的 20 列滚动手感缺口；不重做后端接口 |
| 任务 04 | 六道题、连续规模与相关回归已落地；当前 owner 目录已登记六题且网页可选择 | 等最终人工确认，不再按旧计划重复拉镜像、跑门禁或改白名单 |
| 任务 05 | 9 项受控假提供方验收已对账通过；S3–S11、T1/T2、两个并发固定 Harbor Trial和回归证据已进入主线 | 等最终人工确认；不得把 `internal_test` 假身份当真实上游，不得借此读取真实 Key、调用供应商或宣称真实账单已验证 |
| 任务 06–08 | 未实施 | 真实调用、账户设置、费用与矩阵必须重新取得当轮授权 |
| 正式运行态 | 2026-09-29 现场检查：Docker Desktop 引擎未运行，Web 3000 与 Backend 8000 均拒绝连接，故 PostgreSQL、MinIO、Worker 和数据库最新 Job 终态本轮未读取；这是当前离线状态，不是数据丢失结论 | 需要运行平台时先按现有启动入口恢复 Docker 与 AgentExam，再现场核对数据库和队列；不得沿用 9 月 23 日 PID 或在线快照 |
| 团队数据库接入 | B 侧已定位为不在同一 tailnet；当前不需要数据库，暂不重试 | 不写入私有 tailnet 名/IP；由 owner 分享设备或邀请账号后才重验 |

通用边界：不把规划或文档回执当作产品实现；不自动批准 Job、不自动重试真实模型、不自动充值；不读取或输出 `auth.json`、Key、Cookie、密码等正文；不使用全局 Docker prune；不把历史 passed/skipped 数字冒充本轮刚跑结果。

## 3. 权威文档必读顺序

开始任何修改前按以下顺序读取，按任务追加而不是一次加载全部历史：

1. [AGENTS.md](AGENTS.md) 与本文：协作规则、当前 Git/任务边界。
2. [CONTEXT.md](CONTEXT.md)：Job、Run、Agent Configuration、确定性验证等领域词义。
3. [总架构](docs/architecture/ARCHITECTURE.md)、[模块索引](docs/architecture/modules/README.md)与相关模块架构：模块边界、依赖方向和现实代码地图。
4. [模块契约](docs/architecture/MODULE_CONTRACTS.md)、[HTTP API](docs/interfaces/HTTP_API.md)、[数据模型](docs/architecture/DATA_MODEL.md)：接口、错误、字段、状态机与持久化约束。
5. [Harbor 执行接口](docs/interfaces/HARBOR_EXECUTION.md)、[认证接口](docs/interfaces/CODEX_AUTHENTICATION.md)、[依赖表](docs/dependencies/DEPENDENCIES.md)：执行链、秘密边界和固定身份。
6. 做规格或任务前，先读 [`docs/agents`](docs/agents/) 约定，再读当前[扩展计划](.scratch/ui-catalog-providers/plan.md)、对应 issue 和同任务行动。
7. 做运行、Docker、网络或远程接入前，追加读[所有者行动指南](docs/architecture/modules/owner-host-runtime/ACTION_GUIDE.md)、[本机环境](docs/operations/LOCAL_DOCKER_ENVIRONMENT.md)和[远程接入](docs/operations/REMOTE_TEAM_ACCESS.md)。

完成阅读的标准不是“打开过文件”，而是能从代码和契约指出当前入口、拒绝条件、授权边界及未验证项。历史行动中的旧快照不能覆盖当前代码或持续维护文档。

## 4. 核心代码与测试必读

当前主要依赖方向仍为 `Web/CLI → delivery → application → domain/ports ← adapters`。继续工作前按涉及模块实际读实现和测试：

- 目录与六题身份：[受控镜像映射](apps/backend/src/eval_platform/adapters/tasks/catalog.py)、[HTTP 题目预设](apps/backend/src/eval_platform/delivery/catalog_presets.py)、[三项生产 Agent 预设](apps/backend/src/eval_platform/delivery/agent_presets.py)及 `apps/backend/tests/catalog/`。
- Job 提交/批准/执行：[提交](apps/backend/src/eval_platform/application/job_submission.py)、[批准](apps/backend/src/eval_platform/application/owner_approval.py)、[执行](apps/backend/src/eval_platform/application/execute_job.py)、`application/job_lifecycle/` 与 `adapters/persistence/jobs/`。
- 报告与五结果矩阵：[矩阵](apps/backend/src/eval_platform/application/reporting/matrix.py)、[比较路由](apps/backend/src/eval_platform/delivery/http/routes/jobs/reporting/comparisons.py)及 `apps/backend/tests/jobs/reporting/`。
- Worker 与现有提供方边界：[Worker 装配](apps/backend/src/eval_platform/delivery/worker/runtime.py)、[按 Run 选绑定](apps/backend/src/eval_platform/delivery/worker/bindings.py)、[固定配置渲染](apps/backend/src/eval_platform/adapters/execution/codex/provider_config.py)、[代理网络](apps/backend/src/eval_platform/adapters/execution/provider_access/net/)和认证接口。正式真实路径仍只有三项固定 Codex/`openai_chatgpt`；`internal_test_fake/provider_run_token` 已接入受控假链，但真实新提供方身份和调用仍不存在。
- Web 工作台与对比页：`apps/web/src/features/workbench/`、`apps/web/src/features/jobs/`、[对比页](apps/web/src/features/jobs/reporting/comparison.tsx)及 `apps/web/tests/`。
- 生命周期与部署：`infra/local/` 下的四个公开 PowerShell 入口、`infra/compose.yaml` 和 owner-host-runtime 文档；运行状态必须现场检查。

核心诊断与代码修复的历史验证见对应行动；当前 `agent+api` 分支已包含文档与代码对账、结果文案映射、Web 比较响应解析器统一、三项固定 Codex 配置、任务 05 S9–S11、Harbor Compose 有界清理及 Docker/WSL 迁移记录。接续时先读相关行动和现实源码，不把旧行动中的状态或测试数字当作本轮新结果。

## 5. Git、环境与测试快照

### Git 与必须保留的增量

2026-09-29 本轮现场核对：

- 当前工作区位于本地 `main`，其上游仍是 `origin/main@f1f97b5`；本地 `main` 已通过 fast-forward 包含 `agent+api` 的全部成果，旧 `runtime/main-t2-verify` worktree 已在保留唯一暂停行动记录后退役。远端 `main` 尚未推送，恢复时不要把本地领先误写成远端已发布。
- `origin` 指向 `https://github.com/anphuchoang5-sys/agent-exam.git`。恢复时仍以 `git remote -v`、`git branch -vv`、`git status` 的现场输出为准。
- `apps/web/%USERPROFILE%/` 是 npm 缓存；根目录 `蓝色商务风企业介绍演示文稿.pptx` 是 132 MB、元数据 0 张幻灯片的通用模板。两者都不是 AgentExam 成果，本轮不提交、不删除。
- 完成本轮后继续按路径暂存，不使用 `git add .`、reset 或清理其他 worktree/运行证据。

### 最近已完成的验证

下列数字来自此前核心修复行动的实际检查，属于历史验证；本次对账、文案映射和 Web 解析器修改的验证另见[对账行动](docs/actions/2026-09-22-code-documentation-alignment.md)与[解析器统一行动](docs/actions/2026-09-22-web-comparison-parser-unification.md)：

- Backend：Ruff lint/format（321 个文件）和无参数 Mypy（177 个源文件）通过；复杂度阈值 `C901 > 10` 为 0；默认全量 `510 passed / 102 skipped`，分支覆盖率 `86.38%`，超过 80% 门禁。
- 仓库根统一 Pytest：修正现实目录为 `infra/tests` 并取消会误排 Worker 测试的宽泛 `runtime` 规则后，收集 633 项，`521 passed / 112 skipped`；未误收 `.venv`/第三方代码，基础设施和 16 项 Worker runtime 测试都进入统一门禁。
- PostgreSQL：受控身份对及显式迁移在隔离真实 PostgreSQL 中 `2 passed`；迁移 CLI 定向回归 `5 passed / 1 skipped`。
- 依赖：PyArrow 23.0.1、pytest 9.0.3 与 PostCSS 8.5.28 关闭本轮审计发现的公开漏洞；`pip-audit` 无已知漏洞（本地未发布包明确跳过），npm 生产和全量审计均为 0 漏洞。
- Web：ESLint、类型检查、生产构建通过；使用系统 Chrome 的完整 Playwright 回归 `45 passed / 0 failed`。
- 依赖浏览器缺少 Playwright 捆绑 Chrome 的首次失败是测试环境限制，改用已安装系统 Chrome 后通过；`.next-e2e` 隔离目录与生成配置恢复逻辑已验证不污染工作树。

`skipped` 仍代表外部存储、Docker、Fork/Harbor 等显式门禁未在该轮启用，不能计为通过；这些历史数字本身也不证明任务 05 的后续切片。

任务 05 的较新验收覆盖上一段末句中的旧状态：S11 行动记录了统一入口定向 75 passed、提交前全量 696 passed / 102 skipped、覆盖率 86.79%，Ruff/format/Mypy 通过；任务单随后对 9 项逐项对账为通过。T1–S11 仍是受控假提供方证据，不能替代真实供应商验证。

2026-09-22 当前运行态核对：五道新题通过既有 owner HTTP 登记进入目录，PostgreSQL 六个 `instance_id` 各 1 条，Job/Run 仍各 2 条；系统 Chrome 中任务页和新建向导显示并选中六题，`continuous(1–20)` 下只走到确认页，没有提交评测。运行中的后端已刷新到当前代码；密码恢复、旧后端 400 的原因与逐项证据见[本机登记行动](docs/actions/2026-09-22-register-five-verified-tasks.md)。进程在线状态在接续时仍需现场重查。

随后按用户要求再次执行专属启动脚本并清理旧进程：当前 Web `127.0.0.1:3000`、Backend `127.0.0.1:8000`、PostgreSQL、MinIO 与原有私有 HTTPS 入口可用；HTTPS 转发已从旧 Web 59336 切到 3000，PostgreSQL TCP 55432 转发保留，旧网页、旧 Worker 和旧 owner 恢复终端退出。当前无排队或活动 Job，Worker 未运行；证据及动态状态边界见[启动与旧进程清理行动](docs/actions/2026-09-22-start-current-project-and-stop-old-processes.md)。

2026-09-22 19:04 +08:00 按用户再次要求启动全部组件，正式 `agentexam-owner` Worker 已作为一棵父子进程链持续运行；Web/API/私有 HTTPS 均返回 200，专属 PostgreSQL/MinIO 运行，Serve 仍将 HTTPS 转发到 Web 3000、TCP 55432 转发到本机 55432。主库仍为 6 题、2 个 Job、2 个 Run，排队与活动 Job 均为 0。此为时点证据，后续使用时重查；详见[全组件启动行动](docs/actions/2026-09-22-start-all-components.md)。

随后新建的三题评测批次在 Harbor 准备容器镜像时失败，主库现为 6 题、3 个 Job、5 个 Run。按用户要求准备五道新题的运行环境：五张白名单固定摘要镜像已加载到当前 Docker 引擎，五次无模型 Dockerfile 构建通过；失效的阿里云镜像加速源已在精确备份后移除。Docker Desktop 受控重启后，专属存储、Worker、Web/API 与私有 HTTPS 恢复，原失败 Job 未重试。完整 Harbor Compose 原临时文件已清理，不能把本轮构建检查写成真实 Trial 验收；E 盘 19:52 +08:00 可用约 4.22 GiB，真实批次峰值仍待核对。步骤与证据见[五题运行镜像行动](docs/actions/2026-09-22-prepare-five-task-runtime-images.md)。

2026-09-23 后续运行与机器变更：九 Run 批次曾因 E 盘接近耗尽并卡在 Harbor Compose 清理，Job/9 Run 后来以受控基础设施失败收束；代码已为 `stop/down` 增加 120 秒上限并通过定向单测。Docker Desktop 的数据盘和 `docker-desktop` WSL 启动盘随后迁至 `D:\dockerdata\DockerDesktopData`，旧 E 盘路径已清空。2026-09-29 现场检查时 Docker Desktop、Web、Backend 和 Worker均离线，本轮没有启动服务或读取数据库，所以最新业务数据数量与最后一个 9 Run Job 的数据库终态必须在下次启动后重查。

## 6. 下一窗口的工作顺序与验收

1. 完整读当前 `AGENTS.md` 与本文，再运行只读的 `git status --short --branch`、`git log -8 --oneline --decorate` 和按路径 `git diff`；先识别文件归属，保留诊断任务、临时产物、`framework/` 与 `runtime/`。
2. 若用户只说“恢复上下文”，完成只读核对后汇报已恢复并等待，不自动拉取、测试、实现、提交或推送。
3. 若接续当前修复，读取[修复行动](docs/actions/2026-09-21-core-diagnostic-remediation.md)和[诊断报告](docs/reviews/2026-09-21-core-code-diagnostic-report.md)；保持历史 actions/research 只读，完成权威文档、最终门禁和本地提交，不自动 push。
4. 若接续任务 04，只处理人工确认或明确缺口，不重复已完成的五题门禁、白名单、continuous 和向导回归。
5. 任务 05 已完成受控假链并等待人工确认；不要重复 T2/S9–S11。若处理遗留受控码文档或发现回归，先读任务单末尾 9 项对账和 S11 行动，再立新行动。
6. 任务 06–08、任务 14 或机器网络/运行态均需用户明确安排。任何真实供应商调用、充值、账号设置、Docker/WSL/代理/防火墙变更或共享数据库写入都不得从任务 05 假链或历史授权推断。
7. 修改后同步当前架构/接口/状态文档与本任务行动记录，实际运行相称的检查并查看输出；历史证据与本轮新验证分开报告。

当前分支已汇集文档与代码对账、Web 比较解析器、三项生产 Codex 配置、任务 05 受控假链、Harbor 清理超时和 Docker/WSL 迁移成果。托管 CI、任务 03/04/05 人工确认、真实新提供方任务 06/07、冻结矩阵任务 08 与任务 14 远程验收分别按用户后续安排处理。

## 7. 历史入口

早期 M0、M1 分任务、持久化、远程运行和网络实验均保留在 `docs/actions/`、`docs/research/` 及对应接口/运维文档中。它们记录各自时点的过程和证据，不再把旧提示词、旧 PID、旧提交领先数或旧测试数量复制到本恢复入口。

面向项目所有者的阅读路线见[项目阅读指南](docs/architecture/READING_GUIDE.md)。需要追溯 M0 真实运行时，从[M0 行动记录](docs/actions/2026-09-05-m0-codex-harbor-implementation.md)对应事件段落进入；需要追溯持久化时，从[所有者单机运行模块](docs/architecture/modules/owner-host-runtime/ARCHITECTURE.md)与其行动指南进入。

## 8. 建议使用的技能

- 修改项目文件：`action-document`。
- 项目范围、进度与收尾汇报：`project-control-report`。
- 审查当前分支或固定差异：`code-review`；全量语言/安全/架构诊断按已开始的 `code-review-skill` 行动范围继续。
- 复杂故障或性能回归：`diagnosing-bugs`。
- 实际出现 Git 冲突：`resolving-merge-conflicts`。

技能只规定工作方法，不扩展业务、运行、提交或外部调用授权。
