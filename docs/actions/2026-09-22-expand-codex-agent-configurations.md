# 扩展受控 Codex Agent 配置

## 状态与情况说明

状态：In progress（2026-09-22）。

来源请求：在已推送的 `agent+api` 分支上扩展 Agent 配置，新增 `gpt-5.6-luna / low` 与 Sol 中等推理配置，并允许消耗额度进行全量测试。用户已确认第二项的准确模型 ID 为 `gpt-5.6-sol / medium`，不使用不存在的 `gpt-5.5-sol`。OpenAI 官方 [Luna](https://developers.openai.com/api/docs/models/gpt-5.6-luna)、[Sol](https://developers.openai.com/api/docs/models/gpt-5.6-sol) 文档支持对应模型和推理档位；账号在固定 Codex CLI 及本机 ChatGPT 登录下的实际可用性仍待实测。

任务开始前事实：生产 `AGENT_PRESETS` 只有 Terra/medium；`AgentRegistry` 已支持受控预置登记，Job 会冻结配置并映射至固定 Harbor/Codex；Web 的登记按钮和客户端写死旧预置。正式执行使用 owner 的 `chatgpt_auth_json`，本任务不改认证身份、数据库结构、公开路由、提供方代理或资源上限。运行目录已有六题，磁盘余量和完整 Trial 能否承载须在实际运行前复查。已结束行动记录作为历史档案不反向修改。

实施中补查：`harbor_entry.validate_agent_mode` 另有只接受单个 Terra/medium 的 `_FIXED_CODEX` 常量；仅新增目录预置无法真正运行新型号。须在既有执行 Adapter 内复用生产受控预置生成精确允许运行的配置集合，继续拒绝任意模型、参数和混合 NOP。

## 实施措施

1. 在现有生产预置表新增两项，同用固定 Codex `0.153.0` 和既有 owner 登录身份；旧预置与指纹保持不变。执行入口以同一受控预置为允许集合，允许三种预置的任意非空且不重复子集，不放开任意模型。
2. 复用现有登记 API，在 Web 提供明确的三个固定预置选择；保持 owner 权限及未知预置失败关闭。
3. 对齐当前目录架构、HTTP 契约与交接中的预置状态；不新增顶层 Module、Interface 或表。
4. 运行预置登记、配置冻结/Harbor 映射、Web 选择和既有门禁；随后先验证两项新模型的固定 CLI 可用性，再在资源允许的条件下运行已授权的真实全量评测，按实际结果记录额度消耗、失败和证据。

完成标准：两项新配置在生产受控预置中可由 owner 分别登记，Web 能选中并如实显示，评测冻结的模型与推理档位传至固定 Harbor/Codex；相关自动检查通过。真实模型与六题评测以实际运行结果报告，不能把未跑、受限或失败的项记为通过。

## 需要修改的文件树

```text
apps/backend/src/eval_platform/delivery/agent_presets.py            # 仅依赖领域模型的三项生产固定配置，目录与独立 Harbor 运行时共用
apps/backend/src/eval_platform/delivery/catalog_presets.py          # 题目和测试配置；导入生产固定配置供现有 AgentRegistry 登记
apps/backend/src/eval_platform/adapters/execution/harbor/config_mapper.py # 将单一 Agent 配置映射为 Harbor 固定形状，供执行入口复用
apps/backend/src/eval_platform/adapters/execution/harbor_entry.py    # 启动前按生产受控预置拒绝未登记模型、档位和参数
apps/backend/tests/catalog/agent_identity/test_production_presets.py # 三项生产预置的 owner 登记与 Harbor/Codex 映射核对
apps/web/src/lib/catalog-client.ts                                   # 固定预置 ID 的登记请求参数
apps/web/src/features/catalog/agents.tsx                             # owner 选择预置和登记界面
apps/web/tests/catalog.spec.ts                                       # 浏览器选择和登记请求核对
docs/architecture/modules/catalog-and-configuration/ARCHITECTURE.md # 当前配置目录与文件树
docs/architecture/modules/execution-and-evaluation/ARCHITECTURE.md # Harbor 启动前受控模型校验与数据流
docs/interfaces/HTTP_API.md                                          # 既有登记接口允许的固定预置
docs/interfaces/CODEX_AUTHENTICATION.md                              # 运行绑定历史与当前三项受控配置的区别
docs/interfaces/HARBOR_EXECUTION.md                                  # 执行接口的历史单配置描述与当前白名单
HANDOFF.md                                                            # 当前接续入口与运行边界
docs/actions/2026-09-22-expand-codex-agent-configurations.md        # 本次措施、偏差与验证证据
.tmp/agent-presets-real-probe.py                                      # 忽略的单次真实模型/Fork 探针入口；不进入 Git
.tmp/agent-presets-full-batch.py                                      # 忽略的十次顺序试跑与受控空间回收入口；不进入 Git
.tmp/owner-register-new-agents.ps1                                    # 忽略的 owner 交互式登记脚本，密码只从本机终端输入
.tmp/verify-new-agents-ui.mjs                                         # 忽略的真实网页登录与向导选择核对脚本
runtime/prototype/agent-presets-20260922/                             # 忽略的逐次受控运行证据；不进入 Git
```

模式仍为现有 Registry + Adapter：`agent_presets.py` 提供有限身份，`catalog_presets.py` 与 Harbor 运行入口共同导入；`AgentRegistry` 校验并登记，Job 冻结后由现有 Harbor Adapter 将模型和推理档位交给固定 Codex。Web 仅提交预置 ID，不承载任意模型名、URL 或认证字段。首次真实运行发现 Harbor 的隔离 Python 环境没有后端服务使用的 `botocore`；新增的轻量文件把生产预置从带存储依赖的目录装配文件中分离，避免仅为启动校验而加载 MinIO。

## 修改后自验证方式

- 后端：定向目录/配置、Job 冻结与 Harbor 映射测试；Ruff、Mypy 和默认全量 Pytest。成功标准是新增预置、旧预置及失败关闭均通过，固定映射精确传递新模型与档位。
- Web：类型检查、lint、构建与目录浏览器测试，再运行全量浏览器套件。成功标准是 owner 能选三项，两个新项请求体使用各自 ID，协作者无登记权限。
- 运行态：只读核对固定 CLI、owner 目录、六题镜像、队列和磁盘；模型可用性及真实评测按批准路径逐级运行。只有完成的 Run 和报告可作为真实通过证据，记录 Job/Run 数、受控失败码和资源限制；不自动重试旧失败批次。
- 提交前核对 `git diff --check`、当前文档链接和工作区范围；临时证据与凭据不提交。

## 自验证情况

进行中。本行动开始时已确认远端 `agent+api` 与本地 `2381480` 一致，工作区只剩三个未跟踪临时产物，均须保留且不提交。用户确认的两个准确模型 ID 已在 OpenAI 官方文档核对；后续真实 CLI、目录登记与网页核对结果按时间顺序记录如下。

- 已增加两项生产预置、Web 选择与独立的生产预置→owner 登记→Harbor 映射测试。首次 Pytest 因默认 `.coverage` 被系统拒绝而未收集；第二次改覆盖率路径仍因本机临时目录拒绝访问在 setup 阶段报错。改用已核对为空的工作区专用 `--basetemp` 并在获准权限下运行，新增测试 **3 passed**。前两次是测试运行环境问题，不是断言失败；完整门禁仍待执行。
- 深查发现 `harbor_entry.py` 曾只允许 Terra/medium，新增目录预置不能启动真实 Trial；已改为从同一 `AGENT_PRESETS` 生成运行白名单。三项生产预置、既有 Harbor 映射、Codex guard 和网络合同的定向回归 **43 passed**，包含未知模型/档位、重复配置与混合 NOP 拒绝。
- 首轮改动时后端默认全量 Pytest **619 passed / 102 skipped**；这是补上 Harbor 启动白名单之前的结果，最终代码须再跑一次。Ruff 全量检查通过、格式 347 文件通过，Mypy 186 个源文件通过，同样需按最终代码重查。
- Web 类型检查、排除原有未跟踪 `.next-codex-run` 生成文件后的全量 lint、系统 Chrome 下 27 个 spec 文件的浏览器套件均通过。Playwright 默认浏览器缺失时首次 3 个测试均在启动前失败；改用已安装 Chrome 后定向 3 项与全量套件通过。Next 首次构建在遥测配置跨盘 rename 处失败；以 `NEXT_TELEMETRY_DISABLED=1` 重跑生产构建通过。
- 宿主机旧版 Codex CLI `0.142.0` 的 Luna/low 最小真实请求未取得回复：其 WebSocket 到 `chatgpt.com` 被拒绝，尝试在第二次重连后中断；属于宿主网络/旧 CLI 探针限制，未证明模型不支持。正式运行固定的是 `0.153.0`，其可用性仍待实测。
- 真实运行前只读核对：六道任务固定摘要镜像 `docker image inspect` 为 **6/6**，专属 PostgreSQL 与 MinIO 运行，活动 Job 为 0；固定 Codex 归档和 owner 私有认证文件存在且认证文件大小在既有门禁范围内，未读取正文。E 盘空闲约 3.56 GiB，需逐次监测而不能预先声称可承载 12 个完整 Trial。
- 最终后端回归（新增运行白名单后）**620 passed / 102 skipped**；Ruff 检查及格式通过（347 文件），Mypy **186 source files** 通过。此结果发生在下述轻量预置文件拆分之前，拆分后的最终回归还需重跑。
- 固定 CLI 的首个 Luna/low 单题探针 `new-agent-009c2773c997` 进入 Harbor 启动，但 `harbor-process.json` 退出码 1，`execution.json` 为 `INFRASTRUCTURE_INTERRUPTED` / `HARBOR_JOB_RESULT_MISSING`；受控提取的 stderr 错误类型为 `ModuleNotFoundError: No module named 'botocore'`，未进入 Codex 请求，不计作模型可用性或题目结果。已拆分轻量生产预置，Harbor 自身 Python 能导入三个模型配置；须重新运行真实探针。首试解包占用约 0.31 GiB，E 盘空闲降至约 2.93 GiB；重试前仅清理该次已失败探针的可重建 Codex 解包副本，保留诊断证据。
- 拆分后 Harbor 自身 Python 能加载三项完整映射；相关定向测试 **43 passed**，Mypy **187 source files** 通过。最终默认全量 Pytest **620 passed / 102 skipped**，Ruff 导入排序与换行格式修正后检查通过，**348 文件已格式化**。新增三预置同一 Harbor 矩阵回归单独 **5 passed**。
- Luna/low 单题探针 `new-agent-45179bd8dc5e` 与 Sol/medium 单题探针 `new-agent-06808310b382` 均成功完成固定 Harbor/Codex/Fork 链路，`python__mypy-15413` 均判卷 `resolved=true`。它们在忽略的原型证据目录中有 `request.json`、`execution.json`、`evaluation.json` 与 `result.json`，不写正式 Job 或目录数据库；不把此结果当作正式提交。每次结束后仅删除经路径核验的可重建 Codex 解包副本，保留运行证据。
- 真实试跑全部完成：每项新配置各跑六道已核验题，**12/12** 次固定 Harbor/Codex/Fork 执行与独立判卷完成；Luna/low 解出 **3/6**，Sol/medium 解出 **6/6**。`resolved=false` 是该次补丁未解决题目，不是基础设施失败。独立读取私有原型目录的 `request.json`、`execution.json`、`result.json` 核对为 **12 completed / 1 failed / 9 resolved**；额外的 `failed` 是前述模型启动前缺 `botocore` 的首次探针，不混入 12 次模型结果。每个完成 Trial 都有 patch，终止原因为 `completed`，但 12 次都带有已知 `TRAJECTORY_UNAVAILABLE`，`trajectory_ref` 缺失；至少抽查的 Sol 结果 `usage=null`，不能据此报告精确 Token 或费用。运行结束后题目 Docker 容器均已清理，E 盘余约 **3.10 GiB**。结果是隔离原型证据，不是数据库内正式 Job/Run，也未在网页提交评测。

| 题目 instance | Luna/low | Sol/medium |
|---|---|---|
| `python__mypy-15413` | resolved | resolved |
| `python__mypy-15131` | 未解决 | resolved |
| `python__mypy-15139` | 未解决 | resolved |
| `python__mypy-15184` | resolved | resolved |
| `python__mypy-15208` | resolved | resolved |
| `python__mypy-15876` | 未解决 | resolved |

- 切换运行服务前确认正式活动 Job 为 0。更新版后端先在备用端口 8001 返回 HTTP 200，再替换 8000 的旧进程并再次取得 HTTP 200，备用实例已关闭；旧 Worker 的两个 Python 进程被定向停止，新 Worker 的两个 Python 进程运行且 stderr 文件为空。Web 旧版为 `next start`，更新版生产构建先在备用端口 3001 返回 HTTP 200，再替换 3000 的旧进程；新版主页 200、经 Web 转发的未登录 Agent API 401，备用实例已关闭。2026-09-23 00:09 +08:00 复查：后端 200、Web 200、新 Worker Python 进程两个，专属 PostgreSQL/MinIO 运行，正式活动 Job 0。实际 owner 登录、两个新配置登记及网页向导选择仍待执行，不把无登录 HTTP 检查充作该验收。已准备本机交互式 owner 登记与浏览器核对脚本并通过 PowerShell/Node 语法检查；脚本尚未输入凭据或运行登记。
- Git：15 个明确文件以 `877b7b1` 本地提交，提交前 `git diff --cached --check` 通过；原有三个未跟踪临时产物仍保留。提交前已核对远端 `agent+api` 为 `2381480`，推送该新提交时自动审批以「远端归属未确认」拒绝创建进程，没有发生远端写入；已向用户请求对具体 GitHub 目的地的确认，不经其他入口绕过。
- 2026-09-23 续查当前 owner 目录仍只有启用的 Terra/medium；交互脚本尚未运行。准备投入使用前发现脚本把 POST 响应的 `agent_configuration_id` 误当成预置 ID 比较，而 `AgentRegistry.register` 实际生成 UUID；这会在首项成功登记后误报失败并停止第二项。已改为检查响应 UUID、模型、版本、提供方、推理档位及启用状态，按 UUID 核对 GET 列表中两条不同记录。PowerShell 语法解析、独立 UUID 查找表达式和浏览器脚本 Node 语法检查通过；生产预置 HTTP 回归新增响应 UUID 与目录列表同 ID 断言后 **5 passed**，Ruff 全量检查和 348 文件格式门禁通过。尚未用 owner 凭据实跑，不能把这些检查当作真实登记通过。
- 2026-09-23 owner 通过现有登录和登记 API 实跑交互脚本：Luna/low 与 Sol/medium 均返回 201，响应身份检查及按返回 UUID 的目录回查通过。随后只读查询当前 PostgreSQL，确认 Terra/medium、Luna/low、Sol/medium 三条记录均启用且模型、推理档位正确。浏览器自动核对在 `browser_verify` 阶段失败，因此当前只把后端 owner 目录登记记为通过，不能把真实网页选择记为通过；未提交正式 Job。临时浏览器脚本已增加不含凭据的步骤名和 API 状态诊断，待 owner 再次在本人终端运行后定位并完成最后验收。
