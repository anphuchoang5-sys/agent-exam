# 任务 05 T2：活体其他 Trial 网络隔离对照

> 状态：本轮已完成。固定 Harbor 最小 Trial 13/13 PASS，活体其他项目目标的同 IP 正反对照成立；目标是独立 Compose 网络替身，**不是第二个 Harbor 管理的 Trial**。前轮无活体目标的历史事实见[历史行动](2026-09-22-task05-t2-response-measurement.md)。

## 情况说明

用户 2026-09-22 明确授权补建带 `agentexam.task=05` 和本轮 scope 标签的独立活体 Trial 容器及隔离网络，仅做跨 Trial 不可达正反对照、精确清理。本轮仍在现有 `runtime/lly-dev-verify` worktree 的 `lly/dev`，不切分支或新建 worktree；已 `git fetch origin` 并核对 `origin/main` 是当前 HEAD 祖先（`HEAD...origin/main` 为 `8\t0`，即 main 无新提交需合并）。固定 Harbor 工作树侧车入口仍是 `i/lf w/crlf`，需要沿用已证的 `export_sidecar()` 上下文。

本轮 scope 为 `t05-harbor-20260922-05`。在原 Harbor 项目 `agentexam-t05-topology` 之外，新建**独立 Compose 项目** `agentexam-t05-other-trial`，其中仅有缓存 Redis 镜像的活体 `target` 服务和 `isolated` 网络（`internal: true`）。这是一只“其他 Trial”**网络替身**，不是第二次 Harbor 管理的 Trial；该区别必须在结论中保留。先在其容器内通过实际网络 IP 取得 `PONG`，再在 Harbor `main` 的 Trial 命令中把 `T05_OTHER_TRIAL_HOST` 设为**同一 IP**、端口 6379，期望 `CLOSED`；检验后再次确认 target 活着，排除“目标未起/已死”的假阴性。

## 实施措施

1. 创建本轮行动记录后，机械复制上轮已核实的临时 Harbor 驱动与 Compose 到新 `.tmp` scope；新增独立其他 Trial 的 Compose 清单。所有新资源均以名称、任务标签、本轮 scope 三重标识；运行前拒绝同名或同项目已有资源。
2. 只用已缓存镜像，不重建/拉取固定 Harbor，不使用真 Key、真实供应商、Codex CLI，也不开放宿主端口/挂载宿主路径/Docker 套接字。内核探针仍按附三许可的无挂载、无发布端口 `--rm` 运行。
3. 其他 Trial target 先启动并记录镜像/容器/网络 inspect；正对照是 Redis 对自己的**网络 IP**返回 `PONG`。随后固定 Harbor 仅复用已证双网络，Trial 命令跑原 13 条判定，其中 a3 用 target 的真实 IP；结束后正对照再复测 target 仍运行。
4. 两项目分别在拆除前按名称+task+scope 验明归属，先走 Harbor 自身常规拆除，再拆独立替身项目；前后记录镜像/卷清单、拆除 argv、标签残留查询。禁止全局 prune、删除其他镜像/卷或停止既有服务。
5. 将原始 stdout、inspect、清单差异和每个证据文件 SHA-256 写入忽略目录；行动记录如实判定。用户本轮指定只继续 T2，因此即使本轮对照成立，也不在本轮进入 S9。

## 需要修改的文件树

| 路径 | 职责与关系 |
|---|---|
| `docs/actions/2026-09-22-task05-t2-live-other-trial.md` | 本轮活体对照的授权、原始证据、判定和问题/解决方案 |
| `.tmp/t05-harbor-minimal/t05-harbor-20260922-05/` | 本轮忽略的 Harbor 驱动、主 Compose、独立项目 Compose、原始证据与 manifest；不覆盖前轮 |
| `docs/LLY/03-progress/PROGRESS_LOG.md` | 完成后更新 T2/S9 实际状态；不预记通过 |
| `.scratch/ui-catalog-providers/issues/05-fake-provider-secure-execution-chain.md` | 任务 05 Comments 追加结论与提交号 |

本轮不修改产品模块或原 `t2-assertions.sh` 判定。固定 Harbor `DockerEnvironment` 是受测适配器，独立 Compose 只提供活体网络目标；两者通过 target 的 inspect IP 与 Trial 命令显式关联，不共用网络。

## 自验证方式与成功标准

