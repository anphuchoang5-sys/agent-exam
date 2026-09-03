---
status: accepted
date: 2026-09-03
---

# 使用 Harbor 作为执行后端，而不是最终判卷平台

AgentExam 采用 PostgreSQL 管理用户提交的评测 Job 队列，通过一个小型 `ExecutionBackend` interface 调用固定提交的 Harbor；Harbor 负责把多个 Agent×多个任务展开为 Trial、运行 Agent、管理 Docker 环境并收集轨迹与制品。每个 Trial 生成的补丁仍由 AgentExam 交给固定 SWE-Bench-Fork 独立判卷，Harbor reward 不作为最终正确性事实。

## 为什么这样决定

- 全部自研 Runner、Agent 适配、沙箱和轨迹会超过一个月、2.5 人的可控范围。
- 让 Harbor 接管课程用户、数据库、MinIO、排行榜、人工复核和最终判卷，会吞掉 AgentExam 自己的产品边界，并与题目指定的固定 SWE-Bench-Fork 证据链冲突。
- 把 Harbor 放在 Adapter 后面，可以复用其 Agent、Environment、Job/Trial 和 ATIF 能力，同时让业务层只理解“执行请求进去，补丁与证据出来”。

## 后果与退出条件

- 首版每次只领取一个平台评测 Job，并固定 Harbor `n_concurrent_trials=1`；单个 Job 内的 Trial 顺序执行。
- Harbor 固定到 [`DEPENDENCIES.md`](../dependencies/DEPENDENCIES.md) 记录的完整提交；升级必须先更新依赖事实源、重新核验接口并跑契约测试。
- Harbor `TrialResult` 没有已核验的标准 `model_patch` 字段；首次真实单题原型必须证明能在环境清理前可靠提取 Git diff、保存轨迹、执行资源/网络限制并由固定 Fork 判卷。
- 若原型在限定验证周期内不能满足上述门槛，只替换 `HarborExecutionAdapter` 为自研轻量 `ProcessExecutionAdapter`，不改变评测 Job、评测运行、报告或 HTTP interface。
- Mock 只用于内部软件测试，禁止进入正式展示、报告和排行榜。
