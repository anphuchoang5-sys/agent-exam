# Agent 登记范围确认行动记录

## 状态和情况说明

- 状态：已完成
- 来源请求：用户在理解两种 Agent 接入方式后选择 A。
- 已确认决定：第一版只运行项目组预先适配、审核并固定版本的 Agent；不支持输入任意 GitHub 地址后自动下载、识别依赖并执行。
- 当前阶段：架构讨论设计，只同步术语和架构文档，不编写业务代码。
- 明确排除：本次不决定首批具体 Agent 清单，不设计最终 Runner JSON schema，不实现 Agent Adapter。

## 实施措施

1. 已在 `CONTEXT.md` 增加“已登记 Agent”领域词义。
2. 已在架构约束中把固定登记模式标记为已确认。
3. 已更新 Agent Runner、安全范围、候选文件树、风险和待确认问题队列。
4. 已检查任意 GitHub 自动执行不再被描述为待确认能力。

完成标准：术语表与架构文档一致表达 A 方案，且首批 Agent 清单仍保持待确认。

## 需要修改的文件树

```text
E:\9.1实训\
├─ CONTEXT.md
│  # 增加“已登记 Agent”的唯一领域定义
└─ docs\
   ├─ actions\2026-09-01-agent-registration-scope.md
   │  # 本次架构决定的修改范围和验证证据
   └─ architecture\ARCHITECTURE.md
      # 当前架构唯一事实源；同步 Agent 登记、安全和 Runner seam
```

设计关系：`Agent Runner` interface 保持统一；`registry.py` 作为 Factory/Registry 只选择允许列表中的 Adapter。新的 Agent 类型通过人工审核后增加 Adapter，不让任意仓库绕过该 seam。

## 修改后自验证方式

1. 检查架构约束表包含已确认的固定登记决定。
2. 检查 Runner 和安全章节同时写明“不自动执行任意 GitHub 仓库”。
3. 检查待确认问题中已移除自定义 Agent 提交形式，但保留首批 Agent 清单问题。
4. 检查 `CONTEXT.md` 新词义不包含具体框架或文件实现细节。

## 自验证情况

- 架构约束检查：`C-08` 已标记“已确认”，内容为只运行项目组预先适配、审核并固定版本的 Agent。
- Runner 检查：新增“Agent 登记范围”，明确 Registry 是允许列表和 Adapter 选择器，不是任意仓库自动安装器。
- 安全检查：不可信代码章节已从“待确认”改为“已确认”，明确不自动执行任意 GitHub Agent 仓库。
- 文件树检查：`custom_process.py` 的职责已同步为只运行符合统一协议并经人工登记的自研 Agent。
- 问题队列检查：已移除“是否允许任意自定义 Agent 提交”的问题；仍保留“首批具体支持哪些已登记 Agent”，没有臆自决定清单。
- 术语检查：`CONTEXT.md` 已定义“已登记 Agent”，且未加入 FastAPI、Docker、Next.js、PostgreSQL、MinIO、Adapter 或 `registry.py` 等实现细节。
- 范围检查：本次只修改 3 个 Markdown 文件，没有创建业务代码或安装依赖。
