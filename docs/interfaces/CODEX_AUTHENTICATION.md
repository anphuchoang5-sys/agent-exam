# Codex 认证与协作凭据约定

> 状态：已确认（2026-09-04）
> 权威范围：Codex 原型认证方式、多人协作时的凭据所有权与安全边界。
>
> 反向导航：[`ARCHITECTURE.md`](../architecture/ARCHITECTURE.md) 只维护全局决定，[`DEPENDENCIES.md`](../dependencies/DEPENDENCIES.md) 只维护版本状态，[`HARBOR_EXECUTION.md`](./HARBOR_EXECUTION.md) 只维护执行映射，[`FRAMEWORK_INTERFACES.md`](./FRAMEWORK_INTERFACES.md) 只维护上游 CLI 接口；认证事实发生变化时必须回到本文更新。

## 1. 先用一句话理解

项目可以共享“怎样配置 Codex”的文档，但任何人都不得共享自己的 `auth.json`、API Key 或 Token。

`auth.json` 不是普通配置文件。它保存 Codex CLI 登录 ChatGPT 后使用的账号凭据，应按密码级敏感信息处理。

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

1. **只在统一评测机执行真实评测**：协作者正常开发和提交代码；需要真实 Codex Trial 时，由评测机所有者在自己的机器上运行。协作者不需要取得评测机所有者的凭据。
2. **协作者在自己机器执行**：协作者使用自己的 ChatGPT 账号运行 `codex login`，或使用自己获授权的 API Key；本机路径只放在本机未跟踪的环境配置中。

项目当前为单机架构，因此第 1 种方式是默认方案。

## 4. Kimi 与 DeepSeek 的边界

Kimi 和 DeepSeek 作为后续独立 Agent Configuration 处理，例如：

```text
codex-openai-chatgpt-pro
codex-kimi-api
codex-deepseek-api
```

每项评测结果必须记录实际 Agent、模型提供方、模型名和认证类型。一次 Trial 开始后不得从 OpenAI 静默切换到 Kimi 或 DeepSeek；失败后如需换提供方，必须创建新的运行配置和新的 Trial。

在正式写入具体 Kimi/DeepSeek 接口参数前，必须查阅各平台官方接口文档并完成兼容性实测。

## 5. 实现时的强制安全约束

- 只向经过检查的 SWE-Gym-Lite 原型任务注入个人 `auth.json`。
- 不把凭据文件复制进镜像层，不提交 Git，不写入 PostgreSQL 或 MinIO。
- `CODEX_AUTH_JSON_PATH` 只保存在执行节点本机、未跟踪的秘密配置中；执行节点在启动受控 Codex Trial 时解析它，既不把真实路径写入 Job，也不返回给对外接口。
- 公开 Job 请求、`ExecutionJobRequest` 和 PostgreSQL 只保存非秘密的认证类型与 Agent Configuration 身份，不接收凭据文件、文件内容或真实宿主路径。
- Trial 使用临时容器；结束后销毁容器及其可写层。
- 制品收集明确排除 `$CODEX_HOME`、Harbor secrets 目录和任何 `auth.json`。
- stdout、stderr、轨迹和异常信息进入存储前执行凭据脱敏。
- 首次实测只检查认证状态并运行一个真实任务，然后人工检查容器销毁和全部制品。
- 未通过凭据泄露检查前，不允许批量运行，也不允许对不可信用户开放。

## 6. 尚待实测，不伪装成已确认

- 当前 Codex CLI 与固定 Harbor Adapter 组合能否稳定刷新 ChatGPT 登录 Token。
- Trial 结束后容器和凭据副本是否在所有成功、失败、超时路径上删除。
- Harbor 生成的完整日志与轨迹是否可能包含认证信息。
- Kimi/DeepSeek 的 OpenAI 兼容接口与当前 Codex CLI/Harbor 固定版本是否兼容。