- 静态核对：两项目各自唯一、scope/标签完全一致，`target` 仅在 `isolated`，Harbor `main` 仅在 `internal`；无端口发布/宿主挂载/套接字，镜像全部缓存。
- 活体正反：target 从自身网络 IP 得 `PONG`（Harbor Trial 前后各一次），且整个 Trial 期间 running；Harbor `main` 对同一 IP:6379 得 `CLOSED`，其余 12 项不回归，末行 `status=verified`。
- 宿主侧代理→假上游、来源 IP、私有文件/进程正反对照均成立；两项目完整 inspect、镜像/卷前后差异与常规拆除 argv 留证。按任务+scope 查询容器、网络、卷应为空；SHA-256 清单逐项匹配。
- 若目标正对照失败或隔离断言失败，按阶段计划停在 T2；不把“名称不存在”或“目标已死”记为成功。不带真 Key、不进 S9/S10/S11。

## 自验证情况

### 开工只读核对（原始输出）

已先 `git fetch origin`，本轮运行前 HEAD `d263d10`；`origin/main` 是 HEAD 的祖先，`git rev-list --left-right --count HEAD...origin/main` 输出 `8 0`，没有遗漏 main 新提交。运行后复核的原始输出如下（`status` 只多出本轮行动文档）：

```text
E:/9.1agent_exam                                     594f51f [agent+api]
C:/Users/YINGYI/.codex/worktrees/b025/9.1agent_exam  3ed4dca (detached HEAD)
E:/9.1agent_exam/.tmp/codex-ci-main                  ee30743 [codex/ci-local-commits]
E:/9.1agent_exam/runtime/lly-dev-verify              d263d10 [lly/dev]
E:/9.1agent_exam/runtime/main-t2-verify              e6a7138 [main]
## lly/dev...origin/lly/dev
?? docs/actions/2026-09-22-task05-t2-live-other-trial.md
d263d10 docs(task05): note PR limitation and review path
8	0
```

`git -C E:/9.1agent_exam/framework/harbor ls-files --eol src/harbor/environments/docker/harbor-docker-egress-control-sidecar/` 原文：

```text
i/lf    w/crlf  attr/                  src/harbor/environments/docker/harbor-docker-egress-control-sidecar/Dockerfile
i/none  w/none  attr/                  src/harbor/environments/docker/harbor-docker-egress-control-sidecar/allowlist.txt
i/lf    w/crlf  attr/                  src/harbor/environments/docker/harbor-docker-egress-control-sidecar/bin/network-policy
i/lf    w/crlf  attr/                  src/harbor/environments/docker/harbor-docker-egress-control-sidecar/entrypoint.sh
i/lf    w/crlf  attr/                  src/harbor/environments/docker/harbor-docker-egress-control-sidecar/gost.yaml
```

这对应[计划第 3.1 节](../LLY/01-plan/STAGE1_T2_S9_S10_S11_PLAN.md)的 `w/crlf` 分支。本轮用 `export_sidecar()` 导出的 LF + Docker Desktop DNS 适配上下文，侧车实测 `running/healthy`，没有改固定 Harbor 源码。未走 `harbor_entry.py`，因为产品入口仍按 `HARBOR_NETWORK_CONFIG_INVALID` 拒绝必要的 `extra_docker_compose`（计划第 3.2 节）。

### 原文要求 → 措施 → 实测结果

| 原文引用 | 本轮措施 | 原始证据与结果 |
|---|---|---|
| [计划第 3 节](../LLY/01-plan/STAGE1_T2_S9_S10_S11_PLAN.md)：“把七条断言测到” | 固定 Harbor 启动 `main`/`proxy`/`fake-upstream`；Trial 内执行未改判定的脚本 | `trial-stdout.txt`：13 PASS、0 FAIL、`status=verified`；七类读数均非跳过 |
| [组长机器预案附三](2026-09-21-task05-owner-machine-runbook.md)：“做题侧→其他 Trial 所在网络：不通” | 独立 Compose 项目先启动有监听的 `target`；把其 inspect IP `172.22.0.2` 注入 Harbor `main`；目标前后两次自 IP `PONG` | `other-trial-before-positive.json` / `other-trial-after-positive.json` 都为 `PONG`；Trial `3 workload -> other trial CLOSED`、`PASS a3`；不是不存在的 DNS 名称 |
| [预案附三](2026-09-21-task05-owner-machine-runbook.md)：“无主机发布端口、无 Docker 套接字、无可写宿主挂载” | 逐容器 inspect `HostConfig.PortBindings`、`HostConfig.Binds`、`Mounts`；Trial 内查 socket | 五个容器均 `PortBindings={}`、`Binds=null`、`Mounts=[]`；`7 docker.sock present no` |
| [计划第 3.3 节](../LLY/01-plan/STAGE1_T2_S9_S10_S11_PLAN.md)：“镜像/卷清单差异与清理复核” | 两项目拆除前后清单、限定本轮 task+scope 查询 | 90 镜像、16 卷前后不变；镜像/卷 added、removed 均空；容器/网络/卷残留均空 |

