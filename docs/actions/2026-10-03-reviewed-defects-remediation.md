# 九项已审查缺陷修复

## 情况说明
状态：Completed（九项代码修复、可运行验证与独立审查完成；真实集成限制见下文）。用户要求开始修复已确认的九项缺陷，在重要节点提交，最后推送。云端 main 基线 `908d2d0`；2026-10-03 fetch 确认 origin/main 没有新增提交。保留未追踪的环境配置行动，不纳入此次提交。
范围：同内容原始日志去重、准备阶段取消竞态、Harbor 异常退出定向清理、五项前端状态/选择/退出错误，以及 retention UUID 幂等比较。读取放大/完整性策略、真实模型、用户本机、运行环境重构均不在范围。

## 实施措施
1. 存储与 retention 最小修复及回归，形成提交。
2. Worker 取消竞态与 Harbor 清理最小修复及回归，形成提交。
3. Web Job/Run 身份与请求次序、分页选择和退出错误修复及回归，形成提交。
4. 汇总静态检查与测试，更新当前文档和问题状态，复核差异后提交并普通 push；不 force push。

## 实际修改文件树
- apps/backend/src/eval_platform/
  - application/execution/raw_evidence.py：规范对象去重与保留审计一致性。
  - application/execute_job.py：准备阶段取消冲突识别。
  - adapters/persistence/jobs/retention/state.py：删除完成 UUID 幂等比较。
  - adapters/execution/harbor/adapter.py：非零退出定向清理。
- apps/backend/tests/
  - jobs/artifacts/identity/test_raw_identity.py：重复来源/限额/CompletionFactory 回归。
  - jobs/artifacts/identity/test_retention_identity.py：数据库 UUID 形状与审计负向回归。
  - jobs/artifacts/test_postgres_minio.py：门控真实完成和重复审计回归。
  - jobs/execution/cancellation/test_preparing_worker.py：真实 Worker 循环的受控取消竞争。
  - unit/harbor/test_abnormal_cleanup.py：异常退出、精确资源与告警。
- apps/web/
  - package.json：无浏览器状态测试入口，无新增依赖。
  - src/features/jobs/submit.tsx、report.tsx、evidence.tsx：Job/Run 身份、报告次序、轨迹重入保护。
  - src/features/jobs/lifecycle/recovery.tsx：重试详情读成功才更新 URL，卸载废弃迟到状态。
  - src/features/jobs/reporting/comparison.tsx：保留首屏外选择，权限核验及卸载失效。
  - src/features/identity/session.tsx、src/features/workbench/shell.tsx：退出失败在登录态可见。
  - tests/support/component-probe.mjs：实际 TSX 转译/隔离 hook 测试辅助，非 React DOM renderer。
  - tests/jobs/report-state.test.mjs、tests/reporting/selection-state.test.mjs、tests/security/logout-state.test.mjs：可运行状态回归。
  - tests/jobs/report-state.spec.ts、tests/security/logout-failure.spec.ts：新浏览器回归。
  - tests/jobs/interruption-recovery.spec.ts、tests/workbench/pagination.spec.ts：扩展原浏览器恢复/跨页选择用例。
- docs/architecture/DATA_MODEL.md：规范对象及审计合同，纠正读取成本描述。
- docs/architecture/modules/job-control/ARCHITECTURE.md、web-and-http/ARCHITECTURE.md：取消和页面状态边界。
- docs/interfaces/HARBOR_EXECUTION.md、HTTP_API.md：清理及跨页选择合同。
- docs/reviews/2026-10-03-reviewed-defects-status.md：九项当前状态及剩余验证边界。
- docs/actions/2026-10-03-reviewed-defects-remediation.md：本次行动与证据。
- HANDOFF.md：当前修复入口，保留并标识本机历史状态。
无新设计模式；保持 Web/CLI → delivery → application → domain/ports ← adapters。新增 identity/ 只是在既有 artifacts 测试职责内分组，父目录不超过 8 个文件。原有超限 adapter.py 已减少到 200 行；本次改动的生产源文件均不超过 200 行。忽略态 runtime/tests/review-fixes/ 保存检查日志，不进入 Git。

