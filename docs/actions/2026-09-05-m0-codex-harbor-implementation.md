# M0 Codex → Harbor → SWE-Bench-Fork 实现行动记录

## 状态与情况说明

- 本轮本地检查点：本记录随 `feat: checkpoint M0 networking and Codex safety groundwork` 保存，包含自 `6e66125` 以来的网络接线、固定安装输入、安全兼容代码/测试及同步文档；具体提交哈希用 Git 日志核对，不在提交自身写入循环引用。已知远端仍为 `42484d8`，本轮不 fetch、不 push；首轮配置和无凭据安装已通过，真实运行仍待验收。

- 状态：进行中；M0 未完成。最新完成固定 Harbor 启动兼容实现的方法契约与生成权限的独立容器验证；凭据解析刻意关闭，兼容类尚未注册到生产 Job。此前已知值日志小修保留；完整 Trial、原生输出/刷新值、网络与真实账号验收仍未通过，入口保持关闭，不自行 push。
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
- 初始动态事实（历史）：本机 Python 为 `3.13.2`；Codex CLI 为 `0.153.0`，不同于旧文档探针的 `0.142.0`，当时尚未选作项目固定版本；Docker Desktop `4.38.0` / Engine `27.5.1` 可响应；E 盘开始时可用 `22,829,572,096` bytes；三个框架源码已恢复到权威文档固定提交。Codex 首轮版本现已由用户确认，最新状态见末节与依赖总表。
- 恢复动态事实：2026-09-06 提升权限只读探针确认 Docker Client/Server 均为 `27.5.1`，Docker 可见内存为 `10,429,505,536` bytes；E 盘可用空间降至 `19,709,878,272` bytes。默认沙箱访问 Docker named pipe 被拒绝，仅是权限边界，不是 Engine 停止。
- 数据事实：`SWE-Gym/SWE-Gym-Lite` 当前仅有 `train` split，共 230 条；本轮固定读取不可变 revision `61231f2c90b18985b42a1419738a240085a15107`。Parquet 已保存到忽略的运行时缓存，大小 `931,193` bytes，SHA-256 为 `f3a7cd934e8cc523b6053298d0abb2c82fd7db2b83f9f2ccba5944545aaa4eb1`。
- Harbor 源码事实：固定提交要求 Python `>=3.12`，仓库 `.python-version` 为 `3.13`，项目版本为 `0.22.0`；固定提交已经内置 `adapters/swegym`、Codex Adapter 与 `[[verifier.collect]]`。单步 Trial 的顺序是 Agent、日志同步、collect hook、artifact 收集、可选 verifier；因此全局关闭 verifier 时 collect/artifact 仍执行。
- 复用边界：内置 SWE-Gym Adapter 会用未指定 `revision` 的 `load_dataset()` 读取远端最新数据，并把含 `gold_patch`、`test_patch`、`FAIL_TO_PASS`、`PASS_TO_PASS` 的原始 datum 写入任务 `tests/config.json`。M0 将复用其镜像命名和 Harbor 任务约定，但保留项目既有规划中的薄 `adapters/tasks/swe_gym.py`，直接读取已校验的固定 Parquet，只生成 Agent 必需的公开任务文件；隐藏字段只交给独立 Evaluator。
- OpenAI 官方事实复核：Codex 当前仍支持 ChatGPT 登录和 API Key 登录；`codex exec` 是非交互入口，支持 `--ephemeral`、`--json` 和显式 sandbox；文件型缓存含访问令牌，必须按密码处理。项目仍采用已经确认的评测机所有者 ChatGPT 登录政策，不改为 API Key。
- 已确认的超时事实：真实 Harbor 外层超时会绕过上游正常清理；修复前探针留下 1 个 Compose 容器、1 个网络和 1 个本地镜像。生产 Adapter 现按本 Job 落盘 Trial 身份推导精确 project label，清理并复核容器、网络、卷和本地镜像；日志采集使用总期限，Windows 对仍阻塞的同步读执行定向取消，无法完整收束时返回 `HARBOR_LOG_CAPTURE_INCOMPLETE`，不再无限等待。
- 已知未知：账号对已选模型/推理强度的实际可用性、所需端点、Token 刷新、日志脱敏和异常路径清理；固定 Fork 已通过的单题以外的适配范围；真实单题的资源峰值与清理结果。首轮 CLI/模型/推理强度选择已确认，见依赖总表。
- 安全红线：不读取、显示、复制或提交 `auth.json` 内容、Token、Cookie 或 API Key；不把秘密路径写入业务输入或证据；不把 Agent 可见输入与 gold patch、`test_patch`、`FAIL_TO_PASS`、`PASS_TO_PASS` 混合；不把 Mock、Harbor reward 或 Agent 自述写成真实判卷结果。
- 明确排除：本行动不实现 Next.js、FastAPI HTTP、PostgreSQL、MinIO、应用登录、Owner Approval、Judge、排行榜、Tailscale 或 P2 自研 Agent；不提前创建 M1 空壳。

## 实施措施

2026-09-07 用户要求“本地提交之后解释下一阶段和距离 MVP 的差距”：本轮仅建立本地检查点并汇报，不继续实现、不 push、不 fetch、不使用真实凭据或模型。先复核当前 35 个项目变更（前述各轮代码/测试/权威文档），只暂存该精确清单；runtime 证据、安装缓存和 framework 保持忽略。

本轮新增编辑仅为以下两份文档，其余 33 个文件仅复核并随检查点提交，完整职责树沿用本记录已有实际文件树，不增加设计模式参与者：

```text
docs/actions/2026-09-05-m0-codex-harbor-implementation.md # 记录提交范围、复核结果和 M0 尚未完成的边界
HANDOFF.md # 同步检查点定位方式，避免将已提交代码继续描述为未提交
```

自验证方式：重新运行默认 pytest/Ruff/mypy，检查暂存文件名、常见秘密形态（只报告文件名，不输出匹配内容）、Markdown 链接/围栏与 git diff --cached --check；创建一个本地提交后检查提交摘要、文件数及 git status。成功标准为范围内 35 文件被单个检查点保存、工作区干净、无推送；跳过的 Docker/模型集成不得说成本轮通过。验证状态：预提交检查通过，证据见末节；提交身份及最终工作区状态由 Git 和本轮回执核对。

2026-09-07 用户要求解释已知值日志替换并进入下一阶段：继续假值安全接线，不授权真实凭据/模型调用。本轮将权限配置与固定 Harbor Codex 启动命令衔接；原生硬编码 bypass 会压过配置，不能仅加 TOML 后声称生效。保持 NOP 门禁和上游源码不变，在现有执行适配层内增加固定版本兼容实现，不新增服务、业务 Module、公开 Interface、表或目录。

本轮实际文件树及职责（5 份源码/测试、5 份文档，忽略探针另存）：

```text
apps/backend/src/eval_platform/adapters/execution/codex_policy.py # 新增：纯权限配置与固定命令校验；network.py 负责容器网络，不混入 Codex 本地权限
apps/backend/src/eval_platform/adapters/execution/codex_agent.py # 新增：固定上游 Codex 的窄兼容子类，复用 run 并覆盖配置/启动命令；仅供安全契约使用
apps/backend/tests/test_codex_policy.py # 新增：配置/命令正反契约、篡改拒绝、指令正文保真
apps/backend/tests/codex_guard_probe.py # 新增：固定 Harbor Python 的假 Environment 合约驱动；不执行 codex exec 或访问真实认证
apps/backend/tests/test_codex_guard.py # 新增：调用无模型契约，核验上游 run 的配置/命令/异常清理
docs/actions/2026-09-05-m0-codex-harbor-implementation.md # 计划、偏差、实际验证及未完成项
docs/interfaces/CODEX_AUTHENTICATION.md # 当前安全接线能力的唯一事实源
docs/interfaces/HARBOR_EXECUTION.md # 兼容实现和门禁指针
docs/architecture/ARCHITECTURE.md # 内部文件职责与 Adapter/继承协作关系
HANDOFF.md # 已验证事实和恢复限制
runtime/prototype/ # 忽略的全新禁网 Docker 证据，不覆盖前轮数据
```

执行目录由 6 增为 8 个文件；Harbor 子目录已满 8，兼容实现放在同一 Execution Adapter 的既有父目录，隔离上游 Python 依赖，不将启动策略挤入接近 200 行的进程执行器。设计模式仍为 Adapter，内部窄继承复用固定上游算法，不复制整段 run。若需要更多文件/目录或改变认证架构，应先评估并确认。

自验证标准：纯测试验证只接受冻结启动前缀、无 bypass/旧 sandbox 配置、指令正文完整保留；固定上游实际 run 使用仅记录命令和合成上传文件的假 Environment，正常/异常/注入取消均检查清理，不调用模型。禁网容器复用固定缓存 CLI，使用生产生成的 profile 做题目读写正对照和假凭据读取/写入拒绝；CLI 命令失败不算隔离成功。再跑默认 pytest、Ruff、mypy、文件大小/目录数量、文档链接和 git diff --check。自验证情况：本轮兼容实现与局部验证完成，实际失败/修复和结果见末节；完整 Job/Trial、原生轨迹/制品、刷新 Token 和真实网络仍未通过，不用本轮契约替代。

2026-09-07 用户接受“假钥匙”安全收尾并要求开始：本轮在既有 Execution Backend 内验证读取边界、补有界进程日志的已知秘密脱敏，并用假值检查正常/失败/超时清理。授权不包含真实认证、模型调用、DNS/ICMP 改策变更或替换架构；若固定 CLI/容器不能在现有安全限制下隔离读取，记录实测障碍并交由用户决定，不自动加权限或新增认证服务。

本轮实际文件树（4 份代码/测试、6 份文档；不修改上游，无新 port/表/源代码目录）：

```text
apps/backend/src/eval_platform/adapters/execution/redaction.py # 新增内部流式替换实现，现有日志写入职责不适合继续堆算法；execution 层由 5 增至 6 文件
apps/backend/src/eval_platform/adapters/execution/harbor/process_evidence.py # stdout/stderr 落盘前脱敏；保留上限和收束语义
apps/backend/src/eval_platform/adapters/execution/harbor/process_runner.py # 仅在可信调用边界传递内存假值/已知秘密列表，不写入进程环境或 manifest
apps/backend/tests/test_secret_safety.py # 新增跨进程输出安全契约；tests 根层当前无源文件，现有 unit/contract/integration 均满 8，不增目录、不搬无关测试
docs/actions/2026-09-05-m0-codex-harbor-implementation.md # 本轮措施、实际文件树及验证结果
docs/interfaces/CODEX_AUTHENTICATION.md # 读取/脱敏/清理的当前能力和缺口事实源
docs/interfaces/HARBOR_EXECUTION.md # 执行实现与真实入口门槛引用
docs/architecture/ARCHITECTURE.md # 当前文件树及内部职责
docs/research/2026-09-07-dns-icmp-risk-assessment.md # 保留评估历史证据并指向修复后状态
HANDOFF.md # 恢复入口与后续真实运行门槛
runtime/prototype/ # 忽略的假凭据/CLI 沙箱与清理探针；只用新命名证据，不动历史记录
```

