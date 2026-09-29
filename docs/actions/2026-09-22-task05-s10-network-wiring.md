# 任务 05 S10：受控双网络接线（已完成）

## 情况说明与原文对应

> [阶段计划第 5 节](../LLY/01-plan/STAGE1_T2_S9_S10_S11_PLAN.md)：“把 T2 验证过的形态产品化——run 级网络拓扑合成、代理进程随 Run 起停、把 `config.toml` 与短期令牌注入做题侧。”

T2 的 Harbor 最小探针已经证明主容器只接 internal、代理接 internal 与 egress 的可行性；它没有证明正式 Worker/Harbor/Codex 产品路径。S9 已实测：受控假提供方 Run 在 Harbor 启动前以 `PROVIDER_RUNTIME_NOT_READY` 拒绝，不能回退 ChatGPT。本片从该拒绝接缝起步，不启用真实提供方。

## 实施措施与文件树

| 路径 | 职责 |
|---|---|
| `apps/backend/src/eval_platform/adapters/execution/provider_access/net/topology.py` | **已改**：生成唯一双网络覆盖并精确比较；主容器只接 internal、代理接双网、假上游和侧车只接 egress。 |
| `apps/backend/src/eval_platform/adapters/execution/provider_access/net/gate.py` | **已改**：把现有 Harbor 网络门禁移入子目录，只为完全匹配的内部覆盖留入口；任意外部覆盖仍拒绝。 |
| `apps/backend/src/eval_platform/adapters/execution/provider_access/net/runtime.py` | **本次新增**：为单个受控假提供方 Run 生成 scope、固定 Compose 覆盖、无密钥运行清单和临时空认证占位；入口侧重新加载并验证，结束删除私有输入。 |
| `apps/backend/src/eval_platform/adapters/execution/codex/provider_config.py`、`uploads.py` | **已改**：固定 CLI 已实测的文件式认证配置；config 与短令牌分别经 stdin 送往既有私有目标/短命路径，不传宿主 argv/env；由 provider Codex Run 调用。 |
| `apps/backend/src/eval_platform/adapters/execution/codex/provider.py` | **本次新增**：在既有受守卫 Codex 上叠加固定代理配置；从代理私有 tmpfs 经 Compose stdout/Worker 内存取得短令牌，再经 stdin 写入做题侧 tmpfs。 |
| `apps/backend/src/eval_platform/adapters/execution/provider_access/failures.py` | **已改**：新增拓扑/代理/令牌运行失败的受控类别，声明纯 Harbor 配置错误只在本地配置阶段出现。 |
| `apps/backend/src/eval_platform/adapters/execution/harbor_entry.py` | **已改**：保留原导入接口；只有固定 provider agent、运行清单与精确覆盖同时匹配时才注册 provider Codex，其余仍走默认严格门禁。 |
| `apps/backend/src/eval_platform/delivery/worker/bindings.py`、`tests/jobs/runtime/test_worker_bindings.py` | **本次已改**：仅单个受控假 Run 且显式注入代理后端工厂时路由到它；缺工厂或混合 Job 仍拒绝，绝不借 ChatGPT。 |
| `apps/backend/src/eval_platform/adapters/execution/harbor/adapter.py`、`delivery/worker/runtime.py` | **本次已改**：Worker 只在本地同时配置固定 Codex 包与已核验 provider 镜像 ID 时构造 provider 后端；Adapter 为单 Run 生成并回收上述运行输入。缺任一项仍以 `PROVIDER_RUNTIME_NOT_READY` 拒绝。 |
| `apps/backend/tests/providers/net/`、`tests/providers/runtime/test_provider_uploads.py`、`tests/providers/policy/test_provider_config_rendering.py`、`tests/contract/network/test_provider_overlay.py`、`tests/test_codex_uploads.py` | **已改/新增**：拓扑/篡改/配置/私有上传/门禁替身与合同用例；新增用例下沉子目录，避免把既有测试文件推过 200 行。 |
| `apps/backend/tests/providers/runtime/Dockerfile.proxy`、`support/serve.py` | **本次新增并验收**：只用已缓存 Python 基底在离线构建时生成 `.invalid` 自签测试证书；同一受限镜像按角色启动产品代理或 TLS 假上游。令牌及假 profile 只在代理 tmpfs 生成。 |
| `apps/backend/tests/providers/contract/support/fake_responses.py`、`test_fake_upstream_contract.py` | **本次已改**：假上游可绑定容器地址及 TLS，并在自身请求记录中保留 TCP 对端地址；先红后绿验证该证据字段。 |
| `apps/backend/tests/providers/lifecycle/test_request_pipeline.py`、`lifecycle/request/test_request_admission.py` | **本次改/新增**：保留请求字段失败关闭断言，并把既有超 200 行文件按“入站策略 / 额度与可信出站”拆分；测试语义不变。 |
| `apps/backend/tests/providers/net/test_runtime.py`、`tests/jobs/runtime/test_provider_backend.py` | **本次新增**：运行清单/篡改、无密钥 config、入口绑定与 Worker/Adapter provider 选择的替身测试。 |
| `apps/backend/tests/providers/policy/test_controlled_failures.py` | **本次已改**：错误码扫描器把非秘密 Compose 环境字段 `AGENTEXAM_RUN_ID` 从错误码候选中精确排除；断言仍扫描整个包，无跳过。 |
| `docs/architecture/modules/execution-and-evaluation/ARCHITECTURE.md`、`docs/interfaces/CODEX_AUTHENTICATION.md` | 当前运行能力与边界的权威描述。 |
| `docs/LLY/03-progress/PROGRESS_LOG.md`、`.scratch/ui-catalog-providers/issues/05-fake-provider-secure-execution-chain.md` | 本片状态与任务单 Comments。 |

