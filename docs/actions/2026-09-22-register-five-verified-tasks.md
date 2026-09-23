# 2026-09-22 在现有 owner 流程登记五道已核验题目

## 状态与情况说明

状态：Completed（2026-09-22；五道新题通过既有 owner API 进入当前目录，网页目录与提交向导六题选择已核对）。

来源请求：通过现有所有者登记流程，将任务 04 已核验的五道新题加入当前运行目录，再核对网页选择结果。

当前事实：`agent+api` 工作区已有其他未提交改动，须原样保留。项目存储和后端运行，Web 本机页面可响应；运行数据库目前仅登记旧题 `python__mypy-15413` 一道。代码的 `TASK_PRESETS` 与固定镜像白名单均包含旧题加五道新题；任务 04 的历史三补丁门禁为五题 15/15 场景通过。当前 owner API 是 `POST /api/v1/tasks/register`，要求有效 owner 会话并调用既有 `TaskCatalog.register`；登记会将原始快照写入私有对象存储并发布 PostgreSQL 目录记录，不创建 Job，也不启动 Worker。

登记前需要 owner 在本机交互输入用户名与密码；不得在聊天、日志、命令行或文件中存储凭据。`docs/interfaces/HTTP_API.md` 对该端点仍写成只接受旧题，是与现行代码不符的描述。Web 的 owner 登记按钮只指向旧题，但任务目录与提交向导会从目录接口读取已登记题目；本轮使用现有 owner HTTP API 登记，不扩大产品 UI 行为。自动弹出的 PowerShell 进程没有可见窗口，第一次登录返回 401；随即确认任务表仍为 1 条并停止该进程。改为由 owner 在自己的 PowerShell 7 终端运行同一临时脚本并交互输入，助手只读取不含凭据的结果文件与数据库状态。owner 在可见终端再次运行后仍得到登录 401；只读核对确认数据库的 `owner` 账号存在、角色为 owner、处于启用状态，脚本登录字段和网页一致。同一次终端输入经当前数据库 Argon2 校验未通过，直接 HTTP 登录也为 401；认证版本为 3（初始值 1），9 月 21 日运行记录明确记载过一次本机 owner 密码恢复。`infra/.env` 的数据库连接值为空，首次诊断脚本误用该值而提前停止；修正为只读查询当前 PostgreSQL 容器后才得到上述有效双重结果。owner 随后明确选择使用项目既有本机恢复命令，恢复成功后继续登记。

## 实施措施

1. 登记前只读核对五个 preset、固定镜像、数据库现有题目和服务状态；确认无同身份记录后继续。
2. owner 在自己的 PowerShell 7 终端交互输入凭据，临时脚本使用现有登录和任务登记 HTTP 接口逐题提交五个固定 preset；仅在 owner 身份确认后发送写请求。遇到非 201 或身份冲突即停止，不绕过鉴权或直接写库。结束时注销临时会话。若中途失败，再次运行会只登记缺失的预设，先核对已完成条目。
3. 通过同一会话读取任务目录与提交选项，在网页中确认六题可见、可选择；另以数据库只读结果交叉核对。不得创建或批准真实 Job，也不得启动 Worker、调用模型或清理已有数据。
4. 将接口文档的固定预设说明改为当前六题事实，并在本行动记录登记结果、失败与剩余限制；核对原有工作区改动未被覆盖。
5. owner 报告确信现有密码正确而可见终端仍返回 401；在继续登记前，用本机交互诊断脚本以同一次输入分别核对当前数据库密码摘要与 HTTP 登录结果。只输出布尔校验结果和 HTTP 状态，不记录密码或摘要，也不擅自重置 owner 密码。
6. owner 已明确选择按现有本机恢复流程重设密码。临时入口先复用正式部署 ACL 和状态检查，再从 owner 私有 PostgreSQL 密码文件构造仅在该进程存在的 DSN，调用原有 `eval_platform.delivery.owner recover owner` CLI；仅在 CLI 成功后调用五题登记脚本。新密码仍由 owner 自己在交互终端输入，既有会话按原流程撤销。
7. 恢复成功后第一题登记返回 400，数据库仍为旧题 1 条。只读证据显示 8000 端口后端于 9 月 21 日 17:15 启动，其 OpenAPI 仍为更新前的单一模型 provider 结构；当前源码的六题预设已在仓库。先用当前源码和现有私有部署配置在备用回环端口启动并验明 OpenAPI，再替换本项目旧后端进程；随后重新运行幂等登记脚本。

完成标准：五个新身份各恰好一条、加旧题共六条；owner 目录和网页选择器都显示六题；`continuous` 允许六题选择；没有新增 Job/Run 或真实模型调用，原有文件改动保留。

## 需要修改的文件树与数据

