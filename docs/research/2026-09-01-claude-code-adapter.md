# Claude Code 黑盒评测 Adapter 可行性研究

> 核验日期：2026-09-01  
> 来源范围：只使用 Anthropic 官方文档及 `anthropics/claude-code` 官方仓库。  
> 当前状态：**理论可接入**；尚未完成真实账号 Adapter 测试，也尚未完成 SWE-Gym 端到端评测。  
> 本文是研究事实记录，不是已经确认的架构或实现方案。

## 1. 给初学者的结论

**评测 Claude Code 不需要拿到它的内部源码。**我们的平台可以像自动测试一个普通命令行程序一样，把官方 Claude Code CLI 安装到受控容器中，向它提交题目，记录它对文件和工具做了什么，最后提取代码补丁并交给 SWE-bench/SWE-Gym 测试器判分。

但要区分两件事：

- **黑盒评测**：只观察输入、输出、工具调用、文件变化、测试结果、耗时和资源；不需要知道 Claude Code 内部怎么实现。
- **白盒审核**：阅读并审查 Agent 的内部源码；这不是题目要求，也不能以官方 Claude Code 主实现已经开源为前提。

Anthropic 官方已经提供适合自动化的非交互接口：`claude -p`、标准输入、`json` / `stream-json` 输出、退出码、会话 ID、工具调用事件、usage 和成本估算。较新的 CLI 还提供专门面向 evaluation harness（评测执行器）的 `--restricted` 模式。因此从接口事实看，制作黑盒 Adapter 是可行的。[非交互运行文档](https://code.claude.com/docs/en/headless)、[CLI 参数文档](https://code.claude.com/docs/en/cli-reference)

## 2. 必须使用的三种成熟度表述

| 成熟度 | 含义 | 当前状态 |
|---|---|---:|
| 理论可接入 | 官方接口足以设计 Adapter，但还没有用真实 CLI 和凭据验证 | ✅ 已核实 |
| Adapter 测试通过 | 使用固定 Claude Code 版本和真实凭据，在小型测试仓库完成启动、工具调用、改文件、轨迹采集、补丁提取和异常处理 | ❌ 尚未验证 |
| SWE-Gym 端到端跑通 | 在真实 SWE-Gym 题目镜像运行 Claude Code，并由 FAIL_TO_PASS / PASS_TO_PASS 得出最终成绩 | ❌ 尚未验证 |

在第二、三级实际通过前，文档和答辩只能说“官方接口支持、理论可接入”，不能说“已经支持 Claude Code”。

## 3. 公开仓库不等于 CLI 主实现开源

### 已核实事实

- Anthropic 有公开的 [`anthropics/claude-code`](https://github.com/anthropics/claude-code) 仓库，其中能看到安装说明、插件、示例、开发容器、变更日志和问题跟踪材料。
- 该仓库的官方许可证不是 MIT、Apache-2.0 等开源许可证，而是“© Anthropic PBC. All rights reserved”，使用受 Anthropic 条款约束。[官方 LICENSE](https://github.com/anthropics/claude-code/blob/main/LICENSE.md)
- 官方法律文档把 Claude Code 的使用分别置于商业条款或消费者条款下；如果在产品或托管沙箱中预装/运行 Claude Code，必须使用 Anthropic 发布的原始二进制，不得修改，并遵守官方列出的认证和计费条件。[法律与合规文档](https://code.claude.com/docs/en/legal-and-compliance)

### 准确表述

可以说：

> Claude Code 是 Anthropic 发布的专有 CLI；官方公开仓库包含可公开查看的插件、示例、配置和发布材料，但不能把它描述成“CLI 主实现的开源源码仓库”。

不应说“Claude Code 什么都没公开”，因为插件、示例和开发容器确实公开；也不应因为仓库是 public 就说“Claude Code 已经开源”。

### 对本项目的意义

Agent Adapter 依赖的是官方可执行程序和机器接口，而不是内部源码：

```text
题目输入 → 官方 claude 命令 → 工作区文件变化 + 结构化事件 → Adapter 提取补丁
```

因此，Agent 是否开源和 Agent 是否能被黑盒评测是两个独立问题。

## 4. 官方非交互接口

### 4.1 启动和输入

- `claude -p "任务"`（`-p` 等价于 `--print`）会非交互运行并在结束后退出。[官方 headless 文档](https://code.claude.com/docs/en/headless)
- 非交互模式可从 stdin 读取内容，所以 Runner 可以把 Issue 题目通过标准输入传入；也可以把提示放在命令行参数中。官方说明管道输入上限为 10 MB，超过后会报错并以非零状态退出。[官方管道输入说明](https://code.claude.com/docs/en/headless#pipe-data-through-claude)
- `--input-format` 支持 `text` 和 `stream-json`；单道 SWE-Gym 题目首版使用文本输入即可，持续多轮控制才需要 `stream-json`。[CLI 参数文档](https://code.claude.com/docs/en/cli-reference)

### 4.2 输出格式

`--output-format` 官方支持：

- `text`：普通文本；
- `json`：一次性 JSON，包含最终结果、session ID 和元数据；
- `stream-json`：逐行 JSON（NDJSON），适合实时收集轨迹。

`stream-json` 的最后一行是 `result` 消息，包含最终响应、成本和会话元数据。使用 `--verbose` 可以取得完整逐轮消息；如还需要 token 级增量，可增加 `--include-partial-messages`。[结构化输出和流式输出](https://code.claude.com/docs/en/headless#get-structured-output)

### 4.3 退出和失败信息

- 正常成功退出码为 `0`，运行失败为非零；无效参数在启动前写入 stderr。[官方基本用法](https://code.claude.com/docs/en/headless#basic-usage)
- 运行中的失败（例如未认证）会作为 stdout 上的结果输出，因此 Adapter 不能只看 stderr；必须同时解析结果事件和进程退出码。
- 收到 SIGTERM 时官方记录的退出码是 `143`，并会终止仍在运行的 Bash 进程树；这可供外部超时控制器区分“平台终止”和“Agent 自己结束”。[SIGTERM 行为](https://code.claude.com/docs/en/headless#stop-a-run-with-sigterm)
- Agent SDK 的结果类型区分 `success`、`error_max_turns`、`error_max_budget_usd`、`error_during_execution`、结构化输出失败等；结果还携带 `stop_reason`。CLI 的 print mode 建立在同一 Agent SDK 接口之上，可据此设计错误分类，但最终字段必须以固定 CLI 版本的真实输出为准。[Agent loop 与 ResultMessage](https://code.claude.com/docs/en/agent-sdk/agent-loop)

## 5. CI、容器、认证与权限

### 5.1 可以在 CI 和容器中运行

Anthropic 官方明确把 `claude -p` 用于脚本和 CI/CD，并提供官方开发容器指南。开发容器允许 Claude Code、项目依赖和命令都在容器内运行；官方参考容器还包含网络出口防火墙示例。[非交互运行](https://code.claude.com/docs/en/headless)、[开发容器](https://code.claude.com/docs/en/devcontainer)

为了成绩可复现，应记录 `claude -v` 并固定 CLI 版本、关闭自动更新。官方容器文档说明可以安装指定版本并设置 `DISABLE_AUTOUPDATER`；不能让同一排行榜中的运行自动漂移到不同版本。[容器中的版本固定说明](https://code.claude.com/docs/en/devcontainer#enforce-organization-policy)

### 5.2 认证方式

官方支持的自动化认证包括：

- `ANTHROPIC_API_KEY`：Claude Console API key；`-p` 模式存在时会直接使用；
- `apiKeyHelper`：由外部脚本动态提供或轮换 API key；
- `CLAUDE_CODE_OAUTH_TOKEN`：由 `claude setup-token` 生成，适合账号自己的 CI/脚本；
- Amazon Bedrock、Google Cloud Agent Platform、Microsoft Foundry 的提供商凭据。

需要注意：推荐用于脚本的 `--bare` 模式不会读取订阅 OAuth 或系统钥匙串，只读取 `ANTHROPIC_API_KEY`、`apiKeyHelper` 或云提供商凭据。[认证优先级与 setup-token](https://code.claude.com/docs/en/authentication)、[bare mode](https://code.claude.com/docs/en/headless#start-faster-with-bare-mode)

### 5.3 托管平台的认证合规边界

这是本项目容易忽略的限制：Anthropic 官方说明，第三方产品不能向用户提供自制的 Claude.ai 登录，也不能收集、保存或中转 Claude.ai session token；产品开发应使用 API key 或受支持的云提供商凭据。若在托管沙箱中运行 Claude Code，默认还要求每个最终用户使用自己的凭据并由凭据所有者直接承担使用费用，除非另有商业协议。[官方法律与认证要求](https://code.claude.com/docs/en/legal-and-compliance#can-customers-offer-claude-code-in-their-products)

对课程内部原型而言，可以研究“由团队自己的 Console API key 为团队授权成员运行”的方式，但是否符合具体账号条款仍应由凭据所有者确认；本文不是法律意见。平台绝不能把真实 key/token 写进日志、轨迹或 MinIO 制品。

### 5.4 权限和安全选项

- `--allowedTools` / `--disallowedTools` 控制免询问或禁止的工具；`--tools` 可以限制本次会话实际可见的内置工具。[CLI 参数文档](https://code.claude.com/docs/en/cli-reference)
- `--max-turns` 和 `--max-budget-usd` 可限制非交互运行的轮数与成本。[CLI 参数文档](https://code.claude.com/docs/en/cli-reference)
- `dontAsk` 模式适合 CI 的明确 allowlist：凡是仍需询问的调用会自动拒绝，进程不会卡在等待人工输入。[权限模式文档](https://code.claude.com/docs/en/permission-modes#allow-only-pre-approved-tools-with-dontask-mode)
- `--restricted`（官方标注需 Claude Code v2.1.248 或更高）明确用于 evaluation harness 驱动共享机器的场景：默认移除执行命令/代码和 WebFetch 等工具，只允许显式重新加入；文件工具被限制在工作目录；只加载 managed settings 与 `--settings`；并拒绝 `bypassPermissions`。[`--restricted` 官方定义](https://code.claude.com/docs/en/cli-reference)
- `--dangerously-skip-permissions` 不应在宿主机使用；官方只建议在隔离容器/VM 且无互联网时使用。它不能和 `--restricted` 同时使用。[权限模式安全说明](https://code.claude.com/docs/en/permission-modes#skip-all-checks-with-bypasspermissions-mode)

Docker 本身不自动等于安全。官方明确提醒：恶意项目仍可能读取容器内可访问的凭据并通过允许的网络外传。需要外部 CPU/内存/进程/磁盘/超时限制、非 root 用户、最小挂载和网络出口白名单；这些不是 Claude Code Adapter 单独能完成的。[开发容器安全说明](https://code.claude.com/docs/en/devcontainer)

## 6. 可采集的评测证据

使用 `stream-json + verbose`，官方接口能够提供：

| 证据 | 官方可用性 | 使用边界 |
|---|---:|---|
| 会话 ID、模型、工具列表、MCP/插件状态 | ✅ | `system/init` 事件；适合记录运行配置 |
| Agent 文本消息 | ✅ | 只代表可观察输出，不等于模型全部内部思维 |
| `tool_use` 的工具名、ID和输入 | ✅ | 可统计调用次数、重复调用和调用参数 |
| `tool_result`、错误和输出 | ✅ | 可与 `tool_use_id` 关联 |
| 子 Agent 调用关系 | ✅/依版本 | `parent_tool_use_id` 可重建父子关系；完整转发需固定满足文档要求的 CLI 版本 |
| 最终结果与成功/错误 subtype | ✅ | 仍要结合退出码、外部测试和平台状态判断 |
| `usage`、轮数、session ID、`stop_reason` | ✅ | ResultMessage 提供 |
| `total_cost_usd` 和按模型拆分 | ✅（估算） | 官方强调是客户端估算，不是权威账单，不能用于向用户计费 |
| 工具耗时、成功状态、命令/文件路径 | ✅/可选 | 可通过官方 OpenTelemetry；详细内容受隐私开关和截断限制 |
| 最终 Git 补丁 | ◐ 外部采集 | Claude Code 修改工作区；Adapter 需在结束后由 Git 生成 patch |
| FAIL_TO_PASS / PASS_TO_PASS | ◐ 外部判定 | 由 SWE-bench/SWE-Gym verifier 运行，不应让 Claude Code 自报成绩 |

事件结构见[Agent loop 消息类型](https://code.claude.com/docs/en/agent-sdk/agent-loop)；成本字段与误差边界见[成本追踪](https://code.claude.com/docs/en/agent-sdk/cost-tracking)；额外工具指标见[OpenTelemetry 监控](https://code.claude.com/docs/en/monitoring-usage)。

“全程可追溯”应解释为可追溯公开消息、工具请求、工具结果、文件变化和测试证据，不能宣称平台获得了 Claude 未输出的内部思维链。

## 7. 黑盒 Adapter 的候选工作方式

以下是基于官方接口的可行性推导，不代表命令已经实测：

```text
1. Runner 创建固定 SWE-Gym 题目容器和干净仓库快照
2. Adapter 记录 Claude Code/模型/题目/镜像/配置版本
3. 通过 stdin 把 Issue 交给 claude -p
4. 捕获 stream-json、stderr、退出码和超时信号
5. Claude Code 在受限工作区中读取、修改和运行允许的命令
6. Adapter 在进程结束后提取包含新文件的 Git patch
7. 在独立验证阶段运行 FAIL_TO_PASS / PASS_TO_PASS
8. 保存轨迹、补丁、测试日志、usage 和资源数据
```

候选启动参数组合可以围绕以下官方参数构造：

```text
claude --restricted -p
  --output-format stream-json
  --verbose
  --tools <明确允许的工具>
  --max-turns <上限>
  --max-budget-usd <上限>
  --model <固定完整模型ID>
  --no-session-persistence
```

实际实现时由 Adapter 捕获 Claude 的 stdout 作为轨迹制品，随后再把外部生成的 Git patch 作为统一 Runner 的 stdout。也就是说：

> Claude Code 原生接口不是“stdout 只输出补丁”；“stdin 题目 → stdout 补丁”是我们自己的 Adapter 契约。

这样既复用官方接口，又不要求修改 Claude Code 二进制。

## 8. 仍需真实账号验证的项目

达到“Adapter 测试通过”之前至少要实际验证：

1. 团队可用的 Claude Code 账号/API key、计费额度、模型权限和所在网络。
2. 选定 CLI 固定版本能否使用 `--restricted`，以及该模式与所需 Bash/Read/Edit/Write 工具的组合。
3. 在 Docker 非 root 用户中能否无交互认证，凭据是否会泄露给工具子进程或日志。
4. 网络白名单既允许 Claude API，又阻止题目代码任意联网时，CLI 是否能稳定运行。
5. `stream-json` 的真实事件样本、结果 subtype、stderr 和退出码是否与解析器假设一致。
6. 工具调用数是否包含子 Agent；usage 是否因子 Agent 出现口径差异。
7. 外部超时发送 SIGTERM 后，Claude 的子进程是否全部退出，轨迹是否完整落盘。
8. Git patch 是否正确包含修改、删除、二进制文件和新建文件。

达到“SWE-Gym 端到端跑通”还需再验证：

1. 选择一条小型 SWE-Gym 实例并准备对应 Docker 镜像。
2. 在该镜像或相容的双容器流程中安装固定 Claude Code 版本。
3. 完成一次真实 Issue → Agent 修改 → patch → verifier 测试。
4. 保存 FAIL_TO_PASS、PASS_TO_PASS、轨迹、补丁、成本和资源证据。
5. 重复同一配置，确认结果可复现或至少能够解释随机差异。

## 9. 最终事实判断

- **不需要 Claude Code 开源源码才能评测。**官方 CLI 已具备黑盒自动化所需的启动、输入、结构化事件和结果接口。
- **理论上可以实现本题要求的 Claude Code Adapter。**特别是官方 `--restricted` 已明确提到 evaluation harness 场景。
- **Claude Code 不会天然按我们的统一 Runner 契约只向 stdout 输出 Git patch。**Adapter 必须捕获其机器输出，并从工作区独立生成补丁。
- **目前不能说 Adapter 已经测试通过。**缺少真实 CLI 版本、真实凭据和测试仓库运行证据。
- **更不能说 SWE-Gym 已经端到端跑通。**这需要在真实题目镜像中完成一次由确定性测试判分的运行。
- **认证合规可能影响产品边界。**课程内部自测和向外部用户提供托管 Claude Code 是不同场景，后者必须按 Anthropic 官方商业及逐用户认证要求重新确认。
