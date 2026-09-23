# 任务 05 S11 集成验证与收口行动记录

- 日期：2026-09-23
- 状态：完成
- 分支：`lly/dev`
- 范围：`STAGE1_T2_S9_S10_S11_PLAN.md` 第 6 节及用户追加的六项挂账收口

## 1. 情况说明

S10 已把 T2 验证过的双网络形态接入正式 Worker → Harbor 路径，但只跑过单个 Harbor Trial，并使用内存仓储和假判卷。S11 要在不读取真实 Key、不访问真实供应商、不重建固定 Harbor、不触碰负责人机器既有 `127.0.0.1:55432` 服务的前提下，完成五组正反对照和六项遗留验证。

开工前合并顺序已落实：`origin/agent+api` 先进入 `origin/main`，再由 `origin/main` 进入 `origin/lly/dev`。当前提交 `119cdd6`，三者祖先关系均已验证；固定 Harbor 由本 worktree 的目录联接指向主仓库中干净的固定提交 `6af8d6e31eced13b93849cdf80feeadf24603d15`。

本轮开工时 E 盘只余约 505 MiB。原始证据必须紧凑保存并持续监控空间，不删除既有证据、镜像、卷或他人资源。

## 2. 已确认的公开接缝

本轮按 TDD（先写失败测试，再实现）推进，测试接缝为：

1. `runtime/verify.ps1`：S11 五组对照、并发 Trial、证据与精确清理的公开入口。
2. `codex/provider_config.py` 与 provider access 失败映射：配置错误必须成为受控失败码，不能裸抛 `ValueError`。
3. 代理流式响应和结算接缝：压缩 SSE 仍应正确识别终止用量；无法安全解释时失败关闭，绝不少计费。
4. Harbor 进程证据接缝：Windows 上 trajectory 临时不可见不得被静默当成完整成功；须有可复现诊断和受控处理。
5. 固定 Fork 判卷接缝：使用仓库固定 Fork 的独立判卷/报告路径，不再以内存 evaluator 代替。
6. Worker 兼容路径与持久化接缝：旧 ChatGPT 合成链在隔离 PostgreSQL/MinIO 上回归，且不使用既有 55432。
7. 网络合成与资源标签：两个并发 Harbor Trial 必须各自隔离，且只按项目名 + `agentexam.task=05` + 本轮 scope 三重匹配清理。

## 3. 实施措施与成功标准

### 3.1 受控配置失败

- 先增加失败测试，证明现有裸 `ValueError("PROVIDER_CONFIG_*")` 未进入公开受控失败映射。
- 再将配置错误收口到现有 provider access 错误类型及稳定公开码。
- 成功：全部配置反例均返回受控码，公开消息不含秘密或内部异常细节。

### 3.2 压缩 SSE 与用量结算

- 先用本地假上游构造 `Content-Encoding: gzip` 的 SSE 终止事件，证明现实现无法正确结算。
- 再在代理响应链中加入受限解码/扫描，同时保留客户端响应语义或明确失败关闭。
- 成功：压缩正例按上游 usage 结算；损坏压缩体失败关闭且不低估用量；不调用真实供应商。

### 3.3 Windows trajectory 竞态

- 从 S10 原始 stderr 和固定 Harbor 源码定位 `FileNotFoundError` 的确切阶段。
- 写竞态回归测试后，在本仓库适配层做最小、可界定的等待/重试或受控失败；不修改固定 Harbor。
- 成功：轨迹证据可读；若最终不可读则明确失败，不把缺轨迹写成通过。

### 3.4 五组正反对照与双 Trial

- 新增 `runtime/verify.ps1`，复用 `Dockerfile.proxy`，辅助实现落到子目录；为保持顶层最多 8 文件，将既有可移动测试放入子目录并更新引用。
- 五组分别验证：拓扑、直连拒绝、宿主隔离、假 Key 探查、精确清理。
- 每组包含正例、反例和“受控注入错误 → 断言失败 → 恢复”的区分力记录。
- 两个 Harbor Trial 同时存活时验证网络、项目、标签、临时令牌和资源互不可见。
- 成功：全部真实断言通过；任一不成立即停止，不降低标准。

