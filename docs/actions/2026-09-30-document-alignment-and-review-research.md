# 文档差异修正与代码质量审查资料调研

## 状态与情况说明

- 状态：已完成（文档修正与资料调研；未开展产品代码审查）。
- 来源：用户要求先修正上下文恢复时发现的差异，再上网查找代码质量审查提示词或项目。
- 基线：`main@a550eb6ef6a544b9e42e0df3db50c1dec180723a`；本地领先 `origin/main` 7 个提交，开始时无已跟踪文件修改。
- 已核对：三项生产 Codex 配置、任务 05 内部测试身份的 Worker/Harbor 接线及 S11 历史验收、六个公开 provider 失败码、本地持久化与 Docker 迁移记录。
- 更正前轮判断：M1 01–11 的 `ready-for-agent` 标签有明确历史约定（任务 01 Comments：不增设完成标签，以验收项和行动证据判定完成），本次不改标签、不重新验收任务。
- 边界：仅修改当前文档和新增本轮行动/研究记录；不修改产品代码、不执行代码风格修复、不启动服务或评测、不读取凭据、不安装工具、不提交或推送。已结束 actions/research 不改写，其他 worktree 和两个指定未跟踪项不触碰。

## 实施措施

1. 已对照源码、配置与较新验收记录，修正当前架构、接口、运维及交接中的过期状态；历史时间段保留原记录。
2. 已按 `provider_access/failures.py` 补齐 `PROVIDER_UPSTREAM_FAILED`、对应短句及错误族，区分代码映射、浏览器夹具证据和真实供应商验收。
3. 已为当前任务 05 追加文档缺口已修正的说明，不改写历史 Comments。
4. 已使用 research 技能安排后台研究，只查第一方文档/仓库；保存带日期的研究记录，比较提示词、人工审查准则、静态工具及本项目适用范围，并编写可复制的中文只读审查提示词。未安装或接入服务。
5. 已核对差异、链接与错误码一致性；交付实际结果及仍未知的代码质量，不凭已有测试数字推断风格没有问题。

## 实际修改与新增文件树

```text
HANDOFF.md                                             # 当前恢复入口与本轮对账指针
docs/architecture/
  ARCHITECTURE.md                                      # 全局扩展阶段与实现树
  MODULE_CONTRACTS.md                                  # 内部执行合同及持久化状态
  modules/README.md                                   # 七模块状态索引
  modules/identity-and-membership/ARCHITECTURE.md       # 身份模块遗留边界
  modules/web-and-http/ARCHITECTURE.md                  # Worker接线与浏览器夹具覆盖边界
  modules/owner-host-runtime/ARCHITECTURE.md            # Docker/业务数据位置的权威指针
  modules/owner-host-runtime/ACTION_GUIDE.md            # 当前生命周期操作说明的路径边界
docs/interfaces/
  HTTP_API.md                                         # 六个失败码与当前公开执行边界
  HARBOR_EXECUTION.md                                  # 内部测试接线已实现与真实接入未实现的分界
docs/operations/LOCAL_DOCKER_ENVIRONMENT.md             # 当前路径与历史现场状态的区分
docs/dependencies/DEPENDENCIES.md                      # 已固定存储部署与未固定运行时的区分
.scratch/ui-catalog-providers/issues/
  05-fake-provider-secure-execution-chain.md            # 当前文档缺口收口说明
docs/actions/2026-09-30-document-alignment-and-review-research.md # 本轮措施与验证
docs/research/2026-09-30-code-quality-review-resources.md # 新增：第一方审查资料及建议提示词
```

沿用既有 Adapter（适配器）关系：Worker 组装 ExecutionBackend，Harbor 执行，PatchEvaluator 独立判卷；本轮仅修正这些关系的文档描述，不引入新的设计模式或接口。

## 修改后自验证方式

- `git diff --check`：无空白错误。
- 定向 `git diff`：只有列明的 Markdown 文件；既有已结束行动/研究文件无修改。
- 以只解析源码的 AST 检查比对 provider 公开失败码及短句与 HTTP 表格，六项均一致，不导入产品模块。
- 检查本轮新增/修改行中的本地 Markdown 链接目标可解析；核对三项配置、S9–S11、持久化和迁移的依据。
- 定向搜索被替换的过期句子应无残留；日期明确的历史段落不计为错误。
- 不运行单测、浏览器、数据库或 Docker：本轮为文档修正与资料调研，检查不应触发运行态。

## 自验证情况

- `git -c core.safecrlf=false --no-optional-locks diff --check`：通过，无输出、退出码 0。仅对本次命令关闭换行转换提醒，没有修改 Git 配置。
- 只读 AST 检查（`apps/backend/.venv/Scripts/python.exe -B -`）：六项 provider 公开码及短句与 HTTP 表格逐项相等；三项生产配置身份与模块索引描述一致。脚本不导入产品模块、不读取环境凭据。
- 修改行及两份新增文档的本地链接目标检查：38 项、缺失 0；新增文档行尾空白检查无问题。该检查验证目标文件存在，不声称验证了所有 Markdown 锚点。
- 定向过期句搜索：无匹配，`rg` 退出码 1 表示未找到，不是检查运行失败。日期明确的早期过程说明保留。
- Git 差异范围：13 个已跟踪 Markdown 文件，新增本轮行动和研究记录 2 份；无产品代码、既有已结束 actions/research 的修改。
- 编辑偏差：一次批量补丁返回上下文不匹配；只读核对发现首个运维文件已落盘，随后只补齐其余文件，未重复覆盖或回退现有内容。
- 已确认限制：新增上游失败码尚无单独浏览器覆盖；本轮未补测试或重跑历史验收。运行状态沿用 2026-09-29 记录，真实新供应商及远程验收缺口未关闭。
- 研究已完成并完整重读：`docs/research/2026-09-30-code-quality-review-resources.md`。主任务另行打开 Google 官方审查清单、PR-Agent 仓库与提示词源码复核。建议以人工审查准则和现有 Ruff/ESLint 等配置为基础；Import Linter、Semgrep CE 为按需补充，未安装、执行或外发项目代码。
- 尚未开展完整代码审查；不能据此断言当前代码存在或不存在风格/架构问题。下一步可按研究文档中的只读提示词分模块审查，再由用户决定修复范围。