```text
docs/actions/2026-09-22-register-five-verified-tasks.md # 本次登记措施、证据与结果
docs/interfaces/HTTP_API.md                           # 修正任务登记接口的当前固定预设描述
HANDOFF.md                                            # 更新当前运行目录的事实与接续入口
.tmp/owner-register-five.ps1                         # 临时本机交互脚本；只调用现有 owner HTTP 登录/登记/读取/注销接口，不入 Git
.tmp/owner-recover-and-register.ps1                  # 临时本机恢复入口；复用正式 owner CLI，成功后串行调用登记脚本，不入 Git
.tmp/start-current-backend.ps1                       # 临时本机后端启动入口；在进程内装配既有私有连接配置，可指定回环端口，不入 Git
.tmp/diagnose-owner-login.py                          # 临时本机交互诊断；核对数据库密码摘要与 HTTP 登录，不输出凭据
.tmp/verify-six-tasks-ui.mjs                         # 临时浏览器核对脚本；只读目录并在向导中选择，不提交
PostgreSQL evaluation_tasks                           # 现有任务目录表：每个固定题目一条
MinIO task_source_snapshot                            # 现有私有对象：每个固定题目的不可变源快照
```

模式关系：FastAPI 目录路由是 HTTP Adapter，`TaskCatalog.register` 是既有应用用例，PostgreSQL 与 MinIO 是其持久化 Adapter；临时脚本仅作 owner HTTP 客户端，不增加业务 Interface、数据库表或产品模块。

## 自验证方式

- 登记前后只读查询 `evaluation_tasks` 的 `instance_id` 和计数，结果应从旧题 1 条变为固定六题各 1 条；活动 Job/Run 数不增加。
- owner 登录后逐题检查 `POST /api/v1/tasks/register` 返回 201 和对应 `instance_id`；`GET /api/v1/tasks?limit=20` 返回六个唯一身份，详情和对象校验路径无错误。
- 已登录网页任务目录和三步提交向导显示六道题，`continuous` 选项可承载六题；只选择，不提交。
- 401 诊断脚本从本机终端读取一次密码；当前专属数据库 Argon2 校验与同一输入的 HTTP 登录各自给出通过/失败，足以区分本地存储、PowerShell 输入转换和后端配置路径。
- 若执行 owner 恢复，核对正式 CLI 返回成功、认证版本增加、旧会话数归零；随后的新密码登录及六题登记通过，且不在仓库或终端命令中出现密码。
- `git diff --check` 与 `git status --short`：只出现本任务文档和临时运行产物，既有未提交工作保留。HTTP 文档的相对链接可解析。

## 自验证情况

- PowerShell 7 脚本语法检查、Node 浏览器脚本语法检查、接口文档 `git diff --check` 已通过；网页首页可返回 200。
- 首次可见终端登录返回 401；当时尚未登记任何新题。数据库只读查询显示 `account=owner,role=owner,active=true` 与 `tasks=1`。
- 本机诊断确认同一次输入的密码摘要校验未通过且 HTTP 登录为 401；账号版本 3、摘要格式 Argon2id。诊断脚本初版因 `.env` 数据库连接值为空而未完成；改由 Docker 读取当前库后，owner 账号只读预检通过，用户终端完成了有效双重诊断。
- owner 明确选择本机恢复；新增临时恢复入口，PowerShell 语法检查通过，`-PreflightOnly` 已从正式私有凭据文件构造进程内 DSN 并成功 `SELECT 1`，确认它能连接当前数据库；该预检未恢复密码、未登记题目。
- 恢复命令成功，认证版本从 3 变为 4 且旧会话清零；新密码登录及读取原目录成功。第一道新题登记返回 400 后立即停止；数据库仍仅旧题 1 条、Job 2 条、Run 2 条。后端旧进程及旧 OpenAPI 结构表明运行代码过期，须刷新进程后重试。
- 当前代码后端先在备用回环 8001 成功启动，OpenAPI 的 provider 集合由旧进程单值变为当前代码双值；随后仅停止已核实的旧 8000 后端父子进程，并用同一入口在 8000 启动当前代码。8000 新 OpenAPI、任务登记端点和 Web 3000 均响应；源码固定任务预设 6 个，五道新题从配置的 Parquet 均能读取。备用 8001 进程已停止，owner 随后用新密码运行幂等登记脚本。
- owner 用恢复后的新密码在当前代码后端登录成功；五个固定 preset 的登记响应逐项为 201，对应 `python__mypy-15131`、`python__mypy-15139`、`python__mypy-15184`、`python__mypy-15208`、`python__mypy-15876`。脚本结果为 `state=completed`、`ui_verified=true`，目录响应含原题 `python__mypy-15413` 与五道新题共六个身份。
- PostgreSQL 独立只读核对：`evaluation_tasks=6`、`DISTINCT instance_id=6`，六个身份各 1 条；Job=2、Run=2，均与登记前相同。任务目录读取期间由现有 `TaskCatalog.list` 对每条源快照执行 MinIO `read_verified`，未报存储错误。owner 临时会话注销后为 0 条。
- 系统 Chrome 中 Playwright 实际打开 Web 任务页与三步新建向导：目录 6 题、已选择 6 题、`continuous(1–20)`、1 个现有 Agent 配置，确认页显示 `6 道题 × 1 个配置 = 6 个 Run`；输出 `UI_OK: catalog=6 selected=6 continuous=1-20 submitted=0`。仅核对选择，没有提交 Job 或触发 Worker/模型。
- 后端 `127.0.0.1:8000` 当前 OpenAPI 显示更新后的受控 provider 集合，Web `127.0.0.1:3000/?view=tasks` 返回 200。备用 8001 已停止。接口文档与 `HANDOFF.md` 已同步当前事实；工作区原有未提交改动保持原样。
