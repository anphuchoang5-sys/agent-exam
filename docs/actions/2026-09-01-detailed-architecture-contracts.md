# 细化架构与接口契约行动记录

## 状态和情况说明

- 状态：已完成
- 来源请求：用户接受单机总体方案，但指出现有架构文档不够清晰，要求把每个模块的大致职责、输入、输出、接口，以及需要调用的上游框架接口分别形成可持续维护的文档。
- 当前阶段：架构讨论设计；本次只创建和更新 Markdown 文档，不实现业务代码、不安装依赖、不运行评测。
- 已确认事实：
  - 项目直接使用 SWE-Gym 的任务数据，并直接使用其配套 SWE-Bench-Fork 完成确定性评测。
  - 系统采用单台物理机上的模块化单体：Next.js 15 + React 19、FastAPI、Python Worker、PostgreSQL、MinIO 和 Docker。
  - 第一阶段支持本地自研 Agent、Codex、Aider、Claude Code；它们通过统一 Runner 协议和各自 Adapter 接入。
  - 排行榜比较单位是固定版本的 Agent 配置，即 Agent、模型和行为配置的组合。
  - 轨迹、补丁、测试输出和 Judge 原始响应必须可追溯；确定性测试事实、Judge 分析和人工复核分别保存。
- 文档状态规则：
  - “已确认”表示用户已确认的项目决定。
  - “已核验”表示已从本地上游源码或官方文档查到的外部接口事实。
  - “候选 v0.1”表示供本轮继续讨论的项目自定义契约，尚未实现，也不是上游现成接口。
  - “待确认/待实测”表示不能写成既成事实的内容。

## 实施措施

1. 把 `ARCHITECTURE.md` 收缩为全局入口，只维护系统边界、关键流程、依赖方向、确认决定、候选文件树和文档导航。
2. 新建模块契约文档，逐个记录模块职责、调用方、输入、输出、错误、不变量、依赖和验证点。
3. 新建统一 Runner 协议文档，明确 stdin、stdout、stderr、退出状态、轨迹副通道和保密边界。
4. 新建框架接口文档，只记录从 SWE-Gym、SWE-Bench-Fork、Codex、Aider 和 Claude Code 的源码或官方文档核验过的真实接口，并把 Adapter 映射与上游事实分开。
5. 新建 HTTP API 候选契约，明确前端与后端之间的请求、响应、错误格式和接口状态。
6. 新建数据模型文档，明确 PostgreSQL 元数据和 MinIO 制品的边界、实体关系、运行状态与对象键规则。
7. 更新所有文档的交叉链接，避免在多个文件复制维护同一事实。
8. 完成后执行链接、标题、Mermaid、术语、状态标签、接口字段和范围检查，并把实际结果更新到本文档。

完成标准：新成员只读总架构和对应契约文档，即可回答“模块做什么、吃什么、吐什么、失败时怎样表示、依赖哪个真实上游接口、哪些内容仍待确认”，而不需要从聊天记录猜测。

## 需要修改的文件树

```text
E:\9.1实训\
└─ docs\
   ├─ actions\
   │  └─ 2026-09-01-detailed-architecture-contracts.md
   │     # 本轮范围、实施偏差、验证方法和实际验证证据
   ├─ architecture\
   │  ├─ ARCHITECTURE.md
   │  │  # 全局架构唯一事实源和细分文档入口；不重复字段级契约
   │  ├─ MODULE_CONTRACTS.md
   │  │  # 项目内部模块职责及输入/输出契约的唯一事实源
   │  └─ DATA_MODEL.md
   │     # PostgreSQL 实体关系、运行状态和 MinIO 制品布局的唯一事实源
   ├─ interfaces\
   │  ├─ RUNNER_PROTOCOL.md
   │  │  # 所有 Agent Adapter 对外呈现的统一 stdin/stdout 协议
   │  ├─ HTTP_API.md
   │  │  # Next.js 与 FastAPI 之间的候选 HTTP 接口契约
   │  └─ FRAMEWORK_INTERFACES.md
   │     # 已核验的上游框架/CLI 接口及其到本项目 Adapter 的映射
   └─ research\
      └─ 2026-09-01-aider-cli-interface.md
         # Aider 官方 CLI 接口的来源、事实、限制和待实测项
```

文档职责关系：`ARCHITECTURE.md` 回答“系统整体怎样组成”；`MODULE_CONTRACTS.md` 回答“内部模块怎样协作”；`RUNNER_PROTOCOL.md` 与 `HTTP_API.md` 回答“边界上怎样交换数据”；`FRAMEWORK_INTERFACES.md` 回答“我们实际复用哪些上游接口”；`DATA_MODEL.md` 回答“状态和证据存在哪里”；研究记录保存接口事实的查证过程。

