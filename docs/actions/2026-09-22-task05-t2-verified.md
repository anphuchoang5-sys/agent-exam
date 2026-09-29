# 任务 05 T2：固定 Harbor 双网络实证

> 状态：**Blocked，T2 未验证通过**（2026-09-22）。文件名沿用阶段计划指定的交付名，不能把文件名或侧车启动成功解释为 T2 `verified`。本轮 Trial stdout 为 `status=failed`；按停止条件未重跑、未改断言，未进入 S9/S10/S11。

## 情况说明

用户要求在现有 `runtime/lly-dev-verify` worktree 的 `lly/dev` 上先合入最新 `origin/main`，再按[阶段计划](../LLY/01-plan/STAGE1_T2_S9_S10_S11_PLAN.md)顺序执行 T2 → S9 → S10 → S11。本片只处理 T2：在固定 Harbor 内测七条拓扑断言，不接 Codex CLI、真实模型、真实 Key 或真实供应商。沿用[负责人机器预案附三、附四](2026-09-21-task05-owner-machine-runbook.md)授权与停止条件。

开工事实：`git fetch origin` 后 `git merge origin/main` 成功；合并提交 `c66a79f`。开工前 worktree 为 `runtime/lly-dev-verify`、分支 `lly/dev`，工作树干净。固定 Harbor 为 `6af8d6e31eced13b93849cdf80feeadf24603d15`，跟踪文件无改动。`entrypoint.sh` 和 `bin/network-policy` 为 `i/lf w/crlf`，未触发计划 §3.1 的 `w/lf` 停止条件。需要本轮运行进一步验证修正后的上下文是否使侧车健康，以及拓扑断言是否成立；此前 T1 与侧车 127 记录均不能代替 T2。

## 实施措施

1. 在 `.tmp/t05-harbor-minimal/` 内建立本轮独立证据目录，使用唯一 `agentexam.scope`；所有本轮项目资源需同时符合名称、`agentexam.task=05` 和本轮 scope。
2. 探针使用固定 `DockerEnvironment`，将 `export_sidecar()` 从固定 Harbor Git blob 导出的侧车上下文显式交给 Harbor；不走会拒绝 `extra_docker_compose` 的产品入口。
3. Compose 中 `main` 仅接 `internal: true`，`proxy` 接 `internal` 与 `egress`，`fake-upstream` 仅接 `egress`；做题侧执行仓库原有 `t2-assertions.sh`，宿主补测代理→假上游、假上游来源日志、端口/挂载/标签/进程与私有文件隔离。
4. 记录镜像与卷清单、容器与网络 inspect、Harbor 原始命令与 Trial stdout。拆除前核对项目资源身份，只调用本 Trial 的 Harbor 常规拆除；随后按三重条件复核残留为零，绝不全局 prune。
5. 结果失败时只完成证据、精确拆除与状态回报，不继续 S9。提交/推送/PR 不得把失败片描述为已通过。

## 受影响文件树

| 路径 | 职责 |
|---|---|
| `docs/actions/2026-09-22-task05-t2-verified.md` | 本片行动、原始输出摘录、清理与停止结论；执行中持续更新 |
| `.tmp/t05-harbor-minimal/<scope>/` | 本机忽略目录：独立探针/Compose 和原始证据及 SHA-256 manifest |
| `docs/LLY/03-progress/PROGRESS_LOG.md` | 仅在取得本片结果后追加实际状态 |
| `.scratch/ui-catalog-providers/issues/05-fake-provider-secure-execution-chain.md` | 仅在取得本片结果后追加 Comments |

本片不改产品接口或断言；探针复用 Harbor `DockerEnvironment`（执行适配器）与现有 `network.export_sidecar()`（固定侧车上下文导出）职责，不新建 Module、表或产品入口。

## 自验证方式与成功标准

