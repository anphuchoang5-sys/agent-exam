# 行动：Harbor Trial 收尾卡死诊断与有界清理

## 状态与情况

- 状态：**Completed**。
- 来源：用户要求监测最近评测、找出第五个 Trial 长期未完成的根因，并授权在必要时停止任务。
- 范围：诊断 2026-09-23 批次 `c9e9a414-ea5c-4317-af85-2e7fb680b743`，停止已确认卡死的 Harbor 子进程，让 Worker 收束批次；在现有 Execution Adapter 内为 Harbor 的 Docker `stop/down` 增加有界等待，并同步当前执行文档。
- 已确认事实：第五个 Trial 在 15:08:12 获准执行，Agent 日志在 15:09:47 停止，制品清单在 15:09:48 成功写出；该 Trial 禁用了 Harbor 内置判卷，之后只剩环境停止与 `result.json` 写入。Harbor 进程此后无 CPU 增量、无子进程、无结果文件，数据库心跳与状态不再变化。日志同时记录会话复制失败、截断 JSONL 和 `collect-patch.sh` 的 Git 写入失败；E 盘只剩约 505 MiB。
- 停止结果：15:52 按用户授权只终止 Harbor 子进程树，保留 Worker；15:53 Worker 将 Job 与 9 个 Run 收束为 `FAILED / EXECUTION_PIPELINE_INVALID`。进程中断前没有完整 Harbor Job 结果，因此半成品没有被发布为可信结果。
- 根因边界：直接缺陷是固定 Harbor 的 `DockerEnvironment.stop()` 调用 `docker compose stop/down` 时没有传入超时，外层平台仅对整个 9 Trial 进程设置约 8 小时 6 分钟的总兜底。低磁盘与 Trial 内写入失败是本次清理异常的高可信触发因素；在没有操作系统级调用栈或原始临时补丁的情况下，不把具体哪一次磁盘写入称为唯一已证实触发点。
- 明确不做：不执行全局 Docker prune，不删除历史 runtime、缓存、证据或固定镜像；不自动重试真实模型批次，不把失败 Trial 计为模型成绩。

## 实施措施与完成标准

1. 在项目自有 Harbor 生命周期 Adapter 中安装窄范围装饰器，只为 `docker compose stop/down` 补入既有进程终止宽限时间；显式调用方超时和其他 Compose 命令保持原值。
2. 清理命令异常时写入 Job 证据目录标记；外层 Adapter 读取标记、增加明确 warning，并沿用现有 project label 清理器精确复核该 Job 的资源。
3. 在 Harbor 子进程 Composition Root 启用该装饰器，保持应用层、数据库与 HTTP Interface 不变。
4. 增加回归测试，证明 `stop/down` 的隐式无限等待变为有界等待、显式超时不被覆盖、普通命令不受影响、重复安装幂等，且外层只复核当前 Job。
5. 同步执行模块架构、Harbor Interface 和本机 Docker 运维文档：记录本次真实故障、直接根因、收束结果、空间风险和未自动重跑边界。
6. 运行定向测试、Ruff、Mypy 与差异检查；只有实际通过的检查才记为通过。

完成标准：Harbor 正式入口会对清理命令应用有限超时；回归测试能在不启动 Docker/模型的情况下验证该合同；当前 Job 已终态且相关进程不存在；文档、代码和行动记录一致。

## 受影响文件树

```text
docs/actions/runtime/
  2026-09-23-harbor-trial-cleanup-timeout.md  # 本次诊断、实施和验证记录
apps/backend/src/eval_platform/adapters/execution/
  harbor_entry.py                             # Harbor 子进程 Composition Root，安装清理超时装饰器
  harbor/adapter.py                           # 识别子进程清理失败标记并精确复核当前 Job 资源
  harbor/lifecycle/cleanup.py                 # 现有清理实现；补充 Compose stop/down 有界装饰器
apps/backend/tests/unit/
  test_harbor_cleanup.py                      # 清理超时合同回归
  test_harbor_adapter.py                      # 清理失败标记与精确外层复核回归
docs/architecture/modules/execution-and-evaluation/
  ARCHITECTURE.md                             # 当前实现树与清理边界
docs/interfaces/
  HARBOR_EXECUTION.md                         # 当前执行事实、失败语义和真实故障记录
docs/operations/
  LOCAL_DOCKER_ENVIRONMENT.md                 # 本次容量快照与不自动清理边界
```

这里深化现有 `harbor/lifecycle/cleanup.py`，不新增业务 Module、Interface、数据库表或顶层目录。装饰器只适配固定 Harbor 的私有 Compose 执行接缝；外层 `cleanup_timed_out_projects()` 仍负责 Harbor 整体进程异常后的精确资源复核。

## 自验证方式

- `pytest apps/backend/tests/unit/test_harbor_cleanup.py apps/backend/tests/unit/test_harbor_adapter.py`
  - 期望：隐式 `stop/down` 获得固定超时；显式超时和 `up` 不变；现有 Adapter 合同继续通过。
- `ruff check` 与 `ruff format --check` 覆盖本轮 Python 变更。
- 对本轮 Python 源运行 Mypy。
- `git diff --check`；逐项核对实际变更树和文档链接。
- 只读复查 Job 已终态、Harbor PID 不存在、Worker 与项目服务是否仍在线。

## 自验证情况

- `pytest -o 'addopts=' -p no:cacheprovider --basetemp E:\9.1agent_exam\.tmp\pytest-harbor-cleanup-final-20260923b apps/backend/tests/unit/test_harbor_cleanup.py apps/backend/tests/unit/test_harbor_adapter.py`：**8 passed in 0.27s**。首次尝试因关闭覆盖率插件后项目默认 `--cov` 参数无法识别而未进入收集；覆盖默认 `addopts` 后通过，未把首次工具配置失败写成代码失败。
- `ruff check --no-cache`：**All checks passed**；`ruff format --check --no-cache`：**5 files already formatted**。
- `mypy --cache-dir=NUL`：**Success: no issues found in 3 source files**。
- `git diff --check`：通过；仅输出 Git 的 LF/CRLF 工作树提示，没有空白错误。变更后动态语言源文件为 172、115、200 行，均未超过项目默认 200 行指标。
- 文档相对链接逐项解析到现有文件；架构、Interface、运维和本行动记录对根因边界及停止结果一致。
- 运行状态复核：已卡死 Harbor 进程树不存在；Job `c9e9a414-ea5c-4317-af85-2e7fb680b743` 与 9 个 Run 已收束为 `FAILED / EXECUTION_PIPELINE_INVALID`，未提交为模型成绩。正式 Docker 中仍有项目 PostgreSQL、MinIO 两个容器运行。
- 容量只读复核：E 盘可用约 **1.11 GiB**；Docker 报告 Build Cache **2.463 GB 全部可回收**，镜像 **7.722 GB 可回收**。六道题基础镜像也被列为 dangling，因此不得直接使用无差别 `docker image prune`。本轮没有删除 runtime、缓存、镜像、容器或卷。
- 限制：没有在当前低磁盘条件下再次消耗模型额度运行真实 Docker 批次；本轮证明的是单元合同、静态类型和精确外层复核路径，真实九 Run 重跑须在 owner 人工释放并复核空间后进行。
