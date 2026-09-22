# 行动：S9 的 PG 验收缺口在本机补齐（跨机环境差异定位）

> 状态：**已完成**（2026-09-22）。本行动只补证据与修正文档，不改代码。

## 1. 情况说明

**来源**：用户 2026-09-22 要求"读取本分支新的提交内容，卡在 S9 了看看什么情况怎么解决"。

**已核实的事实**（本轮实测，不采信转述）：

| 项 | 结论 | 证据 |
|---|---|---|
| S9 代码是否已实现 | ✅ 已实现并推送（`009e7cf`，作者为本仓另一台开发机） | `delivery/worker/bindings.py`（74 行）、`runtime.py`（180 行）、`domain/agent.py`、`catalog_presets.py`、`tests/jobs/runtime/test_worker_bindings.py`（156 行） |
| S9 卡在哪 | **卡在验收证据，不在代码**：显式 PG 全量在负责人机器上跑不了 | 该机 `127.0.0.1:55432` 是既有 Docker 项目 `agentexam-local` 的发布端口（`ISSUE-05`），夹具 62 项在连接阶段报 `fe_sendauth: no password supplied` |
| 专属测试库在哪 | **在本机（E 的开发机）**：便携实例，回环 trust 认证，无需密码 | 本轮以 `postgresql://agentexam_identity_test@127.0.0.1:55432/agentexam_identity_test` 直连成功（`current_user/current_database` 均为 `agentexam_identity_test`） |
| 本机 PG 全量能否跑通 | ✅ 跑通 | 见第 3 节实测 |
| 文档是否被误导 | ⚠️ **是**：`LOCAL_SETUP.md` 把另一台机器的失败写成了"本机 DSN 不再可用" | 原文"不再可作为当前认证方式使用"与本机实测矛盾，本轮已按机器区分改写 |

**结论**：S9 的"阻塞"是把**负责人机器的环境约束**误当成 S9 的代码问题。PG 验收按计划本来就在本机的专属库上做（[阶段 1 实施方案](../LLY/01-plan/STAGE1_IMPLEMENTATION_PLAN.md)第 4 节：真实 PG 复用阶段 0 的 `agentexam_identity_test`）。本机补齐后 **S9 的两项验收（定向单测 + 全量回归）均已具备**，S10 可开工。

## 2. 实施措施

1. 在本机直连专属测试库，确认认证方式（无需密码）。
2. 跑 S9 定向用例与**显式 PG 全量**，记录实际数字。
3. 复核 S9 代码与用例（含其 4 项区分力注入的结论）。
4. 修正 `02-environment/LOCAL_SETUP.md` 被误导的那条注记，改为**按机器区分**；更新 `04-issues/KNOWN_ISSUES.md` 的 `ISSUE-05` 为已解决（按"在已有专属实例的机器上执行并回传证据"这条路径）。
5. 在 S9 行动文档与进度日志、任务单 Comments 记录验收补齐。

**完成标准**：S9 的 PG 证据有原始数字与命令；文档不再把两台机器的 PG 现场混为一谈。

## 3. 实际运行与原始结果

| 检查 | 命令 | 实际输出 |
|---|---|---|
| 专属库直连 | `.venv/Scripts/python.exe -c` 以测试 DSN 连接 | `OK ('agentexam_identity_test', 'agentexam_identity_test')`（**无密码**） |
| S9 定向用例 | `.venv/Scripts/python.exe -m pytest tests/jobs/runtime -q -p no:cacheprovider --no-cov` | **27 passed**（含 `test_worker_bindings.py`） |
| **显式 PG 全量** | `AGENTEXAM_RUN_IDENTITY_POSTGRES=1 AGENTEXAM_RUN_LEADERBOARD_POSTGRES=1 AGENTEXAM_TEST_DATABASE_URL=<测试 DSN> ... -m pytest -q -p no:cacheprovider` | **2 failed / 676 passed / 51 skipped**（198.51s） |

- 2 项失败是 `tests/contract/test_execution_network.py` 的两条，原因仍是本机缺 `.gitignore` 排除的 `framework/harbor`（ISSUE-04），**与 S9 无关**；在负责人机器上这两项通过。
- 负责人机器上那 62 个 error（连接即失败）在本机**全部进入数据库断言并通过**——同一批用例，差异只在 DSN 指向的实例。
- 与 S9 之前的本机 PG 基线（`664 passed / 52 skipped / 2 failed`）相比：通过数 +12、失败项不变，增量即 S9 的新用例与改动用例。