- `git worktree list`、`git status -sb`、`git log --oneline -1`、`git -C framework/harbor ls-files --eol ...`：逐条保留原始输出；若脚本行尾为 `w/lf`，停在只读诊断。
- Docker 前置：固定版本与源码干净，所需镜像全已缓存，同名项目资源为空；内核探针命令不带挂载、宿主端口或写宿主路径。
- `main` 内运行未经改写的 `t2-assertions.sh`；必须见实际 `status=verified`，但这只覆盖做题侧可观察的断言子集。再以宿主 inspect 和假上游自身日志补齐第 4–6 条及第 7 条正对照。
- 两张网络的 `Internal`、连接成员、所有容器标签、`HostConfig.PortBindings` 与 `Mounts` 必须符合最小结构；做题侧无 Docker socket、无代理私有文件/进程；假上游日志显示连接来自 proxy 的 egress IP。
- 拆除前后镜像/卷清单逐项比对；不移除预存固定镜像/其他卷。最后按名称、任务标签、scope 三重过滤容器/网络/卷，残留为零。
- `.tmp` 原始证据逐文件算 SHA-256，写入 manifest 并核对；文档中的输出必须能从这些文件追溯。

## 自验证情况

### 1. 同步与两条只读检查的原始输出

在现有 `E:\9.1agent_exam\runtime\lly-dev-verify` 执行；未新建 worktree，未切分支。运行前：

```text
> git worktree list
E:/9.1agent_exam                                     594f51f [agent+api]
C:/Users/YINGYI/.codex/worktrees/b025/9.1agent_exam  3ed4dca (detached HEAD)
E:/9.1agent_exam/.tmp/codex-ci-main                  ee30743 [codex/ci-local-commits]
E:/9.1agent_exam/runtime/lly-dev-verify              ec489af [lly/dev]
E:/9.1agent_exam/runtime/main-t2-verify              e6a7138 [main]
> git status -sb
## lly/dev...origin/lly/dev [ahead 41]
> git log --oneline -1
ec489af docs: record main fast-forward into lly dev
```

```text
> git fetch origin
From https://github.com/anphuchoang5-sys/agent-exam
   c40ea2e..173dc12  lly/dev    -> origin/lly/dev
   594f51f..ec30317  main       -> origin/main
> git merge origin/main
Merge made by the 'ort' strategy.
 .../05-fake-provider-secure-execution-chain.md     |  17 ++
 .../tests/providers/lifecycle/serve_proxy.py       |  95 +++++++++
 apps/backend/tests/providers/runtime/README.md     |  16 ++
 .../tests/providers/runtime/t2-assertions.sh       | 124 ++++++++++++
 docs/LLY/01-plan/STAGE1_T2_S9_S10_S11_PLAN.md      | 220 +++++++++++++++++++++
 docs/LLY/03-progress/PROGRESS_LOG.md               |  10 +-
 docs/LLY/README.md                                 |   1 +
 .../2026-09-21-task05-owner-machine-runbook.md     |  38 ++++
 docs/actions/2026-09-22-t05-t2-next-round.md       |  74 +++++++
 9 files changed, 594 insertions(+), 1 deletion(-)
 create mode 100644 apps/backend/tests/providers/lifecycle/serve_proxy.py
 create mode 100644 apps/backend/tests/providers/runtime/t2-assertions.sh
 create mode 100644 docs/LLY/01-plan/STAGE1_T2_S9_S10_S11_PLAN.md
 create mode 100644 docs/actions/2026-09-22-t05-t2-next-round.md
> git status -sb
## lly/dev...origin/lly/dev [ahead 5]
> git log --oneline -1
c66a79f Merge remote-tracking branch 'origin/main' into lly/dev
> Test-Path docs/LLY/01-plan/STAGE1_T2_S9_S10_S11_PLAN.md
True
```

计划 §3.1 的第二条只读检查（这里 `framework/harbor` 使用其实际绝对路径；命令语义与计划相同）：

