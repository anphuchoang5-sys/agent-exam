# Codex 与自研 Agent 模型凭据约定

> 状态：M0/M1 Codex 认证政策和 P2 自研 Agent 凭据边界已确认；运行方式仍待实测
> 权威范围：Codex 原型认证方式、自研 Agent 的 DeepSeek/Kimi 凭据所有权，以及多人协作时的秘密边界。
>
> 反向导航：[`ARCHITECTURE.md`](../architecture/ARCHITECTURE.md) 只维护全局决定，[`DEPENDENCIES.md`](../dependencies/DEPENDENCIES.md) 只维护版本状态，[`HARBOR_EXECUTION.md`](./HARBOR_EXECUTION.md) 只维护执行映射，[`FRAMEWORK_INTERFACES.md`](./FRAMEWORK_INTERFACES.md) 只维护上游 CLI 接口；认证事实发生变化时必须回到本文更新。

## 1. 先用一句话理解

项目可以共享非秘密配置，但任何人都不得共享自己的 `auth.json`、API Key 或 Token。正式评测所需凭据只由评测机所有者在本机可信秘密配置中管理。

`auth.json` 和 DeepSeek/Kimi API Key 都不是普通配置，应按密码级敏感信息处理。Codex 的固定 Harbor Adapter 当前需要在 Trial 生命周期内使用 `auth.json`；P2 自研 Agent 则明确不得取得 DeepSeek/Kimi 真实 Key，两条路径不能混为同一种注入方式。自研路径尚未验证不阻塞 Codex MVP。

## 2. 已确认的原型选择

首个真实 Codex 原型采用以下配置：

```text
Agent：Codex CLI
模型提供方：OpenAI / ChatGPT
认证方式：运行机器所有者本人的 ChatGPT Pro auth.json
执行位置：运行机器所有者控制的单机 Harbor 临时 Trial 容器
```

OpenAI 官方文档区分两类本地认证：使用 ChatGPT 登录以使用订阅权益，或使用 API Key 按 API 用量计费：

- <https://learn.chatgpt.com/zh-Hans/docs/pricing>
- <https://learn.chatgpt.com/docs/auth>

固定版本 Harbor 的 Codex Adapter 支持通过 `CODEX_AUTH_JSON_PATH` 指定本机 `auth.json`，并在运行时把文件上传到 Trial 容器：

- <https://github.com/harbor-framework/harbor/blob/6af8d6e31eced13b93849cdf80feeadf24603d15/src/harbor/agents/installed/codex.py#L1380-L1391>

这只能证明 Harbor 技术上支持该接入方式，不代表可以共享个人 ChatGPT 账号凭据。

## 3. 多人协作规则

### 3.1 可以共享

- 本文档和其他项目文档。
- 环境变量名称，例如 `CODEX_AUTH_JSON_PATH`。
- 不含个人目录的示例路径，例如 `<your-codex-home>/auth.json`。
- Agent、模型提供方、模型名、超时和资源限制等非秘密配置。
- 脱敏后的失败日志。

### 3.2 禁止共享

- 任何人的真实 `auth.json` 文件或文件内容。
- ChatGPT 登录 Token、Refresh Token、Cookie 或会话信息。
- OpenAI、Kimi、DeepSeek 等平台的真实 API Key。
- 包含上述内容的截图、终端输出、数据库记录、MinIO 制品或聊天消息。

OpenAI 的个人账户供创建者本人使用，不能把账户凭据交给其他人：

- <https://openai.com/es-US/policies/row-terms-of-use/>

### 3.3 协作者怎样工作

有两种允许的方式：

1. **只在统一评测机执行正式真实评测**：协作者可以远端提交冻结的评测选择，但 Job 初始必须为 `AWAITING_OWNER_APPROVAL`；评测机所有者通过可信会话批准后才进入本机 `QUEUED`，随后只能由本机 Worker 执行。远端提交和批准都不携带或读取 `auth.json`、DeepSeek/Kimi Key，协作者不需要取得评测机所有者的凭据。
2. **协作者在自己机器开发或冒烟测试**：协作者只能使用自己获授权的账号或 Key，并保存在自己的未跟踪秘密配置中；这类结果不是本项目正式评测机产生的正式排行证据。

