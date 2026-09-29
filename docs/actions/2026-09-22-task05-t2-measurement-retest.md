# 任务 05 T2：测量方法修正与新 scope 复测

> 状态：已收口，**T2 未验证通过**；新 scope Trial 为 12 PASS / 1 FAIL、`status=failed`。依计划停止在 T2，不进入 S9/S10/S11。前轮失败事实保存在[已封存行动](2026-09-22-task05-t2-verified.md)，不反向改写。

## 情况说明

用户 2026-09-22 要求继续完成[阶段计划](../LLY/01-plan/STAGE1_T2_S9_S10_S11_PLAN.md)，按 T2 → S9 → S10 → S11 一片完成才进入下一片；并明确批准**仅修正 T2 测量方法、使用新 scope 重测**，保持原期望、全部断言和失败即停规则不变。另要求遇到问题同时记录事实和解决方案。

当前 worktree `runtime/lly-dev-verify`、分支 `lly/dev`、HEAD `04929b1`，工作树干净。`git fetch origin` 后核对 `origin/main` 与 `origin/lly/dev` 均为 HEAD 祖先。前轮固定 Harbor T2：适配侧车健康、结构 inspect 取得，原断言脚本 **11 PASS / 2 FAIL、`status=failed`**，因而 S9/S10/S11 尚未开工。两项 FAIL 分别是经代理回复 `NO-REPLY` 与哨兵文件计数 1；假上游自己的日志已记录来自代理 IP 的 `cmd=ping`。本轮只修这两个测量问题及由其暴露的假值正对照布置，不把旁证写成 T2 通过。

## 问题、证据与拟采取的解决方案

| 问题 | 已有证据 | 本轮解决方案与不可改变的判定 |
|---|---|---|
| 短回复被测成 `NO-REPLY` | 原脚本发送 `PING\n` 后 `head -c 16`；本轮同一 Harbor 主容器经同一代理发送 `PING\r\n`、读取 7 字节，**实际得到 `+PONG\r\n`**。原脚本仍为 `NO-REPLY`。本地实验又推翻了“短字节数单独造成空回复”的强假设：Git Bash `head -c 16` 在开放管道上已输出 7 字节。**两种读法同时改变了请求换行和读取长度，不能仅凭本轮判定哪一个是根因。** | 下一轮先把原断言的测量代码改为协议完整的 `PING\r\n` 并读取完整响应行；以“确从代理收到 `+PONG`”为原期望，不改判定目标。先离线证明无回复、错误回复仍失败，再用**新 scope** 复测；当前轮次不改断言或追跑 |
| 哨兵计数 1 | 脚本自身含默认哨兵字面量，前轮把该脚本上传到它扫描的 `/tmp`；原脚本只报数量，不能断言命中路径唯一 | **已验证措施**：同一 Git blob 脚本上传到扫描范围外的 `/opt`，扫描 `/tmp /run /var/tmp` 与零命中期望保持不变；本轮 `sentinel files=0`、代理私有文件确含假哨兵且做题侧不可见 |
| 前轮因 Trial 失败即停，宿主侧第 4/7 条补测未执行 | 前轮行动的“未验证项”清单 | **已验证措施**：新探针在 Trial stdout 之后采集代理→假上游、私有文件/进程正反对照，再作总判定；五项宿主补测和假上游日志判定均通过，但 Trial 的 1 FAIL 仍阻断 S9 |
| SHA-256 清单生成时控制台仍在写入 | 首次独立抽检发现 `probe-console.txt` 记录哈希 `64423a…`、最终文件哈希 `e7f1ea…`；其他 36 项一致 | 进程退出后用 `apply_patch` 修正该一项，随后对 37 个原始文件逐项重验；不改原始控制台文件 |

## 实施措施

1. 先在不改 Docker 资源的小实验与真实 Harbor 新 scope 中区分“固定字节读取缺陷”和“中继回程缺陷”；**不预先修改 `t2-assertions.sh`**。若确需改读法，只改测量方式，不改任何 `t05_expect` 名称、期望值、目标地址或退出码逻辑。
2. 本轮新 scope 与新 `.tmp` 证据目录；复用上轮已核实的固定 Harbor 环境和双网络结构。只调整探针将脚本上传到 `/opt`，并确保代理私有假值文件同时包含两种假标记，做题侧在同一路径不得可见。
3. 在固定 Harbor 环境中实际运行做题侧脚本；再于宿主补测代理→假上游、假上游来源日志、网络 `Internal`、端口/挂载/标签、私有文件与进程的正反对照。
4. 前后记录镜像/卷清单，仅在名称+`agentexam.task=05`+本轮 scope 三重匹配后走本 Trial 常规拆除；独立查询残留为零。原始文件逐项计算 SHA-256。
5. 若 T2 全部验证，才创建 S9 行动记录与实现；若任一断言失败，记录问题、可证原因、候选解决方案及未验证项后停在 T2。

