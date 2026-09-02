# 将 action-document skill 共享到项目

## 状态与情况说明

- 状态：已完成。
- 来源请求：用户确认采用仓库级共享方案，要求把本地 `action-document` skill 复制进项目目录，随后提交并推送一次。
- 范围：将完整 skill 放入仓库根目录的 `.agents/skills/action-document/`，记录并验证变更，提交到当前 `main` 分支并推送至 `origin/main`。
- 当前事实：本地 skill 包含 `SKILL.md` 和 `agents/openai.yaml`；项目尚无 `.agents/skills/` 目录；当前存在与本任务无关的未跟踪文件 `docs/actions/2026-09-02-harbor-runner-comparison.md`。
- 已确认决定：使用 Codex 支持的仓库级 `.agents/skills` 位置，让项目协作者克隆仓库后获得该 skill。
- 未知项：无影响实施的未知项。
- 明确排除：不修改 skill 内容，不修改业务代码，不提交或改动 `docs/actions/2026-09-02-harbor-runner-comparison.md`，不扩大为 plugin 发布。

## 实施措施

1. 创建本行动文档，先定义范围、文件树和成功标准。
2. 将本地 `action-document` skill 的全部文件复制到 `.agents/skills/action-document/`。
3. 核对源文件与仓库副本的文件清单和 SHA-256 哈希，确认内容完整一致。
4. 检查暂存差异，确保只包含本任务文件且不存在空白错误。
5. 更新本行动文档为真实完成状态，提交本任务文件并推送当前分支。

完成标准：仓库副本包含完整的两个 skill 文件，内容与本地源一致；提交不包含用户现有的无关未跟踪文件；提交成功推送到 `origin/main`。

## 受影响文件树

```text
E:\9.1实训\
├── .agents\
│   └── skills\
│       └── action-document\                 # 仓库级可发现的 action-document skill
│           ├── SKILL.md                     # 定义触发范围与行动文档工作流程
│           └── agents\
│               └── openai.yaml             # 定义显示名称、默认提示和隐式调用策略
└── docs\
    └── actions\
        └── 2026-09-02-share-action-document-skill.md
                                                # 记录本次复制、验证、提交与推送过程
```

本任务不涉及设计模式；`.agents/skills/action-document/` 是完整的可分发 skill 单元，`SKILL.md` 是核心指令，`agents/openai.yaml` 是可选界面与调用元数据。

## 自验证方式

1. 枚举源目录与仓库副本的相对文件路径；期望两边均只有 `SKILL.md`、`agents/openai.yaml`，且清单一致。
2. 使用 `Get-FileHash -Algorithm SHA256` 比较对应文件；期望两个文件的哈希分别一致。
3. 使用 `git diff --cached --check`；期望无空白错误。
4. 使用 `git diff --cached --name-status` 和 `git status --short`；期望暂存区仅包含本行动文档和两个 skill 文件，无关未跟踪文件仍未暂存。
5. 执行 `git commit` 与 `git push origin main`，并检查 `git status --short --branch`；期望本地分支与远端同步，且只剩原有无关未跟踪文件。

## 自验证情况

- 文件清单比较：已执行。源目录与仓库副本均为 `SKILL.md`、`agents/openai.yaml`，结果 `FILE_LIST_MATCH=True`。
- SHA-256 比较：已执行。`SKILL.md` 哈希均为 `E5D113AF3F7272D6A7F415C06C9CFA8914E02EFE5B132BF007CF50251F73ECD5`；`agents/openai.yaml` 哈希均为 `929FBAA12EC36A6D02BDC33D13207400557BCC47AC16B63B20B17605404625F0`，两个文件均为 `HASH_MATCH=True`。
- Git 暂存差异检查：已执行。`git diff --cached --check` 无输出，未发现空白错误；`git diff --cached --name-status` 仅列出本行动文档和两个 skill 文件。
- 范围隔离检查：已执行。无关文件 `docs/actions/2026-09-02-harbor-runner-comparison.md` 仍为未跟踪、未暂存状态。
- 交付说明：行动文档与 skill 同批提交；提交和推送在本文档定稿后执行，其实际结果以本任务最终 Git 输出为准。
- 遗留风险：未发现 skill 内容或仓库范围风险；若远端拒绝推送，将如实报告而不会改写验证结论。
