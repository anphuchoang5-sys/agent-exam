# 任务 05 T2：代理回复测量修正与新 scope 实测

> 状态：本轮已收口。**固定 Harbor 最小 Trial 的脚本 13/13 PASS、`status=verified`；任务 05 完整 T2 验收仍未签收**，因为“其他 Trial”没有活体目标，只有缺席名称的不可达读数。按“一片完成再进下一片”停在 T2，未进入 S9/S10/S11。前轮事实见[测量复测记录](2026-09-22-task05-t2-measurement-retest.md)。

## 情况说明

用户已批准“仅修 T2 测量方法并重测”，现明确允许在需要时启动容器做真实测试。上一轮固定 Harbor Trial 原脚本 12 PASS / 1 FAIL、`status=failed`；失败为经代理回复 `NO-REPLY`。同一主容器的独立诊断能经代理收到 `+PONG\r\n`，但诊断与脚本同时改变了请求换行（CRLF/LF）和读取长度（7/16），尚未定因。原脚本仍是 Git 中未改的版本。用户要求问题及解决方案一起记录。

## 实施措施

1. 保持全部 13 个逐项判定的目标、期望、服务与失败即停规则不变，仅在 `t05_through_proxy()` 中发送协议完整的 `PING\r\n`，并用有时限的 Bash `read` 读取完整响应行，不再等待固定 16 字节。
2. 先做离线正反例：真实 `+PONG\r\n` 必须判 `PONG`；无回复、错误回复不得判 `PONG`；`bash -n` 与脚本的期望调用 diff 核对通过后才启动 Docker。
3. 创建全新 scope `t05-harbor-20260922-04` 的忽略目录，沿用上轮固定 Harbor、侧车 LF+DNS 适配、两网络最小形态及宿主 inspect/清理测量；仅合成本轮假值，不接 CLI/真 Key/真实供应商。
4. Trial 结束时无论成败记录原始输出、宿主证据、镜像卷差异、Harbor 拆除 argv、独立残留查询及 SHA-256；不因旁证改变 Trial verdict。
5. 任一硬边界或断言失败，按阶段计划停在 T2，记录明确的问题与可证解决方案，不进 S9/S10/S11。

## 需要修改的文件树

| 路径 | 职责 |
|---|---|
| `docs/actions/2026-09-22-task05-t2-response-measurement.md` | 本轮行动、实际命令/结果、问题与解决方案 |
| `apps/backend/tests/providers/runtime/t2-assertions.sh` | 仅修原代理回程读数函数，不改变 13 项判定和期望 |
| `apps/backend/tests/providers/runtime/README.md` | 更新 Harbor 实测状态、CRLF/整行读取约束及其他 Trial 需活体目标的限制 |
| `.tmp/t05-harbor-minimal/t05-harbor-20260922-04/` | 忽略的本轮驱动、Compose 和原始证据，不覆盖前轮 |
| `docs/LLY/03-progress/PROGRESS_LOG.md` | 本轮结束后同步真实状态 |
| `.scratch/ui-catalog-providers/issues/05-fake-provider-secure-execution-chain.md` | 任务 05 Comments 追加真实结果与提交号 |

不新增业务 Module、Interface、数据库表、顶层目录。现有 `DockerEnvironment`、`network.export_sidecar()`、`t2-assertions.sh` 是唯一接缝，保持最小改动。

## 自验证方式与成功标准

- `bash -n` 通过，离线正例/无回复/错误回复全部区分；`t05_expect` 调用名及期望与修改前逐字一致，13 项不减少。
- 固定 Harbor Trial 必须真正输出 `status=verified` 且 13/13 PASS；宿主代理→假上游、假上游日志来源、私有文件/进程正反对照及结构 inspect 同时成立。其他 Trial 无活体目标时明确留为未验证，不外推。
- 本轮所有容器/网络按名称+task+scope 三重核对后交 Harbor 常规路径拆除；镜像/卷清单差异如实记录、非本轮资源不删除、残留为零；原始文件 SHA-256 清单独立复核一致。
- 任一未取得则不写 T2 验证通过，不继续 S9/S10/S11，不带真 Key。

## 自验证情况

### 离线区分测试与工具问题

仅 `t05_through_proxy()` 的测量代码改变：由 `PING\n` + `head -c 16` 改为 `PING\r\n` + `IFS= read -r -t 3 line`，外层 `timeout 5` 与 `PONG`/`NO-REPLY` 原期望保留。`t05_expect` 的 **13 行调用逐字一致**；`bash -n` exit 0。初始离线脚本误调用 Windows WSL 的 `bash.exe`，报 `Bash/Service/CreateInstance/E_ACCESSDENIED`（exit 127）；指定 Git Bash 后，`source /dev/stdin` 在该环境不存在，又报 `No such file or directory`（exit 127）。二者是**离线试具错误**，均未创建 Docker 资源；最终把函数字符串直接交给 Git Bash `-c`，实测原文：

