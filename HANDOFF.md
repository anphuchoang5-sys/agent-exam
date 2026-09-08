# AgentExam MVP 实现交接

> 更新：2026-09-08；工作区：`E:\9.1agent_exam`。
>
> 当前状态：第四场授权真实单题已成功完成：Codex 生成真实补丁，固定 SWE-Bench-Fork 独立判卷 resolved=true，补丁一致性、私有证据和精确清理已核对。M0 真实单题核心闭环已通过；完整安全/生命周期验收仍按专题文档收尾，M1 尚未实现、MVP 未完成。用户已授权将本轮源码、测试和文档提交推送；Git 状态见第 5 节，私有原始证据不上传。
>
> 本文是当前恢复入口，不替代专题事实源。历史架构讨论、迁移和逐轮探针保留在对应行动记录，不再全文复制到交接中。

## 1. 目标与当前阶段

既有目标是完成 **Codex-only MVP（最小可用平台）**。交付顺序不变：先完成不带网页的本机技术原型 M0，再进入包含网页、账号、批准、队列和存储的 M1。Aider/Claude Code 后续接入，自研 Agent 属于 P2；具体业务规则见第 3 节权威文档。

当前 **M0 真实单题核心闭环已通过，M1 尚未实现**。已经拿到真实补丁和独立通过报告；下一步核对 M0 剩余验收边界，再按既定顺序进入 M1，不能把本次单题成功等同于 MVP 完成。

| 能力 | 已有事实 | 不能据此推断 |
|---|---|---|
| 固定 SWE-Gym 题目与补丁 | 第四场真实 Codex 生成 1,225-byte 补丁；实际公开任务字节与固定快照一致，补丁三份实际文件哈希相同 | 整个 mypy 项目或所有题目均通过 |
| Harbor 执行与独立判卷 | 第四场真实 Agent → 补丁 → 固定 Fork，patch_applied=true、resolved=true，有原始报告和轨迹 | 已实现网页、账号、批准、队列和存储 |
| Codex 安装与保护 | 第四场实际 UID 65534、模型命令/文件修改、正常清理已核对；第三场 Agent 超时清理证据保留 | Token 刷新、完整崩溃/强杀或全面输出保护已验收 |
| 正式入口与网络 | 限定 DNS 修正已接入；第四场当前账号/模型连接和真实工具执行可用，原有拒绝检查保留 | IPv6、所有长连接/故障或全面网络防护已通过 |
| 产品与远程协作 | 架构已确定；Web、应用账号、批准、队列、项目 PostgreSQL/MinIO 接入尚未实现，Tailscale 未完成双机验证 | 用户电脑已有服务就是本项目已接入 |

实现与逐轮验证的唯一记录是 [M0 行动记录](docs/actions/2026-09-05-m0-codex-harbor-implementation.md)。前两次模型前失败、第三次 DNS 超时均保留；第四场已完成真实回复、工具执行、补丁和独立判卷。取证不显示认证内容，源登录文件仍由所有者本机私有保存；假值测试中的“Token 泄漏”不是用户账号泄漏，本场有限秘密形态 0 命中也不等于全面保护。

## 2. 当前阻塞与授权边界