### 3.5 固定 Fork 与旧链回归

- 固定 Fork 执行独立判卷并生成报告；验证报告不是 Worker 内存替身生成。
- 旧 ChatGPT 路由在隔离 PostgreSQL/MinIO 上做无真实模型/无真实凭据的合成回归，验证编排、持久化与失败关闭。
- 成功：固定 Fork 产出可核验报告；旧路由回归不触碰 55432，隔离存储资源精确清理。

### 3.6 证据与文档

- 原始输出留在 `.tmp`，生成逐文件 SHA-256 清单。
- 行动文档写入真实命令、输出、Run 终态、假上游记录、inspect 摘录、清理复核、区分力和未验证项。
- 同步进度日志、任务 05 Comments、当前架构/接口文档（若行为改变）。
- 提交只包含 S11 本片，推送 `origin/lly/dev`，更新既有 `lly/dev → main` PR。

## 4. 实际修改文件树

```text
apps/backend/
├── src/eval_platform/adapters/execution/
│   ├── codex/provider_config.py              # 配置异常改为 ProviderAccessError
│   ├── harbor/
│   │   ├── adapter.py                        # 成功进程后调用 trajectory 恢复
│   │   └── recovery/trajectory.py            # 固定 Harbor 转换器 + Windows 长路径恢复
│   └── provider_access/
│       ├── failures.py                       # 新受控配置/传输错误映射
│       └── server/egress.py                  # identity/gzip 受限解码与流扫描
└── tests/
    ├── jobs/execution/conftest.py             # 允许显式随机回环 MinIO 端口
    ├── providers/
    │   ├── contract/support/fake_responses.py # gzip 假上游响应夹具
    │   ├── lifecycle/test_egress_and_surface.py
    │   ├── policy/test_provider_config_rendering.py
    │   └── runtime/
    │       ├── verify.ps1                     # S11 公共执行入口（顶层第 8 个文件）
    │       ├── uploads/test_provider_uploads.py # 从顶层移入，职责不变
    │       └── s11/                           # 8 个文件：捕获、判定、并发、存储
    └── unit/harbor/test_trajectory_recovery.py
docs/
├── actions/2026-09-23-task05-s11-integration.md  # 本行动与证据报告
├── LLY/03-progress/PROGRESS_LOG.md                # 当前进度
└── interfaces/CODEX_AUTHENTICATION.md             # 当前安全机制与验证边界
.scratch/ui-catalog-providers/issues/
└── 05-fake-provider-secure-execution-chain.md     # 任务 Comments/验收状态
```

设计上沿用 Adapter 模式：`HarborExecutionAdapter` 只编排恢复，不内嵌转换细节；`recovery/trajectory.py` 是固定 Harbor 的兼容适配层。S11 测试侧以 `DockerIO` 作为命令边界，以纯 `verdicts.py` 作为五组判定模块，真实并发运行与判定解耦。所有新增 Python 文件不超过 200 行；`runtime/` 顶层和 `runtime/s11/` 均正好 8 个文件。

## 5. 自验证方式

- 单元/契约：定向 `pytest`，覆盖受控配置失败、gzip SSE 结算、trajectory 竞态和网络/清理断言。
- 静态检查：Ruff lint/format、Mypy。
- 集成：`verify.ps1` 启动两个受控 Harbor Trial 和本地假上游，记录五组正反对照、Run 终态及固定 Fork 报告。
- 存储：仅用本轮隔离 PostgreSQL/MinIO；记录容器、网络、卷、端口及标签，确认不使用 55432。
- 清理：拆除前后镜像/卷清单对比；按三重条件查询容器/网络/卷均为空；禁止全局 prune。
- 秘密：哨兵正对照可检出，而做题侧、环境、argv、日志、公开输出和运行目录均零命中。

## 6. 实际执行与结果

### 6.1 TDD 红绿记录

