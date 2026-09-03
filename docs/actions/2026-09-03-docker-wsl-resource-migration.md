# 行动文档：迁移 Docker 数据并调整 WSL 内存

## 状态与情况说明

- 状态：已完成。
- 来源请求：用户明确要求把 Docker 数据从 D 盘迁移到 E 盘，并给 Docker 增加可用内存。
- 迁移前 Docker Desktop 数据位置：`D:\dockerdata\DockerDesktopWSL`；其中 `disk\docker_data.vhdx` 约 21.36 GiB。
- 迁移前磁盘余量：D 盘约 7.7 GiB，E 盘约 44.2 GiB，C 盘约 56.1 GiB。
- 迁移前内存事实：物理内存约 15.636 GiB；Docker 报告可用约 7.575 GiB；用户目录中不存在 `.wslconfig`。
- 已完成目标：Docker Desktop 实际数据目录为 `E:\dockerdata\DockerDesktopWSL\DockerDesktopWSL`；WSL/Docker 内存上限为 10 GB，Docker 实测约 9.713 GiB。Harbor 单题资源上限仍需后续实测，不能直接等同于 10 GB。
- 已知风险：迁移会停止 Docker Desktop 和所有 WSL2 发行版；E 盘迁入现有虚拟磁盘后预计只剩约 22 GiB，仍不适合下载完整 SWE-Gym 镜像集合。
- 明确排除：不手工移动正在使用的 VHDX；不删除原数据作为迁移手段；不清理用户镜像、容器或卷；本任务不安装 Harbor、不运行 SWE-Gym 评测、不改尚未完成讨论的业务架构。

## 实施措施

1. 核对 Docker Desktop、WSL 版本及当前支持的官方迁移 interface；只采用能安全关闭并迁移数据的受支持方式。
2. 在修改前记录镜像、容器、卷、Docker 内存、数据位置及源/目标磁盘余量。
3. 验证目标绝对路径位于 `E:\dockerdata\DockerDesktopWSL`，且不存在会被覆盖的未知数据。
4. 干净停止 Docker Desktop 与 WSL2，再执行 Docker 数据位置迁移；不得对运行中的 VHDX 做文件级搬运。
5. 创建用户级 `.wslconfig`，设置 `[wsl2] memory=10GB`；如执行前发现文件已出现，则停止并合并而非覆盖。
6. 重新启动 Docker Desktop，等待 Engine 可用。
7. 核对 Docker 数据位置、可用内存、镜像/容器/卷数量和基础运行能力；发现数据缺失立即停止后续操作并保留原位置用于回退。
8. 更新本地环境权威文档和 Harbor 研究文档中的当前资源指针，记录实际结果、限制与回退方式。

## 需要修改的文件树

```text
E:\9.1实训\
├─ .tmp\docker-resource-migration-wizard.sh
│  # 临时人工操作向导；验证完成后删除，不纳入项目交付物
└─ docs\
   ├─ actions\2026-09-03-docker-wsl-resource-migration.md
   │  # 本次系统迁移的范围、措施、验证证据和实际结果
   ├─ dependencies\DEPENDENCIES.md
   │  # 更新本机 Docker 动态验证状态，并引用环境唯一事实源
   ├─ operations\LOCAL_DOCKER_ENVIRONMENT.md
   │  # 本机 Docker/WSL 数据位置、资源上限、验证和回退的唯一事实源
   └─ research\2026-09-02-harbor-runner-comparison.md
      # 不重复维护当前数值，只改为指向本地环境权威文档

C:\Users\YINGYI\
└─ .wslconfig
   # WSL2 全局资源配置；设置 10 GB 内存上限

E:\dockerdata\DockerDesktopWSL\DockerDesktopWSL\
└─ ...
   # Docker Desktop 管理的实际数据目录；界面在所选目录下自动增加一层目录名
```

