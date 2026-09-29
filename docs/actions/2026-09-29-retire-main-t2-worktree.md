# 2026-09-29 退役 main T2 验证工作树并切回 main

## 状态与情况说明

状态：Completed。

来源请求：用户确认不再需要 `E:\9.1agent_exam\runtime\main-t2-verify` 工作树；此前目标是把 `agent+api` 成果合入本地 `main` 并在主工作区切到 `main`。

现场事实：最新 `origin/main@f1f97b5` 是 `agent+api@2d6a712` 的祖先，后者多 5 个提交，可以直接快进，不需要内容合并。目标工作树占用本地 `main@6e7690f`，其中只有一份未跟踪的暂停行动记录 `docs/actions/2026-09-22-task05-main-t2-rerun.md`，没有其他未跟踪或忽略文件。主工作区另有 npm 缓存和无关演示文稿，均不在本轮处理范围。

## 实施措施

1. 在修改工作树前记录目标路径、分支关系、未跟踪文件和 SHA-256。
2. 把唯一未跟踪的暂停行动记录复制到当前项目同路径，复核源文件与副本哈希一致。
3. 提交两份行动记录，使待保留历史进入 `agent+api` 的可追踪提交。
4. 使用 Git 原生 worktree 移除命令退役 `runtime/main-t2-verify`；受管归档工具在本会话不可用，不使用文件系统递归删除替代 Git 生命周期操作。
5. 在工作树释放后将本地 `main` 快进到 `agent+api`，在主工作区切换到 `main`。
6. 更新本行动的实际结果并提交；核对分支、工作树列表、提交祖先关系和保留文件哈希。

完成标准：目标 worktree 不再登记且目录不存在；暂停行动记录进入 Git；当前工作区分支为 `main`；本地 `main` 包含 `agent+api` 全部成果；既有未跟踪缓存和演示文稿未改动；不推送 `origin/main`。

## 实际修改的文件树与职责

```text
HANDOFF.md                                      # 当前分支、worktree 与远端发布状态
docs/actions/
├── 2026-09-22-task05-main-t2-rerun.md       # 从退役 worktree 保留的暂停复测历史
└── 2026-09-29-retire-main-t2-worktree.md    # 本轮退役、分支移动与验证记录
```

不新增业务 Module、Interface、数据库表或设计模式，只处理项目治理记录与 Git worktree 生命周期。

## 自验证方式

- `Get-FileHash` 比较暂停行动记录复制前后的 SHA-256。
- `git status --short --branch`、`git diff --check` 与按路径 diff 检查提交范围。
- `git worktree list --porcelain` 确认目标登记消失，`Test-Path` 确认目标目录不存在。
- `git branch --show-current`、`git merge-base --is-ancestor agent+api main` 和提交号核对本地 `main` 已包含分支成果。
- 保持 `origin/main` 不变，不执行 push。

## 自验证情况

- 退役前目标 worktree 只有一份未跟踪文件、0 个忽略文件。
- 暂停行动记录复制前后 SHA-256 均为 `3B7CFA1954738B2558CF6B7E1427EE37902B1104687829B36C845DE82FDC7E57`。
- 受管 worktree 归档工具在本会话不可用；已改用 Git 原生 `worktree remove --force`，目标登记和 `E:\9.1agent_exam\runtime\main-t2-verify` 目录均已消失。首次严格路径检查只因 Git 正斜杠与 PowerShell 反斜杠格式不同而停止，未删除内容；规范化分隔符后完成受控移除。
- 主工作区已切换到 `main`，并从 `6e7690f` fast-forward 到包含 `agent+api@442a3ba` 全部成果的提交；祖先检查通过。
- `origin/main` 保持 `f1f97b5`，本轮未向远端 `main` 推送。npm 缓存和无关演示文稿仍未跟踪且未改动。
