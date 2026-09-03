# 行动文档：比较 Harbor 与 AgentExam Runner

## 状态与情况说明

- 状态：已完成；研究输出后来在 2026-09-03 被正式架构决定吸收。
- 来源请求：组内有人建议 Runner 模块可以使用 Harbor；用户要求核对并讨论。
- 当前事实：AgentExam 已确认 SWE-Gym 是任务来源、SWE-Bench-Fork 是确定性判卷入口；自定义 Agent Runner 的候选接口是 `RunRequest → AgentRunResult`，负责启动登记 Agent、提取补丁和保留轨迹，不负责判定 `resolved`。
- 研究问题：Harbor 固定版本的 Agent、Environment、Task、Trial、trajectory 与适配能力；能否只实现 Runner 接口而不替换 SWE-Gym/SWE-Bench-Fork 语义；引入后的代码量、双重编排和单机资源风险。
- 明确排除：本次只研究和讨论，不采用 Harbor、不修改已确认架构、不安装或运行 Harbor、不编写业务代码。

## 实施措施

1. 只查 Harbor 官方仓库、官方文档和源码，固定本次核验版本。
2. 将 Harbor 能力逐项映射到 Agent Runner、Sandbox Controller、Trajectory Recorder 和 Patch Evaluator。
3. 比较三种方案：自研 Runner、Harbor 作为 Runner Adapter、Harbor 接管整条评测链路。
4. 给出适合单机、一个月、约 2.5 人团队的建议和必须实测的风险，不把建议写成已确认决定。
5. 将来源化结论写入独立研究文档并验证链接和范围。

## 需要修改的文件树

```text
docs\
├─ actions\2026-09-02-harbor-runner-comparison.md
│  # 本轮研究范围、措施和验证证据
└─ research\2026-09-02-harbor-runner-comparison.md
   # Harbor 官方能力与 AgentExam Runner 的来源化比较结论
```

设计关系：研究候选把 Harbor 视为可能实现 `Agent Runner` interface 的 Adapter；只有在不泄漏 Harbor 类型、不改变 SWE-Gym 任务和 SWE-Bench-Fork 判卷事实时，这个 seam 才成立。

后续状态：团队已在 [`2026-09-03-harbor-execution-backend-architecture.md`](./2026-09-03-harbor-execution-backend-architecture.md) 中把候选 seam 收口为正式 `ExecutionBackend`，并在 [`ADR-0001`](../adr/0001-use-harbor-as-execution-backend.md) 记录采用决定和退出条件。本行动文档保留当时的研究范围，不继续维护当前架构事实。

## 修改后自验证方式

1. 核对所有 Harbor 事实来自固定官方源码/文档链接。
2. 检查研究文档明确区分官方能力、项目推论和待实测项。
3. 检查三种集成方案均覆盖职责、输入输出、优势、代价与冲突。
4. 检查没有把研究建议写入已确认架构，没有安装/运行 Harbor 或修改业务代码。
5. 检查 Markdown 相对链接和代码围栏结构。

## 自验证情况

- 固定 Harbor 提交的 README、包清单、SWE-Gym Adapter、Agent、Trial 和结果模型均已通过官方源码静态核验并记录来源。
- 研究文档已分别说明 Harbor 的已核验能力、AgentExam 推论、三种集成方案以及仍需真实原型验证的 `model_patch`、轨迹、网络和资源风险。
- 研究阶段没有安装或运行 Harbor，也没有修改业务代码；这些限制已如实保留。
- 2026-09-03 提交前复检：本行动文档相对链接目标存在、代码围栏成对、没有高置信度密钥格式。
