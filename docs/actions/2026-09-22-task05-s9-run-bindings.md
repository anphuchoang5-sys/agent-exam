# 任务 05 S9：Worker 按冻结 Run 选择绑定

> 状态：S9 选择代码已实现；通过临时复用主工作区固定 Harbor，A 机默认全量为 **624 passed / 105 skipped**。显式 PG 全量仍未测得：本机 `127.0.0.1:55432` 实为既有 `agentexam-local` Docker PostgreSQL 的发布端口，不是计划中的专属测试实例；身份预检被拒后安全停止。故 **S9 整片验收待补**，未进入 S10/S11。T2 在授权的最小 Harbor + 活体网络替身形态已测得 13/13 PASS；双 Harbor Trial 未验证。

## 情况说明

用户要求提交推送 T2 并进入计划下一步；T2 的两个文档提交已推送到 `origin/lly/dev`。本片遵循[阶段计划第 4 节](../LLY/01-plan/STAGE1_T2_S9_S10_S11_PLAN.md)。当前 `delivery/worker/runtime.py` 在领取前无条件读取和校验 ChatGPT 归档/认证，并为所有冻结 Run 共用一个携带 ChatGPT 凭据的 Harbor Adapter；这与受控假提供方身份不符。冻结的 `AgentConfiguration` 已在 `ExecutionJobRequest.runs` 可见；现有 `ExecutionBackend` port 不必新增字段。生产目录只登记 `owner-codex`，内部假身份只在 `internal_test` 预设，身份对以 `domain/agent.py::CONTROLLED_IDENTITIES` 为权威。

确认的阶段边界：固定 `harbor_entry.py` 仍只接受 ChatGPT 单一 Agent 配置、拒绝 `extra_docker_compose`；因此 S9 可以选择并拒绝不完整的代理绑定，但不能谎称受控假身份已能生产执行。真正代理运行与每 Trial 网络/令牌接线留给 S10。一个 Job 可含多个 Agent 配置，因此必须逐 Run 检查；若任何 Run 的绑定未就绪，整个 Job 在 Harbor 启动前失败关闭，不静默混入 ChatGPT。

环境事实：`lly/dev` 在开工前为干净 `6be6d93`，`origin/main` 是其祖先（`HEAD...origin/main = 10\t0`）。系统 Python 3.13 有 pytest/ruff，但当前 worktree 没有后端 `.venv`；初次 `python -m pytest tests/jobs/runtime -q -p no:cacheprovider --no-cov` 在 conftest 导入 `psycopg` 时因 `ModuleNotFoundError` 退出，**尚未测到 S9 代码**。随后复用主仓库现有 `apps/backend/.venv/Scripts/python.exe` 成功运行测试，不安装包、不改全局 Python。

## 实施措施

1. 在既有 `domain.agent` 身份清单旁固定非秘密 profile ID，使目录预设与 Worker 选择使用同一常量；不读也不输出任何凭据正文。
2. 新增 `delivery/worker/bindings.py` 深模块：逐 Run 验身份对与 profile 对应关系，返回 ChatGPT 或受控代理绑定描述；未知、缺失、错配一律 ValueError。Job 内有未就绪代理绑定时明确失败关闭，不调用 Harbor，不回退到 ChatGPT。
3. `runtime.py` 将归档/认证校验延到已确认全为 ChatGPT 的该次执行前；ChatGPT 的固定主机集合、归档校验、认证校验与原 Harbor Adapter 参数保持不变。受控假身份不读取 ChatGPT auth/归档，S10 前不执行任何代理网络。
4. 用运行时用例覆盖 ChatGPT 保持、受控假身份不读认证且失败关闭、未知身份、profile 错配与混合 Job；逐条做区分力检查。同步执行模块架构、进度与任务单。仅本片文件提交并安全推送 `origin/lly/dev`；PR 若无写入工具如实报告。验证缺口未关闭前不进入 S10。

