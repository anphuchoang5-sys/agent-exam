# 项目依赖唯一事实源

> 文档状态：持续维护；M0 三项上游身份、固定数据/镜像、Harbor 环境、后端锁文件、NOP Trial、四类非空 patch 与超时清理已核验，Codex/Fork 依赖仍待验证
>
> 最后更新：2026-09-06；上游、Harbor 与 CLI 最后核验：2026-09-06
> 权威范围：依赖身份、来源、固定版本、是否进入主仓库、获取/恢复方式和验证状态

## 1. 文档边界

“固定版本”是指团队明确使用一个不可变的版本标识，例如完整 Git 提交哈希（commit SHA）或容器镜像摘要（digest），从而避免上游更新后结果悄悄变化。

本文件是以下事实的唯一维护位置：

- 项目直接依赖什么；
- 依赖来自哪里、固定到哪个版本；
- 依赖是否进入 AgentExam 主仓库；
- 新成员如何恢复相同依赖并核验；
- 哪些依赖已经验证，哪些仍待确认。

字段、命令行参数、输入输出结构和 Adapter（把不同外部工具转换成项目统一接口的适配层）映射由 [`FRAMEWORK_INTERFACES.md`](../interfaces/FRAMEWORK_INTERFACES.md) 维护。本文件不重复维护接口细节。

## 2. 当前依赖总表

| 依赖 | 项目用途 | 固定版本 | 是否进入主仓库 | 当前状态 |
|---|---|---|---:|---|
| SWE-Gym | 任务数据、模型与复现实验材料的上游来源 | `b681068ca20628c6987b7416cc4cf03f06b77ba5` | 否 | 源码身份、许可证和上游制品入口已核验；M0 固定 Lite revision/split/单题已下载并通过内容校验 |
| SWE-Bench-Fork | SWE-Gym 环境常量、Docker 环境构建和评测 Harness（自动执行测试并判定补丁是否解决任务的程序） | `242429c188fcfd06aad13fce9a54d450470bf0ac` | 否 | 源码身份、许可证和安装入口已核验；固定单题摘要镜像已拉取并核验仓库快照，但 Fork Harness 尚未安装或运行 |
| Harbor | Execution Backend（执行后端）：把一个平台 Job 展开并运行成多个 Agent Trial，管理 Agent、环境、资源/网络策略和轨迹 | `6af8d6e31eced13b93849cdf80feeadf24603d15` | 否 | 固定源码和隔离环境已恢复，CLI `0.22.0` 可用；真实类型/Task 契约与 NOP Docker Trial/结果映射通过，Codex Trial 未运行 |
| Python 运行时 | 后端及 SWE-Bench-Fork 运行时 | M0 后端 `>=3.13,<3.14`；Fork 基线待验证 | 不适用 | `apps/backend/pyproject.toml` 与 `uv.lock` 已固定并安装 Python 3.13 项目环境；Fork 独立运行依赖尚未锁定 |
| FastAPI | 后端 HTTP 交付层 | 待确认 | 后续由项目包清单锁定 | 已确认采用；精确版本未固定 |
| Node.js 运行时 | Web 前端构建/运行 | 待确认 | 不适用 | 已确认采用；版本未选定 |
| Next.js | Web 框架 | `15.x`，精确版本待确认 | 后续由前端包清单锁定 | 已确认采用 Next.js 15 |
| React | Web 视图框架 | `19.x`，精确版本待确认 | 后续由前端包清单锁定 | 已确认采用 React 19 |
| Docker Engine / Docker Desktop / Compose | 隔离并运行评测环境 | 项目基线待确认；本机 Desktop `4.38.0.181591`、Engine `27.5.1` | 不适用 | 本机 Windows + WSL2、无网络冒烟和 Harbor NOP Compose Trial 已验证；SWE-Bench-Fork 集成未验证，详见 [`LOCAL_DOCKER_ENVIRONMENT.md`](../operations/LOCAL_DOCKER_ENVIRONMENT.md) |
| PostgreSQL | 结构化业务数据存储与 MVP 平台 Evaluation Job 队列 | 待确认 | 不适用 | 已确认采用；M0 本机脚本原型不依赖；精确版本未固定 |
| MinIO | 对象存储，即保存 patch、日志等文件制品 | 待确认 | 不适用 | 已确认采用；精确版本未固定 |
| Codex CLI | M0 本机真实原型与 M1 平台 MVP Agent | 待确认 | 否 | 已确认首个原型使用 Harbor 内置 Codex Adapter，认证政策为评测机所有者的 ChatGPT Pro `auth.json`（见 [`CODEX_AUTHENTICATION.md`](../interfaces/CODEX_AUTHENTICATION.md)）；2026-09-06 宿主动态探针为 `codex-cli 0.153.0`，但项目固定版本、容器模型、端点和运行兼容性仍待确认或实测 |
| Aider CLI | Codex MVP 之后的已知 Agent | 待确认 | 否 | 已确认在 Codex 平台闭环后接入；尚未安装或固定版本，不阻塞 MVP |
| Claude Code CLI | Codex MVP 之后的已知 Agent | 待确认 | 否 | 已确认在 Codex 平台闭环后接入；尚未安装或固定版本，不阻塞 MVP |
| 本地自研 Agent | P2 扩展 Agent | 待实现 | 是，由提交者固定 Git commit 提交，审核后登记 | 只保留扩展接缝；P2 首版只支持 Python 和固定进程 Interface，完整 manifest、Python 版本、依赖锁格式与 Harbor 包装不阻塞 MVP |
| DeepSeek / Kimi 模型接口 | P2 自研 Agent 唯一允许的外部模型提供方 | 精确模型与接口版本待确认 | 否 | 提供方范围和本机 Key 所有权已确认；Key 不进入被测 Agent，外部协议、受控访问部署和真实调用留到 P2 核验，见 [`CODEX_AUTHENTICATION.md`](../interfaces/CODEX_AUTHENTICATION.md) |

