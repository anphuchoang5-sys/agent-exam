# 行动文档：初始化 AgentExam 主仓库并首次发布文档

## 状态与情况说明

- 状态：已完成
- 来源请求：用户授权创建 `.gitignore`，并把当前项目自有内容上传到 `https://github.com/anphuchoang5-sys/agent-exam.git`。
- 当前事实：
  - `E:\9.1实训` 尚未初始化为 Git 仓库。
  - `docs/`、`AGENTS.md`、`CONTEXT.md` 和正式选题文档属于应共享的项目资料。
  - `framework/` 是本地恢复的第三方上游源码，已确认不进入 AgentExam 主仓库；来源、固定提交和恢复方式由 [`DEPENDENCIES.md`](../dependencies/DEPENDENCIES.md) 维护。
  - 根目录存在空的 `.tmp/` 和 Word 临时锁文件 `~$26年秋季学期-软件项目实训选题目录-征求意见版.docx`，不属于项目成果。
- 已确认决定：创建项目级 `.gitignore`；排除第三方框架、秘密、依赖缓存、构建产物、运行数据、日志和编辑器临时文件；首次上传项目自有文档。
- 已核验远程状态：配置 Windows 本机代理后，`git ls-remote origin` 成功且无引用输出，证明首次推送前远程为空；本机 GitHub 认证可完成 HTTPS 推送。
- 明确排除：不删除任何本地文件；不上传 `framework/`、`.tmp/` 或 Word 锁文件；不安装依赖、不运行 Docker/Harness、不编写业务代码；不提交检测到的真实秘密。

## 实施措施

1. 只读取待提交范围，检查文件名和内容中是否存在常见密钥、令牌、私钥或密码赋值痕迹；输出仅报告文件路径，不回显秘密正文。
2. 创建项目级 `.gitignore`，覆盖当前第三方目录与未来 Python、Node、Docker、数据库、MinIO、Agent 日志和秘密文件。
3. 初始化根 Git 仓库，配置 `origin` 为用户给出的仓库；核验远程分支状态和认证。
4. 仅暂存未被忽略的项目自有文件，人工检查暂存清单，确保没有第三方源码、临时文件或秘密。
5. 创建首次提交并推送；核验本地 HEAD、远程 HEAD 和工作树状态一致。
6. 把实际提交、推送和验证结果写回本行动文档。

完成标准：远程仓库包含当前项目文档、协作规则、依赖说明与正式选题文件；不包含 `framework/`、`.tmp/`、Word 锁文件或已识别秘密；本地与远程提交一致。

## 实际修改的文件树

```text
E:\9.1实训\
├─ .gitignore
│  # 主仓库排除规则：第三方框架、秘密、缓存、运行数据、日志和临时文件
├─ .git\
│  # 本地 Git 元数据和远程配置；不上传为普通文件
└─ docs\actions\2026-09-02-initial-git-publish.md
   # 本次初始化、提交、推送和验证的可追溯记录
```

本次不引入代码设计模式。`.gitignore` 是版本控制入口的保护规则；`DEPENDENCIES.md` 是 `framework/` 恢复事实源，两者共同保证“第三方源码不入库但可复现”。

## 修改后自验证方式

1. 使用 `git check-ignore -v` 验证 `framework/`、`.tmp/`、Word 锁文件、`.env` 和典型私钥文件会被忽略。
2. 使用秘密扫描规则检查待提交文本，只报告命中文件路径；若发现可疑内容则停止提交并人工核对。
3. 使用 `git status --short`、`git diff --cached --name-only` 检查暂存范围，预期不含被排除路径。
4. 提交后使用 `git ls-tree -r --name-only HEAD` 检查提交树。
5. 推送后比较本地 `HEAD` 与 `git ls-remote origin refs/heads/main`，预期哈希完全一致。
6. 记录任何认证、网络或 Git 配置警告，不把失败推送描述为成功。

## 自验证情况

- 秘密扫描：高置信度内容规则检查私钥头、常见 GitHub/OpenAI/AWS/Slack 凭据格式，命中文件数为 0；检查带引号的 `api_key`、`access_token`、`secret`、`password` 赋值，命中文件数为 0。首次敏感文件名扫描命令因 PowerShell 参数多写一个 `-` 而失败，未计为通过；修正后重跑，候选文件数为 0。
- 扫描限制：暂存后再次按文件名报告高置信度秘密格式，命中文件数为 0。正则扫描不能替代专业秘密扫描器；正式选题 DOCX 为用户明确授权上传的二进制资料，不在文本正则扫描范围内。
- 忽略规则：`git check-ignore -v --no-index` 已证明 `framework/`、`.tmp`、`.env`、私钥文件、`node_modules`、`.next`、`infra/data` 和运行日志会被忽略。
- 文件边界：`git status --ignored --short` 显示 `framework/` 与 Word 锁文件为 `!!`；正式选题 DOCX、`docs/`、`AGENTS.md`、`CONTEXT.md` 均未被误忽略。
- 暂存范围：共 27 个文件，禁止路径命中数为 0；提交内容为 `.gitignore`、正式选题 DOCX、`AGENTS.md`、`CONTEXT.md` 和完整 `docs/`。
- Git 配置与网络：沙箱内访问 GitHub 被禁止，获得外部网络权限后首次直连仍被重置。本机 Windows 代理为 `127.0.0.1:7890`，Git 全局未配置代理；只在当前仓库 `.git/config` 设置该代理后远程访问成功，该机器配置不会进入提交。
- 首次提交：`f2f0e3f`（`docs: initialize AgentExam project`），包含 27 个文件、4006 行新增。
- 首次推送：`git push -u origin main` 成功，Git 报告 `main -> main` 并建立 `origin/main` 跟踪关系。
- 行尾提示：暂存时 Git 提示部分 Markdown 工作树将来可能由 LF 转为 CRLF；提交未失败、内容未丢失。本次未扩大范围创建行尾规范，后续出现 Docker/Linux 脚本前再决定是否增加 `.gitattributes`。
- 工具限制：初始化 `.git` 后，Windows 沙箱文件编辑助手无法刷新权限，标准 `apply_patch` 连续两次失败；随后三次 `git apply` 分别因补丁行数头错误或 PTY 匹配差异被拒绝，均未修改文件。第一次受控替换又因过严的末尾换行条件在写盘前停止。最终替换逐项验证旧文本只出现一次；所有失败均未记作通过。
- 范围检查：没有删除本地文件，没有上传 `framework/`、`.tmp/` 或 Word 锁文件，没有安装依赖、运行 Docker/Harness 或编写业务代码。