## 需要修改的文件树

| 路径 | 职责与关系 |
|---|---|
| `apps/backend/src/eval_platform/domain/agent.py` | 身份对与非秘密 profile ID 的唯一常量位置 |
| `apps/backend/src/eval_platform/delivery/catalog_presets.py` | 预设引用同一 profile ID，防止选择器与登记漂移 |
| `apps/backend/src/eval_platform/delivery/worker/bindings.py` | Run 绑定选择/失败关闭 Adapter；从冻结配置到生产后端的窄转换 |
| `apps/backend/src/eval_platform/delivery/worker/runtime.py` | Composition Root；按选择结果延迟组装既有 Harbor Adapter |
| `apps/backend/tests/jobs/runtime/test_worker_bindings.py` | S9 选择与失败关闭用例、负控 |
| `apps/backend/tests/jobs/runtime/test_worker_runtime.py` | 既有 ChatGPT 行为与新装配路径的回归 |
| `docs/architecture/modules/execution-and-evaluation/ARCHITECTURE.md` | 当前 Worker 文件树与 S9 阶段边界 |
| `docs/architecture/modules/README.md` | 模块索引的现实状态 |
| `docs/architecture/ARCHITECTURE.md` | 总文件树中的 Worker 选择器与测试职责 |
| `docs/LLY/02-environment/LOCAL_SETUP.md` | 将历史“PG 无密码”与本轮当前现场区分，避免误导后续重跑 |
| `docs/LLY/04-issues/KNOWN_ISSUES.md` | ISSUE-04 worktree 路径补充与新 ISSUE-05 PG 认证漂移、解决方案 |
| `docs/LLY/03-progress/PROGRESS_LOG.md` | 当前完成/未验证状态 |
| `.scratch/ui-catalog-providers/issues/05-fake-provider-secure-execution-chain.md` | 任务 05 Comments 与提交引用 |
| 本文件 | 实施与自验证实录 |

模式关系：`bindings.py` 是 Worker Composition Root 内部的策略选择器，不新增 `ExecutionBackend` interface；它逐 Run 检查冻结身份，`runtime.py` 仅在安全结果下构造既有 Harbor Adapter。代理绑定的执行留给 S10，不改 Harbor Adapter 的固定 ChatGPT 行为。

## 自验证方式

- `python -m pytest tests/jobs/runtime -q -p no:cacheprovider --no-cov`：预期 S9 用例及旧用例全部通过。测试环境若缺依赖，先核对可复用本机环境，不擅自装包/改全局 Python。
- `python -m ruff check ...`、`python -m ruff format --check ...`、`python -m mypy ...`：至少对变更文件做静态检查；不可用则列限制。
- 负控：分别让受控假身份错误落回 ChatGPT、ChatGPT 失去认证校验、未知身份/错配被接受，期望对应测试失败；还原后通过。不改生产网络、不读真实 Key。
- 默认全量与可用的 PG 全量按计划运行；外部服务不可用则写明 collection/skip/failure 的实际层级。检查单文件≤200行、每层≤8文件、文档与代码齐平、Git diff 仅本片。

## 自验证情况

### 实际实现与边界

`domain/agent.py` 增加 `owner-codex`/`t05-fake-provider` 非秘密 profile ID 常量，登记预设与 Worker 选择器共用。`worker/bindings.py` 逐一检查冻结 Run 的 `(model_provider, authentication_type, credential_configuration_id)`，未知身份/错配拒绝；ChatGPT 保留 `auth.openai.com`、`chatgpt.com` 固定主机和归档、认证校验；受控假身份标记为代理路由、不需要 ChatGPT 认证，但 S10 前任何含此身份的 Job **在 Harbor 启动前**报 `PROVIDER_RUNTIME_NOT_READY`。多 Agent Job 全部 Run 先检查，任一代理路由均不允许其余 ChatGPT Run 借道执行。`runtime.py` 不再领取前无条件验证 ChatGPT 文件，而是在全 ChatGPT Job 的本次 `execute` 前按原逻辑验证并构造同参数 Harbor Adapter；这是计划要求的**验证时机变化**，不是完全逐行相同的启动行为。

