# 上游框架与 Agent CLI 接口清单

> 文档状态：持续维护；上游事实已核验，Harbor 架构映射已确认，运行能力仍待分层实测
>
> 最后更新：2026-09-05
> 权威范围：本文件维护 SWE-Gym、Harbor、SWE-Bench-Fork 和目标 Agent CLI 的真实上游接口入口。Harbor 字段级映射见 [`HARBOR_EXECUTION.md`](./HARBOR_EXECUTION.md)；Codex 与自研 Agent 凭据政策见 [`CODEX_AUTHENTICATION.md`](./CODEX_AUTHENTICATION.md)；依赖来源与固定版本见 [`DEPENDENCIES.md`](../dependencies/DEPENDENCIES.md)。

## 1. 先把最容易混淆的事说清楚

“直接使用 SWE-Gym”不是把整个 Web 平台写进 SWE-Gym 仓库，也不是寻找一个不存在的 `swe_gym.run_agent()` 函数。

当前上游事实是：

1. SWE-Gym 主仓库提供数据、模型与复现实验材料；官方 README 把数据放在 Hugging Face，并明确把环境常量指向 SWE-Bench-Fork。
2. 配套 SWE-Bench-Fork 提供实际的任务字段、Docker 环境构建和 `swebench.harness.run_evaluation` 判卷入口。
3. 因此本项目“直接使用框架”的运行含义是：**读取真实 SWE-Gym 任务 → 让 Agent 在固定仓库快照生成 patch → 把真实 prediction 交给固定版本 SWE-Bench-Fork 判卷**。
4. 本项目用 Harbor 统一运行 Agent 和 Docker 环境，在外面增加平台 Job 队列、长期制品、固定 Fork 判卷、Judge、人工复核和 Web，不重写上游判卷语义。

SWE-Gym 本身没有提供 Codex/Aider/Claude Code 的统一 Runner；固定 Harbor 已核验包含多 Agent、Environment、Job/Trial 与轨迹能力，因此项目通过 `HarborExecutionAdapter` 复用它，而不是重复自研同一层。补丁出口和本机兼容性仍需真实原型证明。

## 2. 事实状态

| 状态 | 含义 |
|---|---|
| 已核验源码 | 已从当前本地固定提交读取到接口定义 |
| 已核验官方文档 | 已从工具供应商官方文档/官方源码确认 |
| 架构已确认 | 项目已决定采用该映射，但不等于本机运行通过 |
| 候选映射 | 本项目怎样使用真实接口的设计，尚未实现 |
| Adapter 契约通过 | 固定版本通过本项目统一协议测试 |
| 真实账号通过 | 使用真实模型凭据在小仓库运行通过 |
| SWE-Gym E2E 通过 | 真实任务从 Issue 到 SWE-Bench-Fork 结果完整跑通 |

后三级都需要实际运行证据，不能从文档可行性直接推导。

Codex 相关状态必须再区分三层：官方 `codex exec` 接口已核验；认证政策已经由项目确认；宿主 CLI 与 Harbor 容器运行能力必须分别用本机证据验证。任一层通过都不能替代另外两层。

2026-09-04 的宿主探针只证明当前 npm 安装的 CLI 能输出版本和帮助；它没有发起模型请求、没有检查登录状态，也不证明 Harbor 容器 E2E 可用。

## 3. 上游身份与固定版本

依赖身份、官方来源、完整提交哈希、本地恢复命令和当前验证状态只在 [`DEPENDENCIES.md`](../dependencies/DEPENDENCIES.md) 维护。本文件中的接口结论必须针对那里记录的固定快照核验，不得默认跟随上游 `main` 漂移。

任何升级先更新依赖事实源，再重新核验本文字段与 CLI，最后执行契约/E2E 测试。

## 4. SWE-Gym Task Source

### 4.1 已核验接口事实