“待确认”不等于推荐使用最新版；在版本被确认并写入本文件前，不得把本机偶然安装的版本当成团队基线。

依赖恢复与验证必须服从顺序：M0 只恢复 Harbor、SWE-Gym Lite 单题所需数据/镜像、SWE-Bench-Fork 和 Codex；M1 再加入 Web、PostgreSQL、MinIO；M1 通过后才处理 Aider/Claude Code；自研 Agent 与 DeepSeek/Kimi 为 P2。不得因为 P2 依赖未定而推迟 Codex 闭环。

## 3. 第三方框架源码策略

`framework/` 是本机用于阅读和运行第三方上游源码的工作区，不是 AgentExam 自有源码的一部分。团队已确认：

1. `framework/swe-gym/`、`framework/swe-bench-fork/` 和计划恢复的 `framework/harbor/` 不上传到 AgentExam 主仓库；
2. 不把它们作为普通目录、复制代码或 Git Submodule（主仓库只记录另一个仓库提交的机制）纳入主仓库；
3. 主仓库只提交本文件记录的来源、固定提交与恢复方法；
4. 后续可以提供恢复脚本，但本次仅提供人工命令，没有创建脚本；
5. 在主仓库批量暂存文件前，应人工确认 `framework/` 未被纳入；当前 `.gitignore` 已忽略整个 `framework/`，后续还应增加自动检查。

## 4. SWE-Gym

### 4.1 身份与来源

| 项目 | 已核验值 |
|---|---|
| 官方仓库 | <https://github.com/SWE-Gym/SWE-Gym.git> |
| 本地恢复路径 | `framework/swe-gym` |
| 固定提交 | `b681068ca20628c6987b7416cc4cf03f06b77ba5` |
| 核验时分支 | `main`，跟踪 `origin/main` |
| 核验时工作树 | 干净；无已修改或已暂存文件 |
| 许可证 | Apache License 2.0 |
| 固定提交入口 | <https://github.com/SWE-Gym/SWE-Gym/tree/b681068ca20628c6987b7416cc4cf03f06b77ba5> |

