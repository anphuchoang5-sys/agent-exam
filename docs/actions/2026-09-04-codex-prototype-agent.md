# 行动文档：确认 Codex 为首个真实原型 Agent

## 状态与情况说明

- 状态：已完成。
- 来源请求：用户在首个真实原型 Agent 选择中确认使用 Codex。
- 已有事实：首个原型数据范围已经固定为 `SWE-Gym/SWE-Gym-Lite` 的 1～3 道真实任务；Harbor 是正式 Execution Backend；固定 SWE-Bench-Fork 是唯一确定性判卷入口。
- 本次确认：第一个跑通 Issue→Harbor→patch→固定 Fork 的真实 Agent 是 Codex；其他 Agent 在该闭环通过后再扩展。
- 仍待确认/核验：容器内 Codex CLI 固定版本、模型 ID、API Key 或认证文件方式、模型端点、网络白名单、预算和真实运行结果。
- 明确排除：本次不安装或运行 Codex/Harbor，不读取或写入密钥，不选择模型和认证方式，不修改业务代码，不提交或推送 Git。

## 实施措施

1. 在总架构决定、验证门槛和下一轮队列中记录 Codex 首发选择。
2. 在 Harbor 接口中明确首个真实 Agent 为 Harbor 内置 Codex Adapter，同时保留版本、模型与认证待定边界。
3. 在框架接口与依赖事实源中同步 Codex 的首发状态，不把 Windows 宿主 CLI 与容器内 CLI 混为一谈。
4. 执行差异、格式、围栏、链接和事实一致性检查，记录实际结果。

完成标准：相关权威文档一致表达“首个原型 Agent=Codex”，且没有声称 Codex 容器版本、模型、凭据或 E2E 已经跑通。

## 需要修改的文件树

```text
E:\9.1实训\
└─ docs\
   ├─ actions\2026-09-04-codex-prototype-agent.md
   │  # 本次 Agent 选择、范围和验证证据
   ├─ architecture\ARCHITECTURE.md
   │  # 已确认决策、真实 Agent 门槛和下一轮问题
   ├─ dependencies\DEPENDENCIES.md
   │  # Codex CLI 的项目用途与当前验证状态
   └─ interfaces\
      ├─ HARBOR_EXECUTION.md
      │  # Harbor Codex 原型输入与未决配置
      └─ FRAMEWORK_INTERFACES.md
         # Codex 宿主/容器能力状态和分层验证顺序
```

设计关系：Codex 是 Harbor `AgentConfig` 选择的一种被测 Agent，不成为上层模块依赖。`HarborExecutionAdapter` 仍负责把平台配置翻译为 Harbor Codex 配置，Job Orchestrator 不直接调用 Codex CLI。

## 修改后自验证方式

1. `git diff --check` 无错误。
2. 四份权威文档均能检出 Codex 首个真实原型事实。
3. 仍能检出 CLI 版本、模型、认证和 E2E 待确认/待实测表述。
4. 目标 Markdown 无尾随空白，代码围栏成对，相对链接存在。
5. Git 状态没有业务源码、密钥或运行产物变化。

## 自验证情况

- `git diff --check`：通过；仅出现 Git 的未来 LF→CRLF 提示，不是差异错误。
- 文件与格式：5 份目标文档均存在、无尾随空白，代码围栏成对。
- 已确认事实：总架构、依赖事实源、Harbor 接口和框架接口都明确首个真实原型 Agent 为 Codex。
- 未知边界：四份权威文档均明确 Codex CLI 版本、模型、认证和/或网络能力仍待确认或实测；框架能力表继续记录 Codex 的真实账号/模型与 SWE-Gym E2E 尚未通过。
- 首次自动检索使用过窄的同义词模式只统计到 3/4 份未决边界，因此检查返回失败；逐行展开后确认第 4 份总架构也明确写有“CLI 版本、模型、认证方式和网络策略仍待确认或实测”，属于检查表达式误报。
- 范围：Git 状态只有讨论阶段 Markdown 文档变化；没有读取/写入密钥，没有安装、运行、提交或推送。
