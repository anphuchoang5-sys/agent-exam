# M0 Codex → Harbor → SWE-Bench-Fork 实现行动记录

## 状态与情况说明

- 状态：进行中；M0 未完成。额度中断后按用户要求恢复；固定 Fork 五类补丁已实测，当前接入 M0 脚本编排，真实 Codex 及其网络/凭据安全门槛仍未完成。沿用同一行动记录，保留未提交实现，不自行 push。
- 来源请求：用户要求先核对 Git 为最新状态，再以长期目标开始实现 MVP，并严格遵守架构、模块契约和接口等权威文档。
- 当前范围：只实施 M0 本机技术原型。使用固定 SWE-Gym-Lite 单题、固定 Harbor、真实 Codex 和固定 SWE-Bench-Fork，形成可检查的 patch 与判卷证据；M0 通过后另建 M1 行动记录。
- Git 基线：2026-09-05 已执行 `git fetch origin --prune`；本地 `main` 与 `origin/main` 均为 `42484d8472b3a258c49ca22d85a7b8a8b5166de2`，领先/落后为 `0/0`，开始时工作区干净。
- 恢复基线：2026-09-06 再次执行 `git fetch origin --prune` 成功；本地 `main` 为交接提交 `0caedda`，`origin/main` 仍为 `42484d8`，`HEAD...origin/main` 为 `1/0`，恢复时工作区干净。本轮不自行 push。
- 第二次恢复基线：交接提交 `37f04d2` 后再次执行 `git fetch origin --prune` 成功；工作区干净，本地 `main` 相对 `origin/main` 为 `2/0`。本轮继续不自行 push。
- 第三次恢复基线：交接提交 `8e53f47` 后执行 `git fetch origin --prune` 成功；工作区干净，本地 `main` 相对仍位于 `42484d8` 的 `origin/main` 为 `3/0`，没有远端新提交需要合并。本轮继续不自行 push。
- 第四次恢复基线：交接提交 `40c6f6c` 后执行 `git fetch origin --prune` 成功；工作区干净，本地 `main` 相对仍位于 `42484d8` 的 `origin/main` 为 `4/0`，没有远端新提交需要合并。本轮继续不自行 push。
- 第五次恢复基线：交接提交 `e629eda` 后执行 `git fetch origin --prune` 成功；工作区干净，本地 `main` 相对仍位于 `42484d8` 的 `origin/main` 为 `5/0`，没有远端新提交需要合并。本轮继续不自行 push。
- 第六次恢复基线：交接提交 `a9306b7` 后执行 `git fetch origin --prune` 成功；工作区干净，本地 `main` 相对仍位于 `42484d8` 的 `origin/main` 为 `6/0`，没有远端新提交需要合并。三个 framework 仓库的 origin、固定 HEAD 与干净工作树再次吻合依赖事实源；Harbor `0.22.0`、Python `3.13.2`、Codex CLI `0.153.0`。Docker Client/Server 均为 `27.5.1`，可见内存 `10,429,505,536` bytes，18 个容器中 13 个运行、21 个镜像；E 盘可用 `19,594,166,272` bytes。本轮继续不自行 push。
- 第七次恢复基线：交接提交 `aca01e7` 后执行 `git fetch origin --prune` 成功；工作区干净，本地 `main` 相对仍位于 `42484d8` 的 `origin/main` 为 `7/0`，没有远端新提交需要合并。本轮继续不自行 push。
- 已读取边界：`AGENTS.md`、`HANDOFF.md`、`CONTEXT.md`、最新 MVP 决策行动记录、总架构、模块契约、依赖事实源、Harbor/框架/Codex 认证接口、本机 Docker 事实和 Harbor ADR。
- 已确认依赖身份：SWE-Gym `b681068ca20628c6987b7416cc4cf03f06b77ba5`、SWE-Bench-Fork `242429c188fcfd06aad13fce9a54d450470bf0ac`、Harbor `6af8d6e31eced13b93849cdf80feeadf24603d15`。
- 当前动态事实：本机 Python 为 `3.13.2`；Codex CLI 为 `0.153.0`，不同于旧文档探针的 `0.142.0`，尚未选作项目固定版本；Docker Desktop `4.38.0` / Engine `27.5.1` 当前可响应；E 盘开始时可用 `22,829,572,096` bytes；三个框架源码现均已恢复到权威文档固定提交并保持干净。
- 恢复动态事实：2026-09-06 提升权限只读探针确认 Docker Client/Server 均为 `27.5.1`，Docker 可见内存为 `10,429,505,536` bytes；E 盘可用空间降至 `19,709,878,272` bytes。默认沙箱访问 Docker named pipe 被拒绝，仅是权限边界，不是 Engine 停止。
- 数据事实：`SWE-Gym/SWE-Gym-Lite` 当前仅有 `train` split，共 230 条；本轮固定读取不可变 revision `61231f2c90b18985b42a1419738a240085a15107`。Parquet 已保存到忽略的运行时缓存，大小 `931,193` bytes，SHA-256 为 `f3a7cd934e8cc523b6053298d0abb2c82fd7db2b83f9f2ccba5944545aaa4eb1`。
- Harbor 源码事实：固定提交要求 Python `>=3.12`，仓库 `.python-version` 为 `3.13`，项目版本为 `0.22.0`；固定提交已经内置 `adapters/swegym`、Codex Adapter 与 `[[verifier.collect]]`。单步 Trial 的顺序是 Agent、日志同步、collect hook、artifact 收集、可选 verifier；因此全局关闭 verifier 时 collect/artifact 仍执行。
- 复用边界：内置 SWE-Gym Adapter 会用未指定 `revision` 的 `load_dataset()` 读取远端最新数据，并把含 `gold_patch`、`test_patch`、`FAIL_TO_PASS`、`PASS_TO_PASS` 的原始 datum 写入任务 `tests/config.json`。M0 将复用其镜像命名和 Harbor 任务约定，但保留项目既有规划中的薄 `adapters/tasks/swe_gym.py`，直接读取已校验的固定 Parquet，只生成 Agent 必需的公开任务文件；隐藏字段只交给独立 Evaluator。
- OpenAI 官方事实复核：Codex 当前仍支持 ChatGPT 登录和 API Key 登录；`codex exec` 是非交互入口，支持 `--ephemeral`、`--json` 和显式 sandbox；文件型缓存含访问令牌，必须按密码处理。项目仍采用已经确认的评测机所有者 ChatGPT 登录政策，不改为 API Key。
- 已确认的超时事实：真实 Harbor 外层超时会绕过上游正常清理；修复前探针留下 1 个 Compose 容器、1 个网络和 1 个本地镜像。生产 Adapter 现按本 Job 落盘 Trial 身份推导精确 project label，清理并复核容器、网络、卷和本地镜像；日志采集使用总期限，Windows 对仍阻塞的同步读执行定向取消，无法完整收束时返回 `HARBOR_LOG_CAPTURE_INCOMPLETE`，不再无限等待。
- 已知未知：Codex 模型 ID、所需端点、Token 刷新、日志脱敏和异常路径清理；固定 Fork 已通过的单题以外的适配范围；真实单题的资源峰值与清理结果。
- 安全红线：不读取、显示、复制或提交 `auth.json` 内容、Token、Cookie 或 API Key；不把秘密路径写入业务输入或证据；不把 Agent 可见输入与 gold patch、`test_patch`、`FAIL_TO_PASS`、`PASS_TO_PASS` 混合；不把 Mock、Harbor reward 或 Agent 自述写成真实判卷结果。
- 明确排除：本行动不实现 Next.js、FastAPI HTTP、PostgreSQL、MinIO、应用登录、Owner Approval、Judge、排行榜、Tailscale 或 P2 自研 Agent；不提前创建 M1 空壳。

## 实施措施

