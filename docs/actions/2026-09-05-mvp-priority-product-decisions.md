# MVP 优先级与产品默认规则同步行动记录

## 1. 状态与情况说明

- 状态：已完成。
- 来源请求：用户确认先用本地脚本跑通 Codex 的 Harbor → patch → SWE-Bench-Fork 真实技术闭环，再接正式 Web/数据库/所有者批准流程；随后确认两种人员身份，并接受其余产品规则的全部推荐方案，要求依据对话记录更新权威文档。
- 当前事实：项目仍处于架构与原型准备阶段；本次只同步文档，不实现应用账号、Harbor Adapter、Judge、清理任务或 Runner。
- 已确认决定：
  1. M0 是单个 Codex 的本地真实技术闭环；M1 把同一能力接入 Web/数据库/所有者批准，形成 Codex-only MVP；之后再接 Harbor 已有的 Aider、Claude Code；自研 Agent 降为 P2，当前 MVP 只保留通用扩展 seam，不实现源码审核、manifest 解析、Python wrapper 或 DeepSeek/Kimi 受控访问。
  2. 人员只有 `collaborator`（协作者）与 `owner`（所有者）两种；所有者兼任管理员和人工复核者。不开公共注册；所有者账户在评测机本地建立，协作者由所有者邀请，密码忘记后由所有者在本机重置，不引入邮件服务。私有网络准入不能替代应用登录。
  3. Quality Judge 在多 Agent 严格确定性并列时，对共同通过题的匿名补丁做两两比较；维度为切题且最小、可读/可维护、健壮性、副作用风险。A/B 顺序颠倒运行两次，冲突则平；多 Agent 循环比较按胜 1、平 0.5、负 0 聚合。所有者只能把质量比较判为无效并恢复并列，不能人工指定赢家。
  4. 工具调用、token、耗时等过程指标第一版只展示，不参与正确性总分或排名；缺失标记未知，不能写成 0。
  5. MVP 只实现闭卷主榜；`open_book_experimental` 只保留兼容字段/扩展位置。以后实现开卷时统一使用平台 Web 工具，不允许各 Agent 用能力不同的原生搜索工具。
  6. PostgreSQL 保存任务的标准查询字段；MinIO 以内容哈希保存不可变原始任务 JSON 快照。隐藏测试和参考答案不进入 Agent 可见输入。
  7. 待批准/排队 Job 可立即取消；运行中取消只停止后续 Trial，当前 Trial 最多运行到已冻结超时。主机或 Harbor 中断不自动续跑/重试，明确记录基础设施中断，由所有者决定是否创建带新证据的新尝试。
  8. 配置快照、确定性结果、最终 patch 与测试摘要长期保留；大型轨迹、stdout/stderr、Judge 原始响应默认保留 30 天。只有所有者可清理，先用本地维护命令，不新增定时服务；删除后保留哈希、大小、产生时间和删除审计。
  9. 第一版拒绝二进制 patch。文本 patch 超过 256 KiB 记录警告但继续，超过 1 MiB 以 `PATCH_TOO_LARGE` 拒绝且不得截断；单个大型原始制品超过 50 MiB 可截断但必须标记，单次运行原始制品总量上限 200 MiB。
  10. 远端私有入口采用 Tailscale Serve；应用账户仍与 tailnet 账户分层。当前 FlClash 保持系统代理开启、TUN 关闭，Tailscale/FlClash/VPN 共存结论以双机实测为准。
- 仍未知：账号密码哈希/session/invite 的具体技术实现；Codex/Harbor 固定版本与容器可行性；具体任务 revision；各上限在真实原型后的调优值；本机维护命令的精确入口；Tailscale 双机共存结果。
- 明确排除：不实现业务代码，不安装/运行 Harbor，不下载任务，不读取凭据，不执行真实模型调用，不把 P2 自研 Agent 细节当作当前 MVP 工作。

## 2. 实施措施

1. 更新领域术语与总架构，把“人员角色”“取消请求”和 M0/M1→已知 Agent→P2 的交付顺序写清，消除“总体首版必须实现自研 Agent/开卷榜”的旧口径。
2. 深化现有模块、HTTP 和数据契约，记录账号邀请、所有者权限、取消/恢复、任务快照、保留/删除和大小限制；不新增顶层 Module、Interface 或数据库表。
3. 固定 Quality Judge 的比较 rubric、双次反序、循环积分和人工作废边界；固定过程指标只展示。
4. 把自研 Agent 相关接口文档标为 P2 预留，并把 Source Review、manifest、受控 DeepSeek/Kimi 访问移出当前 MVP 实现/验收门槛。
5. 更新 Handoff 的已确认决定、待核验项和当前工作区清单，确保下一窗口不会重新把自研 Agent 当 P0。
6. 全文检索旧口径并运行 Markdown、链接和 `git diff --check` 验证；记录实际结果与任何偏差。

完成标准：所有当前权威文档一致表达 M0 本机 Codex 原型 → M1 Codex 平台 MVP → Aider/Claude Code → P2 自研 Agent；十项产品规则不再出现在待确认队列；技术未知仍明确标为待核验；没有新增未经确认的架构模块或把文档决定写成已实现能力。

## 3. 受影响文件树

