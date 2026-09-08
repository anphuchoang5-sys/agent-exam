# 项目依赖唯一事实源

> 文档状态：持续维护；固定依赖已支持第四场真实 Codex 单题与独立 Fork 判卷通过；完整 M0 安全/生命周期验收引用执行与认证接口
>
> 最后更新：2026-09-07；网络镜像核验：2026-09-07；CLI 最后核验：2026-09-07
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
| SWE-Bench-Fork | SWE-Gym 环境常量、Docker 环境构建和评测 Harness（自动执行测试并判定补丁是否解决任务的程序） | `242429c188fcfd06aad13fce9a54d450470bf0ac` | 否 | 已在隔离 Linux 环境运行原 CLI；项目仅适配镜像准备/容器创建，gold、空、错误、不可应用、超时五类真实判卷通过 |
| Harbor | Execution Backend（执行后端）：把一个平台 Job 展开并运行成多个 Agent Trial，管理 Agent、环境、资源/网络策略和轨迹 | `6af8d6e31eced13b93849cdf80feeadf24603d15` | 否 | 固定源码和隔离环境已恢复，CLI `0.22.0` 可用；真实类型/Task 契约与 NOP Docker Trial/结果映射通过，Codex Trial 未运行 |
| Python 运行时 | 后端及 SWE-Bench-Fork 运行时 | 后端 `>=3.13,<3.14`；Fork 当前 Ubuntu Python `3.12.3` | 不适用 | 后端使用 `pyproject.toml`/`uv.lock`；Fork 使用 `swebench-requirements.txt` 的 Linux Python 3.12 带哈希锁，63 项运行依赖已安装且启动时核对版本 |
| FastAPI | 后端 HTTP 交付层 | 待确认 | 后续由项目包清单锁定 | 已确认采用；精确版本未固定 |
| Node.js 运行时 | Web 前端构建/运行 | 待确认 | 不适用 | 已确认采用；版本未选定 |
| Next.js | Web 框架 | `15.x`，精确版本待确认 | 后续由前端包清单锁定 | 已确认采用 Next.js 15 |
| React | Web 视图框架 | `19.x`，精确版本待确认 | 后续由前端包清单锁定 | 已确认采用 React 19 |
| Docker Engine / Docker Desktop / Compose | 隔离并运行评测环境 | 项目基线待确认；本机 Desktop `4.38.0.181591`、Engine `27.5.1` | 不适用 | Harbor NOP/超时与固定 Fork 五类真实补丁集成已验证；环境细节见 [`LOCAL_DOCKER_ENVIRONMENT.md`](../operations/LOCAL_DOCKER_ENVIRONMENT.md) |
| PostgreSQL | 结构化业务数据存储与 MVP 平台 Evaluation Job 队列 | 待确认 | 不适用 | 已确认采用；M0 本机脚本原型不依赖；精确版本未固定 |
| MinIO | 对象存储，即保存 patch、日志等文件制品 | 待确认 | 不适用 | 已确认采用；精确版本未固定 |
| Codex CLI | M0 本机真实原型与 M1 平台 MVP Agent | 首轮 `0.153.0`，用户于 2026-09-07 确认 | 否 | 使用 Harbor 内置 Codex Adapter，认证沿用评测机所有者的 ChatGPT Pro（见 [`CODEX_AUTHENTICATION.md`](../interfaces/CODEX_AUTHENTICATION.md)）；固定包校验、禁网容器启动和 Harbor 预装复用已通过，见第 2.1 节；第四场真实单题已通过，剩余网络/凭据生命周期验收引用执行与认证接口 |
| Aider CLI | Codex MVP 之后的已知 Agent | 待确认 | 否 | 已确认在 Codex 平台闭环后接入；尚未安装或固定版本，不阻塞 MVP |
| Claude Code CLI | Codex MVP 之后的已知 Agent | 待确认 | 否 | 已确认在 Codex 平台闭环后接入；尚未安装或固定版本，不阻塞 MVP |
| 本地自研 Agent | P2 扩展 Agent | 待实现 | 是，由提交者固定 Git commit 提交，审核后登记 | 只保留扩展接缝；P2 首版只支持 Python 和固定进程 Interface，完整 manifest、Python 版本、依赖锁格式与 Harbor 包装不阻塞 MVP |
| DeepSeek / Kimi 模型接口 | P2 自研 Agent 唯一允许的外部模型提供方 | 精确模型与接口版本待确认 | 否 | 提供方范围和本机 Key 所有权已确认；Key 不进入被测 Agent，外部协议、受控访问部署和真实调用留到 P2 核验，见 [`CODEX_AUTHENTICATION.md`](../interfaces/CODEX_AUTHENTICATION.md) |

