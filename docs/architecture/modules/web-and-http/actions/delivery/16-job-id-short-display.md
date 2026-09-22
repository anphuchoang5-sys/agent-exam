# 行动 16：列表与工作台的 job_id 改短码显示（保留可追溯性）

> 状态：**已完成**（2026-09-22，基于 `main = 80c1c29`）。只改 Web 呈现层两处，未动后端、未动 `globals.css`。
>
> 来源请求：用户认为列表／工作台里整串 36 位 UUID 看着难看，要求改成短码显示、但可追溯性不能丢；同时消除"按钮文案里再拼一遍 id"的重复。

## 1. 情况说明

**现状（改前实测，来自 `runtime/tests/jobid-shots.mjs before` 的 DOM 读取）**：

| 位置 | 改前可见文本 | 问题 |
|---|---|---|
| `features/workbench/dashboard.tsx` 批次行 | `执行中 / 1 个 Run / 229b701d-…-b5ba…(整串) / 打开评测 229b701d-…(整串)` | 一行里整串 UUID 出现 **2 次**，按钮文案被撑到换行 |
| `features/jobs/listing/view.tsx` 批次行 | `已完成 / 1 个 Run · 2026/9/22 23:13:08 / a1ec6d23-…(整串) / 查看评测 a1ec6d23-…(整串)` | 同上；且时间戳与 id **黏在一起**（`23:13:08a1ec6d23-…`） |

**请求里一处与代码不符，已按代码事实处理**：请求说"详情页仍显示完整 id（`features/jobs/details.tsx`）"，但 **`details.tsx` 根本不渲染 `job_id`**（全文只有 `rerun_of_job_id` 的展示）。详情页上完整 id 的唯一载体是 URL 的 `?job=` 参数。因此第 3 条要求天然满足：**没有改 `details.tsx`**，并改用"详情页 URL 的 job 参数仍等于完整 id"作为可追溯性的实测证据。

**工作树起点**：开工时 `git status --short` 为**空**——请求提到的 `globals.css` 未提交改动此时已经在 `main` 上（即 `80c1c29`）。本次自始至终未编辑、未回退 `globals.css`。

**范围与排除**：只改工作台与评测列表两个渲染点；`submit.tsx`、`lifecycle/recovery.tsx`、`reporting/*`（对比矩阵等）**本次不动**，仅在报告里列出清单供用户决定。

## 2. 实施措施

1. `features/jobs/listing/labels.ts` 新增唯一事实源 `shortJobId(jobId)`：返回 `${jobId.slice(0, 8)}…`（8 位短码 + 省略号）。两处调用点共用，不各写一份截断逻辑。
2. 两个批次行的 `<article>` 加 `title={job.job_id}`：完整值随行渲染在 **title 上**（悬停即可读到整串），不依赖 API 也能拿到，满足硬要求。
3. 行内 `<code>` 由整串改为 `shortJobId(job.job_id)`。
4. 按钮文案去掉 id：`打开评测 {job.job_id}` → `打开评测`；`查看评测 {job.job_id}` → `查看评测`。
5. 顺手修掉列表行里**改前就存在**的黏连：`<span>` 与 `<code>` 之间补显式空格（`{" "}`），文本变成 `1 个 Run · 2026/9/22 23:17:09 · d432c1e5…`。

## 3. 实际改动的文件树

```
apps/web/src/features/jobs/listing/
  labels.ts        （改）新增 shortJobId()：短码格式的唯一事实源，含"完整值在 title / 详情页 URL"的注释
  view.tsx         （改）列表行：article 加 title、code 改短码、按钮去 id、时间与短码之间补分隔
apps/web/src/features/workbench/
  dashboard.tsx    （改）工作台批次行：同上几何（article 加 title、code 改短码、按钮去 id）
apps/web/tests/workbench/
  dashboard.spec.ts（改）2 条 toContainText(整串) 换成"title = 整串 + code 文本 = 短码… + 行内不出现整串"
  task-02.spec.ts  （改）列表行同一组断言；按钮定位由 name: `查看评测 ${id}` 改为 `查看评测`（scoped 到行）
docs/architecture/modules/web-and-http/
  progress.md      （改）补 2026-09-22 本行动一条进展
  actions/delivery/16-job-id-short-display.md （新增）本文件
runtime/tests/jobid-shots.mjs                  （新增，runtime/ 已被 .gitignore 忽略）一次性前后对照截图脚本
```