项目当前为单机架构，因此第 1 种方式是默认方案。

## 4. P2 Kimi 与 DeepSeek 的边界

自研 Agent 已降为 P2，只保留扩展接缝；其首版模型提供方只允许 DeepSeek 或 Kimi。评测所有者在源码审核通过后，从这两个已登记提供方中生成 Agent Configuration；提交者不能上传 Key、填写任意提供方/Base URL 或要求运行时回退。例如：

```text
codex-openai-chatgpt-pro
team-agent-a-kimi-fixed-model
team-agent-a-deepseek-fixed-model
```

`codex-openai-chatgpt-pro` 使用第 2 节的 Codex 认证路径；后两项是同一自研源码的两个独立配置，不能混分。每项评测结果必须记录实际 Agent、模型提供方、模型名和认证类型。一次 Trial 开始后不得静默切换提供方；失败后如需换提供方，必须创建新的配置和新的 Trial。

DeepSeek/Kimi 真实 Key 只由评测机所有者在本机可信秘密配置中保存。被测 Python Agent 只使用由现有 Execution Backend/LLM Provider Implementation 提供的受控、可撤销单次运行访问能力，不能读取提供方 Key。这里不新增顶层业务 Module；受控访问采用宿主进程还是可信侧车、怎样经过 FlClash/VPN、怎样限制模型/Token/预算以及怎样阻断绕过，均留到 P2 原型裁决。

在正式写入具体 Kimi/DeepSeek 模型 ID、外部接口参数或兼容声明前，必须查阅各平台官方文档并完成真实调用测试。

## 5. 实现时的强制安全约束

- 只向经过检查的 SWE-Gym-Lite 原型任务注入个人 `auth.json`。
- 不把任何凭据文件或 Key 复制进镜像层，不提交 Git，不写入 PostgreSQL 或 MinIO。
- `CODEX_AUTH_JSON_PATH` 只保存在执行节点本机、未跟踪的秘密配置中；执行节点在启动受控 Codex Trial 时解析它，既不把真实路径写入 Job，也不返回给对外接口。
- DeepSeek/Kimi Key 只保存在评测机所有者控制的本机可信秘密配置中；精确保存机制仍待确认，但不得使用仓库 `.env`、提交者输入或可被被测容器挂载的普通文件。
- 公开 Job 请求、`ExecutionJobRequest` 和 PostgreSQL 只保存非秘密的提供方、认证类型、逻辑凭据配置身份与 Agent Configuration 身份，不接收凭据文件、Key 内容或真实宿主路径。
- P2 `agent-exam.yaml` 不声明 Key、自定义提供方/Base URL、代理、宿主路径或 shell 命令；自研 Agent 只选择所有者已登记的 DeepSeek/Kimi 配置。
- 所有者批准只授予该 Job 进入本机执行队列的资格；它不把凭据附加到 Job，也不在 HTTP 请求生命周期内启动 Agent。Worker 真正建立受控 Trial 时才从本机秘密配置解析凭据引用。
- P2 自研 Agent 被测进程及其容器环境、命令行和文件系统不得出现 DeepSeek/Kimi 真实 Key；若实现需要访问令牌，只能签发与单个 `run_id`、固定提供方/模型、预算和有效期绑定的可撤销能力，且必须像秘密一样脱敏和清理。
- Trial 使用临时容器；结束后销毁容器及其可写层。
- 制品收集明确排除 `$CODEX_HOME`、Harbor secrets 目录、任何 `auth.json`、提供方 Key 和运行时访问令牌。
- stdout、stderr、轨迹和异常信息进入存储前执行凭据脱敏。
- M0 首次实测只检查认证状态并运行一个真实任务，然后人工检查容器销毁和受控本机证据目录；接入 M1 后再检查 PostgreSQL/MinIO 全部制品。
- 未通过凭据泄露检查前，不允许批量运行，也不允许对不可信用户开放。

## 6. 尚待实测，不伪装成已确认

### 6.1 2026-09-07 风险评估发现

