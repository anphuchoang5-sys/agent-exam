# 行动：Docker Desktop 数据盘迁回 D 盘

## 状态与情况

- 状态：**Completed**。
- 来源：owner 要求由 Codex 直接把 Docker Desktop 数据盘从 E 盘迁回 D 盘。
- 当前源目录：`E:\dockerdata\DockerDesktopWSL\DockerDesktopWSL`，其中 `docker_data.vhdx` 压缩后约 26.76 GiB。
- 目标目录：`D:\dockerdata\DockerDesktopData`；D 盘迁移前空闲约 44.69 GiB。既有 `D:\dockerdata\DockerDesktopWSL\oslab-ubuntu-noble.tar` 不属于目标目录，不覆盖、不删除。
- 当前前置状态：Docker Desktop 进程为 0，Ubuntu 与 `docker-desktop` WSL 实例均为 Stopped。
- 授权边界：复制并切换 Docker Desktop 配置、启动和验证由 Codex 完成；遵守 owner 此前“不直接删除”的要求，源目录在验证后仍作为回退副本保留，由 owner 自行删除。

## 实施措施与完成标准

1. 再次验证源、目标绝对路径和容量；目标必须不存在或为空。
2. 使用跨卷可靠复制把完整 Docker WSL 数据目录复制到新目标，不修改源目录。
3. 比较源、目标两个 VHDX 的长度与 SHA-256；不一致则不切换。
4. 在 Docker 完全停止时备份并只替换 `settings-store.json` 的 `CustomWslDistroDir` 值，解析复核配置。
5. 启动 Docker Desktop，验证 daemon、六道题镜像、正式 PostgreSQL/MinIO 容器、数据卷和项目 HTTP/Worker 状态。
6. 同步本机 Docker 运维文档；不删除旧 E 盘副本。

完成标准：Docker Desktop 从 D 盘 VHDX 启动，迁移前对象仍可见，项目服务恢复；旧 E 盘路径明确保留为待 owner 删除的回退副本。

## 受影响文件树

```text
docs/actions/runtime/
  2026-09-23-docker-data-migration.md  # 本次外部数据盘迁移、验证和回退记录
docs/operations/
  LOCAL_DOCKER_ENVIRONMENT.md          # 当前 Docker 数据根与旧副本状态
```

外部机器状态：

```text
D:\dockerdata\DockerDesktopData\       # 新 Docker Desktop WSL 数据根
%APPDATA%\Docker\settings-store.json   # Docker Desktop 的数据根配置
E:\dockerdata\DockerDesktopWSL\DockerDesktopWSL\  # 验证后保留的旧回退副本
```

不新增业务 Module、Interface、数据库表或项目运行目录。

## 自验证方式

- 源、目标 VHDX 的文件长度与 SHA-256 一致。
- `settings-store.json` 可重新解析，且 `CustomWslDistroDir` 精确等于目标目录。
- `docker info`、`docker system df`、`docker image inspect`、`docker ps -a` 与 volume 清单核对。
- Web `/` 与后端 `/openapi.json` 返回 200，Worker 进程存在；正式 PostgreSQL、MinIO 容器运行。
- `Get-PSDrive D,E` 和新旧 VHDX 路径只读复核；旧 E 盘副本没有被 Codex 删除。

## 自验证情况

- 前置检查通过：源文件合计 26.88 GiB，D 盘空闲 44.69 GiB；Docker 进程为 0，Ubuntu 与 `docker-desktop` 均为 Stopped，目标目录不存在。
- `robocopy` 用无缓冲跨卷复制完成：3 个目录、2 个文件、26.875 GiB，0 skipped、0 mismatch、0 failed；返回码 1 表示成功复制了新文件。
- 两边文件逐字节身份一致：`disk/docker_data.vhdx` 均为 28,737,273,856 bytes、SHA-256 `288FA4C8940D09AA67A5C4ED9E9960FC24FC088E3F48454C31B28EAF4F6C5C12`；`main/ext4.vhdx` 均为 119,537,664 bytes、SHA-256 `A415F16B62CFA087AF8569A52C689AF6DBE692478BA6275BD68AB12CCF019B43`。
- `settings-store.json` 已原子切换为 `D:\dockerdata\DockerDesktopData`，迁移前备份保存为 `%APPDATA%\Docker\settings-store.before-agentexam-docker-move-20260923.json`；重启后 Docker 仍读取新值。
- Docker Server 27.5.1 从新目录启动；六道题镜像 `d086e512d094`、`2baa3c358e98`、`447a2a7dfa95`、`e2ab233d9d8e`、`f6a407a34254`、`b56fd4805c0f` 与当前 Harbor 侧车 `dd1cd5ac1783` 均可 inspect；107 个镜像、22 个容器、16 个卷的清单仍在，Build Cache 为 0 B。
- 项目现有 `Start-AgentExam.ps1` 通过：初始化状态 complete，PostgreSQL 与 MinIO 均 running，MinIO 内置管理探针成功；Web 与后端分别返回 200，Worker 已重新启动，活动 Job 为 0。
- 持久化复核得到 5 个 Job，事件批次 `c9e9a414-ea5c-4317-af85-2e7fb680b743` 仍存在。新 D 盘 VHDX 的修改时间推进到 18:51:55，旧 E 盘副本停在 18:06:24，确认运行写入已切换到 D 盘。
- 迁移后 D/E 盘空闲分别约 19.24/4.46 GiB。旧 `E:\dockerdata\DockerDesktopWSL\DockerDesktopWSL` 仍完整保留，Codex 没有删除；owner 删除该回退副本后，E 盘才会释放其约 26.76 GiB 物理占用。