设计模式：无新增模式。`shortJobId` 是**纯函数式展示映射**，与既有 `JOB_STATUS_NAMES` 同属该 feature 的标签层（同一模块、同一被 `dashboard.tsx` 复用的既有依赖方向，未新增目录或顶层 Module）。

## 4. 自验证方式

| 检查 | 命令 | 成功标准 |
|---|---|---|
| 类型 | `cd apps/web && npx tsc --noEmit` | 退出码 0 |
| 静态 | `cd apps/web && npx eslint . --max-warnings 0` | 退出码 0、零告警 |
| 构建 | `cd apps/web && npm run build` | 退出码 0 |
| 改动用例 | `AGENTEXAM_USE_SYSTEM_CHROME=1 npm run test:e2e -- workbench/dashboard.spec.ts workbench/task-02.spec.ts` | 全 passed、退出码 0 |
| 无障碍 | `AGENTEXAM_USE_SYSTEM_CHROME=1 npx playwright test tests/a11y/` | **6 passed**（对比度参与断言） |
| 全量 | `AGENTEXAM_USE_SYSTEM_CHROME=1 npm run test:e2e` | 31 个 spec 文件、63 passed、**退出码 0** |
| 窄屏 | `runtime/tests/jobid-shots.mjs` 内置：390 宽度下 `documentElement.scrollWidth <= clientWidth` | 工作台与列表各一次，均不溢出 |
| 视觉 | 同脚本 1440/390 前后各 4 张 | 短码可见、按钮单行、整串只在 title |
| 范围 | `git status --short` | 只出现本行动的文件（+ 用户自己的 `globals.css` 改动，若有） |

## 5. 自验证结果

**全部实测（2026-09-22，本机、串行）：**

- `npx tsc --noEmit` → 退出码 0。
- `npx eslint . --max-warnings 0` → 退出码 0。
- `npm run build` → 退出码 0（`✓ Compiled successfully in 2.2s`，4 个静态页生成完成）。
- 改动用例：`npm run test:e2e -- workbench/dashboard.spec.ts workbench/task-02.spec.ts` → **5 passed / 0 failed，退出码 0**（首轮曾失败 1 条，见 §6）。
- 无障碍：`npx playwright test tests/a11y/` → **6 passed，退出码 0**；扫描行仍是"必须为零 0；只报告 0；需人工复核 0"，`color-contrast` 未回归。
- 全量：见 §7。
- 390 实测（改后）：工作台 `scrollWidth=390 = clientWidth=390`、列表 `390 = 390` → **均不溢出**；1440 同样不溢出。
- 改后 DOM 实测（脚本打印）：工作台行 `执行中 | 1 个 Run | d432c1e5… | 打开评测`、`title=d432c1e5-1362-47eb-a3fd-7b14945505dd`；列表行 `1 个 Run · 2026/9/22 23:17:09 · d432c1e5…`、`title=同上`。
- 详情页可追溯性：点"查看评测"后 `URL ?job=` 仍等于完整 job_id → `true`。

**截图（`runtime/tests/visual-polish/`，1440 与 390 各一组）**：
`before-jobid-dashboard-1440.png` / `after-jobid-dashboard-1440.png` / `before-jobid-jobs-1440.png` / `after-jobid-jobs-1440.png` /
`before-jobid-dashboard-390.png` / `after-jobid-dashboard-390.png` / `before-jobid-jobs-390.png` / `after-jobid-jobs-390.png`。
390 的 before 图里可直接看到整串 UUID 出现两次且按钮换行；after 图里是 `d432c1e5…` 与单行按钮。

## 6. 偏差、失败与未做的事

- **请求里"只有 4 处受影响"的用例清单量漏了 2 处**，实测受影响的是 5 处：
  1. `dashboard.spec.ts:36`、2. `dashboard.spec.ts:38`、3. `task-02.spec.ts:128`、**4. `task-02.spec.ts:129`**（`getByRole("button", { name: \`查看评测 ${job_id}\` })` 也依赖按钮文案里的 id）、**5. `task-02.spec.ts:139`**（重载返回列表后的第二次 `toContainText`）。
