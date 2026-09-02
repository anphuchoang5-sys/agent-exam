# Aider CLI 黑盒接入接口核验

- 调研日期：2026-09-01
- 研究范围：Aider 官方网站、Aider 官方 GitHub 仓库中的当前文档与源码
- 当前验证级别：**只完成官方资料核验；未安装、未运行 Aider，也未做 SWE-Gym 端到端测试**
- 目的：判断本项目能否把 Aider 当作一个“给定 Issue 与仓库快照，运行一次，最后收集补丁”的黑盒 Agent

## 1. 结论先行

**Aider 理论上可以接入，而且它的单次非交互入口比交互式终端工具更直接。**官方明确提供 `--message` 和 `--message-file`：发送一条自然语言任务、处理回复、修改文件，然后退出。

但它**没有被官方定义为“stdin 输入任务、stdout 只输出补丁”的协议**。当前 CLI 输出是面向人的终端文本；错误、警告、普通提示和模型回答在源码中使用同一个 Rich Console，未看到稳定的 JSON/NDJSON 事件协议。最终补丁应从隔离仓库的 Git 状态提取，不能从 stdout 猜，也不能仅依赖进程退出码。

另一个容易踩坑的事实是：Aider 默认自动提交修改、默认可能提交原有脏改动、默认检查并可能修改 `.gitignore`，聊天历史默认也在仓库内。因此 Adapter 必须主动固定这些行为，否则可能出现“Agent 明明改了代码，但 `git diff` 为空”或“评测补丁混入 Aider 自己的历史文件”的情况。

## 2. 证据标记

- **官方已证明**：官方文档明确说明，或官方当前源码直接实现。
- **合理推断**：根据已证明的接口设计出的 Adapter 做法，但不是 Aider 官方承诺的评测协议。
- **需要实测**：必须安装固定版本、使用真实模型账号并在容器中运行后才能确认。

## 3. 非交互调用与任务输入

### 3.1 官方已证明

1. `aider --message "..." <files...>`（别名 `--msg`、`-m`）会发送一条消息、处理回复并退出，关闭聊天模式。
2. `aider --message-file <file>`（别名 `-f`）会从文件读取消息、处理回复并退出。
3. 位置参数或可重复的 `--file FILE` 用于把文件作为可编辑文件加入会话；可重复的 `--read FILE` 用于加入只读材料。
4. 官方 scripting 页面同时展示 Python 调用方式，但明确警告：Python scripting API 没有正式支持或文档保证，未来版本可以不保持向后兼容。

