# Codex Windows 沙盒 ACL 修复行动文档

## 状态与情况说明

- 状态：已完成。
- 来源请求：用户确认执行已定位的 Codex Windows 沙盒修复。
- 范围：修复 `E:\9.1agent_exam\.git` 顶层目录的所有者异常，恢复默认沙盒命令与正常 Diff 审查链路。
- 已确认事实：默认沙盒执行 `Get-Location` 在进程创建前报 `helper_unknown_error: setup refresh had errors`；同一命令在沙盒外成功；当天沙盒日志持续记录 `deny ACE failed on E:\9.1agent_exam\.git: SetNamedSecurityInfoW failed ... 5`。
- 已确认根因：仓库根目录所有者为 `sss\YINGYI`，但 `.git` 顶层目录所有者异常为 `sss\CodexSandboxOffline`，导致沙盒设置程序无法写入用于保护 Git 元数据的 ACL（访问控制列表）。
- 明确排除：不递归修改 `.git` 子项所有者；不删除、移动或改写 Git 内容；不执行 `reset`、`checkout`、`clean`；不修改业务代码或架构方向；不读取 `.sandbox-secrets`。

## 实施措施

1. 记录修复前 `.git` 所有者、ACL、Git 状态和沙盒最小复现结果。
2. 仅将 `.git` 顶层目录所有者恢复为当前用户 `sss\YINGYI`。
3. 重新触发 Codex elevated Windows 沙盒设置，让 Codex 自行添加 `.git` 保护性 ACL。
4. 在默认沙盒中复测 `Get-Location`，成功标准为命令正常启动且返回 `E:\9.1agent_exam`。
5. 核对 `.git` 内容与 Git 工作区状态未丢失，并确认临时 `reconcile-*.patch` 为零。
6. 更新本行动记录及工作区迁移记录，使问题状态、证据和遗留风险保持一致。

## 受影响文件树

```text
E:\9.1agent_exam\
├── .git\
│   # 仅修复顶层目录所有者；Git 元数据内容保持不变；由 Codex 沙盒设置程序维护保护性 ACL
└── docs\actions\
    ├── 2026-09-04-codex-windows-sandbox-acl-repair.md
    │   # 本次根因、实施措施、验证证据和结果的权威行动记录
    └── 2026-09-04-workspace-path-migration.md
        # 补充英文路径并非根因以及本次 ACL 修复结果的链接/状态
```

本次不涉及设计模式、模块边界或代码依赖变化。

## 自验证方式

- 修复前后运行 `Get-Acl -LiteralPath 'E:\9.1agent_exam\.git'`，预期顶层所有者由 `sss\CodexSandboxOffline` 变为 `sss\YINGYI`。
- 通过 Codex 默认沙盒运行 `Get-Location`，预期退出码为 0，并输出 `E:\9.1agent_exam`。
- 检查当天 `.sandbox` 日志的最新设置刷新记录，预期不再出现 `.git` 的 `SetNamedSecurityInfoW failed: 5`。
- 运行 `git status --short` 与 `git diff --stat`，预期既有工作区改动保留，无意外删除或重置。
- 运行 `git diff --check`，预期退出码为 0。
- 检查仓库根目录 `reconcile-*.patch`，预期数量为 0。

## 自验证结果

- 已记录计划偏差：普通沙盒外进程执行 `icacls /setowner` 返回 `Access is denied`，处理 0 个文件；随后尝试通过 UAC 提升权限，但操作被取消，所有者仍未改变，未产生部分修改。
- 通过：经只读确认，独立 Codex 沙盒身份为 `.git` 当时的所有者 `sss\CodexSandboxOffline`。由该所有者在 `.git` 顶层临时授予 `sss\YINGYI` 一条 `FullControl`，处理 1 个文件、失败 0 个。
- 通过：非递归执行所有者恢复后，`.git` 顶层所有者从 `sss\CodexSandboxOffline` 变为 `sss\YINGYI`，处理 1 个文件、失败 0 个。
- 通过：所有者恢复后已移除临时 `sss\YINGYI FullControl` 显式授权，处理 1 个文件、失败 0 个；当前 ACL 中未残留该显式授权。
- 通过：Codex 随后的正常设置刷新为 `processed 3 write roots (read roots delegated); errors=[]`，并自动在 `.git` 上恢复了针对沙盒 SID 的保护性拒绝规则。
- 通过：默认沙盒中的 `Get-Location` 连续两次退出码为 0，并返回 `E:\9.1agent_exam`；原 `setup refresh had errors` 未再出现。
- 通过：默认沙盒中的 `git status --short` 成功列出既有修改与新增文件；未发现删除或重置。命令另有无法读取用户级 `.config/git/ignore` 的警告，不影响仓库状态读取，记录为遗留限制。
- 通过：`git diff --check` 退出码为 0；仓库根目录 `reconcile-*.patch` 数量为 0。
- 通过：使用正常补丁工具成功更新本既有行动文档与工作区迁移记录，说明既有文件写入链路已经恢复。
- 遗留风险：日志仍记录无法隐藏 `C:\Users\Default` 以及一次无法在该目录创建 cwd junction 的非致命警告；当前命令均能正常执行，但该兼容性警告尚未单独修复。
