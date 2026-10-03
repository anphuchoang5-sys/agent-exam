# AgentExam 代码质量审查资源调研

查阅日期：2026-09-30。状态：完成。本文是调研时点的研究档案，不代表已经对项目完成代码审查；后续新结论另开记录。

## 结论与现有基础

建议先使用下文的中文提示词做只读审查，以项目规则和 Google 的审查标准判断问题，再用现有检查工具验证。暂不需要部署一个新的审查平台。代码风格、可维护性和功能缺陷应分别报告，不能用一个缺乏依据的百分制分数代替证据。

本轮静态读取了 [后端配置](../../apps/backend/pyproject.toml)、[前端配置](../../apps/web/package.json)和 [ESLint 配置](../../apps/web/eslint.config.mjs)：Python 3.13/FastAPI 已配置 Ruff 的 `E/F/I/B/UP`、mypy 严格模式及 pytest 覆盖率；TypeScript/React 19/Next.js 15 已配置 Next.js ESLint 规则、类型检查和 Playwright 入口。**配置存在不等于本轮检查通过**，本轮没有运行这些检查。

## 审查标准与可参考的提示词

**Google Engineering Practices：适合作为审查标准。** 官方清单覆盖设计、功能、复杂度、测试、命名、注释、风格和文档，并要求结合上下文阅读。个人风格偏好应标成可选建议，不应被当成功能问题。它是方法文档，不是自动审查程序，也不要求上传代码。建议采用其检查维度，再服从本仓库已有约定。[官方清单](https://google.github.io/eng-practices/review/reviewer/looking-for.html)

**PR-Agent：适合参考实际使用的 AI 审查提示词。** 旧 `qodo-ai/pr-agent` 地址现已重定向到 `The-PR-Agent/pr-agent`；仓库说明它是社区维护的原 PR-Agent，与 Qodo 当前产品不同。它提供命令行和代码托管平台集成，采用 MIT 许可证。运行机器人需要安装、选定模型和配置平台权限；只阅读提示词无需这些步骤。[项目仓库](https://github.com/The-PR-Agent/pr-agent)

它的 [审查提示词源码](https://github.com/The-PR-Agent/pr-agent/blob/main/pr_agent/settings/pr_reviewer_prompts.toml)要求给出具体问题、现实触发条件、文件和行号；证据不足时避免猜测，并允许没有发现。其默认对象是 PR 新增代码，不能直接当作全仓库审查。源码也有可选百分制评分，本项目不采用这一字段。

运行位置和数据去向需要分开判断：PR-Agent 在本机运行时，若选择远程模型，相关代码上下文仍需发送给模型服务；自托管机器人并不自动意味着代码全程留在本机。所选模型、代码托管访问权限、是否发表评论及模型调用费用均应另外确定。本轮没有安装、授权、外发项目代码或查询商用报价。[模型与部署说明](https://github.com/The-PR-Agent/pr-agent#why-use-pr-agent)、[数据说明](https://github.com/The-PR-Agent/pr-agent#data-privacy)

## 静态工具的适用边界

静态检查是“读取代码结构后按明确规则找问题”，不需要实际启动业务服务。它能提供可重复的证据，但无法独自证明业务正确或架构合理。

| 需求 | 首选能力 | 适用与限制 |
| --- | --- | --- |
| 代码风格、常见错误、类型 | 复用现有 Ruff、ESLint、mypy、TypeScript | 优先按仓库配置审查，避免另建一套互相冲突的规则；本轮未运行。 |
| 函数分支过多、难以理解 | Ruff `C901`、ESLint `complexity` | 两者已有复杂度检查能力；当前项目配置没有显式启用这两个指标。超阈值只是复查线索，不能据此断言代码错误。[Ruff 规则](https://docs.astral.sh/ruff/rules/complex-structure/)、[ESLint 规则](https://eslint.org/docs/latest/rules/complexity) |
| Python 模块越界、循环依赖 | 可选 Import Linter | 能表达禁止导入、分层、模块独立及同级无环约束；适合把已经确认的后端依赖方向变成检查。需先盘点现有架构检查，不能直接用工具重定架构。[契约类型](https://import-linter.readthedocs.io/en/stable/contract_types/) |
| 危险编码模式 | 可选 Semgrep Community Edition（CE） | 支持 Python、JavaScript/TypeScript 等语言的社区规则，适合补充安全静态检查；CE 的相关语言分析受单函数边界限制，不能保证发现跨层鉴权或跨文件数据流问题。[CE 支持表](https://docs.semgrep.dev/semgrep-ce-languages) |

Import Linter 是采用 BSD-2-Clause 许可证的 Python 工具，发行记录明确支持 Python 3.13，并记录了 Windows 修复。命令行流程分析本地导入关系，不需要云模型；本轮没有进行安装、网络行为审计或本机兼容性验证。它不检查前端，也不能理解动态运行时的全部依赖。新增依赖与约束配置应在正式审查确认缺口后决定。[项目](https://github.com/seddonym/import-linter)、[发行记录](https://import-linter.readthedocs.io/en/stable/release_notes/)、[运行方式](https://import-linter.readthedocs.io/en/stable/get_started/run/)

Semgrep CE 的 Windows 原生安装在官方快速入门中仍标为 beta，是否能在本机可靠运行需要另行验证。普通 CE 扫描在本地分析代码；从规则库获取规则可能联网，默认指标设置还可能发送统计信息，可用 `--metrics off` 关闭。采用本地规则、是否连接平台或使用 AI 功能，需要分别决定，不能把所有模式概括成“完全离线”。CE 与商业平台能力有区别，本轮没有安装、登录或运行扫描。[快速入门](https://docs.semgrep.dev/getting-started/quickstart-ce)、[指标说明](https://docs.semgrep.dev/metrics)、[源仓库说明](https://github.com/semgrep/semgrep/blob/develop/README.md)

## 可复制的中文只读审查提示词

以下内容为结合本仓库授权边界编写的提示词，不是对外部提示词的逐字翻译。可以直接用于下一次明确授权的只读审查。

```text
请对 E:\9.1agent_exam 的 AgentExam 做一次有证据的只读代码质量审查。
目标是判断哪里确实存在缺陷或维护成本，区分编码规范、设计问题和业务错误。
不要预设项目质量差，不给没有基准的百分制评分，也不为了凑数报告问题。

授权边界：
- 只允许读取文件、rg 搜索和只读 Git 命令；不修改任何文件。
- 不安装依赖，不启动 Web、Backend、Worker、Docker、数据库或评测；不运行测试和扫描工具。
- 不 fetch/pull/switch/merge/reset/clean/commit/push，不修改或清理其他 worktree。
- 不读取、输出或修改密码、Cookie、Key、auth.json、真实 .env 等凭据。
- 不向外部审查服务发送项目代码；不要进入本地 npm 缓存或无关演示文稿。
- docs/actions/ 与 docs/research/ 的已结束文件只可作为历史证据，不反向修改。

准备：
1. 完整读取 AGENTS.md 和其要求的汇报技能，读取 HANDOFF.md。
2. 探索业务代码前读取 docs/agents/domain.md；读取任务单前读取
   docs/agents/issue-tracker.md。随后阅读当前架构、接口与运维文档。
3. 核对现场分支、提交和工作区改动。默认审查当前工作树；若我指定了
   提交范围，则以该范围为主，并阅读必要的调用方、实现和测试。
4. 盘点现有 Ruff、mypy、ESLint、TypeScript 和测试配置，只报告配置事实。
   不把历史通过记录或工具配置存在写成本轮验证通过。

审查范围与方法：
- 重点阅读 apps/backend/src/eval_platform/、apps/web/src/、infra/ 与对应测试。
- 按现有模块分批，先列实际覆盖范围；没有完整阅读的部分明确列为未覆盖。
- 后端检查依赖方向、接口复用、状态转换、异常与资源释放、权限边界、
  并发与重复请求处理、数据库与证据保存的一致性；以现有业务规则为准。
- 前端检查服务端和客户端边界、请求失败与空状态、异步更新、类型边界、
  重复逻辑及可访问性；不要凭个人偏好要求改 UI 或组件架构。
- 检查测试能否发现对应缺陷，是否只重复实现；阅读测试不等于运行测试。
- 检查命名、冗余、循环依赖、职责混杂及不必要复杂性。
- 按 AGENTS.md 检查动态语言源文件 200 行、每层文件夹 8 文件等约束；
  先定义统计口径、排除生成物和第三方文件，并查阅已批准的例外记录。
  只凭超限不得断言架构错误，也不得为达标建议机械拆分。
- 文档与实现矛盾时核对代码、配置、接口定义和 Git 状态，仅报告差异。
- 优先深化已有模块并复用已有接口。涉及新模块、接口或重构范围的建议
  只能标为待用户决定，不得直接实施或把候选设计写成既定架构。

每条问题必须包含：
严重程度、类别、具体路径与当前行号、证据、现实触发条件或维护影响、
最小改进建议、如何验证以及尚未确定的部分。
追踪相关调用方和测试后再判断；不能证明的问题放入“待核实”，不要冒充缺陷。

交付：
- 按风险排序报告已证实缺陷，另列规范违例、可选风格建议与待核实项。
- 相同根因合并；没有发现可报告的问题时明确说明。
- 列实际覆盖范围、未覆盖部分和未执行检查。
- 按项目汇报规则收尾。完成后等待我决定修复范围，不自行修改代码。
```

## 本次核查与限制

所有外部依据来自官方文档或项目源仓库，并于上述日期访问；搜索结果中的第三方文章未作为结论依据。已核对配置、工具用途和提示词来源，未执行代码审查、安装、测试、服务启动或模型调用。推荐次序是本项目条件下的判断，不是工具效果基准测试；尚不能据此认定项目存在多少风格问题或缺陷。