```text
> git -C E:/9.1agent_exam/framework/harbor ls-files --eol src/harbor/environments/docker/harbor-docker-egress-control-sidecar/
i/lf    w/crlf  attr/                 	src/harbor/environments/docker/harbor-docker-egress-control-sidecar/Dockerfile
i/none  w/none  attr/                 	src/harbor/environments/docker/harbor-docker-egress-control-sidecar/allowlist.txt
i/lf    w/crlf  attr/                 	src/harbor/environments/docker/harbor-docker-egress-control-sidecar/bin/network-policy
i/lf    w/crlf  attr/                 	src/harbor/environments/docker/harbor-docker-egress-control-sidecar/entrypoint.sh
i/lf    w/crlf  attr/                 	src/harbor/environments/docker/harbor-docker-egress-control-sidecar/gost.yaml
```

`git -C E:/9.1agent_exam/framework/harbor rev-parse HEAD` 为 `6af8d6e31eced13b93849cdf80feeadf24603d15`；跟踪文件 `status --porcelain --untracked-files=no` 为空。行尾结果满足本轮继续条件，但只证明工作树含 CRLF，不单独证明旧镜像内 127 的唯一原因。

### 2. 本轮实际命令、拓扑与 Trial 原始输出

在固定 Harbor 虚拟环境、现有 worktree 中执行如下命令，退出码 **1**。完整驱动见本地忽略目录的 `probe.py`，完整控制台记录见 `probe-console.txt`，所有 Docker argv 见 `harbor-argv.json`。驱动从固定 Git revision 导出侧车五个 LF blob，照 `codex_trial_probe.py:36-38` 调用 `export_sidecar(REPO.parents[1] / "framework/harbor", context, REVISION)` 并设置 `DockerEnvironment._EGRESS_CONTROL_SIDECAR_CONTEXT_PATH = context`。`t2-assertions.sh` 同样从 `HEAD` 的 Git blob 原样导出（SHA-256 `0e54327486b2f23564a7e98481f0d9d45ca598ed1827e6b5b39b86d870995d42`），未改一字；因 Windows 工作树为 CRLF，上传的是 Git 中的 LF 内容。

```powershell
$env:PYTHONPATH='E:/9.1agent_exam/runtime/lly-dev-verify/apps/backend/src'
& 'E:/9.1agent_exam/framework/harbor/.venv/Scripts/python.exe' '.tmp/t05-harbor-minimal/t05-harbor-20260922-02/probe.py' 2>&1 | Tee-Object -FilePath '.tmp/t05-harbor-minimal/t05-harbor-20260922-02/probe-console.txt'
```

Compose 完整清单原文（本地 `extra-compose.yaml` 的 SHA-256 见 manifest）：

```yaml
services:
  main:
    networks: [internal]
    labels:
      agentexam.task: "05"
      agentexam.scope: t05-harbor-20260922-02
    cap_drop: [ALL]
    security_opt: ["no-new-privileges:true"]

  proxy:
    image: redis:7-alpine
    user: redis
    entrypoint:
      - /bin/sh
      - -ec
      - |
        mkdir -p /tmp/agentexam-private
        printf 'FAKE-T05-PROVIDER-SECRET\n' > /tmp/agentexam-private/fake-provider.json
        printf '#!/bin/sh\nexec nc fake-upstream 6379\n' > /tmp/agentexam-proxy-marker-relay.sh
        chmod +x /tmp/agentexam-proxy-marker-relay.sh
        exec nc -lk -p 8080 -e /tmp/agentexam-proxy-marker-relay.sh
    networks: [internal, egress]
    tmpfs: ["/data:mode=1777"]
    labels:
      agentexam.task: "05"
      agentexam.scope: t05-harbor-20260922-02
    cap_drop: [ALL]
    security_opt: ["no-new-privileges:true"]

  fake-upstream:
    image: redis:7-alpine
    user: redis
    entrypoint: ["redis-server", "--save", "", "--appendonly", "no", "--loglevel", "verbose"]
    networks: [egress]
    tmpfs: ["/data:mode=1777"]
    labels:
      agentexam.task: "05"
      agentexam.scope: t05-harbor-20260922-02
    cap_drop: [ALL]
    security_opt: ["no-new-privileges:true"]

  harbor-docker-egress-control-sidecar:
    networks: [egress]
    labels:
      agentexam.task: "05"
      agentexam.scope: t05-harbor-20260922-02

networks:
  internal:
    internal: true
    labels:
      agentexam.task: "05"
      agentexam.scope: t05-harbor-20260922-02
  egress:
    internal: false
    labels:
      agentexam.task: "05"
      agentexam.scope: t05-harbor-20260922-02
```