### Trial 实际命令与原始输出

执行入口（完整驱动、Compose 与 Harbor argv 均保存在 `.tmp/t05-harbor-minimal/t05-harbor-20260922-05/`）：

```powershell
$env:PYTHONPATH='E:/9.1agent_exam/runtime/lly-dev-verify/apps/backend/src'
& 'E:/9.1agent_exam/framework/harbor/.venv/Scripts/python.exe' '.tmp/t05-harbor-minimal/t05-harbor-20260922-05/live_other_trial.py'
```

目标项目的实际 `up` argv 为 `docker compose --project-name agentexam-t05-other-trial --project-directory E:\9.1agent_exam\runtime\lly-dev-verify\.tmp\t05-harbor-minimal\t05-harbor-20260922-05 -f E:\9.1agent_exam\runtime\lly-dev-verify\.tmp\t05-harbor-minimal\t05-harbor-20260922-05\other-trial-compose.yaml up --detach --wait --wait-timeout 30 --no-build --pull never`；返回 0，容器 `Started`、`Healthy`。前后均在目标容器执行 `redis-cli -h 172.22.0.2 -p 6379 ping`，原始返回 `EXIT=0 STDOUT='PONG\n' STDERR=''`。Harbor Trial 的实际命令见 `trial-command.json`：

```text
T05_PROXY_HOST=proxy T05_PROXY_PORT=8080 T05_UPSTREAM_HOST=fake-upstream T05_UPSTREAM_PORT=8080 T05_PRIVATE_PATH=/tmp/agentexam-private/fake-provider.json bash /opt/t2-assertions.sh
inherited_other_trial_host=172.22.0.2
return_code=0
```

`trial-stdout.txt` 全文（以下保留原输出的制表符）：

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

`trial-stderr.txt` 为空。宿主侧 `host-side-checks.json` 的代理→假上游 `redis-cli ... ping` 为 `PONG`，假私有文件/假标记/进程在代理侧 `PRESENT`、做题侧相应进程 `ABSENT`。`fake-upstream-logs.txt` / `upstream-verdict.json` 记录 `cmd=ping` 的连接来源 `172.23.0.4`，等于 inspect 的代理 egress IP；这是真实转发正对照，不是只看主容器的打印。

### 网络与资源身份

```text
Harbor: internal (Internal=true)  main 172.24.0.2 ── proxy 172.24.0.3
        egress (Internal=false)                  proxy 172.23.0.4 ── fake-upstream 172.23.0.2
                                                sidecar 172.23.0.3
其他项目: isolated (Internal=true) target 172.22.0.2:6379
Harbor main 不接 egress / isolated；其他项目 target 不接 Harbor 的任何网络。
```

五个容器、三条网络均有 `agentexam.task=05`、`agentexam.scope=t05-harbor-20260922-05`；Compose 项目标签分别为 `agentexam-t05-topology` 和 `agentexam-t05-other-trial`。`inspect-containers.json`、`inspect-networks.json`、`other-trial-before-inspect.json` 含完整名称、标签、IP、`Internal`、Mounts 与 PortBindings。

| 容器服务 | inspect 镜像 ID | RepoDigest |
|---|---|---|
| Harbor main | `sha256:db9f02c6bde9fa90cc8074c92754b2b046947392f1a857726e77f041febb7b82` | `debian@sha256:3783cc01769c7b2b1b83a5c5ad96c815348e28ed7da68e2e3687004faa906251` |
| Harbor proxy / fake-upstream、其他项目 target | `sha256:487efc0616382465781b8fdc3d6d1db449e6fd80ae23bf48432a2da6b6929908` | `redis@sha256:6ab0b6e7381779332f97b8ca76193e45b0756f38d4c0dcda72dbb3c32061ab99` |
| Harbor 侧车 | `sha256:dd1cd5ac17830d6ebcf4117ac024792aac92ce428a830270d57afe4fce6b8dd3` | 本地构建 `harbor-prebuilt:harbor-docker-egress-control-sidecar--0b6ae4c0129347c6`，RepoDigest 空；以镜像 ID 识别 |