1. 读取真实数据源元信息，固定 SWE-Gym-Lite 的不可变 revision、split、一个首题和内容校验值；只下载单题所需内容，不扩到完整题库。
2. 按依赖事实源恢复 `framework/harbor` 固定提交并核验 remote、HEAD、工作树、Python 要求和真实 Codex/Task/Artifact extension point；不依赖上游 `main` 或记忆写接口。
3. 建立最小、隔离且可复现的 Python 环境，先验证 Harbor 与固定 Fork 的导入/CLI；项目包清单只锁实际使用的依赖，不把本机偶然版本当团队基线。
4. 在已经确认的 `apps/backend` 规划边界中实现 M0：薄脚本入口负责参数和阶段编排，领域/port 只表达项目对象，Harbor Adapter 隐藏上游类型，SWE-Gym Adapter 隔离隐藏字段，Patch Evaluator Adapter 隔离固定 Fork CLI。
5. 实现受控本机证据目录与 manifest：每次原型运行使用唯一 ID；保存脱敏配置、原始结果、轨迹、stdout/stderr、完整文本 patch、大小和 SHA-256；明确标记 `prototype`，不得进入正式排行。
6. 在不调用真实模型的测试中先覆盖隐藏字段隔离、Trial 身份映射、空/普通/新建/删除 patch、256 KiB 警告、1 MiB 与二进制拒绝、哈希不一致、日志显式截断、错误映射和证据不可覆盖。
7. 用固定 Fork 对同一首题执行 gold、空和错误 patch 的最小验证，确认 `resolved` 与基础设施失败的区别；再运行 Harbor 无真实秘密的安装/任务/制品探针。
8. 只检查登录可用性和凭据文件元数据，不读取内容；真实 Codex Trial 前确认代理、最小挂载、临时凭据注入和清理路径，随后只运行一个 Trial。
9. 检查 Trial 前后容器、可写层和所有证据；若 patch 出口、资源治理、轨迹或秘密清理不满足 ADR 门槛，记录失败并停止扩建 M1，先诊断是否触发 Process Adapter 退出条件。
10. 每获得一个动态事实就同步其唯一事实源；收尾时记录全部实际命令、结果、失败、跳过项和遗留风险，并核对代码、规划树、依赖文档、Handoff 与本行动记录一致。
11. 先增加两个受控失败探针：单元测试模拟后代持续持有日志管道，要求执行器在固定上限内返回并显式告警；真实 Docker 集成测试使用上游 `nop` 与测试专用阻塞 collect hook，要求外层超时后该 Trial 的精确 Compose 容器、网络、卷和本地镜像均无残留。测试不得调用模型或注册生产 sleep Agent，`finally` 只能清理按该 Trial project label 核实的资源。
12. 只有探针证明真实缺陷后，才在现有 `process_evidence.py`、`process_runner.py` 和 Harbor Adapter seam 内最小修复；不新增生产顶层模块、Interface 或第二套执行路径。修复后复跑失败探针、全部快速检查和真实 NOP，记录清理前后 Docker 对象与证据目录。
13. 在已规划的 `adapters/evaluation` 内实现固定 Fork 适配：先用现有 Ubuntu WSL2 + Docker 接口建立隔离 Linux Python 环境，生成带哈希的依赖锁；只使用固定 Fork 源码，核实实际 CLI 与镜像预检查。复用 Task Catalog 冻结的原始记录及 `PatchEvaluator` port，不把隐藏字段传回 Agent。补丁结果映射必须区分空补丁、正常 unresolved、报告缺失和基础设施失败。
14. 新增 Evaluator 契约与真实 gold/空/错误补丁测试；运行前定义独立证据目录和精确容器身份。记录实例报告、汇总、测试日志、Fork/依赖/任务/镜像身份与清理结果。原生 Fork 的环境镜像预检查、硬编码资源限制和联网行为先据源码/实测处理，不通过伪造镜像标签或伪造判卷绕过。
15. 经源码确认，Fork 原生 `build_container` 硬编码 `mem_limit=16g`，先检查 base/env/instance 镜像且比较创建时间，不能直接复用已固定的远端预构建 digest。因此在同一 Evaluator Implementation 内加入 `fork_entry.py`，仅替换上游镜像准备和容器创建函数，使用固定摘要、无挂载、禁网、显式 CPU/内存/PID 的独立容器，再通过 `runpy` 执行原模块 CLI。上游源码不修改；`run_instance`、patch/test_patch 应用、测试命令、grading、summary 全部保持原样。真实测试与 manifest 必须清楚记录此基础设施兼容层，不能声称原生 CLI 零适配通过。
16. 恢复时全目录 pytest 收集发现 unit 与 integration 同名 `test_swe_bench.py` 冲突，尽管此前分目录执行通过；将集成文件改为唯一名称并同步引用，再复跑全目录默认测试。不删除缓存来掩盖命名冲突。
17. 在已规划的 `apps/backend/prototype_codex_harbor_e2e.py` 中连接既有 `ExecutionBackend` 与 `PatchEvaluator`：只允许单题单次原型；严格复核执行身份、终止原因及补丁引用；阶段成功/失败写入不可覆盖的原型证据，基础设施错误不得写成 unresolved。CLI 在真实 Codex 安全门槛完成前仅准备非秘密配置，不启动真实模型。契约测试使用显式替身验证编排，真实 NOP→Fork 探针另行标注无模型，二者均不能替代真实 Codex 验收。
18. 真实串联首测发现报告导入失败：Fork 已完成且报告存在，但 Windows 普通路径长 284 字符，Python `is_file()` 返回 false；同一文件使用 Windows 扩展长路径返回 true。按 `diagnosing-bugs` 先以已有证据和秒级单测复现，再仅在现有 Evaluator 的本机文件读取边界支持扩展路径；不改系统注册表、不缩短配置指纹、不重新判卷掩盖问题。修复后重放原报告，并运行一次原始串联回归。

本轮新增验证标准：全目录默认 pytest 能完成收集；格式、lint、strict mypy 通过；编排拒绝多题、错配运行、无效/被修改补丁及证据覆盖；正常结果与基础设施失败能保留各自证据。实际文件为 `prototype_codex_harbor_e2e.py`（M0 Composition Root）、`tests/contract/test_m0_pipeline.py` 与 `conftest.py`（替身编排契约及夹具）、`tests/integration/test_m0_pipeline_integration.py`（真实无模型串联）；不新增业务 Module 或 port。

实施偏差记录：原计划先自行寻找通用 Harbor patch extension point；实际固定提交已提供 collect hook 与 artifact manifest，故改为用任务级 collect hook 在容器销毁前生成 patch，再由项目 Adapter 做强校验。曾尝试读取 `framework/harbor/adapters/swegym/pyproject.toml`，该文件不存在；该 Adapter 不是独立 Python 包，必须通过 Harbor 根环境或项目薄适配使用。项目环境最初在默认沙箱内访问 PyPI 因 Windows socket 权限错误 10013 失败，后续仅为对应 `uv` 进程注入 `127.0.0.1:7890` 并使用项目内缓存完成锁定和安装，没有改变系统代理。

本次实际进度：Harbor 执行/patch/有界日志/超时清理已实测；固定 Fork 的独立 Linux 环境、63 包哈希锁、Evaluator Adapter 与五类补丁判卷已实测。M0 脚本已串接既有 ports，含原型标记、配置冻结、执行身份/patch 内容复核、分阶段证据与基础设施错误不伪装 unresolved；当前只供内部测试/NOP，CLI 只开放 `--check`。真实串联曾暴露 Windows 长路径报告读取失败，已用秒级单测定位和修复，最终回归见本记录末尾。真实 Codex、网络/凭据/轨迹验收仍未完成，M0/MVP 均未完成。

本次恢复的立即措施已经完成：集成探针只把 Agent 临时替换为上游 `nop`，不注册为生产 Agent。实测发现 Harbor 的 Job `result.json` 不落盘 `trial_results`，真实结果须枚举子 Trial 目录；Windows 子进程必须显式使用 UTF-8；artifact 改为一次收集 `/logs/artifacts` 到 `artifacts/agentexam`，避免隐式收集与显式单文件来源重叠。根据这些事实已开始结果映射草稿，但用户要求立即停止，故没有继续修复或测试。

第三次恢复措施：先把 `result_mapper.py` 的纯解析/制品值转换拆入同一 Harbor Adapter 目录的 `result_values.py`，使每个 Python 文件回到 200 行以内并修复 `slots=True` 对象的已知错误；补齐成功、缺失 Job/Trial、进程非零但已完成、异常、patch 无效、usage/资源未知等单元测试；然后把真实 NOP 测试接入正式 mapper。只有 format/lint/strict mypy/普通测试和映射后的 NOP 都通过，才新增规划内的 `adapter.py`。

第三次恢复后续措施：在既有 Harbor Adapter seam 内新增 195 行的 `adapter.py`，不新增顶层模块或接口。它验证固定可执行文件和安全 Job ID，冻结唯一证据目录，调用精确 `harbor.exe run --config <path> --yes` 命令，继承宿主环境但只补 UTF-8/关闭 telemetry 参数，并将正常退出、外层超时或启动失败统一映射到项目结果。单元测试使用受控假进程，不调用模型；外层超时当前只证明结果与部分日志可保留，不能据此声称 Harbor 子进程或 Docker 资源已被可靠清理。

第四次恢复措施已完成：保留现有 `ExecutionBackend` 和 `HarborExecutionAdapter` 对外接口，在同一 Harbor Adapter 目录增加内部 `process_runner.py` 与 `process_evidence.py`。前者负责 `Popen` 生命周期及 Windows 进程树/POSIX 进程组超时终止，后者同时排空 stdout/stderr、每路最多持久化 50 MiB、超过部分继续排空但丢弃，并写显式截断 manifest。`adapter.py` 只消费结构化进程结果并把日志截断/清理告警附到每条运行。小上限真实子进程测试已覆盖双流超限、超时和启动失败；固定 Harbor NOP 已通过同一有界执行器，不发起模型调用。

