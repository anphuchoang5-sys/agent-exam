# 九项已审查缺陷修复

## 情况说明
状态：In progress。用户要求开始修复已确认的九项缺陷，在重要节点提交，最后推送。云端 main 基线 `908d2d0`；2026-10-03 fetch 确认 origin/main 没有新增提交。保留未追踪的环境配置行动，不纳入此次提交。
范围：同内容原始日志去重、准备阶段取消竞态、Harbor 异常退出定向清理、五项前端状态/选择/退出错误，以及 retention UUID 幂等比较。读取放大/完整性策略、真实模型、用户本机、运行环境重构均不在范围。

## 实施措施
1. 存储与 retention 最小修复及回归，形成提交。
2. Worker 取消竞态与 Harbor 清理最小修复及回归，形成提交。
3. Web Job/Run 身份与请求次序、分页选择和退出错误修复及回归，形成提交。
4. 汇总静态检查与测试，更新当前文档和问题状态，复核差异后提交并普通 push；不 force push。

## 需要修改的文件树
- apps/backend/src/eval_platform/application/execution/：证据发布/完成记录；保持既有存储端口。
- apps/backend/src/eval_platform/adapters/persistence/jobs/retention/：删除审计幂等比较。
- apps/backend/src/eval_platform/application/execute_job.py：Worker 执行准入与取消识别。
- apps/backend/src/eval_platform/adapters/execution/harbor/：异常终止后的既有 project 精确清理。
- apps/backend/tests/：以上行为的回归证据。
- apps/web/src/features/jobs/、identity/：按资源身份绑定状态，隔离过期请求并展示退出失败。
- apps/web/tests/：前端回归；不引入新顶层架构。
- docs/actions/2026-10-03-reviewed-defects-remediation.md：本次行动及验证。
- docs/architecture/modules/、docs/interfaces/：按实际改动同步当前契约说明。
无新设计模式；保持 Web/CLI → delivery → application → domain/ports ← adapters。

## 修改后自验证方式
后端使用 apps/backend/.venv/bin 下 Ruff check、Ruff format --check、Mypy、Pytest；先运行定向回归，再运行根 Pytest。前端 npm run lint、typecheck、build 及可执行的无浏览器回归；新增浏览器用例若当前隔离环境不可运行，明确记为未运行。回归尽量验证修复前失败、修复后通过。Docker/PostgreSQL/MinIO/真实模型未运行不得宣称通过。按路径暂存，检查每次提交内容，推送后核对 origin/main SHA 与可用 CI。

## 自验证情况
Pending。

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