1. provider config：旧实现对五类 `PROVIDER_CONFIG_*` 直接抛 `ValueError`，新增测试首轮 `25 failed / 14 passed`；接入 `ProviderAccessError` 和公开受控映射后 `39 passed`。
2. gzip SSE：新增真实 HTTP gzip 流与未知编码用例，旧实现 2 项失败（压缩字节被原样中继且未拒绝）；实现受限解码后相关用例 `39 passed`。损坏/未知编码分别映射 `TRANSPORT_CONTENT_DECODING_FAILED` / `TRANSPORT_CONTENT_ENCODING_UNSUPPORTED`。
3. trajectory：先复现固定 Harbor 转换器在 Windows bind mount session 上的 `FileNotFoundError`。生成式恢复脚本的语法测试先以 `unterminated string literal` 失败；修复后又以 299 字符路径复现两套 Python 均 `FileNotFoundError`。只在子进程和宿主文件检查使用 `\\?\` 扩展路径后，两个既有 session 均生成 7,223 字节 trajectory；最终 5 项恢复测试通过。
4. Windows → Linux stdin：真实 Trial 的秘密扫描返回 2；独立 `bash -n` 原文为 `syntax error near unexpected token $'do\r'`。回归测试先证明 stdin 是 `str`，改成 UTF-8 `bytes` 后五组区分力测试共 `7 passed`。
5. 五组区分力：对已验证形状分别注入错误网络角色、metadata 开放、宿主端口、workload 哨兵命中、残留容器，五组判定各自失败；恢复原证据后全部通过。该负控位于判定层，未在真实机器上故意开放公网或宿主边界。
6. 提交前审计发现“损坏 gzip”已有受控错误映射但缺独立实测；补入畸形 gzip 负例和 `zlib.error` 映射后定向 `65 passed`。首轮重跑因当前受限进程无权读取系统 pytest 临时目录、Ruff 旧缓存也不可写而出现基础设施错误；改用工作树 `.tmp` 下的专用 pytest 临时目录，并让 Ruff 禁用缓存后，定向、静态与全量检查全部通过。

### 6.2 最终统一入口与原始输出

最终命令（参数均为本地固定输入，无 Key）：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File apps/backend/tests/providers/runtime/verify.ps1 `
  -Python E:\9.1agent_exam\apps\backend\.venv\Scripts\python.exe `
  -ProjectRoot E:\9.1agent_exam\runtime\lly-dev-verify `
  -Parquet E:\9.1agent_exam\runtime\lly-dev-verify\runtime\cache\swe-gym-lite\61231f2c90b18985b42a1419738a240085a15107\train-0000.parquet `
  -CodexArchive E:\9.1agent_exam\runtime\prototype\m0-codex-install-20260907-01\codex-0.153.0-linux-x64.tgz `
  -ProviderImage sha256:b69ab6d82f8dee840b381f038b6ad7ecad3c9cf4f6013990d2d1ed482a27037a `
  -PostgresImage sha256:5cce759a2777634ff1edd0d56b9241a2961deb7f72e125d4af6ae2928163a6b6 `
  -MinioImage sha256:922042a62be66dc71bd1b23de25c7c232a6084033f3bcc2337ab49611cc3aba8 `
  -EvidenceRoot .tmp\t05-s11-verified-20260923-06
```

控制台原文：

```text
........................................................................ [ 96%]
...                                                                      [100%]
75 passed in 12.89s
{"groups":{"direct_refusal":[],"fake_key":[],"host_isolation":[],"precise_cleanup":[],"topology":[]},"inventory_diff":{"images":{"added":[],"removed":[]},"volumes":{"added":[],"removed":[]}},"scopes":["t05-s10-c22b2ca1298ccafb0c2c","t05-s10-286ed0b40cc405362b6f"],"status":"verified","trials":[{"run_id":"33d2bb5a-edf8-43b3-a4bd-cd44b5866088","termination_reason":"completed","trajectory":true,"warnings":[]},{"run_id":"27c37df8-c75f-46f5-a5e8-b15986e24cbb","termination_reason":"completed","trajectory":true,"warnings":[]}]}
.                                                                        [100%]
1 passed, 4 deselected in 54.19s
.                                                                        [100%]
1 passed in 1.96s
status=verified
```

固定 Fork 留下一个已断开的 `image_build_dir` 重解析点，首轮最终散列因 `Get-FileHash` 的长路径限制失败。修复为“重解析点单列、普通文件用扩展路径文件流哈希”后只补清单（未重跑容器）：

