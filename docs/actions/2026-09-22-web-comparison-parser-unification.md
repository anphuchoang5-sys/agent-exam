# 2026-09-22 Web 比较响应解析器统一

## 状态与情况说明

状态：Completed。

来源请求：用户在理解两套比较响应解析规则的差异后，要求统一。当前工作区为 `agent+api`，已有上轮尚未提交的文档对账与结果文案复用改动；本行动只追加 Web 比较响应解析器的统一，不覆盖、回退或封存前一行动的成果。上轮已结束的 `docs/actions/2026-09-22-code-documentation-alignment.md` 作为历史记录只读。

修改前的代码事实：`lib/reporting/comparison-shape.ts` 由当前比较页面的 `comparison-client.ts` 使用，校验五档 `outcome`、结果真值、Run/报告引用以及列行汇总长度；`lib/reporting/comparison-shapes.ts` 由 `job-client.ts` 的 `comparisons()` 使用，但该包装函数目前没有页面调用，且旧解析器对部分不一致的结果放行。两个入口请求同一个 `GET /reports/comparisons`。后端矩阵与 `docs/interfaces/HTTP_API.md` §10.4 是响应事实源。

## 实施措施

1. 保留当前页面已使用的 `comparison-shape.ts` 作为唯一解析器、类型和五档中文映射来源；把 20 列限制常量移入该文件。
2. `job-client.comparisons()` 改用同一解析器；比较页面和 Job 列表从同一文件读取限制常量。删除不再被运行时代码引用的旧 `comparison-shapes.ts`。
3. 增加针对先前校验分歧的回归用例：合法的缺失报告保留 `run_id` 可通过；“已解决但 `resolved=null`”及非缺失格缺少报告引用必须失败关闭。
4. 更新当前模块架构对 Web 解析器的描述，并核对差异、引用、测试与工作区。

完成标准：Web 源码只保留一个比较响应解析函数；两条请求入口使用它；合法响应继续显示，矛盾响应统一拒绝；公开 HTTP 形状和结果词语不变。

## 实际修改的文件树

```text
apps/web/src/lib/reporting/
  comparison-shape.ts                 # 唯一的响应类型、五档映射、解析器和列数上限
  comparison-shapes.ts                # 删除宽松的重复解析器及重复类型
apps/web/src/lib/job-client.ts        # 旧导出包装函数引用统一解析器
apps/web/src/features/jobs/
  listing/view.tsx                    # Job 列表读取统一的列数上限
  reporting/comparison.tsx            # 比较页读取统一的列数上限
apps/web/tests/reporting/
  comparison-parser.spec.ts           # 校验分歧的合同回归
HANDOFF.md                             # 当前分支的后续变更入口
docs/architecture/modules/evidence-and-reporting/
  ARCHITECTURE.md                     # 当前 Web 比较响应的唯一解析来源和依赖方向
docs/architecture/modules/web-and-http/
  ARCHITECTURE.md                     # Web 侧对比数据流的唯一形状校验入口
docs/actions/
  2026-09-22-web-comparison-parser-unification.md # 本次行动与验证证据
```

这里是现有 HTTP Adapter 的响应形状校验：两个客户端包装函数只负责调用同一个只读端点，再交给 `comparison-shape.ts` 校验；展示组件仅消费通过校验的矩阵。不新增顶层 Module、公开 Interface、数据库表或目录。`comparison-shapes.ts` 已删除；原本位于其中的 `COMPARISON_LIMIT` 移入唯一解析文件。新增测试复用两个客户端入口，实际验证一致的接受和拒绝结果。

## 自验证方式

- `rg` 确认源代码仅有一处比较响应解析函数定义，两个入口均调用它，旧文件没有引用。
- Web `npm run typecheck` 和 `npm run lint` 全通过；新解析器回归验证合法缺失格和两类矛盾格。
- 使用项目的系统 Chrome 开关运行比较页面相关浏览器用例，确认矩阵和证据钻取未退化。
- `git diff --check`、改动文档相对链接检查及 `git status --short`；确认保留上一行动和原有未跟踪文件。

## 自验证情况

已执行并查看输出：

- `rg` 对 `apps/web/src` 的扫描：仅 `comparison-shape.ts` 定义 `parseComparison`；`job-client.ts` 和 `comparison-client.ts` 均调用它；没有旧 `comparison-shapes` 引用。
- `npm run typecheck` 和 `npm run lint`：通过，Lint 零 warning。
- 设置项目已有的 `AGENTEXAM_USE_SYSTEM_CHROME=1` 后运行 `npm run test:e2e -- reporting/comparison-parser.spec.ts reporting/comparison.spec.ts reporting/comparison-semantics.spec.ts`：新合同回归 **3 passed**，既有对比语义 **2 passed**，既有对比页面 **3 passed**，共 **8 passed / 0 failed**。新增用例确认两条客户端入口对有效响应均接受，对同一矛盾响应均拒绝；合法的“有 Run、无报告”缺失格保持可读。
- `git diff --check` 通过；`HANDOFF.md`、两份当前模块架构和本行动文档的相对链接均存在。Playwright 包装器运行期间暂时更新的 `next-env.d.ts`/`tsconfig.json` 已恢复，最终工作区没有这两项差异。
- 已结束的上一行动和研究记录没有修改；此前未提交的文档/文案映射改动及 `.scratch/ui-catalog-providers.zip`、`apps/web/%USERPROFILE%/` 两项未跟踪产物均保留。未运行后端测试、全量浏览器测试或真实提供方调用；本次变更不涉及这些路径。
