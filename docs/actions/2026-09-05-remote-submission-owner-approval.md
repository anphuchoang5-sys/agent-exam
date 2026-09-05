# 远端提交与评测机所有者审批行动记录

> 状态：已完成（文件修改和发布前检查完成；本地提交/推送结果由 Git 记录）
>
> 日期：2026-09-05
>
> 范围：文档与架构契约；本次不安装联网软件、不修改校园网/VPN/防火墙、不实现业务代码、不推送远程仓库

## 1. 情况说明

- 用户已确认：当前只有机器所有者的笔电是正式真实评测节点；协作者从自己的机器提交评测请求，但请求必须先等待机器所有者明确批准，批准后本机 Worker 才能领取并执行真实测评。
- 用户已接受：协作者提交和使用平台时，评测机及本机平台必须在线；离线时不提供远程入口。
- 旧架构仍把 `POST /jobs` 直接记录为 `QUEUED`，没有“等待所有者批准”状态和批准接口，不能表达已确认流程。
- 评测机位于校园网后，且机器所有者需要开启既有 VPN 访问外网。直接从校园网路由器开放端口既不可靠也扩大攻击面；需要记录私有覆盖网络候选和 VPN 共存条件。
- 更新前按用户要求先把原有工作区改动本地提交。已完成本地检查点提交 `a2e85bb`（`docs: reconcile evaluation architecture records`），未推送。
- 用户随后确认 FlClash 的虚拟网卡/TUN 当前关闭，并明确授权把本轮文档创建新本地提交后推送到 `origin/main`。

## 2. 已确认、候选与未知

### 2.1 已确认

1. 远端协作者只提交请求，不能直接启动正式真实评测。
2. 新 Job 的初始状态为 `AWAITING_OWNER_APPROVAL`；只有评测机所有者批准后才进入 `QUEUED`。
3. Worker 只领取 `QUEUED` Job，并且只在评测机本地运行。
4. Codex 个人认证凭据仍只存在于评测机；远端入口、HTTP 请求、PostgreSQL、MinIO 和 Git 都不得接触凭据正文或真实秘密路径。
5. 评测机离线时远端入口不可用；这是当前单机架构的可接受约束。

### 2.2 推荐候选，尚未最终确认

- 使用 Tailscale 私有覆盖网络和 Tailscale Serve，把本机 Web 的单一 HTTPS 入口只开放给获邀成员；不做校园网公网端口映射。
- 只暴露 Next.js Web；FastAPI 绑定回环地址并由 Web 同源转发。PostgreSQL、MinIO、Docker、Worker 和 Codex 凭据路径不对协作者网络开放。
- 若既有 VPN 无法与 Tailscale 共存，再评估 Cloudflare Tunnel + Access；它不是当前已确认依赖。

### 2.3 尚未知/待实测

- 已知现用代理客户端为 FlClash，且用户确认 Windows 上“虚拟网卡/TUN”当前关闭；仍未知当前版本、是否同时开启系统代理，以及 Docker/Codex 是否能沿用该联网路径。
- Tailscale 在双方校园网/NAT/VPN组合下建立直连还是经中继；中继速度只能实测。
- 可信登录的具体实现、所有者角色如何绑定账户、Tailscale 身份是否只做网络准入而不承担应用授权。
- Next.js/FastAPI 的最终端口和生产启动命令；文档示例端口不得当作已实现事实。

## 3. 实施措施

1. 更新总架构的已确认决定、总体图、关键数据流、规划文件树、风险、验证门槛和待讨论项。
2. 更新内部模块契约：把提交与批准拆成两个用例，明确 Worker 无权领取待批准 Job。
3. 更新数据模型：加入 `AWAITING_OWNER_APPROVAL`、所有者批准/拒绝审计字段和状态迁移。
4. 更新 HTTP 契约：创建 Job 返回待批准；增加所有者批准和拒绝接口、权限错误和验证标准。
5. 更新 Codex 认证事实源：说明远端提交不传递凭据，所有者批准只开放本机队列资格，凭据仍由本机执行节点在 Trial 生命周期内解析。
6. 新增远程接入运维事实源，给出校园网 + 既有 VPN 下的推荐拓扑、最小暴露面、Tailscale 配置步骤、检查命令、故障判断和 Cloudflare 备选触发条件。
7. 更新 Handoff，使当前确认状态、待实测风险和下一步与权威架构一致。
8. 执行文档引用、状态词、旧流程残留、diff 空白和 Git 状态检查，并把实际结果写回本记录。