```text
evidence=E:\9.1agent_exam\runtime\lly-dev-verify\.tmp\t05-s11-verified-20260923-06
status=verified
```

最终证据：`.tmp/t05-s11-verified-20260923-06/`；`SHA256SUMS.txt` 139 行，`REPARSE_POINTS.txt` 1 行。完整命令记录、stdout、inspect、日志与中间失败轮次均保留在 `.tmp`；最终清单不把断开的重解析点伪装成普通文件。

### 6.3 五组真实对照

两个 scope：`t05-s10-c22b2ca1298ccafb0c2c`、`t05-s10-286ed0b40cc405362b6f`。

| 组 | 两个 Trial 的实际结果 |
|---|---|
| 拓扑 | 各有独立 `internal`（`Internal=true`）与 `egress`（`false`）；main 仅 internal，proxy 双网，fake-upstream/Harbor sidecar 仅 egress；四个 Network ID 互异。 |
| 直连拒绝 | `own_proxy=OPEN`；`own_upstream/public/host_gateway/metadata/other_trial=CLOSED`；`proxy_upstream=RECORDED`。 |
| 宿主隔离 | 8 个容器 `PortBindings={}`，无 Docker socket；proxy、fake-upstream、sidecar 均无挂载。两个 main 仅有各自 Trial evidence root 下 `/logs/agent`、`/logs/verifier`、`/logs/artifacts` 三个 Harbor 必需可写绑定。 |
| 假 Key | 两个代理私有正对照均为 1；两个 main 的文件/env/argv 命中均为 0；公开证据命中为 0。 |
| 精确清理 | 两 scope 的容器/网络/卷残留数组均为空；最终全局 `label=agentexam.task=05` 只读查询也为空。 |

假上游原文：

```text
{"header_names":["Accept-Encoding","Authorization","Content-Length","Content-Type","Host","accept","user-agent"],"method":"POST","model":"deepseek-flash","path":"/responses","peer":"172.23.0.4"}
{"header_names":["Accept-Encoding","Authorization","Content-Length","Content-Type","Host","accept","user-agent"],"method":"POST","model":"deepseek-flash","path":"/responses","peer":"172.22.0.4"}
```

两 peer 与各自 proxy egress IP 一致。最终镜像/卷稳定身份前后差异均为空；测试代理镜像为 `sha256:b69ab6d...27037a`，带 `agentexam.task=05` / `agentexam.scope=t05-s11-build-20260923-01`，因授权不含镜像删除而保留。

### 6.4 六条挂账项

1. **provider config 受控失败：完成。** 五个裸 `ValueError("PROVIDER_CONFIG_*")` 已进入现有受控错误类型和公开 `PROVIDER_ACCESS_FAILED` 文案。
2. **压缩与用量结算：受控假上游范围完成。** gzip SSE 在真实 HTTP 栈中解码、扫描终止 usage 并结算；未知/损坏编码失败关闭。硬边界禁止真实供应商调用，因此 DeepSeek/Kimi 的真实压缩响应与账单仍未验证。
3. **Windows trajectory：完成。** 修复生成脚本转义和 Python 260 字符路径限制；最终两个 Run trajectory 均为 true、warnings 为空，不修改固定 Harbor 或全局 LongPaths。
4. **固定 Fork：完成。** `wrong` 场景使用固定 Fork/固定镜像独立判卷：补丁成功应用但 `resolved=false`，FAIL_TO_PASS 记录目标测试失败；容器 `NetworkMode=none`、4 GiB、1 CPU、PIDs 256、无挂载，进程 returncode 0、warnings 空、cleanup verified 且 remaining_ids 空。
5. **旧 ChatGPT 合成链 + 隔离 PG/MinIO：完成到无真实模型边界。** ChatGPT Worker 绑定/运行时替身回归 `16 passed`；真实 PostgreSQL/MinIO 的 Registry→提交→批准→Worker→结果/审计/保留清理用例 `1 passed`。PG 使用随机回环 `32772`（不是 55432），MinIO 使用 `32773`；专属网络关闭 IP masquerade，发布只绑定 `127.0.0.1`；清理后容器/网络/卷均空。未读取 ChatGPT auth，也未调用真实模型。
6. **两个并发 Harbor Trial：完成。** 两个 Run 均 `completed`、trajectory=true、warnings=[]；做题侧不能连接另一 Trial 的实际 proxy IP。

