# 架构与 Codex 认证文档对账行动记录

## 状态与情况说明

- 状态：已完成。
- 来源请求：用户提供上一任务的 Handoff 行动记录，要求在新工作区恢复架构讨论；Handoff 明确把第一项工作定义为同步已经确认、但尚未闭环到各权威文档的 Codex 认证与单机协作事实。
- 当前范围：只对账文档与执行只读探针，不安装 Harbor、不下载数据、不运行真实 Trial、不编写业务代码、不提交或推送 Git。
- 已确认决定：首个真实原型使用 Codex 和 `SWE-Gym/SWE-Gym-Lite` 的 1～3 道真实任务；认证采用评测机所有者本人通过 ChatGPT Pro 登录产生的 `auth.json`；凭据不得共享或进入 Git、PostgreSQL、MinIO、日志、轨迹和制品；Kimi/DeepSeek 只能作为独立 Agent Configuration。
- 已知未知：Codex CLI 固定版本、模型 ID、Harbor 容器内 Token 刷新、脱敏、清理和真实 E2E 均未确认或未实测。
- 新发现：本窗口在 `E:\9.1agent_exam` 中连续尝试默认沙箱命令时再次出现 `setup refresh had errors`；提升权限后只读命令可运行。这否定了“英文路径已经根治故障”，但不能据此判定 Codex CLI 自身不可用。
- 工作区边界：开始时保留 4 个已修改文档和 7 个未跟踪文档；不重置、不覆盖、不清理现有工作。
- 计划偏差：默认沙箱故障导致规范补丁工具只能新增文件、不能读取并更新既有文件；因此先由补丁工具生成可审查的 unified diff，再逐份执行 `git apply --check` 与 `git apply`。一次架构变更记录 hunk 因标记错误被拒绝，随后用唯一行补丁修正；所有临时 `.patch`/`.rej` 已核对路径并清理。

## 实施措施

1. 完整阅读 Handoff 第一层文档，并在遇到路径故障后补读路径迁移行动记录。
2. 用官方 OpenAI 文档核对 Codex 的 ChatGPT 登录、API Key 登录和 `codex exec` 当前接口边界。
3. 在新路径分别运行 `codex --version` 与 `codex exec --help`，记录命令、退出码和实际输出；把宿主命令启动故障与 Codex CLI 结果分开。
4. 按 Handoff 的精确修改表同步总架构、依赖、Harbor 执行、框架接口和 Codex 认证专题文档，不把待实测事项写成已通过。
5. 收尾原 Codex 认证行动记录，并更新路径迁移记录及 Handoff 中已经被本轮证据或完成状态改变的内容。
6. 运行 Markdown 链接、权威术语、旧活动路径、常见密钥模式、`git diff --check` 和 `git status --short` 检查，将实际结果写回本文件。

完成标准：Handoff 列出的认证冲突全部闭环；各文档对“已确认认证政策”“已核验 CLI 接口”“宿主/容器运行待实测”采用一致且可追溯的表述；所有已运行检查的真实结果已记录。

## 受影响文件树

```text
E:\9.1agent_exam\
├── HANDOFF.md
│   # 更新对账状态、下一步入口和本窗口重新出现的沙箱事实
└── docs\
    ├── actions\
    │   ├── 2026-09-04-architecture-document-reconciliation.md
    │   │   # 本轮修改、偏差和验证证据
    │   ├── 2026-09-04-codex-authentication-policy.md
    │   │   # 补齐实际修改树并收尾原认证行动
    │   └── 2026-09-04-workspace-path-migration.md
    │       # 记录默认沙箱故障在英文路径重新出现，修正“已根治”推断
    ├── architecture\
    │   └── ARCHITECTURE.md
    │       # 同步全局决定、秘密边界、规划树、风险、验证和讨论队列
    ├── dependencies\
    │   └── DEPENDENCIES.md
    │       # 区分已确认认证政策与仍待固定的 CLI/模型/容器版本事实
    └── interfaces\
        ├── CODEX_AUTHENTICATION.md
        │   # Codex 认证、凭据所有权和秘密边界的唯一事实源
        ├── FRAMEWORK_INTERFACES.md
        │   # 记录实际 CLI 探针并区分官方接口、宿主运行和 Harbor 容器运行
        └── HARBOR_EXECUTION.md
            # 同步非秘密输入、执行节点秘密解析、制品排除和原型验收边界
```

本轮不改变模块边界或设计模式；只是把现有 Adapter、Execution Backend 和秘密注入边界的文档表述对齐。

## 自验证方式

- 检查 `ARCHITECTURE.md` 的导航、决定表、边界、规划树、风险、验证策略、讨论队列和变更记录是否覆盖 Handoff 指定事实。
- 检查 `DEPENDENCIES.md`、`HARBOR_EXECUTION.md` 与 `FRAMEWORK_INTERFACES.md` 是否把认证选择和运行实测分开。
- 检查 `CODEX_AUTHENTICATION.md` 是否包含反向链接，且未出现真实凭据路径或内容。
- 运行 `codex --version` 与 `codex exec --help`，记录退出码；不执行登录、不读取登录状态、不运行模型请求。
- 解析本轮活动 Markdown 相对链接，预期目标缺失数为 0。
- 搜索过期表述、旧活动路径和常见明文密钥模式，预期活动文档无错误匹配；历史事实允许保留旧路径。
- 运行 `git diff --check`，预期无空白错误。
- 运行 `git status --short`，确认既有改动仍在且只有计划内文档变化。

## 自验证结果

- 通过：OpenAI 官方文档复核确认 Codex 支持 ChatGPT 登录与 API Key 登录，并继续把 `codex exec` 列为稳定的非交互入口；项目选择仍以本地认证事实源为准。
- 通过：提升权限后的只读宿主探针中，`codex --version` 返回 `codex-cli 0.142.0`，`codex exec --help` 正常输出，两个退出码均为 0；没有执行登录状态检查或模型请求。
- 通过：总架构已新增认证导航、C-23～C-25、秘密边界、规划树、独立风险、首次 Trial 安全门槛和更新后的技术讨论项。
- 通过：依赖、Harbor、框架接口和认证专题文档一致区分“认证政策已确认”“宿主 CLI 探针成功”“项目版本/模型/Harbor 容器仍待固定或实测”。
- 通过：42 份第一方 Markdown 共检查 102 个相对链接，缺失数为 0。
- 通过：本轮 9 份受影响文档的尾随空白数为 0，代码围栏全部成对。
- 通过：活动权威文档中的过期认证措辞搜索无匹配；本轮受影响文档的常见明文密钥模式搜索无匹配。
- 通过：旧路径只在 Handoff 的迁移示意、旧路径已不存在和历史保留说明中出现，没有被当作当前工作区。
- 通过：`git diff --check` 退出码为 0；临时补丁与 reject 文件计数为 0。
- 通过：`git status --short` 保留原有 4 个修改文件和 7 个未跟踪文档，并只新增本行动记录；没有业务源码、凭据、运行产物、提交或推送变化。
- 限制：首次不加范围的递归扫描进入了不属于主仓库的 `framework/` 第三方源码，报告 11 个上游相对链接问题和若干上游/历史 Markdown 尾随空白；按第一方文档和本轮受影响文件重跑后均为 0，本轮没有修改第三方源码或无关研究记录。
- 遗留风险：Windows 默认沙箱的 `setup refresh had errors` 已在英文路径重现，当前只能通过提升权限的受控命令工作；根因未诊断，已回写路径迁移行动记录。