SWE-Gym README 说明任务数据在 Hugging Face，环境常量位于 SWE-Bench-Fork；复现实验分别通过项目固定的 OpenHands/MoatlessTools 流程完成。来源：[固定提交的 SWE-Gym README](https://github.com/SWE-Gym/SWE-Gym/blob/b681068ca20628c6987b7416cc4cf03f06b77ba5/README.md)。

固定 SWE-Bench-Fork 中：

- `load_swebench_dataset(name, split, instance_ids)` 支持 Hugging Face 数据集名称，也支持本地 `.json`/`.jsonl`；来源：[固定提交的 `utils.py`](https://github.com/SWE-Gym/SWE-Bench-Fork/blob/242429c188fcfd06aad13fce9a54d450470bf0ac/swebench/harness/utils.py)。
- `SWEbenchInstance` 在固定提交中列出以下字段；来源：[固定提交的 `constants.py`](https://github.com/SWE-Gym/SWE-Bench-Fork/blob/242429c188fcfd06aad13fce9a54d450470bf0ac/swebench/harness/constants.py)。

| 上游字段 | 用途 | Agent 是否可见 |
|---|---|---:|
| `instance_id` | 任务唯一身份 | ✅ |
| `repo` | 目标仓库 | ✅ |
| `base_commit` | 固定仓库快照 | ✅（审计信息） |
| `problem_statement` | Issue 题目 | ✅ |
| `patch` | gold 修复补丁 | ❌ |
| `test_patch` | 判分测试补丁 | ❌ |
| `FAIL_TO_PASS` | 修复后应从失败变通过的测试 | ❌ |
| `PASS_TO_PASS` | 原本通过且不能回归的测试 | ❌ |
| `hints_text` | 上游提示 | 待确认是否使用；默认不暴露 |
| `version` / `created_at` | 元数据 | 页面按需展示 |
| `environment_setup_commit` | 环境准备信息 | 只供环境 Adapter |

`FAIL_TO_PASS`/`PASS_TO_PASS` 在该固定代码的 `TypedDict` 中声明为字符串，而 `make_test_spec` 会把 JSON 字符串或对象解析成列表。项目内部要规范化为列表，不能假定加载后天然同一类型。

### 4.2 候选 Adapter 映射

| Task Catalog 输入 | 上游调用 | Task Catalog 输出 |
|---|---|---|
| `dataset_id`、固定 `dataset_revision`、`split`、`instance_id` | 固定 revision 的数据加载 + `load_swebench_dataset` 兼容层 | 内部 `EvaluationTask` |

映射规则：

1. 导入/登记时校验必需字段和内容哈希，不在每次运行时盲目下载会漂移的数据。
2. 标准化字段写 PostgreSQL，同时把完整原始任务 JSON 以内容 SHA-256 寻址写入 MinIO；两者在同一同步动作中冻结。
3. 内部对象分成 Agent 可见视图和 Evaluator 受限视图；原始快照中的隐藏字段不能因为存入 MinIO 就暴露给 Agent/API。
4. 普通 HTTP API 和 Runner 永远不返回 gold patch 与判分测试答案。
5. 首个原型数据集 ID 已确认为 `SWE-Gym/SWE-Gym-Lite`；revision、split 和具体实例必须在实际读取数据元信息后记录，本文不凭 README 猜 split 名称。

## 5. SWE-Bench-Fork Patch Evaluator

### 5.1 已核验入口

官方 fork 文档把主入口定义为：

```text
python -m swebench.harness.run_evaluation
```

来源：[固定提交的 Docker Harness 文档](https://github.com/SWE-Gym/SWE-Bench-Fork/blob/242429c188fcfd06aad13fce9a54d450470bf0ac/docs/20240627_docker/README.md)和[`run_evaluation.py`](https://github.com/SWE-Gym/SWE-Bench-Fork/blob/242429c188fcfd06aad13fce9a54d450470bf0ac/swebench/harness/run_evaluation.py)。

固定提交的 CLI：

| 参数 | 必需/默认 | 含义 |
|---|---|---|
| `--dataset_name` | 默认 `princeton-nlp/SWE-bench_Lite` | HF 数据集名或本地 JSON/JSONL；本项目必须显式传 SWE-Gym 数据源 |
| `--split` | 默认 `test` | 本项目必须显式传实际 split，不借用默认值猜测 |
| `--instance_ids` | 可选，多值 | 限制本次任务；单次运行传一个 ID |
| `--predictions_path` | 必需 | `gold`、`.json` 或 `.jsonl` prediction |
| `--max_workers` | 默认 4 | Harness 并行度；单机首版候选显式传 1 |
| `--timeout` | 默认 1800 秒 | 每个实例测试超时 |
| `--run_id` | 必需 | Harness 日志和容器的运行标识 |
| `--force_rebuild` | 默认 false | 是否重建镜像 |
| `--cache_level` | 默认 `env` | `none/base/env/instance` 缓存清理层级 |
| `--clean` | 默认 false | 是否清理高于缓存层级的镜像 |
| `--open_file_limit` | 默认 4096 | 进程文件描述符上限；Linux 环境约束 |

不要直接依赖所有默认值。项目 Adapter 要显式记录 dataset、split、instance、worker 数、timeout、cache 策略、run ID 和 fork commit。

### 5.2 prediction 输入

每条 prediction 的已核验最小 schema：

```json
{
  "instance_id": "upstream-instance-id",
  "model_patch": "git unified diff",
  "model_name_or_path": "stable-agent-configuration-identity"
}
```

字段常量分别为 `instance_id`、`model_patch`、`model_name_or_path`；来源：[固定提交的 `constants.py`](https://github.com/SWE-Gym/SWE-Bench-Fork/blob/242429c188fcfd06aad13fce9a54d450470bf0ac/swebench/harness/constants.py)。

项目映射：

| 本项目字段 | prediction 字段 | 规则 |
|---|---|---|
| `EvaluationTask.instance_id` | `instance_id` | 原样使用上游 ID |
| Runner patch 制品正文 | `model_patch` | 必须与保存的 patch SHA-256 一致 |
| `AgentConfiguration` 稳定标识 | `model_name_or_path` | 使用安全、稳定、可追溯字符串；上游会把 `/` 替换为 `__` 作为日志路径 |

### 5.3 已核验输出

单实例路径：

```text
logs/run_evaluation/{run_id}/{model_name_or_path}/{instance_id}/
├─ patch.diff
├─ eval.sh
├─ test_output.txt
├─ run_instance.log
└─ report.json
```

成功形成的实例 `report.json` 至少包含：

- `patch_exists`；
- `patch_successfully_applied`；
- `resolved`；
- `tests_status`（启用详细状态时）。

Harness 还在当前工作目录生成 `<model_name_or_path>.<run_id>.json` 汇总，固定 schema version 为 2，包含 completed/resolved/unresolved/empty patch/error 等计数和 ID 列表。

重要边界：

- 空 patch 会进入 `empty_patch_ids`，可能不会产生单实例 `report.json`。
- 某实例没有产生 report 时，汇总会放入 `error_ids`；Adapter 必须把它当 Harness/基础设施失败调查，不能自动写 `resolved=false`。
- `resolved=false` 且 report 完整表示测试正常执行但补丁没有完全解决任务；这是正常评测结果，不是平台崩溃。
- Patch Evaluator Adapter 需要复制这些原始文件到 MinIO，再规范化为内部 `DeterministicResult`。

### 5.4 候选调用方式

第一版建议 Adapter 生成单条临时 JSONL prediction，并以子进程调用固定模块 CLI，而不是把上游 `main()` 的内部参数传播到整个应用。这样：

- 仍然是直接执行真实 SWE-Bench-Fork Harness；
- 上游进程、Linux `resource`、Docker 日志目录和退出状态被隔离在一个小 Adapter 内；
- 业务层只接收 `EvaluationRequest → DeterministicResult`；
- CLI 变化只需改 Adapter 与契约测试。

该方式仍需在 Linux/WSL2 + Docker Desktop 环境进行 gold patch 冒烟测试后确认。

## 6. Harbor Execution Backend

[`DEPENDENCIES.md`](../dependencies/DEPENDENCIES.md) 固定的 Harbor 提交已通过官方源码静态核验：

- `JobConfig` 接受 `agents`、`datasets`/`tasks`、`n_attempts`、`n_concurrent_trials`、`environment`、`verifier` 与 `artifacts`；
- `JobPlan.build_trial_configs()` 按 attempts×tasks×agents 展开 `TrialConfig`；
- `VerifierConfig.disable` 可关闭 Harbor Verifier；
- `SingleStepTrial` 在运行 Agent 后、Verifier 前同步 Agent 输出并收集 artifacts；
- `JobResult` 聚合 `trial_results`，但 `TrialResult` 没有标准 `model_patch` 字段。

架构决定是：平台 Job→Harbor Job，评测运行→Harbor Trial，`n_attempts=1`、`n_concurrent_trials=1`、`verifier.disable=true`；每个 Trial 的 patch 由 Adapter 强校验后交给固定 SWE-Bench-Fork。完整输入、输出、错误和验收门槛只在 [`HARBOR_EXECUTION.md`](./HARBOR_EXECUTION.md) 维护。

静态核验不能证明 Harbor 已经在本机安装、任务能运行或 patch 能提取；当前状态仍是“架构已确认、运行待原型”。

## 7. Codex CLI Adapter

项目已确认首个真实原型使用 Harbor 内置 Codex Agent，认证采用评测机所有者本人通过 ChatGPT Pro 登录产生的 `auth.json`。该政策不等于容器内 Codex 已可运行；项目固定 CLI 版本、模型 ID、端点白名单、Token 刷新、脱敏、清理和网络策略仍须固定或实测。

### 7.1 已核验官方接口

OpenAI 官方将 `codex exec` 标为稳定的非交互/脚本运行入口：

- `PROMPT` 可直接传字符串；使用 `-` 时从 stdin 读取完整 prompt；
- `--cd/-C` 设定工作区根目录；
- `--sandbox` 支持 `read-only`、`workspace-write`、`danger-full-access`；
- `--ephemeral` 不把 session rollout 持久化到默认目录；
- `--json` 使 stdout 成为 JSONL 事件流；
- 官方列出的事件包括 `thread.started`、`turn.*`、`item.*` 和 `error`；item 可包括命令执行、文件修改、MCP 调用、Web 搜索和计划更新；
- `--output-last-message/-o` 可另存最终回答，但它不是最终 Git patch。

来源：[Codex Non-interactive mode](https://developers.openai.com/codex/noninteractive)、[Codex CLI reference](https://developers.openai.com/codex/cli/reference)，复核日期 2026-09-04。官方页面当前仍把 `codex exec` 列为稳定的非交互入口；本项目认证选择及秘密边界只在 [`CODEX_AUTHENTICATION.md`](./CODEX_AUTHENTICATION.md) 维护。

### 7.2 直接 CLI 后备映射

正式主路径优先使用 Harbor 已有 Codex Agent。以下映射保留为 Harbor Adapter 调试参考和 `ProcessExecutionAdapter` 后备方案，不代表首版同时维护两套 Codex 执行实现。

```text
Runner RunEnvelope
    → Adapter 生成只含 Issue 和约束的 prompt
    → codex exec --json --ephemeral --sandbox workspace-write --cd <repo> -
    → 捕获 JSONL/stdout、stderr、退出码和超时
    → 规范化公开事件
    → 从受控 Git 工作区提取 patch
    → Runner stdout 输出 patch
```

| 统一信息 | Codex 映射 |
|---|---|
| Issue 输入 | `codex exec -` 的 stdin |
| 仓库根 | `--cd` + 外层容器工作目录 |
| 可观察轨迹 | `--json` JSONL；保留原始事件并规范化 |
| 工具调用数 | 只统计官方输出中可识别的 item，保留事件类型 |
| patch | 从最终 Git 工作区提取，不取最终回答文本 |
| 超时/CPU/内存/网络 | Execution Backend 的环境策略；Codex 自身 sandbox 是第二层，不替代 Docker |
| 版本/模型/配置 | Agent Configuration 冻结并写入 `result.json` |

历史记录：2026-09-01 从旧工作区尝试 `codex --version` / `codex exec --help` 时，WindowsApps 中打包的 `codex.exe` 被操作系统拒绝启动。该结果不再作为当前宿主 CLI 状态。

当前宿主探针：2026-09-04 在 `E:\9.1agent_exam` 的提升权限只读 shell 中，`Get-Command codex` 解析到 `C:\Users\YINGYI\AppData\Roaming\npm\codex.ps1`；`codex --version` 返回 `codex-cli 0.142.0`，`codex exec --help` 正常输出，两个退出码均为 0。

限制：同一窗口的默认沙箱命令启动器在命令执行前返回 `setup refresh had errors`，而提升权限后探针成功；因此该故障应归入 Codex Windows 沙箱/宿主运行环境，不应误写为 CLI 命令失败。上述结果也没有固定项目 CLI 版本、验证真实账号、发起模型请求或证明 Harbor 容器内 Codex 可用。

## 8. Aider CLI Adapter

### 8.1 已核验官方接口

- `aider --message "..."` / `--message-file <file>` 会处理单条任务后退出；
- Aider 直接修改当前 Git 仓库，不原生输出纯 patch；
- 当前没有官方 JSON/JSONL/NDJSON 工具事件协议；人类终端输出不能硬解析成稳定工具调用流；
- Git 集成默认开启，`--auto-commits` 和 `--dirty-commits` 默认 true，可能让普通 `git diff` 为空或污染基线；
- `--no-auto-commits --no-dirty-commits --no-gitignore` 可关闭相关行为；
- `--chat-history-file`、`--llm-history-file`、`--input-history-file` 可把历史写到指定位置；
- CLI/config 有真实版本漂移，必须固定精确版本；不依赖官方明确不保证兼容的 Python scripting API。

完整来源和源码行号见 [`2026-09-01-aider-cli-interface.md`](../research/2026-09-01-aider-cli-interface.md)。

### 8.2 直接 CLI 后备映射

正式主路径优先使用 Harbor 已有 Aider Agent。以下映射只作为能力差异事实和后备实现参考。

```text
Runner stdin JSON
    → Adapter 把 Issue 写到仓库外 UTF-8 文件
    → 固定 cwd，调用 aider --message-file ...
    → 禁止自动提交/dirty commit/.gitignore 修改
    → 捕获终端文本、历史、退出码
    → 从 base commit 和最终工作区生成包含新文件的 patch
    → Runner stdout 输出 patch
```

| 统一信息 | Aider 映射/限制 |
|---|---|
| Issue 输入 | `--message-file`；Aider 本身不是 stdin 任务协议 |
| 仓库根 | 子进程 `cwd`；需隔离 HOME 和仓库内 Aider/.env 配置污染 |
| 可观察轨迹 | 原始终端/聊天/LLM history；没有官方结构化 tool-call 流 |
| 工具调用数 | 当前不能提供与 Codex/Claude 同口径的可靠统计；显示“不支持/未知” |
| patch | 关闭自动提交后，从一次性 Git 工作区统一提取 |
| 认证 | provider key 通过 secret 环境注入；不放命令行/历史 |

当前状态：只证明理论可接入；Aider 未在本机安装或运行。

## 9. Claude Code CLI Adapter

### 9.1 已核验官方接口

- `claude -p` 是非交互模式，支持 stdin；
- `--output-format stream-json --verbose` 可输出逐行结构化会话和工具事件；
- `--max-turns`、`--max-budget-usd`、`--tools` 提供轮数、预算和工具约束；
- 较新版本的 `--restricted` 明确面向 evaluation harness 共享机器场景，但仍需固定满足最低版本的 CLI 实测；
- 运行成功/失败、结果 subtype、usage、session、成本估算可观察；最终 patch 仍需从 Git 工作区提取；
- Claude Code 是受 Anthropic 条款约束的专有 CLI；平台不能收集或中转用户 Claude.ai session token，自动化认证与费用边界要按官方政策复核。

完整来源和许可/认证边界见 [`2026-09-01-claude-code-adapter.md`](../research/2026-09-01-claude-code-adapter.md)。

### 9.2 直接 CLI 后备映射

正式主路径优先使用 Harbor 已有 Claude Code Agent。以下映射只作为能力差异事实和后备实现参考。

```text
Runner RunEnvelope
    → 生成安全 prompt 并通过 stdin 交给 claude -p
    → stream-json + verbose 捕获公开消息/工具/usage
    → 外层 Docker + 候选 --restricted/工具 allowlist
    → 从 Git 工作区提取 patch
    → Runner stdout 输出 patch
```

| 统一信息 | Claude Code 映射 |
|---|---|
| Issue 输入 | `claude -p` stdin |
| 轨迹 | `stream-json + verbose`，保留原始 event/type/id |
| 工具调用数 | 由公开 `tool_use`/`tool_result` 事件统计；子 Agent 口径需实测 |
| 预算 | `--max-turns`、`--max-budget-usd` + 外层资源限制 |
| patch | Git 工作区提取，不取 `result` 自述 |
| 认证 | API key/官方支持凭据通过 secret 注入；不得保存用户 session token |

当前状态：官方接口证明理论可接入；本机没有检测到可运行 `claude`，尚未通过 Adapter 或真实账号测试。

## 10. P2 本地自研 Agent 接口

自研 Agent 已降为 P2，不是 MVP 完成条件；当前只保留扩展接缝。P2 首版只支持 Python，并直接实现 [`RUNNER_PROTOCOL.md`](./RUNNER_PROTOCOL.md) 的 stdin JSON → stdout patch 进程 Interface。平台拥有的包装负责把审核后的 Python 模块接入 Harbor；提交者不直接实现 Harbor `BaseAgent`，也不提交 shell 命令。完整 manifest 字段、Python 版本、依赖锁格式和 Harbor 包装 extension point 留待 P2 确认/实测。

P2 自研 Agent 必须固定 Git commit、登记模型提供方/模型和关键配置、在 Agent 沙箱运行、保存轨迹/日志、生成 patch，并由同一个 SWE-Bench-Fork Evaluator 判分。提供方只允许 DeepSeek/Kimi，二者形成独立 Agent Configuration；真实 Key 由评测机可信配置持有，不进入被测进程。它不能因为是“自己写的”就绕过沙箱、取得提供方 Key 或看到隐藏答案。

## 11. 统一能力差异

| 能力 | 自研进程 | Codex | Aider | Claude Code |
|---|---:|---:|---:|---:|
| 非交互单任务 | 由我们实现 | ✅ 官方 | ✅ 官方 | ✅ 官方 |
| 任务可从 stdin 直接读 | ✅ | ✅ | ❌，用 message file | ✅ |
| 官方结构化事件流 | 由我们定义 | ✅ JSONL | ❌ | ✅ stream-json |
| 可可靠统计公开工具调用 | 取决于自研实现 | ✅/待固定版本实测 | ❌ 当前无统一口径 | ✅/待子 Agent 口径实测 |
| 原生 stdout 是 patch | 可实现 | ❌ | ❌ | ❌ |
| 统一 Git patch 提取 | ✅ | Adapter | Adapter | Adapter |
| 真实账号/模型已测试 | 待自研 | ❌ | ❌ | ❌ |
| SWE-Gym E2E 已通过 | ❌ | ❌ | ❌ | ❌ |

因此页面不能把“工具调用数”当成所有 Agent 天然等价的指标。过程指标只展示、不参与排序；缺失值必须显示为“不支持/未知”，不能记成 0。

## 12. Adapter 错误映射

| 上游现象 | 统一终止原因 | 是否进入 Evaluator |
|---|---|---:|
| CLI/镜像不存在、认证缺失 | `agent_unavailable` | ❌ |
| 上游明确失败/非零退出且无可信完成结果 | `agent_failed` | ❌ |
| 外层达到墙钟超时 | `timed_out` | ❌ |
| 触发路径/网络/资源策略 | `sandbox_violation` | ❌ |
| Agent 正常结束，提取 diff 失败 | `patch_extraction_failed` | ❌ |
| 文本 patch 超过 1 MiB | `PATCH_TOO_LARGE` 无效 Agent 输出 | ❌ |
| 二进制 patch | `BINARY_PATCH_NOT_ALLOWED` 无效 Agent 输出 | ❌ |
| Agent 正常结束，补丁为空 | `completed` | ✅，记录 empty patch/unresolved |
| Agent 正常结束，有补丁 | `completed` | ✅ |

不能只看上游 exit 0：Aider/Codex/Claude 都可能正常结束但没有修好；也不能因为测试失败就把 Adapter 运行标成平台失败。

## 13. 接入验证顺序

每类 Agent 按同样四层推进，但进入开发的先后固定：

1. **官方接口/源码核验**：本文当前覆盖的级别。
2. **Adapter 契约测试**：用 Fake executable 验证参数、事件、退出、超时、patch 和脱敏，不消耗模型额度。
3. **真实 CLI 小仓库测试**：固定版本和真实凭据，在极小仓库完成一次修改。
4. **SWE-Gym E2E**：一条固定任务，保存 Runner 证据并由固定 SWE-Bench-Fork 判卷。

实现顺序为：Mock 只验证内部状态/错误分支 → M0 本机脚本用 Harbor 固定提交 + 真实 Codex 跑通单题 → M1 加入 Web/数据库/所有者批准形成 Codex 平台 MVP → Aider → Claude Code → P2 自研 Agent。Mock 和 M0 都不产生正式排行证据；P2 未定不阻塞 MVP。

## 14. 升级维护清单

升级任一框架/CLI 时必须在同一个行动文档中：

1. 记录旧/新精确版本和升级理由；
2. 查阅官方 changelog、CLI help 或源码；
3. 更新本文件的真实参数/事件/限制；
4. 保存新版 `--version` 和 `--help` 证据（秘密脱敏）；
5. 运行 Adapter 契约测试；
6. 至少运行小仓库冒烟测试，影响 Harness 时再跑 gold patch 与 E2E；
7. 只有证据通过后，才启用新的 Agent Configuration；历史成绩保留旧版本身份。

## 15. 当前未解决接口问题

1. `SWE-Gym/SWE-Gym-Lite` 的不可变 revision、真实 split 和 1～3 个首批任务；需实际读取数据集元数据，不能暗猜。
2. Windows + Docker Desktop 下 SWE-Bench-Fork 固定提交是否无需补丁即可运行；需 gold patch 实测。
3. Harbor 固定提交在本机的安装方式、Worker 载体、`model_patch` 受控提取和 Trial→`run_id` 映射。
4. 固定 Codex 项目 CLI 版本、模型 ID 和端点白名单，并验证 Harbor 容器内安装、ChatGPT 登录 Token 刷新、日志脱敏及成功/失败/超时清理路径；当前宿主 `0.142.0` 只是一条环境探针，不是已选基线。
5. Aider 仓库内 `.aider.conf.yml`/`.env` 的彻底隔离方式。
6. Claude Code `--restricted` 与评测所需工具组合、账号/费用/网络策略。
7. P2 `agent-exam.yaml` 的完整 schema、Python 版本、依赖锁格式，以及平台怎样把已确认进程 Interface 包装进 Harbor；不再待选 Harbor `BaseAgent` 或进程协议，且不阻塞 MVP。
8. P2 DeepSeek/Kimi 的精确模型/外部接口、受控访问部署和 Docker 网络防绕过；不得把“架构已确认”写成真实调用已通过。

## 16. 变更记录

- 2026-09-02：把依赖来源、固定版本、获取与入库策略迁移到 `DEPENDENCIES.md` 唯一维护；公开证据改用固定提交的 GitHub permalink，避免 `framework/` 不入库后链接失效。
- 2026-09-01：创建；核验固定 SWE-Gym/SWE-Bench-Fork 源码、Codex 官方非交互接口，并汇总 Aider/Claude Code 官方研究；定义四类 Adapter 映射、能力差异、错误映射和分层验证。
- 2026-09-03：加入固定 Harbor 的真实 Job/Trial/Verifier/Artifact 接口入口；确认 Harbor 为主 Execution Backend，直接 CLI 映射降为后备，运行状态仍保持待原型。
- 2026-09-04：确认首个真实原型使用 `SWE-Gym/SWE-Gym-Lite` 的 1～3 道任务；其 revision、split 和具体实例仍待真实元数据核验。
- 2026-09-04：确认首个真实原型 Agent 为 Harbor 内置 Codex；认证政策采用评测机所有者的 ChatGPT Pro `auth.json`，容器 CLI、模型、Token 生命周期和网络能力仍待实测。
- 2026-09-04：在新路径复测宿主 `codex --version` 与 `codex exec --help` 均成功；记录本机 `codex-cli 0.142.0`，但不将其自动固定为项目版本，也不据此宣称 Harbor 容器 E2E 通过。
- 2026-09-05：确认首版自研 Agent 只支持 Python stdin JSON → stdout patch 进程 Interface，由平台包装进 Harbor；模型提供方限 DeepSeek/Kimi，真实 Key 不进入被测进程，具体外部接口和隔离待实测。
- 2026-09-05：固定 M0 Codex 本机脚本→M1 Codex 平台 MVP→Aider/Claude Code→P2 自研 Agent 的验证顺序；过程指标改为只展示，并补充任务原始快照与无效 patch 映射。
