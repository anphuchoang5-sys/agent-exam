# 2026-09-23 将 agent+api 经 main 并入 lly/dev

## 状态与情况说明

状态：In Progress。

来源请求：S11 开工前必须确认 `agent+api` 与 `lly/dev` 已合并；预检证明 `origin/agent+api`、`origin/main` 与 `origin/lly/dev` 三条线均有独立提交。用户确认先完成合并，再开始 S11。

当前事实：`origin/agent+api=b425b65`、`origin/main=c0a34fd`、`origin/lly/dev=81a83eb`。`agent+api...main` 为 7/18 个独立提交，`agent+api...lly/dev` 为 7/38 个独立提交。本地 `lly/dev` 比远端落后 1 个文档提交。

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

若发生冲突，实际人工修改路径将在本节补充并说明取值依据。

## 自验证方式

- `git status -sb`、`git ls-files -u`、`git diff --check`：检查工作树、冲突与空白错误。
- 后端 Ruff、Mypy 和受影响测试；Web lint、typecheck 与相关测试：验证两条分支的代码组合。
- `git merge-base --is-ancestor origin/agent+api origin/main` 与对 `origin/lly/dev` 的同类检查：验证合并关系。
- `git rev-list --left-right --count HEAD...origin/<branch>`：验证推送后本地远端同步。

## 自验证情况

Pending。
