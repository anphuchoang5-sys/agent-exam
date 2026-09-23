# 2026-09-23 将 agent+api 经 main 并入 lly/dev

## 状态与情况说明

状态：Completed。

来源请求：S11 开工前必须确认 `agent+api` 与 `lly/dev` 已合并；预检证明 `origin/agent+api`、`origin/main` 与 `origin/lly/dev` 三条线均有独立提交。用户确认先完成合并，再开始 S11。

起始事实：`origin/agent+api=b425b65`、`origin/main=c0a34fd`、`origin/lly/dev=81a83eb`。`agent+api...main` 为 7/18 个独立提交，`agent+api...lly/dev` 为 7/38 个独立提交，本地 `lly/dev` 比远端落后 1 个文档提交。最终 `agent+api` 与 `main` 指向 `6e7690f`，`lly/dev` 的合并提交为 `f6926df`。

显式排除：本行动不运行 S11、不创建 Docker 资源、不读取真实凭据、不调用真实供应商。三个现有 worktree 的既有未跟踪文件均保留，不纳入提交。

## 实施措施

1. 在 `agent+api` 中合入最新 `origin/main`，如有冲突按现实代码与当前权威文档逐项解决。
2. 运行与合并影响相称的后端、Web、静态及差异检查；失败或跳过项如实记录。
3. 推送 `agent+api`，将其合入 `main` 并推送；不使用强制推送。
4. 将本地 `lly/dev` 快进至 `origin/lly/dev`，再合入最新 `origin/main`，验证并推送。
5. 用祖先关系和远端同步计数证明 `origin/agent+api` 已进入 `origin/lly/dev`，随后本行动结束，S11 另立行动。

完成标准：三个远端分支的目标提交关系可由 `merge-base --is-ancestor` 证明；没有未解决冲突；既有未跟踪文件仍在；验证结果和未运行项被准确记录。

## 受影响文件树

```text
docs/actions/2026-09-23-merge-agent-api-into-main.md  # 本轮合并、验证与分支关系证据
<origin/main 与 agent+api 的既有提交路径>             # 仅通过 Git 合并进入目标分支，不在本轮重写历史
```

实际冲突路径：

```text
docs/LLY/README.md  # 两侧均复制了已过期的任务状态；改为只指向权威架构、进度、计划和回执入口
apps/backend/src/eval_platform/adapters/execution/harbor_entry.py  # 合并多 ChatGPT 预设白名单与 S10 provider 专用入口
apps/backend/src/eval_platform/delivery/catalog_presets.py        # 生产预设改用共享轻量模块，同时保留内部测试身份常量
apps/backend/tests/providers/runtime/README.md                    # 保留较新 T2 测量约束并移除机器时点假设
docs/architecture/modules/execution-and-evaluation/ARCHITECTURE.md # 合并 Agent 预设与 S9/S10 产品接线现状
docs/interfaces/CODEX_AUTHENTICATION.md                           # 保留较新 S10 状态及 main 对令牌现实实现的修正
```

冲突取值依据：导航中的具体 T2/S9/S10 状态和历史测试数字都已被后续 `lly/dev` 事实覆盖，因此不任选旧侧；保留双方新增的计划与回执链接。代码以 `lly/dev` 已验证的 S10 provider 路径为主，同时纳入 `agent+api` 的三项生产 ChatGPT 预设白名单；二者以是否存在精确 provider runtime manifest 分流，不互相回退。当前文档同步描述这一现实组合。

## 自验证方式

- `git status -sb`、`git ls-files -u`、`git diff --check`：检查工作树、冲突与空白错误。
- 后端 Ruff、Mypy 和受影响测试；Web lint、typecheck 与相关测试：验证两条分支的代码组合。
- `git merge-base --is-ancestor origin/agent+api origin/main` 与对 `origin/lly/dev` 的同类检查：验证合并关系。
- `git rev-list --left-right --count HEAD...origin/<branch>`：验证推送后本地远端同步。

## 自验证情况

进行中：`origin/main` 合入 `agent+api` 时仅 `docs/LLY/README.md` 发生内容冲突；已按上述依据人工合并，`git ls-files -u` 为空。

合并提交前检查：

- 后端 `ruff check --no-cache src tests` 通过；Mypy `Success: no issues found in 187 source files`。
- Agent 目录与提供方定向回归 `174 passed, 2 skipped`；两项跳过分别是 Windows 目录 symlink 与 POSIX owner/权限位能力，不计为通过。
- Web 在排除既有未跟踪 `.next-codex-run/` 生成目录后 lint 通过，`npm run typecheck` 通过；目录/比较解析/可访问性/刷新失败/排行榜入口 7 个浏览器文件共 17 项通过。
- 首次 Ruff/Mypy/Pytest 因缓存或临时目录权限中止，改用无缓存参数和授权环境后取得上述结果。`npm ci` 因运行中的 Next 进程锁住 SWC 二进制失败；未停止既有服务，改为不改锁文件、不运行脚本地补齐锁文件指定的 `@axe-core/playwright@4.13.0` 后完成 Web 检查。
- 合入文件带来的两处 EOF 空行使 `git diff --cached --check` 报错；仅删除多余空行，未改正文或断言。
- `origin/main` 合入 `lly/dev` 时上述后五个路径发生冲突；人工合并后 `git ls-files -u` 为空。Ruff/format 通过（363 文件），Mypy 通过（193 个源文件）。后端组合回归先得到 `276 passed, 6 skipped, 2 failed`，两项失败都因 worktree 缺固定 Harbor 路径；把主工作区干净的固定提交 `6af8d6e...` 以目录联接提供给当前 worktree 后，两项原失败 `2 passed`。目录联接不复制、不修改或重建 Harbor。

最终 Git 证据：`origin/agent+api` 是 `origin/main` 与 `origin/lly/dev` 的祖先，`origin/main` 是 `origin/lly/dev` 的祖先，三项 `merge-base --is-ancestor` 退出码均为 0；本地 `lly/dev...origin/lly/dev` 为 `0 0`。三个 worktree 的既有未跟踪文件未纳入提交。

推送后的 Git 自动整理因 E 盘耗尽生成约 58 MiB 的失败临时 pack；同时仓库内误落有约 444 MiB 的可重建 npm cache。精确校验目标均在 `E:\9.1agent_exam` 后，只删除上述临时 pack 与 npm cache，未删除源码、证据、镜像、卷或用户文档；E 盘恢复约 505 MiB。磁盘余量仍偏低，是后续 S11 必须持续监控的基础设施风险。