### 6.5 精确清理与镜像/卷清单

- Trial：正式 Harbor 拆除后按 `agentexam.task=05 + scope` 查询，两 scope 的容器/网络/卷均空。
- 存储：资源名固定为 `agentexam-t05-s11-storage-*`，删除前逐个核验精确名称、`agentexam.task=05` 与本轮 scope；最终 `residual.json` 三数组为空。
- 固定 Fork：容器为 `--rm`，终态没有需删除的 ID；固定 Fork 自身用不可变 `agentexam.evaluator.run` + `agentexam.evaluator.evidence` 两标签复核 remaining 为空。它没有任务 05 的 task/scope 标签，这是既有 Fork 的标签模型，不伪装成三重匹配；本轮没有由清理器删除该容器。
- 最终 images/volumes 清单稳定差异均为 `added=[] / removed=[]`；没有删除固定镜像、其他卷或执行 prune。
- 提交前另做一次全局 `agentexam.task=05` 只读查询时，Docker Desktop 已停止，三条查询都返回命名管道不存在；没有为重复查询启动或修改共享 Docker。最终活体轮拆除后的同类查询已实际返回空并进入证据，因此本项记录为“提交时点无法再次观察”，不把它改写成第二次通过。

### 6.6 静态与回归检查

- Ruff check：`All checks passed!`；Ruff format check：`375 files already formatted`。
- Mypy：`Success: no issues found in 195 source files`。
- 默认全量 pytest（含 80% 覆盖率门）：`696 passed / 102 skipped`，总覆盖率 `86.79%`；跳过项为需显式环境的 PostgreSQL/Docker/平台用例，本轮要求的固定 Fork、双 Harbor Trial 与隔离 PG/MinIO 已由统一入口分别显式执行，不借默认 skip 计为通过。
- 统一入口定向测试：75 passed。
- 旧 ChatGPT Worker 合成回归：16 passed。
- trajectory + 五组判定专项：13 passed。
- 固定 Fork：1 passed / 4 deselected；隔离 PostgreSQL/MinIO：1 passed。

## 7. 偏差、风险与未验证项

- **真实供应商未验证。** “真实上游复核”与“不调用真实供应商”冲突时服从硬边界：本轮使用真实 HTTP/gzip/SSE 传输栈的受控 `.invalid` 假上游，不外推 DeepSeek/Kimi 的实际压缩、usage 或账单语义。
- **真实 ChatGPT 模型未验证。** 旧路由只做无凭据合成回归；没有把假成功写成真实模型通过。
- **Fork 标签偏差。** 固定 Fork 使用其既有两标签所有权模型而非 task+scope；容器由 `--rm` 自动删除，本轮清理器实际删除 ID 为空、remaining 为空。若未来要求所有 evaluator 容器也统一三重标签，需要单独改 Fork 接口，不在本轮偷塞任务 05 常量。
- **判定层负控而非危险活体降级。** 五组“改实现→失败→还原”通过变异证据执行；没有为负控真的开放公网、宿主端口或秘密泄漏。真实正反对照均来自两个活体 Trial。
- **存储网络的 `Internal=false` 是已测选择。** Docker Desktop 在 `internal=true` 网络上即便接受 `-p` 也不会建立端口映射；为让宿主 pytest 访问，使用专属 bridge 并关闭 IP masquerade，端口仅绑定随机 `127.0.0.1`。这不同于 Trial 的双网络安全边界，且容器仅持有合成凭据。
- **磁盘与失败轮次。** 第 04 轮因两份 Codex 解包把 E 盘压到约 630 KiB 而无法并发启动；只删除本任务失败轮次的 `execution` 解包目录与可再生 Mypy 缓存，保留诊断摘要，未删历史证据。最终轮在 06 目录完成。
- **main 的可写宿主绑定。** 固定 Harbor 必须写三个 Trial 专属日志/制品目录；这些绑定范围均在本轮 evidence root，辅助容器无挂载。未声称“绝对无可写宿主挂载”。