采用的模式：Worker 的 `RunBoundExecutionBackend` 保持既有执行端口，代理运行时作为 Harbor Adapter 内部组合对象；`net/` 只负责验证及创建固定拓扑，不成为第二执行接口。固定 Harbor/Codex 合成链已按此接口实测。

## 自验证方式与成功标准（修改前定义）

1. 本机替身：固定拓扑合成；任意主容器出网附加、缺少代理/令牌、非法覆盖均在运行前失败；令牌颁发与结束撤销；生成 `config.toml` 不含凭据值。反例改动应使相应断言失败。
2. 负责人机器合成链：正式 Registry → 提交 → 批准 → Worker → Harbor，仅使用受控假提供方，收集完整实际命令、假上游自身请求记录与 Run 终态；失败或没跑不得称通过。
3. 宿主侧：容器、网络、卷按名称 + `agentexam.task=05` + 本轮 scope 三重核对后精确清理；留镜像/卷前后清单、Docker inspect、原始证据及 SHA-256。
4. 静态与回归：相关 pytest、ruff、mypy；PG 回归仅在本机专属实例运行，负责人机器现有 55432 不碰。

2026-09-23 接线 TDD：入口测试先红为 `TypeError: validate_agent_mode() got an unexpected keyword argument 'provider_bound'`；说明产品入口尚未识别经清单绑定的 provider 模式。实现只增加该受控模式，不放宽普通 `extra_docker_compose`。

## 已执行的只读核查与实际结果

