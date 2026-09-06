# 本机 Docker / WSL 运行环境

> 状态：已动态验证
>
> 最后核验：2026-09-06
> 权威范围：本机 Docker/WSL 的实际版本、数据位置、资源上限、磁盘余量和验证状态

## 1. 这份文档解决什么问题

本文件是“这台笔电当前能怎样运行 Docker”的唯一事实源。架构、研究和依赖文档只引用这里，不各自复制一套容易过期的内存与磁盘数值。

这里记录的是**本机事实**，不是全组电脑必须一致的项目版本基线。项目依赖是否正式固定，仍由 [`DEPENDENCIES.md`](../dependencies/DEPENDENCIES.md) 决定。

## 2. 当前环境

| 项目 | 已验证值 | 通俗解释 |
|---|---:|---|
| 物理内存 | 约 15.636 GiB | 整台 Windows 笔电的内存 |
| Docker Desktop | `4.38.0.181591` | Windows 上管理 Docker 的桌面程序 |
| Docker Engine | `27.5.1` | 真正创建和运行容器的后台引擎 |
| WSL | `2.4.12.0`，WSL2 后端 | Docker Linux 容器使用的轻量 Linux 虚拟环境 |
| Windows 系统代理 | 已关闭；FlClash 进程仍监听 `127.0.0.1:7890` | 2026-09-06 `ProxyEnable=0`；需要联网的本轮命令仅使用进程级代理，不改变系统设置 |
| Docker Desktop 代理 | `ProxyHTTPMode=system` | Desktop 读取 Windows 系统代理；Engine 内部显示 `http.docker.internal:3128` |
| Docker CLI 容器代理 | `http://http.docker.internal:3128` | 新的 CLI 创建容器/构建自动注入 HTTP(S) 代理；Harbor 动态 Trial 仍须显式映射 |
| WSL 内存上限 | `10GB` | 所有 WSL2 虚拟机可动态使用的上限，不会启动时立刻占满 |
| Docker 实际可见内存 | `10,429,505,536` bytes，约 `9.713 GiB` | 2026-09-06 Engine 动态探针；10 GB 扣除 WSL/Linux 自身开销后的可用量 |
| Docker 数据目录 | `E:\dockerdata\DockerDesktopWSL\DockerDesktopWSL` | Docker Desktop 实际记录的镜像、容器与卷所在目录 |
| 主数据盘文件 | `...\disk\docker_data.vhdx`，约 21.34 GiB | 一个虚拟 Linux 磁盘文件；不得在 Docker 运行时手工剪切 |
| D 盘可用空间 | 约 29.13 GiB | 迁移完成后的核验值 |
| E 盘可用空间 | `19,594,158,080` bytes，约 18.25 GiB | 2026-09-06 collect-patch 四场景复测后动态值；会随镜像和运行制品变化 |

Docker Desktop 会在用户选择的 `E:\dockerdata\DockerDesktopWSL` 下再创建自己的 `DockerDesktopWSL` 子目录，所以实际路径多一层。这是 Docker Desktop 保存的真实设置，不是重复迁移。

## 3. 生效配置

### 3.1 WSL 资源上限

用户级文件 `C:\Users\YINGYI\.wslconfig` 当前内容为：

```ini
[wsl2]
memory=10GB
```