许可证结论来自固定提交中的 [`LICENSE`](https://github.com/SWE-Gym/SWE-Gym/blob/b681068ca20628c6987b7416cc4cf03f06b77ba5/LICENSE)。

### 4.2 安装、数据与镜像入口

- 该固定提交的仓库根目录没有 `pyproject.toml`、`setup.py`、`setup.cfg`、`requirements.txt`、`environment.yml`、`Pipfile`、`poetry.lock` 或 `package.json`，因此不能把 SWE-Gym 本身描述成一个具有统一安装入口的软件包。
- 官方 [`README.md`](https://github.com/SWE-Gym/SWE-Gym/blob/b681068ca20628c6987b7416cc4cf03f06b77ba5/README.md) 将数据与模型入口指向 Hugging Face 的 [`SWE-Gym`](https://huggingface.co/SWE-Gym) 组织页，并把环境常量指向 SWE-Bench-Fork。
- 同一 README 声明实例预构建镜像位于 Docker Hub 的 `xingyaoww/sweb.eval.x86_64` 前缀下。
- 团队已确认首个真实原型使用 `SWE-Gym/SWE-Gym-Lite` 的 1～3 道任务。M0 当前固定 revision `61231f2c90b18985b42a1419738a240085a15107`、`train` split 和候选 `python__mypy-15413`；固定 Parquet 大小为 `931,193` bytes，SHA-256 为 `f3a7cd934e8cc523b6053298d0abb2c82fd7db2b83f9f2ccba5944545aaa4eb1`。
- 当前候选镜像固定为 `xingyaoww/sweb.eval.x86_64.python_s_mypy-15413@sha256:f069dfc74592d438ad870bbc6dfb369bff1b125d21237ead49190b414f5f3456`，已拉取并确认 `/testbed` HEAD 为任务 base commit `e7b917ec7532206b996542570f4b68a33c3ff771`。这只证明镜像身份，不证明 Harness 或 Codex Trial 通过。
- OpenHands 和 MoatlessTools 出现在上游复现实验说明中；它们当前不是 AgentExam 已固定的直接依赖，不能仅凭上游示例自动纳入项目。

当前验证状态：固定源码、README、许可证、Lite 数据 revision/split/内容哈希、候选字段与固定摘要镜像均已核验；项目 Task Adapter 的公开/隐藏字段隔离和真实 Parquet 契约测试已通过；该任务镜像已用于 Harbor NOP Trial。没有运行真实 Agent 或 Harness。

## 5. SWE-Bench-Fork

### 5.1 身份与来源

| 项目 | 已核验值 |
|---|---|
| 官方仓库 | <https://github.com/SWE-Gym/SWE-Bench-Fork.git> |
| 本地恢复路径 | `framework/swe-bench-fork` |
| 固定提交 | `242429c188fcfd06aad13fce9a54d450470bf0ac` |
| 包内版本 | `2.0.13` |
| 核验时分支 | `main`，跟踪 `origin/main` |
| 核验时工作树 | 干净；无已修改或已暂存文件 |
| 许可证 | MIT License |
| 固定提交入口 | <https://github.com/SWE-Gym/SWE-Bench-Fork/tree/242429c188fcfd06aad13fce9a54d450470bf0ac> |

完整提交哈希是项目的权威固定版本；包内版本 `2.0.13` 只作为辅助身份。许可证结论来自固定提交中的 [`LICENSE`](https://github.com/SWE-Gym/SWE-Bench-Fork/blob/242429c188fcfd06aad13fce9a54d450470bf0ac/LICENSE)。

两个上游仓库的许可证只约束各自上游内容，不会自动替 AgentExam 选择许可证；AgentExam 主仓库是否开源、采用哪种许可证仍需团队另行确认。

### 5.2 安装入口与直接 Python 依赖

固定提交提供 `pyproject.toml`、`setup.py` 和 `setup.cfg`，源码安装入口为：

```powershell
python -m pip install -e .
```

该命令只记录上游入口，本次没有执行。上游 [`setup.py`](https://github.com/SWE-Gym/SWE-Bench-Fork/blob/242429c188fcfd06aad13fce9a54d450470bf0ac/setup.py) 声明：

- Python 要求：`>=3.8`；
- 核心直接依赖：`beautifulsoup4`、`chardet`、`datasets`、`docker`、`ghapi`、`GitPython`、`pre-commit`、`python-dotenv`、`requests`、`rich`、`unidiff`、`tqdm`；
- `inference` 可选依赖：`tiktoken`、`openai`、`anthropic`、`transformers`、`peft`、`sentencepiece`、`protobuf`、`torch`、`flash_attn`、`triton`、`jedi`、`tenacity`。

这些依赖在 `setup.py` 中没有固定精确版本，仓库也没有锁文件，所以单独运行安装命令不能保证不同日期得到完全相同的环境。项目采用哪些依赖、固定到哪些版本，仍需后续生成项目自己的锁定清单后确认。

### 5.3 数据与镜像来源

- Harness 支持 Hugging Face 数据集名称以及本地 JSON/JSONL；具体字段和 CLI 规则见 [`FRAMEWORK_INTERFACES.md`](../interfaces/FRAMEWORK_INTERFACES.md)。
- 上游 CLI 默认数据集是 `princeton-nlp/SWE-bench_Lite`、默认 split 是 `test`。这是上游默认值，不是 AgentExam 已确认的 SWE-Gym 数据选择；项目调用时必须显式指定后续确认的数据集与 split。
- 固定源码把本地镜像命名为 `sweb.base.<arch>:latest`、`sweb.env.<arch>.<hash>:latest` 和 `sweb.eval.<arch>.<instance_id>:latest`。
- 基础 Dockerfile 从 `ubuntu:22.04` 构建并下载 Miniconda 安装器；两者都未按镜像 digest 或文件校验和固定。
- 对固定提交执行源码搜索，没有发现 `docker pull` 或 Docker SDK `images.pull` 调用。也就是说，SWE-Gym README 提到的 `xingyaoww/...` 预构建镜像不是当前 Harness 自动恢复流程；默认行为是在本机缺少镜像时按源码构建。

当前验证状态：安装声明、包内版本、数据加载入口、镜像命名和本地构建路径已经静态核验；该 Fork 尚未安装，没有构建或运行其评测镜像，也没有执行评测。本机 Docker daemon 的独立冒烟验证记录在 [`LOCAL_DOCKER_ENVIRONMENT.md`](../operations/LOCAL_DOCKER_ENVIRONMENT.md)，不能据此宣称 Harness 已跑通。

## 6. Harbor

### 6.1 身份与来源

| 项目 | 已核验值 |
|---|---|
| 官方仓库 | <https://github.com/harbor-framework/harbor.git> |
| 本地恢复路径 | `framework/harbor` |
| 固定提交 | `6af8d6e31eced13b93849cdf80feeadf24603d15` |
| 包内版本 | `0.22.0` |
| Python 要求 | `>=3.12` |
| 许可证 | Apache License 2.0 |
| 固定提交入口 | <https://github.com/harbor-framework/harbor/tree/6af8d6e31eced13b93849cdf80feeadf24603d15> |

完整提交哈希是项目的权威固定版本；包内版本 `0.22.0` 只作为辅助身份。固定源码和按上游 `uv.lock` 的隔离环境已在本机恢复，CLI 可启动；真实 NOP Docker Trial 已通过，但不等于 Codex Trial 或完整 M0 已跑通。

### 6.2 在项目中的边界

- Harbor 是已确认采用、但仍须通过原型验收的 Execution Backend，不是平台数据库、课程管理后端或最终判卷器。
- PostgreSQL 继续管理平台 Evaluation Job 队列；一个平台 Job 映射为一个 Harbor Job。
- Harbor 按 Agent × Task × Attempt 展开 Trial；首版 `n_attempts=1`、`n_concurrent_trials=1`。
- 固定 SWE-Bench-Fork 的 `swebench.harness.run_evaluation` 仍是唯一确定性最终判卷入口，Harbor Reward 不能覆盖其结论。
- Harbor 的精确接口、转换与退出门槛由 [`HARBOR_EXECUTION.md`](../interfaces/HARBOR_EXECUTION.md) 维护；采用决定见 [`ADR-0001`](../adr/0001-use-harbor-as-execution-backend.md)。

当前验证状态：固定源码/环境已恢复；配置模型、Job/Trial 展开、结果模型、制品顺序和 Verifier 关闭能力已做源码核验，真实 `JobConfig`/`Task` 契约测试通过。NOP Docker Trial 已实际启动并完成，collect hook 生成的空 `model.patch`/元数据、单目录 artifact、结果映射和正常 Compose 清理均通过；固定摘要、禁网容器又覆盖了修改、新建、删除和 Agent commit 四类非空 patch，并经宿主生产校验器验证。阻塞 collect 探针复现外层强杀残留并验证生产 Adapter 的精确 Compose project 清理和日志有界收束。Codex、网络/凭据和固定 Fork 仍待验证。

## 7. 恢复固定源码

在 AgentExam 仓库根目录执行以下命令。目标目录必须不存在；如果已经存在，应先核验，不要直接覆盖。

```powershell
git clone https://github.com/SWE-Gym/SWE-Gym.git framework/swe-gym
git -C framework/swe-gym checkout --detach b681068ca20628c6987b7416cc4cf03f06b77ba5

git clone https://github.com/SWE-Gym/SWE-Bench-Fork.git framework/swe-bench-fork
git -C framework/swe-bench-fork checkout --detach 242429c188fcfd06aad13fce9a54d450470bf0ac

git clone https://github.com/harbor-framework/harbor.git framework/harbor
git -C framework/harbor checkout --detach 6af8d6e31eced13b93849cdf80feeadf24603d15
```

`--detach` 表示不跟随某个可继续移动的分支，而是直接停在指定提交。恢复源码不等于安装依赖，也不会自动下载数据集或镜像。

## 8. 核验本地源码

分别执行：

```powershell
git -C framework/swe-gym remote get-url origin
git -C framework/swe-gym rev-parse HEAD
git -C framework/swe-gym status --porcelain

git -C framework/swe-bench-fork remote get-url origin
git -C framework/swe-bench-fork rev-parse HEAD
git -C framework/swe-bench-fork status --porcelain

git -C framework/harbor remote get-url origin
git -C framework/harbor rev-parse HEAD
git -C framework/harbor status --porcelain
```

成功标准：

- 三个远程地址分别与第 4、5、6 节完全一致；
- 三个 `HEAD` 分别等于表中的 40 位完整提交哈希；
- 三个 `status --porcelain` 均无输出，表示没有本地改动；
- SWE-Bench-Fork 的 `swebench/__init__.py` 仍声明 `2.0.13`；若任一结果不同，不得把该环境标记为已复现。

Harbor 已恢复到本机固定提交且工作树干净；若上述核验失败，应先查明本机后续变化，不得覆盖或重建现有环境。

## 9. 尚待确认的锁定项

以下事项必须通过后续架构确认或真实运行完成，当前不得补猜：

1. 首个原型已经固定 Lite revision、`train` split、候选单题和内容校验值；候选成为正式首题仍取决于真实 M0 闭环，正式榜最终数据范围另行确认；
2. M0 已采用并拉取候选预构建实例镜像；其固定 digest 和 `/testbed` base commit 已核验，Harbor/Codex/Harness 兼容性仍待实测；
3. Python、FastAPI、Node.js、Next.js 15、React 19、Docker/Compose、PostgreSQL、MinIO 的精确版本和部署形态；
4. SWE-Bench-Fork 未固定 Python 依赖的项目级锁定版本；
5. Codex、Aider、Claude Code 的精确 CLI 版本、安装来源和校验方式；Codex 认证政策已经确认，不再作为待选择项，但项目固定版本、模型 ID、端点和容器兼容性仍待固定或实测；
6. P2 自研 Agent 的精确 Python 版本、依赖锁格式、DeepSeek/Kimi 模型 ID、外部接口和受控访问运行依赖；不阻塞 M0/M1；
7. Windows + Docker Desktop、WSL2 或 Linux 中哪一种环境作为官方运行基线；
8. Harbor Job/Trial 目录、空 patch collect 和结果映射已由 NOP 固定；修改/新建/删除/Agent commit 四类非空 patch 已由固定摘要、禁网容器验证；CLI 进程 Adapter 的正常 NOP、外层超时精确 Compose 清理和日志有界收束均已验证，仍待真实 Codex 与完整原型验收；
9. 恢复脚本、依赖缓存和供应链校验流程。

## 10. 本次核验证据摘要

| 检查 | 结果 |
|---|---|
| 本机三仓库 `remote.origin.url` | SWE-Gym、SWE-Bench-Fork 与 Harbor 均与第 4～6 节官方地址一致 |
| 本机三仓库 `HEAD` | SWE-Gym、SWE-Bench-Fork 与 Harbor 均与固定提交一致 |
| 本机三仓库 tracked worktree / index | 均干净 |
| 三项上游许可证 | SWE-Gym、Harbor 为 Apache-2.0；SWE-Bench-Fork 为 MIT |
| Harbor 固定源码与环境 | 本机固定提交、`uv.lock` 环境和 CLI `0.22.0` 已核验；真实 NOP Job/Trial 与结果映射通过，Codex 未运行 |
| SWE-Gym 根目录安装清单 | 未发现统一包清单或锁文件 |
| SWE-Bench-Fork 安装入口 | `setup.py` / `pyproject.toml` 存在；Python `>=3.8`，依赖未锁版本 |
| 数据集来源 | 固定 Lite revision、`train` split、230 条记录、候选单题和 Parquet 内容哈希已核验 |
| 镜像来源 | 候选 Docker Hub 镜像的 linux/amd64 digest、拉取结果与 `/testbed` base commit 已核验 |
| Codex 宿主 CLI 探针 | 2026-09-06 `codex --version` 返回 `codex-cli 0.153.0`；它仍不是项目固定版本，容器运行未验证 |
| 动态验证 | Docker/WSL、固定镜像无网络探针、项目 Task/Harbor 类型契约及 NOP Docker Trial/结果映射通过；Codex Trial 和 SWE-Bench-Fork 评测仍未执行 |