设计关系：`LOCAL_DOCKER_ENVIRONMENT.md` 是本机运行环境事实的权威来源；研究和架构文档只引用它。Docker Desktop/WSL 是外部运行时，项目不直接解析或修改其内部 VHDX 内容。

## 修改后自验证方式

1. `docker info --format '{{.MemTotal}}'`：Docker Engine 正常响应，内存接近新的 10 GB WSL 上限，允许存在 Linux/WSL 开销差值。
2. Docker Desktop 设置检查：`CustomWslDistroDir` 指向 E 盘目标位置。
3. 文件检查：E 盘存在 Docker 管理的 VHDX；D 盘旧目录仅在确认迁移成功后由 Docker 自身处理，本任务不主动删除未知残留。
4. 数据一致性：迁移前后镜像、容器和卷计数一致；现有容器元数据仍可列出。
5. 冒烟验证：运行无网络、低资源的官方小型 Docker 镜像命令，退出码为 0；若镜像不存在，不为了冒烟测试下载大型镜像。
6. 配置检查：`.wslconfig` 可解析，且只包含本次确认的资源设置。
7. 文档检查：当前路径、内存、磁盘余量、限制和实际命令输出与文档一致。

## 自验证情况

- 官方接口核对：通过。Docker 官方文档确认应使用 `Settings → Resources → Advanced → Disk image location`，没有手工移动运行中的 VHDX。
- 目标预检：通过。迁移前 `E:\dockerdata\DockerDesktopWSL` 不存在；创建后确认空目录再交由 Docker Desktop 使用。
- 数据路径：通过。`CustomWslDistroDir` 为 `E:\dockerdata\DockerDesktopWSL\DockerDesktopWSL`，主 VHDX 位于 E 盘且约 21.34 GiB。
- 数据一致性：通过。迁移前后均为 20 个镜像、18 个容器、15 个卷。
- 内存配置：通过。`C:\Users\YINGYI\.wslconfig` 仅含 `[wsl2]` 与 `memory=10GB`；完整关闭 WSL 后 Docker 报告 `10,429,509,632` bytes，约 9.713 GiB。
- 冒烟测试：通过。本地已有 `busybox:latest` 在 `--network none` 下输出 `docker-smoke-ok`，退出码为 0。
- 磁盘余量：迁移后 D 盘约 29.13 GiB，E 盘约 22.80 GiB。
- 源目录检查：D 盘只剩 `oslab-ubuntu-noble.tar`，约 0.88 GiB；来源未在本任务确认，因此没有删除。
- 向导验证：`bash -n` 通过并完成实际人工步骤；本机没有安装 `shellcheck`，未把该检查描述为通过。临时向导在任务结束时删除。
- 文档一致性：已建立 `LOCAL_DOCKER_ENVIRONMENT.md` 作为本机环境唯一事实源，并同步 Harbor 研究与依赖文档中的旧状态。
- 文档格式：首次 `git diff --check` 检出依赖文档两行行尾空格，修复后复查通过；没有把首次失败写成通过。
- 最终运行状态：Docker Desktop 进入 `paused`（空闲资源节省）状态，但 Engine 仍能正常响应 `docker info` 并列出全部镜像、容器和卷。

## 实际偏差与遗留风险

- 用户在界面选择 `E:\dockerdata\DockerDesktopWSL` 后，Docker Desktop 自动在其下创建同名子目录；文档采用设置文件报告的实际路径，没有强行改名。
- 第一次执行 `wsl --shutdown` 后 Docker Desktop 外壳仍在但 Engine 为 `stopped`；随后使用受支持的 `docker desktop restart` 恢复，数据计数保持一致。
- 10 GB 是整个 WSL2 的共享上限，不是 Harbor 单个 Trial 的保证内存。真实 SWE-Gym 任务、Harbor 和固定 SWE-Bench-Fork 均尚未运行。
- E 盘仅余约 22.80 GiB，完整数据集或大量实例镜像会很快占满；正式试验必须限制任务数量并监控磁盘增长。