设计模式保持 Adapter：公开 ExecutionBackend 不变，Harbor Adapter 内部进程执行器组合流式脱敏函数，不新增业务 Interface。先完成能暴露分块边界和异常日志泄露的失败测试，再实现并跑完整默认 pytest/Ruff/mypy；已知缺陷上轮已用假值定位，`diagnosing-bugs` 不重复既有多假设取证，只保留红→绿回归。流式输出在持久化前替换已知完整值，不能把已知值替换宣传成识别未知刷新 Token 或对抗任意编码泄露。

容器验证成功标准：固定摘要、`--pull=never`、禁网、去全部 capability、不提权、无真实秘密/宿主凭据挂载、资源限额，记录同用户读取正对照和固定 Codex 沙箱的读取结果；命令自身启动失败与真正拒绝读文件分开。仅按本次唯一标签清理并复核。检查失败/超时也不得把假值写入可交付日志。Docker 默认读取被沙箱拒绝时仅申请本任务所需执行权限，不调整 ACL、重启服务或放开容器安全配置。自验证情况：本轮局部检查与小修完成，实际结果和未完成项见末节。

2026-09-07 用户要求“去做风险评估”：本轮仅评估 DNS/ICMP 与凭据边界，形成来源可追溯的报告；不实施网络修复、不打开真实入口、不读取真实秘密。使用 `research` 核对协议资料，使用 OpenAI Docs 核对产品安全边界，使用 `writing-for-agents` 修正恢复入口中把“开放通道”直接当成“已证实外泄/必须全面封禁”的推断。评估建议不是用户已经批准的新架构或风险豁免。

本轮实际文件树（现有目录内 6 份文档，运行代码/上游源码均不改；无新增设计模式参与者）：

```text
docs/actions/2026-09-05-m0-codex-harbor-implementation.md # 本轮措施、文件树和实际验证记录
docs/research/2026-09-07-dns-icmp-risk-assessment.md # 新增：证据分级、威胁前提、风险与优先级建议的单一报告
docs/interfaces/HARBOR_EXECUTION.md # 网络实测事实及限制；更正超出证据的结论，链接评估
docs/interfaces/CODEX_AUTHENTICATION.md # 凭据路径的固定源码事实及仍待实测的边界
docs/architecture/ARCHITECTURE.md # 更正旧代理状态，链接网络/凭据事实，不新增架构决定
HANDOFF.md # 恢复入口引用评估，区分已确认政策、技术未知与待用户裁决建议
```

自验证方式与成功标准：确认固定 Harbor HEAD/工作树；只读取既有无秘密网络探针的摘要/清理证据；核对实际 `run()`、网络规则和日志/收集实现；重跑现有无模型网络契约测试（真实入口拒绝、宿主环境过滤、配置防篡改），不把这些契约当真实外泄测试。所有报告关键结论标注源码/实测/推断及未验证前提；检查 6 份文档的链接、围栏、旧结论残留与 `git diff --check`。不访问校园网其他机器、不部署公网收集端、不改变防火墙/代理/Docker/WSL，不提交或 push。实际测试已完成，文档收尾检查与最终结果见末节。

评估中追加的无模型验证：固定上游 `_scrub_jobs_dir()` 按敏感环境变量值做替换，不能仅凭名字推断它能清除文件内 Token。使用忽略的 `runtime/prototype/dns-icmp-risk-probe.py` 调用真实脱敏方法，全部输入为自行生成的假值；对照“环境变量值能脱敏”与“仅通过文件路径提供的假 Token 是否残留”，并调用项目日志持久化函数验证其是否做内容脱敏。结果保留于 `runtime/prototype/dns-icmp-risk-20260907/`；这是测试夹具，不是模型 Trial、安全修复或正式网络回归，不接触真实认证文件。脚本仅执行只读 Git 身份校验，不启动 Docker/模型进程，不清理历史证据。

2026-09-07 用户要求开始安装、网络隔离和凭据安全验证。本轮完成固定 Codex 无凭据容器安装：公开 npm 元数据核对官方版本与 Linux x64 包；固定校验值、带超时下载及安全解包，在现有 Execution Adapter 内部准备离线安装输入，用固定任务摘要镜像验证 CLI 版本/帮助及 Harbor 预装复用。不读取登录文件、不执行模型任务、不放开真实入口；不升级宿主 CLI、不修改上游、代理或 Docker/WSL 全局设置。原有模块缺少制品校验职责，因此新增内部 `codex_install.py`，不新增业务 Module、port 或目录；安装契约及辅助驱动放入原有 contract 目录，现恰好 8 文件。旧代理说明已按代码修正。网络追加取证复现开放通道，完整网络与凭据验收未通过；不能用安装成功覆盖安全缺口。

本轮实际文件树与职责（10 个项目文件均在既有目录；采用离线安装输入加临时容器内复制，不构建或替换任务基础镜像）：

```text
apps/backend/src/eval_platform/adapters/execution/codex_install.py # 新增：固定制品校验、安全解包、离线安装输入，Execution Adapter 内部实现
apps/backend/tests/contract/test_codex_installation.py # 新增：包损坏/危险成员拒绝；显式开关的无凭据 Docker/Harbor 安装契约
apps/backend/tests/contract/codex_install_probe.py # 新增：固定 Harbor Python 驱动真实禁网容器，命令白名单与精确清理；测试辅助实现
docs/actions/2026-09-05-m0-codex-harbor-implementation.md # 范围、失败、实测和剩余门槛
docs/dependencies/DEPENDENCIES.md # 安装包精确身份/校验值与缓存指针
docs/interfaces/FRAMEWORK_INTERFACES.md # 实际预装复用证据与范围
docs/interfaces/HARBOR_EXECUTION.md # 安装已验证与网络/凭据仍未验证的边界
docs/architecture/ARCHITECTURE.md # 内部实现文件职责与下一步
docs/operations/LOCAL_DOCKER_ENVIRONMENT.md # 纠正旧代理说明；资源前后核对
HANDOFF.md # 恢复入口按真实结果更新
runtime/prototype/ # 忽略的逐次证据；安装包、解包 hash、三轮网络诊断脚本/结果，不含真实凭据
```

安装契约已先通过（7 passed，包含真实禁网容器；默认全套 128 passed / 15 skipped）。随后在新的忽略证据目录补一次网络边界诊断脚本：复用现有四容器夹具和固定原生侧车，在两个受控 HTTP 服务旁启动自签测试 TLS 服务，验证 public 正对照、allowlist 和 SNI 伪装；再比较 no-network 下 DNS 与 ICMP ping socket 能力。只使用合成标记与本次受控容器，不发送真实凭据或模型请求，不修改上游策略/源码。自签证书只用于测试路由，不称为真实 HTTPS 证书校验通过。结果记录实际允许/阻断，不把发现开放通道写成安全通过；若发现边界未满足则继续保持真实入口关闭。临时脚本属于诊断证据，不宣称已成为生产隔离实现或永久回归测试。

网络追加探针首轮 `m0-network-extra-20260907-01` 在导入测试夹具时失败：固定 Harbor 隔离环境没有 pytest，尚未创建容器。保留原失败日志；第二轮改为由项目测试环境生成夹具 JSON，固定 Harbor 进程只读该输入，不为一次诊断向上游环境安装 pytest，也不覆盖首轮证据。

验证先定义：损坏 hash、错误平台包/危险路径必须拒绝且不产生可执行安装输入；Docker 使用无凭据、禁网、去能力、限制资源的固定基础镜像，仅版本/帮助探针，不调用模型；Harbor 同版本复用不得执行联网安装或认证 setup；逐个精确清理本次容器并保留证据。默认 pytest、Ruff、strict mypy 和显式安装契约已运行，结果见末节；收尾检查覆盖源码 200 行/每层 8 文件、文档链接/围栏及 `git diff --check`。前检默认沙箱 Docker/公网 socket 被拒绝，提权重试成功；首次 rg 包含不存在的 scripts 目录及两次旧路径读取报错，后续按实际目录查询，未将失败视为通过。Docker 前检 18 个容器、0 个运行、25 个镜像，E 盘可用约 19.1 GB；固定 Harbor HEAD 与干净工作树已复核。

2026-09-07 用户以“yes”确认首轮推理强度采用中等档，另说明 Dify 是其为释放内存主动关闭。本轮只同步下面当前增量文件树中的 7 份既有文档：依赖总表登记 effort 唯一值；架构/接口/Handoff 移除重复确认步骤并保留真实可用性门槛；运维文档区分先前查询结果与用户补充原因。本行动记录范围和结果，无新增文件/目录、源码或测试修改。既有 `critical_config.reasoning_effort` 能承载已选值，无需新接口。验证：7 份文档围栏/相对文件链接、当前失效待办检索、`git diff --check`；成功标准是三项配置决定一致且未误标真实运行通过。自验证已完成，结果见末节“首轮推理强度确认”。此前各步记录保留历史语义。

2026-09-07 用户确认首轮模型 `gpt-5.6-terra`，并询问 Docker 中的 Dify 是否为本项目。本轮将确认落入依赖事实源，其他活动文档改为引用已确认 CLI/模型、只保留推理强度及真实运行门槛待办。Docker/进程调查只读，不启动、停止或删除服务；不把 Dify 的停止状态推断为本助手操作或已查明原因。

本轮实际文件与职责：本行动（确认、检查方法与结果）；`docs/dependencies/DEPENDENCIES.md`（首轮模型 ID 唯一值）；`HANDOFF.md`（恢复待办）；`docs/architecture/ARCHITECTURE.md`（技术队列）；`docs/interfaces/FRAMEWORK_INTERFACES.md`、`docs/interfaces/HARBOR_EXECUTION.md`（配置确认与实际可用性边界）；`docs/operations/LOCAL_DOCKER_ENVIRONMENT.md`（带时间的只读容器状态）。无源码/测试变更、新增文件或架构元素。成功标准：7 份文档无相互矛盾的当前待选状态、相对链接/围栏/差异检查通过；只报告 Docker/进程查询实际结果，权限失败不得记为通过，沿用测试证据必须标注非本次重跑。实际结果见末节“首轮模型确认与运行状态核对”。

2026-09-07 用户明确同意首轮 Codex CLI 固定为 `0.153.0`。本次先同步该依赖决定，并核对固定 Harbor 的预装版本判定；模型与 reasoning effort 仍待分别确认，不把版本确认视为凭据使用或模型调用授权。不改变生产入口/port，不安装容器软件、不升级宿主、不提交或 push。使用 `action-document` 留下措施和验证结果，`openai-docs` 核对官方安装与模型资料；Handoff 按 `writing-for-agents` 区分已确认和待确认项。

