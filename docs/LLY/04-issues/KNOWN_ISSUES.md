# 本机开发环境问题记录

> 只记录**本机环境**问题。产品缺陷、业务流程问题和项目级风险请记录到对应权威文档或 `docs/actions/`，不要放这里。

## ISSUE-01：本机 Tailscale 虚拟网卡无法创建（未解决）

**状态**：未解决　**影响**：本机无法连接团队共享 PostgreSQL（只影响"看共享库数据"，不影响代码开发与测试）

### 现象

- 安装 Tailscale 1.102.4 成功（MSI 报告 Installation completed successfully），服务 `Tailscale` 处于 Running。
- 但界面点 "Log in" 无任何反应；`tailscale status` / `tailscale login` 均无输出或报 `503 Service Unavailable: no backend`。
- 设备管理器中的 `Tailscale Tunnel`（`SWD\WINTUN\{37217669-42DA-4657-A55B-0D995D328250}`）长期处于 **Error** 状态；系统里没有生成 Tailscale 网络适配器。

### 直接证据

- Tailscale 服务日志持续循环报错：

  ```text
  Using existing driver 0.14
  Creating adapter
  Timed out waiting for device query: 等待的操作过时。(Code 0x00000102)
  Failed to setup adapter (problem code: 0x38, ntstatus: 0x0): 设备未就绪。(Code 0x000010DF)
  ```

- 设备属性：`ProblemCode = 56`（0x38）、`ConfigFlags = 524288`（0x80000，`CONFIGFLAG_FAILEDINSTALL`）、`DriverInfPath = oem528.inf`、`Service = wintun`。
- `Get-PnpDevice` 的 `Problem` 字段显示 `CM_PROB_NEED_CLASS_CONFIG`。
- 同一时刻 **`Sangfor aTrust VNIC`（`ROOT\NET\0000`，服务 `SdpVnic`）也处于 Error** —— 两块不同的虚拟网卡都装不上，说明问题在网络设备安装层，而非 Tailscale 特有。

### 已排除（均经实际检查）

| 嫌疑 | 排除依据 |
|---|---|
| 未真正重启 | 已确认 `LastBootUpTime` 更新、服务与进程 PID 全部刷新 |
| Fast Startup 导致假重启 | 首次确为假重启，改用真正重启后问题依旧 |
| 360 安全卫士拦截 | 已完整卸载（10 个内核驱动、驱动文件、服务、进程均清零），问题依旧 |
| Clash Verge / FlClash 抢占 Wintun | 两个服务已停止，问题依旧 |
| 设备安装类系统服务被禁用 | `DeviceInstall`、`PlugPlay`、`DcomLaunch`、`NetSetupSvc` 均 Running/Automatic |
| 网络类过滤驱动注册表干扰 | 类级 `UpperFilters` / `LowerFilters` / `FilterList` 均为空 |
| 类安装器缺失 | `netcfgx.dll` 存在 |
| 内存完整性（HVCI）拦截驱动 | 未配置/未启用 |
| 驱动文件缺失 | `C:\Windows\System32\drivers\wintun.sys` 存在（0.14，文件时间 2025-11-12） |

### 关键观察

- `wintun.sys` 的文件时间是 **2025-11-12**，早于本次 Tailscale 安装（2026-09-18），说明这份 Wintun 驱动是**此前被其他软件（网易UU加速器或 Clash Verge）安装**的，Tailscale 只是复用（日志中的 "Using existing driver 0.14"）。
- 磁盘上存在三份同版本（0.14.1）的 `wintun.dll`：Tailscale、网易UU加速器（两处）。

### 尚未尝试的下一步（按风险从低到高）

1. **删除 Wintun 驱动包后重建**：`Stop-Service Tailscale` → `pnputil /remove-device <实例ID>` → `pnputil /delete-driver oem528.inf /uninstall /force` → 重启（Tailscale 会用自带 wintun.dll 重新安装驱动）。
2. 卸载 **Npcap**（Wireshark 抓包驱动，绑定在所有网卡上的轻型筛选器）。
3. 临时停用 **aTrust**（深信服 VPN，其网络过滤驱动 `SdpNetFilter0.sys` 常驻；注意它可能关系到校园网访问）。
4. 重置网络适配器：`netcfg -d` + 重启（执行前先建系统还原点）。

### 绕过方案（当前采用）

不修 Windows 网络栈，改为在本机建立**独立的本地测试数据库**用于开发与测试（见[本地环境文档](../02-environment/LOCAL_SETUP.md)）。理由：E 模块的代码工作与真实执行链都不依赖共享库；真实跑题在组长的机器上完成。

### 备注

这是**本机环境问题，不是项目缺陷**。同组其他成员不需要因此做任何改动。

## ISSUE-02：本机开发环境完全缺失（已解决）

**状态**：已解决（2026-09-18）

- 现象：`apps/backend` 无 `.venv`、`apps/web` 无 `node_modules`、Docker 未运行、`D:\AgentExamData` 不存在。
- 原因：本机是新克隆；`framework/`、`runtime/` 等运行环境不进 Git。
- 处理：已建本地 PostgreSQL 15（55432）、专属测试库与 schema（11 张表）、Python 3.13 环境与依赖，静态检查与默认回归基线已取得。步骤与结果见[本地环境文档](../02-environment/LOCAL_SETUP.md)。
- 遗留：前端依赖未安装；MinIO 与 Docker 未配置。

