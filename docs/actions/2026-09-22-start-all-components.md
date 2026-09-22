# 2026-09-22 启动 AgentExam 全部运行组件

## 状态与情况说明

状态：Completed（2026-09-22 19:04 +08:00；正式持续 Worker 与现有服务同时运行）。

来源请求：在上轮完成现有 Web/API/存储启动和旧进程清理后，用户明确要求“全部项目进行启动”。本轮“全部”包含现有正式 Worker 持续循环；Worker 会领取以后获 owner 批准的 Job，可能使用现有 Codex 登录调用模型。用户本轮已明确授权启动。当前分支 `agent+api` 有其他未提交改动，须原样保留。

启动前只读事实：专属 PostgreSQL/MinIO 初始化完整且运行，Web `127.0.0.1:3000`、Backend `127.0.0.1:8000` 已监听；主库任务 6，排队和活动 Job 均为 0；本项目无 Worker 进程，停止标记不存在。正式 Worker 的本地数据、Codex 归档、认证文件和证据目录的配置路径均存在；不读取或输出认证正文。运行模式复用现有 `eval_platform.delivery.worker.runtime agentexam-owner --loop --stop-file ...`，应用代码不改。

## 实施措施

1. 复用当前临时本机启动入口的环境装配，增加 Worker 模式：从现有 `.env` 与 owner 私有密码文件向进程内提供应用数据库和对象存储连接；工作目录为 `apps/backend`，运行现有正式 Worker 模块和既有停止文件路径。
2. 只在确认无现有 Worker、存储可用且停止标记不存在后启动一个持续 Worker；使用既有生产装配检查固定 Codex 归档、认证文件、Harbor/Fork 身份和任务数据源，失败即报告，不伪称启动成功。
3. 启动后核对 Worker 进程仍存活且只有一棵；Web/API/私有 HTTPS 与 PostgreSQL/MinIO 仍可用，队列和 Job/Run 计数未意外变化；同步 `HANDOFF.md` 当前运行快照。

完成标准：专属 PostgreSQL、MinIO、Backend 8000、Web 3000、私有 HTTPS 和一个正式持续 Worker 同时运行；当前队列为空且已有 Job/Run 不变；无重复 Worker，原工作区其他增量保留。

## 需要修改的文件树与状态

```text
docs/actions/2026-09-22-start-all-components.md # 本次全组件启动的措施与实际证据
HANDOFF.md                                 # 更新当前 Worker 与全组件运行快照
.tmp/start-current-backend.ps1            # 忽略的本机启动入口：增加复用相同私有环境装配的 Worker 模式
本机正式 Worker 进程                      # 调用现有 runtime.py/command.py 持续消费受控队列
```

不新增业务 Module、Interface、数据库表或设计模式；临时入口只负责已有 Composition Root 所需的进程环境。真实提供方扩展链的任务 05 后续阶段未因此视为完成。

## 自验证方式

- `Get-AgentExamStatus.ps1` 返回两项存储运行、停止标记不存在；本机和私有 HTTPS 页面返回 200，后端 OpenAPI 可读。
- 核对 Worker 生产装配进程持续存活、命令行包含固定 `agentexam-owner --loop --stop-file`，不存在第二个本项目 Worker；主库 `QUEUED`/活动 Job 仍为 0，Job/Run 计数与启动前一致。
- `git diff --check` 与 `git status` 确认本次文档修改无空白错误，其他未提交改动保留。若装配失败，记录实际失败并停止本次 Worker 启动，不将前台命令发出等同于成功。

## 自验证情况

- PowerShell 7 解析 `.tmp/start-current-backend.ps1` 无语法错误。现有本机入口只增加 `-Worker` 模式，保留后端默认启动路径；未修改应用业务代码。普通权限下 Windows 进程枚举返回拒绝访问，按已授权的本机启动操作使用提升权限启动并核对。
- 正式命令 `python -B -m eval_platform.delivery.worker.runtime agentexam-owner --loop --stop-file D:\AgentExamData\control\worker.stop` 已启动，启动会话持续运行。19:02:32 +08:00 创建的两个 `python.exe` 进程为同一父子链，命令行相同；未发现第二棵本项目 Worker。Worker 空闲时不打印周期输出，所以以持续存活、进程关系和数据库空队列为证据。
- `Get-AgentExamStatus.ps1` 返回初始化完整、PostgreSQL 与 MinIO 均为 `running`、`activeJobs=0`、`stopRequested=false`。本机 Web `/`、后端 `/openapi.json` 和私有 HTTPS `/` 实测均返回 200；Tailscale Serve 仍为 HTTPS 443 → `127.0.0.1:3000`，TCP 55432 → `127.0.0.1:55432`。
- 主库只读查询：`evaluation_tasks=6`、`evaluation_jobs=2`、`evaluation_runs=2`、`QUEUED=0`、活动 Job=0；与启动前相同。未提交新评测，未触发模型执行。`HANDOFF.md` 已更新为带时点的当前运行快照；服务在线状态仍需使用时重查。
- 最后再次枚举到 2 个 Worker `python.exe`、1 棵父子进程链，进程持续存活；`git diff --check -- HANDOFF.md` 通过（只有 Git 的 LF/CRLF 提示），`git status --short` 显示本次交接文档修改及本行动文档，其他原有未提交改动保留。行动文档完成并封存。
