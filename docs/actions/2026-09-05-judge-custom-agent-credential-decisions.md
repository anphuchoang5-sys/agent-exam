# Judge、自研 Agent 与凭据决定同步行动记录

## 1. 状态与情况说明

- 状态：已完成。
- 来源请求：用户确认 Judge 触发规则、自研 Agent 接入范围与 DeepSeek/Kimi 凭据规则后，要求立即同步所有权威文档，避免长上下文导致决定丢失；同时要求后续遵守最小修改原则。
- 当前事实：项目尚无业务代码；本次只同步已确认架构与协作规则，不实现 Runner、模型调用、网络隔离或 Judge。
- 已确认决定：
  1. 确定性结果是首要排序事实；Quality Judge 只在同一评测条件、逐题确定性结果完全相同、存在共同通过题且清洗证据齐备时打破并列；Judge 不可用时保持并列。
  2. Failure Judge 只在失败运行被人工请求或固定抽样策略选中时诊断，不参与排名。
  3. Judge 输入必须先经过裁剪、脱敏、去重和限量；不得直接提交混杂的完整轨迹、日志与代码，也不得包含秘密或隐藏答案。
  4. 首版自研 Agent 只支持 Python，采用固定的项目进程 Interface；不接受任意 shell 命令。具体 Python 版本和依赖锁格式仍待原型核验后固定。
  5. 首版自研 Agent 只允许已登记的 DeepSeek 或 Kimi 模型配置；真实 API Key 由评测机所有者管理，只保存在评测机可信秘密配置中，不由提交者填写，不进入被测 Agent 容器、HTTP 请求、数据库、MinIO、日志或轨迹。
  6. 受控模型访问优先深化现有 Execution Backend 与 LLM Provider Adapter 的 Implementation，不新增顶层业务 Module；宿主进程或可信侧车等部署形态以及 Docker 网络强制方式仍待实测。
  7. 后续遵守最小修改原则：先复用或深化现有 Module；新增顶层 Module、Interface、表或目录前，必须说明现有职责为何不能承载，并取得用户确认。
- 仍未知：DeepSeek/Kimi 的精确模型 ID、外部协议兼容、凭据保存机制、运行时受控访问部署形态、网络防绕过、`agent-exam.yaml` 完整 schema、依赖锁文件格式、Judge 评分 rubric 与聚合细节。
- 明确排除：不读取或写入真实凭据；不安装依赖；不运行 Harbor/SWE-Gym；不修改业务代码；不把待实测项写成已实现。

## 2. 实施措施

1. 在协作规则中收紧最小修改与新增 Module/Interface 的确认纪律。
2. 更新总架构、模块契约、数据模型和术语，使两类 Judge、触发条件、证据清洗和排名语义一致。
3. 更新自研 Agent、Harbor、HTTP 与框架接口文档，固定 Python-only、受审核进程 Interface、DeepSeek/Kimi allowlist 和秘密边界，同时保留未确认的 schema/部署细节。
4. 扩展现有认证与本机 Docker 运维事实源，记录模型 Key 的所有权、禁止流向和待实测网络条件；不新增顶层业务 Module。
5. 用全文检索和 `git diff --check` 核对旧的 Judge 待确认描述、任意提供方/用户填 Key 表述、Python-only 决定和最小修改规则；检查实际 diff 后回填结果。

完成标准：所有直接受影响的权威文档一致表达上述已确认决定；旧的“Judge 是否计分”“自研 Agent 接入方式待确认”“secret 可直接注入自研容器”等冲突表述被删除或收窄为真实待实测项；行动记录反映实际变更与验证结果。

## 3. 受影响文件树