- `git fetch origin`：`origin/lly/dev` 前进至 `1a0832e`；`git merge --ff-only origin/lly/dev` 成功；`git merge --no-edit origin/main` 成功，无冲突。当前 `lly/dev` HEAD `ac22f7d`，包含最新 `origin/lly/dev` 与当时的 `origin/main`；开工前工作树干净。
- S9 最新证据见 [本机 PG 验收](2026-09-22-task05-s9-pg-acceptance-local.md)，本轮未在负责人机器的 55432 上运行 PG 测试。
- `harbor_entry.validate_network_config()` 明确拒绝任意 `extra_docker_compose`；T2 探针绕开了产品入口。S10 必须提供受控内部接线，不能把原门禁删除。
- `codex/provider_config.py` 只渲染 `env_key`（令牌变量名）；固定 Harbor Codex 使用 `CodexUploads` 上传配置，阶段计划同时要求“令牌不进 argv/env/日志/制品”。[OpenAI Docs 的自定义提供方配置](https://developers.openai.com/codex/config-advanced#custom-model-providers)另有 `[model_providers.<id>.auth]` 命令取令牌入口，不能只因最新文档存在就推断固定 0.153.0 支持。
- 固定 0.153.0 实测：使用已缓存的 `python:3.12.13-slim-bookworm` 与固定 `bin/codex`，`docker run --rm --pull never --network none`，只读挂载非秘密脚本与 CLI 文件包，容器内 tmpfs 生成随机假令牌与短命文件，认证命令通过 stdout 向 CLI 返回令牌；宿主 Docker 参数/环境均无令牌值。四次独立 scope 分别为 `t05-s10-auth-20260922-01/02/03/04`，`--rm` 后按 task+scope 查询容器、网络、卷均为空。前三轮先用 Python helper，第四轮换成产品渲染器采用的 `/bin/cat`。

| 探针条件 | 原始计数与结果 | 判定 |
|---|---|---|
| 不带零重试键，假上游回 401 | `exit=1`，`observed` 12 条，12 条 `bearer_matched=true` | 认证命令取令牌可行，但不能把默认重试当零。 |
| 顶层与 provider 表均设置 `request_max_retries=0`、`stream_max_retries=0`，回 401 | `exit=1`，`observed` 2 条，均匹配令牌 | 一次额外请求是 CLI 对 401 的认证刷新/重试行为；不能宣称所有 401 不重发。 |
| 同样的零重试配置，回代理预期的受控 502 | `exit=1`，`observed` 1 条，匹配令牌 | 固定 CLI 在该受控失败形态无重发；仍须在正式代理链验证所有上游 401 被改写，绝不直传。 |
| 同样的零重试 + `/bin/cat` 文件式认证，回受控 502 | `exit=1`，`observed` 1 条，`path=/responses`、`bearer_matched=true` | 精确验证本片新 TOML 的命令形态；仍不是 Harbor Trial。 |

这些是固定 CLI → 容器内假 HTTP 端点的隔离兼容性探针，**不是**正式 Registry/Worker/Harbor 合成链；执行镜像 ID `sha256:64d91f7b885eed272bba87909446b12ff408d4aaa5f1a0e9ca787bbea1a020b9`，每轮均有 `agentexam.task=05` 与相应 scope，`--rm`、`--pull never`、`--network none`，无宿主发布端口和可写挂载。不能用上述计数代替 S10 的整体验收。

隔离探针脚本（Git 忽略目录）`.tmp/t05-s10-auth-probe.py` 最终 SHA-256 为 `96CDDF753E1DEF23152395AE3B45EBA3070D648E904D30C5E5035F7E47E266FB`；本轮执行中先后改变过脚本的回复状态码和认证命令，因此这个哈希**只对应最终第四轮版本**，不能冒充前 3 轮的文件哈希。末次按标签只读复核原文：

```text
t05-s10-auth-20260922-01 containers=0 networks=0 volumes=0
t05-s10-auth-20260922-02 containers=0 networks=0 volumes=0
t05-s10-auth-20260922-03 containers=0 networks=0 volumes=0
t05-s10-auth-20260922-04 containers=0 networks=0 volumes=0
t05-s10-openssl-20260922-01 containers=0 networks=0 volumes=0
```

第五个 scope 只读确认缓存 Python 镜像含 `/usr/bin/openssl`，不是模型或 Harbor Trial。

## 自验证情况、偏差与停点

**替身与静态实测**：最终 `pytest tests/providers tests/jobs/runtime tests/test_codex_uploads.py tests/contract/test_execution_network.py -q --no-cov ... -k <排除两项缺固定 Harbor 路径>` → `258 passed, 2 skipped, 2 deselected in 31.97s`；两项 skip 是 Windows 不能创建目录 symlink、POSIX owner/权限位仅类 Unix；两项 deselect 是此 worktree 没有 `framework/harbor` 的固定路径测试，**不是通过**。`ruff check` 全绿、`ruff format --check` 本片文件全绿；`mypy src/eval_platform --no-incremental` → `Success: no issues found in 190 source files`。未做 PG 测试：此机 55432 是既有 `agentexam-local`，按用户要求不碰。

**历史中途记录——夹具增量**：`test_the_upstream_records_the_network_peer_not_just_a_request_count` 首跑按预期失败：`TypeError: FakeUpstream.__init__() got an unexpected keyword argument 'host'`，实现后单例复跑 `1 passed, 13 deselected in 0.57s`。该时点 Dockerfile 与 `serve.py` 只是新增，尚未构建、启动或验证；后续结果见文末最终验收。

**夹具独立实测（不等于 S10 正式链）**：`docker build --pull=false --network=none --label agentexam.task=05 --label agentexam.scope=t05-s10-fixture-20260922-01 -f tests/providers/runtime/Dockerfile.proxy -t agentexam-t05-s10-proxy:20260922 .` 退出 0；基底在本机缓存，未拉取，所得镜像 `sha256:d6afb8dc72c27b0a0cb106c6e8e3d07939c407ff847a2fabe32e02b59459cf42`。随后两只 `--pull never --network none --read-only --cap-drop ALL --security-opt no-new-privileges --user 65534:65534 --rm` 容器按 `agentexam.task=05` 与 `agentexam.scope=t05-s10-fixture-20260922-02` 启动：`agentexam-t05-s10-fixture-upstream` 日志 `fake-upstream-ready`；`agentexam-t05-s10-fixture-proxy` 日志 `proxy-ready`。`docker inspect` 显示两者 `network=none ports={} mounts=[]`、仅有 `/tmp` 的 65534-owned tmpfs；容器镜像 ID 与上述一致。代理内私有文件仅做 `stat`，结果：

```text
65534:65534:600 /tmp/run-token
65534:65534:600 /tmp/provider-profile.json
```

假上游容器内本地握手 `openssl s_client -connect 127.0.0.1:8080 -servername fake-upstream.t05.invalid -verify_hostname fake-upstream.t05.invalid -CAfile /opt/agentexam/tls/upstream.crt -brief` 退出 0，输出含 `Protocol version: TLSv1.3`、`Verification: OK`、`Verified peername: fake-upstream.t05.invalid`。这只证明夹具的 TLS 端点，不证明代理到它的跨容器转发。按名称、任务标签、scope 三重比对后执行 `docker stop`，两只 `--rm` 容器消失；同 scope 的 `docker ps -a`、`docker network ls`、`docker volume ls` 标签查询均为空。构建镜像暂留本机供后续合成链使用，非固定 Harbor 镜像，未删除任何已拉取镜像。

**跨容器正对照先红后绿（仍不是 Harbor Trial）**：第一次 `t05-s10-forward-20260922-01` 在带任务及 scope 标签的 `agentexam-t05-topology_egress` 临时 `internal=true` 网络上启动同一镜像的代理与 TLS 假上游，两者 `ports={}`、`mounts=[]`。容器内部发一条带 tmpfs 假令牌的 `POST /responses`，返回 `HTTP Error 502`，假上游日志只有 `fake-upstream-ready`，**未收到请求**。直接从代理容器到 `fake-upstream.t05.invalid:8080` 的 DNS/TLS 握手成功，定位为夹具监听 8080，但受控固定 URL `https://fake-upstream.t05.invalid` 未声明端口、实际走 443。此失败不计作产品拓扑失败；第二次探查得 429 是第一次失败使本 Run 的预算失败关闭，未当作网络结论。仅把夹具上游监听端口改为 443，不改固定地址/断言；失败轮三重核对后拆除。

第二次 `t05-s10-forward-20260922-02` 重用同名、重新建标记 scope 的无公网临时网络，镜像离线重建为 `sha256:fa721b35abba466fc8836e7af652b153615ecf98d33c6cc7051a9b75179d0d67`。代理容器内用其 tmpfs 假令牌向 `127.0.0.1:8080/responses` 发一条受控请求，原始输出：

```text
status 200 bytes 777
```

假上游自己的日志原文（从不打印 Authorization 值）：

```text
fake-upstream-ready
{"header_names": ["Accept-Encoding", "Authorization", "Content-Length", "Content-Type", "Host", "User-Agent"], "method": "POST", "model": "deepseek-flash", "path": "/responses", "peer": "172.22.0.3"}
```

`docker network inspect` 同时显示 proxy `172.22.0.3/16`、fake-upstream `172.22.0.2/16`、`internal=true`，因此上述对端地址确系代理 IP。`docker inspect` 显示两容器均有任务+本轮 scope 标签、`ports={}`、`mounts=[]`、镜像 ID 同上；三重核对后逐一 `docker stop`（`--rm` 自动删除），无连接容器后按名称+标签删除该网络。成功轮标签查询 `docker ps -a`、`docker network ls`、`docker volume ls` 均为空。**这仍是单内网替身正对照，不是双网络 Harbor Trial、不是正式 Registry→批准→Worker→Harbor Run，不能作为 S10 完成依据。**

**新增用例回归中的测量误判**：`pytest tests/providers tests/jobs/runtime tests/test_codex_uploads.py tests/contract/test_execution_network.py ...` 本轮首次为 `1 failed, 259 passed, 2 skipped, 2 deselected`；失败是 `test_every_internal_code_has_a_decision` 的正则把拓扑中的非秘密环境字段 `AGENTEXAM_RUN_ID` 当作错误码候选。没有改产品错误码或跳过断言；仅在扫描器现有 `_NON_CODES` 排除表中标注这一环境字段，保留递归扫描和相同的 `undecided == set()` 断言。针对性复跑 `tests/providers/policy/test_controlled_failures.py tests/providers/net/test_topology.py` → `18 passed in 0.06s`。全套相关回归**尚须再跑**。

该相关无 PG 回归随后以新的独立 `.tmp/pytest-s10-20260922-13` 完整复跑，实际 `260 passed, 2 skipped, 2 deselected in 32.38s`、退出 0。两项 skip 与此前相同（Windows symlink、POSIX 权限）；两项 deselect 仍是当前 worktree 缺固定 Harbor 路径，未宣称通过。以上 260 项不含正式 Registry/Worker/Harbor Run 验收。

**历史中途记录——Worker 路由首个纵切**：新增用例先红 `TypeError: RunBoundExecutionBackend.__init__() got an unexpected keyword argument 'provider_backend'`；实现后 `tests/jobs/runtime/test_worker_bindings.py` 全部 `12 passed in 0.04s`。该时点工厂尚未由 Worker 提供；后续接线与验收见文末。

**2026-09-23 产品链前的中途复核（历史）**：`pytest tests/providers tests/jobs/runtime tests/test_codex_uploads.py tests/contract/test_execution_network.py -q --no-cov -p no:cacheprovider -k <排除两项当时 worktree 缺 Harbor 路径的用例> --basetemp=.tmp/pytest-s10-20260923-01` → `261 passed, 2 skipped, 2 deselected in 32.22s`、exit 0。两项 skip 的平台原因未变，deselect 非通过。`ruff check --no-cache` → `All checks passed!`；`ruff format --check --no-cache` → `10 files already formatted`；`mypy src/eval_platform --no-incremental` → `Success: no issues found in 190 source files`；`git diff --check` exit 0，仅输出 Windows `core.autocrlf` 的 LF→CRLF 提示，未发现空白错误。该时点正式 Run 尚未运行；现由文末第 07 轮与 `276 passed, 2 skipped` 覆盖。

收尾残留复核：`t05-s10-fixture-20260922-02`、`t05-s10-forward-20260922-01`、`t05-s10-forward-20260922-02` 三个 scope 的容器/网络/卷按双标签查询均为空。首次统一复核把 Docker `ps` 模板写成 `.Name`，容器项命令 exit 1；改为 `.Names` 后三个 scope 都 exit 0、空输出，故只以后者作为容器残留证据。离线构建的任务镜像未删、仍留本机供后续 S10 正式链使用，不计入容器/网络/卷零残留。

**历史停点与当时方案（已由文末验收覆盖）**：该时点 `RunBoundExecutionBackend` 仍拒绝假提供方，`harbor_entry.main()` 仍调用默认严格门禁；新渲染器/上传方法尚无 Run 调用方，代理镜像、启动/就绪、令牌与资源收束未接线。该记录解释后续为何新增固定运行清单、精确镜像 ID 与产品链验收，不再表示当前状态。

阶段依赖需处理：现有 `tests/providers/contract/support/fake_responses.py` 是**明文 HTTP**，`provider_access/server/egress.py` 强制上游 **HTTPS**；可启动的代理镜像与假上游 TLS 包装被计划第 6 节列在 S11（`Dockerfile.proxy` 等），但第 5 节已经要求 S10 跑完整假提供方合成链。可行的下一步是把**仅用于受控假提供方的镜像/证书测试夹具**提前纳入 S10，或由用户提供已缓存、身份可核的等价镜像；随后接通 Worker/Harbor/Agent 并做正反对照。未确认这个阶段边界前，不会把 HTTP 假上游当 HTTPS、放开默认网络门禁、把令牌塞入 env 或带真实 Key 试跑。

**2026-09-22 用户确认**：允许把 `Dockerfile.proxy` 与只含合成证书的假上游 TLS 测试夹具提前纳入 S10，以完成第 5 节要求的真实合成链；这仅改变夹具的实施顺序，不提前宣称 S11 五组对照已通过。相应计划文件树增加 `apps/backend/tests/providers/runtime/Dockerfile.proxy` 及受控假上游夹具（若 runtime 目录达到 8 文件，后者置于既有 support 子目录或新建其子目录）。S10 验收后才可顺序进入 S11。以上前一段“未确认”描述为本次确认前的历史停点，不再是当前阻塞。

**2026-09-23 用户确认继续**：继续完成 S10，仍不提前进入 S11。已确认的测试接缝是现有 `ExecutionBackend.execute()`：正式 Registry/提交/批准保持应用层现有接口，Worker 的 `RunBoundExecutionBackend` 只选择现有 `HarborExecutionAdapter` 的 ChatGPT 或 provider 实例；provider 的 overlay、短令牌转运和结束清理由 Harbor Adapter 内部组合，不新增第二个应用端口。成功标准不变：必须实际取得正式合成 Run 终态、假上游自己的请求记录及三重标签清理证据后才能签收/提交/推送。

本段是第 03 轮后的历史状态：当时 **S10 尚未通过，未提交、未推送、未开 PR**；后续第 07 轮成功事实见文末。全过程未读取真 Key，未调用真实供应商，未修改共享 Docker/代理/防火墙，未重建 Harbor。

### 2026-09-23 正式合成链第一次执行（失败，保留）

使用正式 `AgentRegistry`、`JobSubmission`、`OwnerApproval`、`WorkerShell`、`JobExecutor` 与真实 `HarborExecutionAdapter`；仓储和判卷边界为隔离内存替身，未连接负责人机器 PostgreSQL 55432/MinIO。受控夹具镜像离线重建为 `sha256:00cd61c88f5296be6b05e0592799ab8c3c10d13eeecf5255177b4b1ed5deff1d`，构建禁用网络和拉取。

第一轮 scope `t05-s10-f6c12baf78c7b7347d6f`：提交状态 `AWAITING_OWNER_APPROVAL`，批准后 `QUEUED`，Worker 确实领取；终态 Job `FAILED/BATCH_FAILED`、Run `FAILED/EXECUTION_AGENT_FAILED`。假上游日志只有 `fake-upstream-ready`，没有请求；按任务+scope 查询容器、网络、卷均为空。原始证据 `.tmp/t05-s10-product-20260923-01/`。

诊断事实：Codex 实际请求 `http://proxy:8080/models`，主请求也收到代理返回的受控 `PROVIDER_REQUEST_REJECTED`，所以 provider 配置已生效且没有绕过代理；同时 CLI 后台尝试 `chatgpt.com` MCP，但主容器仅接 internal 网络，连接失败，未形成外部请求。失败点是代理严格白名单拒绝固定 CLI 的实际 POST 结构，不是拓扑。下一步只在测试夹具中输出内部拒绝码、body 字段名、工具类型和 header 名称（不输出正文、令牌或 header 值），取得区分证据后再决定最小白名单改动。

第二轮诊断 scope `t05-s10-29099855fa1f082345de` 同样安全失败并清理为 0，原始证据 `.tmp/t05-s10-product-20260923-02/`。代理日志给出内部码 `REQUEST_UNKNOWN_FIELD`；实际 body 字段名为 `client_metadata/include/input/instructions/model/parallel_tool_calls/prompt_cache_key/reasoning/store/stream/tool_choice/tools`，工具类型为 `function` 与 `namespace`。假上游仍只有 ready、请求数 0。不能据此把未知字段全部放开；先补取这些控制字段的类型/固定值，再写精确校验和反例。

第三轮诊断 scope `t05-s10-511b9373847b10e15c46` 仍按预期以同一码失败、清理为 0，原始证据 `.tmp/t05-s10-product-20260923-03/`。安全摘要确认：`include=[reasoning.encrypted_content]`、`parallel_tool_calls=true`、`reasoning={effort: medium, summary: auto}`、`store=false`、`tool_choice=auto`；`prompt_cache_key` 为 36 字符 UUID；`client_metadata` 只有 7 个固定键且值均为字符串。未记录缓存键内容、metadata 值、题目正文、工具定义或认证头值。

据此新增精确策略：上述控制字段只有固定形态可通过；任一变体统一 `REQUEST_CONTROL_FIELD_INVALID` 并映射受控拒绝。`client_metadata` 与 `prompt_cache_key` 校验后从上游 body 剥离；固定 Codex 追踪 header 只接收后剥离，只有原有 `Accept/Accept-Encoding/User-Agent` 可转发。未知字段仍拒绝。策略 TDD 首轮 `10 failed, 28 passed`，实现后策略/生命周期/失败码 `45 passed`，Ruff、mypy 通过；文件随后压回项目 200 行上限内。

格式化后的当前全量无 PG 回归使用仓库外层现有 venv，并把 pytest 临时目录显式放在本 worktree：`276 passed, 2 skipped in 33.58s`。两项跳过仍分别是 Windows 不能创建目录 symlink、POSIX owner/权限位仅类 Unix。此前两次非授权沙箱执行分别被 `C:\Windows\Temp\pytest-of-YINGYI` 和 worktree 临时目录的清理权限拒绝，表现为 `169 passed, 1 skipped, 108 errors`；错误栈均是 `PermissionError [WinError 5]`，不是产品断言失败。换用相同测试命令、全新 worktree 临时目录并在已授权本机环境执行后退出 0，未删除或跳过测试。

当前静态复核：`ruff check` → `All checks passed!`；`ruff format --check` → `224 files already formatted`；`mypy src/eval_platform`（缓存定向到 `.tmp/mypy-s10-20260923-01`）→ `Success: no issues found in 192 source files`。最终产品合成链尚待以包含该精确策略的新夹具镜像复跑，故本段仍不把 S10 标为通过。

最终受控夹具镜像离线构建命令使用 `--pull=false --network=none`，镜像 ID 为 `sha256:7442477ce2f92718249315558fb6a21db3d3184a3de337ba1c94c0530aca2ed9`，镜像标签为 `agentexam.task=05`、`agentexam.scope=t05-s10-product-final-build-20260923-01`。第 04 轮因命令参数把既有数据修订目录 `61231f2...15107` 误写为 `612b420...15107`，在 Task Registry 读取前以 `CatalogUnavailable` 停止；未形成 Trial scope、未创建 Docker 项目资源。解决为只读确认实际缓存文件 `train-0000.parquet` 存在且大小 931,193 字节后，使用正确固定修订路径和新证据目录重跑，保留第 04 轮为执行偏差。

第 05 轮 scope `t05-s10-2ed691ef9d19c5b43cd9` 已证明产品拓扑和代理主请求成立，但 Job 后处理失败：Harbor returncode=0，假上游记录 `/responses` 的 TCP 对端为 `172.22.0.4`，与 proxy 的 egress IP 完全相同；main 仅 internal，proxy 为 internal+egress，fake-upstream 与侧车仅 egress；internal=`true`、egress=`false`；四容器 `PortBindings={}`，proxy/fake-upstream/侧车无挂载，main 只有本 Trial 下 `/logs/verifier`、`/logs/agent`、`/logs/artifacts` 三个 Harbor 必需可写绑定。拆除后 task+scope 容器/网络/卷均为空。

第 05 轮终态仍为 Job `FAILED/BATCH_FAILED`、Run `FAILED/EVIDENCE_UNAVAILABLE`，不能计通过。根因是隔离合成脚本同时用了本地 Harbor 产物和内存假判卷产物，却把 `EvidencePublication` 的读取端单独绑定到 `LocalArtifactReader`；因此补丁读取成功后，内存判卷报告被错误地到本地目录查找。解决只改 Git 忽略的 `.tmp/t05-s10-product-chain.py`：绝对路径引用路由到受限本地读取器，相对 `runs/...` 引用路由到同一个内存制品仓库；产品门禁、网络和断言均未改变。脚本 Ruff 复核通过，须以新 scope 重跑。

第 06 轮 scope `t05-s10-0ccc1f7af595770c3bbe` 的正式链终态已成为 Job `COMPLETED`、Run `COMPLETED`、失败码均为空，Worker 已领取，受控假判卷因空补丁给出 `resolved=false`；标签残留容器/网络/卷均为空。证据 SHA-256 清单共 56 项，独立复算 `mismatches=0`；卷前后清单相同。**但本轮仍不作为最终签收轮**：监控线程在 Harbor 拆容器竞态中先取得旧容器 ID，随后 `docker logs` 返回 `No such container`，脚本错误地用该 daemon 错误覆盖了已经取得的 proxy/假上游日志；末期无 IP 的 inspect 同样覆盖了网络仍连接时的快照。解决只改忽略目录证据采集器：日志仅在 `docker logs` returncode=0 时更新，容器 inspect 按非空网络 IP 数保留信息最完整快照。产品行为、门禁、断言与夹具镜像均未改变；须以新 scope 再跑并实际保住假上游自己的请求记录。

## 最终验收：第 07 轮正式产品合成链

### 实际命令与原始终态

实际从 worktree 执行（命令参数只含固定数据、固定 Codex 包、固定测试镜像与证据目录，无凭据）：

```powershell
& E:\9.1agent_exam\apps\backend\.venv\Scripts\python.exe .tmp\t05-s10-product-chain.py `
  --project-root E:\9.1agent_exam\runtime\lly-dev-verify `
  --parquet E:\9.1agent_exam\runtime\cache\swe-gym-lite\61231f2c90b18985b42a1419738a240085a15107\train-0000.parquet `
  --codex-archive E:\9.1agent_exam\runtime\prototype\m0-codex-install-20260907-01\codex-0.153.0-linux-x64.tgz `
  --provider-image sha256:7442477ce2f92718249315558fb6a21db3d3184a3de337ba1c94c0530aca2ed9 `
  --evidence E:\9.1agent_exam\runtime\lly-dev-verify\.tmp\t05-s10-product-20260923-07
```

原始 stdout（exit 0）：

```json
{"approval":{"status":"QUEUED"},"registry":{"agent_configuration_id":"a70f6796-3e88-4fd3-be5d-bb6c5bdb5967","task_id":"6338356e-7baf-46ba-b047-0970644db04d"},"residual":{"containers":[],"networks":[],"volumes":[]},"scope":"t05-s10-8282ed1a824cc79310f6","submission":{"job_id":"4be19d58-43dd-42d4-8904-5b2bf774e8e4","status":"AWAITING_OWNER_APPROVAL"},"terminal":{"job_failure_code":null,"job_status":"COMPLETED","resolved":false,"run_failure_code":null,"run_id":"e92f7977-15ae-4b6f-965f-775d85f618d0","run_status":"COMPLETED"},"worker_claimed":true}
```

这里使用正式 `AgentRegistry → JobSubmission → OwnerApproval → WorkerShell → JobExecutor → HarborExecutionAdapter`；为遵守“不碰负责人机器 55432/MinIO”，仓储与判卷端口采用隔离内存替身。`resolved=false` 是受控假判卷对空补丁的预期判定，不是 Run 失败；Job/Run 终态与失败码是本片验收事实。

Harbor 进程证据：returncode=0、timed_out=false、warnings=[]，运行 1m21s；内部入口由产品代码构造为固定 Harbor Python + `harbor_entry.py --config <本轮 harbor-config.json> --harbor-root <固定 Harbor> --control-dir <本轮目录>`，入口再执行 `harbor run --config <同一配置> --yes`。配置的 `environment.delete=true`，拆除由固定 Harbor 常规路径执行；没有另行使用全局删除命令。

### 假上游原始记录与网络图

假上游自己的原始日志：

```text
fake-upstream-ready
{"header_names": ["Accept-Encoding", "Authorization", "Content-Length", "Content-Type", "Host", "accept", "user-agent"], "method": "POST", "model": "deepseek-flash", "path": "/responses", "peer": "172.22.0.2"}
```

日志只记录 header 名，不记录 Authorization 值。`peer=172.22.0.2` 与 inspect 中 proxy 的 egress IP 完全相同。

```text
main (172.23.0.3)
  └─ internal [Internal=true]
       └─ proxy (172.23.0.2)
            └─ egress [Internal=false] (172.22.0.2)
                 ├─ fake-upstream (172.22.0.4)
                 └─ Harbor sidecar (172.22.0.3)
```

main 没有 egress 附加；proxy 是唯一跨两网服务。固定 Harbor 侧车没有共享 main 网络命名空间，而是按精确 provider 覆盖接在 egress。

### 宿主 inspect、私有面与清单差异

| 服务 | 镜像 ID | 网络 | PortBindings | Mounts | 标签 |
|---|---|---|---|---|---|
| main | `sha256:250daa08...ed3a` | internal `172.23.0.3` | `{}` | 本 Trial 目录内 `/logs/artifacts`、`/logs/verifier`、`/logs/agent` 三个 Harbor 必需可写绑定 | task=05、scope=`t05-s10-8282ed1a824cc79310f6` |
| proxy | `sha256:7442477c...2ed9` | internal `172.23.0.2` + egress `172.22.0.2` | `{}` | `[]` | 同上 |
| fake-upstream | `sha256:7442477c...2ed9` | egress `172.22.0.4` | `{}` | `[]` | 同上 |
| Harbor sidecar | `sha256:dd1cd5ac...8dd3` | egress `172.22.0.3` | `{}` | `[]` | 同上 |

镜像和卷清单使用稳定身份（镜像 ID/repository/tag/digest）比较：前后差异均为空；未删除固定拉取镜像或其他项目卷。最终测试镜像在 Trial 前已经离线构建，因此留在本机，不伪装成拆除差异。

短令牌与私有文件核查：Run 后 `.provider-auth-placeholder.json` 已删除；本轮执行目录没有 token/profile/auth/config.toml/secret 命名文件；对固定假值、client token、run token、profile 与 Bearer 标记的受限证据复扫输出 `no-matches`。`provider-runtime.json` 只保留 version、scope、固定镜像 ID、compose 路径。单测另钉住 config.toml 不含凭据、令牌只经 stdin 上传、缺失/畸形令牌在 I/O 前失败关闭。

### 清理、哈希与失败关闭区分力

Harbor 返回后，脚本及独立宿主命令分别按 `agentexam.task=05` + 本轮 scope 查询：容器、网络、卷均为空。没有全局 prune，没有停止或删除既有持久化服务。

原始证据目录：`.tmp/t05-s10-product-20260923-07/`。`SHA256SUMS.txt` 含 56 个文件，逐项重新计算结果 `entries=56 mismatches=0`；该清单文件自身 SHA-256 为 `51a1530d4f041c32afd45cd2c770cb0d0669379131ec849a263330377d07c262`。

区分力证据不是只看成功轮：

- 拓扑任一网络成员、路径、scope、镜像 ID 被篡改时，`test_tampered_topology_fails_closed` / `test_product_gate_rejects_a_different_path_or_tampered_file` 失败关闭。
- 缺失或畸形代理短令牌由 `test_missing_or_malformed_proxy_token_fails_closed` 拒绝；令牌不进入 Compose argv，受 `test_fetches_proxy_token_without_echoing_it_into_compose_arguments` 钉住。
- 未批准字段和固定 CLI 控制字段变体分别由 `test_rejects_unknown_and_missing_fields`、`test_rejects_any_mutation_of_the_fixed_cli_control_fields` 拒绝。第 02/03 诊断轮实际得到代理拒绝、假上游请求数 0；精确适配后第 07 轮才得到一条上游记录。
- 拆分后的相关无 PG 全量回归最终为 `276 passed, 2 skipped in 34.86s`；`ruff check` 为 `All checks passed!`，`ruff format --check` 为 `227 files already formatted`，mypy 为 `Success: no issues found in 192 source files`。两项 skip 仅为 Windows 目录 symlink 和 POSIX owner/权限位能力限制。
- 架构指标复核：本片新增/修改 Python 文件均不超过 200 行；`provider_access/` 顶层 8 文件、`net/` 4 文件、`tests/providers/runtime/` 8 文件，均未越线。新增测试按职责下沉，未再向已满目录增加顶层文件。

### 偏差、限制与结论

- Harbor stderr 仍有一次“转换 Codex events 为 trajectory 时文件暂不可见”的 `FileNotFoundError`；Harbor returncode=0，补丁和 Run 终态可信，但公开 trajectory 本轮未形成。它不属于 S10 网络接线验收，作为 S11/后续 Windows Harbor 证据兼容问题保留，不能写成已验证。
- 本轮不跑 PostgreSQL/MinIO 和真实 SWE-Bench 判卷；这是遵守负责人机器 55432 硬边界，仓储/判卷使用隔离替身。产品应用服务、Worker 选择和真实 Harbor Adapter 已实际执行。
- 没有读取真实 Key、调用真实供应商、验证真实 DeepSeek/Kimi 协议、跑 S11 五组完整对照或第二个真实 Harbor Trial；这些均不得由本轮外推。

**结论：S10 的产品接线及计划要求的一 Run 受控合成链已通过，实现提交为 `d96fad9`，已推送至 `origin/lly/dev` 并更新 PR #41。S11 现在具备顺序前置条件，但本次没有启动 S11。**