**S9 代码复核要点**（读码所得，未改）：
- `select_run_binding()` 同时校验**身份对**（`CONTROLLED_IDENTITIES`）与**非秘密凭据引用**（`owner-codex` / `t05-fake-provider`），未知或错配一律 `ValueError`；代理路由返回 `needs_chatgpt_auth=False`、`needs_codex_archive=True`——**正确**：容器仍跑固定 Codex CLI，只是不读 ChatGPT 认证。
- `RunBoundExecutionBackend.execute()` 先为**每个 Run** 选绑定，Job 内出现任一代理路由即 `PROVIDER_RUNTIME_NOT_READY` 并在 Harbor 启动前失败，不静默混入 ChatGPT。
- **一处观察（未改，交负责人判断）**：ChatGPT 归档/认证的校验时机由"worker 启动时"改为"首次执行 ChatGPT Run 前"（测试相应改名为 `test_chatgpt_backend_rejects_unverified_archive_before_harbor`）。这是计划"不再无条件要求 ChatGPT auth"的直接后果，但意味着**配置写错时 worker 仍能启动**，失败推迟到有 Job 被领取时。若希望保留启动期快速失败，可加一句"两个环境变量都存在时仍在启动时校验"；是否要做属于产品行为选择，本行动不擅自改。

## 4. 受影响文件树

| 路径 | 改动与职责 |
|---|---|
| `docs/LLY/02-environment/LOCAL_SETUP.md` | **改**：运行状态行更新为本轮实测（676/51/2）；被误导的那条注记改为**按机器区分**（本机 trust 可用；另一台机器的 55432 是既有 Docker 服务） |
| `docs/LLY/04-issues/KNOWN_ISSUES.md` | **改**：`ISSUE-05` 由"未解决"改为已解决，写明按"在已有专属实例的机器上执行并回传证据"这条路径关闭及其数字 |
| `docs/actions/2026-09-22-task05-s9-run-bindings.md` | **改**（仅状态行与一小节）：S9 的 PG 验收已在本机取得，指向本文件；其余原文保留 |
| `docs/LLY/03-progress/PROGRESS_LOG.md` | **改**：当日条目追加一条 |
| `.scratch/ui-catalog-providers/issues/05-fake-provider-secure-execution-chain.md` | **改**（仅 Comments）：记录 S9 验收补齐与 S10 可开工 |
| `docs/actions/2026-09-22-task05-s9-pg-acceptance-local.md` | 本文件（新增） |

未改动：任何 `.py`、S9 的用例、负责人机器的任何环境或服务。

## 5. 自验证方式与结果

| 检查 | 手段 | 结果 |
|---|---|---|
| 专属库可用 | 直连并读取 `current_user/current_database` | 通过（无需密码） |
| S9 定向用例 | `pytest tests/jobs/runtime --no-cov` | 27 passed |
| 显式 PG 全量 | 两个开关 + 测试 DSN，全量 pytest | 676 passed / 51 skipped / 2 failed（失败项为 ISSUE-04） |
| 文档修正是否准确 | 逐句对照本轮实测与 ISSUE-05 的原始记录 | 通过（本机与负责人机器的现场分开陈述） |

**未执行与限制**：未在负责人机器上跑任何命令；未安装/修改任何数据库服务；未改代码，故未重跑静态检查（S9 提交已自带 `ruff`/`mypy`/全量结论）。**S9 的"含固定 Harbor 的默认全量"由负责人机器提供（`624 passed / 105 skipped`，退出码 0，含临时目录联接的补测）**，本机因缺 `framework/harbor` 仍为 2 failed。

## 6. 下一步

1. **S10 可以开工**（在负责人机器上；拓扑形态以 T2 的已测结论为准）。
2. **PG 相关回归一律在本机跑**：那边 55432 指向既有持久化服务，不能用于会建/删临时库的测试；这条已写进 `ISSUE-05` 与 `LOCAL_SETUP.md`。
3. 若负责人希望恢复"启动期"快速失败，见第 3 节的观察，改动很小但属产品行为选择。
