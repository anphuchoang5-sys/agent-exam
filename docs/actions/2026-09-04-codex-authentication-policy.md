# Codex 原型认证与协作凭据政策行动文档

## 状态与情况说明

- 状态：已完成。
- 已确认首个 Codex 原型优先使用评测机所有者本人 ChatGPT Pro 登录产生的 `auth.json`。
- Kimi 与 DeepSeek API 只作为后续独立 Agent Configuration，不在一次运行中自动切换。
- 项目存在多人协作场景，必须明确区分“可以共享的配置说明”和“禁止共享的真实凭据”。
- `auth.json` 属于个人账号登录凭据，不得发送给协作者、提交到 Git，或进入 PostgreSQL、MinIO、日志和评测制品。

## 实施措施

1. 在 Codex/Harbor 接口文档中记录两种认证方式及原型默认选择。
2. 明确每位协作者必须使用自己的 ChatGPT 账号登录，或使用自己获授权的 API 密钥。
3. 明确仓库只保存环境变量名、路径示例和操作步骤，不保存真实凭据或真实本机路径值。
4. 明确每个评测配置记录 Agent、模型提供方、模型名和认证方式；禁止运行中静默切换提供方。
5. 将凭据隔离、日志脱敏、制品排除和临时容器销毁列为实现前置验收项。
6. 同步总架构、依赖和框架接口文档，并把认证专题文档设为唯一事实源；宿主 CLI 探针与 Harbor 容器 E2E 分开记录。

## 需要修改的文件树

```text
docs/
├── actions/
│   ├── 2026-09-04-architecture-document-reconciliation.md
│   │   # 后续对账任务的实际修改与验证证据
│   └── 2026-09-04-codex-authentication-policy.md
│       # 本次认证决定的行动记录与收尾证据
├── architecture/
│   └── ARCHITECTURE.md
│       # 全局决定、秘密边界、风险和验证门槛
├── dependencies/
│   └── DEPENDENCIES.md
│       # 区分已确认认证政策与待固定 CLI/模型/容器版本
└── interfaces/
    ├── CODEX_AUTHENTICATION.md  # 认证政策、凭据所有权和秘密边界的唯一事实源
    ├── FRAMEWORK_INTERFACES.md  # 官方 CLI、宿主探针和容器待实测状态
    └── HARBOR_EXECUTION.md      # 非秘密输入、执行节点注入、制品排除和验收门槛
```

## 修改后自验证方式

- 检查上述文档是否明确写出“不得共享 `auth.json`”。
- 检查是否明确写出“每位协作者使用自己的凭据”。
- 检查是否明确写出 Kimi/DeepSeek 不能作为同一运行的静默回退。
- 检查文档中没有真实 Token、API Key、`auth.json` 内容或个人凭据路径值。
- 检查认证专题文档与总架构、依赖、Harbor、框架接口之间的相对链接均存在。
- 检查 `codex --version` 与 `codex exec --help` 的真实退出码；不得把宿主成功写成容器 E2E 成功。
- 检查 `git diff --check` 无空白错误。

## 自验证情况

- 通过：总架构、依赖、Harbor 执行和框架接口均链接认证唯一事实源，并一致记录评测机所有者 ChatGPT Pro `auth.json` 的选择。
- 通过：文档明确协作者不得取得所有者凭据；协作者自行运行时必须使用自己的 ChatGPT 登录或自己获授权的 API Key。
- 通过：Kimi/DeepSeek 只作为独立 Agent Configuration，不能在同一 Trial 中静默回退。
- 通过：42 份第一方 Markdown 的 102 个相对链接目标全部存在；本轮 9 份受影响文档无尾随空白，代码围栏成对。
- 通过：常见明文密钥模式扫描无匹配；本次没有读取真实 `auth.json`、登录状态、API Key 或 Token。
- 通过：`codex --version` 与 `codex exec --help` 在提升权限的只读宿主 shell 中退出码均为 0；该结果没有被写成 Harbor 容器或真实 Trial 已通过。
- 通过：`git diff --check` 退出码为 0；默认沙箱初始化故障和验证范围限制已在新的对账行动记录中如实保留。