## 修改后自验证方式
后端使用 apps/backend/.venv/bin 下 Ruff check、Ruff format --check、Mypy、Pytest；先运行定向回归，再运行根 Pytest。前端 npm run lint、typecheck、build 及可执行的无浏览器回归；新增浏览器用例若当前隔离环境不可运行，明确记为未运行。回归尽量验证修复前失败、修复后通过。Docker/PostgreSQL/MinIO/真实模型未运行不得宣称通过。按路径暂存，检查每次提交内容，推送后核对 origin/main SHA 与可用 CI。

## 自验证情况
三个代码里程碑与前后端检查均已执行。完整测试并非全绿，失败与跳过如下实录。

### 存储与删除审计里程碑
- 已修复 #1、#9：`publish_raw` 对每份来源独立校验后按规范对象键去重，重复项在 Run 预算中只计一次；保留正文相同但截断审计矛盾时失败关闭。既有 CompletionFactory 因此只为每个对象分配一个 UUID，无需修改该类。
- `retention/state.py` 把已完成记录的 `deletion_intent_id` 规范成字符串，其他身份/确认/审计字段核验保持不变。
- 新增 `tests/jobs/artifacts/identity/test_raw_identity.py`（原始来源、预算、独立验证与 CompletionFactory）和 `test_retention_identity.py`（UUID 数据库形状、已完成审计回退与负向字段）；嵌入现有 artifacts 测试职责，避免在已达 8 文件的父目录继续堆文件。`test_postgres_minio.py` 补空/非空重复日志的真实完成与并发重复审计门控回归。
- 同一新增纯回归对旧实现为 8 failed / 18 passed，修复后为 26 passed；扩大相关执行/制品回归为 60 passed / 7 skipped。
- 五文件 Ruff check、Ruff format --check、两个生产源文件 Mypy 和 diff 空白检查通过。独立审查重新执行全部新增后端回归为 46 passed，存储/取消/清理实现未发现阻断项。
- PostgreSQL/MinIO 未运行；对应门控测试 skipped，不把唯一约束真实回滚或数据库竞争写成已验证。同步 DATA_MODEL 的对象身份和幂等审计说明，并纠正已有“元数据列表不读取正文”的不实描述；未改变完整性读取策略。

### Worker 与 Harbor 里程碑
- 已修复 #2、#3：启动租约冲突仅在同一 Job 重读为 CANCELED 时正常结束本轮；真正的租约/存储/读取错误仍向上传播。Harbor 已启动进程返回非零退出码时复用原 project 精确清理，保留已有结果和清理告警。
- 新增 `tests/jobs/execution/cancellation/test_preparing_worker.py`：真实命令循环 + 同步屏障固定 claim/start 取消窗口，确认当前 Job 不执行、下一项批准 Job 完成、循环正常停止；覆盖版本、Worker、过期、读取及存储错误不被吞掉。
- 新增 `tests/unit/harbor/test_abnormal_cleanup.py`：退出 1/-9、已有完成结果、清理失败/未验证与启动失败；执行实际 project label 清理函数，仅替代 Docker 子进程结果，确认四类目标资源清理且其他 project 保留。
- 新增 20 项回归对旧实现为 13 failed / 7 passed，修复后 20 passed；相邻执行/Worker/取消/Harbor 回归为 132 passed / 11 skipped。4 文件 Ruff check/format、2 源文件 Mypy、diff 检查通过。
- `adapter.py` 内联仅单次使用的路径辅助，204 行降至 200；其余改动源文件不超过 200 行。无新生产模块、接口、依赖或迁移。
- 真实 Docker、PG、MinIO 与模型未运行；11 项 skipped 为既有显式持久化门禁，不代表真实容器故障注入通过。

