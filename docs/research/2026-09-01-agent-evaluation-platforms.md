# AI Coding Agent 评测平台相似项目研究

> 调研日期：2026-09-01  
> 调研范围：只核查项目官方 GitHub 仓库、官方文档和官方论文。  
> 状态：研究记录，不是已经确认的项目架构。
>
> **当前决定提示：** 后续讨论已经确认直接使用 SWE-Gym 及配套 SWE-Bench-Fork，并确认只在单台物理计算机运行。当前架构状态以 [`docs/architecture/ARCHITECTURE.md`](../architecture/ARCHITECTURE.md) 为唯一事实源；本文保留外部事实、比较和当时的候选建议。

## 1. 结论摘要

GitHub 上存在多种相似项目，但它们分成了不同层次：

- **SWE-bench** 更像“标准题库 + 标准判卷器 + 官方排行榜”，不负责统一启动各种 Agent。
- **SWE-agent** 更像“一个具体的参赛 Agent + 它自己的运行和轨迹查看工具”，不是多 Agent 评测管理平台。
- **HAL Harness** 曾经提供“Agent 目录 + 统一入口函数 + 多基准 + 成本/轨迹 + 中央排行榜”，与“提交被测 Agent 代码”很接近；但官方已停止通过该 Harness 更新排行榜，并把仓库归档，只适合研究接口，不宜作为当前项目底座。
- **OpenHands Benchmarks** 更像“OpenHands 自己的批量评测基础设施”，有容器、并发和详细工具日志，但没有核实到面向任意第三方 CLI Agent 的统一适配层。
- **Inspect AI** 是通用评测框架，已经支持外部 Python Agent、Claude Code、Codex CLI、Gemini CLI 等桥接，并同时提供沙箱、轨迹、确定性 Scorer 和模型评分；但它不是开箱即用的软件工程排行榜产品。
- **Harbor** 与设想最接近：任务/数据集、Docker 或云沙箱、多种 Coding Agent 适配、标准化完整轨迹、测试验证、LLM Judge、Web 结果查看和失败摘要都已有官方实现。
- **SWE-Gym** 是本题最直接的任务设计参考和候选题库/环境来源：它提供 SWE-bench 风格的真实 Issue、固定仓库版本、测试字段和逐实例 Docker 环境，但不是统一运行多种 Agent、管理评测、展示排行榜的完整平台。

因此，“有没有类似项目”的答案是：**有，但它们分别覆盖不同层。**本题应优先采用或兼容 SWE-Gym/SWE-bench 的任务与补丁验证模型；统一 Runner、资源/网络治理、失败归因、人工复核、Next.js 前端和 PostgreSQL/MinIO 仍是项目主体。Harbor/Inspect 可以作为可选执行层比较对象，不再预设为题目指定底座。

## 2. 能力对照

符号说明：✅ 表示官方资料明确支持；◐ 表示通过配套仓库或自定义可实现，但不是该项目的完整原生产品能力；— 表示没有在本次一手来源中核实到。

| 项目 | 任务/数据集 | Docker/沙箱 | 多 Agent 适配 | 完整轨迹/工具调用 | 确定性测试判分 | LLM Judge/失败归因 | 排行榜/可视化 |
|---|---:|---:|---:|---:|---:|---:|---:|
| SWE-bench | ✅ | ✅ | — | ◐ | ✅ | — | ✅ |
| SWE-agent | ◐ | ✅ | — | ✅ | ◐ | — | ✅ 轨迹查看，非排行榜 |
| HAL Harness（已归档） | ✅ | ✅ | ✅ | ✅ | ✅/依基准而定 | ◐ 论文做过 LLM 辅助日志检查 | ✅ 历史中央排行榜 |
| OpenHands Benchmarks | ✅ | ✅ | — | ✅ | ✅/依基准而定 | ◐/依基准而定 | ✅ 轨迹查看，非通用排行榜 |
| Inspect AI | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ 日志查看，非公开排行榜 |
| Harbor | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ 本地查看与对比，非官方公共排行榜 |
| SWE-Gym | ✅ | ◐ 逐实例 Docker 环境，非完整治理 | — | ◐ 依赖实验 Agent | ✅ | ◐ learned verifier，非失败归因 Judge | — |