## 受影响文件树

| 路径 | 职责与关系 |
|---|---|
| `docs/actions/2026-09-22-task05-t2-measurement-retest.md` | 本轮行动、问题/解决方案、原始结果、与前轮封存记录的衔接 |
| `apps/backend/tests/providers/runtime/t2-assertions.sh` | 本轮**未修改**；仍为 HEAD 中 SHA-256 `0e543274…` 的原 Git blob，全部原断言照跑 |
| `apps/backend/tests/providers/runtime/README.md` | 本轮**未修改**；待真正修复测量方法的后续切片再同步 |
| `.tmp/t05-harbor-minimal/<本轮 scope>/` | 被 Git 忽略的新一轮 Compose、驱动、原始证据及 SHA-256 manifest；不覆盖前轮 |
| `docs/LLY/03-progress/PROGRESS_LOG.md` | 本轮结束后追加实际状态，不预记通过 |
| `.scratch/ui-catalog-providers/issues/05-fake-provider-secure-execution-chain.md` | 本轮结束后在 Comments 追加事实、问题与解决方案 |

本轮不变更产品入口、Harbor 源码或侧车适配。探针通过现有 `DockerEnvironment` 与 `network.export_sidecar()`，不新建业务 Module、Interface、表或顶层目录。相关测试 seam 是计划已明确的“固定 Harbor 做题容器内执行 `t2-assertions.sh` + 宿主只读 inspect”。

## 自验证方式与成功标准

- 小实验和真实 Harbor 诊断必须能够区分短回复读取与中继回程；若修改断言脚本，`bash -n` 必须通过且原期望名/期望值的 diff 为零。不能用未经证实的 `head` 猜测直接修改测试。
- 新 scope 的 Harbor T2：侧车健康、脚本实际返回 `status=verified`，13 条逐项判定全 PASS；宿主第 4–6 条及第 7 条正对照都测到且成立。其他 Trial 端口只在确有活体目标时宣称实体隔离，缺席则显式记未验证。
- `main` 仅连 internal，`proxy` 连 internal+egress，`fake-upstream` 连 egress；网络 `Internal`、标签、镜像身份、端口/挂载/私有文件与进程按原计划验收，不降低标准。
- 镜像/卷清单与专属资源拆除前后差异如实记录；非本轮资源零删除、三重条件残留为零；`.tmp` 每个原始证据文件 SHA-256 校验通过。
- 若上述任一环节未取得，结论保留“未验证通过”，不进 S9/S10/S11、不接真实 Key/模型。

## 自验证情况

已完成的最小诊断：本地首次 `read-regression.sh` 因 Git Bash 管道实现方式提前退出（exit 1，**不是产品判定**）；随后 `read-regression.py` 用真实 Git Bash 子进程和保持打开的 stdin 复现，输出 `old=(True, b'+PONG\\r\\n', b'')`、`new=(False, b'+PONG\\r\\n', b'')`、`bad=(False, b'-ERR bad\\r\\n', b'')`，其“旧读法会空输出”预期断言**失败**。这说明旧读法可能等待但已输出短回复，不能把上一轮 FAIL 直接归因为 `head -c 16`。

### 只读开工检查（原始输出）

`git fetch origin` 无新引用；检查时 `lly/dev` HEAD `04929b1`，`origin/main` 与 `origin/lly/dev` 均为 HEAD 祖先，未切分支或新建 worktree。已有工作树列表：

```text
E:/9.1agent_exam                                     594f51f [agent+api]
C:/Users/YINGYI/.codex/worktrees/b025/9.1agent_exam  3ed4dca (detached HEAD)
E:/9.1agent_exam/.tmp/codex-ci-main                  ee30743 [codex/ci-local-commits]
E:/9.1agent_exam/runtime/lly-dev-verify              04929b1 [lly/dev]
E:/9.1agent_exam/runtime/main-t2-verify              e6a7138 [main]
```

```text
> git status -sb
## lly/dev...origin/lly/dev
?? docs/actions/2026-09-22-task05-t2-measurement-retest.md
> git log --oneline -1
04929b1 docs(task05): record blocked Harbor T2 trial
> git -C E:/9.1agent_exam/framework/harbor ls-files --eol src/harbor/environments/docker/harbor-docker-egress-control-sidecar/
i/lf    w/crlf  attr/                 src/harbor/environments/docker/harbor-docker-egress-control-sidecar/Dockerfile
i/none  w/none  attr/                 src/harbor/environments/docker/harbor-docker-egress-control-sidecar/allowlist.txt
i/lf    w/crlf  attr/                 src/harbor/environments/docker/harbor-docker-egress-control-sidecar/bin/network-policy
i/lf    w/crlf  attr/                 src/harbor/environments/docker/harbor-docker-egress-control-sidecar/entrypoint.sh
i/lf    w/crlf  attr/                 src/harbor/environments/docker/harbor-docker-egress-control-sidecar/gost.yaml
```