### 拆除原文、差异与独立复核

Harbor 常规拆除实际 argv（完整 JSON 亦见 `harbor-argv.json`）：

```text
docker compose --project-name agentexam-t05-topology --project-directory E:\9.1agent_exam\runtime\lly-dev-verify\.tmp\t05-harbor-minimal\t05-harbor-20260922-05\environment -f C:\Windows\Temp\tmp493pxxe_\agentexam-t05-topology-docker-compose-resources.json -f E:\9.1agent_exam\framework\harbor\src\harbor\environments\docker\docker-compose-prebuilt.yaml -f E:\9.1agent_exam\runtime\lly-dev-verify\.tmp\t05-harbor-minimal\t05-harbor-20260922-05\extra-compose.yaml -f C:\Windows\Temp\tmpdh0i2_ps\docker-compose-environment.json -f C:\Windows\Temp\tmpvwgl5xns\docker-compose-mounts.json -f E:\9.1agent_exam\framework\harbor\src\harbor\environments\docker\docker-compose-egress-control.yaml down --rmi local --volumes --remove-orphans
```

独立目标项目拆除实际 argv：

```text
docker compose --project-name agentexam-t05-other-trial --project-directory E:\9.1agent_exam\runtime\lly-dev-verify\.tmp\t05-harbor-minimal\t05-harbor-20260922-05 -f E:\9.1agent_exam\runtime\lly-dev-verify\.tmp\t05-harbor-minimal\t05-harbor-20260922-05\other-trial-compose.yaml down --remove-orphans
```

拆除前通过 `pre-down-ownership.json` 与另项目 inspect 核对了名称/ID/任务+scope。`all-inventory-before.json`、`all-inventory-before-teardown.json`、`all-inventory-after-teardown.json` 各为 90 镜像、16 卷；`all-inventory-diff.json` 原文为 `images: {added: [], removed: []}, volumes: {added: [], removed: []}`。`cleanup.json` 和 `other-trial-cleanup.json` 的容器、网络、卷三项均为 `[]`；另外独立执行 `docker ps -a`、`docker network ls`、`docker volume ls` 同时筛选 `agentexam.task=05` 与本轮 scope，三条均无输出（exit 0）。无全局 prune、无其他项目资源删除。

证据根目录：`E:/9.1agent_exam/runtime/lly-dev-verify/.tmp/t05-harbor-minimal/t05-harbor-20260922-05/`。`manifest.json` 列出 43 个文件 SHA-256；逐项 `Get-FileHash -Algorithm SHA256` 复核 **43/43 一致**。这里的证据不入 Git；本行动记录摘录关键原文。

### 偏差、失败与未验证项

- **实测判定**：本轮固定 Harbor 最小形态及有活体网络替身的“其他 Trial”直连拒绝均成立；前轮无活体目标的缺口已在授权范围内关闭。项目验收其它项没有因本轮自动变为通过，S9/S10/S11 本轮未执行。
- **边界**：目标是独立 Compose 项目 `agentexam-t05-other-trial`，不是第二个 Harbor 发起/管理的 Trial；因此“两个同时由 Harbor 管理的 Trial 的隔离”**未验证**。如验收要求必须是后者，需在另一轮明确扩大范围，不能把本轮替身写成该证据。
- **方法偏差**：用目标容器对自己的实际网络 IP 两次 `PONG` 证明监听服务活着，并用 Harbor `main` 对相同 IP 的 `CLOSED` 做负对照；未在目标网络另启动一个客户端容器。静态 `docker compose config` 单独读取覆盖文件时因没有基础镜像字段报错，改用 `--no-consistency` 验证其语法并逐项检查 Compose 归属；这是静态检查用法问题，不是本轮 Trial 失败。
- **未做**：没有真实 Key、真实模型/供应商请求、Codex CLI、正式产品入口或公网放行测试；没有验证产品化接线和双 Harbor Trial。固定 Harbor 的无标签 `--rm` 内核探针遵循已授权特例，原始 argv 在 `kernel-probe-command.json`；本轮未发现端口、宿主挂载或 Docker 套接字参数。
