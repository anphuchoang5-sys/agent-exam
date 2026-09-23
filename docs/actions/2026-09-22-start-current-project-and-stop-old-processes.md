# 2026-09-22 启动当前项目并结束旧进程

## 状态与情况说明

状态：Completed（2026-09-22；当前 Web/API/存储与私有 HTTPS 可用，旧项目进程精确结束）。

来源请求：启动项目；启动成功后结束此前遗留的旧项目进程。工作区是 `agent+api`，已有其他未提交改动，须保留。操作前核对：专属 PostgreSQL 与 MinIO 均运行、初始化完整；后端在 `127.0.0.1:8000`、当前网页在 `127.0.0.1:3000`，另有旧网页在 `127.0.0.1:59336`、旧 Worker 自 2026-09-21 起运行。主库活动 Job 为 0。私有 Tailscale HTTPS 入口当时仍代理旧网页 59336，因此结束旧进程前须把现有入口切到已验证的新网页 3000，并保持已有 PostgreSQL TCP 55432 转发。

范围是现有项目的启动、健康核对、原有私有网页入口切换和精确结束旧进程；不新增网络入口、不提交评测、不批准 Job、不运行新 Worker 或模型。Worker 启动会消费已批准 Job 并可能调用模型，现有运行指南要求另行真实运行授权；本轮只结束确认空闲的旧 Worker。旧进程候选必须按工作区命令行、端口、启动时间和父子关系逐一核对，不能清理 Docker 容器或其他项目进程。

## 实施措施

1. 使用现有 `Start-AgentExam.ps1` 确认专属存储启动；只读核对活动与待执行 Job、六题目录、当前后端和网页响应。
2. 读取本机 Tailscale Serve 的当前配置与 CLI 用法，仅把现有私有 HTTPS 根路径代理从旧网页 59336 切到当前网页 3000；核对 PostgreSQL TCP 55432 转发仍在，且私有 HTTPS 页面可响应。
3. 在新入口成功后，按已核实的 PID/命令行/父子关系结束旧网页进程、空闲旧 Worker 和其旧终端外壳；主库再次确认排队和活动 Job 均为 0 后，对无法通过当前终端发送正常停止信号的旧进程使用精确 PID 结束。保留当前 3000/8000 进程及两项专属存储。
4. 复查新旧端口、项目进程、存储与 Job 状态，并同步 `HANDOFF.md` 的当前运行态；记录任何偏差。

完成标准：当前网页 3000、后端 8000、专属 PostgreSQL/MinIO 和既有私有 HTTPS 入口可用；旧网页 59336 与已核实的旧 Worker/外壳进程退出；TCP 55432 转发、六题目录和 Job/Run 数据不变。

## 实际修改的文件树与状态

```text
docs/actions/2026-09-22-start-current-project-and-stop-old-processes.md # 本轮操作顺序、证据、结果
HANDOFF.md                                                        # 当前运行入口与 Worker 状态快照
docs/operations/REMOTE_TEAM_ACCESS.md                            # 私有 HTTPS 当前转发目标、登录与回环端口事实
.tmp/serve-before-switch.json                                      # 忽略的临时 Serve 状态备份；仅用于精确核对原规则
Tailscale Serve HTTPS 根路径                                       # 现有私有入口从旧 59336 改指当前 3000；保留 TCP 55432
本机旧 Next.js 与 Worker 进程                                     # 核实身份后退出，不修改代码或数据库
```

不涉及新的业务 Module、Interface、数据库表或设计模式。现有关系仍是私有 HTTPS 入口 → Next.js → FastAPI → PostgreSQL/MinIO；Worker 是独立消费者。

## 自验证方式

- 运行现有生命周期状态命令，确认 PostgreSQL/MinIO `running` 且 `activeJobs=0`；只读查询目录六题与 Job/Run 计数。
- 本机 Web 3000、后端 8000 和私有 HTTPS 页面返回成功；Serve 状态显示 HTTPS 代理目标 3000、原 TCP 55432 转发未变化。
- 按端口和进程命令核对旧 59336 无监听、旧 Worker/外壳 PID 不存在，当前 3000/8000 仍监听；`git diff --check` 和 `git status` 确认原工作区改动未被覆盖。

## 自验证情况

- 现有 `Start-AgentExam.ps1` 返回 `operation=started`、初始化 `complete`、PostgreSQL/MinIO `running`、活动 Job 0、停止标记不存在。新网页 3000 返回 200；后端 8000 的 OpenAPI 有 29 条路径与当前受控 provider 集合。当前库任务 6、Job 2、Run 2，待执行与活动 Job 均为 0。
- Tailscale Serve 原状态已保存到忽略的临时备份；原 HTTPS 根路径代理旧 59336，TCP 55432 转发本机 55432。按现有 CLI 将同一私有 HTTPS 根路径改到新网页 3000 后，状态核对显示 HTTPS 主机未变、代理目标为 3000、TCP 55432 转发逐项未变；通过该私有 HTTPS URL 实际读取页面返回 200。
- 旧网页 PID 18460/48580 的命令行、父子关系和 59336 监听均核实后结束；旧 Worker PID 34852/47788 及旧终端 PID 53420 在主库再次确认排队与活动 Job 均为 0 后结束；9 月 21 日遗留的 owner 恢复终端 PID 57312 仅有专属 `conhost.exe` 子进程，也已结束。复查工作区命令行进程只剩当前 Web 3000 和 Backend 8000 两棵；59336 端口关闭，3000/8000 仍监听，Serve 仍代理 3000 且 TCP 55432 保持。
- 因本机 CLI 的 `serve get-config` 仅适用于 service 配置，最初两次备份尝试返回参数错误且未生成备份；改用只读 `serve status --json` 的现有配置作为精确备份与前后核对依据。首次结束旧 owner 恢复终端时发现子进程，未盲目结束；查明只有专属 `conhost.exe` 后再结束。旧 Worker 所在控制台无法从当前会话发送正常停止信号，而正式停止标记流程会连同存储一起停止，故在队列与活动 Job 均为 0 的条件下按用户要求精确结束旧 PID；未触碰当前服务或任何其他 Worker。
- 清理后再次实测：本机 Web 3000 返回 200、原私有 HTTPS 页面返回 200、后端 OpenAPI 有 29 条路径；私有 HTTPS 中转 `/api/v1/auth/me` 在无会话时返回预期 401，表明 Web 到 API 转发仍可达。生命周期状态为初始化完整、PostgreSQL/MinIO 运行、活动 Job 0、停止标记不存在；数据库仍为任务 6、Job 2、Run 2、排队与活动 Job 均 0。旧 PID 检查为 0 个存活，59336 无监听，当前 3000/8000 保持监听；Serve HTTPS 指向 3000、TCP 55432 指向原本机端口。
- `HANDOFF.md` 与远端接入文档已同步；`git diff --check` 无空白错误，行动文档无行尾空格，原工作区其他未提交改动保留。Worker 当前未运行，后续真实模型队列消费仍需按运行指南单独授权。