第四次恢复实施偏差：初稿把上述两类职责都放进 `process_runner.py`，Ruff 格式化后为 216 行，超过项目默认 200 行指标；因此按职责拆出内部 `process_evidence.py`，而不是压缩可读性或申请超标。拆分后 Harbor 源目录恰好 8 个文件，仍不增加顶层 Module、Interface 或目录。默认受限环境不能调用 Windows `taskkill` 时，超时结果会显式包含 `HARBOR_PROCESS_TREE_CLEANUP_FAILED`；提升权限的真实父子进程探针则证明允许调用时父子进程均被终止。该探针不包含 Docker Compose，不能替代真实 Harbor 外层超时清理验证。

第五次恢复措施：不增加生产接口或第二套 patch 实现，只新增受环境变量 `AGENTEXAM_RUN_PATCH_INTEGRATION=1` 保护的 Docker 集成测试。测试使用已经固定且本机存在的 `python__mypy-15413` 摘要镜像，显式 `--network none`，把生产 `collect_patch.sh` 复制进一次性容器，分别制造跟踪文件修改、新文件、删除和容器内 Git commit；随后复制 `/logs/artifacts` 回 pytest 唯一临时目录，并调用生产 `validate_patch_artifact()` 校验完整文本、大小、SHA-256 和二进制标志。每个容器使用测试生成的唯一安全名称，并在 `finally` 中只删除该精确容器；失败不得宽泛清理其他 Docker 资源。测试文件已实现且为 122 行，Ruff 检查通过，默认运行结果为 4 项按设计跳过；用户要求立即交接，因此本窗口没有启动四个真实容器，不能记为集成通过。

第六次恢复措施：不新增测试或生产路径，直接显式启用现有 `test_collect_patch_scenarios.py`，为 pytest 指定新的 `runtime/prototype` 唯一证据目录。运行前核对该目录不存在；运行后检查四项实际结果及 `agentexam-patch-*` 精确名称容器是否残留。只有四种变更均由生产 hook 生成完整、哈希一致、非二进制的文本 patch 且测试容器全部清理，才把该门槛记为通过。

第七次暂停与调查结论：用户要求立即停止实现、汇总并本地提交。停止前只读检查发现 `LogCaptureSession.finish()` 当前对两个日志线程执行无超时 `join()`；若后代进程仍持有继承的 stdout/stderr 管道，调用方可能无限等待。固定 Harbor 自身在 Trial `finally` 中调用环境 `stop(delete=True)`，Docker 环境会执行精确 Compose `down --rmi local --volumes --remove-orphans`；Harbor CLI 也安装 SIGTERM 处理以进入该清理路径。但项目当前 Windows 超时使用 `taskkill /T /F`，POSIX 使用进程组 SIGKILL，因此外层强制终止可能绕过 Harbor 的优雅清理。以上是源码风险分析，尚未用真实 Harbor 超时探针复现，不能写成已发生或已修复。下一窗口应优先用上游 `nop` 加测试专用阻塞 collect hook 构造受控超时，不调用模型、不注册生产 sleep Agent；只检查并清理该 Trial 精确 Compose project 的资源，再在既有 Harbor Adapter seam 内作最小修复。

第八次恢复措施已完成：先让日志管道测试以 `TypeError` 证明 `finish()` 没有收束期限，再让真实 NOP + 阻塞 collect 探针证明强杀后残留精确 Compose 资源。修复保留 `ExecutionBackend` 和生产 Agent Registry 不变：`process_evidence.py` 用同一个总期限等待双流，Windows 只对仍阻塞的采集线程调用 `CancelSynchronousIo`，`process_runner.py` 把未收束流映射为显式告警；`config_mapper.py` 承担固定 Harbor 阶段预算计算；`result_values.py` 承担纯粹的启动失败结果转换；`adapter.py` 只在 `timed_out` 后读取本 Job 下路径名一致的 Trial 配置，并按固定 Harbor 相同规则净化 project name，再逐类查询、删除、复核精确 project label。没有全局 prune、通配删除、新生产接口或新生产目录。

完成标准：真实 Codex 在固定 SWE-Gym-Lite 单题上通过固定 Harbor Trial 产生经过大小、类型和 SHA-256 校验的完整 patch 与可追溯过程证据；固定 SWE-Bench-Fork 在独立干净环境生成可信确定性报告；成功、失败和清理证据中均未发现凭据内容或真实秘密路径。只有全部满足，M0 才标记完成并进入 M1。

## 受影响文件树

本次恢复实际变更（沿用总架构第 8 节已规划的 Evaluator 与 M0 入口，不新增业务模块；下方历史树是前八次提交的累积记录）：

```text
apps/backend/
├─ src/eval_platform/adapters/evaluation/
│  ├─ __init__.py           # Patch Evaluator Adapter 包
│  ├─ swe_bench.py          # 已实现 Adapter：冻结请求、调用 Fork、导入报告
│  ├─ result_mapper.py      # 严格身份/分类校验、空补丁/异常映射与 Windows 长路径读取
│  ├─ fork_entry.py         # Linux 入口：仅适配固定镜像和受限容器创建
│  └─ process.py            # WSL 命令、期限、缓存隔离与双标签容器清理
├─ prototype_codex_harbor_e2e.py # M0 Composition Root：仅无模型编排与只读 --check
├─ pyproject.toml           # pytest 增加脚本根导入路径，不新增生产依赖
├─ src/eval_platform/application/ports/evaluator.py # 增加错误与证据引用
├─ swebench-requirements.in # 固定 Fork setup.py 的运行依赖清单
├─ swebench-requirements.txt# Linux Python 3.12 依赖与分发文件哈希锁
├─ tests/unit/test_swe_bench.py              # 参数、证据不可覆盖与映射边界
├─ tests/contract/test_swe_bench_contract.py # 冻结 prediction、命令与清理所有权契约
├─ tests/contract/conftest.py               # 合成公开/隐藏标记夹具，拆分后避免测试超行数
├─ tests/contract/test_m0_pipeline.py       # 编排、失败、不覆盖与隐藏字段隔离契约
├─ tests/integration/test_swe_bench_integration.py # 五类真实补丁与清理；避免同名收集冲突
└─ tests/integration/test_m0_pipeline_integration.py # 真实 NOP＋测试注入无效修复→Fork 串联
runtime/tools/uv-linux/                     # 忽略：Linux uv 引导工具
framework/swe-bench-fork/.venv/             # 忽略：隔离 Linux Python 环境
```

验证方式：在 `apps/backend` 执行 `.venv/Scripts/ruff.exe check src tests`、`ruff format --check src tests`、`mypy src` 和 `pytest -q -m 'not integration'`；真实 Fork 测试须显式开启独立环境变量并检查实际 report/summary/log 与容器清理。已执行结果见本记录末尾；Ruff 与 mypy 还必须包含 `prototype_codex_harbor_e2e.py`。全套默认 pytest 必须成功收集，不能仅以分目录运行替代。

本次暂停时，实际进入主仓库的文件为：