### 本轮真实 Harbor 命令与原始输出

复测使用 `.tmp/t05-harbor-minimal/t05-harbor-20260922-03/`（本地忽略目录），固定 Harbor revision `6af8d6e31eced13b93849cdf80feeadf24603d15`。驱动命令退出码 **1**：

```powershell
$env:PYTHONPATH='E:/9.1agent_exam/runtime/lly-dev-verify/apps/backend/src'
& 'E:/9.1agent_exam/framework/harbor/.venv/Scripts/python.exe' '.tmp/t05-harbor-minimal/t05-harbor-20260922-03/probe.py' 2>&1 | Tee-Object -FilePath '.tmp/t05-harbor-minimal/t05-harbor-20260922-03/probe-console.txt'
exit $LASTEXITCODE
```

实际 `extra-compose.yaml` 清单如下；`main` 的镜像由固定 Harbor 环境提供，另外两个服务仅用缓存的 `redis:7-alpine`。代理私有文件只是假标记，不含真 Key；所有端口仅在容器网络内监听。

```yaml
services:
  main:
    networks: [internal]
    labels: {agentexam.task: "05", agentexam.scope: t05-harbor-20260922-03}
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
        printf 'FAKE-T05-PROVIDER-SECRET\nFAKE-T05-CLIENT-TOKEN\n' > /tmp/agentexam-private/fake-provider.json
        printf '#!/bin/sh\nexec nc fake-upstream 6379\n' > /tmp/agentexam-proxy-marker-relay.sh
        chmod +x /tmp/agentexam-proxy-marker-relay.sh
        exec nc -lk -p 8080 -e /tmp/agentexam-proxy-marker-relay.sh
    networks: [internal, egress]
    tmpfs: ["/data:mode=1777"]
    labels: {agentexam.task: "05", agentexam.scope: t05-harbor-20260922-03}
    cap_drop: [ALL]
    security_opt: ["no-new-privileges:true"]
  fake-upstream:
    image: redis:7-alpine
    user: redis
    entrypoint: ["redis-server", "--save", "", "--appendonly", "no", "--loglevel", "verbose"]
    networks: [egress]
    tmpfs: ["/data:mode=1777"]
    labels: {agentexam.task: "05", agentexam.scope: t05-harbor-20260922-03}
    cap_drop: [ALL]
    security_opt: ["no-new-privileges:true"]
  harbor-docker-egress-control-sidecar:
    networks: [egress]
    labels: {agentexam.task: "05", agentexam.scope: t05-harbor-20260922-03}
networks:
  internal:
    internal: true
    labels: {agentexam.task: "05", agentexam.scope: t05-harbor-20260922-03}
  egress:
    internal: false
    labels: {agentexam.task: "05", agentexam.scope: t05-harbor-20260922-03}
```

原始 Trial 命令（`probe.py` 通过 `DockerEnvironment.exec` 在 `main` 内执行）：

```bash
T05_PROXY_HOST=proxy T05_PROXY_PORT=8080 T05_UPSTREAM_HOST=fake-upstream T05_UPSTREAM_PORT=8080 T05_PRIVATE_PATH=/tmp/agentexam-private/fake-provider.json bash /opt/t2-assertions.sh
```

