# M0 Codex → Harbor → SWE-Bench-Fork 实现行动记录

## 状态与情况说明

- 状态：已暂停并交接；M0 未完成。2026-09-06 用户要求停止当前实现、汇总给下一窗口并本地提交。
- 来源请求：用户要求先核对 Git 为最新状态，再以长期目标开始实现 MVP，并严格遵守架构、模块契约和接口等权威文档。
- 当前范围：只实施 M0 本机技术原型。使用固定 SWE-Gym-Lite 单题、固定 Harbor、真实 Codex 和固定 SWE-Bench-Fork，形成可检查的 patch 与判卷证据；M0 通过后另建 M1 行动记录。
- Git 基线：2026-09-05 已执行 `git fetch origin --prune`；本地 `main` 与 `origin/main` 均为 `42484d8472b3a258c49ca22d85a7b8a8b5166de2`，领先/落后为 `0/0`，开始时工作区干净。
- 已读取边界：`AGENTS.md`、`HANDOFF.md`、`CONTEXT.md`、最新 MVP 决策行动记录、总架构、模块契约、依赖事实源、Harbor/框架/Codex 认证接口、本机 Docker 事实和 Harbor ADR。
- 已确认依赖身份：SWE-Gym `b681068ca20628c6987b7416cc4cf03f06b77ba5`、SWE-Bench-Fork `242429c188fcfd06aad13fce9a54d450470bf0ac`、Harbor `6af8d6e31eced13b93849cdf80feeadf24603d15`。
- 当前动态事实：本机 Python 为 `3.13.2`；Codex CLI 为 `0.153.0`，不同于旧文档探针的 `0.142.0`，尚未选作项目固定版本；Docker Desktop `4.38.0` / Engine `27.5.1` 当前可响应；E 盘开始时可用 `22,829,572,096` bytes；三个框架源码现均已恢复到权威文档固定提交并保持干净。
- 数据事实：`SWE-Gym/SWE-Gym-Lite` 当前仅有 `train` split，共 230 条；本轮固定读取不可变 revision `61231f2c90b18985b42a1419738a240085a15107`。Parquet 已保存到忽略的运行时缓存，大小 `931,193` bytes，SHA-256 为 `f3a7cd934e8cc523b6053298d0abb2c82fd7db2b83f9f2ccba5944545aaa4eb1`。
- Harbor 源码事实：固定提交要求 Python `>=3.12`，仓库 `.python-version` 为 `3.13`，项目版本为 `0.22.0`；固定提交已经内置 `adapters/swegym`、Codex Adapter 与 `[[verifier.collect]]`。单步 Trial 的顺序是 Agent、日志同步、collect hook、artifact 收集、可选 verifier；因此全局关闭 verifier 时 collect/artifact 仍执行。
- 复用边界：内置 SWE-Gym Adapter 会用未指定 `revision` 的 `load_dataset()` 读取远端最新数据，并把含 `gold_patch`、`test_patch`、`FAIL_TO_PASS`、`PASS_TO_PASS` 的原始 datum 写入任务 `tests/config.json`。M0 将复用其镜像命名和 Harbor 任务约定，但保留项目既有规划中的薄 `adapters/tasks/swe_gym.py`，直接读取已校验的固定 Parquet，只生成 Agent 必需的公开任务文件；隐藏字段只交给独立 Evaluator。
- OpenAI 官方事实复核：Codex 当前仍支持 ChatGPT 登录和 API Key 登录；`codex exec` 是非交互入口，支持 `--ephemeral`、`--json` 和显式 sandbox；文件型缓存含访问令牌，必须按密码处理。项目仍采用已经确认的评测机所有者 ChatGPT 登录政策，不改为 API Key。
- 已知未知：collect hook 是否能稳定生成包含未跟踪/删除/空输出以及 Agent 自行 commit 的完整 patch；Codex 模型 ID、所需端点、Token 刷新、日志脱敏和异常路径清理；固定 Fork 在 Windows/WSL2 + Docker Desktop 的真实行为；真实单题的资源峰值与清理结果。
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