```text
E:\9.1agent_exam\
├─ HANDOFF.md
│  # 更新 M0 真实进度、恢复顺序、安全边界和下一窗口提示词
├─ docs\actions\2026-09-05-m0-codex-harbor-implementation.md
│  # 本轮行动、实现、失败、验证结果和待续计划
├─ docs\architecture\ARCHITECTURE.md
│  # 将“尚无业务代码”更正为 M0 第一批代码已实现并验证
├─ docs\architecture\MODULE_CONTRACTS.md
│  # 同步 ExecutionBackend 有界日志、宿主清理证据与未验证边界
├─ docs\dependencies\DEPENDENCIES.md
│  # 同步固定数据、Harbor 环境、镜像和当前 CLI 动态事实
├─ docs\interfaces\HARBOR_EXECUTION.md
│  # 同步生产进程执行器、显式截断和 Harbor 超时后的 Compose 风险
├─ docs\interfaces\FRAMEWORK_INTERFACES.md
│  # 同步真实 Task/Harbor 契约测试状态和剩余接口问题
├─ docs\operations\LOCAL_DOCKER_ENVIRONMENT.md
│  # 同步 Docker 资源、磁盘、固定镜像和仍未验证的 Trial 边界
├─ apps\backend\
│  ├─ pyproject.toml
│  │  # Python 3.13、pyarrow 和开发检查的项目配置
│  ├─ uv.lock
│  │  # 项目依赖的可复现锁文件
│  ├─ src\eval_platform\
│  │  ├─ __init__.py
│  │  │  # 项目包标记
│  │  ├─ domain\
│  │  │  ├─ __init__.py  # domain 包标记
│  │  │  ├─ task.py      # Agent 公开任务、Evaluator 隐藏字段及 TaskBundle
│  │  │  ├─ agent.py     # 不可变 AgentConfiguration 与稳定配置指纹
│  │  │  └─ result.py    # 制品、Trial、确定性判卷结果和终止原因
│  │  ├─ application\ports\
│  │  │  ├─ __init__.py  # ports 包标记
│  │  │  ├─ execution.py # ExecutionBackend、请求和资源限制接口
│  │  │  └─ evaluator.py # PatchEvaluator 与判卷请求接口
│  │  └─ adapters\
│  │     ├─ __init__.py  # adapters 包标记
│  │     ├─ tasks\
│  │     │  ├─ __init__.py       # Task Adapter 包标记
│  │     │  ├─ swe_gym.py        # 校验固定 Parquet、隔离隐藏字段并渲染 Harbor task
│  │     │  └─ collect_patch.sh  # 容器销毁前按固定 base commit 导出完整 patch 元数据
│  │     └─ execution\
│  │        ├─ __init__.py        # Execution Adapter 包标记
│  │        └─ harbor\
│  │           ├─ __init__.py     # Harbor Adapter 包标记
│  │           ├─ config_mapper.py# 已深化：固定 Harbor JobConfig、运行绑定与外层超时预算
│  │           ├─ result_mapper.py# 已实现：Trial 子目录身份匹配与项目结果汇总
│  │           ├─ result_values.py# 已深化：原始值及进程启动失败的纯结果转换
│  │           ├─ adapter.py      # 已深化：固定 CLI、进程错误与精确 Compose 超时清理
│  │           ├─ process_runner.py# 已深化：进程树终止后以固定期限收束日志采集
│  │           ├─ process_evidence.py# 已深化：日志截断、收束超时告警和进程 manifest
│  │           └─ artifacts.py    # patch/原始结果大小、文本、哈希与元数据强校验
│  └─ tests\
│     ├─ unit\test_task_adapter.py          # 固定数据、公开/隐藏隔离与 task 渲染
│     ├─ unit\test_harbor_config_mapper.py # 固定配置、身份和秘密路径拒绝
│     ├─ unit\test_patch_artifacts.py      # 空/文本/阈值/二进制/哈希校验
│     ├─ unit\test_harbor_result_mapper.py # 已实现：身份、缺失、失败和制品映射
│     ├─ unit\test_harbor_result_values.py # 已实现：异常、usage 和时间纯转换
│     ├─ unit\test_harbor_adapter.py       # 已实现：CLI、UTF-8、证据不可覆盖与超时边界
│     ├─ unit\test_harbor_process_runner.py# 已扩展：后代持有日志管道时仍有界返回
│     ├─ contract\test_harbor_contract.py  # 真实 Harbor 类型与固定 Parquet 契约
│     ├─ integration\test_harbor_nop.py    # 已实测：有界进程、真实 Docker Trial、空 patch 与清理
│     ├─ integration\test_process_tree_cleanup.py# 已实测：显式超时后的父子进程清理
│     ├─ integration\test_collect_patch_scenarios.py# 已实测：真实镜像四类非空 patch
│     └─ integration\test_harbor_timeout_cleanup.py# 已实测：NOP 阻塞 collect 的真实 Compose 超时清理

忽略的运行时路径：
├─ framework\harbor\.venv\
│  # 已安装的固定 Harbor 环境；Windows 源码构建昂贵，不应重复创建
├─ runtime\tools\uv-bootstrap\
│  # uv 0.12.10 的隔离引导环境
├─ runtime\tools\data\
│  # 只含 pyarrow 22.0.0 的数据读取环境
├─ runtime\tools\cargo\ 与 runtime\tools\rustup\
│  # Rust 1.98.1 隔离工具链；没有修改系统 PATH
├─ runtime\cache\uv\ 与 runtime\cache\swe-gym-lite\
│  # 同盘包缓存和固定数据文件
└─ Docker image cache
   # 已拉取固定 python__mypy-15413 摘要镜像，并用于通过的 Harbor NOP Trial
```

设计模式与关系：`execution.py`/`evaluator.py` 是 Ports；`swe_gym.py` 是 Task Adapter；`adapter.py` 是 `ExecutionBackend` 的 Harbor Adapter；`config_mapper.py`、`result_mapper.py`、`result_values.py`、`process_runner.py`、`process_evidence.py` 与 `artifacts.py` 是它的内部边界。`process_runner.py` 管进程生命周期，`process_evidence.py` 管有界证据；`result_mapper.py` 负责流程与身份匹配，`result_values.py` 隔离纯值转换，避免单文件混合职责。`swe_bench.py` 实现 `PatchEvaluator`，内部 mapper/进程/Fork 入口隐藏平台差异；M0 入口依赖两个 ports 串联执行与判卷，不能把 evaluator 隐藏视图传给执行器。`tests/contract/conftest.py` 只承载测试夹具，避免 210 行测试初稿超标，不是新增业务模块。M0 不实现 Repository、Job State、HTTP Command 或生产 Composition Root，因为这些属于通过技术门槛后的 M1。

## 自验证方式

1. Git：`git status --short --branch`、`git diff --check`、`git rev-list --left-right --count HEAD...origin/main`；成功标准是无意外文件、无空白错误，开始基线仍可追溯。
2. 上游身份：三个 `framework` 源码分别核对 remote、40 位 HEAD 和干净工作树；成功标准是与 `DEPENDENCIES.md` 完全一致。
3. 静态质量：运行项目固定格式化、lint、类型检查和单元/契约测试；所有动态语言源文件默认不超过 200 行，每层目录默认不超过 8 个文件。
4. 安全测试：固定样例验证隐藏字段不进入 Agent 请求，秘密模式和真实路径不进入配置、日志、轨迹、patch 或 manifest；不输出被检测内容本身。
5. Patch 契约：验证空 patch、普通文本、新建/删除、256 KiB 警告、1 MiB 拒绝且不截断、二进制拒绝、SHA-256 和不可覆盖。
6. Harness：对固定首题运行 gold、空和错误 patch，检查实例报告、汇总、退出码与 `resolved`/基础设施错误映射。
7. Harbor：验证固定提交安装、`n_concurrent_trials=1`、`n_attempts=1`、Docker、`verifier.disable=true`、artifact 顺序、Trial 身份和失败映射。
8. 真实 Codex：仅一个固定单题 Trial；检查实际 patch、轨迹、usage、stdout/stderr、固定 Fork 报告和清理结果，不以 Agent 自述或 Harbor reward 代替判卷。
9. 资源与网络：记录 Trial 峰值、耗时、磁盘变化、代理实际注入和端点；确认当前代理连通没有被误写成闭卷防绕过已完成。
10. 文档：检查第一方 Markdown 相对链接、代码围栏、权威术语和状态；未运行或失败的检查必须保留为限制。

## 自验证结果

