# 项目依赖唯一事实源

> 文档状态：已建立；三项上游源代码身份及本机 Docker/WSL 运行时已核验，项目版本基线与外部制品版本仍待确认
>
> 最后核验：2026-09-03
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
| SWE-Gym | 任务数据、模型与复现实验材料的上游来源 | `b681068ca20628c6987b7416cc4cf03f06b77ba5` | 否 | 源码身份、许可证和上游制品入口已核验；数据未下载 |
| SWE-Bench-Fork | SWE-Gym 环境常量、Docker 环境构建和评测 Harness（自动执行测试并判定补丁是否解决任务的程序） | `242429c188fcfd06aad13fce9a54d450470bf0ac` | 否 | 源码身份、许可证和安装入口已核验；该 Fork 尚未安装或运行 |
| Harbor | Execution Backend（执行后端）：把一个平台 Job 展开并运行成多个 Agent Trial，管理 Agent、环境、资源/网络策略和轨迹 | `6af8d6e31eced13b93849cdf80feeadf24603d15` | 否 | 固定源码接口、包版本和许可证已静态核验；本机尚未下载、安装或运行 |
| Python 运行时 | 后端及 SWE-Bench-Fork 运行时 | 待确认 | 不适用 | 已确认采用；上游只声明 `>=3.8`，项目基线未选定 |
| FastAPI | 后端 HTTP 交付层 | 待确认 | 后续由项目包清单锁定 | 已确认采用；精确版本未固定 |
| Node.js 运行时 | Web 前端构建/运行 | 待确认 | 不适用 | 已确认采用；版本未选定 |
| Next.js | Web 框架 | `15.x`，精确版本待确认 | 后续由前端包清单锁定 | 已确认采用 Next.js 15 |
| React | Web 视图框架 | `19.x`，精确版本待确认 | 后续由前端包清单锁定 | 已确认采用 React 19 |
| Docker Engine / Docker Desktop / Compose | 隔离并运行评测环境 | 项目基线待确认；本机 Desktop `4.38.0.181591`、Engine `27.5.1` | 不适用 | 本机 Windows + WSL2 部署和无网络冒烟测试已验证；Compose 与 SWE-Bench-Fork 集成未验证，详见 [`LOCAL_DOCKER_ENVIRONMENT.md`](../operations/LOCAL_DOCKER_ENVIRONMENT.md) |
| PostgreSQL | 结构化业务数据存储与首版平台 Evaluation Job 队列 | 待确认 | 不适用 | 已确认采用；精确版本未固定 |
| MinIO | 对象存储，即保存 patch、日志等文件制品 | 待确认 | 不适用 | 已确认采用；精确版本未固定 |
| Codex CLI | 目标 Agent 执行器 | 待确认 | 否 | 已确认接入目标；可运行版本未固定 |
| Aider CLI | 目标 Agent 执行器 | 待确认 | 否 | 已确认接入目标；尚未安装或固定版本 |
| Claude Code CLI | 目标 Agent 执行器 | 待确认 | 否 | 已确认接入目标；尚未安装或固定版本 |
| 本地自研 Agent | 目标 Agent 执行器 | 待实现 | 是，由 AgentExam 项目维护 | 已确认接入目标；进程接口和版本载体未确定 |

“待确认”不等于推荐使用最新版；在版本被确认并写入本文件前，不得把本机偶然安装的版本当成团队基线。

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
- README 没有为 AgentExam 要使用的数据给出已确认的精确 dataset ID、revision、split，也没有给镜像记录不可变 digest。为保证复现性，这些值必须在实际选取和下载后再写入本文件。
- OpenHands 和 MoatlessTools 出现在上游复现实验说明中；它们当前不是 AgentExam 已固定的直接依赖，不能仅凭上游示例自动纳入项目。

当前验证状态：只核验了固定提交中的源码、README 与许可证；没有访问 Hugging Face 内容，没有下载数据或模型，没有拉取或运行镜像。

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
| 计划恢复路径 | `framework/harbor`；当前目录不存在 |
| 固定提交 | `6af8d6e31eced13b93849cdf80feeadf24603d15` |
| 包内版本 | `0.22.0` |
| Python 要求 | `>=3.12` |
| 许可证 | Apache License 2.0 |
| 固定提交入口 | <https://github.com/harbor-framework/harbor/tree/6af8d6e31eced13b93849cdf80feeadf24603d15> |

