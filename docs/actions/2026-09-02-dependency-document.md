# 行动文档：建立项目依赖唯一事实源

## 状态与情况说明

- 状态：已完成
- 来源请求：用户确认 `framework/` 中的第三方框架不上传主仓库；若项目尚无依赖文档，则现在创建，并在其中说明外部框架依赖。
- 当前事实：
  - 项目已有 [`FRAMEWORK_INTERFACES.md`](../interfaces/FRAMEWORK_INTERFACES.md)，负责维护 SWE-Gym 与 SWE-Bench-Fork 的字段级、命令级接口事实，但没有集中维护“依赖来源、固定版本、获取方式、是否入库、验证状态”的依赖清单。
  - 本地 `framework/swe-gym` 与 `framework/swe-bench-fork` 均为独立 Git 仓库，不属于 AgentExam 自有源码。
  - 已知固定提交分别为 `b681068ca20628c6987b7416cc4cf03f06b77ba5` 和 `242429c188fcfd06aad13fce9a54d450470bf0ac`，仍需从本地 Git 元数据重新核验来源与当前提交。
- 已确认决定：
  - `framework/` 不上传 AgentExam 主仓库。
  - `docs/` 属于需要上传和供组员阅读的项目资料。
  - 依赖文档只记录可核验事实；尚未选型或尚未固定版本的依赖必须标为待确认。
- 明确排除：本次不初始化或推送 Git，不删除本地第三方仓库，不安装依赖，不下载数据集或 Docker 镜像，不编写业务代码。

## 实施措施

1. 核对现有架构、接口文档以及两个本地上游仓库的远程来源、固定提交、许可证和安装入口。
2. 创建依赖唯一事实源，记录依赖分类、用途、来源、固定策略、本地目录策略、获取与版本核验方式。
3. 把 `framework/` 的“不进入主仓库”规则写清楚，并说明新成员如何恢复相同依赖。
4. 在总架构和框架接口文档中增加指向依赖事实源的链接，避免重复维护版本事实。
5. 执行链接、提交哈希、Markdown 结构和范围检查，并把实际结果写回本行动文档。

完成标准：新组员只读取依赖文档，即可回答“依赖什么、为什么依赖、去哪里获取、固定到哪个版本、哪些内容不入库、如何验证本地版本”，且专题接口细节仍由框架接口文档维护。

## 实际修改的文件树

```text
docs\
├─ actions\
│  └─ 2026-09-02-dependency-document.md
│     # 本轮依赖文档建设的可追溯行动记录
├─ dependencies\
│  └─ DEPENDENCIES.md
│     # 项目依赖清单、来源、固定版本、获取方式与入库策略的唯一事实源
├─ architecture\
│  └─ ARCHITECTURE.md
│     # 仅增加依赖事实源导航，不复制依赖版本表
└─ interfaces\
   └─ FRAMEWORK_INTERFACES.md
      # 保留真实框架接口事实，并改为引用依赖文档中的版本与获取策略
```

设计关系：`DEPENDENCIES.md` 维护依赖身份与供应链事实；`FRAMEWORK_INTERFACES.md` 维护这些依赖在 AgentExam 中使用的真实接口；`ARCHITECTURE.md` 只提供全局导航。三者职责分离，不构成代码设计模式。

## 修改后自验证方式

1. 使用本地 Git 命令核验两个上游仓库的 `remote.origin.url`、`HEAD` 和工作树状态，预期来源与固定提交均可明确记录。
2. 检查上游许可证和依赖声明文件存在性，预期文档不会臆造许可证、安装命令或运行版本。
3. 使用 `rg` 检查依赖文档包含两个上游名称、完整提交哈希、“不进入主仓库”和恢复/核验命令。
4. 检查所有新增本地 Markdown 链接均能解析到真实文件。
5. 检查本次变更只涉及上述 Markdown 文档，没有初始化 Git、安装依赖、下载数据或修改业务代码。

## 自验证情况

- 上游身份：
  - `framework/swe-gym` 的 `origin` 为 `https://github.com/SWE-Gym/SWE-Gym.git`，`HEAD` 为 `b681068ca20628c6987b7416cc4cf03f06b77ba5`。
  - `framework/swe-bench-fork` 的 `origin` 为 `https://github.com/SWE-Gym/SWE-Bench-Fork.git`，`HEAD` 为 `242429c188fcfd06aad13fce9a54d450470bf0ac`。
  - 两个仓库的 tracked worktree 与 index 均由 `git diff --quiet`、`git diff --cached --quiet` 返回码 0 证明无改动。`git status` 同时报告本机全局 ignore 文件无读取权限；该警告已如实保留，未被误记为仓库改动。
- 许可证与安装入口：固定源码确认 SWE-Gym 为 Apache-2.0、SWE-Bench-Fork 为 MIT；Fork 包内版本为 `2.0.13`，声明 Python `>=3.8`，直接依赖没有精确版本约束。本次未执行安装命令。
- 内容完整性：`DEPENDENCIES.md` 已检出两个上游名称、两条完整提交哈希、不进入主仓库规则、恢复/核验命令、许可证，以及 FastAPI、Next.js、React、Docker、PostgreSQL、MinIO 和目标 Agent 的待锁定状态。
- 文档链接：检查 4 个本轮文件的相对 Markdown 链接，失效数为 0；`FRAMEWORK_INTERFACES.md` 指向 `../../framework/` 的本地链接已清零，证据改为固定提交的公开链接。
- Markdown 结构：4 个本轮文件代码围栏计数均为偶数。
- 范围检查：项目根目录仍不存在 `.git`，`apps/` 业务文件数为 0；本次没有初始化或推送 Git，没有安装依赖、下载数据/镜像、运行 Docker/Harness 或编写业务代码。
- 剩余限制：精确 SWE-Gym dataset ID/revision/split、镜像 digest、项目运行时与 Agent CLI 版本，以及 Fork 未锁 Python 依赖仍待后续确认；不能把静态源码核验描述为端到端已运行。