- **固定源码事实**：上述 `run()` 把登录文件上传到 `/tmp/codex-secrets/auth.json`，在指定 Agent 用户时改为该用户所有，并从 `$CODEX_HOME/auth.json` 链接过去；随后用 `--dangerously-bypass-approvals-and-sandbox` 运行 Codex。目录命名和容器外层隔离不能证明同一用户的仓库进程读不到文件。是否采用额外读取隔离仍是实现/验收问题，不因此更改已确认认证方式。
- **方法级合成验证**：固定 Harbor `Trial._scrub_jobs_dir()` 只搜集敏感环境变量的值做文本替换；已验证它可以抹除合成环境变量值和合成文件路径，但不会自动解析该文件内的假 Token。项目 `process_evidence.write_log()` 同样原样保存假 Token。完整证据、来源与优先级见 [风险评估](../research/2026-09-07-dns-icmp-risk-assessment.md)；这不是实际登录信息泄露，也没有执行完整 Trial。
- **待验收边界**：成功/失败/超时清理、文件内 Token（含刷新后的值）、日志/轨迹/patch 和可写挂载中的秘密覆盖都尚未通过。网络封禁不能代替这些检查；仅排除名为 `auth.json` 的文件也不能证明内容未被复制进其他输出。当前真实入口继续关闭，本次评估没有授权读取真实凭据或接受剩余风险。

### 6.2 2026-09-07 假凭据安全收尾

状态：用户已授权假值检查及现有适配层内的小修；日志能力已增强、独立沙箱读取限制有正反对照、专属容器清理已验证。**完整 Harbor Trial 凭据安全未通过**，不包含真实认证或网络剩余风险豁免。

| 项目 | 本轮证据 | 能证明 / 不能证明 |
|---|---|---|
| 凭据读取正对照 | 固定任务镜像，UID 65534，同用户创建的假 `auth.json` 为 0600；直接路径和 `$CODEX_HOME/auth.json` 链接均可读 | 仅靠同用户权限及目录名不足以隔离读取；没有真实凭据 |
| Codex 沙箱拒绝读取 | 固定 CLI `0.153.0` 的 `codex sandbox -- <command>` 配合权限 profile：根目录只读、题目目录可写、两个假凭据目录 deny；题目读写正常，两条凭据路径均不可读 | 独立 Linux 沙箱命令对照通过；没有增加 capability 或关闭 seccomp，也不是完整 Codex 模型会话/Harbor Trial |
| 已知值日志脱敏 | `run_bounded_process(..., redactions=(...))` 将仅驻内存的值交给内部 `Redactor`，双流在落盘前替换；启动异常返回值也处理 | 已传入的完整值跨分块、超时/失败和日志上限测试通过；不会自动发现认证文件内/刷新后的 Token，不抵御任意编码 |
| 正常/报错/超时清理 | 三个独立禁网假凭据容器，分别返回 0/7/124；测试 finally 显式调用生产精确 Compose 清理 helper，标签资源复核为空 | 证明该 helper 能移除这三种测试容器及其可写层；不证明完整 Harbor 的每条退出路径均已接线、挂载目录无残留 |

首次沙箱调用误用了旧式 `codex sandbox linux ...`：退出 101，未执行读取程序，不能算拒绝读取通过。读取本包帮助后改为上述实际命令，复测退出 0，包含题目读写正对照及两条 `credential-denied`。CLI 还提示临时目录下不能创建 PATH aliases；直接调用沙箱成功不能代替后续完整工具链兼容性验证。

复现证据为忽略目录 `runtime/prototype/credential-boundary-20260907-01/`（三种结束路径及首次命令失败）和 `...-02/`（命令纠正后读取对照）；专用脚本为同级 `credential-boundary-probe.py` / `credential-fixture.py`。全部使用现有缓存镜像、`--pull=never --network none`、无挂载、去全部 capability、禁止提权和资源限额；本轮未改上游、代理或网络放行规则。