实施偏差记录：原计划先自行寻找通用 Harbor patch extension point；实际固定提交已提供 collect hook 与 artifact manifest，故改为用任务级 collect hook 在容器销毁前生成 patch，再由项目 Adapter 做强校验。曾尝试读取 `framework/harbor/adapters/swegym/pyproject.toml`，该文件不存在；该 Adapter 不是独立 Python 包，必须通过 Harbor 根环境或项目薄适配使用。

完成标准：真实 Codex 在固定 SWE-Gym-Lite 单题上通过固定 Harbor Trial 产生经过大小、类型和 SHA-256 校验的完整 patch 与可追溯过程证据；固定 SWE-Bench-Fork 在独立干净环境生成可信确定性报告；成功、失败和清理证据中均未发现凭据内容或真实秘密路径。只有全部满足，M0 才标记完成并进入 M1。

## 受影响文件树

本次暂停时，实际进入主仓库的文件只有：

```text
E:\9.1agent_exam\
├─ HANDOFF.md
│  # 更新 M0 真实进度、恢复顺序、安全边界和下一窗口提示词
└─ docs\actions\2026-09-05-m0-codex-harbor-implementation.md
   # 本轮行动、失败、环境结果和待续实施计划
```

没有创建 `apps/backend` 或任何业务代码。下列内容仍是按已确认架构规划的下一窗口最小预期树；实现时必须按实际需要更新，不能把计划文件当成已经存在：

```text
E:\9.1agent_exam\
├─ apps\backend\
│  ├─ pyproject.toml
│  │  # M0/M1 共用 Python 基线、依赖、测试与命令入口；只固定实测依赖
│  ├─ prototype_codex_harbor_e2e.py
│  │  # M0 薄入口；选择固定单题并编排 Harbor、patch 校验和固定 Fork
│  ├─ src\eval_platform\
│  │  ├─ domain\
│  │  │  ├─ task.py
│  │  │  │  # EvaluationTask；严格区分 Agent 可见字段和 Evaluator 隐藏字段
│  │  │  ├─ agent.py
│  │  │  │  # AgentConfiguration；记录固定 Codex 身份和非秘密配置
│  │  │  └─ result.py
│  │  │     # ArtifactRef、执行结果和确定性结果的分层对象
│  │  ├─ application\ports\
│  │  │  ├─ execution.py
│  │  │  │  # ExecutionBackend Port；M0 脚本只依赖项目接口
│  │  │  └─ evaluator.py
│  │  │     # PatchEvaluator Port；正确性不由 Harbor 判断
│  │  └─ adapters\
│  │     ├─ tasks\swe_gym.py
│  │     │  # Task Adapter；固定数据身份并阻止隐藏答案进入 Agent 视图
│  │     ├─ execution\harbor\
│  │     │  ├─ adapter.py
│  │     │  │  # HarborExecutionAdapter；固定并发、Verifier、Trial 和错误边界
│  │     │  ├─ config_mapper.py
│  │     │  │  # 项目请求到真实 Harbor 配置的唯一转换点
│  │     │  ├─ result_mapper.py
│  │     │  │  # Harbor 结果到项目结果的唯一转换点
│  │     │  └─ artifacts.py
│  │     │     # patch/日志/轨迹读取、大小、文本、哈希和脱敏校验
│  │     └─ evaluation\swe_bench.py
│  │        # 固定 Fork 子进程 Adapter；生成 prediction 并规范化报告
│  └─ tests\
│     ├─ unit\
│     │  # 不耗模型额度的领域、patch、脱敏、限额和错误映射测试
│     ├─ contract\
│     │  # Fake/Harbor 与 Evaluator 的接口契约测试
│     └─ integration\
│        # Docker、固定 Fork 和最终单题真实闭环测试
├─ framework\harbor\
│  # 被 .gitignore 排除的固定第三方源码；只恢复和核验，不修改上游
├─ docs\actions\2026-09-05-m0-codex-harbor-implementation.md
│  # 本行动的实时状态、实际文件树、验证命令和证据
├─ docs\dependencies\DEPENDENCIES.md
│  # 仅同步已核验的数据 revision、实例、版本和安装状态
├─ docs\interfaces\
│  ├─ HARBOR_EXECUTION.md
│  │  # 仅同步真实 Harbor/Codex/patch 接口发现和 M0 验收状态
│  └─ FRAMEWORK_INTERFACES.md
│     # 仅同步真实数据、CLI 与 Harness 接口事实
├─ docs\operations\LOCAL_DOCKER_ENVIRONMENT.md
│  # 同步本轮重新测得的动态环境、资源和网络事实
├─ docs\architecture\ARCHITECTURE.md
│  # M0 完成后只更新实现状态和与实际一致的文件树
└─ HANDOFF.md
   # 同步下一任务恢复入口、Git 状态和 M0 真实进度

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
└─ runtime\prototype\<run-id>\
   # 尚未创建；未来本机原型证据不进入正式排行或 Git
```

