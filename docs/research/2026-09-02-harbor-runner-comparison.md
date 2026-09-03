# Harbor 能否承担 AgentExam 的 Runner

> 状态：研究完成；方案 B 已于 2026-09-03 确认为架构决定，运行验收仍待完成
>
> 研究日期：2026-09-02 至 2026-09-03
>
> Harbor 固定版本：`6af8d6e31eced13b93849cdf80feeadf24603d15`

## 问题

团队提出“Runner 模块可以使用 Harbor”。本研究核对：Harbor 能否在不改变 SWE-Gym 任务语义、且不取代固定 SWE-Bench-Fork 最终判卷的前提下，复用为 AgentExam 的 Agent 执行能力。

这里的 Runner 指“把题目交给 Agent、启动受限环境、等待 Agent 工作并收回补丁与轨迹”的模块，不包括最终判断补丁是否通过测试。

## 结论摘要

最终判断为：**方向可行，但“Harbor 就是 Runner”并不准确。团队已确认把 Harbor 放在 Execution Backend（执行后端）这一更完整的接缝后面，并保留明确退出门槛。**

Harbor 是完整度较高的 Agent 评测执行框架，不是只实现 `stdin -> stdout patch` 的小型 Runner。它的 Agent 接口与 Harbor 的 Environment、Trial、Artifact 和 Verifier 模型相互配合。因此，更合理的候选接缝是：

```text
AgentExam Job Orchestrator
        |
        v
Harbor Execution Backend（已确认，待运行验收）
  |- Harbor Agent Adapter
  |- Harbor Docker Environment / 网络与资源策略
  `- Harbor 轨迹和运行制品
        |
        v
model_patch
        |
        v
AgentExam Patch Evaluator
        `- 固定 SWE-Bench-Fork run_evaluation（唯一最终判卷）
```

换句话说，Harbor 将封装“Agent Runner + 一部分 Sandbox Controller + 一部分 Trajectory Recorder”，但不替代 AgentExam 的课程管理后端、PostgreSQL、MinIO、人工抽检、排行榜，也不替代固定的 SWE-Bench-Fork 判卷链路。

正式架构边界见 [`HARBOR_EXECUTION.md`](../interfaces/HARBOR_EXECUTION.md)，决策理由和退出门槛见 [`ADR-0001`](../adr/0001-use-harbor-as-execution-backend.md)。本文件保留研究证据，不再作为当前架构状态的唯一事实源。

## 已核验事实

### 1. Harbor 原生具备我们需要的多项执行能力

当前 Harbor 的官方仓库声明支持评测任意 Agent，并自带 Codex、Claude Code、Aider 等 Agent 实现、Docker 与其他环境提供者、任务/试验编排、网络策略、制品和轨迹模型。当前 `pyproject.toml` 显示版本为 0.22.0、要求 Python 3.12 或更高版本，并采用 Apache-2.0 许可证。

官方 `BaseAgent` 的核心抽象方法是：

```python
setup(environment)
run(instruction, environment, context)
```

这说明 Harbor 的 Agent 运行与 Harbor Environment 紧密协作，并非 AgentExam 当前文档中的纯 `stdin -> stdout patch` 黑盒协议。

### 2. Harbor 已有官方 SWE-Gym Adapter

Harbor 的 `adapters/swegym` 会读取 SWE-Gym 数据集中的 `instance_id`、`repo`、`base_commit`、`problem_statement`、`test_patch`、`FAIL_TO_PASS` 和 `PASS_TO_PASS`，并转换成 Harbor Task 目录。其模板能够设置 CPU、内存、磁盘和超时；官方 README 也记录了 Oracle 验证和 OpenHands 对比实验。

这证明 Harbor 不是只能“参考 SWE-Gym”，而是已经具备实际转换和运行 SWE-Gym 任务的能力。

### 3. Harbor 的 SWE-Gym 判卷不是我们的固定判卷入口

Harbor 的 SWE-Gym `tests/test.sh` 会生成测试命令，然后用其自写 Python 解析器读取日志、匹配 `FAIL_TO_PASS` 与 `PASS_TO_PASS` 并输出 Reward。它没有直接调用本项目固定的：

```text
swebench.harness.run_evaluation
```

因此，即使 Harbor 官方报告了与原基准接近的 parity，也不能直接证明它与本项目固定的 SWE-Bench-Fork 在每个边界情况上完全等价。题目要求的最终确定性证据仍应由固定 SWE-Bench-Fork 产生。