- 第九次恢复：`git fetch origin --prune` 成功，起点 `74f7149` 工作区干净，相对 `origin/main` 为领先 8/落后 0。固定 Fork HEAD 为 `242429c188fcfd06aad13fce9a54d450470bf0ac` 且干净；E 盘可用 `19,577,884,672` bytes。默认沙箱读取 WSL/Docker 被拒绝，提升权限只读探针确认 Ubuntu Python `3.12.3`、Docker Engine `27.5.1` 与 Unix socket 可用；固定 Fork 尚无 `.venv`。源码确认原生 CLI 无条件依赖 `resource`，且实例镜像存在也仍先检查 base/env 镜像，不能直接凭预构建镜像宣称可运行。
- Git 基线：`git fetch origin --prune` 退出码 0；开始时 `HEAD` 与 `origin/main` 同为 `42484d8472b3a258c49ca22d85a7b8a8b5166de2`，`git rev-list --left-right --count` 为 `0 0`，工作区干净。Git 多次提示无法读取用户级 `C:\Users\YINGYI\.config\git\ignore`，未影响仓库命令结果。
- 上游身份：三个 framework 仓库的 remote、完整 HEAD 和工作树已核验；SWE-Gym、SWE-Bench-Fork、Harbor 分别处于权威依赖文档固定提交且干净。
- 数据：固定 Parquet 为 230 行、唯一 `train` split；大小 `931,193` bytes 和 SHA-256 `f3a7cd934e8cc523b6053298d0abb2c82fd7db2b83f9f2ccba5944545aaa4eb1` 均与数据源 LFS 元数据一致。候选 `python__mypy-15413` 存在，repo/base commit/公开题面字段可解析；隐藏字段只统计了字段名和长度，没有写入 Agent 目录。
- 镜像：不带代理的 `docker manifest inspect` 因 Docker Hub header 超时退出 1；只给重试进程设置 `HTTP_PROXY/HTTPS_PROXY=http://127.0.0.1:7890` 后退出 0。固定 manifest digest 为 `sha256:f069dfc74592d438ad870bbc6dfb369bff1b125d21237ead49190b414f5f3456`，Linux/amd64，13 个压缩层共 `1,075,118,139` bytes。随后同样只为拉取进程注入代理，成功拉取该固定摘要镜像；本机 image ID 为 `sha256:2baa3c...054e`、镜像大小 `2,511,912,411` bytes。
- 当前网络：Windows `ProxyEnable=0`、`ProxyServer` 为空，FlClash/FlClashCore/Helper 进程运行。本轮没有开启系统代理或修改 VPN，只在具体网络命令的进程环境中使用 7890。
- 环境引导：已在忽略路径 `runtime/tools/uv-bootstrap` 创建 Python 3.13 虚拟环境，并安装 `uv 0.12.10`。
- 失败记录：首次执行 Harbor `uv sync --locked --extra huggingface --no-dev` 失败；`uv` 默认把临时文件从 E 盘移动到 C 盘缓存，Windows 返回跨盘移动错误 `os error 17`。未产生可用 Harbor 环境；下一次重试将显式把 `UV_CACHE_DIR` 固定到项目忽略的 E 盘缓存，不降低锁文件要求。
- 失败记录：第二次同步已成功解析锁文件、创建 `framework/harbor/.venv` 并下载主要 wheels，但 `litellm==1.93.0` 在固定锁文件中没有 Windows wheel，转为源码构建；构建器自动下载 Rust 时又在其默认缓存触发 `WinError 17`，同步以退出码 1 结束。已核实 Visual Studio 2022 Community 含 C++ 构建组件；修复路径是在项目忽略目录安装隔离 Rust 工具链，再从同一 E 盘缓存续装，而不是更改锁定依赖。
- 环境结果：已从 Rust 官方地址下载 `rustup-init.exe`，本地 SHA-256 `6f4bef66261261fcb43131be8720bab817d403a09edec7455c371974b90bdb7e` 与官方校验内容一致；以 `--no-modify-path --profile minimal` 安装到忽略的项目目录，得到 `rustc 1.98.1` / `cargo 1.98.1`。首次 Rust 直连安装长时间无进展后人工中止；仅给重试进程注入 `127.0.0.1:7890` 后安装成功，未改变 Windows 系统代理。
- Harbor 安装：在 Visual Studio 2022 C++ 开发环境中再次执行完全相同的 `uv sync --locked --extra huggingface --no-dev`，`litellm==1.93.0` 源码构建实际耗时 275 分 06 秒，随后成功安装 Harbor `0.22.0` 和 101 个锁定运行依赖。固定锁文件未修改。
- Harbor CLI：`framework/harbor/.venv/Scripts/harbor.exe --version` 退出 0 并返回 `0.22.0`；`--help` 与 `run --help` 可解析。源码确认关闭 verifier 时不要求 `tests/test.sh`，collect hook 仍在 Agent 之后、环境销毁之前运行。
- 源码探针偏差：读取不存在的 `adapters/swegym/pyproject.toml` 失败，证明该 Adapter 不是独立包；一次把真实 `template/task.toml` 误写成 `templates/task.toml` 的读取也失败，随后用 `rg --files` 找到正确路径并完成核验。未修改 Harbor 上游源码。
- 第一阶段交接时未执行的项目包与镜像工作已在恢复后继续，具体结果见下方新增记录。固定 Fork 环境、gold/空/错误 patch、凭据元数据检查、真实模型调用、Harbor Trial、轨迹与运行清理结果仍未执行，因此 M0 和 MVP 均不得标记完成。
- 第一次交接验证：主仓库 `git diff --check` 退出 0；两份交接文档的代码围栏数分别为 10 和 4，均为偶数；当时新增/修改 Markdown 的相对链接逐项解析后均存在；常见 API key、Bearer token 与 JWT 模式扫描无命中。Git 显示的 LF→CRLF 提示符合当前 Windows working copy 行尾设置，不是空白错误。
- 第一次提交失败记录：默认沙箱执行精确 `git add` 时无法创建 `.git/index.lock`，返回 `Permission denied`；两个目标文件仍保持未暂存，未留下锁文件或部分暂存。随后按用户明确授权在提升权限下重试同一精确文件列表，没有扩大提交范围。
- 第一次提交前复核：提升权限重试后只暂存 `HANDOFF.md` 与本行动记录；`git diff --cached --check` 退出 0，name-status 为 `M HANDOFF.md` 与 `A 本行动记录`，统计为 2 files / 250 insertions / 58 deletions。
- 交接提交：本地提交 `0caedda docs: hand off M0 implementation progress` 已创建且未 push；2026-09-06 恢复核验时主仓库工作区干净、本地领先远端 1 个提交。
- 恢复验证：三个 `framework` 仓库的 origin、完整 HEAD 与干净工作树再次匹配依赖事实源；`harbor --version` 为 `0.22.0`。Docker 只读探针见“恢复动态事实”；随后开始并完成下述 M0 第一批业务代码，固定 Fork 环境和真实 Trial 仍未开始。
- 项目环境：新增 `apps/backend/pyproject.toml` 与 `uv.lock`，固定 Python `>=3.13,<3.14`、`pyarrow 22.0.0`、`mypy 1.18.2`、`pytest 9.0.2`、`ruff 0.15.17` 与 `setuptools 80.9.0`。默认沙箱内 `uv lock`/`uv sync` 因 PyPI socket 权限错误 10013 失败；仅为对应进程注入 `HTTP_PROXY/HTTPS_PROXY=http://127.0.0.1:7890` 后成功完成锁定和安装。
- 代码与安全边界：固定 Task Adapter 校验 Parquet 大小与 SHA-256，只把题面、仓库、base commit 和固定 image digest 写入 Harbor task；隐藏判卷字段只保留在宿主 `EvaluatorTaskData`。Harbor 配置映射强制单次/串行/零重试、关闭 Harbor verifier、固定 Docker 资源与显式 Codex 版本/模型/推理强度，不接受凭据路径或 ID。patch 校验拒绝超过 1 MiB、二进制、非 UTF-8、哈希/大小不一致和疑似自然语言输出，超过 256 KiB只告警且绝不截断。
- 自动检查：`ruff format --check`、`ruff check`、严格 `mypy` 均通过；`pytest` 的 unit + contract 共 18 项通过。交接前完整复跑结果为 `18 passed in 0.89s`。契约测试直接加载固定 Parquet，并使用固定 Harbor 的真实 `JobConfig` 与 `Task(..., disable_verification=True)` 解析生成配置。项目自有 Python 文件最大 183 行，各层目录未超过 8 个文件。
- 固定镜像探针：`docker run --rm --network none` 确认 `/testbed` HEAD 为固定 base commit `e7b917ec7532206b996542570f4b68a33c3ff771`，容器用户为 `0:0`，bash 位于 `/usr/bin/bash`，Git 为 `2.34.1`；镜像内没有 Node/npm，因此 Codex 安装阶段仍需要受控网络和 Harbor 的 NVM/npm 路径实测。
- 第二次交接时的未执行项中，Harbor `nop` Trial、空 patch、artifact 目录和清理现已实测通过；新建、删除、Agent commit 的真实 Git diff 仍未覆盖。固定 Fork gold/空/错误 patch、凭据元数据、真实模型和 Codex 模型/reasoning effort 仍未检查或运行。M0 和 MVP 均不得标记完成。
- 第二次交接验证：代码的 format/lint/strict mypy/18 项测试全部复跑通过；`git diff --check` 通过；项目自有 Python 文件和每层目录数量均符合 200 行/8 文件指标；7 份本轮 Markdown 代码围栏均成对、相对链接均存在；对本轮代码与文档扫描常见 API key、Bearer token 和 JWT 形态无命中。默认沙箱再次因 Docker named pipe 权限无法重跑 Engine/image inspect，但已有本轮提升权限只读探针和实际 pull/run 成功证据，因此不把这次权限错误误记为 Docker Engine 故障。
- 第二次恢复 Git：交接提交 `37f04d2` 后 `git fetch origin --prune` 再次退出 0；工作区开始时干净，本地/远端领先落后为 `2/0`。
- NOP 集成测试基线：新增的 Docker 集成测试默认关闭，普通测试结果为 `18 passed, 1 skipped`；Ruff 与 strict mypy 同时通过。只有显式设置 `AGENTEXAM_RUN_HARBOR_INTEGRATION=1` 才会启动固定 Harbor/Docker。
- NOP 首次运行失败：显式探针在 pytest setup 阶段因 `runtime/prototype` 父目录尚不存在而返回 `WinError 3`，没有进入测试函数、Harbor 或 Docker。提升权限进程另对普通 `.pytest_cache` 报写权限警告，但不是本次主失败。后续创建精确父目录，并以 `-p no:cacheprovider` 关闭非必要缓存后重试；不得把这次结果记成 Trial 失败。
- NOP 第二次运行部分成功：固定 Docker Trial 实际完成 1/1，约 20 秒；持久化 Trial 的 `exception_info=null`、Agent 为 `nop 1.0.0`、Verifier 未运行，四个 patch 文件均由 Harbor 收集且没有遗留对应 Compose 容器。CLI 随后在 Windows GBK 控制台打印汇总字符 `•` 时触发 `UnicodeEncodeError`，因此外层进程退出 1；这是真实的宿主编码兼容问题，不是 Trial 失败。修复是在受控 Harbor 子进程显式设置 `PYTHONUTF8=1` 和 `PYTHONIOENCODING=utf-8`，不修改上游源码。
- NOP 第二次运行接口发现：落盘的 Job `result.json` 为减小热路径写入而故意不含 `trial_results`；真实 Trial 结果只在 Job 子目录各自的 `result.json` 中，未来结果 Adapter 必须枚举并严格校验唯一身份，不能按先前内存模型猜读 Job 文件。Harbor 还会隐式收集约定目录 `/logs/artifacts`，原四个显式单文件声明造成来源重叠警告和重复副本；Task 契约已改为一次收集整个约定目录到 `artifacts/agentexam`，宿主校验器读取该受控目录。
- NOP 第三次运行部分成功：UTF-8 子进程使 Harbor CLI 正常退出，单个 Trial 无异常且 Verifier 关闭；测试随后因断言落盘 `TrialConfig` 必须显式含 `environment.delete` 而失败。源码和实际 JSON 表明 Harbor 以 `exclude_defaults=true` 保存 Trial config，默认 `delete=true` 会省略。测试改为核对提交给 Harbor 的冻结输入明确为 `true`、落盘省略符合默认序列化，并以对应 Compose 容器/网络/卷均不存在作为实际清理证据。
- NOP 第四次运行部分成功：Harbor CLI/Trial 和单目录 artifact 收集均成功，宿主强校验随后发现目录内仍是旧元数据名 `model.patch.sha256/.bytes/.binary`，与稳定制品契约 `patch.sha256/.bytes/.binary` 不一致。原先四个显式 artifact 声明曾顺带重命名文件，合并为单目录后这一隐式行为消失；修复只把 collect hook 的三个输出名改为契约名称，不放宽校验或增加重复映射。
- NOP 最终成功：修正稳定元数据名后，证据 `runtime/prototype/m0-harbor-nop-20260906-04` 以 `1 passed in 18.40s` 通过。实际 Job 1/1 完成、Trial 无异常、Verifier 关闭、0-byte patch 与哈希/大小/二进制元数据通过宿主校验、manifest 只有一个目录项，且对应 Compose container/network/volume 均无残留。该结论只适用于 NOP 无模型探针。
- 结果映射草稿：新增 `HarborRunBinding`，配置映射强制请求形成完整 Agent×Task 笛卡尔积并为每个 Run 记录稳定 task/agent key；领域结果增加原始配置/结果、usage 和资源摘要接缝。`result_mapper.py` 已按真实子 Trial 目录开始映射，但暂停时为 296 行，超过项目 Python 200 行指标；其 `_usage()` 对 `slots=True` dataclass 使用 `__dict__` 是已知运行时错误；尚无单测、未接 NOP 集成测试，且加入这些草稿后的全套 ruff/mypy/普通 pytest 尚未复跑。下一窗口必须先修复并验证，不能把草稿记为完成。
- 本次暂停：用户明确要求停止、汇总给下一窗口并本地提交。只更新 `HANDOFF.md` 与本行动记录，不继续实现 Adapter；提交前仅执行适合交接的 diff/静态/测试核对，并如实记录失败。
- 本次交接检查：`git diff --check` 通过；strict mypy 对 17 个源文件通过；unit + contract 共 `20 passed in 0.75s`。Ruff 未通过：`config_mapper.py` 与 `result_mapper.py` 需要格式化，lint 共 4 项（1 个多余前向引用引号、2 个超长行、1 个应使用 `datetime.UTC`）；`result_mapper.py` 的 296 行也不符合 200 行指标。由于用户要求立即停止，本窗口不再修复这些草稿问题，下一窗口必须先处理。
- 第三次恢复检查：`git fetch origin --prune` 成功，主仓库起点干净且相对 `origin/main` 为 `3/0`；三个 framework 的 origin、固定 HEAD 与干净工作树再次匹配依赖事实源；Harbor CLI 仍为 `0.22.0`。Docker Client/Server 均为 `27.5.1`、可见内存 `10,429,505,536` bytes；E 盘可用 `19,606,081,536` bytes。
- 草稿修复结果：将结果映射拆为 197 行 `result_mapper.py` 与 170 行 `result_values.py`，修复 `slots=True` 对象无 `__dict__` 的运行时缺陷；新增身份不猜配、部分进程失败保留完成 Trial、Job/Trial 缺失、Harbor 异常、patch 缺失、usage/时间值等测试。`ruff format --check`、`ruff check`、strict mypy 均通过，unit + contract 为 `35 passed in 0.65s`；所有项目 Python 文件不超过 200 行，每层文件数仍不超过 8。
- 映射后 NOP 集成：证据 `runtime/prototype/m0-harbor-nop-20260906-05` 以 `1 passed in 20.56s` 通过；真实落盘 Job/Trial 经 task path + agent config 唯一匹配到 `m0-nop-run`，得到 `COMPLETED`、可信 0-byte patch、原始配置/结果引用与预期的 `TRAJECTORY_UNAVAILABLE`，同时保留原有 Verifier/manifest/Compose 清理断言。
- Harbor 进程 Adapter：新增固定可执行文件/项目根校验、安全证据路径、任务快照冲突拒绝、冻结配置、精确 CLI 调用、UTF-8 stdout/stderr、按 Trial 预算计算的外层超时和启动失败映射；配置快照不含逻辑凭据 ID 或 `CODEX_AUTH_JSON_PATH`。新增 3 项单元测试后，`ruff format --check`、`ruff check`、strict mypy 对 19 个源文件均通过，unit + contract 共 `39 passed in 0.81s`；`adapter.py` 195 行、测试 166 行，仍符合指标。测试没有启动真实 Harbor/Codex；当前整体捕获 stdout/stderr，尚未落实 50 MiB 日志限额和显式截断；外层 timeout 是否连带清理 Docker 资源也仍待真实失败探针。
- 第四次暂停：用户要求立即停止、汇总进度、写 Handoff 与下一窗口提示词，并在有改动时本地提交。本窗口不继续 fixed Fork、Composition Root 或真实模型工作；提交前只做完整静态/普通测试、文档一致性、安全扫描和 Git diff 核对，不 push。
- 第四次交接检查：最终复跑 `ruff format --check`、`ruff check`、strict mypy 对 19 个源文件均通过，unit + contract 为 `39 passed in 0.76s`；`git diff --check` 通过；8 份本轮 Markdown 的代码围栏成对且相对链接均存在；对本轮代码与文档扫描常见 API key、Bearer token 和 JWT 形态无命中；项目自有 Python 文件均不超过 200 行，每层源代码目录不超过 8 个文件。最终暂存内容与提交后工作树状态以提交后核对为准。
- 第四次恢复首次测试暴露两个真实问题：初版 Windows timeout 路径等待约 30.6 秒，且静态检查发现导入顺序、IO 类型和 Windows 上 POSIX API 类型问题。随后把进程树清理等待限制为 5 秒、失败时直接终止父进程，并隔离 POSIX 分支类型；没有掩盖清理失败，而是用 `HARBOR_PROCESS_TREE_CLEANUP_FAILED` 明示。
- 有界进程验证：`ruff check` 和 strict mypy 对 21 个源文件通过，unit + contract 为 `42 passed in 1.30s`。真实固定 Harbor NOP 通过生产 `run_bounded_process` 与正式 mapper，在 `runtime/prototype/m0-harbor-bounded-process-20260906-01` 为 `1 passed in 19.61s`；stdout 未截断、Trial/空 patch/原有 Compose 清理断言均通过，但测试为安全起见只把 Agent 改成上游 `nop`，没有调用模型，也没有直接调用公开 `HarborExecutionAdapter.execute()`。
- 父子进程清理验证：提升权限运行 `AGENTEXAM_RUN_PROCESS_TREE_INTEGRATION=1` 的真实 Windows 父子进程超时探针，在 `runtime/prototype/m0-process-tree-timeout-20260906-01` 为 `1 passed in 1.35s`，返回稳定退出码 124 且没有清理失败告警。它只证明宿主进程树路径，尚未证明外层杀死 Harbor 后由 Docker Compose 创建的容器、网络和卷被清理。
- 第五次暂停：用户再次要求立即停止、汇总给下一窗口、写 Handoff 与提示词，并把当前文件修改创建本地提交。本窗口不再开展 collect patch 场景、Harbor 外层超时 Docker 清理、固定 Fork、Composition Root 或真实模型工作；提交前只做适合交接的静态/普通测试、文档一致性、安全扫描和 Git 核对，不 push。
- 第五次交接检查：`ruff format --check` 显示 31 个文件已格式化，`ruff check` 通过，strict mypy 对 21 个源文件通过，unit + contract 为 `42 passed in 1.30s`；`git diff --check` 通过；项目 Python 文件均不超过 200 行，源代码每层目录不超过 8 个文件，Harbor 源目录恰好 8 个文件；7 份变更 Markdown 的代码围栏成对、相对链接均存在；对本轮代码与文档扫描常见 API key、Bearer token 和 JWT 形态无命中。第一次文档链接辅助脚本因根目录文件的父路径为空而产生 `Join-Path` 参数错误，修正为使用当前目录后重新运行并通过；没有据此掩盖项目检查失败。最终暂存内容与提交后工作树状态以提交后核对为准。
- 第五次恢复新增：`tests/integration/test_collect_patch_scenarios.py` 已以 122 行实现，默认关闭，只有显式设置 `AGENTEXAM_RUN_PATCH_INTEGRATION=1` 才创建四个固定摘要、禁网的一次性容器。该文件直接复制生产 collect hook 并调用生产 patch 校验器，没有增加生产接口或替代实现。Ruff 格式/检查通过；单独默认 pytest 为 `4 skipped in 0.06s`。本轮还只读确认镜像 `/testbed` 干净、HEAD 匹配固定 base commit，且 `sha256sum`、`mktemp` 可用；四种变更没有真实执行。
- 第六次暂停：用户要求停止当前实现，汇总进度与情况给下一窗口，在存在修改时创建本地提交，并提供目标不变、遵守提示词原则的下一窗口提示词。本窗口收到要求后没有启动 Docker 容器、固定 Fork 或模型调用，只收束现有测试代码和交接文档，不 push。
- 第六次交接检查：`ruff format --check` 显示 32 个文件已格式化，`ruff check` 通过，strict mypy 对 21 个源文件通过；unit + contract 加默认关闭的 collect-patch 集成为 `42 passed, 4 skipped in 1.37s`，四项跳过是未设置真实 Docker 开关的预期结果，不是集成通过。`git diff --check` 通过；新测试 122 行，Harbor 源目录 8 个文件、integration 测试目录 3 个文件；两份变更 Markdown 的代码围栏成对、相对链接均存在；三份变更文件的常见 API key、Bearer token 和 JWT 形态扫描无命中。第一次陈旧措辞搜索从 `apps/backend` 工作目录引用根路径而报“找不到文件”，改在仓库根目录重跑后只命中描述未来“全部通过”条件的正常句子；没有掩盖检查失败。最终暂存内容与提交后工作树状态以提交后核对为准。
- 第六次恢复 collect-patch 验证：快速基线为 `ruff format --check` 32 个文件、`ruff check`、strict mypy 21 个源文件全部通过，unit + contract 为 `42 passed in 2.03s`。随后显式设置 `AGENTEXAM_RUN_PATCH_INTEGRATION=1`，以唯一证据目录 `runtime/prototype/m0-collect-patch-scenarios-20260906-01` 运行现有集成测试，固定摘要镜像在 `--network none` 下对跟踪文件修改、新文件、删除和容器内 Git commit 四种场景得到 `4 passed in 5.91s`。每种结果均经生产 `validate_patch_artifact()` 复核非空、完整 UTF-8、大小、SHA-256、非二进制和预期 diff 标记；四个 `model.patch` 分别为 279、233、1,462、281 bytes，commit 场景还确认 HEAD 已变化但相对固定 base commit 的补丁仍完整。测试前后 Docker 均为 18 个容器、13 个运行和 21 个镜像，`agentexam-patch-*` 精确名称查询无输出，证明四个一次性容器均已清理。该证据只覆盖 collect hook 与精确容器清理，不覆盖 Harbor Compose 外层超时、模型、凭据或固定 Fork。
- 第七次交接检查：用户要求暂停后没有再修改或运行生产/测试代码，也没有启动容器、固定 Fork 或模型调用；只把四场景证据与源码风险调查同步到 8 份 Markdown。第一次文档检查脚本因 PowerShell 在双引号字符串中把冒号紧随的变量名解析为非法引用而失败，改用 `${file}` 明确变量边界后重跑：8 份变更文档的代码围栏成对、相对链接均存在，`git diff --check` 通过，常见 API key、Bearer token 和 secret 赋值形态扫描无命中。提交前再次运行同一检查确认最终文本，随后只创建本地提交，不 push。
- 第八次恢复 Git：`git fetch origin --prune` 成功；`HEAD=aca01e7`、`origin/main=42484d8`，本地/远端为 `7/0`，开始时工作区干净。第七个本地提交主题为 `docs: hand off verified patch scenarios`，本轮继续未 push。
- 日志收束红灯：新增的开放管道单测首先以 `TypeError: LogCaptureSession.finish() got an unexpected keyword argument 'timeout_sec'` 失败，证明生产接口没有期限；另一个只读实验确认 Windows 上从主线程直接 `close()` 正在阻塞读取的 pipe 会一同阻塞，不能作为修复。对测试线程使用 Windows `CancelSynchronousIo` 的隔离实验成功取消同步读并让线程退出，因此生产实现只在收束期限后对仍存活的日志线程使用该机制；非 Windows 仍有总期限并返回不完整告警。
- Harbor Compose 红灯：`runtime/prototype/m0-harbor-timeout-red-20260906-01` 使用固定镜像、公开 Adapter、上游 `nop` 和测试专用阻塞 collect，结果为 `1 failed in 48.51s`。强杀后精确 project `agentexam-timeout-probe__zd6kqcw__env` 留下容器 `1c819e8021ee`、网络 `f53dc51c4e0b` 和本地镜像 `d44d1832ae94`，无 volume；测试 `finally` 只按该 project label 清理，随后容器/网络/卷/镜像总数恢复为 `18/5/15/21`。
- Harbor Compose 绿灯：生产修复后的第一次复测实际查询四类资源均为空，但测试误用 `any(dict.values())`，因每个 project 的资源字典本身非空而错误报告失败；修正为检查嵌套资源 ID，并新增无 `CLEANUP_FAILED/UNVERIFIED` 告警断言。新证据 `runtime/prototype/m0-harbor-timeout-green-20260906-02` 为 `1 passed in 49.47s`；精确 project `agentexam-timeout-probe__tmkz7uf__env` 的四类 label 查询均无输出，测试后总数仍为 `18/5/15/21`。
- 回归验证：`ruff format --check` 首次诚实报告新集成测试需要格式化；执行 Ruff 格式化后，33 个文件格式检查、Ruff lint、strict mypy 21 个源文件均通过，unit + contract 为 `44 passed in 6.60s`。默认关闭的 integration 为 7 项按设计跳过，不算真实通过；其中本轮超时探针已通过上面的显式开关实测。正常 Harbor NOP 回归 `runtime/prototype/m0-harbor-timeout-regression-20260906-01` 为 `1 passed in 18.87s`；真实 Windows 父子进程回归 `runtime/prototype/m0-process-tree-timeout-20260906-02` 为 `1 passed in 1.34s`。所有生产 Python 文件不超过 200 行，Harbor 源目录仍为 8 个文件；unit 与 integration 目录分别为 7 和 4 个文件。
- 第八次暂停：用户要求立即停止当前实现、汇总进度与情况、更新 Handoff 和下一窗口提示词，并把已有文件修改创建本地提交。本窗口收到要求后不再实现固定 Fork、Composition Root 或真实 Codex Trial，不再启动容器或模型调用；只更新交接状态、执行提交前核对并创建本地提交，不 push。最终检查与提交事实记录在提交后核对中。
- 第八次交接检查：`ruff format --check` 显示 33 个文件已格式化，Ruff lint 通过；第一次直接按 `pyproject.toml` 的 package 配置调用 mypy 时因已安装包缺少 `py.typed` 标记退出 1，改为对项目源码执行 `mypy src` 后严格检查 21 个源文件通过。unit + contract 为 `44 passed, 7 deselected in 6.67s`，7 项真实 integration 因本次明确不启动 Docker 而被排除，不算重新通过。`git diff --check`、8 份变更 Markdown 的围栏/相对链接、Python 200 行/源目录 8 文件指标均通过。第一次敏感形态扫描因 PowerShell/PCRE2 引号导致正则编译失败，修正模式后重跑，对全部变更文件未发现常见 API key、Bearer token 或 JWT 形态。16 个精确目标以主题 `fix: clean up timed-out Harbor trials` 创建本地提交；提交后核对工作区干净，`main...origin/main [ahead 8]`，未 push。