原始 stdout，退出码 **1**，stderr 空；脚本 Git blob SHA-256 `0e54327486b2f23564a7e98481f0d9d45ca598ed1827e6b5b39b86d870995d42`（与前轮一致）：

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
7	sentinel files	0
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
PASS a7 sentinel files
PASS a7 no docker socket
status=failed
```

同一 Harbor `main` 的诊断命令 `exec 3<>/dev/tcp/proxy/8080; printf 'PING\\r\\n' >&3; timeout 3 head -c 7 <&3` 实测 **exit 0**、stdout `+PONG\r\n`，说明代理入口和回程在该实验下存在；正式脚本的 `PING\n` + `head -c 16` 仍未得到回复。这两处差异未被单变量隔离。代理容器内 `redis-cli -h fake-upstream -p 6379 ping` 得 `PONG`；假上游日志增量记录 `Accepted 172.23.0.3:...` 和 `cmd=ping`，该 IP 是 proxy 的 egress IP。五项宿主补测（代理→上游、代理私有文件假标记、假哨兵、代理进程、主容器进程不可见）均为 `return_code=0` 且符合期望，逐项原文在 `host-side-checks.json`。

### 宿主 inspect、镜像身份、拆除

固定 Harbor 实测拓扑（侧车也只在 egress，**未与 main 共享网络命名空间**）：

```text
internal (Internal=true):  main + proxy
egress   (Internal=false): proxy + fake-upstream + harbor-docker-egress-control-sidecar
```

四个容器均 `agentexam.task=05`、`agentexam.scope=t05-harbor-20260922-03`、无 `HostConfig.PortBindings`、`Mounts=[]`；代理/fake-upstream 的 `/data` 是容器 tmpfs，不是宿主挂载。`main`、`proxy`、`fake-upstream` 均 running，侧车 running/healthy。两网络同样有双标签。镜像身份：`main` 镜像 ID `sha256:db9f02c6…`、RepoDigest `debian@sha256:3783cc01…`；`proxy`/`fake-upstream` 镜像 ID `sha256:487efc06…`、RepoDigest `redis@sha256:6ab0b6e7…`；侧车镜像 ID `sha256:dd1cd5ac…`，本地构建、RepoDigests 空。完整 4 容器和 2 网络的 inspect、标签与镜像身份分别在 `inspect-containers.json`、`inspect-networks.json`、`image-identities.json`。

Harbor 常规拆除实际执行的 argv **原文**（同一次启动的项目资源已在拆除前逐项核对名称+task+scope，见 `pre-down-ownership.json`；启动前也曾执行同 compose 列表的 `down --remove-orphans` 空项目预清理）：

```json
["docker","compose","--project-name","agentexam-t05-topology","--project-directory","E:\\9.1agent_exam\\runtime\\lly-dev-verify\\.tmp\\t05-harbor-minimal\\t05-harbor-20260922-03\\environment","-f","C:\\Windows\\Temp\\tmpofn0svwe\\agentexam-t05-topology-docker-compose-resources.json","-f","E:\\9.1agent_exam\\framework\\harbor\\src\\harbor\\environments\\docker\\docker-compose-prebuilt.yaml","-f","E:\\9.1agent_exam\\runtime\\lly-dev-verify\\.tmp\\t05-harbor-minimal\\t05-harbor-20260922-03\\extra-compose.yaml","-f","C:\\Windows\\Temp\\tmpbh5wr16f\\docker-compose-environment.json","-f","C:\\Windows\\Temp\\tmpfj4i4x5g\\docker-compose-mounts.json","-f","E:\\9.1agent_exam\\framework\\harbor\\src\\harbor\\environments\\docker\\docker-compose-egress-control.yaml","down","--rmi","local","--volumes","--remove-orphans"]
```

拆除前后清单均为 **90 镜像、16 卷**，逐项差集 `images.added=[]`、`images.removed=[]`、`volumes.added=[]`、`volumes.removed=[]`；没有删已缓存镜像或他人卷。驱动 `cleanup.json` 中项目容器/网络/卷均 `[]`；随后独立执行按 `agentexam.task=05` + 本轮 scope 的 `docker ps -a`、`docker network ls`、`docker volume ls`，原始输出均为空。内核探针命令原文见 `kernel-probe-command.json`：只有 `docker container run --rm` 和缓存的 Alpine 镜像，无挂载、宿主发布端口或 Docker 套接字。

本地 manifest 对 **37 个**原始文件列出 SHA-256，完整路径在 `.tmp/t05-harbor-minimal/t05-harbor-20260922-03/manifest.json`。初次生成时控制台仍在 `Tee-Object` 写入，故只有 `probe-console.txt` 的哈希发生变化；进程结束后已按最终文件更新那一个哈希，独立逐项复核后 37/37 一致。`.tmp` 不进 Git，正文保留关键原文以便远端审阅。

### 结论、失败与未验证项

**T2 未通过**：Trial 原判定 12 PASS / 1 FAIL，`status=failed`。这是正式测量脚本失败，不能以单独诊断读到 `+PONG` 替代其判定，更不能进入 S9/S10/S11 或带真 Key。已经验证的结构、私有文件与真实中继旁证仅限定在本次最小假上游环境。

- 代理回复失败的精确成因**未定位**：诊断和原脚本同时差在请求换行及读取长度。下一次先做单变量离线测试，再在获准的新 scope 中修测量方法复测；仍要求从代理真收到 `PONG`，无回复/错误回复必须 FAIL。当前原断言一字未改。
- “其他 Trial”目标 `t05-other-trial` 未部署活体容器；本轮仅测到该名称不能连通，**不能宣称已实证跨 Trial 活体隔离**。若后续验收必须证明实体间隔离，应在授权范围内另设受控活体反例；本轮不能扩建。
- 未接 Codex CLI、真实模型、真实 Key 或真实供应商；未验证产品化网络接线、完整工具循环、S9/S10/S11；也未修改共享 Docker/WSL/防火墙或既有容器。