完整提交哈希是项目的权威固定版本；包内版本 `0.22.0` 只作为辅助身份。版本、Python 要求与许可证已经从固定提交的 `pyproject.toml` 和 `LICENSE` 静态核验，但这不等于 Harbor 已在本机安装或跑通。

### 6.2 在项目中的边界

- Harbor 是已确认采用、但仍须通过原型验收的 Execution Backend，不是平台数据库、课程管理后端或最终判卷器。
- PostgreSQL 继续管理平台 Evaluation Job 队列；一个平台 Job 映射为一个 Harbor Job。
- Harbor 按 Agent × Task × Attempt 展开 Trial；首版 `n_attempts=1`、`n_concurrent_trials=1`。
- 固定 SWE-Bench-Fork 的 `swebench.harness.run_evaluation` 仍是唯一确定性最终判卷入口，Harbor Reward 不能覆盖其结论。
- Harbor 的精确接口、转换与退出门槛由 [`HARBOR_EXECUTION.md`](../interfaces/HARBOR_EXECUTION.md) 维护；采用决定见 [`ADR-0001`](../adr/0001-use-harbor-as-execution-backend.md)。

当前验证状态：已对固定提交中的配置模型、Job/Trial 展开、结果模型、制品顺序和 Verifier 关闭能力进行静态核验；尚未下载源码、安装依赖、创建 Harbor Job、启动 Trial 或验证 `model_patch` 提取。

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

Harbor 当前尚未恢复到本机，所以对它执行上述命令会因目录不存在而失败；这正是当前真实状态，不应标记为已复现。

## 9. 尚待确认的锁定项

以下事项必须通过后续架构确认或真实运行完成，当前不得补猜：

1. AgentExam 使用的精确 SWE-Gym dataset ID、revision、split、首批实例及内容校验值；
2. 是否采用预构建实例镜像；若采用，需要记录完整仓库名、架构、不可变 digest 与来源验证；
3. Python、FastAPI、Node.js、Next.js 15、React 19、Docker/Compose、PostgreSQL、MinIO 的精确版本和部署形态；
4. SWE-Bench-Fork 未固定 Python 依赖的项目级锁定版本；
5. Codex、Aider、Claude Code 的精确 CLI 版本、安装来源和校验方式；
6. Windows + Docker Desktop、WSL2 或 Linux 中哪一种环境作为官方运行基线；
7. Harbor 的安装方式、项目隔离环境、完整依赖锁、Job 目录位置及原型验收结果；
8. 恢复脚本、依赖缓存和供应链校验流程。

## 10. 本次核验证据摘要

| 检查 | 结果 |
|---|---|
| 本机两仓库 `remote.origin.url` | SWE-Gym 与 SWE-Bench-Fork 均与第 4、5 节官方地址一致 |
| 本机两仓库 `HEAD` | SWE-Gym 与 SWE-Bench-Fork 均与固定提交一致 |
| 本机两仓库 tracked worktree / index | 均干净 |
| 三项上游许可证 | SWE-Gym、Harbor 为 Apache-2.0；SWE-Bench-Fork 为 MIT |
| Harbor 固定源码 | 配置/Job/Trial/结果/制品/Verifier 接口已远程静态核验；本机目录尚不存在 |
| SWE-Gym 根目录安装清单 | 未发现统一包清单或锁文件 |
| SWE-Bench-Fork 安装入口 | `setup.py` / `pyproject.toml` 存在；Python `>=3.8`，依赖未锁版本 |
| 数据集来源 | SWE-Gym Hugging Face 组织页已从 README 核验；精确数据 revision 未核验 |
| 镜像来源 | Docker Hub 前缀已从 SWE-Gym README 核验；镜像 digest 与可用性未核验 |
| 动态验证 | 本机 Docker/WSL 已通过无网络最小容器验证；Harbor、SWE-Gym 数据、镜像构建和 SWE-Bench-Fork 评测仍未执行 |