### 4. Harbor 能关闭自身 Verifier，但补丁出口仍需验证

`SingleStepTrial` 的执行顺序是运行 Agent、同步日志、收集制品，然后运行 Verifier；配置允许关闭 Harbor Verifier。这使“Harbor 只负责 Agent 执行，AgentExam 另行判卷”在结构上具有可能性。

不过，`TrialResult.AgentContext` 主要记录 token、成本和 metadata，并没有一个已核验的标准 `model_patch` 字段。Agent 修改的是容器内仓库，AgentExam 如何稳定取得 `git diff`，仍需要用最小原型确认。候选方式包括在 Harbor Trial 清理环境前，由受控的收尾步骤把 `git diff` 写成制品；不能依赖 Agent 自觉输出补丁。

### 5. 轨迹复用价值较高

Harbor 的 Codex 实现会读取 Codex 会话 JSONL，转换为 ATIF 轨迹，并记录消息、工具调用、工具输出、token 和成本。它比为每个 Agent 从零设计轨迹解析更成熟。但不同 Agent 的轨迹完整度仍取决于该 Agent 和 Harbor Adapter 的能力，不能假定四类 Agent 的字段天然完全一致。

## 与当前设计逐项对照

| 当前模块 | Harbor 能否复用 | 判断 |
|---|---|---|
| SWE-Gym Task Adapter | 部分可以 | Harbor 有官方转换器，但 AgentExam 仍需冻结数据版本并保留自己的规范化任务身份 |
| Agent Runner / Agent Adapter | 高度可以 | 这是 Harbor 最有价值的部分，已有多种 Agent 实现 |
| Sandbox Controller | 大部分可以 | Harbor 环境层已管理 Docker、资源和网络；若只取 Runner 而另写一套 Sandbox，会职责重复 |
| Trajectory Recorder | 部分到高度可以 | Codex 等适配器可输出 ATIF；需逐 Agent 验证完整度 |
| Patch 提取 | 尚未证明 | Harbor 结果模型未直接保证返回 `model_patch`，必须原型验证 |
| SWE-Bench-Fork Evaluator | 不替代 | Harbor SWE-Gym verifier 不是固定 Fork 的 `run_evaluation` |
| PostgreSQL / MinIO | 不替代 | AgentExam 仍保存业务元数据和不可变制品；不把 Harbor 本地 Job 目录当课程平台数据库 |
| LLM Judge / 人工抽检 / Web | 不替代 | 仍属于 AgentExam 产品能力 |

## 三种方案

### A. 全部自研 Runner

优点是接口最可控、课程贡献清晰；缺点是一个月、2.5 人需要自己处理 Codex/Claude Code/Aider、自研 Agent、Docker、轨迹兼容和错误恢复，工作量与风险最大。

### B. Harbor 作为 Execution Backend（已选择，须先验收）

AgentExam 保留自己的 Orchestrator、数据库、MinIO、报告与固定 SWE-Bench-Fork；Harbor 负责 Agent 安装/启动、环境执行、网络资源约束和轨迹。AgentExam 通过一个薄 Adapter 把规范化任务转换给 Harbor，再取回补丁和证据。

优点是显著复用成熟能力，同时保留本项目的业务边界和唯一判卷权。风险是 Harbor 的公开接缝不是现有 `stdin -> stdout patch`，需要做任务转换、补丁提取、错误映射和版本锁定。

### C. Harbor 接管整个评测

直接使用 Harbor Task、Job、Trial 和 Verifier。开发量最少，但会与已确认的 SWE-Bench-Fork 直接判卷、PostgreSQL/MinIO 和自研平台边界发生明显冲突，也容易让作品变成 Harbor 的包装界面。当前不推荐。

## 单机可行性

Harbor 不会让单台笔记本变成分布式系统。它仍然运行 Docker 容器，并受本机可用内存限制。本机迁移后的路径、版本、磁盘余量和动态内存核验统一记录在 [`LOCAL_DOCKER_ENVIRONMENT.md`](../operations/LOCAL_DOCKER_ENVIRONMENT.md)，本文件不复制维护这些易变化数值。

官方 SWE-Gym Task 模板默认给**单个任务环境** 8192 MB，而本机的 10 GB 是整个 WSL2 的**共享上限**。Agent 环境、Docker/WSL 自身和其他 WSL 进程会竞争这部分内存，因此模板仍不能仅凭数值小于 10 GB 就直接判定可用；继续采用重型评测并发 1，并用真实单题实验确定 Trial 资源模板。