```text
old=(0, 'PONG', [b'PING\n'], 4.15, '')
good=(0, 'PONG', [b'PING\r\n'], 0.12, '')
bad=(0, '-ERR bad', [b'PING\r\n'], 0.12, '')
silent=(0, 'NO-REPLY', [b'PING\r\n'], 3.12, '')
status=verified
bash_n_exit= 0 expectations= 13 unchanged= True stderr= ''
```

旧读法在本地假监听端关闭连接后也能得到 `PONG`，所以**不能仅凭旧读数断言固定长度一定丢数据**；已实证的是新读法发送 CRLF、快速返回，坏回复与无回复仍不是 `PONG`。新 `.tmp` 的 `measurement-regression.py` 是可复核的离线试具，不是产品入口；其末次原始 stdout 在 `measurement-regression-output.txt`。

### 真实 Harbor 命令和 Trial 原始输出

现有 worktree `E:\9.1agent_exam\runtime\lly-dev-verify`、分支 `lly/dev`；启动前只读确认同名项目容器/网络/卷为空，镜像预检命中本机缓存。未新建 worktree、未切分支。固定 Harbor revision `6af8d6e31eced13b93849cdf80feeadf24603d15`；`export_sidecar()` 从该 revision 导出 LF+DNS 适配上下文并设置 `_EGRESS_CONTROL_SIDECAR_CONTEXT_PATH`。脚本候选从工作树读取、标准化 CRLF 为 Git blob 的 LF 形式，上传至 `/opt/t2-assertions.sh`，SHA-256 `1954c033834f094167c6059094450878f622472089372226261ae4f7f2c5df08`。驱动命令**退出 0**，控制台原文保存在 `.tmp/t05-harbor-minimal/t05-harbor-20260922-04/probe-console.txt`：

```powershell
$env:PYTHONPATH='E:/9.1agent_exam/runtime/lly-dev-verify/apps/backend/src'
& 'E:/9.1agent_exam/framework/harbor/.venv/Scripts/python.exe' '.tmp/t05-harbor-minimal/t05-harbor-20260922-04/probe.py' 2>&1 | Tee-Object -FilePath '.tmp/t05-harbor-minimal/t05-harbor-20260922-04/probe-console.txt'
exit $LASTEXITCODE
```

原始 Trial 命令：

```bash
T05_PROXY_HOST=proxy T05_PROXY_PORT=8080 T05_UPSTREAM_HOST=fake-upstream T05_UPSTREAM_PORT=8080 T05_PRIVATE_PATH=/tmp/agentexam-private/fake-provider.json bash /opt/t2-assertions.sh
```

Trial 实际 stdout（退出 0，stderr 空；**13 PASS / 0 FAIL**）：

```text
readings
1	workload -> proxy entry	OPEN
1	  reply through proxy	PONG
2	public 1.1.1.1	CLOSED
2	public 223.5.5.5	CLOSED
3	workload -> fake upstream	CLOSED
3	workload -> other trial	CLOSED
3	host gateway	CLOSED
3	metadata	CLOSED
7	private path	ABSENT
7	marker in /proc/*/environ	0
7	marker in /proc/*/cmdline	0
7	sentinel files	0
7	docker.sock present	no
verdicts
PASS a1 workload to proxy entry
PASS a1 reply through proxy
PASS a2 public 1.1.1.1
PASS a2 public 223.5.5.5
PASS a3 workload -> fake upstream
PASS a3 workload -> other trial
PASS a3 host gateway
PASS a3 metadata
PASS a7 private path
PASS a7 marker in environment
PASS a7 marker in argv
PASS a7 sentinel files
PASS a7 no docker socket
status=verified
```

实际 `extra-compose.yaml` 的服务与网络（全清单在本轮 `.tmp` 并纳入 SHA-256）：`main` 显式 `networks: [internal]`；`proxy` 使用缓存的 `redis:7-alpine`，`networks: [internal, egress]`，持有仅在其容器内的两种假标记，以 `nc -lk -p 8080 -e /tmp/agentexam-proxy-marker-relay.sh` 转发到 `fake-upstream:6379`；`fake-upstream` 为缓存的 `redis:7-alpine` verbose Redis，`networks: [egress]`；Harbor 侧车显式 `networks: [egress]`；`internal: true`，`egress: false`。四服务、两网络均标 `agentexam.task=05`、`agentexam.scope=t05-harbor-20260922-04`。没有 `ports`、宿主 bind mount、Docker 套接字或真 Key。`kernel-probe-command.json` 原文是 `docker container run --rm alpine:3.23.4@sha256:5b10f432... sh -c ...`，无挂载、端口或 socket。

### 宿主侧 inspect 与正对照

```text
agentexam-t05-topology_internal  Internal=true:  main + proxy
agentexam-t05-topology_egress    Internal=false: proxy + fake-upstream + harbor-docker-egress-control-sidecar
```

