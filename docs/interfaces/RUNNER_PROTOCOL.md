# 自研 Agent / 后备进程 Runner 协议

> 文档状态：候选 v0.1，尚未实现；不是正式 Harbor 接口
>
> 最后更新：2026-09-03
> 权威范围：本文件只维护自研 Agent 或 Harbor 验收失败时 `ProcessExecutionAdapter` 使用的跨进程协议。正式主路径见 [`HARBOR_EXECUTION.md`](./HARBOR_EXECUTION.md)；真实上游接口见 [`FRAMEWORK_INTERFACES.md`](./FRAMEWORK_INTERFACES.md)。

## 1. 一句话解释

如果某个自研 Agent 采用独立进程方式，平台用一种简单协议调用它：**stdin 输入一份 JSON 任务，stdout 只接收 Git 补丁**。这不是 Harbor 内置 Codex/Aider/Claude Code 的原生用法，也不要求 Harbor 为迁就本协议而改造。

## 2. 协议边界

```mermaid
flowchart LR
    O[ExecutionBackend seam] --> P[ProcessExecutionAdapter]
    P -->|stdin: RunEnvelope JSON| A[自研 Agent wrapper]
    A -->|自研进程接口| G[自研 Agent]
    G --> A
    A -->|stdout: unified diff| O
    A -->|stderr: 诊断| LOG[原始日志制品]
    A -->|trajectory.jsonl + result.json| ART[制品目录]
```

适用方式：

- 对本地自研 Agent：是否采用本协议或 Harbor `BaseAgent` 适配，待 `agent-exam.yaml` schema 讨论后确定。
- 对 Codex/Aider/Claude Code：正式主路径复用 Harbor 已有 Agent，不经过本文 stdin/stdout wrapper。
- 对后备实现：`ProcessExecutionAdapter` 可把项目类型化对象序列化为本文格式，但对外仍实现统一 `ExecutionBackend` interface。

## 3. 进程启动约定

| 项目 | 候选 v0.1 |
|---|---|
| 当前工作目录 | 已准备好的任务仓库根目录 |
| stdin | 一个 UTF-8 JSON 对象，读到 EOF；最大尺寸由平台限制 |
| stdout | 只允许 UTF-8 Git unified diff；不得包含 Markdown 围栏、解释或进度日志 |
| stderr | 人类可读诊断；平台完整捕获、脱敏并保存 |
| 环境变量 | `EVAL_JOB_ID`、`EVAL_RUN_ID`、`EVAL_ARTIFACT_DIR`、`EVAL_PROTOCOL_VERSION`；由 wrapper 注入，Agent 不得覆盖 |
| secret | 通过沙箱的 secret 注入机制提供，不进入 stdin、命令行、环境快照、轨迹或制品 |
| 超时 | `ProcessExecutionAdapter` 所属 Execution Backend 强制执行；Agent 自报超时不能替代外层限制 |

`stdout` 为空并不自动表示平台错误：它可能表示 Agent 正常结束但没有修改代码。Evaluator 应把空补丁记录为未解决，而不是把它伪装成 Runner 崩溃。

## 4. stdin：`RunEnvelope`

示例只表达字段语义，不代表已经有对应代码：

```json
{
  "protocol_version": "0.1",
  "job_id": "job_01J...",
  "run_id": "01J...",
  "task": {
    "instance_id": "django__django-12345",
    "dataset_id": "SWE-Gym/SWE-Gym",
    "dataset_revision": "fixed-revision",
    "split": "train",
    "repo": "django/django",
    "base_commit": "0123456789abcdef",
    "problem_statement": "Issue 原文"
  },
  "agent": {
    "configuration_id": "codex-example-config",
    "adapter_type": "codex",
    "agent_version": "fixed-version",
    "model": "fixed-model",
    "public_options": {
      "reasoning_effort": "fixed-value"
    }
  },
  "evaluation_policy": {
    "evaluation_track": "closed_book",
    "network_policy_id": "provider-only-v1",
    "tool_profile_id": "no-web-tools-v1"
  },
  "limits": {
    "wall_time_seconds": 1800,
    "cpu_cores": 2,
    "memory_mib": 4096,
    "pids": 256,
    "max_output_bytes": 10485760
  }
}
```

### 4.1 必需字段