## ISSUE-03：与项目无关的本机设备故障（仅记录）

**状态**：不处理

- `ROOT\HIDCLASS\0000` 故障码 28（驱动未安装）。与本项目无关，仅记录以免后续排查时误判。

## ISSUE-04：默认回归在新克隆上有 2 项契约测试失败（环境依赖，不处理）

**状态**：已知，不处理　**影响**：默认回归不是全绿，需人工区分这 2 项

### 现象

在没有 `framework/` 的全新克隆上运行默认回归，得到 `386 passed, 82 skipped, 2 failed`，失败项都在 `tests/contract/test_execution_network.py`：

| 测试 | 失败原因 |
|---|---|
| `test_bootstrap_imports_fixed_harbor_not_the_adjacent_adapter_package` | 要执行 `framework/harbor/.venv/Scripts/python.exe`，路径不存在 |
| `test_sidecar_exports_traceable_dns_adaptation_and_never_overwrites` | 要执行 `git -C framework/harbor rev-parse HEAD`，返回 128 |

### 原因

两项都依赖 `framework/harbor`——被 `.gitignore` 排除的**固定 Harbor 上游源码**，只存在于组长的机器上。文档明确要求不要无理由重建该环境（Windows 首次编译约 275 分钟）。

### 结论

**这是环境依赖导致的失败，不是产品缺陷，也不由本机任何改动引入。** 判断方法：在组长机器上（存在 `framework/`）应能通过；在本机属预期失败。

### 建议

不要为了让它变绿而修改这两个测试。若确实需要在本机跑，唯一正确做法是按[依赖总表](../../dependencies/DEPENDENCIES.md)固定版本恢复 `framework/`，这需要单独授权与时间预算。

**2026-09-22 当前补充**：主仓库 `E:/9.1agent_exam/framework/harbor` 已存在且为固定提交 `6af8d6e31eced13b93849cdf80feeadf24603d15`、受控文件干净、虚拟环境可用；独立 `runtime/lly-dev-verify` worktree 的同名路径默认不存在。S9 初次默认全量为 `620 passed / 107 skipped / 2 failed`，失败均来自该缺失路径。用户明确允许后，临时目录联接复用固定 Harbor，定向两项 `2 passed`、默认全量 `624 passed / 105 skipped`，证明这两项是环境依赖；补测后精确移除联接，主框架保持原提交且干净。当前 worktree 再次没有该路径，未来要复测这两项仍需恢复同样的受控前提；见[S9 行动](../../actions/2026-09-22-task05-s9-run-bindings.md)。

## ISSUE-05：负责人 worktree 的 PostgreSQL 测试 DSN 指向既有服务（已解决）

**状态**：已解决（2026-09-22）　**影响**：曾使 S9 的显式 PG 全量未测到数据库断言；已按“在已有专属实例的机器上执行并回传证据”这条路径关闭。

**解决（2026-09-22）**：该全量按计划本就在本机（E 的开发机）的专属库上执行——本机 `127.0.0.1:55432` 是可用的便携专属实例（回环 trust、无需密码），实测跑通 **676 passed / 51 skipped / 2 failed**（2 项失败为缺 `framework/harbor` 的 ISSUE-04，与本问题无关）；负责人机器上那 62 个连接期 error 在同一批用例上全部进入数据库断言并通过。**结论：负责人机器不运行 PG 全量（那里的 55432 是既有 `agentexam-local` 服务，不得建/删临时库）；PG 相关回归一律在本机跑。** 证据见[本机补测行动](../../actions/2026-09-22-task05-s9-pg-acceptance-local.md)。以下为定位过程（保留原样）。

- 2026-09-22 初次实测：端口 `127.0.0.1:55432` 可连接，但按[本机环境文档](../02-environment/LOCAL_SETUP.md)历史的无密码专属测试 DSN 开启 `AGENTEXAM_RUN_IDENTITY_POSTGRES=1`，夹具收到 `fe_sendauth: no password supplied`。全量结果 `620 passed / 45 skipped / 2 failed / 62 errors`；62 个 error 均在连接时出现，没有进入建临时库或数据库断言。
- 同日补查：用户在可见 PowerShell 为专属测试角色隐藏输入密码，预检实际为 `auth_exit=1 / test_exit=not-run / cleanup=ok`，服务器返回 `password authentication failed for user "agentexam_identity_test"`；脚本未运行全量。随后只读确认 `127.0.0.1:55432` 由 Docker Desktop 转发给既有 Compose 项目 `agentexam-local` 的 `agentexam-local-postgres-1`，**不是**文档所述便携专属测试实例；此机器上 `D:/pgsql` 与本机 `postgres.exe` 进程均不存在。密码拒绝不能证明输入有误，旧“仅认证方式漂移”的假设已被现场证据取代。未读取凭据、改配置或动既有服务。
- 解决方案：不要再对 `agentexam-local` 重试密码，也不要在该既有持久化服务上运行会创建/删除临时数据库的测试。负责人确认后，在**隔离的专属 PostgreSQL 实例**上提供单独端口和 `agentexam_identity_test` 角色/库（角色需 `CREATEDB`），或在已有专属实例的机器上执行 PG 全量并回传证据；不改既有 Docker/数据库服务。当前环境不足以签收 S9 的 PG 全量，S10/S11 暂停。