本次修改文件及职责：本行动记录（确认范围、源码核验、实际验证）；`docs/dependencies/DEPENDENCIES.md`（唯一版本事实源）；`docs/interfaces/FRAMEWORK_INTERFACES.md`（Harbor 预装判定与版本引用）；`docs/interfaces/HARBOR_EXECUTION.md`（M0 门槛引用）；`docs/architecture/ARCHITECTURE.md`（技术核验队列）；`HANDOFF.md`（恢复时不再重复询问版本）。没有新增文件/目录，也不改变已有 Adapter 关系。验证方式：宿主 `codex --version`、固定上游版本匹配/不匹配/命令失败的无容器检查、六份文档的差异/围栏/相对链接和当前失效描述检索；不把这类检查写成容器安装通过。本步已验证，结果见末节“Codex 首轮 CLI 版本确认”。

2026-09-07 检查点 `6e66125 test: verify Harbor network policies and WSL preflight` 已创建，12 个文件，提交后干净；相对已知远端 ahead 10，未 push。接下来只做生产网络配置接线，真实入口保持关闭。复用已有 Task TOML 的环境基线、Job `environment.extra_allowed_hosts`、任务 Compose 和 CLI；显式设置空 allowlist，主容器去全部能力/禁止提权，CPU/内存来自既有 RunLimits，PID 先复用已实测的 M0 探针 64 上限，真实 Codex 资源模板另行实测。宿主白名单只放进本机 Adapter 的可信构造配置，并冻结到每次 Harbor config，不增加公开 Job 输入或业务 port。

本步文件树与职责：`adapters/execution/network.py` 新增为既有 Execution Backend 的内部实现，负责精确主机名验证、Compose 安全模板、固定 Git blob 导出；`adapters/execution/harbor_entry.py` 新增为同一后端的内部 CLI 引导，只在固定 Harbor Python 中校验源码身份、设置构建上下文并调用原 CLI，同时过滤宿主环境并拒绝真实 Agent。现有 `harbor/` 目录已满 8 文件，故这两项放在已有父目录（原 2 文件，新增后 4），不建目录/业务 Module/Interface。修改 `harbor/adapter.py`（Adapter 委托引导）、`harbor/config_mapper.py`（冻结白名单）、`tasks/swe_gym.py`（Task/Compose 生成）。新增现有 contract 目录中的 `test_execution_network.py`，调整现有 unit/contract/integration 测试复用生产模板与导出，不另添 integration 文件；每文件保持 200 行以内。

验证标准：先测试精确主机名拒绝 URL/通配/IP/宿主别名、空白名单与受控列表的 Harbor 实际阶段解析、环境变量不继承秘密、源码版本/脏工作树拒绝和不可覆盖；再跑既有无凭据真实网络探针（使用生产模板）、生产 Adapter→NOP→Fork 串联及强杀后的精确 Compose 清理。默认全套/格式/lint/strict mypy、上游固定身份和文档必须同步通过。真实模型端点、DNS/ICMP、IPv6、长连接和其他故障仍是单独验收缺口，不因本次接线写成已完成；本步实际通过项、首次失败与修复见末节“网络配置接线与本地检查点”。

2026-09-07 用户要求“本地提交之后继续下一步”：先把现有内核预检、无凭据网络探针和同步文档建立本地检查点，再深化既有 Execution Adapter 的网络配置接线；不 push，不把该请求当成 Codex 版本/模型选择或真实凭据使用的确认。提交前复核：Ruff 格式 49 文件、lint、strict mypy 28 文件均通过；默认全套为 93 passed / 14 skipped（7.10 s），真实网络结果沿用末节证据而非声称本次重跑。

以下措施按历史阶段保留；其中“尚未接入/待执行”等描述是当时状态，不替代上方当前状态和末节验证结果。

2026-09-07 网络首测准备阶段失败：侧车退出 127，全部 project 资源已清理。禁网最小启动复现显示脚本首行末尾为 `0d 0a`，报 `/opt/egress-sidecar/entrypoint.sh: not found`，而 nft/gost 均存在；原因是 Windows CRLF 检出进入了 Linux 镜像。测试将从已固定 Git revision 导出侧车的五个原始 blob 到本次证据目录，仅替换测试进程的构建上下文路径，再走原生内容哈希构建。不上游补丁、不改规则、不改全局 Git 设置；此兼容处理当时只用于测试，后续生产接线结果见末节。保留首轮失败证据并使用新目录重跑。

2026-09-07 用户要求开始下一步：本次先验证固定 Harbor 原生网络策略，不读取凭据、不调用模型、不新增业务模块或 port。复用已有 `DockerEnvironment` 与项目固定任务镜像，使用同一临时 Compose project 下两个受控 HTTP 目标作为允许/禁止正反对照，验证策略切换、主容器去能力、绕过宿主代理和伪造目标信息等路径；无法建立正对照的外网检查必须标记未验证，不能按拒绝通过。新测试 `tests/integration/test_harbor_network.py` 管显式开关、外层期限、证据和精确 project 清理；同目录 `network_probe.py` 在固定 Harbor 虚拟环境内操作真实 Environment。既有 integration 目录 6 个文件，新增后为 8；每文件不超过 200 行，不新增目录。预期按需拉取固定 Harbor 引用的两个摘要镜像、构建其内容哈希命名的原生侧车，保留共享缓存，不升级上游或宿主。成功标准：受控允许路径可达、禁止及绕过路径有可信阻断证据、全部测试资源精确清理；任何漏洞先记录复现，不把原生 API 存在当作安全验收通过。同步实际接口、依赖/环境事实、Handoff 和本记录；计划验证为默认快速全套、格式/lint、显式真实网络探针。受控 HTTP/IPv4 场景现已通过；早期准备失败、证据强化及未验收边界见本记录末节，生产接线仍待完成。

2026-09-06 用户已明确同意更新 WSL，并在需要时重启 WSL/Docker 后继续验证。本次只更新 WSL，不升级 Docker/Harbor/Python/模型配置，不改代理、防火墙或数据位置。先记录发行版、运行容器和资源身份；调用官方 `wsl --update`，仅在默认渠道失败时考虑官方 `--web-download`；更新成功后按需正常停止 Docker、关闭 WSL、重启 Docker。复测 `--check-network`，核对原容器/网络/卷/镜像和固定 Fork 可用性；内核前提通过仍不代表白名单流量或 Codex 验收通过。同步本行动、Docker 事实、Handoff 与引用当前阻塞的权威文档；不创建新业务代码或接口。成功标准：新内核实际生效，现有资源保留、Docker 恢复，网络前提结果和失败如实落盘。当前验证结果待执行；不自动重启整台 Windows。

本次继续的网络预检措施：只读固定 Harbor 发现其白名单依赖 `CONFIG_NFT_FIB_INET`；固定任务镜像的禁网内核探针确认当前 `5.15.167.4-microsoft-standard-WSL2` 缺少该能力。在既有 `adapters/execution` 目录新增 `preflight.py` 执行侧内部预检实现（不是新顶层业务 Module 或 port），由既有 M0 脚本 `--check-network` 调用。预检只运行固定摘要、禁止拉取、禁网、低资源、无挂载、无能力的一次性容器，记录内核事实与精确标签清理；不支持/未知/清理失败返回非零，不能默认为开放网络。`tests/contract/test_network_preflight.py` 验证支持、缺失、未知、启动失败、超时、清理失败和不覆盖证据；实际命令再验证本机限制。M0 入口只增加委托，不超过 200 行。禁止自动更新 WSL/重启 Docker/修改宿主防火墙；若需要此类全局变更先请求用户授权。没有新网络业务模块、数据库表或生产端点白名单。

本次文件职责与验证计划：`preflight.py` 是现有 Execution Adapter 的内部就绪探针；`prototype_codex_harbor_e2e.py` 仍为 Composition Root；`test_network_preflight.py` 只用假 Docker 子进程做契约验证。同步 Handoff、执行接口、框架接口、总架构规划树和本机 Docker 事实。成功标准是能够区分“内核前提满足”与“真实网络防绕过通过”，本机不支持时如实返回明确阻断码并清理探针容器；不把拒绝运行测试通过写成网络已通过。

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

本次实际进度：Harbor 执行/patch/有界日志/超时清理已实测；固定 Fork 的独立 Linux 环境、63 包哈希锁、Evaluator Adapter 与五类补丁判卷已实测。M0 脚本已串接既有 ports，含原型标记、配置冻结、执行身份/patch 内容复核、分阶段证据与基础设施错误不伪装 unresolved；当前只供内部测试/NOP，CLI 开放互斥的 `--check` 与 `--check-network`，后者只检查内核前提。真实串联曾暴露 Windows 长路径报告读取失败，已用秒级单测定位和修复，最终回归见本记录末尾。真实 Codex、网络/凭据/轨迹验收仍未完成，M0/MVP 均未完成。

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

当前未提交集合由上方“本轮实际文件树”与下方“`6e66125` 后的网络配置接线”共同组成；配置确认记录只说明此前文档步骤，不覆盖新增安装代码。当前未提交总计 24 个项目文件（含 6 个新文件），无删除；忽略的逐轮诊断/安装证据另行保留。

### 已完成的历史增量：首轮配置确认与运行状态核对（仅文档）

```text
E:\9.1agent_exam\
├─ HANDOFF.md # 已确认首轮三项配置的指针，恢复时直接进入技术核验
└─ docs/
   ├─ actions/2026-09-05-m0-codex-harbor-implementation.md # 本次范围与真实验证
   ├─ dependencies/DEPENDENCIES.md # 首轮 CLI/模型/推理强度唯一事实源，实际可用性待验证
   ├─ architecture/ARCHITECTURE.md # 核验队列不再列首轮三项配置待选
   ├─ operations/LOCAL_DOCKER_ENVIRONMENT.md # 保留运行快照并补充用户主动关闭 Dify 的说明
   └─ interfaces/
      ├─ FRAMEWORK_INTERFACES.md # 预装版本判定的源码/契约事实
      └─ HARBOR_EXECUTION.md # M0 已确认配置与待验收门槛
```

上述配置确认步骤当时未改源码/测试；以下网络接线改动完整保留，新增安装实现以本轮实际文件树为准。

### 当前：`6e66125` 后的网络配置接线