`memory=10GB` 是上限，不是预留值。Docker、Ubuntu 等 WSL2 工作负载共同受它影响；修改后必须执行 `wsl --shutdown`，再启动 Docker 才会生效。Microsoft 将 `.wslconfig` 定义为 WSL2 的全局配置文件，参见 [WSL 高级配置官方文档](https://learn.microsoft.com/windows/wsl/wsl-config)。

### 3.2 Docker / FlClash 代理通路

2026-09-05 的本机配置采用两级本地代理：

```text
新 Docker CLI 容器
  → http.docker.internal:3128（Docker Desktop 内部代理）
  → 127.0.0.1:7890（Windows 系统代理 / FlClash）
  → 外网目标
```

- Docker Desktop 设置文件已经是系统代理模式，并指向当前 Windows 系统代理；没有修改 Docker Engine `daemon.json`。
- 用户级 Docker CLI 配置只新增 `proxies.default`，HTTP 与 HTTPS 均指向 `http://http.docker.internal:3128`；原有 `auths`、`credsStore`、context、feature 和 plugin 字段保留。
- `NO_PROXY` 当前覆盖 loopback、Docker 的宿主/内部代理名称、`.local` 和 RFC1918 私网。它是应用兼容配置，不是安全边界；不同客户端对 CIDR 的支持并不完全一致。
- FlClash 仍为 `mixed-port: 7890`、`allow-lan: false`、`tun.enable: false`，宿主监听仍是 `127.0.0.1:7890`。本次没有修改 FlClash 配置，也没有创建 7890 防火墙规则。
- Harbor 是动态创建 Trial 的执行后端，不能假设它读取宿主 Docker CLI 配置。正式 `HarborExecutionAdapter` 仍须从本机受控配置把代理变量映射到已登记 Codex `AgentConfig.env`；公开 Job 不得提供任意代理值。

## 4. 迁移和回退纪律

- 数据位置只通过 Docker Desktop 的 `Settings → Resources → Advanced → Disk image location` 修改。
- 不在 Docker 运行时用资源管理器移动 `docker_data.vhdx`，也不直接修改 VHDX 内部内容。
- 如需迁回其他磁盘，仍使用同一 Docker Desktop 设置入口，并在操作前记录镜像、容器和卷数量。
- Docker 官方确认该设置可移动 Linux 磁盘镜像，参见 [Docker Desktop 设置文档](https://docs.docker.com/desktop/settings-and-maintenance/settings/#resources)。

D 盘目前仍有 `D:\dockerdata\DockerDesktopWSL\oslab-ubuntu-noble.tar`，约 0.88 GiB。它不是迁移后的 Docker 主 VHDX，本次没有删除；确认其来源与用途前不得把它当作“迁移残留垃圾”清理。

## 5. 2026-09-03 验证证据

| 检查 | 迁移前 | 迁移后 | 结果 |
|---|---:|---:|---|
| Docker 镜像 | 20 | 20 | 一致 |
| Docker 容器 | 18 | 18 | 一致 |
| Docker 卷 | 15 | 15 | 一致 |
| Docker 可见内存 | 约 7.575 GiB | 约 9.713 GiB | 10 GB 上限已生效 |
| 主 VHDX | D 盘，约 21.36 GiB | E 盘，约 21.34 GiB | 迁移成功 |
| 无网络冒烟测试 | 未执行 | `busybox:latest` 输出 `docker-smoke-ok` | 通过 |

冒烟测试使用本地已有镜像，并显式设置 `--network none`，没有下载新镜像：

```powershell
docker run --rm --network none busybox:latest sh -c 'test -x /bin/sh && echo docker-smoke-ok'
```

## 6. 2026-09-05 容器代理验证证据

| 检查 | 实际结果 | 结论 |
|---|---|---|
| Docker Desktop / Engine | Desktop `running`；Client/Server 均为 `27.5.1` | Engine 恢复并可执行容器 |
| Engine 代理 | `HTTPProxy`/`HTTPSProxy` 均为 `http.docker.internal:3128` | 镜像链路使用 Desktop 内部代理 |
| 内部代理 TCP | BusyBox 连接 `http.docker.internal:3128` 成功 | 运行中容器可达 Desktop 内部代理 |
| 自动环境变量 | 新 BusyBox 自动获得大小写两套 `HTTP_PROXY`、`HTTPS_PROXY`、`NO_PROXY` | Docker CLI 用户级配置已对新容器生效 |
| OpenAI 无凭据 HTTPS | `GET https://api.openai.com/v1/models` 返回 `401 Unauthorized` | DNS、TCP、代理和 TLS 已通；不表示 Codex 已认证 |
| 固定摘要镜像拉取 | `busybox@sha256:32015e...` 返回 `Image is up to date` | Docker Hub 拉取链路可用，且没有移动 `latest` 标签 |
| Docker 代理日志 | 明确记录 OpenAI 与 Docker Registry 经 `127.0.0.1:7890` 的系统 HTTPS 代理转发 | 不是根据 `401` 猜测 FlClash 路径 |
| 校园网 WLAN 地址访问 7890 | 对实测 WLAN 地址 `10.62.158.77:7890` 连接失败 | FlClash 没有向校园网接口监听 |

有一项与原先假设不同：容器连接 `host.docker.internal:7890` 实测成功，即使宿主 `netstat` 只显示 `127.0.0.1:7890`。这是 Docker Desktop 的宿主转发能力，不表示校园网能访问该端口，但意味着不可信 Agent 容器可能绕过 `HTTP_PROXY` 直接使用宿主 FlClash。**因此代理变量只解决连通，不构成闭卷网络隔离。** 正式 Trial 仍必须通过 Docker 网络/代理策略阻断宿主入口和任意直连，只允许平台登记的受控模型访问路径及其必需端点。

本次读取具体 7890 防火墙筛选器时系统返回“拒绝访问”，因此没有把“已完整审计现有防火墙规则”记为通过；本次自身没有创建、修改或删除任何防火墙规则。

第一次更新 Docker CLI JSON 时，使用带空备份参数的 `.NET File.Replace` 被拒绝；原文件 SHA-256 和 JSON 随即复核未变，临时文件数为 0。第二次使用同目录覆盖移动成功，写入后重新解析 JSON 并核对全部原顶层字段和代理字段。

2026-09-06 的 Harbor NOP 探针使用固定任务镜像真实创建 Docker Compose Trial。映射后复测 `runtime/prototype/m0-harbor-nop-20260906-05` 为 `1 passed in 20.56s`；生产有界执行器接真实 Harbor CLI 的复测 `runtime/prototype/m0-harbor-bounded-process-20260906-01` 为 `1 passed in 19.61s`：Verifier 关闭，collect hook 生成并校验 0-byte patch，stdout 未截断，Harbor CLI 在显式 UTF-8 环境正常退出，Trial 对应的 Compose container/network/volume 均无残留。修复后的正常 NOP 回归为 `1 passed in 18.87s`，真实 Windows 父子进程回归为 `1 passed in 1.34s`。这些证据不包含模型、认证或网络白名单，不能推导真实 Codex Trial 已安全可用。

同日的固定摘要镜像 collect-patch 探针使用 `--network none`，对跟踪文件修改、新文件、删除和容器内 Git commit 四种场景得到 `4 passed in 5.91s`。测试直接运行生产 `collect_patch.sh` 并调用宿主生产校验器；运行前后均为 18 个容器、13 个运行和 21 个镜像，测试前缀容器查询无输出。该证据证明四类非空 patch 与测试容器精确清理，不证明 Harbor 外层超时后的 Compose 清理。

外层超时探针使用上游 `nop` 和测试专用阻塞 collect。修复前 `1 failed in 48.51s` 并精确观测到该 project 留下 1 个容器、1 个网络、1 个本地镜像；测试 `finally` 清理后总数恢复。生产 Adapter 随后只按本 Job 落盘 Trial 身份推导的 project label 清理并复核，`runtime/prototype/m0-harbor-timeout-green-20260906-02` 为 `1 passed in 49.47s`，运行前后容器/网络/卷/镜像总数都是 `18/5/15/21`。该证据不包含真实模型或凭据。

## 7. 对 AgentExam 的直接限制

- 单机重型评测并发继续固定为 `1`；增加 WSL 上限不会让笔电变成多机系统。
- Harbor SWE-Gym 模板中的 `8192 MB` 是**单个任务环境上限**，而 `10GB` 是整个 WSL2 的共享上限，两者不是同一个概念。
- Agent 容器、判卷容器、Docker/WSL 开销和宿主进程会竞争内存，因此不能因为 `8192 MB < 10GB` 就断言模板稳定可用。
- 首个真实任务必须实测峰值内存、耗时和磁盘增长，再决定 Harbor Trial 的正式资源模板。
- 2026-09-06 collect-patch 四场景复测后 E 盘可用 `19,594,158,080` bytes（约 18.25 GiB），不适合批量下载完整 SWE-Gym 镜像集合；M0 只能选择 1 道任务起步、必要时扩至 3 道，并控制镜像缓存。
- 固定 Harbor 源码/环境/CLI、候选摘要镜像和 NOP Docker Trial 已核验；固定镜像的无网络探针确认 `/testbed` 位于任务 base commit。仍没有验证容器内 Codex CLI、ChatGPT `auth.json`、Token 刷新或完整闭环。
- Docker CLI 自动代理不等于 Harbor 动态 Trial 自动代理；实现时必须核对 Harbor `AgentConfig.env` 的实际容器结果。
- `host.docker.internal:7890` 可达证明环境变量可以被绕过；闭卷赛道不得把当前配置直接当作端点白名单或防绕过措施。
- 当前最先验证的是 M0 本机 Codex 脚本闭环；Web、PostgreSQL、MinIO、登录和所有者审批属于其后的 M1 平台集成，不应阻塞 M0。
- P2 自研 Agent 只允许 DeepSeek/Kimi，但其真实 Key 不得直接注入被测容器；当前尚未实现或验证受控模型访问路径，不能把一般容器 HTTPS 已通当成该安全要求已满足，也不因此阻塞 Codex MVP。

## 8. 尚未验证

- Harbor 固定环境、CLI `0.22.0`、NOP Job/Trial、正式有界进程 Adapter、四类非空 patch 和外层超时后的精确 Compose 清理已通过；真实 Codex 尚未验证。
- 尚未执行带真实模型的 SWE-Gym Agent Trial。
- 尚未运行固定 SWE-Bench-Fork 的 `run_evaluation`。
- 尚未确定单个 Trial 的安全内存、CPU、磁盘和超时上限。
- 尚未确认 Codex CLI 实际所需的完整域名集合，也未完成只允许登记模型访问且阻断宿主/任意公网直连的网络策略。
- P2 尚未裁决自研 Agent 的受控 DeepSeek/Kimi 访问采用宿主进程还是可信侧车，也未验证单次运行访问能力、预算限制、撤销、清理和“真实 Key 不进入被测容器”；该项不属于 M0/M1 验收门槛。

以上事项完成真实实验前，不得在其他文档中标记为“已跑通”。