## 采用后的最小验收原型

在不改变上层接口的前提下，用一个 SWE-Gym Lite 任务做短期技术验收：

1. 固定 Harbor commit 与 Python 版本。
2. Mock Agent 只用于配置转换、状态机和错误映射等内部软件测试；端到端验收必须使用一个真实可用的 Agent 运行 Trial，并关闭 Harbor 的最终判卷权。
3. 明确设置并验证网络策略，不能采用未声明的默认值。
4. 自动提取容器中 Agent 修改产生的 Git diff，形成 `model_patch`。
5. 把同一 `model_patch` 交给固定 SWE-Bench-Fork `run_evaluation`。
6. 检查 Harbor 的轨迹、工具调用、原始日志、超时、取消与容器清理。
7. 使用空补丁、错误补丁和正确补丁做判卷一致性检查。

成功标准是：稳定返回补丁与轨迹；固定 Fork 能独立判卷；Harbor 结果不会覆盖 Fork 结果；资源不超过单机限制；网络与凭证不泄露。若核心接缝不能可靠满足标准，则保持上层 `ExecutionBackend` 接口不变，把实现换成轻量 Process Adapter；不能为了保留 Harbor 而降低判卷证据标准。

## 当前未知与风险

- 尚未在本机安装或运行 Harbor，运行兼容性未验证。
- Harbor 当前要求 Python 3.12+，需要与项目后端依赖隔离或统一版本。
- `model_patch` 的稳定、非 Agent 自觉式提取方式尚未实测。
- Harbor 的不同 Agent Adapter 是否都能生成同等完整的 ATIF 轨迹尚未逐一核验。
- 网络 allowlist 对模型 API、GitHub 和 Agent 原生 Web 工具的实际边界尚未实测。
- Harbor 版本演进较快，必须固定 commit，不能追随 `main` 漂移。
- Harbor SWE-Gym Adapter 的 parity 是重要参考，但不是固定 SWE-Bench-Fork 的逐项等价证明。

## 官方来源

- [Harbor 固定版本 README](https://github.com/harbor-framework/harbor/blob/6af8d6e31eced13b93849cdf80feeadf24603d15/README.md)
- [Harbor 固定版本 pyproject.toml](https://github.com/harbor-framework/harbor/blob/6af8d6e31eced13b93849cdf80feeadf24603d15/pyproject.toml)
- [Harbor SWE-Gym Adapter README](https://github.com/harbor-framework/harbor/blob/6af8d6e31eced13b93849cdf80feeadf24603d15/adapters/swegym/README.md)
- [Harbor SWE-Gym 转换源码](https://github.com/harbor-framework/harbor/blob/6af8d6e31eced13b93849cdf80feeadf24603d15/adapters/swegym/adapter.py)
- [Harbor SWE-Gym 判卷模板](https://github.com/harbor-framework/harbor/blob/6af8d6e31eced13b93849cdf80feeadf24603d15/adapters/swegym/template/tests/test.sh)
- [Harbor BaseAgent 接口](https://github.com/harbor-framework/harbor/blob/6af8d6e31eced13b93849cdf80feeadf24603d15/src/harbor/agents/base.py)
- [Harbor SingleStepTrial 流程](https://github.com/harbor-framework/harbor/blob/6af8d6e31eced13b93849cdf80feeadf24603d15/src/harbor/trial/single_step.py)
- [Harbor TrialResult 模型](https://github.com/harbor-framework/harbor/blob/6af8d6e31eced13b93849cdf80feeadf24603d15/src/harbor/models/trial/result.py)
- [Harbor Codex Adapter](https://github.com/harbor-framework/harbor/blob/6af8d6e31eced13b93849cdf80feeadf24603d15/src/harbor/agents/installed/codex.py)

## 已采用的决定

团队已把“Runner 使用 Harbor”收敛为以下正式决定：

> AgentExam 保留自身评测编排、PostgreSQL Job 队列和固定 SWE-Bench-Fork 判卷。Harbor 作为正式 Execution Backend，复用 Agent、Docker 环境、网络资源策略与轨迹能力；一个平台 Job 映射一个 Harbor Job，Agent × Task × Attempt 映射为 Trial，首版 `n_attempts=1`、`n_concurrent_trials=1`。单题端到端原型是继续采用 Harbor 的验收门，不是允许跳过的可选实验。