```text
AGENTS.md
  # 修改：协作规则唯一事实源；加入最小修改和新增架构元素前的确认纪律
CONTEXT.md
  # 修改：领域术语唯一事实源；固定 Agent Configuration 与两类 Judge 的语义
HANDOFF.md
  # 修改：下一窗口导航；移除已经失效的 Judge 与自研模型接入口径
docs/
├─ actions/
│  └─ 2026-09-05-judge-custom-agent-credential-decisions.md
│     # 新增：本次同步的决定、范围、文件关系和验证证据
├─ architecture/
│  ├─ ARCHITECTURE.md
│  │  # 修改：全局决定、关键数据流、规划树、风险、验收门槛和讨论队列
│  ├─ MODULE_CONTRACTS.md
│  │  # 修改：Judge、自研 Agent、Provider Adapter 的 Interface 与不变量
│  └─ DATA_MODEL.md
│     # 修改：两类 Judge 的最小存储语义与排行榜约束
├─ dependencies/
│  └─ DEPENDENCIES.md
│     # 修改：自研 Python 运行时与 DeepSeek/Kimi 外部依赖的已确认/待实测边界
├─ interfaces/
│  ├─ HTTP_API.md
│  │  # 修改：提交审核、结果展示和排行榜的外部契约
│  ├─ HARBOR_EXECUTION.md
│  │  # 修改：Python 自研 Agent 到 Harbor 的受控映射及秘密边界
│  ├─ RUNNER_PROTOCOL.md
│  │  # 修改：首版 Python 进程协议、模型访问与凭据禁入规则
│  ├─ FRAMEWORK_INTERFACES.md
│  │  # 修改：自研 Agent 接入选择和仍待实测事项
│  └─ CODEX_AUTHENTICATION.md
│     # 修改：现有凭据事实源扩展 DeepSeek/Kimi 所有权与运行时访问规则
└─ operations/
   ├─ LOCAL_DOCKER_ENVIRONMENT.md
   │  # 修改：受控模型访问在 Docker Desktop/FlClash 下的未验证边界
   └─ REMOTE_TEAM_ACCESS.md
      # 修改：远端协作者的凭据禁入、受控访问与网络边界
```

设计关系：不创建新的顶层业务 Module。现有 Agent Registry 审核并冻结 Agent/模型配置；Execution Backend 在运行期使用现有 LLM Provider Seam，DeepSeek 与 Kimi 是该 Seam 的两个 Adapter；Judge 通过现有证据与 Provider 路径运行。具体宿主代理/可信侧车仅是 Implementation 与部署选择，未实测前不定稿。

## 4. 自验证方式

1. `rg` 检查所有权威文档中与 Judge、`agent-exam.yaml`、Python 自研 Agent、DeepSeek/Kimi、API Key、最小修改有关的描述。
2. 检查旧的“Judge 是否进入总分”“自研 Agent 接入方式待确认”等表述不再出现在当前权威待确认队列。
3. 检查文档仍明确区分“已确认架构”“待确定 schema”和“待实测部署/网络”，没有把 Gateway 或容器隔离写成已实现。
4. 运行 `git diff --check`，预期无空白错误。
5. 检查 `git diff --stat` 与 `git status --short`，确认只触及本次权威文档和行动记录，没有覆盖用户其他改动。

## 5. 自验证结果

1. 旧口径全文检索通过：`rg` 未再找到“Judge 只做失败归因”“Judge 是否进入总分”“Kimi/DeepSeek 以后接入”“自研 Agent 接入方式仍待选择”“直接把模型 Key 注入自研容器”等冲突描述。`rg` 以退出码 1 表示零匹配。
2. 已确认口径检索通过：最小修改原则、Python 固定进程 Interface、DeepSeek/Kimi allowlist、真实 Key 禁入、Failure/Quality 严格触发、Judge 版本幂等与不新增顶层 Module 均能在各自权威文档中定位。
3. `git diff --check` 退出码 0，无空白错误；输出只有 Git 对工作副本 LF/CRLF 转换的提示，不影响内容检查。
4. Markdown 结构检查通过：全部修改文档的 fenced-code 标记成对；无相邻重复非空行；全部相对 Markdown 链接的本地目标存在。
5. 变更范围检查通过：只修改协作规则、领域/架构/接口/依赖/运维权威文档、交接导航和本行动记录，没有修改业务代码、安装依赖、读取凭据或执行真实 Harbor/Judge/模型调用。
6. 工作区原先已有 `HANDOFF.md`、架构/运维文档中的 FlClash/Tailscale 修改，以及未跟踪的 `docs/actions/2026-09-05-docker-flclash-container-proxy.md`；本次在原内容上追加一致口径，没有重置、覆盖或把该行动记录冒充成本次新增。最终 diff 审阅还发现 Handoff 保留着旧 HEAD、旧工作区清单和“AGENTS 本轮未修改”，已按实际 `ef6f22e` 与 `git status --short` 修正。
7. 本次是纯文档同步，没有可运行的业务测试；未把未执行的 Harbor、网络隔离、DeepSeek/Kimi 或 Judge 原型测试描述为通过。

实施偏差：两次多文件补丁因部分文件上下文已经变化而报告匹配失败，且此前已匹配的 hunks 已写入。随后逐文件检查实际 diff，补齐未应用部分并移除一处重复的最小修改规则；最终旧口径、重复行和 `git diff --check` 均通过。
