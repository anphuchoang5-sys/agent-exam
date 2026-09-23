# 2026-09-22 准备五道新题的运行镜像

## 状态与情况说明

状态：Completed（2026-09-22；五题固定镜像与无模型 Dockerfile 构建均通过，完整新 Trial 未运行）。

来源请求：用户要求把五道新题配置到可以实际运行。五题已通过固定 Fork 三补丁资格门禁，并已由 owner 登记到当前目录；资格验证结束后镜像曾按计划删除。2026-09-22 新批次中三题在 Harbor 的 Docker Compose 构建阶段失败，原因是本机缺少固定基础镜像，现有阿里云镜像加速源返回 HTTP 403；任务容器和 Codex 未启动。

本轮范围：只准备 `python__mypy-15131`、`15139`、`15184`、`15208`、`15876` 的既有固定摘要镜像，做不调用模型的环境构建检查；不改题目、白名单、固定摘要、评测 Job/Run，不重试失败批次。启动前五个固定镜像均不在 Docker 本地缓存。Docker Desktop 代理已指向 `127.0.0.1:7890`；该端口可到达 Docker Hub，显式原始仓库地址的固定镜像 manifest 查询成功。磁盘 C/D 余量分别约 55/44 GiB。当前工作树另有未提交增量，须保留。

## 实施措施与完成标准

1. 从产品白名单读取五个 `instance_id → 镜像@sha256`，串行从显式原始仓库拉取，每个镜像完成后核对本地固定摘要；先用一题验证该方式不会被现有镜像加速源拦截。
2. 用生产任务 Dockerfile 的同等构建步骤做不调用模型的构建检查。显式原始仓库地址可拉取，但规范 `FROM` 引用一度仍走失效镜像源并返回 403；因此精确备份 Docker Engine 配置，仅移除这一项，然后受控重启 Docker Desktop。重启前无排队/活动 Job；专属 PostgreSQL/MinIO 容器的重启策略均为 `no`，故先按现有停止流程让 Worker 退出，Desktop 重启后按现有启动流程恢复存储并重启 Worker，再检查 Web/API。
3. 五题逐一核验完成后，核对 Web/API/存储/Worker 与目录正常，更新 `HANDOFF.md` 和本机 Docker 运维文档的当前时点事实。

完成标准：五个产品固定镜像摘要可在当前 Docker 引擎中读取；五个对应基础环境 Dockerfile 都能完成构建；没有创建新 Job、调用模型或改写已失败证据。

## 需要修改的文件树与状态

```text
docs/actions/2026-09-22-prepare-five-task-runtime-images.md # 本轮措施、实际运行证据和限制
HANDOFF.md                                              # 已更新当前运行镜像与失败批次的时点状态
.tmp/daemon-before-five-task-images.json                 # 当前 Docker Engine JSON 的精确回退备份（不含凭据）
.tmp/daemon-for-five-task-images.json                    # 仅移除失效镜像源的候选配置，用于回读校验
docs/operations/LOCAL_DOCKER_ENVIRONMENT.md              # 同步本机 Docker 代理、镜像源和磁盘余量的当前事实
C:/Users/YINGYI/.docker/daemon.json                     # 仅移除失效 registry-mirrors；保留其余键
Docker Desktop 本地镜像缓存                              # 五张固定摘要基础镜像，按白名单身份准备
```

不新增产品 Module、Interface、数据库表或设计模式；现有 Task Catalog 固定镜像身份由 Harbor Execution Adapter 消费。Docker 全局配置调整前已把实际路径、影响和验证方式补入本文件。

## 自验证方式

- 每题 `docker image inspect` 的固定摘要引用返回成功，并与 `FIXED_TASK_IMAGES` 相同；不以 `latest` 标签替代摘要。
- 对每题运行无模型 Dockerfile 构建检查：固定基础镜像、`collect_patch.sh` 拷贝、`/testbed` 工作目录及权限步骤均完成，退出码 0；失败按镜像来源、构建命令和本地资源区分。
- 只读核对 PostgreSQL/MinIO、Web/API、Worker 状态与六题目录；已失败 Job 不改变，排队/活动 Job 为 0。
- 文档空白检查和工作区差异核对，不覆盖其他现存未提交变更。

