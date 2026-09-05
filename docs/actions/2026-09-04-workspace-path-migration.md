# 工作区英文路径迁移行动文档

## 状态与情况说明

- 状态：迁移已完成；复发的沙箱故障已定位并修复，英文路径仅用于排除 Unicode 路径因素。
- 来源请求：用户确认把整个项目从 `E:\9.1实训` 移动到无中文字符的英文路径；原计划目标为 `E:\agent_exam`，实际由用户重命名为 `E:\9.1agent_exam`。
- 目的：排除中文（Unicode）工作区路径对当前 Codex Windows elevated 沙箱初始化故障的影响，并降低后续 Docker、WSL 和脚本兼容风险。
- 已确认事实：旧目录已不存在；新目录及 `.git` 存在；迁移前的未提交文档修改和 Git 远程地址均已保留。
- 计划偏差：最终目录名为 `9.1agent_exam` 而非 `agent_exam`。两者都不含中文字符，本次按实际路径更新当前事实源。
- 已验证：文件系统迁移、Git 状态与远程仓库保持完整；迁移后一度通过默认沙箱探针，但 2026-09-04 的后续新窗口又出现 `setup refresh had errors`，因此英文路径只排除了一个可能因素，不能视为根治。
- 排除范围：不修改 Git 历史、不删除文件、不重置未提交变更、不移动 Docker 磁盘镜像、不读取或迁移任何账号凭据。

## 实施措施

1. 记录迁移计划并确认源、目标和当前 Git 状态。
2. 完全退出占用源目录的 Codex、编辑器和终端进程。
3. 将整个 `E:\9.1实训` 重命名为实际目标 `E:\9.1agent_exam`；不得复制后删除，也不得只移动部分文件。
4. 从新路径重新打开 Codex 项目，并确认 Git 仓库、未提交变更和远程地址保持不变。
5. 更新当前权威架构文档中的活动工作区根路径；历史行动文档保留其当时路径事实，不批量篡改历史记录。
6. 在新路径运行最小沙箱探针和文档检查；如仍失败，继续排查 Codex 版本或 Windows elevated 沙箱权限。

## 受影响文件树

```text
E:\9.1agent_exam\                   # 迁移后的唯一活动工作区根目录
├── .git\                            # 原仓库元数据与未提交状态原样保留
├── AGENTS.md                        # 项目协作规则，内容不因移动而改变
├── docs\
│   ├── actions\
│   │   └── 2026-09-04-workspace-path-migration.md
│   │       # 本次路径迁移、验证结果和遗留风险的行动记录
│   └── architecture\
│       └── ARCHITECTURE.md          # 更新候选文件树中的当前活动根路径
└── framework\                       # 第三方框架目录随工作区整体迁移
```

本次只改变工作区位置，不涉及设计模式或模块依赖变化。

## 自验证方式

- `Test-Path -LiteralPath 'E:\9.1实训'` 预期为 `False`。
- `Test-Path -LiteralPath 'E:\9.1agent_exam'` 预期为 `True`。
- 在新路径运行 `git status --short`，预期与迁移前的修改/未跟踪清单一致。
- 在新路径运行 `git remote -v`，预期仍指向原 AgentExam 仓库。
- 在 Codex 默认沙箱中运行最小输出命令，确认 `setup refresh had errors` 是否消失。
- 运行 `git diff --check`，预期无空白错误。
- 搜索活动架构/运维文档中的旧路径引用；历史行动文档中的旧路径作为历史事实保留。

## 自验证结果

- 通过：`E:\9.1实训` 返回 `False`，旧路径已不存在。
- 通过：`E:\9.1agent_exam` 存在，且 `git rev-parse --show-toplevel` 返回 `E:/9.1agent_exam`。
- 通过：分支仍为 `main`，远程 `origin` 仍为 `https://github.com/anphuchoang5-sys/agent-exam.git`。
- 通过：迁移前记录的 4 个已修改文档和 5 个未跟踪文档均仍存在；没有观察到迁移导致的 Git 状态丢失。
- 通过：当前架构文件树已更新为 `E:\9.1agent_exam`；活动架构、接口、依赖和运维文档中未发现旧路径引用。历史行动文档中的旧路径按历史事实保留。
- 通过：Codex 默认沙箱中的最小命令输出 `sandbox-probe-ok`，此前的 `setup refresh had errors` 未复现。
- 通过：`git diff --check` 退出码为 0，未发现空白错误；仅出现现有 Markdown 文件未来可能由 LF 转为 CRLF 的 Git 提示。
- 限制：当前这条旧 Codex 任务的写入授权仍绑定迁移前目录，因此本次文档补丁需要显式授权；从新路径重新创建/打开的任务才能彻底刷新工作区写入边界。

## 后续复核：故障在英文路径重新出现

2026-09-04 从 `E:\9.1agent_exam` 打开的后续任务中，以下只读默认沙箱命令均在真正启动前失败：

- 读取用户附件；
- `Get-Location`；
- 通过规范补丁工具读取并更新既有文件。

共同错误仍为 `windows sandbox failed: helper_unknown_error: setup refresh had errors`。相同窗口提升权限后，普通只读 PowerShell 命令、`codex --version` 和 `codex exec --help` 均可运行，后两者退出码均为 0。

后续诊断确认直接根因是 `.git` 顶层目录所有者异常变成 `sss\CodexSandboxOffline`，导致沙箱设置程序添加 Git 元数据保护 ACL 时收到 `SetNamedSecurityInfoW failed: 5`。恢复所有者并清除临时授权后，默认沙箱探针及设置刷新均恢复成功。完整措施、失败分支、验证证据与遗留风险见 [Codex Windows 沙盒 ACL 修复行动文档](./2026-09-04-codex-windows-sandbox-acl-repair.md)。因此，中文路径已被排除为本次复发故障的根因。
