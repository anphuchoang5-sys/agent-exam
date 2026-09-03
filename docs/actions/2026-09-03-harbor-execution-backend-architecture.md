# 行动文档：收口 Harbor 执行后端架构

## 状态与情况说明

- 状态：已完成（文档架构收口完成；Harbor 运行验收属于后续实施任务）。
- 来源请求：用户确认把 Harbor 定为“带验收退出条件的正式执行后端”，并要求把已确认讨论同步为项目事实。
- 当前事实：架构文档仍以自研 `Agent Runner + Sandbox Controller` 为主，Harbor 研究文档仍标为候选；数据模型只有单个 Agent×单个任务的 `evaluation_runs`，尚无平台批次与 Harbor Job/Trial 的清晰映射。
- 已确认决定：PostgreSQL 管理平台级评测 Job 队列；单机同时只运行一个重型 Job；Harbor Job 承担 Agent 执行并展开多个 Agent×多个任务为 Trial；固定 SWE-Bench-Fork 是唯一最终确定性判卷；Mock 只用于内部软件测试；正式展示、报告和排行只接受真实 Agent 运行。
- 已确认接入范围：可信任的组员/教师/同学可提交固定 Git URL + commit 的 Agent 仓库；仓库必须声明 `agent-exam.yaml`，经管理员审核后才能进入评测。
- 固定上游事实：Harbor 提交 `6af8d6e31eced13b93849cdf80feeadf24603d15` 的 `JobConfig` 包含 `agents`、`datasets`/`tasks`、`n_attempts`、`n_concurrent_trials`、环境和制品配置；`JobPlan` 按 attempts×tasks×agents 展开 `TrialConfig`；`TrialResult` 不保证存在标准 `model_patch` 字段。
- 验收退出条件：首次真实单题原型必须能稳定生成 `model_patch`、保留可追溯轨迹、执行资源/网络限制，并把补丁交给固定 Fork 独立判卷；若不能在限定验证周期内满足，则只替换 Harbor Adapter 为自研轻量执行实现，不改上层业务接口。
- 明确排除：本次不安装或运行 Harbor，不下载 SWE-Gym 数据/镜像，不执行真实 Agent 或 Harness，不创建业务代码/数据库迁移，不推送 Git，不把未实测能力写成“已跑通”。

## 实施措施

1. 在 `CONTEXT.md` 统一“Agent 源码提交、评测 Job、评测运行”的领域含义；Harbor Job/Trial 属于实现映射，只在接口文档定义，不污染领域词汇表。
2. 新建 ADR，记录为何采用 PostgreSQL 平台队列 + Harbor 执行 + 固定 Fork 判卷，而不是 Harbor 全盘接管或全部自研。
3. 更新总架构、Mermaid 数据流、确认决策、候选文件树、设计模式、风险与验证门槛。
4. 把外部执行 seam 收口为深模块 `Execution Backend`；Harbor Adapter 隐藏 Job 配置、Trial 目录、ATIF、环境和异常翻译细节。
5. 增加 Harbor 执行接口文档，逐项记录 AgentExam 输入、Harbor 固定提交真实字段、输出、制品和错误映射；未知项保持待实测。
6. 扩展数据模型和 HTTP 接口，使一个平台 Job 可冻结多个 Agent 与多个任务，并由多条 `evaluation_runs` 表示逐 Trial 尝试。
7. 调整统一 Runner 协议：保留为自研 Agent 仓库/后备实现的逻辑协议，不再谎称所有 Harbor 内置 Agent 都直接使用 stdin/stdout。
8. 将 Harbor 加入依赖唯一事实源，并把研究文档状态从“候选建议”更新为“架构已采纳、运行待验收”。
9. 执行跨文档术语、链接、Mermaid 围栏、旧结论和 Git 格式检查；记录实际结果。

完成标准：所有权威文档一致表达已确认方案；事实与候选/待实测明确区分；上层只依赖 Execution Backend interface；不存在“Harbor 已本机跑通”或“Mock 可进入正式成绩”的错误描述。

## 需要修改的文件树

```text
E:\9.1实训\
├─ CONTEXT.md
│  # 领域词汇唯一事实源；定义评测 Job 与评测运行，不放实现细节
└─ docs\
   ├─ actions\2026-09-03-harbor-execution-backend-architecture.md
   │  # 本次架构收口的范围、措施、文件树与验证证据
   ├─ adr\0001-use-harbor-as-execution-backend.md
   │  # 已接受的难逆转架构取舍及退出条件
   ├─ architecture\
   │  ├─ ARCHITECTURE.md
   │  │  # 总体拓扑、数据流、项目文件树、设计理由和风险
   │  ├─ MODULE_CONTRACTS.md
   │  │  # Execution Backend 深模块及上下游模块输入输出
   │  └─ DATA_MODEL.md
   │     # 平台 Job、Job 选择项、逐 Trial 运行及状态/队列关系
   ├─ interfaces\
   │  ├─ HARBOR_EXECUTION.md
   │  │  # AgentExam↔Harbor 固定提交的输入、输出、字段映射和验收门槛
   │  ├─ RUNNER_PROTOCOL.md
   │  │  # 自研 Agent/后备 Runner 的逻辑协议，不冒充 Harbor 原生接口
   │  ├─ HTTP_API.md
   │  │  # Web 创建/查询/取消平台 Job 与读取逐运行结果的契约
   │  └─ FRAMEWORK_INTERFACES.md
   │     # 上游框架清单新增 Harbor 身份和指向专门接口文档
   ├─ dependencies\DEPENDENCIES.md
   │  # Harbor 来源、固定提交、不进主仓库和未安装状态
   └─ research\2026-09-02-harbor-runner-comparison.md
      # 研究结论状态改为已采纳，保留未实测风险
```