- **首轮 `task-02.spec.ts` 失败 1 条，是本次改动引入的**：按钮文案去 id 后，`list.getByRole("button", { name: "查看评测" })` 在该文件内命中了 **2 个**按钮（同一夹具后端，前一条用例创建的批次仍在 `AWAITING_OWNER_APPROVAL`，Playwright 报 strict mode violation）。修法是**把点击 scope 到被断言行**（`row.getByRole(...)`），断言没有删、也没有放宽。复跑 4 passed。
- **`task-02.spec.ts:95` 请求要求改写，但没有改**：那是 `URL ?job=` 的断言（`expect.poll(...searchParams.get("job")).toBe(created.job_id)`），**不显示任何文本**，改短码显示不影响它——它恰好是"URL 仍携带完整 id"的可追溯性证据，保留更有价值。
- **已知取舍（未做，交用户）**：按钮文案去 id 后，同一列表/工作台里多个按钮的可访问名完全相同（"打开评测"/"查看评测"）。行的 `<article>` 因 `title` 获得了等于 UUID 的可访问名，屏幕阅读器按 article 导航时仍能区分，但**按钮列表**里无法区分。若要修，可用 `aria-label`（带短码）而不改可见文案；本次未做，因为请求明确要求文案不带 id。
- **未做**：仍渲染整串 id 的 4 处（`reporting/configuration.tsx`、`reporting/comparison.tsx`、`reporting/matrix.tsx`、`report.tsx` 的 run_id）本次未动，清单见 §8。`submit.tsx`、`lifecycle/recovery.tsx`、`reporting/metrics.tsx` 只是把 id 用作 API 参数、URL 参数或 React key（**不渲染**），无需改；`leaderboard/view.tsx` 与 `workbench/shell.tsx` 同理。未改 `details.tsx`。未改 `globals.css`。
- 本次**未** `git add` / `commit` / `push`。

## 7. 全量套件结果

`AGENTEXAM_USE_SYSTEM_CHROME=1 npm run test:e2e`（本机、串行、`AGENTEXAM_USE_SYSTEM_CHROME=1`）→ **31 个 spec 文件、63 passed / 0 failed / 0 skipped，退出码 0**（日志 `runtime/tests/jobid-full-e2e.log`，与改前基线一致）。**没有出现请求预判之外的失败**；唯一一次失败发生在改动用例的首轮（§6），原因已定位并修好。

收尾：`npm run build` 改写的 `apps/web/tsconfig.json` 已用 `git checkout --` 还原（`next-env.d.ts` 未被改写）；`git status --short` 只有本行动的文件加一个未跟踪的新文档。未 `git add` / `commit` / `push`。

## 8. 仍显示完整 id 的地方（本次未动，供用户决定）

| 位置 | 形态 |
|---|---|
| `features/jobs/reporting/comparison.tsx:146` | 对比选择列表：`<small>{job.job_id}</small>`（每行整串） |
| `features/jobs/reporting/matrix.tsx:30` | 对比矩阵表头：`配置 {n} · {column.job_id}`（整串） |
| `features/jobs/reporting/configuration.tsx:70` | 矩阵明细 `<details>` 里 `<code>{column.job_id}</code>`（整串） |
| `features/jobs/report.tsx:14` | 单次运行报告：`Run：{report.run.run_id}`（**run_id 整串**） |
| `features/jobs/lifecycle/recovery.tsx:55` | 恢复列表按 `run_id` 作 key，未直接渲染 id（无显示） |
| `features/jobs/details.tsx:39` | 仅在"重试批次"上显示 `rerun_of_job_id` 整串（**不是本批次自己的 id**） |
| 详情页 URL | `?view=jobs&job={完整 id}`（地址栏可见，本次有意保留） |
| `features/leaderboard/view.tsx:79`、`shell.tsx:120`、`lifecycle/recovery.tsx:43` | 只把 id 拼进链接/路由参数，不显示 |