重要边界：表中的“多 Agent 适配”指能够用统一接口运行不同 Agent，不等于“给一个任意 GitHub 地址就能安全地自动拉取并执行源码”。主流框架通常要求 Agent 已有适配器、可执行 CLI 或固定容器镜像。

## 3. 各项目核查结果

### 3.1 SWE-bench

#### 已核实事实

- SWE-bench 是由真实 GitHub Issue 和对应代码仓库构成的软件工程任务基准；原始论文记录了 2,294 个任务。参见[官方论文](https://arxiv.org/abs/2310.06770)和[官方排行榜](https://www.swebench.com/)。
- 官方评测器把候选补丁应用到指定仓库版本，并在 Docker 中运行测试；输出总体结果、逐实例结果和运行日志。参见[官方评测指南](https://github.com/SWE-bench/SWE-bench/blob/main/docs/guides/evaluation.md)。
- 核心判分检查 `FAIL_TO_PASS` 与 `PASS_TO_PASS`：修复相关测试必须通过，同时原本通过的测试不能回归。参见[官方 grading.py](https://github.com/SWE-bench/SWE-bench/blob/main/swebench/harness/grading.py)。
- 配套的 `swe-bench/experiments` 仓库保存排行榜提交的 predictions、执行日志、结果，并在部分提交中提供 reasoning trajectories。参见[官方 experiments 仓库](https://github.com/swe-bench/experiments)。

#### 不能直接覆盖

- 主评测器消费的是 Agent 最终生成的 patch，不负责用统一接口启动 Codex、Claude Code、OpenHands 等不同 Agent。
- 主仓库没有统一记录所有 Agent 工具调用的在线轨迹协议；`experiments` 中的轨迹取决于提交者是否提供。
- 没有核实到内置 LLM Judge 或标准化失败归因流水线。

#### 可复用方式

- 复用少量 SWE-bench Verified 任务或其任务字段设计。
- 复用 Docker 判卷流程以及 `FAIL_TO_PASS` / `PASS_TO_PASS` 的确定性判分思想。
- 把官方评测结果作为本平台“功能正确性”的最高优先级证据，而不是让 LLM Judge 覆盖测试结论。

### 3.2 SWE-agent

#### 已核实事实

- SWE-agent 接受文本、文件或 GitHub Issue 作为 problem statement，并能在 Docker、Modal、AWS Fargate 等环境中运行自己的 Agent。参见[官方入门文档](https://github.com/SWE-agent/SWE-agent/blob/main/docs/usage/hello_world.md)和[问题输入文档](https://github.com/SWE-agent/SWE-agent/blob/main/docs/reference/problem_statements.md)。
- 每次运行保存 JSON 格式 `.traj`，包含 thought/action/observation 步骤，同时保存配置、日志和最终 predictions。参见[官方轨迹文档](https://github.com/SWE-agent/SWE-agent/blob/main/docs/usage/trajectories.md)。
- 官方提供命令行和 Web Inspector 查看轨迹。参见[官方 Inspector 文档](https://github.com/SWE-agent/SWE-agent/blob/main/docs/usage/inspector.md)。
- SWE-agent 明确说明：批量运行只生成预测，SWE-bench 判分是单独步骤。

#### 不能直接覆盖

- 它本身是一个 Agent 实现，主要比较的是同一 Agent 在不同模型或配置下的表现，不是统一托管任意第三方 Agent 的平台。
- 没有核实到综合排行榜、通用 LLM Judge 或跨 Agent 的统一失败分类。

#### 可复用方式

- 借鉴“问题输入、环境、Agent、轨迹输出”分离的配置方式。
- 借鉴 thought/action/observation 的轨迹查看体验。
- 可以把 SWE-agent 当作首批被测 Agent 之一，而不应把其整套内部结构照搬成平台架构。

### 3.3 HAL Harness——接近“提交 Agent 代码”，但已经归档

#### 已核实事实

- HAL 的目标是标准化不同 Agent、模型和 benchmark 的评测，统一记录准确率、成本与轨迹，并曾连接 Holistic Agent Leaderboard。参见[官方仓库](https://github.com/princeton-pli/hal-harness)和[官方论文](https://arxiv.org/abs/2510.11977)。
- 它的 Agent 接口很接近用户提出的“拉取/登记被测 Agent 代码”：通过 `--agent_dir` 指向 Agent 目录，通过 `--agent_function` 指定 Python 入口函数；Agent 目录可包含 `main.py`、`requirements.txt` 和其他文件。参见[官方 Agent 接入文档](https://github.com/princeton-pli/hal-harness/blob/main/agents/README.md)。
- Harness 支持 SWE-bench Verified、USACO、AppWorld、tau-bench 等基准；支持本地、Docker 和 Azure VM 并行执行，并通过 Weave 记录成本、用量和 Agent traces。
- 官方论文报告用 LLM 辅助检查日志以发现 Agent 行为异常；公开 HAL 结果仍可查看和下载轨迹。
- **当前状态必须注意：**官方仓库首页明确说明，该 Harness 已不再更新 HAL 排行榜、停止接收新结果和活跃 PR，仓库已归档为历史参考。

#### 不能直接覆盖

- 已归档，不能把它当成仍在维护的生产底座。
- Agent 接口主要是 Python 入口函数，不是 Harbor 那种已经内置多种 Coding Agent CLI 的适配目录。
- LLM 辅助日志检查是论文分析能力；没有核实到一个可配置、可审计、直接参与每次运行评分的通用 LLM Judge 模块。
- 确定性判分和沙箱方式随具体 benchmark 变化，不是统一的软件工程 verifier 协议。

#### 可复用方式

- 借鉴 `Agent 目录 + requirements + 明确入口函数` 的提交契约，作为“自定义 Agent 提交”候选方案。
- 借鉴排行榜把 **Agent scaffold + 精确模型版本** 作为参赛对象，并同时展示准确率与成本。
- 只借鉴接口和可复现性思想，不直接依赖已归档代码。

### 3.4 OpenHands Benchmarks 与 Trajectory Visualizer

#### 已核实事实

- OpenHands 官方 `benchmarks` 仓库目前列出 SWE-Bench、SWE-Bench Pro、GAIA、OpenAgentSafety 等评测，并提供本地 Docker Workspace 和远程容器 Workspace。参见[官方 Benchmarks 仓库](https://github.com/OpenHands/benchmarks)。
- 官方 Rich Logging 会逐步输出工具调用、消息数、工具调用次数、错误数和结束原因；每个实例有文件日志。
- OpenHands 官方另有 Web 版 [Trajectory Visualizer](https://github.com/OpenHands/trajectory-visualizer)，可以显示 action、observation、时间和元数据。
- OpenHands Runtime 以 EventStream 连接 Agent Action、环境 Observation 和前端，核心项目入口见[官方 OpenHands 仓库](https://github.com/OpenHands/OpenHands)。

#### 不能直接覆盖

- 本次官方资料中，评测执行目标是 OpenHands Agent Server/SDK；没有核实到像 Harbor 那样面向多种独立 CLI Agent 的统一内置适配器目录。
- 不同 benchmark 自己定义判分方式，未核实到整个 OpenHands Benchmarks 层统一提供 LLM Judge 和失败归因。
- Trajectory Visualizer 是查看器，不是任务调度、判卷和排行榜后端。

#### 可复用方式

- 把 OpenHands 作为一个被测 Agent，通过外部评测框架运行。
- 参考 EventStream 和轨迹时间线的交互表达。
- 参考“本地 Docker + 远程并发 Workspace”的两级执行方案，但首月只做本地 Docker。

### 3.5 Inspect AI

#### 已核实事实

- Inspect AI 是英国 AI Security Institute 开发的通用评测框架，官方仓库说明它支持工具使用、多轮交互和 model-graded evaluations，并有 200 多个预置评测。参见[官方仓库](https://github.com/UKGovernmentBEIS/inspect_ai)和[Inspect Evals 官方仓库](https://github.com/UKGovernmentBEIS/inspect_evals)。
- Agent Bridge 可以桥接同进程 Python Agent，也可以桥接运行在沙箱内的 CLI Agent；官方明确列出 Claude Code、Codex CLI、Gemini CLI 示例。参见[官方 Agent Bridge 文档](https://inspect.aisi.org.uk/agent-bridge.html)。
- Inspect 内置 Docker 沙箱，也可以扩展 Kubernetes、Modal、Daytona、EC2 等环境；沙箱可以绑定在 Sample、Task 或整个 eval 上。参见[官方 Sandboxing 文档](https://inspect.aisi.org.uk/sandboxing.html)。
- Inspect View 能实时查看样本状态、消息、工具调用、scoring decision、metadata、模型 Token 用量，并可把查看器和日志打包成静态站点。参见[官方 Log Viewer 文档](https://inspect.aisi.org.uk/log-viewer.html)。
- Scorer 既可以是确定性函数，也有官方的 `model_graded_qa` 实现；模型评分会保存评分提示、Judge 输出和解释。参见[官方 model scorer 源码](https://github.com/UKGovernmentBEIS/inspect_ai/blob/main/src/inspect_ai/scorer/_model.py)。

#### 不能直接覆盖

- Inspect 是 Python 评测开发框架，不是开箱即用的“软件项目题库管理 + 参赛 Agent 管理 + 公共排行榜”产品。
- 外部 Agent 仍需按 Bridge 规范集成；没有核实到对任意 GitHub Agent 源码的通用自动安装协议。
- 失败归因需要自定义 Scorer、Scanner 或后处理逻辑，并非固定的软件工程失败分类器。

#### 可复用方式

- 如果团队倾向自己掌控评测流程，Inspect 可作为比“从零写 Agent Runner”更成熟的候选底座。
- 可借鉴其 `Dataset → Solver/Agent → Scorer → EvalLog → Viewer` 数据流。
- 可直接借鉴“确定性评分和模型评分都是 Scorer，但必须分别保存结果和证据”的设计。

### 3.6 Harbor——与目标最接近

#### 已核实事实

- Harbor 官方定位是运行 Agent 评测和构建容器化任务的框架，可评测 Claude Code、OpenHands、Codex CLI、Aider 等任意已适配 Agent；官方示例在 Docker 中运行 Terminal-Bench，并可运行 SWE-Bench。参见[官方仓库](https://github.com/harbor-framework/harbor)。
- Harbor 的 Task 同时定义 instruction、environment、test script 和资源/网络限制；dataset 是 Task 集合。`harbor run` 会解析并下载已发布数据集的任务产物。参见[官方运行文档](https://github.com/harbor-framework/harbor/blob/main/docs/content/docs/run-jobs/run-evals.mdx)和[任务格式文档](https://github.com/harbor-framework/harbor/blob/main/docs/content/docs/tasks/index.mdx)。
- Harbor 内置多种 Coding Agent 适配，包括 Claude Code、Copilot CLI、OpenHands、Aider、Codex、Gemini CLI、SWE-agent 等；自定义 Agent 需要实现统一的 setup/run 接口。参见[官方仓库的开发说明](https://github.com/harbor-framework/harbor/blob/main/AGENTS.md)。
- 每个 Trial 输出 config、result、Agent 轨迹和 verifier 产物。Web Viewer 能查看任务结果、奖励、耗时、错误、工具调用、Observation、Token、执行阶段耗时、验证器输出，并能并排比较多个 Job；官方还列出 AI 失败摘要。参见[官方结果查看文档](https://github.com/harbor-framework/harbor/blob/main/docs/content/docs/run-jobs/run-evals.mdx#using-the-viewer)。
- Harbor 使用 ATIF（Agent Trajectory Interchange Format）保存完整交互历史，字段覆盖 Agent 响应、结构化工具调用、环境反馈、Token、成本和时间；并提供轨迹校验器。参见[官方 ATIF 规范](https://github.com/harbor-framework/harbor/blob/main/rfcs/0001-trajectory-format.md)。
- verifier 的 `test.sh` 可产生单一数值奖励或多项数值奖励；验证环境可以与 Agent 环境分离，避免 Agent 看到或污染隐藏判分逻辑。参见[官方 Task 文档](https://github.com/harbor-framework/harbor/blob/main/docs/content/docs/tasks/index.mdx#tests)。
- RewardKit 支持把 `/logs/agent/trajectory.json` 交给 LLM Judge，对 Agent 过程而不仅是最终输出进行 rubric 评分；原始 Judge 回答会保存以便审计。参见[官方 Judge Criteria 文档](https://www.harborframework.com/docs/rewardkit/judge-criteria)。

#### 不能直接覆盖

- Harbor 是评测执行框架，不是已经符合本课程需求的完整管理系统；用户、权限、题目审核、课程批次和定制排行榜仍需自行设计。
- 它没有把“任意 GitHub Agent 源码地址”直接等同为可信被测对象；新增 Agent 仍需适配、安装规则或固定镜像。
- 官方 Viewer 可查看和比较结果，但不等同于 SWE-bench 那种公开提交排行榜。
- Harbor 能生成 AI 失败摘要，但本项目需要的稳定失败类型、复核状态和申诉证据仍需要独立定义。

#### 可复用方式

- 优先评估直接使用 Harbor 承担 Task、Agent、Environment、Trial、Verifier 和 ATIF 轨迹层。
- 本项目把精力放在 Harbor 之上的中文管理页面、评测流程状态、可解释评分、人工复核和课程答辩展示。
- 即使最终不直接依赖 Harbor，也应尽量兼容它的 Task/ATIF 概念，避免发明一套不可互操作的私有协议。

### 3.7 SWE-Gym——题目与训练环境来源，不是完整评测平台

#### 官方定位与组成

- SWE-Gym 官方把自己定义为“用于训练真实软件工程 Agent 的开放环境”，核心由 **2,438 个真实 Python 任务、仓库上下文、可执行环境、测试验证**组成；官方同时发布数据、逐实例预构建 Docker 镜像、模型、轨迹和复现实验脚本。它因此不是单一数据集，但也不是包含用户管理、统一 Agent 接入、排行榜、人工复核和持久化服务的完整 Web 平台。参见[官方 README](https://github.com/SWE-Gym/SWE-Gym/blob/main/README.md)、[官方论文第 3 节](https://arxiv.org/html/2412.21139#S3)和[官方数据集](https://huggingface.co/datasets/SWE-Gym/SWE-Gym)。
- 主仓库明确把环境常量放在独立的 [SWE-Bench-Fork](https://github.com/SWE-Gym/SWE-Bench-Fork)，并要求分别使用固定版本的 [OpenHands 复现实验](https://github.com/SWE-Gym/SWE-Gym/blob/main/docs/OpenHands.md)或 [MoatlessTools 复现实验](https://github.com/SWE-Gym/SWE-Gym/blob/main/docs/MoatlessTools.md)。这说明它的公开代码更接近“数据/环境 + 论文实验组合”，不是一个统一运行任意 Coding Agent 的成品 Harness。

#### 与 SWE-bench Verified 的关系

- SWE-Gym **不是 SWE-bench Verified 的替代名称，也不是 Verified 的扩充 split**。它按照 SWE-bench 的数据收集和执行验证方法构建，但刻意选择了不同的 11 个 Python 仓库，以降低与 SWE-bench 的数据污染。参见[官方论文 3.1 节](https://arxiv.org/html/2412.21139#S3.SS1)。
- SWE-Gym 的主要用途是训练 Agent 和 learned verifier；SWE-bench Verified（500 个经人工筛选的评测实例）在论文中充当独立测试集，用来衡量经 SWE-Gym 训练后的 Agent 是否真正提升。论文报告的是“在 SWE-Gym 上训练，在 SWE-bench Verified/Lite 上评测”。参见[官方论文实验设置](https://arxiv.org/html/2412.21139#S4.SS1)和[官方 README](https://github.com/SWE-Gym/SWE-Gym/blob/main/README.md)。

#### 与题目指定技术框架的逐项对照

符号说明：✅ 原生满足；◐ 只满足一部分，仍需本项目实现关键能力；— 官方 SWE-Gym 不提供。

| 题目要求 | 结论 | 一手来源与边界 |
|---|---:|---|
| `Issue + repo snapshot + FAIL_TO_PASS` 任务格式 | ✅ | 官方数据字段包含 `problem_statement`、`repo`、`base_commit`、`test_patch`、`FAIL_TO_PASS` 和 `PASS_TO_PASS`；论文说明每项任务由 GitHub Issue、Issue 创建时的仓库快照和单元测试组成，Agent 最终产生 git patch。参见[官方数据集字段](https://huggingface.co/datasets/SWE-Gym/SWE-Gym)和[官方论文 3.1 节](https://arxiv.org/html/2412.21139#S3.SS1)。 |
| Docker 隔离执行、资源限额、网络管控 | ◐ | 官方为每个实例发布预构建 Docker 镜像，并使用可执行单元测试验证 patch；但主仓库和论文没有定义本题所需的统一 CPU/内存限额、超时、网络白名单/断网策略与审计接口。Docker 题目环境可复用，资源和网络治理仍需评测 Runner 实现。参见[官方 README 的镜像说明](https://github.com/SWE-Gym/SWE-Gym/blob/main/README.md#reproducing-results)和[官方论文环境构建说明](https://arxiv.org/html/2412.21139#S3.SS1)。 |
| 统一 Runner：stdin 接任务、stdout 输出 patch，并适配 Claude Code/Codex/Aider/自研 Agent | — | 官方复现文档只提供 OpenHands 和 MoatlessTools 两条独立流程，并依赖各自 fork/脚本；没有官方统一 stdin/stdout Runner，也没有核实到 Claude Code、Codex、Aider 的原生适配器目录。参见[OpenHands 复现文档](https://github.com/SWE-Gym/SWE-Gym/blob/main/docs/OpenHands.md)、[MoatlessTools 复现文档](https://github.com/SWE-Gym/SWE-Gym/blob/main/docs/MoatlessTools.md)和[官方主仓库目录](https://github.com/SWE-Gym/SWE-Gym)。 |
| LLM-as-Judge 失败归因分类 + 人工抽检界面 | — | 论文训练了 outcome-supervised learned verifier：读取问题、轨迹和 git diff，估计成功概率并为 Best-of-N 候选排序。这不是通用 LLM-as-Judge，不输出预设失败类型，也没有人工抽检/复核 UI。参见[官方论文 5.1.1 节](https://arxiv.org/html/2412.21139#S5.SS1.SSS1)。 |
| Next.js 15 + React 19 排行榜与报告页 | — | 官方主仓库公开目录只有 `assets/`、`docs/`、`scripts/` 等论文与复现实验资产，没有对应 Web 应用；README 也没有排行榜/报告前端能力说明。参见[官方主仓库目录](https://github.com/SWE-Gym/SWE-Gym)。 |
| PostgreSQL + MinIO 保存补丁、日志和制品 | — | 官方发布数据、模型、轨迹和 Docker 镜像，但没有 PostgreSQL 元数据服务、MinIO/S3 制品服务或相应 schema/API。参见[官方 README 的公开产物说明](https://github.com/SWE-Gym/SWE-Gym/blob/main/README.md)和[官方主仓库目录](https://github.com/SWE-Gym/SWE-Gym)。 |

#### 对“我们要用的就是这个框架”的准确解释

题目把 SWE-Gym 写在“评测框架参考”中，最稳妥的技术解释是：**本项目应原生采用或兼容 SWE-Gym/SWE-bench 风格的任务数据和测试判分方法，并可复用其预构建 Docker 任务环境；但不能假定 SWE-Gym 已经实现题目后面列出的 Runner、沙箱治理、分析 UI、Next.js 前端和 PostgreSQL/MinIO。**这些正是本题要求团队开发或集成的主体部分。

因此，SWE-Gym 与 Harbor 不是简单的二选一：SWE-Gym 更适合作为 **题库/任务规范/可执行环境来源**，Harbor 之类的 Harness 才属于可选的 **多 Agent 执行与轨迹基础设施**。是否引入 Harbor 是后续架构选择；无论是否引入，都可以把 SWE-Gym 任务兼容性作为明确目标。

## 4. 对拟议使用动线的事实判断

用户提出的动线为：

```text
拉取测试的 Agent 代码
→ 启动题目评测
→ 查看 Agent 回答与完整过程节点
→ 根据行为指标辅助评分
→ LLM Judge
```

根据以上项目，核心动线是合理且已有工程先例的，但第一个节点应进一步拆分：

```text
登记 Agent 版本/适配器
→ 准备或拉取可信镜像/安装包
→ 校验 Agent 能否启动
→ 选择题目和固定配置
→ 创建隔离环境并运行
→ 记录不可变轨迹事件
→ 在独立验证环境运行确定性测试
→ 计算过程指标
→ LLM Judge 辅助解释
→ 汇总成绩与完整证据链
```

**事实依据：** Harbor 和 Inspect 都要求外部 Agent 经过明确适配；SWE-bench 接受最终 patch；没有核实到成熟框架把“任意 GitHub 地址直接 clone 后执行”当作安全、通用接口。

**设计建议：** 首月不要做“任意 Agent 仓库自动识别”。先支持两个明确适配的 Agent，并固定 Agent 版本、模型、题目版本、运行镜像和配置；否则分数无法复现，也会引入运行不可信源码的安全风险。

## 5. “工具调用次数代表积极性”的判断

### 已核实事实

- SWE-agent 轨迹能记录 action/observation；OpenHands Rich Logging 明确汇总工具调用次数；Inspect Viewer 可显示工具调用；Harbor ATIF 对每次工具调用、参数、Observation、Token 和成本都有结构化字段。
- Harbor RewardKit 可以让 Judge 读取完整轨迹并判断过程效率，因此“观察 Agent 怎么做”在技术上可实现。

### 建议

**不要因工具调用次数多而直接加分。**调用次数是可观测数据，但不是“积极性”或能力的可靠代理：

- 优秀 Agent 可能一次精准搜索后完成修复；较差 Agent 可能反复读取同一文件、重复运行命令。
- 一旦工具次数能加分，Agent 就可以用无效调用刷分。
- 不同 Agent 把同一动作封装成不同粒度，次数天然不可比。

更稳妥的候选分层是：

1. **硬结果分（最高权重）**：隐藏测试、回归测试、补丁可应用性、超时与资源限制，全部由确定性程序计算。
2. **过程合规分**：是否越权联网、是否访问禁止路径、是否超预算、是否产生无效重复、是否在修改后主动验证。这里依据事件规则，不奖励单纯“多调用”。
3. **效率指标（先展示，不急于计分）**：总耗时、Token、成本、工具调用数、重复调用率、错误调用率。
4. **LLM Judge 辅助项**：代码质量、问题理解、过程合理性和失败原因；必须保存 Judge 模型版本、prompt、输入证据、原始输出和解析结果。

初期可以把工具调用次数放进报告和 Judge 上下文，但不进入总分。等积累真实运行数据后，再决定是否设计经过归一化、不可刷的效率分。

## 6. 对本项目的候选复用优先级

以下为建议，不是已确认架构：

1. **第一优先：验证 SWE-Gym/SWE-bench 风格的最小闭环。**只取一项任务，验证固定仓库版本、Agent 生成 patch、应用 patch、运行 `FAIL_TO_PASS/PASS_TO_PASS` 和保存结果能否在团队电脑跑通。
2. **Runner 层：实现题目明确要求的统一 stdin/stdout 接口。**先适配一个真实 Agent 和一个 Mock Agent；Claude Code、Codex、Aider 后续通过同一 Runner seam 增加 Adapter。
3. **执行层：再比较自研轻量调度与 Harbor/Inspect。**只有在候选框架能复用 Docker、轨迹或调度能力，同时不吞掉本题要求的统一 Runner 时才采用；Harbor 不再被预设为第一选择。
4. **题库层：优先取极少量 SWE-Gym/SWE-bench 风格任务。**完整 SWE-Gym/SWE-bench 对镜像、磁盘、内存和运行时间要求较高，不适合作为首月最低交付线。
5. **判分和展示层：确定性测试为主，LLM Judge 为辅。**分别保存两者的结果和证据；前端可参考现有 Viewer，但自行实现任务状态、证据时间线、人工抽检、评分拆解和 Agent 对比。

## 7. 仍待人类确认的问题

1. “被测 Agent”最终是固定支持两种 CLI Agent，还是允许提交自定义 Agent？
2. 若允许自定义 Agent，提交物应是 Git 仓库、Docker 镜像还是符合接口的安装包？
3. 排行榜是比较“Agent 产品”，还是比较“Agent + 模型 + 配置”这一完整组合？
4. LLM Judge 是参与总分、只生成解释，还是只在确定性测试无法覆盖时使用？
5. 工具调用、Token、成本等过程指标在首月是“仅展示”还是“参与评分”？

这些问题会实质改变 Agent 适配层、隔离边界、数据模型和评分规则，应在架构文档定稿前逐项确认。