“待确认”不等于推荐使用最新版；在版本被确认并写入本文件前，不得把本机偶然安装的版本当成团队基线。

依赖恢复与验证必须服从顺序：M0 只恢复 Harbor、SWE-Gym Lite 单题所需数据/镜像、SWE-Bench-Fork 和 Codex；M1 再加入 Web、PostgreSQL、MinIO；M1 通过后才处理 Aider/Claude Code；自研 Agent 与 DeepSeek/Kimi 为 P2。不得因为 P2 依赖未定而推迟 Codex 闭环。

Codex 的版本选择已完成，不再根据宿主升级或 `latest` 自动变化。[官方安装文档](https://learn.chatgpt.com/docs/cli) 提供独立安装器和 npm `@openai/codex`；本项目采用该包发布的 Linux 平台制品完成无凭据离线安装探针，身份见第 2.1 节。Harbor 复用同版本预装 CLI 的条件见 [框架接口第 7 节](../interfaces/FRAMEWORK_INTERFACES.md#7-codex-cli-adapter)。

2026-09-07 用户确认首轮模型 ID 为 `gpt-5.6-terra`，随后确认 reasoning effort（推理强度）为 `medium`；提供方仍为 OpenAI，认证仍用既定 ChatGPT 登录政策。首轮 CLI、模型与推理强度选择已完成，实际配置沿用现有 `critical_config.reasoning_effort` 显式传入。该选择不等于已经证明本账号或固定容器 CLI 能实际调用；不自动换模型或强度，不把测试占位符当真实配置，也不因本次确认打开尚未验收的真实入口。

### 2.1 Codex 无凭据安装制品

2026-09-07 已从官方 npm registry 的主包元数据核对 Linux x64 optional dependency，并下载对应平台包。仅核验 registry 公布的完整性值与实际包字节，未验证签名/来源证明链，不将校验和称为完整供应链审计。

| 输入 | 固定值或事实 |
|---|---|
| 平台包 | `@openai/codex@0.153.0-linux-x64`；目标 `x86_64-unknown-linux-musl` |
| 下载地址 | `https://registry.npmjs.org/@openai/codex/-/codex-0.153.0-linux-x64.tgz` |
| 大小 | `129210185` bytes |
| SHA-512 | `b0517e83ba75a3ab1954be8f1ddf494d8acfda3df16a8dd07aee409e072b0f96eb5ab09cfb0f627c124226e45233bdbc59f8235cc2fd3d03dd1cf69949e1c010` |
| 包布局 | 8 个普通文件；包含 Codex、code-mode host、rg、bwrap、zsh 和平台布局元数据 |
| 本机证据 | 忽略目录 `runtime/prototype/m0-codex-install-20260907-01/`；归档保留，解包逐文件 SHA-256 写入 `installation-input.json` |
| 实现 | [`codex/install.py`](../../apps/backend/src/eval_platform/adapters/execution/codex/install.py)；先核验大小/整包 hash/严格成员列表/平台身份，再创建独占解包目录；不执行 npm 脚本或下载最新版 |

使用既有固定任务摘要镜像创建临时禁网容器，离线复制已校验工具包；以非 root 用户执行版本/帮助，通过固定 Harbor 真实 `Codex.install()` 的版本检查复用已安装工具。随后正式接线把同一校验加入生产 `GuardedCodex.install()`：每次运行重新验证归档与解包文件，固定 `/opt/agentexam-codex` 和 PATH，版本不符即失败而不进入 curl/npm 在线安装；假认证、`network none` 的 Docker 契约已通过。首次真实 Trial 暴露的版本首行误判已修复，现严格要求最后一条非空行等于 `codex-cli 0.153.0`；第二次启动误传不存在的 Windows `.zip` 后，正确固定 Linux `.tgz` 的大小与 SHA-512 再次复核一致。第三次授权运行共用同一预检/启动构造，已通过生产离线安装、真实认证上传和 UID 65534 的 CLI 会话启动，但因 DNS 转发受阻而超时，无模型回复或有效补丁。未重建基础镜像、安装 Node/npm 或升级宿主；本轮无生产代码变更。上述为第三场历史结果；后续 DNS 修正已获授权并接入，第四场真实模型/工具、补丁和独立判卷已通过，剩余 Token 刷新等验收见[当前执行状态](../interfaces/HARBOR_EXECUTION.md#第四次授权运行真实补丁与独立判卷通过2026-09-08)及[M0 行动记录](../actions/2026-09-05-m0-codex-harbor-implementation.md)。

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

当前验证状态：Task Adapter 的公开/隐藏隔离、固定 Parquet、摘要镜像与 Harbor NOP 已核验；同一固定镜像又用于通过的 Fork 五类真实补丁验证。第四场真实 Codex 与独立 Fork 已通过，具体结果见第 2.1 节执行状态指针。

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

该命令是上游入口；项目实际使用固定源码的 `PYTHONPATH` 加隔离依赖环境，没有对上游执行 editable 安装。上游 [`setup.py`](https://github.com/SWE-Gym/SWE-Bench-Fork/blob/242429c188fcfd06aad13fce9a54d450470bf0ac/setup.py) 声明：

- Python 要求：`>=3.8`；
- 核心直接依赖：`beautifulsoup4`、`chardet`、`datasets`、`docker`、`ghapi`、`GitPython`、`pre-commit`、`python-dotenv`、`requests`、`rich`、`unidiff`、`tqdm`；
- `inference` 可选依赖：`tiktoken`、`openai`、`anthropic`、`transformers`、`peft`、`sentencepiece`、`protobuf`、`torch`、`flash_attn`、`triton`、`jedi`、`tenacity`。

上游没有锁文件；项目现以 [`swebench-requirements.in`](../../apps/backend/swebench-requirements.in) 记录这 12 项运行依赖，以 [`swebench-requirements.txt`](../../apps/backend/swebench-requirements.txt) 锁定 Linux Python 3.12 的 63 项传递依赖及分发文件 SHA-256，不安装 inference extra。当前载体为已有 Ubuntu WSL2 的 Python `3.12.3`，隔离环境位于 `framework/swe-bench-fork/.venv`。每次 Fork 启动核对锁文件哈希与全部已装版本，并保存 `runtime.json`。

本机恢复流程（先确认目标不存在，复用已有缓存；不修改系统 Python）：

```text
Windows：uv pip install --target runtime/tools/uv-linux --python-version 3.12 --python-platform x86_64-unknown-linux-gnu --no-python-downloads --only-binary :all: uv==0.12.10
WSL：runtime/tools/uv-linux/bin/uv venv framework/swe-bench-fork/.venv --python /usr/bin/python3 --no-python-downloads
Windows：uv pip install --target framework/swe-bench-fork/.venv/lib/python3.12/site-packages --python-version 3.12 --python-platform x86_64-unknown-linux-gnu --no-python-downloads --only-binary :all: --require-hashes -r apps/backend/swebench-requirements.txt
```

这里 Windows 的 `uv` 为本项目 `runtime/tools/uv-bootstrap/Scripts/uv.exe`（`0.12.10`）。需要下载时仅给对应进程配置既有代理和 `UV_CACHE_DIR`；Linux 实际执行使用清空后重建的环境变量，不继承个人凭据或 `.env`。原生 `--help` 已在该隔离环境通过；接口适配范围见 [`FRAMEWORK_INTERFACES.md` 第 5.4 节](../interfaces/FRAMEWORK_INTERFACES.md#54-项目实际调用方式)。

### 5.3 数据与镜像来源

- Harness 支持 Hugging Face 数据集名称以及本地 JSON/JSONL；具体字段和 CLI 规则见 [`FRAMEWORK_INTERFACES.md`](../interfaces/FRAMEWORK_INTERFACES.md)。
- 上游 CLI 默认数据集是 `princeton-nlp/SWE-bench_Lite`、默认 split 是 `test`。这是上游默认值，不是 AgentExam 已确认的 SWE-Gym 数据选择；项目调用时必须显式指定后续确认的数据集与 split。
- 固定源码把本地镜像命名为 `sweb.base.<arch>:latest`、`sweb.env.<arch>.<hash>:latest` 和 `sweb.eval.<arch>.<instance_id>:latest`。
- 基础 Dockerfile 从 `ubuntu:22.04` 构建并下载 Miniconda 安装器；两者都未按镜像 digest 或文件校验和固定。
- 对固定提交执行源码搜索，没有发现 `docker pull` 或 Docker SDK `images.pull` 调用。也就是说，SWE-Gym README 提到的 `xingyaoww/...` 预构建镜像不是当前 Harness 自动恢复流程；默认行为是在本机缺少镜像时按源码构建。

当前验证状态：固定 Fork CLI 与五类真实判卷已经通过。原 CLI 的 base/env 预检查与 16 GiB 默认限制由 Evaluator 内部基础设施适配处理，直接使用已固定的实例镜像 digest，不伪造 base/env 标签、不重建上游镜像、不修改上游源码或 grading。原始报告与失败证据见 [M0 行动记录](../actions/2026-09-05-m0-codex-harbor-implementation.md)；第四场 Codex 端到端已通过，完整验收边界引用执行接口。

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

当前验证状态：固定源码/环境已恢复；配置模型、Job/Trial 展开、结果模型、制品顺序和 Verifier 关闭能力已做源码核验，真实 `JobConfig`/`Task` 契约测试通过。NOP Docker Trial 已实际启动并完成，collect hook 生成的空 `model.patch`/元数据、单目录 artifact、结果映射和正常 Compose 清理均通过；固定摘要、禁网容器又覆盖了修改、新建、删除和 Agent commit 四类非空 patch，并经宿主生产校验器验证。阻塞 collect 探针复现外层强杀残留并验证生产 Adapter 的精确 Compose project 清理和日志有界收束。固定 Fork 已完成第 5 节的五类验证；真实 Codex 最新单题结果及剩余网络/凭据验收引用第 2.1 节执行状态指针。

### 6.3 网络探针的固定镜像与构建输入

2026-09-07 为 M0 无凭据网络探针拉取固定 Harbor 源码已引用的两个镜像，并核对摘要：

| 输入 | 固定身份 | 用途 |
|---|---|---|
| Alpine | `alpine:3.23.4@sha256:5b10f432ef3da1b8d4c7eb6c487f2f5a8f096bc91145e68878dd4a5019afde11` | Harbor 原生内核探针；该镜像没有 httpd applet，不作测试 HTTP 服务 |
| GOST | `gogost/gost:3.2.7-nightly.20260602@sha256:afc0137758ab4ce399d47a299f9abbacbf522b52a17e59cbb4b4e7a1a66e9196` | 原生透明网络侧车的基础镜像；版本来自固定源码，不是选择 nightly 最新值 |

侧车由固定提交的 `src/harbor/environments/docker/harbor-docker-egress-control-sidecar/` 五个文件构建，复用 Harbor 原生内容哈希命名及构建缓存。Windows 检出中的 CRLF 会使脚本解释器无效；既有 Execution Backend 内部 `network.py` 使用 `git show <固定提交>:<路径>` 获取原始 blob，拒绝覆盖或非固定/跟踪文件有修改的上游工作树。2026-09-08 已授权限定 DNS 修正只作用于导出的 network-policy 运行副本；`network-source.json` 同时保存 revision、五项 `upstream_sha256`、五项生效 `sha256` 和 adaptation 标识。生产 `harbor_entry.py` 与网络测试共用该导出，按生效内容构建；固定上游工作树、其他四个 blob、旧缓存与全局 Git 配置不变。允许/禁止 HTTP 对照服务复用第 4.2 节任务摘要镜像中的 Python 标准库，无额外 Python 依赖。具体适配边界、失败关闭与验证状态唯一维护在 [Harbor 执行接口](../interfaces/HARBOR_EXECUTION.md#限定-dns-适配2026-09-08)。

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
4. SWE-Bench-Fork 已有 Linux Python 3.12 哈希锁与单题实测；新增题目/升级依赖时重新验证，不默认把当前单题扩展成全题库通过；
5. Codex 首轮 CLI 版本、模型 ID、推理强度与认证政策已确认；制品身份及无凭据容器安装见第 2.1 节，第四场账号/模型路径和实际工具执行已通过，完整生命周期与网络边界仍按专题接口收尾。Aider、Claude Code 的精确 CLI 版本、安装来源和校验方式仍待确认；
6. P2 自研 Agent 的精确 Python 版本、依赖锁格式、DeepSeek/Kimi 模型 ID、外部接口和受控访问运行依赖；不阻塞 M0/M1；
7. Windows + Docker Desktop、WSL2 或 Linux 中哪一种环境作为官方运行基线；
8. Harbor Job/Trial 目录、空 patch collect 和结果映射已由 NOP 固定；修改/新建/删除/Agent commit 四类非空 patch 已由固定摘要、禁网容器验证；CLI 进程 Adapter 的正常 NOP、外层超时精确 Compose 清理和日志有界收束均已验证，第四场真实 Codex 核心闭环已通过，完整原型验收继续按专题接口收尾；
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
| Codex 宿主 CLI 探针 | 2026-09-07 `codex --version` 返回值与第 2 节已确认首轮版本一致；容器运行未验证 |
| 动态验证 | Harbor NOP/超时、collect-patch 四场景及固定 Fork 五类真实判卷通过；Codex Trial 仍未执行 |
