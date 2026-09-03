# 本机 Docker / WSL 运行环境

> 状态：已动态验证
>
> 最后核验：2026-09-03
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
| WSL 内存上限 | `10GB` | 所有 WSL2 虚拟机可动态使用的上限，不会启动时立刻占满 |
| Docker 实际可见内存 | `10,429,509,632` bytes，约 `9.713 GiB` | 10 GB 扣除 WSL/Linux 自身开销后的可用量 |
| Docker 数据目录 | `E:\dockerdata\DockerDesktopWSL\DockerDesktopWSL` | Docker Desktop 实际记录的镜像、容器与卷所在目录 |
| 主数据盘文件 | `...\disk\docker_data.vhdx`，约 21.34 GiB | 一个虚拟 Linux 磁盘文件；不得在 Docker 运行时手工剪切 |
| D 盘可用空间 | 约 29.13 GiB | 迁移完成后的核验值 |
| E 盘可用空间 | 约 22.80 GiB | 迁移完成后的核验值 |

Docker Desktop 会在用户选择的 `E:\dockerdata\DockerDesktopWSL` 下再创建自己的 `DockerDesktopWSL` 子目录，所以实际路径多一层。这是 Docker Desktop 保存的真实设置，不是重复迁移。

## 3. 生效配置

用户级文件 `C:\Users\YINGYI\.wslconfig` 当前内容为：

```ini
[wsl2]
memory=10GB
```

`memory=10GB` 是上限，不是预留值。Docker、Ubuntu 等 WSL2 工作负载共同受它影响；修改后必须执行 `wsl --shutdown`，再启动 Docker 才会生效。Microsoft 将 `.wslconfig` 定义为 WSL2 的全局配置文件，参见 [WSL 高级配置官方文档](https://learn.microsoft.com/windows/wsl/wsl-config)。

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

## 6. 对 AgentExam 的直接限制

- 单机重型评测并发继续固定为 `1`；增加 WSL 上限不会让笔电变成多机系统。
- Harbor SWE-Gym 模板中的 `8192 MB` 是**单个任务环境上限**，而 `10GB` 是整个 WSL2 的共享上限，两者不是同一个概念。
- Agent 容器、判卷容器、Docker/WSL 开销和宿主进程会竞争内存，因此不能因为 `8192 MB < 10GB` 就断言模板稳定可用。
- 首个真实任务必须实测峰值内存、耗时和磁盘增长，再决定 Harbor Trial 的正式资源模板。
- E 盘仅余约 22.80 GiB，不适合批量下载完整 SWE-Gym 镜像集合；首版只能选择少量任务并控制镜像缓存。

## 7. 尚未验证

- 尚未安装或运行 Harbor。
- 尚未执行真实 SWE-Gym Agent Trial。
- 尚未运行固定 SWE-Bench-Fork 的 `run_evaluation`。
- 尚未确定单个 Trial 的安全内存、CPU、磁盘和超时上限。

以上事项完成真实实验前，不得在其他文档中标记为“已跑通”。