设计关系：`ExecutionBackend` 是外部执行 seam；`HarborExecutionAdapter` 是主 Adapter，未来 `ProcessExecutionAdapter` 是验收失败时的后备 Adapter。两者向 Orchestrator 返回相同的执行结果，调用方不学习 Harbor 内部类型。PostgreSQL Repository 只管理平台 Job/运行状态，Harbor Job 只管理一次执行批次内部的 Trial。固定 SWE-Bench-Fork Evaluator 位于执行后端之后，不接受 Harbor reward 替代。

## 实际变更与计划偏差

- 已按文件树更新领域词汇、总架构、模块契约、数据模型、HTTP/Runner/框架接口、依赖事实源和研究结论，并新增 Harbor 专门接口与 ADR。
- 领域词汇表只增加“Agent 源码提交、评测 Job、评测运行”。Harbor Job/Trial 是实现术语，留在架构和接口文档；这是为保持领域模型不依赖具体框架所作的边界收紧。
- 执行证据职责进一步明确为：Harbor Adapter 先把 patch、轨迹、日志和原始结果写入 MinIO 并返回 `ArtifactRef`；Job Orchestrator 再按 `patch_ref` 读取同一份已校验字节交给固定 Fork，避免重复保存或字节不一致。
- 没有创建业务源码、数据库迁移或恢复脚本；没有安装/运行 Harbor、SWE-Gym 数据或 SWE-Bench-Fork；没有推送 Git。

## 修改后自验证方式

1. `git diff --check`：无行尾空格或补丁格式问题。
2. Markdown 相对链接检查：本次新增/修改文档中的本地链接目标全部存在。
3. 围栏检查：Markdown 代码围栏成对；Mermaid 块包含平台 Job→Harbor Job→Trial→Patch→固定 Fork 的真实链路。
4. 术语检查：`CONTEXT.md` 只含领域词义；实现细节只出现在架构/接口/ADR。
5. 事实检查：检出固定 Harbor commit、`JobConfig`、`TrialConfig`、`n_concurrent_trials=1`、`model_patch` 缺口和固定 Fork 判卷权。
6. 冲突检查：不得残留“Harbor 仍未形成架构决策”“PostgreSQL 逐条调度重型 Trial”“所有 Agent 必须原生 stdin/stdout”“Mock 可用于正式结果”等旧结论。
7. 数据一致性：一个平台 Job 能映射多 Agent×多任务的 `evaluation_runs`，且每条运行只对应一个 Agent×一个任务×一次尝试。
8. 范围检查：没有新增业务源代码、安装依赖、运行 Harbor/SWE-Gym/Harness 或推送 Git。

## 自验证情况

- `git diff --check`：通过；只有 Git 关于未来 LF→CRLF 转换的提示，不是差异错误。
- 目标文件存在性：12 份本次目标文档全部存在。
- Markdown 格式：12 份文档均无尾随空白；所有代码围栏计数为偶数；没有重复标题。
- 本地链接：本次目标文档内的相对链接全部能解析到现有文件或目录。
- 术语/冲突：当前权威文档未检出 `Run Submission`、`Run Orchestrator`、`Sandbox Controller`、旧的 Harbor 候选结论或普通用户 `POST /api/v1/runs` 等遗留断言。
- 关键事实：已检出平台 Job→Harbor Job、Run→Trial、`n_concurrent_trials=1`、`TrialResult` 无标准 `model_patch`、固定 Fork 唯一判卷、运行不是独立数据库队列和 Mock `internal_test` 隔离。
- 领域边界：`CONTEXT.md` 未检出 Harbor、PostgreSQL、MinIO、Docker、FastAPI、Next.js 或 SWE-Bench 等实现名。
- 依赖状态：`framework/harbor` 当前确实不存在；`git check-ignore` 证明 `.gitignore` 的 `/framework/` 规则会忽略未来恢复目录。
- 范围：Git 状态显示本次内容均为 Markdown 文档；工作区另有先前 Docker/Harbor 研究行动文档仍未提交，本次未删除、覆盖或推送它们。
- 限制：本次只做静态 Markdown/Mermaid 围栏和链路文字检查，没有用 Mermaid 渲染器做语法渲染；按明确范围也没有执行 Harbor 运行验收，所以所有动态能力仍标为待实测。