```text
E:\9.1agent_exam\
├─ apps/backend/
│  ├─ src/eval_platform/adapters/
│  │  ├─ execution/
│  │  │  ├─ network.py              # 新增：精确主机名、Compose 模板与固定 Git blob 导出
│  │  │  ├─ harbor_entry.py         # 新增：固定 Python/源码引导、环境过滤与真实 Agent 门禁
│  │  │  └─ harbor/
│  │  │     ├─ adapter.py           # Adapter：沿用 ExecutionBackend，委托内部引导
│  │  │     └─ config_mapper.py     # 冻结可信本机白名单到上游 JobConfig
│  │  └─ tasks/swe_gym.py           # Task Adapter：公开 Task 和受限 Compose 生成
│  └─ tests/
│     ├─ contract/
│     │  ├─ test_execution_network.py # 新增：配置拒绝、源码身份/不可覆盖及真实导入回归
│     │  └─ test_harbor_contract.py # 固定上游实际阶段网络解析契约
│     ├─ unit/
│     │  ├─ test_harbor_adapter.py  # 引导命令/解释器及既有 Adapter 行为
│     │  └─ test_task_adapter.py    # 公开 Task 文件树增加受限 Compose
│     └─ integration/
│        ├─ test_harbor_network.py  # 复用生产模板和导出，保留真实对照/清理
│        ├─ test_harbor_nop.py      # 正常无模型 Trial 经过生产引导
│        ├─ test_harbor_timeout_cleanup.py # 接线后的超时资源回归
│        └─ test_m0_pipeline_integration.py # 接线后的 NOP→patch→Fork 回归
├─ HANDOFF.md                       # 更新检查点、恢复入口及已验证/未验证边界
└─ docs/
   ├─ actions/2026-09-05-m0-codex-harbor-implementation.md # 本步计划、偏差与证据
   ├─ architecture/ARCHITECTURE.md  # 内部文件职责及下一步核验队列
   ├─ architecture/MODULE_CONTRACTS.md # 既有 Backend 的接线状态指针，不改 port
   ├─ dependencies/DEPENDENCIES.md  # 固定 blob 构建已被生产引导复用
   ├─ interfaces/HARBOR_EXECUTION.md # 配置流、真实挂载及网络验收边界的事实源
   ├─ interfaces/FRAMEWORK_INTERFACES.md # 当前接口进展指针
   └─ operations/LOCAL_DOCKER_ENVIRONMENT.md # 实测后资源及未改宿主的事实
```

Adapter 模式关系不变：应用只依赖 `ExecutionBackend`，`HarborExecutionAdapter` 为实现；本步两个内部文件由该实现调用，不暴露为新 port。Task Adapter 输出配置，由固定上游实际模型解析。未新增目录、业务 Module、Interface 或数据库表。

### 历史：`f0a1a4a` 后、现已包含在 `6e66125` 的改动

当时授权的 WSL 更新复用下列文档；忽略的 `runtime/prototype/wsl-update-20260906/` 已保存更新前后的非秘密快照 `before.json` / `after.json`，包含资源身份逐项对比。下面网络预检/测试不再是当前未提交文件清单：

```text
E:\9.1agent_exam\
├─ apps/backend/
│  ├─ prototype_codex_harbor_e2e.py  # 修改：Composition Root 委托互斥的两种预检
│  ├─ src/eval_platform/adapters/execution/preflight.py
│  │  # 新增：既有 Execution Adapter 内部探针，非新业务模块/port
│  └─ tests/
│     ├─ contract/test_network_preflight.py # 新增：14 项假子进程内核预检契约
│     └─ integration/
│        ├─ test_harbor_network.py # 新增：真实网络测试入口、固定源码导出与精确资源清理
│        └─ network_probe.py       # 新增：固定 Harbor Environment 的受控对照/绕过驱动
├─ HANDOFF.md                       # 修改：检查点、当前阻塞、恢复提示词
└─ docs/
   ├─ actions/2026-09-05-m0-codex-harbor-implementation.md
   │  # 修改：本行动的范围、措施、实际命令和结果
   ├─ architecture/ARCHITECTURE.md   # 修改：内部文件规划与实施优先级
   ├─ dependencies/DEPENDENCIES.md  # 修改：固定网络镜像与原始 Git blob 构建事实
   ├─ interfaces/HARBOR_EXECUTION.md # 修改：固定源码能力与预检/验收区别
   ├─ interfaces/FRAMEWORK_INTERFACES.md # 修改：M0 CLI 就绪检查语义
   └─ operations/LOCAL_DOCKER_ENVIRONMENT.md # 修改：唯一内核事实与环境变更边界
```

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
- 当时下一任务：确认 Codex CLI/模型/effort 并核验网络能力。其后用户要求先提交再继续，检查点与新增网络预检结果见下一节；此处是编排完成时的历史状态，不代表最新 Git 或预检状态。

## 2026-09-06 检查点后的网络预检续记