代理入口是 `nc -lk -p 8080 -e /tmp/agentexam-proxy-marker-relay.sh`，该短脚本再连接 `fake-upstream:6379`；假上游是禁用持久化、verbose 日志的 Redis。网络图：

```text
main 172.23.0.2 ── internal (Internal=true) ── proxy 172.23.0.3
                                               proxy 172.22.0.3 ── egress (Internal=false) ── fake-upstream 172.22.0.4
                                                                 └─ Harbor sidecar 172.22.0.2（自身 no-network 策略）
```

Harbor 构造期内核探针的实际 argv（原有 `--rm` 短命容器，无挂载/端口/宿主写入）：

```json
["docker","container","run","--rm","alpine:3.23.4@sha256:5b10f432ef3da1b8d4c7eb6c487f2f5a8f096bc91145e68878dd4a5019afde11","sh","-c","if [ ! -f /proc/config.gz ]; then exit 0; fi; zcat /proc/config.gz 2>/dev/null | grep -qE '^CONFIG_NFT_FIB_INET=[ym]'"]
```

Harbor `up` 实际 argv（侧车镜像已缓存，未触发 build/pull；原始文件为 `harbor-argv.json`）：

```json
["docker","compose","--project-name","agentexam-t05-topology","--project-directory","E:\\9.1agent_exam\\runtime\\lly-dev-verify\\.tmp\\t05-harbor-minimal\\t05-harbor-20260922-02\\environment","-f","C:\\Windows\\Temp\\tmp36x7lco5\\agentexam-t05-topology-docker-compose-resources.json","-f","E:\\9.1agent_exam\\framework\\harbor\\src\\harbor\\environments\\docker\\docker-compose-prebuilt.yaml","-f","E:\\9.1agent_exam\\runtime\\lly-dev-verify\\.tmp\\t05-harbor-minimal\\t05-harbor-20260922-02\\extra-compose.yaml","-f","C:\\Windows\\Temp\\tmpobv48vhd\\docker-compose-environment.json","-f","C:\\Windows\\Temp\\tmpnu6t8o89\\docker-compose-mounts.json","-f","E:\\9.1agent_exam\\framework\\harbor\\src\\harbor\\environments\\docker\\docker-compose-egress-control.yaml","up","--detach","--wait"]
```

Harbor 在 `main` 内实际执行的命令为 `T05_PROXY_HOST=proxy T05_PROXY_PORT=8080 T05_UPSTREAM_HOST=fake-upstream T05_UPSTREAM_PORT=8080 bash /tmp/t2-assertions.sh`；`/tmp/t2-assertions.sh` 是仓库原脚本的 LF 原样副本，**不是**用户示例中的相对路径，属路径布置偏差。`trial-command.json` 记录 `return_code: 1`。Trial stdout 原文：

```text
readings
1	workload -> proxy entry	OPEN
1	  reply through proxy	NO-REPLY
2	public 1.1.1.1	CLOSED
2	public 223.5.5.5	CLOSED
3	workload -> fake upstream	CLOSED
3	workload -> other trial	CLOSED
3	host gateway	CLOSED
3	metadata	CLOSED
7	private path	ABSENT
7	marker in /proc/*/environ	0
7	marker in /proc/*/cmdline	0
7	sentinel files	1
7	docker.sock present	no
verdicts
PASS a1 workload to proxy entry
FAIL a1 reply through proxy: got 'NO-REPLY' want 'PONG'
PASS a2 public 1.1.1.1
PASS a2 public 223.5.5.5
PASS a3 workload -> fake upstream
PASS a3 workload -> other trial
PASS a3 host gateway
PASS a3 metadata
PASS a7 private path
PASS a7 marker in environment
PASS a7 marker in argv
FAIL a7 sentinel files: got '1' want '0'
PASS a7 no docker socket
status=failed
```