设计模式关系：

- Adapter：各 Agent Adapter 把不同 CLI/进程行为转换为 `RUNNER_PROTOCOL.md` 的统一契约。
- Factory/Registry：Agent Registry 依据已登记 Agent 配置选择 Adapter，不接受任意命令。
- Repository：后端领域模块通过 Repository 边界访问 PostgreSQL 和 MinIO，不直接散落存储语句。
- State：评测运行只能按 `DATA_MODEL.md` 定义的状态迁移前进。

## 修改后自验证方式

1. 检查上述所有文件均存在，且每份文档都有状态、维护责任或权威边界说明。
2. 检查模块契约中的每个模块都有职责、输入、输出、错误、不变量、依赖和验证点。
3. 检查 Runner 文档明确 stdin、stdout、stderr、退出状态、轨迹文件、敏感字段禁止暴露规则，并区分空补丁与基础设施失败。
4. 检查框架接口文档能够追溯到本地 SWE-Gym/SWE-Bench-Fork 源码或各工具官方文档；未核实接口必须标成待实测。
5. 检查 HTTP API 的每个端点至少有方法、路径、输入、成功输出和错误语义，并明确它是候选 v0.1 而不是已实现接口。
6. 检查数据文档中的数据库实体、MinIO 制品和模块输入输出名称一致。
7. 用脚本检查 Markdown 相对链接指向的本地文件存在，代码围栏成对闭合。
8. 检查 Mermaid 代码块结构闭合；若本机无 Mermaid 渲染器，如实记录只做源码检查。
9. 用 `rg` 检查“已确认”“已核验”“候选 v0.1”“待确认/待实测”状态没有混用。
10. 确认本次没有创建业务源代码、安装依赖或执行 Agent/评测。

## 自验证情况

- 文件存在性：计划中的 8 个本轮文件全部存在，缺失数为 0；其中新增 5 份架构/接口契约、1 份 Aider 研究和本行动记录，重构 1 份总架构文档。
- 模块完整性：`MODULE_CONTRACTS.md` 检出 15 个逐模块章节；“输入、输出、错误、不变量、依赖、验证”各检出 15 行，模块总表和跨模块规则也已覆盖。
- HTTP 契约：`HTTP_API.md` 检出 15 个带方法和 `/api/v1` 路径的端点；创建运行、查询、轨迹、制品、报告、排行榜和人工复核均含输入/输出及错误说明。
- Runner 契约：已人工核对 JSON stdin、纯 patch stdout、诊断 stderr、统一退出原因、旁路 `trajectory.jsonl`/`result.json`、空补丁语义、Git patch 提取和隐藏答案禁止暴露规则。
- 框架事实：已从本地固定提交核验 SWE-Gym README、SWE-Bench-Fork 的 `constants.py`、`utils.py`、`run_evaluation.py` 和 Harness 文档；两个提交仍分别为 `b681068ca20628c6987b7416cc4cf03f06b77ba5`、`242429c188fcfd06aad13fce9a54d450470bf0ac`。
- Agent 接口：Codex 使用 OpenAI 官方非交互/CLI 文档核验；Claude Code 沿用既有官方研究记录；Aider 后台研究新增官方资料记录，并明确它缺少结构化工具事件流和默认自动提交风险。三者均未被误写成已真实跑通。
- Codex 本机限制：尝试执行 `codex --version` 和 `codex exec --help` 时，WindowsApps 打包的 `codex.exe` 被操作系统拒绝启动；因此只记录官方接口已核验，没有记录虚假的本地版本/Adapter 通过状态。
- 链接检查：扫描 8 个本轮文档的 Markdown 本地链接，断链数为 0。
- Markdown 结构：8 个文档的 fenced code block 总计 72 个，所有文件的 fence 数均为偶数；Mermaid 源码共 8 个。
- Mermaid 限制：本机未发现 `mmdc`，没有执行图形渲染；只完成 Mermaid 围栏结构和源码人工检查，不能描述为渲染通过。
- 状态与唯一事实源：总架构已改为导航和全局决定；字段级内容分别指向模块、Runner、HTTP、数据和框架接口文档。文档明确区分“已确认/已核验/候选 v0.1/待确认/待实测”。
- 范围检查：`apps` 下没有业务文件，本次未创建业务源代码、未安装依赖、未运行 Agent、Docker 或 Harness。
- 仓库限制：`E:\9.1实训` 当前不是 Git 仓库，`git status --short` 无法提供顶层文档 diff；已改用明确文件清单、链接扫描和内容计数验证。
- 验证脚本偏差：第一次 PowerShell 检查因字符串中变量后紧跟冒号导致解析错误；修正变量边界后已重新完整执行并得到上述结果，未把失败的首次运行描述为通过。