### Web 状态里程碑
- 已修复 #4–#8：Run 身份隔离与轨迹防重入、最后一次报告请求生效、新 Job 切换清空旧报告、首屏外选择单独核验、登录态可见退出错误并保留重试。
- 独立审查发现比较刷新卸载后迟到 `JOB_NOT_FOUND` 仍可能调用父级 toggle，已补卸载/清空请求失效与回归。恢复组件也在卸载后废弃迟到结果；新 Job 详情读取成功后才更新 URL，失败仍保留原幂等键。
- `cd apps/web && npm run test:state`：21 passed / 0 failed。隔离源码副本使用 `908d2d0` 旧实现时同 21 例为 20 failed / 1 passed；没有改回共享工作树源码。日志在忽略态 `runtime/tests/frontend-state-before.log` 与 `frontend-state-after.log`。
- `npm run lint`、`npm run typecheck`、`npm run build` 均通过；未新增依赖，锁文件未变化，`next-env.d.ts`/`tsconfig.json` 未变化。
- `npx playwright test --list tests/jobs/report-state.spec.ts tests/security/logout-failure.spec.ts tests/jobs/interruption-recovery.spec.ts tests/workbench/pagination.spec.ts` 成功收集 4 文件 6 例（新增 4，扩展原 2）。本轮未执行浏览器，不将收集算作测试通过。
- 独立审查重跑 21 项状态回归通过，并额外核对失败重试沿用幂等键、recover 卸载后不更新父状态；无待处理代码 blocker。状态辅助只是实际 TSX 的隔离 hook 探针，不是 React DOM 或浏览器渲染验收。


### 最终统一检查与交付边界
- `apps/backend/.venv/bin/ruff check apps/backend`：通过。
- `apps/backend/.venv/bin/ruff format --check apps/backend`：通过，380 文件。
- `apps/backend/.venv/bin/mypy`：失败，仅既有两处 Windows 专属属性 `process_evidence.py:154 ctypes.windll`、`process_runner.py:116 subprocess.CREATE_NEW_PROCESS_GROUP`；195 源文件。本轮未扩大为跨平台类型修复。
- `apps/backend/.venv/bin/mypy --platform win32`：通过，195 源文件；不替代 Linux 检查。
- 根目录 `apps/backend/.venv/bin/pytest`：871 项，740 passed / 118 skipped / 13 failed，97.70 秒。与原环境基线 694/117/13 相比增加 46 项通过和 1 项门控跳过；失败测试名逐项 diff 完全相同。
- 13 项失败：9 项缺 Docker Compose CLI，2 项缺固定 Harbor checkout/Windows 虚拟环境入口；另 2 项分别为已复现的提供方断连时序与日志捕获 Linux 双读取线程收束计时。没有放宽断言或改为伪跳过。完整输出：忽略态 `runtime/tests/review-fixes/pytest-root.log`；静态检查日志同目录。
- 修复前/后回归汇总：后端新增 46 项，旧实现 21 failed / 25 passed，修复后 46 passed；前端新增 21 项隔离状态测试，旧实现 20 failed / 1 passed，修复后 21 passed。它们不能替代真实 PostgreSQL、MinIO、Docker 和浏览器验收。
- 提交前 `git diff --check` 通过；最终 fetch 确认远端没有新增并行提交。按路径暂存，原未追踪环境配置行动保持不动；没有 force push、stash、秘密复制或本机修改。
- 代码里程碑：`f0776d7` 存储身份；`a82ed10` Worker/Harbor；`cc8fa09` Web 状态。提交仅使用命令级 `dot <dot@localhost>` 作者，不修改持久 Git 配置，不冒用既有作者。
- 本仓库没有受版本控制的 GitHub Actions 工作流；自动检查与最终发布 SHA 以本次推送后的 GitHub 远端现场核对为准，不由本地测试推断远端 CI 通过。