来源：[Scripting aider](https://aider.chat/docs/scripting.html)、[当前 CLI 参数源码](https://github.com/Aider-AI/aider/blob/main/aider/args.py#L623-L641)

### 3.2 对本项目的合理推断

优先使用 `--message-file`，不要把 Issue 长文本拼进 shell 命令：这样可以避免引号、换行、特殊字符和命令长度问题。任务文件应放在仓库外的运行制品目录，编码固定为 UTF-8。

Aider 的 CLI 不是 stdin 协议，所以本项目统一 Runner 应做一层很薄的转换：

```text
Runner 标准输入中的任务 JSON
        ↓ Adapter 写入 UTF-8 临时文件
aider --message-file <task-file>
        ↓ Aider 直接修改隔离仓库
Adapter 从 Git 状态生成 patch，再按统一协议输出
```

不要由 Adapter 臆测“应该改哪些文件”再传入文件列表。对于仓库级 Issue，较稳妥的候选做法是把仓库根目录作为工作目录，让 Aider 使用仓库信息自行定位；只有任务数据明确给出允许编辑范围时，才传 `--file` 或位置文件参数。

## 4. 工作目录、目标仓库与配置污染

### 4.1 官方已证明

- 当前源码通过进程当前目录向上寻找 Git 仓库；官方也提示应在项目目录中运行 Aider。
- 位置参数只有一个且它是目录时，Aider 可以把该目录作为 Git 仓库目录；多个参数中若混入目录则报错。
- 配置搜索会涉及当前目录、Git 根目录和用户主目录中的 `.aider.conf.yml`。
- `.env`、`.aider.model.settings.yml`、`.aider.model.metadata.json` 等也有默认搜索路径；当前源码加载 `.env` 时使用覆盖现有环境变量的方式。
- 当当前目录与 Git 根目录不同，Aider 会提示聊天中的文件名相对于 Git 工作目录，而不是当前目录。

来源：[入口与仓库发现源码](https://github.com/Aider-AI/aider/blob/main/aider/main.py#L55-L79)、[配置与环境文件搜索源码](https://github.com/Aider-AI/aider/blob/main/aider/main.py#L283-L380)、[主流程中的目录处理](https://github.com/Aider-AI/aider/blob/main/aider/main.py#L625-L666)

### 4.2 对本项目的合理推断

- 子进程的 `cwd` 固定为当前任务的仓库快照根目录；不要依赖操作者所在目录。
- 在隔离容器中使用干净、任务专属的 HOME，防止评测机个人目录中的 Aider 配置进入本次运行。
- 关键参数全部由 Adapter 显式传入，并记录实际 Aider 版本、模型 ID 和启动参数。
- 仓库内 `.aider.conf.yml` 或 `.env` 仍可能改变运行行为。当前官方资料未显示一个可以彻底关闭所有默认配置/`.env` 搜索的总开关，因此要把“如何隔离仓库自带 Aider 配置与 `.env`”列为接入前的安全实测项，不能假设 `--config` 或 `--env-file` 会自动屏蔽默认搜索路径。

## 5. 自动确认、Git 提交与补丁提取

### 5.1 官方已证明

- `--yes-always` 会对每个确认回答 yes。旧文档仍出现 `--yes`，当前参数名是 `--yes-always`。
- Git 集成默认开启。
- `--auto-commits` 默认是 true：Aider 每次修改会自动提交；`--no-auto-commits` 可关闭。
- `--dirty-commits` 默认是 true：发现仓库原有未提交修改时，会先提交它们；`--no-dirty-commits` 可关闭。
- 默认会检查是否把 `.aider*` 和 `.env` 写入 `.gitignore`；`--no-gitignore` 可关闭该检查/修改行为。
- `--git-commit-verify` 默认 false，也就是 Aider 创建提交时默认使用 `--no-verify` 跳过 Git hooks。
- `--show-diffs` 只是“在提交修改时展示 diff”的终端输出选项，不是官方补丁输出协议。

来源：[Git integration](https://aider.chat/docs/git.html)、[当前 Git 参数源码](https://github.com/Aider-AI/aider/blob/main/aider/args.py#L393-L490)、[`.gitignore` 处理源码](https://github.com/Aider-AI/aider/blob/main/aider/main.py#L144-L191)

### 5.2 为什么默认行为不适合作为评测输出

如果保留自动提交，Aider 可能已经把修改放进新 commit，运行结束后的普通 `git diff` 就可能为空。若仓库起点本来不干净，默认的 dirty commit 还会改变基准历史。聊天历史默认位于 Git 根目录的 `.aider.chat.history.md`，也可能成为额外文件。

### 5.3 推荐的补丁提取方式（合理推断）

1. 每次任务使用独立、可丢弃、起点干净且固定到明确 base commit 的仓库快照。
2. 启动时传 `--no-auto-commits --no-dirty-commits --no-gitignore`，不允许 Aider 改写评测基准历史或插入自身配置文件变更。
3. 把 `--chat-history-file`、`--llm-history-file` 和 `--input-history-file` 都指向仓库外的制品目录。
4. Aider 退出后，在隔离副本中执行等价于 `git add -A` 的暂存，再对 base commit 生成 `git diff --cached --binary <base>`。这样新增、删除、重命名和二进制变更均由 Git 统一表示。
5. 生成 patch 后校验：不得包含任务仓库之外路径，不得包含 Adapter 的任务文件、聊天历史、密钥或运行配置。
6. 最后把仓库恢复/销毁；暂存动作只发生在一次性沙箱，不回写原始仓库。

只运行 `git diff` 不够可靠，因为它不包含未跟踪的新文件。若项目选择保留 Aider 自动提交，则必须改为同时收集“base commit 到最终 HEAD 的差异”和最终未提交差异，复杂度更高，因此不推荐作为第一版。

## 6. stdout、stderr、退出码和日志可观测性

### 6.1 官方已证明

- `--no-pretty` 可关闭彩色/美化输出，`--no-stream` 可关闭流式响应，`--verbose` 增加诊断输出。
- `--chat-history-file` 记录聊天历史；`--llm-history-file` 记录与 LLM 的会话；两者都是文本文件，不是文档化的结构化事件流。
- 当前 `InputOutput` 源码中，普通提示、警告、错误和助手回答都写到同一个 `Console`；`tool_error()` 只是增加内部错误计数后调用同一输出函数。源码未建立“stderr 专门代表错误”的稳定契约。
- 当前主流程对一部分启动/参数/文件错误明确 `return 1`；正常完成 `--message` 或 `--message-file` 时直接返回（Python 值为 `None`）。项目入口把 `aider` 映射到 `aider.main:main`。
- 当前官方选项中未看到 JSON、JSONL 或 NDJSON 的机器可读输出模式，也未看到通用的结构化 tool-call 事件流。

来源：[输出与历史参数](https://aider.chat/docs/config/options.html#output-settings)、[历史文件参数源码](https://github.com/Aider-AI/aider/blob/main/aider/args.py#L261-L318)、[同一 Console 输出实现](https://github.com/Aider-AI/aider/blob/main/aider/io.py#L892-L961)、[单消息返回路径](https://github.com/Aider-AI/aider/blob/main/aider/main.py#L1040-L1063)、[CLI 入口声明](https://github.com/Aider-AI/aider/blob/main/pyproject.toml#L23-L24)

### 6.2 合理推断与限制

- Adapter 必须分别完整捕获 stdout、stderr 和进程退出码，但不能把某一通道当作唯一错误依据。
- 退出码为 0 只能先解释为“进程正常结束”，不能直接解释为“生成了有效补丁”或“任务测试通过”。是否修改文件、补丁能否应用、测试是否通过，必须由 Runner 外部验证。
- 终端文本、聊天历史和 LLM history 可以作为审计制品，但不能当稳定 API 逐行解析计数。尤其不能承诺从中可靠统计统一意义上的“工具调用次数”。Aider 并未把自身公开为 Claude Code/Codex 那类标准 tool-call 事件源。
- `--no-pretty --no-stream` 能减少 ANSI 和分块输出带来的噪声，但不把输出变成机器协议。

### 6.3 需要本地安装后实测

以下情况的实际退出码、输出顺序和制品完整性不能只靠文档推定：

- API key 无效、额度耗尽、网络断开、模型名错误；
- LLM 返回了无法应用的编辑格式，或只回答文字没有改文件；
- 超时、外部 kill、Ctrl-C、磁盘只读、Git 仓库异常；
- `--yes-always` 是否会使所有可能的确认都真正无交互，以及它是否会自动允许模型建议的 shell 命令；
- 聊天历史与 LLM history 是否会意外包含认证材料或其他敏感信息；
- Windows/Linux、TTY/非 TTY 和不同固定版本下 stdout/stderr 的差异。

## 7. 认证与模型配置

### 7.1 官方已证明

- `--model MODEL` 选择主模型；Aider 通过 LiteLLM 支持多家模型服务。
- 官方支持环境变量形式的 provider key，也提供 `--openai-api-key`、`--anthropic-api-key` 和通用 `--api-key PROVIDER=KEY`。
- 还提供模型 settings、metadata、alias、弱模型与 editor model 等配置项。
- Aider 可连接本地模型和 OpenAI-compatible API，但具体模型是否能正确产出 Aider 所需编辑格式与模型能力有关。

来源：[Connecting to LLMs](https://aider.chat/docs/llms.html)、[Other LLMs / LiteLLM](https://aider.chat/docs/llms/other.html)、[Options reference](https://aider.chat/docs/config/options.html)

### 7.2 对本项目的合理推断

- 密钥通过沙箱的秘密环境变量注入，不放入命令行、任务文件、仓库、聊天历史或数据库明文字段；命令行 key 可能暴露于进程列表和日志。
- 每次评测记录：Aider 精确版本、provider、完整模型 ID、edit format、weak/editor model（若启用）、关键参数和时间戳。不要只保存容易漂移的模型别名。
- 评测时关闭自动更新检查，容器镜像固定 Aider 版本和依赖；网络只放行所选模型服务所必需的目的地。

## 8. 版本漂移风险

### 8.1 官方已证明

- 官方明确不保证 Python scripting API 向后兼容。
- 官方 release history 记录过 `--yes` 重命名为 `--yes-always`，并连带修改环境变量和 YAML key；这说明 CLI/config 也会发生迁移。
- 当前 CLI 有 `--version`、`--check-update/--no-check-update`，而项目元数据仍标为 Beta。

来源：[Scripting aider](https://aider.chat/docs/scripting.html)、[官方 HISTORY 中的重命名记录](https://github.com/Aider-AI/aider/blob/main/HISTORY.md#L608-L614)、[项目元数据](https://github.com/Aider-AI/aider/blob/main/pyproject.toml#L1-L18)

### 8.2 控制建议（合理推断）

- Adapter 只依赖 CLI，不导入 Aider Python 内部类。
- 按精确版本构建镜像，不使用 `latest`，运行时传 `--no-check-update`。
- 在 Adapter 兼容性测试中保存该版本的 `aider --help` 和 `aider --version` 输出；升级版本时先跑契约测试，再进入正式评测。
- 不使用 `--yes` 的缩写形式，使用当前完整参数名 `--yes-always`。

## 9. 本项目 Adapter 输入/输出映射建议

| 本项目统一字段 | Aider 映射 | 证据级别 | 说明 |
|---|---|---|---|
| `task.issue` | UTF-8 文件 + `--message-file` | 官方接口 + 合理推断 | 官方保证单条消息处理后退出；文件转换由 Adapter 做 |
| `task.repo_snapshot` | 子进程 `cwd` = 仓库根目录 | 官方源码 + 合理推断 | 保持目录与 Git 根一致 |
| `task.base_commit` | 启动前校验 HEAD；退出后作为 diff 基准 | 合理推断 | 防止补丁混入基准外变更 |
| `agent.model` | `--model <完整模型 ID>` | 官方接口 | 同时通过秘密环境变量注入认证 |
| 自动确认 | `--yes-always` | 官方接口 | 是否覆盖全部非交互场景仍需实测 |
| 禁止 Agent 改写 Git 历史 | `--no-auto-commits --no-dirty-commits` | 官方接口 + 合理推断 | 便于统一提取 patch |
| 防止 Aider 修改忽略文件 | `--no-gitignore` | 官方接口 | 避免额外 `.gitignore` 变更 |
| 终端审计 | 捕获 stdout、stderr、exit code | 合理推断 | 不按行解析为稳定事件 |
| 会话审计 | 仓库外 `--chat-history-file`、`--llm-history-file` | 官方接口 + 合理推断 | 保存前需做密钥检查/脱敏 |
| `result.patch` | 在一次性仓库中暂存全部变化后对 base 生成 binary diff | 合理推断 | 不从 stdout 提取；包含新文件 |
| `result.status` | 退出码 + patch 校验 + 外部测试共同决定 | 合理推断 | exit 0 不等于解决 Issue |
| 工具调用次数 | 当前不提供统一、可靠映射 | 官方未提供 | 不应从终端文本硬猜 |

候选命令形态如下，**仅代表待验证设计，不代表已经跑通**：

```text
aider \
  --message-file <artifact-dir/task.md> \
  --model <exact-provider/model-id> \
  --yes-always \
  --no-auto-commits \
  --no-dirty-commits \
  --no-gitignore \
  --no-pretty \
  --no-stream \
  --no-check-update \
  --no-analytics \
  --input-history-file <artifact-dir/input.history> \
  --chat-history-file <artifact-dir/chat.history.md> \
  --llm-history-file <artifact-dir/llm.history>
```

此命令应由参数数组启动，不应拼成 shell 字符串；进程工作目录是任务仓库根目录。资源限制、网络白名单、超时与强制终止由外层 Docker/Runner 实施，不是 Aider CLI 自己提供的评测沙箱能力。

## 10. 接入成熟度分级

| 状态 | 当前结论 |
|---|---|
| 理论可接入 | **是**。官方存在单消息处理后退出的 CLI，且直接修改仓库文件 |
| Adapter 契约测试通过 | **否**。尚未安装固定版本验证参数、退出码、非交互确认、日志和 patch 提取 |
| 真实模型账号测试通过 | **否**。尚未核验认证、费用、限流、模型编辑格式失败路径 |
| SWE-Gym 端到端跑通 | **否**。尚未把 Aider 生成的 patch 交给 SWE-Gym 测试并核对结果 |

## 11. 官方来源清单

以下页面均于 **2026-09-01** 访问：

1. [Aider：Scripting aider](https://aider.chat/docs/scripting.html)
2. [Aider：Options reference](https://aider.chat/docs/config/options.html)
3. [Aider：Git integration](https://aider.chat/docs/git.html)
4. [Aider：Connecting to LLMs](https://aider.chat/docs/llms.html)
5. [Aider：Other LLMs / LiteLLM](https://aider.chat/docs/llms/other.html)
6. [Aider 官方源码：`aider/main.py`](https://github.com/Aider-AI/aider/blob/main/aider/main.py)
7. [Aider 官方源码：`aider/args.py`](https://github.com/Aider-AI/aider/blob/main/aider/args.py)
8. [Aider 官方源码：`aider/io.py`](https://github.com/Aider-AI/aider/blob/main/aider/io.py)
9. [Aider 官方源码：`pyproject.toml`](https://github.com/Aider-AI/aider/blob/main/pyproject.toml)
10. [Aider 官方 Release history](https://github.com/Aider-AI/aider/blob/main/HISTORY.md)