## 2026-09-06 Fork 与 M0 编排恢复验证

本地检查点说明：用户随后明确要求“本地提交一次后继续 MVP 实现”。提交前复跑 Ruff 格式/检查与 strict mypy 通过，默认全套为 `79 passed, 13 skipped in 6.99s`；不重复启动已通过的 Docker 探针。本次仅把现有 Fork、M0 编排、测试和同步文档创建本地检查点，不 push；实际提交身份与后续实现记录在恢复续记中。

### 已完成的 Fork 依赖与独立判卷

- 固定 Fork 源码仍为 `242429c188fcfd06aad13fce9a54d450470bf0ac`，未修改上游源码；Linux Python 为 Ubuntu WSL2 的 `3.12.3`。从固定 `setup.py` 提取 12 个直接运行依赖，生成 63 包的 Linux/Python 3.12 哈希锁。实际安装与 CLI `--help` 通过，恢复方式以依赖事实源为准。
- Windows uv 编译锁时曾尝试下载托管 Python，跨盘重命名缓存失败产生警告；依赖锁仍生成成功。后续明确 `--no-python-downloads`，使用已存在的 Linux Python；Windows 进程通过单次代理下载 Linux wheels，未修改系统网络设置。上游 SyntaxWarning/runpy RuntimeWarning 保存在日志中，不记为无警告。
- 固定基础设施兼容层不修改 grading：使用已存在的镜像 digest，禁网、无宿主挂载、CPU 1、内存与含交换总额 4 GiB、PID 256、去能力与禁止提权。每次记录镜像/任务/源码/锁哈希及实际容器配置。
- 容器清理同时按 `run_id` 和证据目录哈希两个 label 限定所有权；Linux timeout 与宿主有界进程负责期限。读取上游产生的四个 `__pycache__` 目录后，将它们移至忽略的 `runtime/cache/fork-initial-pycache-20260906`，没有删除；随后配置独立 `PYTHONPYCACHEPREFIX`。上游 Git 工作区复核干净。
- 真实测试均以 `AGENTEXAM_RUN_FORK_INTEGRATION=1`、`-p no:cacheprovider` 和全新 `--basetemp` 运行；入口现名为 `tests/integration/test_swe_bench_integration.py`。以下结果是额度中断前的实际运行，并非本轮重新全部启动：