Trial stderr 为空。侧车状态为 `running/healthy`；其日志原文：

```text
ok: deny all controlled TCP egress
harbor-docker-egress-control-sidecar ready: initial egress policy is no-network
```

假上游自身日志摘录（完整原文在 `failed-container-fake-upstream-logs.json`）：

```text
1:M 22 Sep 2026 10:08:29.576 - Accepted 172.22.0.3:37963
1:M 22 Sep 2026 10:08:34.576 - Client closed connection id=4 addr=172.22.0.3:42459 ... cmd=ping ...
1:M 22 Sep 2026 10:08:39.638 - Client closed connection id=6 addr=172.22.0.3:44045 ... cmd=ping ...
```

`172.22.0.3` 是 inspect 中的代理 egress IP，证明请求至少**到达假上游且来源是代理**；但由于 Trial 未读到 `PONG`，不能把完整往返请求写成通过。

### 3. 宿主侧 inspect、镜像/卷与拆除

宿主 inspect 的原始 JSON 分别为 `inspect-containers.json`、`inspect-networks.json`、`inspect-volumes.json`。实际摘录：

| 容器（均前缀 `agentexam-t05-topology-`，后缀 `-1`） | 镜像 ID | 网络 | `PortBindings` | `Mounts` | 标签 |
|---|---|---|---|---:|---|
| `main` | `sha256:db9f02c6bde9fa90cc8074c92754b2b046947392f1a857726e77f041febb7b82` | internal | `{}` | 0 | `task=05; scope=t05-harbor-20260922-02` |
| `proxy` | `sha256:487efc0616382465781b8fdc3d6d1db449e6fd80ae23bf48432a2da6b6929908` | internal, egress | `{}` | 0 | 同上 |
| `fake-upstream` | 同 proxy | egress | `{}` | 0 | 同上 |
| `harbor-docker-egress-control-sidecar` | `sha256:dd1cd5ac17830d6ebcf4117ac024792aac92ce428a830270d57afe4fce6b8dd3` | egress | `{}` | 0 | 同上 |

网络 `agentexam-t05-topology_internal` 为 `Internal=true`，`agentexam-t05-topology_egress` 为 `Internal=false`；两者均有 `agentexam.task=05` 与本轮 scope 标签。基础镜像 RepoDigests：`debian@sha256:3783cc01769c7b2b1b83a5c5ad96c815348e28ed7da68e2e3687004faa906251`；`redis@sha256:6ab0b6e7381779332f97b8ca76193e45b0756f38d4c0dcda72dbb3c32061ab99`。侧车镜像本机标签 `harbor-prebuilt:harbor-docker-egress-control-sidecar--0b6ae4c0129347c6`，`RepoDigests=[]`，ID 如表；无仓库 digest，不能捏造。任务容器无发布端口、无可写宿主挂载；做题侧报告 `docker.sock present=no`。

Harbor 启动前执行一次 `down --remove-orphans` 时项目为空；拆除前 `pre-down-ownership.json` 已把四个容器与两张网络按**名称 + task + scope**逐一核对。实际拆除 argv：

```json
["docker","compose","--project-name","agentexam-t05-topology","--project-directory","E:\\9.1agent_exam\\runtime\\lly-dev-verify\\.tmp\\t05-harbor-minimal\\t05-harbor-20260922-02\\environment","-f","C:\\Windows\\Temp\\tmp36x7lco5\\agentexam-t05-topology-docker-compose-resources.json","-f","E:\\9.1agent_exam\\framework\\harbor\\src\\harbor\\environments\\docker\\docker-compose-prebuilt.yaml","-f","E:\\9.1agent_exam\\runtime\\lly-dev-verify\\.tmp\\t05-harbor-minimal\\t05-harbor-20260922-02\\extra-compose.yaml","-f","C:\\Windows\\Temp\\tmpobv48vhd\\docker-compose-environment.json","-f","C:\\Windows\\Temp\\tmpnu6t8o89\\docker-compose-mounts.json","-f","E:\\9.1agent_exam\\framework\\harbor\\src\\harbor\\environments\\docker\\docker-compose-egress-control.yaml","down","--rmi","local","--volumes","--remove-orphans"]
```

