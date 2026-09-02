# Claude Code 接入与黑盒评测核验行动记录

## 状态和情况说明

- 状态：已完成
- 来源请求：用户确认第一版最终目标支持 Codex、Claude Code、Aider、本地自研 Agent 四类，并询问 Claude Code 似乎不开源时能否测试、如何接入和验证。
- 当前阶段：架构讨论与官方接口核验；不安装或运行 Claude Code，不调用付费模型，不编写 Adapter 业务代码。
- 已确认决定：四类 Agent 都进入第一版架构目标；所有 Agent 通过固定登记和统一 Runner seam 接入。
- 需要核验的技术事实：Claude Code 当前源码/许可边界、非交互启动方式、机器可读输出、工具/会话证据、认证方式，以及在本机是否已安装命令。
- 明确排除：不猜测未公开内部实现；不把“CLI 能启动”误报为“已完成真实评测”；不要求获取 Claude Code 源码才能评测。

## 实施措施

1. 已只查阅 Anthropic 官方 Claude Code 文档/仓库，并检查本机 `claude` 命令是否存在。
2. 已把可核验事实与来源写入独立研究记录。
3. 已用黑盒评测思路说明 Adapter 如何把统一任务翻译为 Claude Code 的真实命令，如何提取补丁和证据。
4. 已更新架构文档：记录四类 Agent 目标、Claude Code 接入事实、分层测试和仍需真实凭据验证的限制。
5. 已检查研究、架构和行动记录状态一致。

完成标准：能够基于官方接口而不是臆测，回答“非开源 Agent 为什么仍可评测、怎样接入、什么才算测试成功”。

## 需要修改的文件树

```text
E:\9.1实训\docs\
├─ actions\2026-09-01-claude-code-adapter-feasibility.md
│  # 本次官方接口核验、架构更新和验证证据
├─ research\2026-09-01-claude-code-adapter.md
│  # Claude Code 官方接口、黑盒评测可行性与限制的事实源
└─ architecture\ARCHITECTURE.md
   # 当前架构唯一事实源；同步四类 Agent 目标和 Claude Code Adapter 方案
```

设计关系：`claude_code.py` 是统一 `Agent Runner` interface 的 Adapter；它只依赖 Claude Code 对外公开的 CLI 行为，不依赖其内部源码。Adapter 隐藏命令参数、认证、输出解析和退出原因；Orchestrator 只接收统一补丁与运行摘要。

## 修改后自验证方式

1. 检查每项易变 Claude Code 事实都有 Anthropic 官方链接。
2. 检查本机命令存在性并记录实际结果。
3. 检查文档区分 Adapter 单元/契约测试、CLI 冒烟测试和 SWE-Gym 真实端到端测试。
4. 检查架构明确四类 Agent 是目标，但不声称它们已经实现或跑通。
5. 检查没有安装 Claude Code、没有消耗账号/API 额度、没有创建业务代码。

## 自验证情况

- 官方来源检查：研究记录中的易变接口事实只链接 `code.claude.com` 和 `github.com/anthropics/claude-code` 一手来源，没有引用二手教程。
- 许可边界检查：记录了官方仓库 `All rights reserved`、Anthropic 条款、原版二进制不得修改以及第三方平台不得中转用户 Claude.ai 凭据；没有把 public 仓库误称为开源主实现。
- 本机检查：`Get-Command claude` 返回 `NOT_INSTALLED_OR_NOT_ON_PATH`；没有安装或启动 Claude Code。
- interface 检查：核实了 `claude -p`、stdin、`json/stream-json`、退出码、`--restricted`、工具/会话/usage/成本估算等公开能力。
- Adapter seam 检查：架构明确 Claude 原始 stdout 是轨迹输入；Adapter 在受控工作区提取 `git diff`，再向统一 Runner stdout 返回 patch。
- 四类目标检查：架构约束 `C-10` 已标记本地自研、Codex、Aider、Claude Code 四类实际跑通目标和分阶段顺序，但没有描述成已实现。
- 测试成熟度检查：研究与架构均区分理论可接入、Adapter 契约测试、CLI 冒烟/真实小测试和 SWE-Gym 端到端；当前只达到理论可接入。
- 未执行检查：没有真实 CLI、凭据和题目镜像，因此没有运行 Claude Code 或 SWE-Gym 端到端测试，也没有消耗账号/API 额度。
- 范围检查：新增 1 份研究记录，更新架构文档和本行动记录；没有创建业务代码或安装依赖。