## 4. 需要修改的文件树

```text
E:\9.1agent_exam\
├─ HANDOFF.md
│  # 下一窗口恢复状态；记录本次已确认流程和仍待实测网络条件
└─ docs\
   ├─ actions\
   │  └─ 2026-09-05-remote-submission-owner-approval.md
   │     # 本次措施、范围、偏差和验证证据
   ├─ architecture\
   │  ├─ ARCHITECTURE.md
   │  │  # 全局拓扑、已确认决定、关键流、规划树、风险和验证门槛
   │  ├─ MODULE_CONTRACTS.md
   │  │  # Job Submission、Owner Approval、Repository、Worker 的内部契约
   │  └─ DATA_MODEL.md
   │     # Job 审批字段、状态机、领取约束和数据库验证
   ├─ interfaces\
   │  ├─ HTTP_API.md
   │  │  # 远端提交、所有者批准/拒绝、查询和权限响应契约
   │  └─ CODEX_AUTHENTICATION.md
   │     # 远端提交/批准与本机凭据解析之间的保密边界
   └─ operations\
      └─ REMOTE_TEAM_ACCESS.md
         # 私有远程入口、校园网/VPN共存、暴露面和诊断步骤的唯一运维事实源
```

## 5. 模式与模块关系

- **State 模式**：`domain/job.py` 规划路径定义 `AWAITING_OWNER_APPROVAL → QUEUED`；PostgreSQL 约束和 Job 状态事件保存同一规则；提交、批准、Worker 复用它，不各自解释状态。
- **Repository 模式**：`ports/repositories.py` 提供待批准创建、所有者决定和 Worker 领取所需的小接口；`adapters/persistence/postgres.py` 负责事务、并发版本和审计事件。
- **Adapter 模式**：Tailscale Serve 或未来 Cloudflare Tunnel 只作为本机 Web 入口的网络 Adapter；应用用例不依赖特定厂商。当前只记录 Tailscale 推荐候选，不把未确认产品写成正式依赖。
- **深模块边界**：Owner Approval 只处理授权决定和排队，不读取 Codex 凭据、不启动 Docker，也不参与 Harbor 编排。

## 6. 修改后自验证方式与成功标准

| 检查 | 方法 | 成功标准 | 当前结果 |
|---|---|---|---|
| 本地检查点 | `git show --stat --oneline a2e85bb` | 能定位用户要求的更新前本地提交，且未执行 push | 通过：提交可读取，13 个文档文件、877 行新增/31 行删除；本轮没有 push |
| 初始状态一致性 | 搜索 `POST /jobs`、`QUEUED`、`AWAITING_OWNER_APPROVAL` | 创建 Job 不再直接进入 `QUEUED`；Worker 仅领取已批准 Job | 通过：权威架构/接口/Handoff 中未找到“创建 QUEUED”、`[*] → QUEUED` 或 `submit_job.py → QUEUED` 残留 |
| 批准边界 | 对照总架构、模块、数据、HTTP | 批准/拒绝只允许评测机所有者；批准才排队；决定可审计 | 通过：四份权威文档一致写明所有者、决定事务、状态事件和 `403 OWNER_APPROVAL_REQUIRED` |
| 秘密边界 | 搜索 `auth.json`、数据库/制品/HTTP描述 | 远端请求不接触凭据；只在本机执行节点临时解析 | 通过：认证事实源已同步；高风险 key/token 形态扫描无匹配 |
| 网络暴露面 | 人工核对运维文档 | 只开放 Web；数据库、MinIO、Docker、Worker、凭据路径均不开放 | 通过（文档）：暴露面表和双机反向检查已写明；未执行网络实测 |
| VPN/校园网诚实性 | 核对 Tailscale、FlClash 与 Mihomo 官方资料及措辞 | 明确可能冲突、中继降速和必须实测；不宣称已连通 | 通过（文档）：现用客户端已固定为 FlClash；按系统代理/TUN分开配置，要求检查最终运行配置并在 Docker 内另测；Tailscale 仍是候选 |
| 文档链接 | 解析本轮 8 个文档的本地 Markdown 链接并执行 `Test-Path` | 导航和 Handoff 能定位运维事实源 | 通过：检查 8 个文件、84 个本地链接，无缺失 |
| 文档格式 | `git diff --check` + 行尾空白搜索 | 无空白错误 | 通过：无空白错误；仅有 Git 提示未来可能按配置把 LF 转为 CRLF |
| 工作区范围 | `git status --short`、`git diff --stat` | 只包含本行动记录列出的文档改动，无业务代码或秘密 | 通过：6 个已跟踪文档修改、2 个新文档；均在本记录文件树内 |