镜像清单：启动前 **90**、拆除前 **90**、拆除后 **90**；卷清单均 **16**。`inventory-diff.json` 原文为：

```json
{"images":{"added":[],"removed":[]},"volumes":{"added":[],"removed":[]}}
```

本轮适配侧车镜像是**缓存复用**，没有观察到“新增+移除”；这是与计划预期不同的实测事实，不解释为异常。没有删除任何预存镜像或卷。`cleanup.json` 原文：

```json
{"containers":[],"networks":[],"volumes":[]}
```

额外独立只读复核：`docker ps -a`、`docker network ls`、`docker volume ls` 均同时按项目名称、`agentexam.task=05`、`agentexam.scope=t05-harbor-20260922-02` 过滤，**原始输出为空**；仅按项目名查询的三条命令原始输出也为空。未执行全局 prune，未停既有持久化服务。

### 4. 失败归类、未验证项与证据校验

**判定：T2 未通过，不进入 S9。** 侧车 127 已不复现，Harbor 启动和结构 inspect 取得；但 Trial 自己返回 `status=failed`，不能按静态拓扑结构或假上游日志将其改判为 `verified`。本轮两条 FAIL：

1. `a1 reply through proxy` 得到 `NO-REPLY`。假上游日志有两次从代理 IP 发出的 `cmd=ping`，所以“代理完全未转发”与证据不符。断言脚本使用 `head -c 16` 等待读满 16 字节，而 Redis `+PONG\r\n` 较短且连接保持开启；**这是强烈的测量方法疑点，不是经复测确认的唯一根因**。本轮未改脚本、未重试、未将往返判通过。
2. `a7 sentinel files` 得到 `1`。被原样上传到 `/tmp/t2-assertions.sh` 的脚本自身包含默认哨兵字面量 `FAKE-T05-CLIENT-TOKEN`，而断言递归扫描 `/tmp`；因此存在明确的**自命中路径**。脚本只返回命中数未返回命中文件名，不能证明该 1 处必定且仅来自脚本自身。本轮未移动脚本、未改判定、未重试。

因为探针按第一轮 Trial 失败即停，**未执行**额外的 `proxy → fake-upstream` 主动检查、代理私有假值文件/进程的正对照、做题侧进程的额外复核、成功轮的假上游日志 delta 判定。脚本中的“其他 Trial”只测试缺省主机名 `t05-other-trial` 的端口不可达，未创建或检测真实的另一 Trial；此点不能写成跨 Trial 实体隔离已证。`host.docker.internal:80` 与 metadata `:80` 为本轮测试端口，不外推为所有端口。生产入口、真实模型、真实 Key、完整 Job/Trial 编排、S9/S10/S11 均未运行。Owner 登录 401 是另一路径的用户报告，本轮探针未调用 Owner 登录，不能将其当作本轮失败原因。

原始证据留于 `.tmp/t05-harbor-minimal/t05-harbor-20260922-02/`；`manifest.json` 列出该目录 **31 个**文件的逐文件 SHA-256，重新生成后全数核验 `manifest_verified=True`。关键文件摘要：`probe-console.txt`=`11967c904a31df9fd46c7cf731b991d592d271a55b06cb13d3a4fc1fef9f1219`；`trial-stdout.txt`=`6f31876f79a3ebb9a8b6296b9537c23f536e54813aa9334697f8da8eaafae2fe`；`inspect-containers.json`=`73ff9904daf7a00f4ca8eea08fd737d60ada7fef72f0580c75ba85d36df66d4f`；`failed-container-fake-upstream-logs.json`=`aefc307452ef76c19eaeee1f7888226cb55cfb5e3f49ea31945ba7a742c664be`。完整清单不进 Git，供本机抽检。