- 按用户要求先创建本地提交 `f0a1a4a feat: add verified Fork evaluator and M0 pipeline`，24 个文件；提交后工作区干净，ahead 9 / behind 0（对已知 origin/main）。提交前格式/lint/strict mypy 通过，快速全套 `79 passed, 13 skipped in 6.99s`，暂存 diff 检查通过。未 push；提交后本节列出的预检与文档仍在工作区。
- 在现有 Execution Adapter 内部增加预检，不新增顶层业务 Module、port 或目录。固定 Harbor 的原生白名单依赖 `CONFIG_NFT_FIB_INET`；先用已有固定摘要镜像、禁网且无凭据的手动探针发现缺失，再实现可重复 CLI。源码能力拒绝路径已经核对，但没有运行 Harbor 白名单 Trial，也未拉取其网络侧车。
- `action-document` 要求先记录范围和成功标准，故继续同一行动记录；`openai-docs` 用于复核官方认证文档，未改变所有者 ChatGPT 登录政策，未读取秘密或调用模型。网络预检只持久化预期协议字段，不把任意 stderr/异常文本保存为证据；唯一目录禁止覆盖，超时只清理本探针的标签与精确名称。
- 新契约首次 Ruff 检查发现导入排序问题，自动排序后复跑通过。`python -m pytest -q tests/contract/test_network_preflight.py -p no:cacheprovider` 为 **14 passed in 0.16s**，覆盖支持/缺失/未知、协议错误、进程失败、缺失 Docker、超时、清理失败、证据禁止覆盖及两种 CLI 行为。
- 在 `apps/backend` 使用 `.venv/Scripts`：`ruff format --check src tests prototype_codex_harbor_e2e.py` 为 **47 files already formatted**；`ruff check` 同路径通过；`mypy src prototype_codex_harbor_e2e.py` 为 **28 source files** 通过；`python -m pytest -q -p no:cacheprovider` 为 **93 passed, 13 skipped in 7.08s**。13 项真实集成默认关闭，不表示本次重新通过。`--check` 仍确认固定任务且 `real_codex_ready=false`。
- 真实 `.venv/Scripts/python.exe prototype_codex_harbor_e2e.py --check-network`：**exit 2 / UNSUPPORTED_KERNEL**，不是网络验收通过。证据为 `runtime/prototype/network-preflight-9f314c10d4d9/network-preflight.json`；清理 verified=true、remaining=[]，未启动模型、未挂载凭据、未拉取镜像。本机内核和资源动态值唯一维护在 [Docker 事实第 3.4 节](../operations/LOCAL_DOCKER_ENVIRONMENT.md#34-harbor-网络前置条件)。
- 下一步建议获得用户明确授权后更新 WSL，并在需要时重启 WSL/Docker，然后复测内核与真实白名单；官方新分支配置包含所需选项，但不能保证本机更新后的效果。本轮没有执行更新、重启或宿主防火墙变更。Codex CLI 固定版本、模型/effort 仍待确认；不得默认选用宿主版本或退回无限制联网，真实入口仍关闭，M1 尚未开始。
- 收尾复核：Ruff 格式 47 文件、lint、strict mypy 28 文件再次通过；默认全套再次为 **93 passed, 13 skipped in 7.05s**。6 份变更 Markdown 围栏成对、相对链接存在；47 个项目 Python 文件均不超过 200 行，每层 Python 文件不超过 8；`git diff --check` 通过。全部变更文件的常见 Key/Bearer/JWT 形态扫描无命中。最终 HEAD 仍是 `f0a1a4a`、ahead 9；新增预检与本次文档未提交，未 push。Git 全局 ignore 读取权限警告和 LF/CRLF 转换提示保留，但上述命令实际退出码均为 0。

## 2026-09-06 已授权 WSL 更新与复测

- 用户随后报告 Docker “WSL distro terminated abruptly”。按 `diagnosing-bugs` 使用既有有界 CLI 做重启前/后对照，不重复安装 WSL 来人为触发中断。原更新会话已 exit 0，MSI 1033/11707 事件确认 2.7.13.0 安装成功，`wsl --version` 报内核组件 6.18.33.2-2；此前尚未手动执行 `wsl --shutdown` 或 Docker 重启。重启前 `--check-network` 确认 Docker run 返回 125、PROBE_PROCESS_FAILED，清理查询同样失败而映射 PROBE_CLEANUP_UNVERIFIED，证据 `runtime/prototype/network-preflight-b950cd08235d`。这只是 daemon 不可用，不能判断 probe 容器实际残留，须恢复后按精确标签再查。
- 当前诊断按可能性区分：安装使 WSL 退出（正常重启可恢复）、Docker 持有旧连接（重启重建连接）、新内核/发行版兼容故障（重启后仍失败）。先正常重启 Docker，不修改配置、不清空/重建发行版；恢复后用相同预检与原资源快照核对。用户报告的弹窗是原症状；系统安装中断无需通过再次安装复现，故不做代码二分或新增单元测试。

- 用户于晚间回复“已点”后恢复原更新会话，没有启动第二个安装器。系统确认进程已消失，安装日志开始增长，正在安装而非仍等待 UAC；先等原安装进程完成，再复核版本并按需重启。后续成功标准仍为原资源逐项保留、新内核实际生效、网络预检与既有无模型串联回归；不升级其他组件，不启动真实模型。

- 用户明确回复“同意”，授权 WSL 更新及必要的 WSL/Docker 重启，不包含整台 Windows 重启、其他组件升级或更改安全策略。更新前工作区仍为 `f0a1a4a` 之后的预检和文档改动；不清理、不提交、不 push。
- 更新前 Docker Engine 为 27.5.1，现有 18 个容器全部处于 exited（运行中 0），Ubuntu 与 docker-desktop 发行版运行中。精确容器 ID、网络 ID/名称、卷名、唯一镜像 ID 已存入忽略的 `runtime/prototype/wsl-update-20260906/before.json`，供更新后逐项比较。
- 已执行官方 `wsl --update`；Windows Installer 事件 1040 确认开始安装微软 WSL 2.7.13.0 x64 MSI，客户端 PID 属于本次更新。不并行启动第二个安装器，不强杀 MSI。当前安装结果与后续复测待返回。只读连接查询在没有匹配 TCP 连接时返回退出码 1，不作为安装失败证据；WSL 输出经 UTF-16 解码后复核旧版本，避免把编码乱码误判成故障。
- 后续只读查明等待原因：`consent.exe` PID 47472，窗口标题“Microsoft 正在请求你的许可”；本次 `wsl --update` 的进程为 40636/51148，终端会话 2655 仍在等待。安装日志文件尚为 0 bytes，不能报安装通过。需要用户亲自在 Windows UAC 中确认，不绕过、不强杀、不重复运行安装器。尚未执行 Docker stop/start、`wsl --shutdown` 或更新后网络/串联测试；之前的 93 passed/13 skipped 属于上一轮，不是本轮更新后回归。
- 已下载 MSI 的 Authenticode 签名状态为 Valid，签名者 Microsoft Corporation。等待系统确认期间已同步本行动、Docker 事实、Handoff 和架构实施队列；6 份变更 Markdown 的围栏/相对链接及 `git diff --check` 通过。本轮没有业务代码改动，没有提交或 push；停止在需要用户点击系统确认的位置，原更新会话不主动终止。

### UAC 确认后的恢复结果

- 原更新会话最终 exit 0，Windows Installer 1033/11707 事件确认安装成功；旧安装日志随后不再存在，读取该临时日志的 `rg` 返回文件不存在（exit 2），改由已取得的安装事件与实际版本确认，不把临时日志缺失当作安装失败。
- 用户报告的弹窗与 Docker 后端日志原文一致：22:56 左右 WSL proxy 退出、main distro terminated、`running wsl-bootstrap: exit status 1`。当时尚未执行手动 shutdown/restart；时间关系支持 WSL 更新中断后端这一判断。使用既有 CLI 建立失败到恢复的对照，不为复现弹窗再次更新系统。
- 按已有授权执行 `docker desktop restart --timeout 90`，exit 0；随后 Desktop running，Docker Engine 仍为 27.5.1，新内核实际生效。没有手动 `wsl --shutdown`，没有重启 Windows、清空/重装发行版或修改代理/防火墙。当前具体内核、内存和资源值只在 [Docker 事实第 3.4 节](../operations/LOCAL_DOCKER_ENVIRONMENT.md#34-harbor-网络前置条件) 维护。
- 原命令 `.venv/Scripts/python.exe prototype_codex_harbor_e2e.py --check-network` 复测 exit 0 / SUPPORTED_KERNEL、kernel_supported=true、cleanup verified=true、remaining=[]；证据 `runtime/prototype/network-preflight-254a062ee2b4/`。全体网络探针 label 查询无输出，包含重启前无法确认清理的 probe；没有改写原失败证据。此次仅证明内核配置前提满足，不是 Harbor 白名单 Trial、模型、凭据或真实 M0 验收。
- 更新后的 format 47 文件、Ruff lint、strict mypy 28 文件均通过；默认 `python -m pytest -q -p no:cacheprovider` 为 **93 passed, 13 skipped in 8.29s**。13 项默认未启用的真实集成不算通过。
- 更新后显式运行 `AGENTEXAM_RUN_M0_INTEGRATION=1` 的 `tests/integration/test_m0_pipeline_integration.py`，全新 `--basetemp=E:\9.1agent_exam\runtime\prototype\m0-wsl-upgrade-20260906-01`，结果 **1 passed in 78.67s**。它实际经过 Harbor NOP、生产 collect、原 patch 字节传递、固定 Fork 干净禁网判卷及精确资源清理；无模型/真实凭据，不能当作 Codex M0 完成。
- `before.json` 与 `after.json` 逐项核对保留原容器/卷/镜像；默认 bridge 网络 ID 随重启变化，其余网络 ID 保留。Docker 原有重启策略自动启动 13 个已有容器；未修改这些策略，也没有额外新建服务。未进行其他应用的业务健康检查。原资源数值由 Docker 事实源维护，本行动保留检查方法与证据位置。
- 收尾：串联测试后四类资源身份与更新后快照逐项一致，Fork 清理 verified=true/remaining=0，Desktop running；Harbor/Fork 上游工作区均干净，更新证据目录确认被 Git 忽略。6 份变更 Markdown 围栏与相对链接、`git diff --check`、常见秘密形态扫描均通过。本轮只更新环境事实与恢复记录，未修改业务代码、未新增提交、未 push。没有临时 DEBUG 插桩；失败证据按审计要求保留在忽略的 runtime/prototype，而非删除。WSL 更新及此次 Docker 中断恢复已完成，下一步是实际白名单/防绕过与 Codex 配置/凭据验证。

## 2026-09-07 无凭据网络探针结果

本步已完成受控 HTTP/IPv4 探针，M0 仍进行中。新增文件是 `tests/integration/test_harbor_network.py`（196 行：固定输入、显式开关、600 秒外层期限、1 MiB 显式日志限额、容器配置及精确清理断言）和 `network_probe.py`（190 行：固定 Harbor Environment 原生策略驱动）。没有新增生产 Module/port/目录；integration 目录恰好 8 个文件。初稿 215 行，按夹具/驱动职责分到这两个文件，未放宽指标。早期导入/长行格式错误已经修正。

使用 `action-document` 先定义范围和成功标准，`diagnosing-bugs` 用最小禁网探针定位启动故障，`writing-for-agents` 将交接入口改为指向实际验收边界。测试曾返回通过，但审查实际退出码后发现代理和停机路径只证明 DNS 失败，因此主动改用 public 阶段取得的 IPv4，再验证相同 IP 的允许/拒绝。最终只接受明确 curl 连接/超时/空响应/CONNECT 失败码；套接字标记必须实际出现 PermissionError，命令不存在或 DNS 失败不能计为阻断。

全部轮次在 `apps/backend` 运行，显式设置 `AGENTEXAM_RUN_NETWORK_INTEGRATION=1`，命令为 `.venv/Scripts/python.exe -m pytest -q tests/integration/test_harbor_network.py -p no:cacheprovider --basetemp=<下表全新目录>`；每次先确认目录不存在，不覆盖旧证据。下表目录均位于 `E:\9.1agent_exam\runtime\prototype\`；内部证据在 `test_fixed_harbor_network_poli0/network/`。

| 目录 | 实际结果 | 原因或覆盖 |
|---|---|---|
| `m0-network-20260907-01` | 1 failed / 8.27 s | 侧车退出 127；禁网启动复现脚本首行 CRLF，nft/gost 命令均存在 |
| `m0-network-20260907-02` | 1 failed / 21.55 s | 原始 Git blob 构建使侧车 healthy；测试 Alpine 没有 httpd applet，改复用任务镜像 Python HTTP 服务 |
| `m0-network-20260907-03` | 1 passed / 40.11 s | 第一版域名测试通过，但代理/停机失败码是 DNS 错误，证据强度不足，不作最终验收 |
| `m0-network-20260907-04` | 1 passed / 40.80 s | 增加已解析 IPv4；两宿主代理 public=0、allowlist=56；停机两目标为 7 |
| `m0-network-20260907-05` | 1 passed / 40.39 s | 最终版 16 项场景全部通过，并断言容器权限/资源配置；明确排除 DNS/命令缺失假阳性 |

最终 `summary.json` 为 prototype=true、real_codex_ready=false、16 项 passed；`addresses.json` 保存本次对照地址，`containers.json` 保存脱敏后的权限、限额与无挂载事实。五轮 `cleanup.json` 均 verified=true，remaining 各类为空；保留失败证据。额外两个禁网一次性启动/命令存在性探针均 `--rm`，最终测试名称查询无残留。固定上游镜像与构建输入由 [依赖第 6.3 节](../dependencies/DEPENDENCIES.md#63-网络探针的固定镜像与构建输入) 维护，Docker 计数和共享缓存变更由 [环境第 3.5 节](../operations/LOCAL_DOCKER_ENVIRONMENT.md#35-无凭据网络探针) 维护。

最终全套默认检查：`.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider` 为 **93 passed, 14 skipped in 7.20s**；14 项真实集成默认未启用，本轮网络测试结果单独见表，不计入默认通过数。`ruff format --check src tests prototype_codex_harbor_e2e.py` 为 **49 files already formatted**；`ruff check` 同路径通过；`mypy src prototype_codex_harbor_e2e.py` 为 **28 source files** 通过。`--check` 仍为任务已验证、real_codex_ready=false，待固定配置、网络与秘密生命周期；没有改变实际 CLI 开放范围。

限定结论与下一步：详见 [执行接口网络探针](../interfaces/HARBOR_EXECUTION.md#无凭据网络探针2026-09-07)。当前只证明测试专用的 HTTP/IPv4 对照、代理 CONNECT、去能力与正常停侧车场景；生产 Task/Harbor 配置还没有接入这些策略，真实端点/TLS/SNI、IPv6、DNS/ICMP、长连接与其他故障路径仍须验证。原生 no-network 允许部分控制流量，不能等同 Docker network none。下一步深化现有 Execution Adapter，而非新增网络业务模块；Codex 固定版本/模型/effort 仍待用户确认。未读取任何真实凭据、未调用模型、未改宿主代理/防火墙或重启服务，未提交、未 push。

收尾复核：7 份变更 Markdown 的围栏/相对文件链接及 `git diff --check` 通过；49 个项目 Python 文件均不超过 200 行，src/tests 每层不超过 8 个文件；常见 Key/Bearer/JWT 形态扫描无命中。Harbor 固定 HEAD 未变且 Harbor/Fork 工作区干净，运行证据由 Git 忽略。最终 HEAD 仍为 f0a1a4a，相对已知 origin/main ahead 9，保留原未提交预检和本次测试/文档。多文件 apply_patch 曾部分生效后报上下文缺失，均读回核对并只补未生效目标，没有把失败返回当成未改文件，也没有盲目覆盖。Git 全局 ignore 权限及 LF/CRLF 提示不影响本次实际检查结果。

## 2026-09-07 网络配置接线与本地检查点

本步完成“先本地提交，再深化既有 Execution Backend 的网络配置接线”，不是完整 M0/MVP 完成。先创建 `6e66125 test: verify Harbor network policies and WSL preflight`，12 文件、908 行新增/51 行删除；提交后干净，相对已知 `origin/main=42484d8` 为 ahead 10 / behind 0，未 fetch、未 push。本节接线与文档是该检查点之后的未提交改动。

### 实施与诊断

- 修改前继续使用 `action-document` 记录措施与可执行成功标准；修改恢复入口时使用 `writing-for-agents`，把实际验证、剩余门槛和下一步分开。当前文件树见上方，不新增业务边界。
- Task 显式空 allowlist、可信本机 `network_hosts` → Job 基线、受限 Compose、固定源码 blob 导出和 CLI 引导均已实现。真实上游契约覆盖空列表与一个受控主机名，验证 setup/Agent/verifier 的实际解析。配置篡改测试覆盖 public 基线、阶段覆盖、host network 和额外 Compose；真实 Agent 在引导加载上游/创建 Docker 资源前被拒绝。
- 初始新增契约先因实现尚不存在而收集失败；实现后针对性 29 项通过。首次格式/type 检查发现长行、二进制流与文本流变量名复用、可空 `harbor.__file__` 未保护，均修正并复跑。格式化后正常 NOP 测试一度为 201 行，删除重复读取同一结果文件的冗余断言后为 199 行，没有压缩职责或放宽指标。
- 首次实际接线批次为 **2 failed / 1 passed in 41.56s**：使用生产模板的网络对照通过；串联和超时在创建 Trial 前因 `HARBOR_IMPORT_SOURCE_MISMATCH` 失败。没有将“网络对照通过”写成整批通过。
- 按 `diagnosing-bugs` 排序核查三个假设：相邻同名包遮蔽 > 固定虚拟环境指向错误源码 > 推导的框架根路径错误。以相同引导目录/环境启动固定 Python，实际 `harbor.__file__` 指向项目内部 `adapters/execution/harbor`，而不是固定上游。秒级回归先为 **1 failed / 27 deselected in 0.11s**；只在引导子进程环境增加 `PYTHONSAFEPATH=1`，保留源码身份检查，再测 **1 passed / 27 deselected in 0.14s**。没有重装 Harbor、改全局 Python/Git 配置或绕过身份门禁。
- 随后重跑原失败的完整两项 Docker 测试，另跑独立正常 NOP，均通过。真实 Trial 保留上游默认三个日志/制品宿主挂载，不能推广独立网络夹具的“无挂载”结论；详细行为只在 [执行接口](../interfaces/HARBOR_EXECUTION.md#无凭据网络探针2026-09-07) 维护。

### 实际自验证

命令均从 `apps/backend` 运行，使用 `.venv/Scripts` 下对应工具；集成测试用各自显式环境开关、`-p no:cacheprovider` 及以下全新 `--basetemp`，没有重用/覆盖旧证据。

| 验证 | 实际结果 / 证据 |
|---|---|
| Ruff format/check | 52 文件格式通过；lint 通过 |
| `mypy src prototype_codex_harbor_e2e.py` | strict mypy 30 个源文件通过 |
| `python -m pytest -q -p no:cacheprovider` | **122 passed / 14 skipped in 8.06s**；默认跳过的重型测试不算重新通过 |
| 开启 NETWORK、M0、HARBOR_TIMEOUT 三个集成开关，运行对应三个测试文件 | 首批 **2 failed / 1 passed in 41.56s**；目录 `runtime/prototype/m0-network-wired-20260907-01`。网络 `summary.json` 的 16 项均 passed，`cleanup.json` verified=true / 四类 remaining 均空；另两项失败及修复原因见上文 |
| 修复后开启 M0、HARBOR_TIMEOUT，重跑 `test_m0_pipeline_integration.py` 与 `test_harbor_timeout_cleanup.py` | **2 passed in 131.31s**；目录 `runtime/prototype/m0-network-wired-20260907-02`。串联 status=completed、patch_applied=true、resolved=false；无模型人工无效修复被正常判卷，不是 Agent 解题成功。超时 returncode=124、timed_out=true，精确资源清理断言通过 |
| 开启 HARBOR，运行 `test_harbor_nop.py` | **1 passed in 22.31s**；目录 `runtime/prototype/m0-network-wired-20260907-03`。生产引导、上游 NOP、0-byte patch/哈希、结果映射与正常 Compose 清理通过 |
| 固定上游身份 | Harbor `6af8d6e31eced13b93849cdf80feeadf24603d15`、Fork `242429c188fcfd06aad13fce9a54d450470bf0ac`，工作树均干净 |
| 实测后环境 | 原容器/网络/卷/镜像计数不变，具体数值及缓存边界见 [环境第 3.5 节](../operations/LOCAL_DOCKER_ENVIRONMENT.md#35-无凭据网络探针) |

### 剩余边界与下一步

配置接线已经完成，不再列为待实现。完整闭卷仍缺 DNS/ICMP、IPv6、TLS/SNI、已有长连接和其他侧车故障路径的可信验证；还需核验侧车自身经 FlClash 到真实模型端点的出站路径。真实 Codex 固定版本/模型/effort 仍需用户确认，安装/资源模板、凭据临时注入及成功/失败/超时销毁仍未通过。继续在现有 Adapter 内推进，不新增网络业务模块，不把 `--check-network` 变为完整就绪信号，不开始 M1/P2。

本步未读取真实 `auth.json`/Key/Token/Cookie，未调用模型，未修改宿主代理/防火墙，未重启 Docker/WSL，未改上游源码。仅清理本次测试所属临时容器/网络/卷/本地 Trial 镜像，保留运行证据与共享缓存。未新建第二个本地提交，未 push。

收尾检查：21 个实际变更文件（含 3 个未跟踪新文件）与当前文件树一致；8 份 Markdown 的围栏/相对文件链接通过，52 个项目 Python 文件均不超过 200 行，src/tests 每层文件数不超过 8。`git diff --check` 通过；全部变更文件的常见 Key/Bearer/JWT 形态扫描无命中，不将该形态扫描称为完整秘密审计。活动权威文档和 Handoff 已没有“生产尚未接线”的失效状态；历史行动阶段保留原证据并明确标注历史。Git 全局 ignore 权限和 LF/CRLF 提示仍存在，不影响本次实际通过结果。

## 2026-09-07 Codex 首轮 CLI 版本确认

- 用户对“首轮采用 Codex CLI `0.153.0`”明确回复“可以”。版本决定已登记在依赖总表，架构、接口和 Handoff 改为引用它；不再将版本列为待确认，也不把本次确认扩展为模型、推理强度或凭据使用许可。
- 本次只修改受影响文件树中标明的 6 份已有文档；此前未提交网络接线源码/测试原样保留，没有新增业务文件或更改生产入口。`writing-for-agents` 用于删除恢复入口中重复询问版本的失效步骤，保留模型/推理强度与容器验收门槛。
- `codex --version` 退出 0，返回与已确认版本一致。使用 `framework/harbor/.venv/Scripts/python.exe -` 执行无容器检查：通过替身 Environment 向固定上游真实 `_installed_codex_satisfies_version()` 方法提供三种结果，同版本=true、不同版本=false、命令失败=false，3 项断言通过。上游 `install()` 的同版本分支直接返回已核对；没有调用该安装方法，也没有证明容器内已有 Codex。
- 固定 Harbor HEAD 再次等于依赖事实源，工作树干净。6 份文档的围栏/相对文件链接、`git diff --check` 通过；当前接口和 Handoff 中的版本待选描述已替换，历史记录保留其当时语义。本次没有修改 Python，因此没有重跑 pytest、Ruff、mypy 或 Docker 集成；上一轮测试结果不冒充本轮重跑。
- OpenAI Docs 实际读取了 [CLI 安装文档](https://learn.chatgpt.com/docs/cli) 与 [模型说明](https://learn.chatgpt.com/docs/models)。安装制品来源/哈希及容器兼容性仍待核验；模型尚未选定，官方列出模型不等于已证明本账号和固定容器 CLI 可用。
- 未安装或升级任何软件、未启动容器、未读取真实登录凭据、未调用模型、未提交或 push。当时下一项为确认模型，然后确认推理强度；后续模型决定见下节，M0 仍进行中。

## 2026-09-07 首轮模型确认与运行状态核对

- 用户确认首轮模型，选择已登记在 [依赖总表](../dependencies/DEPENDENCIES.md#2-当前依赖总表)。本轮仅同步文件树所列 7 份已有文档；`writing-for-agents` 用于移除 Handoff 中重复询问模型的步骤，保留推理强度和实际可用性门槛。此前源码/测试改动完整保留，无新增文件或架构元素。
- Docker 查询均为只读：当前 context、info、ps、ps -a 和 compose ls。Windows CIM 进程查询首次因权限失败，提权重试后成功，过滤到已知项目进程且只输出名称/数量/PID，无匹配。运行状态与检查范围见 [本机 Docker 环境第 3.6 节](../operations/LOCAL_DOCKER_ENVIRONMENT.md#36-项目运行状态只读核对)；没有调查 Dify 停止原因，也没有将首次失败记为通过。
- 7 份文档的代码围栏配对、相对文件链接检查通过；当前待办检索确认 CLI/模型不再列为待选。`git diff --check` 通过，既有 Git ignore 权限与 LF/CRLF 提示不作无关修改。补丁工具部分报错后实际已有文件落盘，逐次读回核实，仅重试尚未生效的修改。
- 本轮没有修改 Python，未重跑 pytest、Ruff、mypy 或 Docker 集成；上轮 122 passed / 14 skipped 等证据不是本轮测试结果。未启动、停止、删除或重启容器/服务，未改代理，未安装软件、读取真实凭据或调用模型，未提交或 push。当时首轮配置下一项为推理强度，后续确认见下节；M0 仍进行中。

## 2026-09-07 首轮推理强度确认

- 本次文档同步完成：首轮 CLI、模型与推理强度均已确认，唯一值见依赖总表；7 份既有文档与当前增量文件树一致。`writing-for-agents` 用于将 Handoff 的重复确认步骤替换为技术核验入口，真实调用门槛保持关闭。Dify 停止原因改为引用用户补充说明，而非推断故障。
- 只读源码核对：现有 `config_mapper.py` 强制显式传入 effort 并写入 Harbor `agents[].kwargs.reasoning_effort`；无需改接口或新增模块。未将契约测试中的既有占位配置冒充真实运行结果。
- PowerShell 检查 7 份 Markdown 围栏配对、相对文件链接均通过；活动依赖/架构/接口/Handoff 的失效待选描述检索无命中，`git diff --check` 通过。Git ignore 权限及 LF/CRLF 提示未作无关修改。
- 本轮仅改文档，未重跑 pytest、Ruff、mypy 或 Docker 集成，未重新查询 Docker/系统进程；未安装、调用模型、接触凭据或变更服务，未提交或 push。当时下一步为 M0 安装、网络隔离和凭据生命周期验收，后续结果见下节，不能因配置选择完成而标记 M0 完成。

## 2026-09-07 无凭据安装与网络追加取证

本步安装与边界取证完成，完整 M0 仍未完成；没有为了运行模型而降低隔离要求。

### 实际安装与验证

- 依照 OpenAI Docs 的 CLI 安装页确认 npm 官方渠道，随后只读主包/平台包元数据，下载精确制品；身份唯一维护在依赖第 2.1 节。未执行动态安装脚本、npm install、宿主升级或 Node/npm 安装，未修改题目镜像。
- 新增 `codex_install.py`，先验证完整包字节/成员/平台，再解出 8 个固定普通文件并保存逐文件 hash。单元契约覆盖大小/hash/平台/路径穿越/符号链接拒绝、有效包与禁止覆盖；先跑为 **6 passed / 1 skipped in 0.13s**。
- 显式设置 `AGENTEXAM_RUN_CODEX_INSTALLATION=1` 与 `AGENTEXAM_CODEX_ARCHIVE`，运行 `python -m pytest -q tests/contract/test_codex_installation.py --basetemp <全新证据目录> -p no:cacheprovider`，结果 **7 passed in 14.41s**。真实 Docker 容器内版本/帮助通过，固定 Harbor 的真实 install 方法只执行版本查询并复用；该方法的测试 Environment 仅允许查询版本，任何联网安装命令会立即拒绝。没有运行真实 Trial、认证 setup 或模型。
- 安装证据保留在 `runtime/prototype/m0-codex-install-20260907-01/`：下载归档、解包 manifest、installation-result/cleanup 和有界进程日志。容器按专属标签删除并复核为空，日志无截断或进程告警；这不代表凭据成功/失败/超时销毁已通过，因为本次没有真实凭据。
- 默认全套 **128 passed / 15 skipped in 8.37s**；15 项跳过为显式集成开关未开，安装集成已另跑，不重复声称其他旧集成本轮通过。Ruff check 通过，55 个 Python 文件格式检查通过；strict mypy 覆盖 src 与原型入口为 **31 source files 通过**。

### 网络诊断及失败保留

- `m0-network-extra-20260907-01` 因固定 Harbor 环境无 pytest，在创建容器前失败；改为项目环境生成夹具 JSON，未给上游安装 pytest。
- `...-02` 的进程退出 0，但 ICMP 报文校验和未处理奇数长度，正反对照均在发包前失败；公网 DNS 也仅报解析失败。两者均没有可信阻断结论。受控自签 TLS 对照已完成，所有本次资源清理通过。
- `...-03` 修复 ICMP 校验和并采用两组受控 Docker DNS 别名，建立 public 正对照后复测；实际确认 no-network 下 DNS 查询和携带合成标记的 ICMP echo 仍成功，源代码显式放行规则解释了结果。准确结论和限制唯一记录在 [执行接口追加取证](../interfaces/HARBOR_EXECUTION.md#无凭据追加边界取证2026-09-07)。程序退出 0 只表示取证完成，网络隔离验收未通过。
- 追加脚本是忽略证据，不是新增业务 Module 或正式网络回归实现。受控 TLS 使用临时自签证书及测试 `-k`，不证明真实模型端点证书验证或 FlClash 出站已通过。三轮证据完整保留；最后一轮有界日志没有截断/超时/告警，专属容器/网络/卷/镜像复核为空。

### 收尾与下一步

`writing-for-agents` 将 Handoff 改为从已确认缺口恢复，避免重复安装或把只读/替身证据误读为真实调用。7 份权威/行动文档同步实际安装、旧代理说明和新发现，原网络接线代码/测试不动。Docker 收尾为 18 个容器、0 个运行、25 个镜像，详情见本机环境文档；没有重启服务、启动 Dify、修改代理/防火墙或上游代码。只清理本轮临时容器与网络，证据及原有共享镜像保留。未读取/注入个人登录凭据，未调用模型，未创建新提交或 push。

当时提出先补 DNS/ICMP 防护；后经用户质疑并授权风险评估，确认该优先级推断过强。纠偏过程见下方风险评估记录，当前实施边界以认证接口第 6.2 节为准，不把本段历史下一步作为全面封禁协议的授权。真实网络/凭据验收与架构变更确认纪律保持不变。

收尾检查通过：7 份文档围栏配对/相对文件链接无错误；55 个项目 Python 文件均不超过 200 行，src/tests 每层文件数不超过 8（contract 和 integration 恰好各 8）。本次三个新文件分别为 112/134/190 行；当前 24 个变更文件与两段增量文件树一致。`git diff --check` 通过，活动依赖/接口/Handoff 没有继续宣称固定包或无凭据安装未验证。既有 Git ignore 权限与 LF/CRLF 提示未作无关修改；保护路径证据的默认读取权限失败由提权只读复核完成，不改 ACL。

## 2026-09-07 DNS/ICMP 风险评估

### 情况说明与实际措施

用户要求评估风险，不是立即修复或接受风险。本轮评估与文档事实纠偏完成，M0 仍进行中。完整论证、证据分级与建议唯一维护于 [风险报告](../research/2026-09-07-dns-icmp-risk-assessment.md)。结论不等于 DNS/ICMP 安全通过或已有真实外泄；凭据输出覆盖不足是更优先的已证实问题。

`action-document` 先记录 6 份文档及忽略诊断证据；`research` 让后台助手仅核对一手协议/Docker/Linux 来源并创建报告外部资料部分，主代理核对代码与实测后合并；OpenAI Docs 核对文件凭据与容器内关闭内层沙箱的边界；`writing-for-agents` 修正 Handoff 恢复优先级，避免把建议当成已确认规则。新增报告落于现有 research 目录（由 4 增为 5 份文件）；没有新增业务 Module/Interface/表/源代码目录。

实际改动为实施措施内的 6 份文档：新增报告；执行接口保留原始网络结果、撤回超出证据的定性；认证接口补固定源码及合成验证限制；架构修正过期的显式代理注入说明并改为权威指针；Handoff 与本记录同步。现有生产代码、测试文件和固定框架不改；本轮无网络规则变更，没有实施风险处置建议。

### 实际验证及限制

- `git -C framework/harbor rev-parse HEAD` 与 `git ... status --short`：固定提交正确、工作树干净。源码确认原生策略放行配置 resolver / ICMP，真实 Agent 入口仍拒绝非 NOP。未 fetch，不能声称远端最新。
- 在 `apps/backend` 运行 `.venv/Scripts/python.exe -m pytest -q tests/contract/test_execution_network.py -p no:cacheprovider`：**28 passed in 0.48s**；覆盖环境过滤、真实入口拒绝、配置防篡改等，不是公网/凭据实测。
- `framework/harbor/.venv/Scripts/python.exe runtime/prototype/dns-icmp-risk-probe.py`：**退出 0，5 项行为断言成立**。真实 Harbor 脱敏方法抹除假 env 值/假文件路径，假文件 Token 仍在；项目日志持久化同样保留假 Token、无截断。报告明确这是覆盖不足复现，不是安全通过。全部输入自行生成，无真实凭据、Docker、登录或模型调用。
- `apps/backend/.venv/Scripts/ruff.exe check runtime/prototype/dns-icmp-risk-probe.py` 及 `ruff ... format --check`：通过。诊断脚本与合成输入/结果留在忽略 runtime 目录，不是新增生产实现或完整 Trial 测试；未删除任何历史证据。
- 既有 `m0-network-extra-20260907-03` 摘要及清理 JSON 本轮只读复核；DNS/ICMP 仅证明测试网络内通路，历史清理 verified=true，不伪装成本轮重跑/全局 Docker 状态。
- 未重跑完整 pytest、mypy、Docker 网络集成或真实模型；没有公网接收端测量、IPv6 实测或真实 Token 生命周期证据。保持未知而非假设安全，不为消除未知擅自配置公网接收端或扫描校园网。
- 定位中首次引用不存在的 `process.py`、使用 Windows 路径通配失败；随后 `rg --files` 定位到实际 `harbor/process_evidence.py` 等文件并读回。补丁工具一次报错但已部分落盘，读回后仅补剩余文件；未把错误当成功。既有 Git ignore 权限提示不作无关配置修改。

本轮未读取/注入真实秘密、未启动/停止容器、未改代理/防火墙/WSL、未新增提交或 push。建议下一项优先做假值凭据读取/输出/清理核验，网络范围补测保持有界；若需改变认证架构或接受剩余风险，交由用户确认，不因评估完成自动继续实施。

最终文档检查：PowerShell 检查本轮 6 份 Markdown 的相对文件链接和代码围栏全部通过；`git diff --check` 退出 0。新增报告已读回，来源、源码事实、方法级复现与历史容器证据分别标注，Handoff 的旧强制封禁步骤已更正；原始实测记录完整保留。诊断脚本为 88 行，research 目录为 5 文件。当前全工作区为 26 个未提交文件（包含此前改动），本轮新增 1 份报告并修改 5 份既有文档，忽略证据另存；未把文档/方法级检查报成完整安全验收通过。

## 2026-09-07 假凭据检查与日志小修

### 实施结果与范围

用户接受假值读取、输出与结束清理检查，以及现有适配层内的小修。本轮局部检查完成，完整 Harbor 凭据安全仍未通过；当前能力及未接线项唯一维护于 [认证接口第 6.2 节](../interfaces/CODEX_AUTHENTICATION.md#62-2026-09-07-假凭据安全收尾)。不把一次沙箱命令成功或已知字符串替换当作完整真实评测的安全保证。

实际修改与本记录首段 10 文件树一致：新增内部 `redaction.py` 与 `tests/test_secret_safety.py`，修改现有 `process_evidence.py` / `process_runner.py`，同步 6 份文档。新能力仅接受可信调用方显式传入的内存字节值，在 stdout/stderr 持久化和大小截断之前替换；启动失败的异常消息也处理。默认未传值时保持原行为，不读取认证文件，不改变公开 ExecutionBackend，不新增业务 Module、port、表或源代码目录。

`action-document` 先记录范围和成功标准；`diagnosing-bugs` 用既有复现加红→绿回归约束修复；OpenAI Docs 用于核对权限配置，固定包的真实 CLI 帮助和实测决定具体命令；`writing-for-agents` 将 Handoff 分开标注局部通过与完整接线待办。未引入新架构决定或网络规则。

### 失败与修复证据

- 初始测试因新参数/模块未实现产生 20 项失败，只说明实现尚不存在，不算泄露复现。随后用兼容旧调用的真实进程测试得到 **3 failed / 1 passed / 16 deselected in 0.52s**：正常、报错、超时三种输出保留完整假 Token；Windows 原生启动错误未包含该标记，故该对照通过。实现后移除临时兼容分支。
- 首轮新测试与既有进程测试合跑为 **25 passed in 6.41s**。追加注入式启动异常和 200 组确定性随机重叠字节模式后，新文件单独为 **22 passed in 0.55s**。覆盖 11 种分块大小、64 KiB 读取边界、双流、落盘前替换、上限截断、无效输入提前拒绝，以及无过滤时二进制保真；全部使用假值。
- 独立 Docker 探针复用缓存镜像和安装文件，运行前复核 8 个安装文件哈希。容器禁网、无挂载、去全部 capability、禁止提权，并设置资源限额；只复制固定 CLI 与合成夹具。UID 65534 的直接命令可读取自己所有的 0600 假凭据及其链接，说明仅靠该文件权限不能隔离同用户仓库命令。
- 第一轮误用 `codex sandbox linux ...`，固定 CLI 将 `linux` 当作待执行程序，退出 101、未执行读取程序；保留失败，不记为阻断。读取实际帮助后改为 `codex sandbox -- <command>`，第二轮退出 0：题目文件读写正常，假凭据原路径和链接均拒绝读取。没有增加容器权限；临时 CODEX_HOME 的 PATH aliases 警告仍保留，完整工具链兼容性未验证。

### 实际验证与清理

默认检查在 `apps/backend` 使用 `.venv/Scripts` 对应工具执行：

| 命令或检查 | 实际结果 |
|---|---|
| `ruff check src tests prototype_codex_harbor_e2e.py` | 通过 |
| `ruff format --check src tests prototype_codex_harbor_e2e.py` | 57 files already formatted |
| `mypy src prototype_codex_harbor_e2e.py` | 32 source files，通过 |
| `python -m pytest -q -p no:cacheprovider` | **150 passed / 15 skipped in 8.86s**；15 项显式开关集成未启用，不算本轮通过 |
| `runtime/prototype/credential-boundary-20260907-01/` | 正常、报错、超时返回 0/7/124；已登记假值在两个持久化日志中均不存在；包含首次沙箱命令失败 |
| `runtime/prototype/credential-boundary-20260907-02/` | 纠正后的固定 CLI 独立读取对照通过；不含模型会话或完整 Harbor Trial |
| 固定 Harbor | HEAD 为 `6af8d6e31eced13b93849cdf80feeadf24603d15`，工作区干净 |

探针在 finally 显式调用现有精确 Compose 清理 helper，三种结束路径均无清理告警、verified=true；第二轮同样清理。收尾按四个专属 project 标签重新查询，四个临时容器全部不存在。删除的是本轮测试容器及其可写层，假凭据随容器移除；合成输入、结果和旧证据保留，可重新生成测试容器。该结果不证明完整 Harbor 的正常/失败/超时路径均已接入清理，也不覆盖真实 Trial 的宿主挂载残留。最后 Docker 为 18 个容器、0 个运行、25 个镜像，共享缓存和 Dify 未动。

运行脚本位于忽略的 `runtime/prototype/credential-boundary-probe.py` 和 `credential-fixture.py`；目前反映第二轮纠正命令，第一轮实际命令/结果保留在其证据 JSON，不覆盖失败记录。Docker 配置/命名管道及历史证据的默认访问权限不足时，仅申请本任务所需权限后重试，没有修改 ACL 或全局配置。

### 收尾与下一步

6 份文档的围栏/相对文件链接、`git diff --check` 通过；57 个项目 Python 文件均不超过 200 行，src/tests 每层文件数不超过 8。全工作区现有 30 个未提交文件，其中包含开始本轮前的 26 个；本轮没有删除或覆盖无关改动。最新状态、文件树、认证接口、执行接口、风险报告指针与 Handoff 已对齐，历史测试数量仍按各轮保留。

下一步仍在既有 Adapter 内把读取限制接入完整 Harbor 路径，并覆盖原生会话/轨迹、刷新值及全部结束路径的假值验证。当前原生 bypass 未改、非 NOP 门禁未开放；生产调用方还没有提供真实秘密列表，不能说所有 Trial 已自动脱敏。若实现要求新增架构边界或改变产品行为，应先提交具体选择给用户确认。网络剩余验证另行保持有界，不默认全面封禁 DNS/ICMP。

本轮没有读取、注入或使用真实 auth.json/API Key/Token，没有调用评测模型、修改上游、重启 Docker/WSL、改变代理/防火墙、安装新镜像或新增服务；没有本地提交或 push。M0/MVP 仍未完成。

## 2026-09-07 固定 Harbor 启动兼容接线

### 实际结果与边界

用户要求解释日志实现并继续下一阶段。本轮兼容代码和局部验证完成，完整生产接线未完成：5 份新增代码/测试、5 份已有文档与实施措施文件树一致；原生 Harbor 不改，真实凭据解析和非 NOP 入口均保持关闭，兼容类还没有注册到 Job。当前能力和下一步只在 [认证接口第 6.2 节](../interfaces/CODEX_AUTHENTICATION.md#62-2026-09-07-假凭据安全收尾) 维护。

内部 Adapter 使用窄继承复用固定上游 run；已知值日志功能不变，未把字符串替换扩大到判卷 patch。行动技能先记录计划；OpenAI Docs 核对旧 sandbox 设置覆盖 profile 的行为，具体固定版本仍以源码/命令实测为准；`writing-for-agents` 将方法契约、独立容器证据与未完成生产接线分开，不让交接误开真实入口。本轮不是 API Key 配置或 API 调用工作，保持已确认的 ChatGPT 认证路线，不检查或索取真实 Key。

### 失败、诊断与修复

- 第一批配置/启动命令及实际固定 Harbor run 的替身契约 **22 passed in 0.95s**。动态导入上游类最初未通过 mypy，改为该隔离边界的两项精确类型注释；没有全局忽略类型错误。后加负例时内嵌脚本有 3 处行宽错误，换行后重跑通过。
- Docker 第一轮 `codex-guard-20260907-01` 的对照命令返回 1，错误为 `bwrap: Can't mkdir .../.codex: Not a directory`；Python 读取程序未执行，记录为失败，绝不是凭据读取已挡住。外层探针返回 0 只表示收集完成，最终断言明确使驱动失败。
- 使用 `diagnosing-bugs`：同一禁网容器把命令最小化为 `/bin/true` 仍失败；向用户说明按“缺失 deny 目录、/proc 禁止、/tmp 写入冲突”排序的三个假设，再做单变量对照。第二轮 `...-02` 中原配置、仅去 /proc deny、仅去 /tmp write 均失败；创建空 `.codex` 目录并恢复原配置后，完整读取/写入测试通过。未将诊断中的临时删规则推广到生产配置。
- 修复为在受控运行前准备实际空目录并拒绝符号链接，保持全部权限规则。第三轮 `...-03` 使用生产生成的准备命令和 profile，正对照可读两条假凭据，沙箱对照退出 0、题目读写正常、两条凭据读取及目录写入/安全配置改写均拒绝。临时 CODEX_HOME 的 PATH aliases 警告保留；该结果不是所有 Codex 工具或模型会话兼容保证。
- 忽略探针的动态 sys.path 导入触发 E402，使用仅针对这五处导入的注释说明，单独 Ruff 检查通过。初次文档补丁上下文不匹配，读回确认后改用唯一标题定位；最初 ADR 路径不存在，经 `rg --files` 找到实际 `docs/adr/0001-use-harbor-as-execution-backend.md` 并完整阅读，没有自行创建替代文档。

### 实际自验证

默认检查从 `apps/backend` 使用 `.venv/Scripts` 中工具运行；固定上游方法契约使用现有 Harbor Python，缺少该解释器时明确 skip。默认全套首次为 174 passed / 15 skipped in 10.70s；行宽修正后完整复跑结果如下：

| 命令 | 实际结果 |
|---|---|
| `ruff check src tests prototype_codex_harbor_e2e.py` | 通过 |
| `ruff format --check src tests prototype_codex_harbor_e2e.py` | 62 files already formatted |
| `mypy src prototype_codex_harbor_e2e.py` | 34 source files，通过 |
| `python -m pytest -q -p no:cacheprovider` | **174 passed / 15 skipped in 9.89s**；15 项显式开关的重型集成未启用，不算重跑通过 |
| `framework/harbor/.venv/Scripts/python.exe runtime/prototype/codex-guard-docker.py`，三轮分别使用全新证据目录 | 第一轮最终断言失败；第二轮定位完成；第三轮最终安全对照断言通过。只运行 sandbox 子命令，没有 codex exec/model |
| 忽略的共用探针、驱动、容器夹具 Ruff format/check | 最终通过；脚本目前反映第三轮修复，历史命令/结果保留于各轮 JSON |

固定上游 run 契约覆盖正常、配置上传失败、运行失败、注入取消、清理失败；额外拒绝未绑定真实凭据、宿主秘密环境、任意 config/extra_env/MCP、root/0 用户及未知命令。RecordingEnvironment 不执行命令，因此只证明控制流和清理尝试。独立容器对照使用固定缓存镜像、无挂载、network none、去全部 capability、禁止提权及资源限额；与完整 Trial 的宿主挂载不同，不推广结论。

三轮本次临时容器均按精确生成标签清理，记录 verified=true；收尾再次查询三个标签均无容器。删除的是本轮测试容器及其可写层，假值可由保留脚本重新生成，历史证据和缓存未删。Docker 最后为 18 个容器、0 个运行、25 个镜像；固定 Harbor HEAD 正确、工作区干净。未动 Dify、代理、防火墙、Docker/WSL 或校园网设备，没有拉取镜像、真实认证、模型调用、本地提交或 push。

收尾检查：62 个项目 Python 文件均不超过 200 行，src/tests 每层不超过 8；execution 父目录及 harbor 子目录现均满 8。5 份 Markdown 的围栏、相对文件链接和新增行动标题检查通过，git diff --check 通过；既有 Git ignore 权限与 LF/CRLF 提示未作无关配置修改。Git 现有 35 个未提交文件，保留开始前的 30 个，本轮新增 5 个。文档收尾以本节与认证事实源为准，恢复时先处理原生输出/刷新值和全流程假值证据，不把本阶段局部完成当作 M0/MVP 完成。

## 2026-09-07 本地检查点与 MVP 进度复核

用户要求本地提交后解释下一阶段和 MVP 剩余距离，本轮不继续实现。仅编辑本记录与 Handoff，其他 33 个既有变更文件原样纳入检查点；前述忽略证据/缓存不进入 Git，不新增架构或业务范围。检查点主题为 `feat: checkpoint M0 networking and Codex safety groundwork`，具体身份及提交后工作区以 Git 为准。

从 `apps/backend` 重新运行 `.venv/Scripts` 工具：`ruff check src tests prototype_codex_harbor_e2e.py` 通过；同路径 `ruff format --check` 为 62 files already formatted；`mypy src prototype_codex_harbor_e2e.py` 为 34 source files 通过；`python -m pytest -q -p no:cacheprovider` 为 **174 passed / 15 skipped in 10.05s**。15 项重型集成未启用，本轮没有启动 Docker 或模型，既有独立容器结果仍是历史证据。

提交范围复核为 35 个项目文件，路径仅限已检查的 Python/Markdown；常见 Key/Bearer/JWT/私钥头形态扫描无命中，只证明该形态检查，不声称全面秘密审计。10 份变更 Markdown 的围栏/相对文件链接、git diff --check 通过。`action-document` 维护可追溯范围；`writing-for-agents` 将检查点后的恢复入口改为实时 Git 核验，保留技术验收未完成的边界。既有 ignore 权限与 LF/CRLF 提示不修改全局配置。

进度判断依据实际 apps 文件树和执行接口第 13 节：Task/Harbor/patch/Fork 底层和无模型验证已有实现，真实 Codex 单题闭环仍未验收；M1 的 Web、HTTP、持久化、账号/批准/队列/Worker、报告与协作部署尚未实现。下一阶段范围继续引用认证接口第 6.2 节，不把本地提交当成 M0 完成，也不把测试数量换算成 MVP 完成百分比。未 fetch、未 push、未访问真实凭据。