设计模式与关系：`execution.py` 是 Port，`HarborExecutionAdapter` 是 Adapter，M0 脚本是 Composition Root/技术编排入口；`swe_gym.py` 和 `swe_bench.py` 分别是 Task 与 Evaluator Adapter。M0 不实现 Repository、Job State、HTTP Command 或生产 Composition Root，因为这些属于通过技术门槛后的 M1。

## 自验证方式

1. Git：`git status --short --branch`、`git diff --check`、`git rev-list --left-right --count HEAD...origin/main`；成功标准是无意外文件、无空白错误，开始基线仍可追溯。
2. 上游身份：三个 `framework` 源码分别核对 remote、40 位 HEAD 和干净工作树；成功标准是与 `DEPENDENCIES.md` 完全一致。
3. 静态质量：运行项目固定格式化、lint、类型检查和单元/契约测试；所有动态语言源文件默认不超过 200 行，每层目录默认不超过 8 个文件。
4. 安全测试：固定样例验证隐藏字段不进入 Agent 请求，秘密模式和真实路径不进入配置、日志、轨迹、patch 或 manifest；不输出被检测内容本身。
5. Patch 契约：验证空 patch、普通文本、新建/删除、256 KiB 警告、1 MiB 拒绝且不截断、二进制拒绝、SHA-256 和不可覆盖。
6. Harness：对固定首题运行 gold、空和错误 patch，检查实例报告、汇总、退出码与 `resolved`/基础设施错误映射。
7. Harbor：验证固定提交安装、`n_concurrent_trials=1`、`n_attempts=1`、Docker、`verifier.disable=true`、artifact 顺序、Trial 身份和失败映射。
8. 真实 Codex：仅一个固定单题 Trial；检查实际 patch、轨迹、usage、stdout/stderr、固定 Fork 报告和清理结果，不以 Agent 自述或 Harbor reward代替判卷。
9. 资源与网络：记录 Trial 峰值、耗时、磁盘变化、代理实际注入和端点；确认当前代理连通没有被误写成闭卷防绕过已完成。
10. 文档：检查第一方 Markdown 相对链接、代码围栏、权威术语和状态；未运行或失败的检查必须保留为限制。

## 自验证结果

