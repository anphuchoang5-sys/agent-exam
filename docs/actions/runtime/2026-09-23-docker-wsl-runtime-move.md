# Docker Desktop WSL 启动盘补充迁移

## 状态与情况说明

状态：Completed（2026-09-23）。

来源请求：owner 在删除 `E:\dockerdata\DockerDesktopWSL` 时收到“文件夹正在使用”，要求查明原因。只读核对确认 Docker 的 26.8 GiB 数据盘已在 D 盘，但 WSL 注册表中的 `docker-desktop` `BasePath` 仍指向 `E:\dockerdata\DockerDesktopWSL\DockerDesktopWSL\main`；其中 `ext4.vhdx` 仍被 WSL 使用，因此旧目录不能删除。

本轮范围是把剩余的 `docker-desktop` WSL 启动盘迁到既定 D 盘数据根，恢复 Docker 与 AgentExam，并修正当前运维文档。此前已结束的迁移行动保持历史只读。遵守 owner 删除边界：不调用删除命令；D 盘旧快照改名保留，E 盘迁移后遗留的空目录由 owner 自行删除。

## 实施措施

1. 核对 WSL 注册路径、旧/新 VHDX、Docker 配置和项目运行状态。
2. 在 Docker、`docker-desktop` 和项目均停止且活动 Job 为 0 时，用本机 WSL 2.7.13 的官方 `wsl --manage docker-desktop --move` 命令迁移启动盘。
3. 启动 Docker，核对 WSL 注册位置、Docker Engine、镜像/容器及 D 盘 VHDX；恢复 AgentExam PostgreSQL、MinIO、后端、Web 和已授权 Worker。
4. 更新当前运维文档，记录两阶段迁移后的真实状态及 owner 可自行清理的精确路径。

完成标准：`docker-desktop` 的 `BasePath` 指向 D 盘；Docker Engine 能列出原镜像和容器；AgentExam 存储、后端、Web 与 Worker 恢复；E 盘旧路径只剩空目录；文档不再把该目录描述为 26.76 GiB 回退副本。

## 实际修改的文件树与职责

```text
docs/actions/runtime/2026-09-23-docker-wsl-runtime-move.md # 本轮原因、操作和验证证据
docs/operations/LOCAL_DOCKER_ENVIRONMENT.md                # Docker Desktop 当前磁盘位置和清理边界
```

不新增业务 Module、Interface、数据库表或设计模式；仅修正 owner 主机的 Docker/WSL 运行位置与当前运维事实。

## 自验证方式

- 读取 `HKCU:\Software\Microsoft\Windows\CurrentVersion\Lxss`，确认 `docker-desktop` `BasePath` 为 D 盘目标。
- `docker version`、`docker info` 和 `docker ps` 核对 Engine、镜像和容器。
- 运行 `infra/local/Start-AgentExam.ps1`，检查初始化、PostgreSQL、MinIO 和活动 Job。
- 请求 `http://127.0.0.1:8000/openapi.json` 与 `http://127.0.0.1:3000/`，并核对 Worker 进程。
- 枚举 E 盘旧目录和 D 盘目标/备份，确认 E 盘旧路径无文件；运行 `git diff --check`。

## 自验证情况

- 根因确认：迁移前注册表中 `docker-desktop` 的 `BasePath` 为 `\\?\E:\dockerdata\DockerDesktopWSL\DockerDesktopWSL\main`，旧 `main\ext4.vhdx` 的修改时间仍在推进；Docker 设置中的 `CustomWslDistroDir` 已是 D 盘。这证明数据盘切换与 WSL 发行版注册是两个状态，Windows 的占用提示来自仍登记在 E 盘的启动盘。
- 迁移前 `wsl --list --verbose` 显示 Ubuntu 与 `docker-desktop` 均已停止，项目无监听端口；`Start-AgentExam.ps1` 在恢复存储后返回活动 Job 0。D 盘已有旧 `main` 快照先改名为 `main-before-official-wsl-move-20260923`，随后官方 `wsl --manage docker-desktop --move D:\dockerdata\DockerDesktopData\main` 成功，过程中未调用删除命令。
- 迁移后 WSL 注册位置为 `D:\dockerdata\DockerDesktopData\main`。D 盘当前启动盘 `ext4.vhdx` 为 `120,586,240` bytes，数据盘为 `28,773,974,016` bytes，启动后修改时间继续更新；E 盘 `E:\dockerdata\DockerDesktopWSL` 递归文件数为 0，只剩空目录。
- Docker Desktop 4.38.0 / Engine 27.5.1 响应正常，保留 107 个镜像和 22 个容器；AgentExam 的 PostgreSQL 与 MinIO 两个容器运行。生命周期状态为初始化 `complete`、两项存储 `running`、活动 Job 0、Worker 停止标记未设置。
- 后端 `http://127.0.0.1:8000/openapi.json` 和 Web `http://127.0.0.1:3000/` 均返回 200；进程核对显示当前后端、Web 和 `agentexam-owner` Worker 运行。恢复 Web 的第二次启动尝试收到 `EADDRINUSE` 并自行退出，因为第一份 Web 已在 3000 端口成功恢复；没有留下第二个监听实例。
- 迁移后 D/E 空闲空间分别约 19.13/31.37 GiB。D 盘的迁移前启动盘快照约 114 MiB，按 owner 删除边界保留并列入可手动清理清单。项目代码和数据库 schema 未修改；仅同步本行动与当前运维文档。
