# LYQ 开发过程文档

> 维护人：LYQ（五人分工中的成员 C，负责「目录与配置」Module）
> 建立日期：2026-09-20

本目录归集 **C 模块负责人的开发过程材料**：我负责模块的个人视图、计划、进度日志和问题记录，目的是让开发过程可追溯、便于交接与复盘。

目录结构参照成员 E 已建立的 [`docs/LLY/`](../LLY/) 约定；该目录现已在本仓库 `main` 中，可直接阅读。早期仅能从成员分支读取的说明已过时。

## 这个目录不放什么（重要）

项目已有权威文档，同一事实只在**一处**维护。以下内容必须写在权威位置，本目录只用链接引用：

| 事实类型 | 权威位置 |
|---|---|
| 系统架构、模块边界、依赖方向 | [`docs/architecture/`](../architecture/) |
| HTTP 路由与请求/响应 | [`docs/interfaces/HTTP_API.md`](../interfaces/HTTP_API.md) |
| 表结构、状态机、对象键 | [`docs/architecture/DATA_MODEL.md`](../architecture/DATA_MODEL.md) |
| 本机部署与运维事实 | [`docs/operations/`](../operations/) |
| 已实施行动的过程与证据 | [`docs/actions/`](../actions/) |
| 团队分工与任务归属 | [`TEAM_WORK_ALLOCATION.md`](../architecture/modules/TEAM_WORK_ALLOCATION.md) |
| 扩展任务 01–08 的正式计划 | [`.scratch/ui-catalog-providers/plan.md`](../../.scratch/ui-catalog-providers/plan.md) |
| 我负责模块的权威架构 | [`catalog-and-configuration/ARCHITECTURE.md`](../architecture/modules/catalog-and-configuration/ARCHITECTURE.md) |

**规则：** 某项事实一旦成为项目级结论（别人也要用它），必须提升到上表对应的权威文档，并在本目录只留链接。不要在本目录复制字段表、路由表或数据库表结构，否则会出现两份会各自过期的事实。

## 分类

| 目录 | 放什么 |
|---|---|
| [`01-plan/`](01-plan/) | 我负责范围的计划书、阶段拆分、待确认事项 |
| [`02-module/`](02-module/) | 我负责模块的架构、输入输出契约、接口的**个人视图**；正文仍在权威文档 |
| [`03-progress/`](03-progress/) | 进度日志，按日期倒序追加，只记事实与实际结果 |
| [`04-issues/`](04-issues/) | 已记录的问题：现象、证据、处理过程、遗留风险 |
| [`05-sessions/`](05-sessions/) | 与 AI 助手的协作过程记录：按阶段记问了什么、查到什么事实、做了什么改动 |
| [`06-environment/`](06-environment/) | 我本机的开发环境事实与命令（Python 3.13 + 便携 PostgreSQL）。编号接在既有目录之后；E 的同类目录是 `docs/LLY/02-environment/` |

## 当前状态

- 长期 Module：**目录与配置**（Task Catalog 题目目录 + Agent Registry 配置目录）
- 任务 04 的五道新题已进入六题受控目录，`continuous(1–20)` 已在服务端和向导落地；代码位置、实际验证和剩余边界分别见[目录与配置 Module](../architecture/modules/catalog-and-configuration/ARCHITECTURE.md)、[Job 控制 Module](../architecture/modules/job-control/ARCHITECTURE.md)与[当前交接](../../HANDOFF.md)。本目录原有“准备阶段”“未开工”和测试数量仅代表 2026-09-20 时点，不再作为当前结论。
- LYQ 本机环境的时点记录见 [`06-environment/LOCAL_SETUP.md`](06-environment/LOCAL_SETUP.md)；运行态、端口与依赖是否仍相同须在那台机器现场核对。
- 计划书：[`01-plan/PLAN.md`](01-plan/PLAN.md)
- 问题记录：[`04-issues/KNOWN_ISSUES.md`](04-issues/KNOWN_ISSUES.md)（以记录内时点和状态为准）
- 协作过程记录：[`05-sessions/2026-09-19_20-collaboration-record.md`](05-sessions/2026-09-19_20-collaboration-record.md)
- 对应行动记录：[任务 04 行动文档](../actions/2026-09-19-task-04-catalog-candidates-and-scale.md)、[本机环境行动文档](../actions/2026-09-20-local-environment-setup.md)

## LYQ 个人 Git 流程记录（2026-09-20 时点）

以下命令只记录 LYQ 当时 fork 工作区的做法，不描述当前 `E:\9.1agent_exam` 的远端或分支。当前工作区须先用 `git remote -v`、`git branch -vv` 和 `git status` 核对；不能把这里的 `origin`、`upstream` 或 `lyq` 直接套用。

```bash
git branch                 # 看当前在哪个分支，应该是 lyq
git fetch upstream         # 拉取团队最新提交（不动我的工作区）
git rebase upstream/main   # 把我的提交挪到团队最新之上
git status                 # 看改了哪些文件
git add <文件>              # 把改动放进待提交区
git commit -m "说明"        # 提交
git push                   # 推到我自己的 fork 的 lyq 分支，上游 PR 会自动更新
```

注意事项：

- GitHub 在本机的连通性不稳定（见 [ISSUE-01](04-issues/KNOWN_ISSUES.md)）：**当前配置为直连**（仓库本地 `http.proxy` 已移除）。报 `Failed to connect to github.com port 443` 超时时，开 Clash 并执行 `git config --local http.proxy http://127.0.0.1:7892`；报 `Failed to connect to 127.0.0.1 port 7892` 时，说明代理没在跑，用 `git config --unset http.proxy` 切回直连。恢复克隆或换机器后必须重新确认这条配置。
- `git push` 只会推到我的 fork，不影响团队仓库；从 fork 到上游的 PR 已经开好，push 之后 PR 会自动更新。
- 不要在没有明确授权时推送 `main`；合并由组长在 PR 页面操作。
- 写文档前先确认事实来源：能查代码的查代码，需要人类判断的（业务规则、范围）先问组长。
