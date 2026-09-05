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

- <https://github.com/harbor-framework/harbor/blob/6af8d6e31eced13b93849cdf80feeadf24603d15/src/harbor/agents/installed/codex.py#L1198-L1286>

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

- 当前 Codex CLI 与固定 Harbor Adapter 组合能否稳定刷新 ChatGPT 登录 Token。
- Trial 结束后容器和凭据副本是否在所有成功、失败、超时路径上删除。
- Harbor 生成的完整日志与轨迹是否可能包含认证信息。
- P2 Kimi/DeepSeek 的精确模型 ID、外部接口与平台 Python 进程 Interface 是否兼容。
- P2 受控模型访问采用宿主进程还是可信侧车，以及短期访问能力的签发、限额、撤销和清理方式。
- P2 Docker Desktop 下能否证明被测容器既没有取得 DeepSeek/Kimi Key，也不能绕过受控路径直连提供方、宿主或任意公网；这些问题不阻塞 M0/M1 Codex。