源文件指标：`runtime.py` 180 行、`bindings.py` 74 行；测试文件 `test_worker_runtime.py` 170 行、`test_worker_bindings.py` 156 行；`delivery/worker/` 5 个 Python 文件、`tests/jobs/runtime/` 3 个，均低于项目默认阈值。无新 `ExecutionBackend` Interface、数据库表或顶层模块。

### 运行命令与实际输出

使用现有 `E:/9.1agent_exam/apps/backend/.venv/Scripts/python.exe`。当前 worktree 无自己的后端 `.venv`，首次系统 Python `pytest` 在 conftest 因缺 `psycopg` 无法收集；改用已有依赖环境。pytest 默认临时目录 `C:/Windows/Temp/pytest-of-YINGYI` 与普通进程新建 `.tmp` 路径均出现 `PermissionError`；经授权用本轮专属 `--basetemp` 路径运行，未改测试内容。

| 检查 | 最终实际输出 | 判定 |
|---|---|---|
| `pytest tests/jobs/runtime -q -p no:cacheprovider --no-cov --basetemp .../pytest-s9-20260922-07` | `27 passed in 0.06s` | S9 与旧 Worker 用例通过 |
| `ruff check --no-cache src tests` | `All checks passed!` | 通过 |
| `ruff format --check --no-cache src tests` | `349 files already formatted` | 通过 |
| `mypy --no-incremental src/eval_platform` | `Success: no issues found in 187 source files` | 通过 |
| 默认全量 `pytest -q -p no:cacheprovider --no-cov --basetemp .../pytest-s9-20260922-08 --tb=line` | `2 failed, 620 passed, 107 skipped in 77.72s` | **未全绿**；失败为固定 Harbor 路径不存在，见下 |
| 显式 PG 全量（专属测试库、scope `.../pytest-s9-20260922-06`） | `2 failed, 620 passed, 45 skipped, 62 errors in 85.29s` | **未通过**；62 项均连接时 `fe_sendauth: no password supplied`，未创建临时库 |

默认全量的两项失败是 `test_bootstrap_imports_fixed_harbor_not_the_adjacent_adapter_package` 与 `test_sidecar_exports_traceable_dns_adaptation_and_never_overwrites`。定向复现原文分别为 `FileNotFoundError: [WinError 2]`（测试在 `runtime/lly-dev-verify/framework/harbor/.venv/Scripts/python.exe` 启动解释器）和 `git -C E:\9.1agent_exam\runtime\lly-dev-verify\framework\harbor rev-parse HEAD` exit 128；本 worktree 无 `framework/harbor`，主仓库 `E:/9.1agent_exam/framework/harbor` 有，但计划禁止新建目录/切分支，未复制或改测试。这两项与之前 ISSUE-04 同形状，**不把本轮全量写为通过**。PG 测试在夹具连接专属库之前认证失败，未执行数据库断言；项目环境文档称无密码回环认证，当前环境事实与文档不一致，不读取密码或修改 PostgreSQL/共享配置。

### 断言区分力

通过 `apply_patch` 暂时注入错误实现、运行单条目标用例、立即还原，再复跑 `test_worker_bindings.py` 得 `9 passed`：

| 故意错误 | 对应断言的实际结果 |
|---|---|
| 把代理路由错误返回为 ChatGPT | `test_internal_test_identity_selects_proxy_without_chatgpt_auth`：`assert 'chatgpt' == 'provider_proxy'`，1 failed |
| 把 ChatGPT 的 `needs_chatgpt_auth` 改为 False | `test_chatgpt_identity_keeps_fixed_hosts_and_auth_requirement`：`assert False is True`，1 failed |
| 取消未知身份拦截并加入错误的 ChatGPT 回落 | `test_unknown_identity_fails_closed[unknown-chatgpt_auth_json]`：`DID NOT RAISE ValueError`，1 failed |
| 取消 ChatGPT profile 错配拒绝 | `test_credential_reference_must_match_identity[False]`：`DID NOT RAISE ValueError`，1 failed |