- Git 基线：`git fetch origin --prune` 退出码 0；开始时 `HEAD` 与 `origin/main` 同为 `42484d8472b3a258c49ca22d85a7b8a8b5166de2`，`git rev-list --left-right --count` 为 `0 0`，工作区干净。Git 多次提示无法读取用户级 `C:\Users\YINGYI\.config\git\ignore`，未影响仓库命令结果。
- 上游身份：三个 framework 仓库的 remote、完整 HEAD 和工作树已核验；SWE-Gym、SWE-Bench-Fork、Harbor 分别处于权威依赖文档固定提交且干净。
- 数据：固定 Parquet 为 230 行、唯一 `train` split；大小 `931,193` bytes 和 SHA-256 `f3a7cd934e8cc523b6053298d0abb2c82fd7db2b83f9f2ccba5944545aaa4eb1` 均与数据源 LFS 元数据一致。候选 `python__mypy-15413` 存在，repo/base commit/公开题面字段可解析；隐藏字段只统计了字段名和长度，没有写入 Agent 目录。
- 镜像：不带代理的 `docker manifest inspect` 因 Docker Hub header 超时退出 1；只给重试进程设置 `HTTP_PROXY/HTTPS_PROXY=http://127.0.0.1:7890` 后退出 0。固定 manifest digest 为 `sha256:f069dfc74592d438ad870bbc6dfb369bff1b125d21237ead49190b414f5f3456`，Linux/amd64，13 个压缩层共 `1,075,118,139` bytes；镜像尚未拉取。
- 当前网络：Windows `ProxyEnable=0`、`ProxyServer` 为空，FlClash/FlClashCore/Helper 进程运行。本轮没有开启系统代理或修改 VPN，只在具体网络命令的进程环境中使用 7890。
- 环境引导：已在忽略路径 `runtime/tools/uv-bootstrap` 创建 Python 3.13 虚拟环境，并安装 `uv 0.12.10`。
- 失败记录：首次执行 Harbor `uv sync --locked --extra huggingface --no-dev` 失败；`uv` 默认把临时文件从 E 盘移动到 C 盘缓存，Windows 返回跨盘移动错误 `os error 17`。未产生可用 Harbor 环境；下一次重试将显式把 `UV_CACHE_DIR` 固定到项目忽略的 E 盘缓存，不降低锁文件要求。
- 失败记录：第二次同步已成功解析锁文件、创建 `framework/harbor/.venv` 并下载主要 wheels，但 `litellm==1.93.0` 在固定锁文件中没有 Windows wheel，转为源码构建；构建器自动下载 Rust 时又在其默认缓存触发 `WinError 17`，同步以退出码 1 结束。已核实 Visual Studio 2022 Community 含 C++ 构建组件；修复路径是在项目忽略目录安装隔离 Rust 工具链，再从同一 E 盘缓存续装，而不是更改锁定依赖。
- 环境结果：已从 Rust 官方地址下载 `rustup-init.exe`，本地 SHA-256 `6f4bef66261261fcb43131be8720bab817d403a09edec7455c371974b90bdb7e` 与官方校验内容一致；以 `--no-modify-path --profile minimal` 安装到忽略的项目目录，得到 `rustc 1.98.1` / `cargo 1.98.1`。首次 Rust 直连安装长时间无进展后人工中止；仅给重试进程注入 `127.0.0.1:7890` 后安装成功，未改变 Windows 系统代理。
- Harbor 安装：在 Visual Studio 2022 C++ 开发环境中再次执行完全相同的 `uv sync --locked --extra huggingface --no-dev`，`litellm==1.93.0` 源码构建实际耗时 275 分 06 秒，随后成功安装 Harbor `0.22.0` 和 101 个锁定运行依赖。固定锁文件未修改。
- Harbor CLI：`framework/harbor/.venv/Scripts/harbor.exe --version` 退出 0 并返回 `0.22.0`；`--help` 与 `run --help` 可解析。源码确认关闭 verifier 时不要求 `tests/test.sh`，collect hook 仍在 Agent 之后、环境销毁之前运行。
- 源码探针偏差：读取不存在的 `adapters/swegym/pyproject.toml` 失败，证明该 Adapter 不是独立包；一次把真实 `template/task.toml` 误写成 `templates/task.toml` 的读取也失败，随后用 `rg --files` 找到正确路径并完成核验。未修改 Harbor 上游源码。
- 未执行：没有创建项目包或测试；没有拉取首题镜像；没有建立固定 Fork Python 环境；没有运行 gold/空/错误 patch；没有读取凭据内容或调用真实模型；没有 Harbor Trial、patch、轨迹、资源或清理结果。因此 M0 和 MVP 均不得标记完成。
- 交接验证：主仓库 `git diff --check` 退出 0；两份交接文档的代码围栏数分别为 10 和 4，均为偶数；本轮新增/修改 Markdown 的相对链接逐项解析后均存在；常见 API key、Bearer token 与 JWT 模式扫描无命中。Git 显示的 LF→CRLF 提示符合当前 Windows working copy 行尾设置，不是空白错误。
- 提交失败记录：默认沙箱首次执行精确 `git add` 时无法创建 `.git/index.lock`，返回 `Permission denied`；两个目标文件仍保持未暂存，未留下锁文件或部分暂存。将按用户明确授权在提升权限下重试同一精确文件列表，不扩大提交范围。
- 提交前复核：提升权限重试后只暂存 `HANDOFF.md` 与本行动记录；`git diff --cached --check` 退出 0，name-status 为 `M HANDOFF.md` 与 `A 本行动记录`，统计为 2 files / 250 insertions / 58 deletions。将创建一个本地交接提交且不 push；提交哈希由任务最终回复和下一窗口 `git log -1` 提供。