| 字段 | 类型 | 生产者 | 约束 |
|---|---|---|---|
| `protocol_version` | string | Job Orchestrator / Process Adapter | 首版固定为 `0.1`；不支持时应拒绝，不静默猜测 |
| `job_id` | string | Job Repository | 所属平台评测 Job；与运行映射一致 |
| `run_id` | string | Run Repository | 全链路追溯 ID；与环境变量一致 |
| `task.instance_id` | string | Task Catalog | 必须能在冻结的数据集版本中唯一定位任务 |
| `task.dataset_id` | string | Task Catalog | Hugging Face 数据集 ID 或项目登记的本地数据集 ID |
| `task.dataset_revision` | string | Task Catalog | 必须冻结到可复查的 revision/校验值，不能只写 `latest` |
| `task.split` | string | Task Catalog | 例如 SWE-Gym 的真实 split；由数据源核验 |
| `task.repo` | string | Task Catalog | 上游仓库身份，用于审计，不允许 Adapter 自行替换 |
| `task.base_commit` | string | Task Catalog | 当前工作区必须与它对应 |
| `task.problem_statement` | string | Task Catalog | Agent 实际收到的 Issue 文本 |
| `agent.configuration_id` | string | Agent Registry | 必须已登记且启用 |
| `agent.adapter_type` | enum | Agent Registry | `custom_process`、`codex`、`aider`、`claude_code` |
| `agent.agent_version` | string | Agent Registry | 固定 Agent/CLI 版本；无法取得时不得进入正式排行 |
| `agent.model` | string | Agent Registry | 固定模型身份；本地 Agent 不使用模型时可采用明确的 `none` |
| `agent.public_options` | object | Agent Registry | 只允许该 Adapter 预先声明的键；不得接受 shell 命令或秘密 |
| `evaluation_policy.evaluation_track` | enum | Job Submission | `closed_book` 或 `open_book_experimental`；运行中不可切换 |
| `evaluation_policy.network_policy_id` | string | Policy Registry | 已登记网络规则；不接受任意代理地址或防火墙命令 |
| `evaluation_policy.tool_profile_id` | string | Policy Registry | 已登记工具集合；Adapter 只能暴露对应工具 |
| `limits.*` | number/string | Job Submission | 来自平台限制模板，用户输入只能在允许范围内选择 |

### 4.2 绝对禁止进入 Agent 输入的内容

- 数据集 gold `patch`；
- `test_patch`；
- `FAIL_TO_PASS`、`PASS_TO_PASS` 的隐藏判分答案或测试清单；
- 其他 Agent 的补丁、Judge 结论或人工复核答案；
- 数据库连接串、MinIO 密钥、模型 API key、宿主机环境变量快照；
- Runner 在宿主机上的任意可执行命令或 Docker Socket。

这些内容可以由 Patch Evaluator 在独立验证阶段使用，但不能泄漏给被测 Agent。

### 4.3 评测赛道与两层联网控制

| 赛道 | 工具层 | 网络层 | 排行 |
|---|---|---|---|
| `closed_book` | 禁用 Web 搜索、抓取、浏览器及未登记联网工具 | 只放行模型调用所需端点；其余一般外网拒绝 | 核心主排行榜 |
| `open_book_experimental` | 开放已登记联网工具，并记录实际工具/版本 | 按实验网络策略放行并保存访问证据 | 独立实验榜 |

工具层和网络层缺一不可：关闭 WebSearch 不代表 Agent 不能用 shell 执行 `curl`；容器能访问模型供应商，也不代表必须允许它访问 GitHub。宿主机代理是否能用不能靠猜，必须在 Docker/WSL 环境实际验证。

两条赛道使用完全相同的 patch 提取和 SWE-Bench-Fork 确定性判卷。开卷并不是降低通过标准，只是允许的取证手段不同，因此成绩不得与闭卷混合。

开卷实验榜究竟提供统一的平台 Web 工具，还是允许各 Agent 原生工具，仍待用户确认。无论哪种，都必须冻结 `network_policy_id` 和 `tool_profile_id`；“国产/国外”不是接口能力字段。

## 5. stdout：补丁输出

### 5.1 格式

