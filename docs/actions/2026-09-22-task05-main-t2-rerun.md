# 任务 05：main 分支最小 T2 复测

## 状态与情况

- 状态：**用户暂停**；本次 `main` 复测尚未启动 Harbor 资源。用户随后改为只要求对上一轮侧车退出 127 补取诊断证据；不继续本行动的整套测试。
- 来源：用户 2026-09-22 要求“切到main分支再次测试”。继续沿用用户同日授予的最小 T2 与硬边界：只允许 Harbor 固定、无标签、`--rm` 内核探针；其他持久资源仅限 `agentexam.task=05` 的 `agentexam-t05-topology` 项目；只清理本次项目，不重建 Harbor/镜像、不删其他项目资源、不读真 Key、不调用真实供应商或放宽公网。
- 工作区：独立 `runtime/main-t2-verify`，`main` 与 `origin/main` 均为 `e6a7138d93d3f10dd8e2ebf17b51030d600f69ec`；主工作区并行改动和 `lly/dev` 上一次失败记录不在本轮修改范围。固定 Harbor 仍从仓库忽略的 `framework/harbor` 只读复用。
- 已知风险：前一次 `lly/dev` 的同形态启动在 Harbor 内置侧车退出 127 后停止，原因未证实。重测不能预设成功；若同样在 `up --wait` 失败，保留原始输出、走仅本项目的标准拆除并停止，不修改断言或侧车。

## 实施措施与完成标准

1. 检查 `main` 工作树、固定 Harbor 版本和镜像缓存；保证项目名当前无资源，核对构造期内核探针 argv 无宿主 Docker 套接字/端口/写入挂载。
2. 在本 worktree 的 Git 忽略证据目录准备与上一轮同义的 `extra_docker_compose` 和薄驱动，使用唯一 scope `t05-harbor-main-20260922-01`。静态合成配置应恰好有 `internal`、`egress` 两网络；主容器只接 internal，代理双网，假上游只接 egress；所有服务和网络有任务/轮次标签，无宿主发布端口和宿主写入挂载。
3. 通过固定 Harbor `DockerEnvironment` + 本次 `TrialPaths` 启动。启动成功才以实际 `env.exec` 执行七组对照，保存命令、退出码、stdout、假上游日志与运行期 `docker inspect`。不接 Codex CLI、真实模型或真实凭据；不把环境层证据称作完整 `Trial.run()`。
4. 无论成功或失败，拆除前后保存镜像/卷清单；仅调用该环境的 `stop(delete=True)`，捕获实际 Compose argv，并按项目名和本轮标签复核残留 0。任一硬边界或断言失效立即停止后续验收。
5. 更新本行动文档，分清启动失败、断言失败和已证实项；不改既有历史行动记录。

## 受影响文件树

```text
docs/actions/
  2026-09-22-task05-main-t2-rerun.md  # 本次 main 复测行动与实际结果
.tmp/t05-harbor-minimal/t05-harbor-main-20260922-01/  # Git 忽略的本轮原始证据
  extra-compose.yaml                    # Harbor 调用方配置，双网络与标签
  probe.py                              # 测试驱动，记录实际 Harbor argv/inspect/断言/清理
  *.json                                # 原始清单、命令、输出和核验记录
framework/harbor/                       # 固定依赖，只读复用，不修改/重建
```

测试驱动调用既有 Harbor Docker 环境边界，Compose 文件仅为调用方覆盖配置；没有新增产品模块、接口、数据库或设计模式。

## 自验证方式

- `git branch --show-current` / `git status --short --branch` / 提交比对；Docker 镜像缓存与项目残留预检；`docker compose config` 静态边界检查。
- 固定 Harbor 真正执行后记录 `up` 原始结果、七组命令与输出（若启动成功）、运行期网络与容器 inspect（若存在）；任何未运行/缺失明确标注。
- Harbor 标准拆除原始 argv、拆除前后镜像/卷完整清单和差异，按项目与本轮标签查询容器、网络、卷均应为空；`git diff --check`。

## 自验证情况

未执行 Harbor 测试。已核对独立 worktree 初始干净、分支 `main` 与本次获取的 `origin/main` 同提交；创建了本行动文档和 Git 忽略的空证据目录，尚未写 Compose/驱动或启动 Docker 资源。用户明确暂停后，本行动停止；后续诊断属于另一独立范围。