`main`、`proxy`、`fake-upstream` 均 running，侧车 running/healthy。四个容器的 `HostConfig.PortBindings={}`、`Mounts=[]`，标签均为 task `05` + 本轮 scope；网络 `Internal` 与双标签均由 `docker inspect` 取得，原始文件为 `inspect-containers.json`/`inspect-networks.json`。容器镜像 ID：`main` `sha256:db9f02c6bde9fa90cc8074c92754b2b046947392f1a857726e77f041febb7b82`，`proxy`/`fake-upstream` `sha256:487efc0616382465781b8fdc3d6d1db449e6fd80ae23bf48432a2da6b6929908`，侧车 `sha256:dd1cd5ac17830d6ebcf4117ac024792aac92ce428a830270d57afe4fce6b8dd3`。RepoDigests：main `debian@sha256:3783cc01769c7b2b1b83a5c5ad96c815348e28ed7da68e2e3687004faa906251`，Redis `redis@sha256:6ab0b6e7381779332f97b8ca76193e45b0756f38d4c0dcda72dbb3c32061ab99`，本地侧车为空；详见 `image-identities.json`。

`host-side-checks.json` 五项均 exit 0 且符合期望：代理→假上游 `PONG`；代理私有文件的假 provider/假哨兵均 `PRESENT`；代理侧 relay 进程 `PRESENT`、main 侧 `ABSENT`。假上游自己的日志增量记下 `Accepted 172.22.0.4:...` 和 `cmd=ping`，该 IP 与 proxy 的 egress IP 一致，见 `upstream-verdict.json`，`passed=true`。独立诊断经 main→proxy 读到 `+PONG\r\n`。这些是旁证，正式 Trial 本次也独立取得 `PONG`。

### 拆除原文、清单差异与 SHA-256

Harbor 在拆除前记录了四个容器 ID 与两个网络 ID，并核对每一项名称+task+scope；常规拆除 argv **原文**如下（启动前还对同一空项目执行一次 `down --remove-orphans`）：

```json
["docker","compose","--project-name","agentexam-t05-topology","--project-directory","E:\\9.1agent_exam\\runtime\\lly-dev-verify\\.tmp\\t05-harbor-minimal\\t05-harbor-20260922-04\\environment","-f","C:\\Windows\\Temp\\tmpx2md6v4n\\agentexam-t05-topology-docker-compose-resources.json","-f","E:\\9.1agent_exam\\framework\\harbor\\src\\harbor\\environments\\docker\\docker-compose-prebuilt.yaml","-f","E:\\9.1agent_exam\\runtime\\lly-dev-verify\\.tmp\\t05-harbor-minimal\\t05-harbor-20260922-04\\extra-compose.yaml","-f","C:\\Windows\\Temp\\tmpcqt92cgz\\docker-compose-environment.json","-f","C:\\Windows\\Temp\\tmp0g6ihk4y\\docker-compose-mounts.json","-f","E:\\9.1agent_exam\\framework\\harbor\\src\\harbor\\environments\\docker\\docker-compose-egress-control.yaml","down","--rmi","local","--volumes","--remove-orphans"]
```

镜像/卷清单拆除前后分别都是 **90 镜像、16 卷**；`images.added=[]`、`images.removed=[]`、`volumes.added=[]`、`volumes.removed=[]`。本轮 `cleanup.json` 的容器/网络/卷为 `[]`；随后独立执行 `docker ps -a`、`docker network ls`、`docker volume ls`，同时以任务标签与 scope 过滤，三条原始输出全为空，残留 **0**。没有删已有镜像、其他项目卷或既有容器。证据 `.tmp/t05-harbor-minimal/t05-harbor-20260922-04/manifest.json` 收录 **32 个**原始文件的路径与 SHA-256（含追加的离线正反例 stdout）；因 `Tee-Object` 在 manifest 首次生成时尚未退出，`probe-console.txt` 哈希随后变更，进程退出后已按最终文件修正，独立复核 **32/32 匹配**。`.tmp` 不进 Git。

### 未完成项、问题与解决方案

1. **关键验收缺口：其他 Trial 没有活体目标。** `t05-other-trial` 在该次 Compose 中不存在，因而脚本的 `PASS a3 workload -> other trial` 只是“名称不可达”，不能证明对另一个实际运行 Trial 的隔离。这不是实测失败，但不能写成完整第 3 条已证成。若要完成原验收，须取得对额外受控活体目标及其独立网络/Trial 的明确授权，给目标与观测端都加任务标签和新 scope，在固定 Harbor 内做通/不通正反对照，然后精确清理；当前硬范围只列 `internal`/`egress` 与 `main`/`proxy`/`fake-upstream`，**本轮没有擅自扩建**。在这个缺口签收前，按计划不进入 S9/S10/S11。
2. **测量函数修复已实测有效，但两项子因素未单独定因。** 本轮同时修正请求 CRLF 和固定字节读取，离线/Harbor 正例均通过且负例仍失败；不声称“仅 `head -c 16`”或“仅 LF”就是前轮唯一根因。原期望、13 条判定与网络策略未放宽。
3. **仍未验证**：真实 Codex CLI/模型、真 Key/真实供应商、产品化 `service.py` 网络接线、跨 Trial 活体隔离及 S9/S10/S11。没有读取真实 Key/登录文件，未发真实供应商请求、未充值，未修改共享 Docker/WSL/代理/防火墙。