- UTF-8 文本；
- Git unified diff；
- 允许多文件、删除文件和二进制补丁；
- 不允许 Markdown 的 ```` ```diff ```` 围栏；
- 不允许前后解释文字；
- 允许 0 字节，表示“正常结束但没有补丁”。

示例：

```diff
diff --git a/example.py b/example.py
index 1111111..2222222 100644
--- a/example.py
+++ b/example.py
@@ -1 +1 @@
-old_value = 1
+new_value = 2
```

### 5.2 为什么不直接信任 Agent 最后一段回答

第三方 Agent 的最终文字可能包含解释、代码块，甚至没有完整列出它已经写入工作区的文件。因此专用 Adapter 的统一提取流程应是：

1. 运行前确认仓库对应固定 `base_commit`，并记录初始工作区状态；
2. Agent 退出后读取 `git status --porcelain`；
3. 对允许范围内的未跟踪文件执行 intent-to-add，使新文件进入 diff，但不提交；
4. 从固定基线执行 `git diff --binary --no-ext-diff`；
5. 拒绝 `.git`、秘密路径、超大文件和越界路径；
6. 把原始 diff 保存为 patch 制品，并把完全相同的字节写到 Runner stdout；
7. 最终正确性仍由干净 SWE-Bench-Fork 验证环境判断。

精确 Git 命令和跨平台路径行为必须在实现行动文档中通过测试固定；这里不把未经测试的命令拼装写成“已实现”。

## 6. stderr：诊断输出

stderr 只用于诊断，不能作为补丁或得分输入。必须：

- 完整捕获并保存为原始日志制品；
- 在入库前脱敏 API key、Authorization header、连接串和临时 token；
- 设置字节上限，超限时记录截断事实和原始总量；
- 保留上游 CLI 原始退出码和 Adapter 错误分类；
- 前端默认不直接展示可能含秘密的原始 stderr，只展示安全摘要。

## 7. 退出码和终止原因

以下是本项目 Adapter wrapper 的候选退出码，不是第三方 CLI 的原生退出码：

| Runner 退出码 | `result.json` 终止原因 | 含义 |
|---:|---|---|
| `0` | `completed` | Adapter 正常完成；stdout 可以是有效 diff 或空 |
| `2` | `invalid_request` | stdin、协议版本或登记配置无效 |
| `10` | `agent_unavailable` | CLI/镜像/模型/认证不可用，Agent 未正常开始 |
| `11` | `agent_failed` | 上游 Agent 非零退出或报告执行失败 |
| `12` | `timed_out` | 外层限制到期并终止进程树 |
| `13` | `patch_extraction_failed` | Agent 可能运行过，但无法安全生成统一 diff |
| `14` | `sandbox_violation` | 触发网络、挂载、路径或资源策略拒绝 |
| `20` | `adapter_internal_error` | Adapter 自身未预期错误 |

上游退出码必须另存为 `upstream_exit_code`，不能直接冒充统一 Runner 退出码。例如 Claude Code 的特定退出码、Aider 的退出码和 Codex 事件失败都先由各自 Adapter 解释，再映射到本表。

## 8. 旁路制品目录

`EVAL_ARTIFACT_DIR` 指向本次运行专用、Runner 可写而其他运行不可见的目录。候选文件：

```text
<EVAL_ARTIFACT_DIR>/
├─ trajectory.jsonl
│  # 规范化可观察事件；不包含私密思维链
├─ upstream.stdout.log
│  # 第三方 CLI 原始 stdout；Codex/Claude 的 JSONL 在这里保真保存
├─ upstream.stderr.log
│  # 第三方 CLI 原始 stderr；入库前经过秘密扫描/脱敏
├─ result.json
│  # Adapter 终止原因、上游退出码、耗时、版本和制品摘要
└─ patch.diff
   # 与 Runner stdout 字节一致的最终补丁副本