两次**无效负控尝试**也如实记录：最初只改最后的未知身份分支，先前的 guard 仍挡住输入，用例 2 passed，不能证明区分力；另一次临时补丁损坏缩进，在收集阶段触发 `IndentationError`，也不能算有效负控。两者均已还原；上述四项有效注入重新执行并恢复，最终 Ruff、Mypy、定向 pytest 结果是还原后的源码。

### 问题、解决方案与未验证项

1. **固定 Harbor 契约全量检查缺口（已补测）**：初跑时当前 worktree 未有 `framework/harbor`，不可把主仓库框架的历史通过外推到本 worktree。用户随后允许临时目录联接，已实际补跑两项契约测试及默认全量，结果见下节；补测后精确移除联接，当前 worktree 再次没有该 Git 忽略路径。不修改断言或复制/重建固定 Harbor。
2. **专属 PG 环境漂移**：端口 `127.0.0.1:55432` 可连，但当前要求密码，与[本机环境文档](../LLY/02-environment/LOCAL_SETUP.md)的“回环信任、无密码”不一致。解决方案由 owner 确认专属测试库认证方式并提供安全测试进程配置，或更新环境文档并在授权后重跑；本轮未读登录文件、未猜密码、未改服务器。
3. **S10 前的预期限制**：代理绑定只完成选择，不启动代理、不导出令牌、不生成双网络。若把受控假身份提交为正式 Job，会显式失败关闭；这是安全停止点，非 T2 回归。S10 在 S9 必要回归补齐前不启动。真实 Key、真实供应商、Codex CLI、Harbor 正式 Job、Fork、双 Harbor Trial 均未在本片运行。

### 2026-09-22 补测：临时复用主工作区固定 Harbor（执行前记录）

用户已明确同意在现有 `runtime/lly-dev-verify` worktree 临时建立目录联接，复用主工作区 `E:/9.1agent_exam/framework/harbor`，补跑缺失路径引起的两项契约检查，随后精确移除联接。不复制、不重建、不修改固定 Harbor，也不改变测试断言；这项临时目录创建是此前“不新建目录”约束的本次明确例外。主工作区框架受控文件干净、提交为固定 `6af8d6e31eced13b93849cdf80feeadf24603d15`，虚拟环境解释器存在；本 worktree `framework` 当前不存在。

实施与临时文件树：只在 `runtime/lly-dev-verify/framework/` 建目录作为本次入口，在其下建立 `harbor` 目录联接（目标为上述主工作区固定 Harbor）；完成后先核实联接类型与目标，再只移除 `harbor` 联接和本次创建且为空的 `framework` 目录。受控源码和其他 worktree 不在删除范围。验证：先运行 `tests/contract/test_execution_network.py` 中上述两项，再运行默认全量；预期两项通过，默认全量不再有 Harbor 路径失败。显式 PG 全量仍受专属库认证问题阻挡，不使用凭据、不修改服务。