| 类型 | 当前缺口 | 恢复动作与事实源 |
|---|---|---|
| 已修复的基础设施阻塞 | Docker 外部 DNS 转发已用限定 UDP53 例外接通；未知 resolver 配置在 nft 前拒绝，固定上游未改，双哈希已记录 | 见[执行接口的限定 DNS 适配](docs/interfaces/HARBOR_EXECUTION.md#限定-dns-适配2026-09-08)；不要重复申请该授权或重做已通过的 DNS 修正 |
| 技术验收 | 第四场真实模型路径已可用；具体 FlClash 路由、IPv6、长连接/故障及 DNS/ICMP 外部范围仍有未验收项 | 先读 [Harbor 接口](docs/interfaces/HARBOR_EXECUTION.md#第四次授权运行真实补丁与独立判卷通过2026-09-08)；保留本场通过结果，不扩大为完整网络保护 |
| 技术验收 | 真实模型命令/文件修改和正常清理已核对；完整外层强杀/崩溃、上传中断及真实 Token 刷新未全部验收 | 先读 [认证接口](docs/interfaces/CODEX_AUTHENTICATION.md#第四次真实单题通过2026-09-08) 第 6.2、6.3 节；按必要范围收尾，不把全部 P2 对抗要求加入 MVP |
| 授权边界 | 限定 DNS 修正和第四次真实运行均已获授权且完成；本场成功，没有第五场 | 不重复询问已批准事项，不自动新跑单题或批量评测；如确需另一次真实调用，先说明目的/额度/剩余风险再取得对应许可 |
| 阶段例外的条件 | 用户已允许暂缓本机私有原始输出的全面清洗；代码以 0700 创建每次原型目录，实际真实目录仍须在运行前后核对权限 | 按认证接口第 6.2 节落实；这不是全面保护已经实现，也不是对外发布含秘密输出的许可 |

最新已确认输出政策的唯一事实源是 [认证接口第 6.2 节](docs/interfaces/CODEX_AUTHENTICATION.md)：仅所有者私有保存、不经共享目录/同步/下载接口发布、不送外部 Judge 的原始输出可暂缓全面清洗；对外提供前仍须保护秘密，凭据隔离与容器清理保留。该决定不授权真实模型使用或剩余网络风险豁免。**此边界、内部目录整理和首轮固定配置都无需重复询问。**

假值四场景已经证明原生日志、session、轨迹、错误报告及 patch 可能带入合成秘密。相关测试以“能检测到刻意泄漏”为部分成功条件，故 `4 passed` 不能表述为“防泄漏通过”。审计明确记录 `full_output_protection_passed=false`。详细观察只在认证事实源维护。

## 3. 权威文档必读顺序

### 3.1 开始修改前必须阅读

以下文档必须完整阅读；M0 行动记录较长，按表中指定段落读完，处理对应问题前再读相应历史实验，避免强制装载全部旧窗口记录。

| 顺序 | 文档 | 目的 |
|---|---|---|
| 1 | [AGENTS.md](AGENTS.md)、本文 | 协作规则、最小修改原则、当前目标与授权 |
| 2 | [CONTEXT.md](CONTEXT.md) | 领域词汇，尤其 Job/Run、M0 技术原型与 MVP 的区别 |
| 3 | [总架构](docs/architecture/ARCHITECTURE.md) | 模块边界、依赖方向、关键数据流、规划文件树；规划不等于实现 |
| 4 | [模块契约](docs/architecture/MODULE_CONTRACTS.md) | Execution Backend、Patch Evaluator 等输入输出与错误边界 |
| 5 | [Harbor 执行接口](docs/interfaces/HARBOR_EXECUTION.md) | 固定执行链、补丁契约、M0/M1 验收及第 13.1 节网络事实 |
| 6 | [Codex 认证接口](docs/interfaces/CODEX_AUTHENTICATION.md) | 凭据所有权、当前私有绑定门槛、假值检查与最新受限输出政策 |
| 7 | [框架接口](docs/interfaces/FRAMEWORK_INTERFACES.md) | SWE-Gym、固定 Fork 和 Harbor 的实际入口，避免凭印象调用 |
| 8 | [依赖总表](docs/dependencies/DEPENDENCIES.md) | 固定版本、模型/推理配置、数据和镜像身份；第 2.1 节固定离线安装输入 |
| 9 | [MVP 决策记录](docs/actions/2026-09-05-mvp-priority-product-decisions.md) | 用户已确认的范围与交付顺序；当时环境/未实现状态是历史快照 |
| 10 | [M0 行动记录](docs/actions/2026-09-05-m0-codex-harbor-implementation.md) | 必读“状态与情况说明”，以及“下一窗口交接整理”“进度说明与已确认输出边界同步”“已批准的 Codex 内部目录整理”“完整假凭据 Trial 接线”“完整假凭据 Trial 结果与暂停点”；继续读末尾“正式 Codex 入口接线”“第三次授权的固定真实单题”“已授权的限定 DNS 适配”和“第四次授权的固定真实单题”全部段落 |

完成阅读的标准：能从文档和源码指出当前真实入口何时允许/拒绝、哪些设置已接线或只存在测试里、哪些是已确认政策、哪些是未验证事实；有冲突先查明并同步，不以历史记录覆盖最新专题事实源。

### 3.2 按工作分支追加必读

- 做 Docker、网络或资源探针前，读 [本机 Docker 环境](docs/operations/LOCAL_DOCKER_ENVIRONMENT.md)、[DNS/ICMP 风险评估](docs/research/2026-09-07-dns-icmp-risk-assessment.md) 及 Harbor 第 13.1 节。风险报告是证据和分析，不自动构成政策授权。
- 改动 Harbor 适配或考虑替代方案前，读 [Harbor ADR](docs/adr/0001-use-harbor-as-execution-backend.md)，并核对依赖总表中固定的本地上游源码；不要无依据切换后端或修改第三方仓库。
- M0 验收后进入 M1 前，完整读 [HTTP API](docs/interfaces/HTTP_API.md)、[数据模型](docs/architecture/DATA_MODEL.md)、[远程接入](docs/operations/REMOTE_TEAM_ACCESS.md)，再按既定范围规划实现。
- 只有实际处理 P2/后备执行路径时读 [Runner 协议](docs/interfaces/RUNNER_PROTOCOL.md)；P2 凭据提供方和包装细节不阻塞当前 Codex 原型。
- 只有出现迁移/沙箱问题时读 [路径迁移记录](docs/actions/2026-09-04-workspace-path-migration.md)。旧路径是历史事实，迁移没有根治所有 Windows 沙箱故障。

## 4. 核心代码与测试必读

以下清单必须实际打开阅读，包含本轮整理后的新路径；不是只核对文件存在。目录均为现有实现，不能照规划树另造一套平行代码。

| 顺序 | 必读文件 | 必须理解的关系 |
|---|---|---|
| 1 | [原型入口](apps/backend/prototype_codex_harbor_e2e.py) | 现有 ExecutionBackend → patch 校验 → PatchEvaluator 编排；单题约束、证据文件、真实调用门禁及 CLI 的 check-only 模式 |
| 2 | [执行 port](apps/backend/src/eval_platform/application/ports/execution.py)、[判卷 port](apps/backend/src/eval_platform/application/ports/evaluator.py) | 业务与适配器的边界；其引用的 [task](apps/backend/src/eval_platform/domain/task.py)、[agent](apps/backend/src/eval_platform/domain/agent.py)、[result](apps/backend/src/eval_platform/domain/result.py) 领域对象也须读 |
| 3 | [SWE-Gym Adapter](apps/backend/src/eval_platform/adapters/tasks/swe_gym.py)、[collect 脚本](apps/backend/src/eval_platform/adapters/tasks/collect_patch.sh) | 冻结任务与隐藏字段分离、生产任务渲染、相对固定 base commit 收集补丁 |
| 4 | [Harbor Adapter](apps/backend/src/eval_platform/adapters/execution/harbor/adapter.py)、[配置映射](apps/backend/src/eval_platform/adapters/execution/harbor/config_mapper.py)、[正式引导入口](apps/backend/src/eval_platform/adapters/execution/harbor_entry.py) | ExecutionBackend 的 Adapter 实现；配置/身份、只清理本 Job；固定 Codex 私有绑定才注册，任意配置/缺项失败关闭 |
| 5 | [Codex 兼容类](apps/backend/src/eval_platform/adapters/execution/codex/agent.py)、[权限策略](apps/backend/src/eval_platform/adapters/execution/codex/policy.py)、[安装输入](apps/backend/src/eval_platform/adapters/execution/codex/install.py)、[私有上传](apps/backend/src/eval_platform/adapters/execution/codex/uploads.py) | 固定上游窄继承、默认拒绝凭据绑定；安装/权限输入如何合作；上传代理仅承接两个固定目标，不是新增业务模块 |
| 6 | [patch 校验](apps/backend/src/eval_platform/adapters/execution/harbor/artifacts.py)、[Fork Adapter](apps/backend/src/eval_platform/adapters/evaluation/swe_bench.py) | 完整性校验不等于秘密检测；独立判卷而非信任 Agent 自述 |
| 7 | [完整假值测试](apps/backend/tests/test_codex_trial.py)、[Job 驱动](apps/backend/tests/codex_trial_probe.py)、[合成 CLI 夹具](apps/backend/tests/codex_trial_fixture.py) | 测试怎样注入离线安装、非 root/PATH 和假认证，哪些断言故意要求发现泄漏；模型命令是替身，固定 CLI 只做无模型操作 |
| 8 | [编排契约](apps/backend/tests/contract/test_m0_pipeline.py)、[无模型串联测试](apps/backend/tests/integration/test_m0_pipeline_integration.py) | 现有编排的成功/失败与原型标记；复用已有闭环，避免绕开接口另写脚本 |

开始修改相应实现前还必须读：

- 网络： [network.py](apps/backend/src/eval_platform/adapters/execution/network.py)、[preflight.py](apps/backend/src/eval_platform/adapters/execution/preflight.py)、[网络契约](apps/backend/tests/contract/test_execution_network.py)、[网络实测](apps/backend/tests/integration/test_harbor_network.py) 与其夹具。
- 运行/输出/清理： [process_runner.py](apps/backend/src/eval_platform/adapters/execution/harbor/process_runner.py)、[process_evidence.py](apps/backend/src/eval_platform/adapters/execution/harbor/process_evidence.py)、[redaction.py](apps/backend/src/eval_platform/adapters/execution/redaction.py)、[result_mapper.py](apps/backend/src/eval_platform/adapters/execution/harbor/result_mapper.py)、[result_values.py](apps/backend/src/eval_platform/adapters/execution/harbor/result_values.py)；对应 [秘密测试](apps/backend/tests/test_secret_safety.py)、[强杀清理测试](apps/backend/tests/integration/test_harbor_timeout_cleanup.py)。
- 安装与权限： [test_codex_policy.py](apps/backend/tests/test_codex_policy.py)、[test_codex_guard.py](apps/backend/tests/test_codex_guard.py)、[test_codex_uploads.py](apps/backend/tests/test_codex_uploads.py)、[安装契约](apps/backend/tests/contract/test_codex_installation.py) 及它们实际调用的 probe 文件。
- 判卷内部： [process.py](apps/backend/src/eval_platform/adapters/evaluation/process.py)、[fork_entry.py](apps/backend/src/eval_platform/adapters/evaluation/fork_entry.py)、[判卷映射](apps/backend/src/eval_platform/adapters/evaluation/result_mapper.py)、[五类真实判卷测试](apps/backend/tests/integration/test_swe_bench_integration.py)。

## 5. Git、环境与测试快照

### Git 与必须保留的增量

提交前基线（历史快照）：分支 `main`，HEAD 为 `f4fa625 feat: checkpoint M0 networking and Codex safety groundwork`，相对 `origin/main=42484d8` 为 ahead 11。2026-09-08 用户明确要求提交推送，`git ls-remote --heads origin main` 已确认当时实际远端仍为 `42484d8`。本轮按该授权提交项目增量并普通推送至既有 `origin/main`；最终提交身份及是否同步以现场 `git status --short --branch`、`git log -4 --oneline` 和远端引用为准，不在文档中维护会随提交自身变化的 HEAD。

本轮提交范围包括：

- 完整假凭据 Trial 测试、非 root 上传和固定 Factory 参数兼容修复。
- 用户已批准的 `execution/codex/{agent,policy,install,uploads}.py` 内部整理及所有相关导入；Git 中旧 `codex_agent.py`、`codex_install.py`、`codex_policy.py` 的删除标记是移动/等价拆分，不是实现丢失。
- 固定离线安装、正式任务 UID/PATH、私有运行绑定、Factory 注册、原型 `codex` 类型及对应测试/文档同步。
- 本次已批准的 `network.py` 限定 DNS 适配、原始/生效哈希、未知配置拒绝，以及现有网络契约/探针的回归增量。

保留全部现有文件和缓存；提交只包含项目源码、测试和文档，不包含真实认证、原始运行补丁/日志/判卷输出。用户本次已授权普通提交与 push，未授权强推、reset、checkout 或 clean；本次授权不自动延伸为后续推送。新窗口仍须核对未提交变化，不能用本次快照覆盖现场。

### 环境与证据

- `framework/` 与 `runtime/` 被主仓库忽略，但含固定源码、依赖环境、题目/镜像安装缓存和实验记录。恢复时核对依赖身份并复用；不要无理由重建 Harbor/Fork 环境。Harbor 首次 Windows 源码编译曾耗时约 275 分钟。
- WSL 更新、UAC 确认和内核预检此前已完成。第三次运行的预检、实际容器与收尾查询均成功访问 Docker；历史全局资源计数仍不是当前状态。若恢复时访问 named pipe 被拒绝，先区分权限错误与引擎停止。
- FlClash 和校园网背景见运维文档；真实侧车出站仍待验收。未经对应授权不重启 WSL/Docker、不更改系统代理、防火墙或现有容器。清理只定位本次 Trial，不能全局 prune。
- 证据根为 `runtime/prototype/`。旧 runtime 脚本可能仍使用整理前的导入，重跑使用跟踪测试的新路径；旧证据保留，不批量改写历史记录。

### 最近实际测试

| 检查 | 最近已记录结果 | 解释 |
|---|---|---|
| Ruff check / format --check | 通过；68 文件已格式化 | 本次 DNS 修改后的检查 |
| mypy | 36 源文件通过 | 同一轮静态检查 |
| 默认 pytest | 194 passed、19 skipped，11.51 秒 | DNS 修正后的结果；19 项为未启用的重型检查，不能计为通过 |
| 固定 Harbor 网络回归 | 原始策略 1 failed / 24.56 秒；修正后 1 passed / 42.01 秒 | 同一 DNS 断言红→绿；既有拒绝与精确清理通过，不代表模型通过 |
| 无凭据追加边界 | 9 个守卫场景、受控 UDP 正负例、两个主机根路径 TLS/证书完成 | HTTP 均 403，无模型/账号验证；首次测试断言错误及全部清理证据保留 |
| 第四场真实 Codex → Fork | completed、patch_applied=true、resolved=true；Harbor Trial 167.15 秒 | 真实 1,225-byte 补丁/ATIF/独立原始报告；本场隔离与清理已核对，不代表所有生命周期通过 |
| 生产 Guarded Codex 离线安装 | 1 passed，12.15 秒；真实 Harbor 无模型回归通过 | 固定镜像、network none/deny-all、假认证；无 curl/npm 回退和模型调用，精确资源残留为 0 |
| 新生产 UID/PATH 下完整假认证 success Trial | 1 passed、3 deselected，38.09 秒 | 合成模型/补丁，只证明接线和自然清理；首次夹具顺序失败已保留 |
| 单独启用的完整假值 Docker Trial | 更早一轮 4 passed，156.44 秒 | 成功、报错、超时、patch 带假值；不是全面防泄漏通过 |

实际命令和实验偏差见 M0 行动记录“已批准的 Codex 内部目录整理”“完整假凭据 Trial 结果与暂停点”。完整假值证据位于 `runtime/prototype/codex-full-trial-20260907-06/`；认证接口第 6.2 节说明审计文件与结论。

第三次运行的真实证据位于 `runtime/prototype/m0-real-codex-20260907-03/`：执行 timed_out / AgentTimeoutError、resolved=null、无有效 patch/判卷、usage=null；该场清理证据保留。本次无凭据 DNS 证据位于 `runtime/prototype/m0-dns-{red,green,light,boundary}-20260908-*/`，各次网络探针的四类资源均为空；未重跑真实 Codex 或四场完整假值 Trial。固定 Linux 包仍在 `runtime/prototype/m0-codex-install-20260907-01/codex-0.153.0-linux-x64.tgz`；预检和运行必须复用同一构造及同一个已校验绑定，不能再次凭记忆拼写启动命令。

轻量回归在 `apps/backend` 执行：

最新真实证据为 `runtime/prototype/m0-real-codex-20260908-04/`，同名 `-launch.py` 和 `-audit.py` 在其父目录，分别为本次同一 check/run 构造和限定审计。真实补丁 SHA-256 为 `d5fefec345eb335c9b17d6305037ef47214c56d265f1ca11175c88c90d3ad09d`，独立原始 report 的 SHA-256 为 `cf943803a6e2d818b446afdecb32d41b9e8c706ae36b00b279ae6a5ecf6cc1ec`；具体路径由 execution.json/evaluation.json 引用。该轮没有生产源码变更，未重跑前轮轻量或四场假值测试。

```powershell
.venv/Scripts/ruff.exe check src tests prototype_codex_harbor_e2e.py
.venv/Scripts/ruff.exe format --check src tests prototype_codex_harbor_e2e.py
.venv/Scripts/mypy.exe src prototype_codex_harbor_e2e.py
.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider --tb=short
```

重型测试先读各测试中的显式开关和依赖，使用全新证据目录，不盲目执行整组。完整假值开关为 `AGENTEXAM_RUN_CODEX_TRIAL_PROBE=1`；这不是实际模型运行开关。

## 6. 下一窗口的工作顺序与验收

1. 核对 Git，完成第 3、4 节阅读；用简短中文先报告“已完成/未完成、下一可见里程碑、这次准备改什么、是否涉及账号/额度/机器设置”。用户不应靠阅读全部行动记录才能理解授权。
2. 继续使用现有 M0 行动记录。第四场真实补丁和独立通过报告已核对，安装/DNS/账号/实际工具路径无需无故重做。先核对第 2 节剩余 M0 安全/生命周期验收项；不得把核心闭环已通过改回“项目没有调用真实模型”。
3. 真实运行前按第 2 节处理必要验收和授权。既定私有输出阶段例外直接遵守，不再次扩大为全面输出清洗项目，也不擅自忽略凭据隔离、清理或网络限制。暂未能满足时准确说明缺口，不靠关闭校验放行。
4. 保留第四场可核对的请求、真实执行/轨迹、完整补丁、独立判卷和本场隔离/清理证据。没有必要不追加真实单题；如需要新一场且另获许可，仍区分题目失败与基础设施失败，不自动重试。秘密不展示、不进 Git。
5. 按 [Harbor 接口](docs/interfaces/HARBOR_EXECUTION.md) 第 13.1 节验收 M0；题目是否修好如实报告，不把 `resolved=false` 伪造成通过，也不以合成补丁替代模型输出。M0 验收后才按第 13.2 节进入 M1；M0 完成不等于 MVP 完成。

## 7. 可粘贴到下一窗口的提示词

```text
请在 E:\9.1agent_exam 接续 AgentExam 的既有 MVP 目标，严格依据项目权威文档与现有接口实现。先完成 M0：真实 Codex 经 Harbor 修一道固定 SWE-Gym-Lite 题，收集补丁并交给固定 SWE-Bench-Fork 独立判卷；之后才是 M1 的网页、登录、所有者批准、队列和存储。自研 Agent 属于 P2。

先读 AGENTS.md、HANDOFF.md。按照 HANDOFF 第 3 节完整阅读必读权威文档及指定行动记录段落，第 4 节核心源码和测试必须实际打开阅读，不能只看文件树。特别检查：
- apps/backend/prototype_codex_harbor_e2e.py；
- apps/backend/src/eval_platform/application/ports/{execution,evaluator}.py；
- apps/backend/src/eval_platform/adapters/execution/harbor_entry.py；
- apps/backend/src/eval_platform/adapters/execution/codex/{agent,policy,install,uploads}.py；
- 第 4 节列出的任务、Harbor 映射、判卷及完整假值测试文件。
先核对 git status/log 和未提交差异，保留全部现有改动及 framework/runtime 缓存。

当前 M0 真实单题核心闭环已通过，MVP 未完成。第四场授权运行 m0-real-codex-20260908-04 已由真实 Codex 生成 1,225-byte 补丁、ATIF 和模型用量，固定 Fork 独立判卷 patch_applied=true、resolved=true；补丁三份文件一致，本场正常清理及私有证据已核对。前三次失败证据保留，不自动新跑。最近轻量回归仍为前轮 DNS 修正后的 194 通过、19 跳过；本次真实运行没有重跑，不是全面保护通过。

用户已批准的限定 DNS 修正已接入既有 network.py：只增加已核实的 192.168.65.7/UDP53 例外，未知配置拒绝，原始/生效哈希均记录。第四场已证明当前账号/模型路径与实际工具可用；剩余是完整网络/生命周期验收收尾，不再是“还没拿到真实补丁”。不要重复索取 DNS 或第四场授权，不自动发起第五场。具体证据及剩余范围见 HANDOFF 第 2 节和 M0 行动记录。

用户已同意：仅所有者本机私有、不共享/同步/下载/发送外部 Judge 的原始输出，暂缓全面清洗；对外提供前仍要保护秘密，凭据隔离和容器清理保留。以 CODEX_AUTHENTICATION.md 第 6.2 节为准。用户另行授权的项目私有 ChatGPT 登录及第四场运行已经实际使用，第四场成功结束；授权不自动延伸为再次运行或豁免剩余网络风险。技术诊断、既定修复和真实模型授权应区分，不反复询问已批准事项，秘密不得显示或进入 Git。

用户目前最关心“到底完成了什么、下一步会改变什么、为什么需要批准”。读完后先用简短中文说明当前阶段、一个下一里程碑、具体修改范围，以及是否涉及账号、额度或机器设置，再推进既定范围内的工作。出错时通俗说明为什么出错、修了什么 bug、怎么修与验证，不只贴错误码。技术事实自己查证；需要用户决定时一次只问一个具体问题，不用测试数量代替产品进度。

修改前使用 action-document，继续更新现有 M0 行动记录。遵守最小修改原则和 AGENTS.md 的文件/目录限制；新增顶层模块、接口、表或目录先获确认。保持现有环境，不自行提交、push、重启 WSL/Docker 或改变代理；确有需要时先解释并取得相应授权。

完成标准是可检查的真实补丁、独立判卷报告和与本次真实运行对应的必要安全/清理证据，不是 NOP 或合成测试。题目未修好与基础设施失败应区分，不伪造结果、不自动重试。M0 完成也不等于 MVP 完成。
```