## 自验证情况

- 只读预检：Docker Desktop `desktop-linux` 运行；C/D 空间约 55/44 GiB；五个白名单固定摘要在当前 Docker 引擎均缺失；阿里云镜像源 `/v2/` 返回 403。FlClash 实际监听 `127.0.0.1:7890`，经该代理原始 Docker Hub `/v2/` 返回预期 401，显式 `registry-1.docker.io/...@sha256` manifest 查询成功。
- 经 7890 代理按五个白名单摘要从显式原始仓库串行拉取，五次命令均成功。第一题 `15139` 的直接仓库引用可以本地 `image inspect`，但白名单的规范引用仍不能本地解析；使用该题真实生成的 Dockerfile 做无模型构建返回 1，错误含原镜像源的 403。因此单纯拉取别名不足以打通正式构建，需移除失效镜像加速配置。
- 重启前 Docker Engine 配置位于用户 `.docker/daemon.json`，仅有 `builder`、`experimental`、`registry-mirrors` 三键；后者是当时唯一加速源。PostgreSQL/MinIO 容器均为 `restart=no`；重启前数据库 Job 状态为已完成 2、失败 1，无活动/排队 Job。
- 原配置先精确复制到忽略的 `.tmp/daemon-before-five-task-images.json`，SHA-256 与原文件一致；候选配置只删除失效的 `registry-mirrors`，`builder` 和 `experimental` 保留。现有 `Stop-AgentExam.ps1` 输出 PostgreSQL/MinIO 已停止、Worker 停止标记已请求；进程枚举确认 Worker 0 个。写入候选后 `docker desktop restart --timeout 120` 退出 0；`docker info` 镜像源为 `null`。现有 `Start-AgentExam.ps1` 输出专属 PostgreSQL/MinIO 运行、停止标记清除、活动 Job 0；正式 Worker 随后重启，检查为 2 个 Python 父子进程、1 棵 Worker 进程链。
- 第一题 `15139` 的规范摘要引用拉取成功且 `docker image inspect` 可解析；同一真实生成 Dockerfile 的无模型 `docker build` 已从之前的 403 失败变为退出 0。其余四题规范引用拉取成功且逐题检查 `docker image inspect` 与同等 Dockerfile 构建均退出 0；五题最终独立固定摘要检查为 5/5。没有修改固定摘要、白名单、数据库或真实 Job。
- 原失败 Trial 的完整 Harbor Compose 命令结构仍可从结果元数据确认，但所需 7 个 Compose 文件中有 4 个临时文件已被 Harbor 清理；尝试精确复验时预检报 `Compose input missing`，**未运行该命令**，不得记为通过。五题 Dockerfile 的构建检查是本轮实际通过范围；完整新 Trial/模型调用未执行。
- Docker 重启后生命周期状态为初始化完整、PostgreSQL/MinIO 运行、活动 Job 0、停止标记不存在；Web `127.0.0.1:3000/`、Backend `127.0.0.1:8000/openapi.json`、私有 HTTPS `/` 均返回 200。主库目录仍 6 题、Job 3、Run 5、排队与活动 Job 0，原失败批次仍为 `FAILED`。Docker 数据所在 E 盘当前可用约 4.22 GiB；这只证明当前构建可完成，未来真实批次的峰值空间尚未验证，应作为容量风险保留。
- 最终核对：Docker 原配置备份含唯一旧镜像源，新配置无 `registry-mirrors`，`builder` 和 `experimental` 值逐项保持一致；生命周期再次返回两项存储运行、Worker 停止标记不存在，唯一 Worker 进程链仍在。`HANDOFF.md` 与 `LOCAL_DOCKER_ENVIRONMENT.md` 的 `git diff --check` 通过（仅有 Git 换行符提示），本行动文档无尾随空白；其他原有未提交改动保留。首次文档检查脚本误把标题行数组当作单个布尔值而退出 1，修正检查表达式后返回 `final_doc_checks=OK`；这是检查方法错误，不是项目文件验证失败。
