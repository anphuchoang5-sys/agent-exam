# SWE-Gym 框架获取行动记录

## 状态和情况说明

- 状态：已完成
- 来源请求：用户已确认项目直接使用 SWE-Gym 开发，并要求先下载框架、再基于真实代码继续讨论架构。
- 当前事实：工作区中尚无 SWE-Gym 或 SWE-Bench-Fork 仓库；Git 已安装可用。
- 已确认决定：SWE-Gym 是项目的核心评测框架，不是仅供阅读的参考项目。
- 已获取版本：
  - SWE-Gym：`b681068ca20628c6987b7416cc4cf03f06b77ba5`
  - SWE-Bench-Fork：`242429c188fcfd06aad13fce9a54d450470bf0ac`
- 许可文件事实：SWE-Gym 仓库为 Apache License 2.0；SWE-Bench-Fork 仓库为 MIT License。
- 本次范围：获取 SWE-Gym 主仓库及其评测环境相关的 SWE-Bench-Fork 仓库，记录真实版本与结构。
- 明确排除：本次不下载完整任务数据集、不批量拉取 Docker 镜像、不安装依赖、不编写平台业务代码、不定稿架构。
- 待讨论：框架与自研 Runner、沙箱管控、轨迹存储、LLM Judge、人工抽检和前端的具体边界。

## 实施措施

1. 已在 `framework/` 下浅克隆 SWE-Gym 官方主仓库和 SWE-Bench-Fork 官方仓库。
2. 已检查两个仓库的远程地址、当前提交、工作区状态、许可证和顶层结构。
3. 已把实际提交版本、文件树、验证结果和发现的限制回填本行动记录。

完成标准：两个官方仓库均可在本地读取；来源和版本可追溯；未开始下载完整数据集、Docker 镜像或安装运行依赖。

## 实际修改的文件树

```text
E:\9.1实训\
├─ docs\
│  └─ actions\
│     └─ 2026-09-01-swe-gym-framework-acquisition.md
│        # 本次框架获取、版本事实和验证证据的唯一行动记录
└─ framework\
   ├─ swe-gym\
   │  # 直接使用的 SWE-Gym 核心框架；固定为本记录所列提交
   │  ├─ README.md
   │  │  # 框架定位、数据集、环境常量、镜像和复现实验入口的官方说明
   │  ├─ docs\
   │  │  # OpenHands 与 MoatlessTools 的官方复现实验说明
   │  ├─ scripts\
   │  │  # 训练、服务和 verifier 实验脚本；并非本平台现成的统一 Runner
   │  └─ LICENSE
   │     # Apache License 2.0 许可文本
   └─ swe-bench-fork\
      # 直接配套使用的可执行评测基础；固定为本记录所列提交
      ├─ swebench\harness\
      │  # Docker 环境构建、补丁测试、日志解析和确定性评分核心
      ├─ swebench\collect\
      │  # SWE-bench 风格任务收集和数据集构建工具
      ├─ tests\
      │  # 上游框架自身的测试
      ├─ setup.py
      │  # Python 包及依赖声明
      └─ LICENSE
         # MIT License 许可文本
```

当前阶段只获取上游框架，尚未新增适配器等项目代码，因此没有已经落盘的设计模式参与文件。后续架构候选会讨论“适配器模式”，但未经用户确认不会写成既定实现。

## 修改后自验证方式

1. 对两个目录执行 `git remote get-url origin`，期望均指向 SWE-Gym 官方 GitHub 组织。
2. 对两个目录执行 `git rev-parse HEAD`，记录精确提交哈希。
3. 对两个目录执行 `git status --short`，期望克隆后没有本地修改。
4. 列出两个仓库顶层文件，确认源码和文档可以读取。
5. 检查本次命令范围，确认没有执行数据集下载、Docker 拉取或依赖安装命令。

## 自验证情况

- `git remote get-url origin`
  - SWE-Gym：`https://github.com/SWE-Gym/SWE-Gym.git`
  - SWE-Bench-Fork：`https://github.com/SWE-Gym/SWE-Bench-Fork.git`
- `git rev-parse HEAD`
  - SWE-Gym：`b681068ca20628c6987b7416cc4cf03f06b77ba5`
  - SWE-Bench-Fork：`242429c188fcfd06aad13fce9a54d450470bf0ac`
- `git rev-parse --is-shallow-repository`：两个仓库均返回 `true`，符合只获取当前源码的范围。
- `git branch --show-current`：两个仓库均为 `main`。
- `git -c core.excludesFile= status --porcelain --untracked-files=no`：两个仓库均退出码 `0` 且无输出，未发现受跟踪文件修改。
- 顶层与关键文件检查：SWE-Gym 的 `README.md`、`docs/`、`scripts/` 可读取；SWE-Bench-Fork 的 `swebench/harness/`、`swebench/collect/`、`tests/` 可读取。
- 本地文件总量约为 SWE-Gym 4.78 MB、SWE-Bench-Fork 1.84 MB；本次未执行 Hugging Face 数据集下载、`docker pull` 或依赖安装。
- 限制：尚未安装依赖或运行上游测试，因此当前只验证了源码获取、来源、版本与完整可读性，不能把运行环境描述为已经可用。