| 场景 | 证据目录（位于 runtime/prototype） | 实际结果 |
|---|---|---|
| 空 patch | `m0-fork-empty-20260906-01` | 1 passed / 4 deselected，18.38 s；明确空补丁分类 |
| gold + wrong | `m0-fork-patches-20260906-01` | 2 passed / 3 deselected，75.97 s；gold resolved=true，wrong=false |
| 不可应用 + 测试超时 | `m0-fork-errors-20260906-01` | 2 passed / 3 deselected，67.23 s；均返回 HARNESS_EVALUATION_FAILED，不写普通 unresolved |
| 双标签清理回归 gold | `m0-fork-ownership-20260906-01` | 1 passed / 4 deselected，38.20 s；无剩余容器 |

以上场景的原始 report/summary/test_output 与清理证据均保留在对应目录；正确/错误补丁对同一 frozen FAIL_TO_PASS 测试产生不同真实结果。资源动态事实只由本机 Docker 文档维护。

### 本轮编排与长路径问题

- 用户要求额度恢复后先汇报测试再继续下一任务。恢复确认 `HEAD=74f7149`、ahead 8，已有未提交 Fork 改动保持原样，没有新建提交或 push。宿主 `codex --version` 本轮仍为 `0.153.0`；已向用户询问是否固定该版本，未把默认预选视为确认。
- 使用 `action-document` 持续记录；OpenAI Docs 官方非交互页面核对后仅保留既有 ChatGPT 所有者认证政策，不改 API Key，不发真实模型调用。当前 CLI 的 `--check` 输出固定任务快照已验证、`real_codex_ready=false`，待版本/模型/effort、网络白名单和秘密生命周期。
- 首次全目录 pytest 失败于 unit/integration 同名模块收集；将集成文件改名后，全目录为 `62 passed, 12 skipped in 7.16s`。12 项因显式开关未打开而跳过，不是重新通过。静态基线 41 个格式文件、26 个源码 mypy 均通过。
- 新编排契约覆盖正常 resolved/unresolved/空 patch、执行失败、错配身份、截断/越界/篡改 patch、Harness 错误与证据保留、禁止覆盖、多题/冻结任务不一致拒绝、真实入口未开放；16 项通过。初稿测试格式化后 210 行，按夹具与行为职责拆到现有 contract 目录的 `conftest.py`，没有放宽 200 行指标。初次 lint 报导入/长行，修正后通过。
- 真实串联使用公开 Harbor Adapter、固定上游 NOP、测试专用 collect 前置写入无关文件和生产 collect hook，生成真实非空 patch，再经生产 Fork Adapter 独立测试。没有注册生产 NOP，没有模型或秘密注入；不把测试人工造 patch 误记为 Codex 修复。
- 首次串联 `runtime/prototype/m0-pipeline-nop-20260906-01` 为 `1 failed in 98.08s`：Fork 已完成、unresolved=1/error=0/无残留，但 Windows 导入 284 字符报告路径时 `is_file=false`，同一文件扩展路径 `is_file=true`。
- 按 `diagnosing-bugs` 建立秒级回归：`pytest -q tests/unit/test_swe_bench.py -k max_path -p no:cacheprovider` 修复前 `1 failed, 16 deselected in 0.06s`。仅在 Evaluator 本机读取边界转换扩展路径，保留原始稳定 object key 和配置指纹，不改系统注册表。修复后 mapper + contract 共 `36 passed in 0.84s`，Ruff 45 个文件、strict mypy 27 个源文件通过。
- 原失败证据只读重放成功：patch_applied=true、resolved=false，报告 SHA-256 `96546551ec3e04ea7e3eb8a3a1c2efae0033bb0bde156a2f00a1952d58ef3d62`，5 个日志引用；没有改写原失败记录或重新判卷。完整串联回归使用新目录 `m0-pipeline-nop-20260906-02`，最终结果见下方续记。