**实际输出与偏差**：普通沙箱在 `New-Item framework` 及 `Remove-Item framework/harbor` 时均返回 `Access is denied`；经受控权限执行相同精确路径操作成功。建立后 `Get-Item` 显示 `LinkType: Junction`、`Target: E:/9.1agent_exam/framework/harbor`。首次定向 pytest 因专属临时目录无法创建而得 `1 passed, 1 error`，错误为 `PermissionError: [WinError 5]`，第二项未测到断言；在受控权限下改用新专属临时目录重跑，同两条命令得到 `2 passed in 0.63s`。默认全量（`python -m pytest -q -p no:cacheprovider --no-cov --basetemp .../.tmp/pytest-s9-harbor-full-01 --tb=line`）实际为 `624 passed, 105 skipped in 78.52s`，退出码 0；跳过的 PostgreSQL、Docker/Fork 等显式集成用例不计通过。解释器沿用主工作区后端现有 `.venv`；测试未改断言，也未运行真实模型或供应商请求。补测后先核实仅有这一条目录联接且目标准确，`Remove-Item` 不带 `-Recurse` 精确移除联接和空父目录；复核 `LinkExists=False`、`ParentExists=False`、`SourceExists=True`、`SourceRevision=6af8d6e31eced13b93849cdf80feeadf24603d15`、主框架受控文件 `git status --short` 为空。

**剩余限制**：显式 PostgreSQL 全量尚未重跑，沿用上文 `fe_sendauth: no password supplied` 的本轮失败实测；未取得专属测试库安全认证配置前不能写为通过。S10/S11 仍未开工。

### 2026-09-22 专属 PostgreSQL 隐藏输入补测（执行前记录）

用户同意尝试在本机可见的交互窗口隐藏输入专属测试角色 `agentexam_identity_test` 的 PostgreSQL 密码；不是 owner 登录密码，也不接收真实 Key。范围仅为先验证 `127.0.0.1:55432/agentexam_identity_test` 的角色/库身份，再按计划运行开启 `AGENTEXAM_RUN_IDENTITY_POSTGRES=1` 的全量后端 pytest。密码不写聊天、命令参数、脚本、仓库或报告；只在窗口进程内存与其测试子进程的短时 `PGPASSWORD` 环境中使用，结束时移除。普通测试输出先在内存替换密码字面量后才写入 `.tmp`；若连接失败不跑全量。此方法仍有进程内存/环境暴露风险，因此只可输入专属低权限测试凭据，不使用任何生产或可复用高权限密码。

实施措施与临时文件树：在现有 `.tmp/` 新建不含秘密的 `s9-pg-interactive.ps1`（隐藏输入、专属库预检、全量测试、脱敏结果与 `finally` 清理），生成同目录的 `.status`/`.log`（仅非秘密状态和脱敏输出）；为使全量同时覆盖两项 Harbor 契约，窗口在通过数据库预检后只在此 worktree 临时建立 `framework/harbor` 目录联接，目标为主工作区固定、干净的 `6af8d6e3…` Harbor，结束后先核身份再无递归精确移除联接与空父目录。不修改测试断言、数据库/共享服务配置或其他 worktree；不运行真实模型/供应商请求。涉及的唯一跟踪文件是本行动记录；`.tmp` 与临时联接均被 Git 忽略。

自验证方式：静态解析脚本、检查不含凭据字面量；窗口身份预检必须返回测试用户名/库名；PG 全量需观察 pytest 退出码与统计（不能把跳过算通过）；窗口退出后检查联接及空父目录不存在、主 Harbor 固定提交与受控文件不变、短时环境变量清除；更新 ISSUE-05、进度日志和任务单为实测状态。**自验证结果：待执行。**

**本次尝试进展**：`.tmp/s9-pg-interactive.ps1` 静态解析 `parse_errors=0`，107 行，未含密码字面量。经用户同意用 `Start-Process -WindowStyle Normal` 启动 PID 47740，但系统回报 `MainWindowHandle=0`，状态一直为 `phase=waiting-for-input`，说明该工具执行会话没有把窗口呈现到用户桌面；未收到输入、未连接数据库、未建立临时 Harbor 联接、未运行 pytest。核对进程路径、PID、状态与无联接后，只停止这一条空等辅助进程；普通沙箱拒绝停止，受控权限精确停止成功。现改为请用户在自己可见的 PowerShell 中运行同一个不含密码的脚本。**数据库预检与 PG 全量实际结果仍待用户本机隐藏输入，不能记为通过。**