## 7. 自验证情况

- `git show --stat --oneline --summary a2e85bb`：确认更新前检查点为 `a2e85bb docs: reconcile evaluation architecture records`，未执行远程推送。
- 旧流程残留搜索：在 `docs/architecture`、`docs/interfaces` 与 `HANDOFF.md` 中搜索直接创建/初始进入 `QUEUED` 的旧写法，无匹配。
- 新流程搜索：总架构、模块契约、数据模型、HTTP、认证、运维和 Handoff 均能定位 `AWAITING_OWNER_APPROVAL`；Owner Approval 共用同一状态含义。
- 本地链接检查：第一次脚本因根目录 `HANDOFF.md` 的父路径为空而误报；修正为以 `.` 解析根目录后重跑，结果为 `LINK_CHECK_OK files=8 local_links=84`。
- `git diff --check` 与 `[ \t]+$` 搜索：无空白错误。Git 的 LF/CRLF 提示是现有换行配置提示，不是 diff 错误。
- 高风险凭据形态扫描：对本轮 8 个文件搜索长 `sk-`、`ghp_`、Bearer 和 refresh token 赋值形态，无匹配。
- 用户补充 FlClash 后，核对其官方仓库/中文字段与 Mihomo TUN/DNS 文档；运维文档已加入系统代理优先方案、TUN 路由/DNS排除片段、最终配置检查和失败回退条件。
- `git status --short`：只出现本记录第 4 节列出的 6 个修改文件与 2 个新文件；未修改业务代码、依赖、网络、VPN、防火墙或真实秘密配置。
- 发布前检查：当前分支为 `main`，远程目标为 `origin`（GitHub 项目仓库）；用户已明确授权本次本地提交和推送，具体提交哈希与远程结果以 Git refs 为准。
- 未运行 Tailscale、Cloudflare、双机网络测试、应用测试或真实 Trial；本次只能宣称文档对账通过。

## 8. 计划偏差与遗留风险

- 初次链接验证脚本没有处理根目录文档的空父路径，导致误报；脚本修正后完整重跑通过，未改变产品文档。
- 对账时发现认证事实源仍可能让人误解为所有者必须重新手动提交，因此把 `CODEX_AUTHENTICATION.md` 纳入范围，明确“远端提交/批准不携带凭据，只有本机 Worker 建立 Trial 时解析”。这属于同一已确认安全边界的同步，不改变认证政策。
- 文档首次收尾后用户补充现用代理客户端为 FlClash，因此重新打开本记录，并把泛化 VPN 说明具体化为 FlClash“系统代理”和“TUN”两条路径；仍未假定用户当前版本或开关状态。
- 未经用户确认，不安装 Tailscale/Cloudflare 软件，不修改现有 VPN、校园网、路由器或 Windows 防火墙。
- 文档更新只能确认设计一致性，不能证明校园网、FlClash 与 Tailscale 已经连通；实际接入仍需在最终端口、登录方式、FlClash 版本/TUN状态明确后做双机测试。