### 本轮最终验证与下一任务

- 文档收尾：8 份变更 Markdown 的代码围栏与相对链接检查通过，项目源码/测试及文档的常见 Key/Bearer/JWT 形态扫描无命中。一次临时覆盖 `core.autocrlf=false` 的检查把原有 CRLF 误报为尾随空白；去掉覆盖、按仓库实际配置运行 `git diff --check` 通过。两次多文件补丁调用曾返回上下文不存在，但读回显示前部目标已更新，故仅补齐未写入目标并逐项核验，没有盲目重复覆盖。

- 完整串联修复后实测：`AGENTEXAM_RUN_M0_INTEGRATION=1`，运行 `python -m pytest -q tests/integration/test_m0_pipeline_integration.py -p no:cacheprovider --basetemp=E:\9.1agent_exam\runtime\prototype\m0-pipeline-nop-20260906-02`，结果为 **1 passed in 63.56s**。断言实际上游 Agent 为 NOP、生产 collect 生成非空 patch、传给 Fork 的字节完全相同、独立验证 patch_applied=true/resolved=false、报告成功导入，以及本 Trial 的 Compose container/network/volume/image 和 Fork 容器都无残留。这是无模型技术串联，不是 Codex M0 验收。
- 最终快速全套：在 `apps/backend` 使用 `.venv/Scripts` 工具，`ruff format --check src tests prototype_codex_harbor_e2e.py` 为 45 个文件；`ruff check` 同路径通过；`mypy src prototype_codex_harbor_e2e.py` 为 27 个源文件通过；默认 `python -m pytest -q -p no:cacheprovider` 为 **79 passed, 13 skipped in 7.05s**。13 个集成项按默认开关跳过；本轮显式运行的串联结果单独如上，不混入默认通过数。
- 最终只读核对八份 Fork 清理记录均 `verified=true`、remaining=0，当前 Evaluator label 容器查询为 0；固定 Fork 工作区干净。资源对象数与磁盘动态值同步到本机 Docker 事实源，未删除其他容器/镜像/卷。
- 项目 45 个 Python 文件均不超过 200 行，每层不超过 8 个源码/测试文件；`git diff --check` 通过。Git 的 LF/CRLF 提示属于行尾转换提示，不是 diff 错误。未增加临时 DEBUG 日志，首测失败证据留存而非删除。
- 同步职责：`HANDOFF.md` 维护恢复入口与下一窗口提示词；`ARCHITECTURE.md` 维护规划树和实施队列；`MODULE_CONTRACTS.md` 维护错误与公开/隐藏边界；`FRAMEWORK_INTERFACES.md` 维护 Fork 调用/长路径兼容；`HARBOR_EXECUTION.md` 维护执行验收；`DEPENDENCIES.md` 维护独立依赖锁；`LOCAL_DOCKER_ENVIRONMENT.md` 维护资源动态事实；本行动记录唯一维护本轮命令、失败和结果。
- 下一任务：先确认真实评测 Codex CLI 固定版本，再确认模型/effort；随后复用固定 Harbor 已有 `network_mode`/`allowed_hosts` 能力验证生成阶段端点白名单、防绕过与凭据生命周期。此轮只是只读发现已有网络能力，尚未把它记为实测。真实 Codex CLI 入口仍关闭，不启动模型、不读取秘密、不开始 M1。本轮未提交、未 push，保留当前可审阅工作区。