**隐藏输入后启动器诊断及修正计划（执行前）**：用户已在可见 PowerShell 输入专属测试库密码，但 `.status` 实际为 `outcome=launcher-error / auth_exit=not-run / test_exit=not-run / cleanup=ok`，`.log` 仅有 `File "<string>", line 1`；没有创建 Harbor 联接或 pytest 临时目录。无密码复现证明 Windows PowerShell 5.1 会剥掉 `python -c 'print("ok")'` 内的双引号，导致 Python 看到 `print(ok)`；`$ErrorActionPreference='Stop'` 又在首条原生 stderr 处提前抛出，使诊断截断。拟在现有 `.tmp/` 新增不含密码的 `s9-pg-preflight.py`，把数据库身份预检从命令内联代码移到文件；`s9-pg-interactive.ps1` 改为调用该文件，并在原生程序调用期间完整捕获、脱敏 stderr 后按退出码判定。先运行 Python 语法检查与不连接数据库的自检，再请用户重新输入专属测试密码。首次输入已由原脚本 `finally` 从进程环境移除；不尝试取回、输出或保存密码。**修正后自验证结果：待执行。**

**修正后无密码自验证**：新增 `.tmp/s9-pg-preflight.py`（仅固定本机专属测试库 DSN、角色/库身份检查和 `--self-check`，不含密码），交互脚本改为执行文件而非 `python -c`；原生 stderr 捕获时临时使用 `ErrorActionPreference=Continue` 并恢复原设置。PowerShell 语法解析 `powershell_parse_errors=0`；Python 不连接数据库的 `--self-check` 返回 `preflight-launch-ok`、exit 0；在 Windows PowerShell 5.1 注入非秘密的 `--bad-argument` 故障，完整收到 `invalid preflight arguments` 且 `native_exit=2`，证明不再被首行 stderr 截断。**数据库身份预检与 PG 全量仍未重跑，需用户在可见窗口重新隐藏输入一次；原密码不留存。**

**重新隐藏输入后的实际结果（较新事实）**：`.tmp/s9-pg-interactive.status` 为 `outcome=authentication-failed / auth_exit=1 / test_exit=not-run / cleanup=ok`；脱敏日志的关键原文为 `psycopg.OperationalError: ... 127.0.0.1, port 55432 ... FATAL: password authentication failed for user "agentexam_identity_test"`。预检在 PostgreSQL 认证阶段失败，未进入身份 SQL、未建立 Harbor 联接或 pytest 临时目录，显式 PG 全量**未运行**。脚本的短时环境变量由 `finally` 移除；没有读取、保存或回显密码。`framework` 路径不存在，源 Harbor 保持固定提交且受控文件干净。

**只读定位与停止条件**：`netstat` 显示 `127.0.0.1:55432` 的监听者为 `com.docker.backend.exe`（PID 30416）；`docker ps --filter publish=55432` 显示既有 `agentexam-local-postgres-1`（`postgres`，`127.0.0.1:55432->5432/tcp`），只读标签为 Compose 项目 `agentexam-local`、服务 `postgres`。本机没有运行的 `postgres.exe`，也没有文档所指的 `D:/pgsql/bin/postgres.exe` 或 `D:/pgsql/data`。因此原先“专属测试库仅认证方式变化”的假设不足；当前 DSN 实际指向既有持久化服务，不能用它执行会 `CREATE DATABASE`/`DROP DATABASE` 的专属测试。密码被拒不能证明用户输错，也无需再对该服务重试。**解决方案**：先由负责人另行提供隔离的专属测试 PostgreSQL 实例（非现有 `agentexam-local`，单独端口、`agentexam_identity_test` 角色/库且具所需 `CREATEDB` 权限），或由已有专属环境的机器执行 PG 全量并回传证据；实例创建/改端口/改现有服务都不在本轮授权内。S9 保持未验收，S10/S11 不启动。