```text
CONTEXT.md
  # 修改：领域词汇；定义协作者、所有者和取消请求
HANDOFF.md
  # 修改：下一窗口恢复入口；同步优先级、产品默认和真实 Git 状态
docs/
├─ actions/
│  └─ 2026-09-05-mvp-priority-product-decisions.md
│     # 新增：本轮决定、措施、文件关系与验证证据
├─ architecture/
│  ├─ ARCHITECTURE.md
│  │  # 修改：M0/M1/后续/P2、已确认决定、数据流、规划树、风险、门槛和技术核验队列
│  ├─ MODULE_CONTRACTS.md
│  │  # 修改：现有 Auth/Job/Judge/Reporting/Artifact 契约；P2 模块标记延后
│  └─ DATA_MODEL.md
│     # 修改：两角色、取消状态、任务快照、Judge 聚合、保留删除和大小约束
├─ dependencies/
│  └─ DEPENDENCIES.md
│     # 修改：Codex/Aider/Claude Code 与自研 Agent 的实施优先级
├─ interfaces/
│  ├─ HTTP_API.md
│  │  # 修改：邀请登录、角色、取消语义、闭卷范围、报告与清理边界
│  ├─ HARBOR_EXECUTION.md
│  │  # 修改：Codex 本地技术原型优先，Aider/Claude Code 次之，自研包装延后
│  ├─ FRAMEWORK_INTERFACES.md
│  │  # 修改：真实 Agent 接入顺序与 P2 自研接口状态
│  ├─ RUNNER_PROTOCOL.md
│  │  # 修改：P2 预留状态、文本 patch/日志/运行制品限制
│  └─ CODEX_AUTHENTICATION.md
│     # 修改：Codex M0/M1 与 P2 自研凭据规则的实施优先级区分
└─ operations/
   ├─ LOCAL_DOCKER_ENVIRONMENT.md
   │  # 修改：M0 网络验证和 P2 自研受控访问优先级
   └─ REMOTE_TEAM_ACCESS.md
      # 修改：两角色、邀请账号、本地恢复和私有网络/应用登录分层
```

设计关系：继续使用既有 Ports and Adapters。M0 通过 `ExecutionBackend` 的 Harbor Adapter 运行 Codex；M1 把该 seam 接入产品流程；之后在同一 seam 增加 Harbor 已有的知名 Agent 配置；P2 才实现自研进程包装。应用身份与现有 Owner Approval/Human Review 合作，不新增独立权限服务；保留清理由现有 Artifact Store/Repository 的维护入口承担，不新增调度服务。

## 4. 自验证方式

1. `rg` 检查所有当前权威文档中的“首版自研 Agent”“开卷第一版”“Judge rubric 待确认”“过程指标是否计分”“登录角色待确认”“二进制 patch 待确认”“保留期限待确认”等旧口径。
2. `rg` 确认 M0/M1/后续/P2、两种角色、邀请/本地恢复、Quality Judge 比较规则、只展示过程指标、闭卷 MVP、任务双层存储、取消/手动重试、30 天保留和 256 KiB/1 MiB/50 MiB/200 MiB 限制均能在各自事实源定位。
3. 检查规划文件树没有因 P2 预留而新增顶层 Module/Interface/table；P2 文件/模块清楚标注延后，不删除未来 seam。
4. 运行 `git diff --check`，并对新行动文档单独做 whitespace check。
5. 检查所有修改 Markdown 的 fenced-code 标记、相邻重复行和相对本地链接。
6. 用 `git status --short` 和逐文件 diff 复核既有未提交修改被保留，且 Handoff 的工作区清单与真实状态一致。

## 5. 自验证结果

- 实际修改与第 3 节文件树一致；未创建业务代码、顶层 Module/Interface、数据库迁移或额外目录。总架构的候选文件树只在既有 `apps/backend` 下补充一个已获授权的 M0 脚本入口，没有在本轮创建该文件。
- 旧决定检索：对 13 份当前权威文档检查“过程指标待计分、开卷工具待选、角色仍待定、执行中取消待定、Tailscale 未确认、二进制 patch 待定、自动恢复待定、Quality rubric 待定”等 10 组表达，结果为 0 命中。
- 新决定定位：对 M0/M1/P2、两角色、Quality 反序比较、制品阈值、保留策略等执行 22 项文件级断言，全部命中预期事实源。
- Markdown 结构与链接：14 份本轮文档的 fenced code 数量均成对，所有相对 Markdown 链接可解析；重复标题和相邻重复非空行检查均通过。
- `git diff --check` 退出码为 0；Git 只提示现有工作区下次写入时会把 LF 转为 CRLF，没有空白错误。新行动文档用 `git diff --no-index --check -- NUL ...` 检查，无空白错误；退出码 1 仅表示该文件相对空设备存在内容。
- `git status --short` 已复核：既有的 `AGENTS.md`、前序文档修改和两个未跟踪行动记录均保留；本轮只新增本行动记录并修改第 3 节列出的权威文档，没有删除、重置或覆盖用户/前序工作。
- 未运行 Harbor、SWE-Bench-Fork、容器、网络或应用测试，因为本次任务只同步架构文档；相应能力仍明确标为未实现/待技术核验，没有写成已通过。
- 实施偏差：两次大块补丁因上下文不完全匹配而整体未应用，随后改为读取当前正文并拆分补丁；失败尝试没有留下半写入内容。
