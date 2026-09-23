# 2026-09-22 当前代码与文档对账

## 状态与情况说明

状态：Completed。

来源请求：在 `agent+api` 分支核对文档与当前代码是否齐平；有不对应之处则修正文档。当前基线为 `e6a7138`。用户随后确认：把重复的结果文案映射也纳入本轮代码修改和验证。范围限于既有结果文案映射的复用，不改变接口行为、业务范围或架构方向。`docs/actions/` 已结束记录和 `docs/research/` 已完成记录作为历史档案保留，不反向修改。

已确认：代码实际入口以 `apps/backend/src/eval_platform/`、`apps/web/src/`、`infra/` 及配置为准；`HANDOFF.md`、架构、接口、模块及当前状态页需对账。未知项先按代码、测试和配置核实，不能把历史测试成绩写成本轮新验证。

## 实施措施

1. 建立代码事实清单：核对生产装配、受控 Agent 身份、Job 状态与规模、HTTP 路由、Web 页面、提供方策略层及运行入口。
2. 将当前事实与交接、总架构、模块索引及模块文档、接口和状态导航页逐项比较；记录确证的矛盾。
3. 修正确证过时的当前状态文字；带日期的计划正文保持历史原貌，仅在入口声明时点并指向当前事实。
4. 将 Web 的结果英文码到中文名称集中到现有 `comparison-shape.ts`，让矩阵和批次报告复用；后端 Markdown 保留其运行时映射，并让汇总表头从同一映射取词。跨 Python/TypeScript 的词语用验证核对，避免引入新的跨语言运行时依赖或 API 字段。
5. 核对最终差异、引用与 Git 工作区；运行前后端相关验证，记录尚未核实的动态状态。

完成标准：本轮识别的当前状态矛盾均有代码依据和同步修正；Web 结果映射仅有一处、后端 Markdown 单处映射驱动单元格和汇总表头，词语保持一致；历史档案未被改写；差异、链接和相关代码检查通过。

## 实际受影响文件树

```text
.scratch/ui-catalog-providers/
  implementation-map.md       # 配置身份对和 continuous 实际取值
  plan.md                     # 提供方阶段进度入口
  verification.md             # 分层验收的当前状态说明
HANDOFF.md                    # 当前分支、阶段、运行入口和本次对账接续入口
apps/backend/src/eval_platform/application/reporting/
  matrix_markdown.py          # Markdown 单元格与汇总表头共用后端结果映射
apps/web/src/lib/reporting/
  comparison-shape.ts         # Web 五档结果码到中文名称的唯一映射
  comparison-shapes.ts        # 移除未使用的旧结果文案映射
apps/web/src/features/jobs/
  batch-report.tsx            # 四档批次结果复用 Web 映射
  reporting/matrix.tsx        # 五档比较矩阵复用 Web 映射
docs/LLY/
  README.md                   # 执行负责人材料导航指向当前权威状态
  01-plan/PLAN.md             # 任务 05 当前切片状态及交接指针
  01-plan/STAGE1_IMPLEMENTATION_PLAN.md # 旧分片计划标注编写时点
  01-plan/STAGE1_PROXY_TEST_DESIGN.md   # 旧测试设计标注编写时点
docs/LYQ/
  README.md                   # 目录负责人材料导航和旧 Git 工作流时点
  01-plan/PLAN.md             # 任务 04 开工前计划标注为时点记录
docs/architecture/
  ARCHITECTURE.md             # continuous 与提供方切片的当前架构事实
  MODULE_CONTRACTS.md         # 受控目录身份与未接线边界
  modules/evidence-and-reporting/ARCHITECTURE.md # 后端/Web 文案映射关系
docs/dependencies/DEPENDENCIES.md # 第三方模型接口准备度
docs/interfaces/CODEX_AUTHENTICATION.md # 令牌实际在内存中以原文为键及未完成边界
docs/actions/2026-09-22-code-documentation-alignment.md # 本次实施与验证记录
```