上述日志小修的准确测试数量和命令见 [行动记录](../actions/2026-09-05-m0-codex-harbor-implementation.md#2026-09-07-假凭据检查与日志小修)。它只处理传入的已知完整值；当前 NOP Adapter 仍不提供真实秘密列表，不能说所有 Trial 已自动脱敏。

#### 下一阶段：固定 Harbor 启动兼容（同日）

用户要求解释日志实现并继续后，新增了现有 Execution Adapter 内部的 `codex_policy.py` 和 `codex_agent.py`，**仍是待完整集成的兼容实现，不是已开放的 Agent**：

- `permission_config()` 生成固定本地权限：题目目录和临时目录可写，凭据目录、CODEX_HOME、日志和 `/proc` 禁止访问；禁止仓库命令联网，关闭审批升级和 Web 搜索。它不是模型进程的端点控制，不能代替已有容器网络策略。官方 [权限说明](https://learn.chatgpt.com/docs/permissions) 提醒旧 sandbox 配置/参数会覆盖 profile，因此兼容层不混用这两套配置。
- `guarded_codex_class()` 窄继承固定上游 Codex，复用原 `run()`，仅接受已核对的启动/辅助命令。它移除启动处的 bypass 与 nvm shell 初始化，保留模型/effort/Web 关闭配置和原始指令正文；命令结构不匹配时在执行前拒绝，不做全文字符串替换。部署时仍须提供已验证的预装 CLI PATH。
- 兼容类要求显式非 root 数值 UID，不读取宿主环境中的 API Key、强制登录或 Base URL；真实凭据解析刻意返回 `CODEX_CREDENTIAL_BINDING_NOT_READY`。测试子类只返回自行生成的假文件。**未修改上游源码、未注册到生产 AgentFactory，`harbor_entry` 仍拒绝非 NOP。**
- 外层 finally 覆盖上游配置上传之前/期间的失败，以及运行失败和取消；清理失败不再被该外层吞掉。固定 Harbor 方法契约使用不执行命令的 RecordingEnvironment，验证正常、配置上传失败、运行失败、注入取消、清理失败五种路径；这是方法调用/清理尝试证据，不是完整 Trial 资源销毁证明，也不是墙钟超时实测。

独立 Docker 对照发现固定 CLI 在不存在的题目 `.codex` 拒绝访问路径上启动失败。仅移除 `/proc` 拒绝或 `/tmp` 可写均未解决；预建空 `.codex` 目录后保持全部限制即可运行。兼容层因此增加目录准备并拒绝工作目录/`.codex` 是符号链接；没有放宽 deny、增加 capability 或修改 seccomp。复测使用生产生成的同一 profile 和准备命令：题目读写通过、两条假凭据读取拒绝、凭据目录写入拒绝、安全配置改写拒绝。PATH aliases 的临时目录警告仍存在，不代表完整工具链可用。

证据保存于 `runtime/prototype/codex-guard-20260907-01/`（失败）、`...-02/`（单变量定位）、`...-03/`（修复后完整对照）；三轮专属容器均清理且复核无残留。准确命令与检查结果见 [兼容接线行动记录](../actions/2026-09-05-m0-codex-harbor-implementation.md#2026-09-07-固定-harbor-启动兼容接线)。

**剩余接线明确保留**：生产 Job 引导尚未使用该兼容类，真实凭据绑定仍关闭；固定任务的非 root 用户、目录权限和预装 PATH 尚未通过完整 Trial 验证。Harbor 自己写的 session/trajectory、挂载目录和 patch 内容拒绝/脱敏、刷新值登记、外层进程超时/崩溃及完整生命周期仍待实现和验证；不得用字符串替换静默修改待判卷 patch。当前产物不是完整 Harbor 安全验收，不授权真实凭据或模型调用。

### 6.3 其他尚待实测项

- 当前 Codex CLI 与固定 Harbor Adapter 组合能否稳定刷新 ChatGPT 登录 Token。
- Trial 结束后容器和凭据副本是否在所有成功、失败、超时路径上删除。
- Harbor 生成的完整日志与轨迹是否可能包含认证信息。
- P2 Kimi/DeepSeek 的精确模型 ID、外部接口与平台 Python 进程 Interface 是否兼容。
- P2 受控模型访问采用宿主进程还是可信侧车，以及短期访问能力的签发、限额、撤销和清理方式。
- P2 Docker Desktop 下能否证明被测容器既没有取得 DeepSeek/Kimi Key，也不能绕过受控路径直连提供方、宿主或任意公网；这些问题不阻塞 M0/M1 Codex。