```

自研 Agent 若直接实现协议，可以不生成 `upstream.*`；但 `trajectory.jsonl`、`result.json` 和 `patch.diff` 仍必须由 wrapper 补齐。

## 9. `result.json`

```json
{
  "protocol_version": "0.1",
  "job_id": "job_01J...",
  "run_id": "01J...",
  "evaluation_track": "closed_book",
  "network_policy_id": "provider-only-v1",
  "tool_profile_id": "no-web-tools-v1",
  "termination_reason": "completed",
  "runner_exit_code": 0,
  "upstream_exit_code": 0,
  "started_at": "2026-09-01T10:00:00Z",
  "finished_at": "2026-09-01T10:03:20Z",
  "duration_ms": 200000,
  "patch_bytes": 1234,
  "patch_sha256": "hex-value",
  "trajectory_events": 42,
  "tool_calls": 8,
  "usage": {
    "input_tokens": 1000,
    "output_tokens": 200,
    "reported_by": "upstream"
  },
  "warnings": []
}
```

规则：

- 上游未提供的字段写 `null` 或省略，不能估算后伪装成官方数据；
- `tool_calls` 只统计可观察并成功解析的调用，不能推断隐藏内部动作；
- token 口径随供应商不同，必须带 `reported_by`，排行榜不能默认横向等价；
- `patch_sha256` 必须与 `patch.diff` 和 stdout 的实际字节一致。

## 10. `trajectory.jsonl`

每行一个事件：

```json
{"sequence":1,"occurred_at":"2026-09-01T10:00:01Z","source":"codex","type":"lifecycle","raw_type":"thread.started","payload":{"session_id":"safe-id"},"redactions":[]}
```

候选公共字段：

| 字段 | 含义 |
|---|---|
| `sequence` | 从 1 开始的本运行严格递增序号 |
| `occurred_at` | 平台观察到事件的 UTC 时间；上游时间可另存 |
| `source` | `runner`、`codex`、`aider`、`claude_code`、`custom_process`、`sandbox` |
| `type` | `lifecycle`、`agent_message`、`tool_call`、`tool_result`、`command`、`file_change`、`usage`、`warning`、`error` |
| `raw_type` | 上游原事件类型；没有则为 `null` |
| `payload` | 允许公开的结构化载荷；字段随 `type` 变化 |
| `redactions` | 本事件移除过哪些敏感类别，不保存原秘密 |

明确不采集：模型隐藏思维链、系统密钥、完整环境变量、宿主机无关文件内容。平台只评估可观察行动和结果。

## 11. 一次调用的状态解释

```mermaid
stateDiagram-v2
    [*] --> validating_input
    validating_input --> starting_agent: 输入与登记有效
    validating_input --> failed: invalid_request
    starting_agent --> running
    starting_agent --> failed: agent_unavailable
    running --> extracting_patch: Agent 正常退出
    running --> failed: agent_failed / timed_out / sandbox_violation
    extracting_patch --> completed: diff 或空补丁已固定
    extracting_patch --> failed: patch_extraction_failed
    completed --> [*]
    failed --> [*]
```

Runner 的 `completed` 只表示“运行流程正常拿到了一个补丁结果”，不表示题目解决。只有 Patch Evaluator 能生成 `resolved=true/false`。

## 12. Process Adapter 验收清单

每个使用本文协议的自研 Agent wrapper 和 `ProcessExecutionAdapter` 都必须通过同一组契约测试：

1. 能读取合法 stdin，并拒绝未知协议版本和额外危险选项。
2. stdout 只有 diff；上游聊天和日志没有混入。
3. 修改、创建、删除文件均能出现在 patch 中；空修改得到 0 字节 patch。
4. 上游非零退出、外层超时、认证缺失、补丁提取失败映射正确。
5. 原始 stdout/stderr、规范化轨迹、结果摘要和 patch 可由同一 `run_id` 追溯。
6. 轨迹事件按序、可解析、脱敏；工具调用统计能由 JSONL 重算。
7. Agent 看不到 gold patch、隐藏测试和其他运行制品。
8. 运行结束后没有遗留 Agent 子进程；沙箱清理失败会显式记录。
9. patch 在干净工作区能够进入 SWE-Bench-Fork；是否通过测试另行判定。
10. 闭卷配置不会暴露 Web 工具且一般外网不可达；开卷事件能追溯实际工具和访问证据；两条赛道的结果不会混分。

## 13. 兼容性和版本升级

- `protocol_version` 使用主版本/次版本语义；不兼容字段变化提升主版本。
- Adapter 必须记录自身版本、上游 CLI 版本和配置指纹。
- 新字段默认只能追加为可选字段；旧 Runner 不认识的危险行为字段必须拒绝。
- 自研 Agent/wrapper 升级先更新登记版本与 manifest，再跑契约测试，最后才能更新 Agent Configuration。

## 14. 仍待确认/待实测

1. stdin 最大字节数和 stdout patch 最大字节数的具体默认值。
2. 首版是否允许二进制补丁；允许会增加 MinIO 和 Harness 验证成本。
3. secret 使用 Docker secret、临时只读文件还是宿主进程注入；不得在文档未确认前写死。
4. 各真实 Agent 的 token 与工具事件能否稳定映射；以固定版本实测为准。
5. Windows 宿主 + Linux 容器下 intent-to-add 和路径安全检查的精确实现。
6. `provider-only-v1` 在 Docker Desktop 下通过何种代理/防火墙可靠执行。
7. 开卷使用平台统一 Web 工具还是 Agent 原生工具，以及访问证据的统一最小字段。

## 15. 变更记录

- 2026-09-01：创建候选 v0.1；确定 JSON stdin、纯 patch stdout、诊断 stderr、旁路制品、统一错误映射、轨迹事件和防泄漏规则。
- 2026-09-02：加入闭卷/开卷评测赛道、网络策略和工具配置；明确工具层与网络层双重治理和严格分榜。
- 2026-09-03：正式主路径改为 Harbor Execution Backend；本文收窄为自研 Agent/后备 Process Adapter 协议，并加入 `job_id` 追溯。