涉及的 Adapter 模式只核对文档描述：`delivery/worker/runtime.py` 作为组合入口，把 `JobExecutor` 接到 `HarborExecutionAdapter` 与 `SWEbenchEvaluator`；`provider_access/` 没有进入生产 Worker 装配。本任务不改变这些参与文件的角色或关系。结果文案的依赖方向是 Web 展示组件引用 Web 解析层的静态映射，后端 Markdown 渲染器读取自身映射；没有跨运行时依赖。没有新增顶层模块、接口、数据表或目录。

## 已核实的差异与处理

- `continuous` 已在 `delivery/job_presets.py` 实现，规模上限为 3 个配置、60 个 Run；总架构及实现地图仍用旧候选/未实现措辞，已改。
- `provider_access/` 已有策略组件与 T1 证据，S8 的 `internal_test` 身份切片已入目录；S2、代理服务、真实供应商身份及生产 Worker 接线仍缺失。交接、计划、依赖和模块契约已区分这些状态。
- `binding.py` 的 `TokenRegistry` 用原始令牌作为进程内字典键，原认证文档声称已哈希，现按代码修正。
- 四个生命周期脚本位于 `infra/local/`；旧交接误称位于根目录，现已修正。旧交接的分支和历史测试表述也已按当前 Git 状态重写。
- 成员计划/导航页保留编写时点，已加当前状态指针；已结束行动和研究记录未改写。
- 后端与 Web 原有结果词语相同，但 Web 另有两份冗余映射，后端汇总表头重复写死五档词语。现在 Web 只有一处结果码映射，后端单元格和表头使用同一映射；跨语言两份映射仍需逐项核对，架构文档已明确这一限制。

## 自验证方式

- `git diff --check`：无空白或补丁格式错误。
- `git diff --name-only` 与 `git status --short`：只出现本轮文档、约定的映射复用代码及原有未跟踪产物，历史档案未改。
- 定向 `rg` 和源码检查：已修正的“已实现/未实现”、文件树、Git 基线描述与当前代码一致。
- 本地 Markdown 相对链接检查：新增或改动的链接指向存在的仓库文件。
- Web `npm run typecheck`、`npm run lint` 与批次/对比浏览器用例；后端 Ruff lint/format 和 `pytest tests/jobs/reporting/test_matrix_markdown.py`。预期结果文案和行为不变。
- 后端和 Web 的五档映射逐项比对；历史测试数字仅保留为历史证据，并明确时点。

## 自验证情况

已执行并查看输出：

- `npm run typecheck`、`npm run lint`：通过。
- `ruff check --no-cache`、`ruff format --check` 对 `matrix_markdown.py`：通过。首次 Ruff lint 因 `.ruff_cache` 无写权限而未运行，格式检查发现补丁插入的混合换行；格式化单文件后复查通过。
- 后端定向 Pytest：默认配置首次因 `.coverage` 无写权限未收集到测试；改用 `-p no:cacheprovider -o addopts=` 后 **3 passed**。本次没有宣称完整覆盖率门禁通过。
- 浏览器回归：默认 Playwright 浏览器缺失，首次 0 项执行；按仓库已有 `AGENTEXAM_USE_SYSTEM_CHROME=1` 使用本机 Chrome 后，`job-batch.spec.ts` **1 passed**、`reporting/comparison.spec.ts` **3 passed**。
- 五个结果码的后端/Web 中文词逐项相同；`rg` 确认 Web 的 `COMPARISON_OUTCOME_NAMES` 定义仅一处。
- 改动的 15 份 Markdown 加本行动记录共 16 份，相对链接目标检查通过；`git diff --check` 通过。`git status` 只有上述 20 个已跟踪文件、本文，以及原先的 `.scratch/ui-catalog-providers.zip` 和 `apps/web/%USERPROFILE%/` 两项未跟踪产物；后两项未修改/清理。已结束 `docs/actions/` 和 `docs/research/` 无跟踪文件差异。
- `comparison-shape.ts` 与 `comparison-shapes.ts` 仍有两套比较响应解析逻辑，分别由 `comparison-client.ts` 与 `job-client.ts` 使用；将来修改响应校验时可能分叉。本轮只收拢中文结果映射，解析器合并需要单独核对调用方与严格度。
- 未重跑全量产品测试、真实供应商调用或动态机器状态检查；旧行动中的性能、运行态和测试数字仍仅代表各自时点。
