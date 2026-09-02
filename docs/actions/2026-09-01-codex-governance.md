# Codex 协作规则与行动文档 Skill 落盘

## 状态与情况说明

- 状态：已完成
- 日期：2026-09-01
- 来源：用户已经明确给出 Codex 协作规则，并指出讨论阶段不应阻止已确认规则落盘。
- 范围：创建项目级 `AGENTS.md`、用户级 `action-document` Skill，以及本次变更的行动记录。
- 明确排除：不创建或定稿业务架构文档，不编写项目业务代码。
- 团队事实：名义成员 5 人，实际有效开发力量约 2.5 人；该事实等待后续架构讨论时进入架构文档的权威位置。

## 实施措施

1. 将已确认的协作原则整理为 Codex 可自动发现的项目根目录 `AGENTS.md`。
2. 创建用户级 `action-document` Skill，固化行动文档的创建、持续更新和收尾规则。
3. 校验 Skill 的结构、YAML 元数据和必填字段。
4. 复核规则是否覆盖接口查证、业务确认、文档唯一事实源、代码架构指标、坏味道报告和验证纪律。

## 需要修改的文件树

```text
E:\9.1实训\
├── AGENTS.md
│   └── Codex 自动读取的项目协作规则；本项目协作规范的唯一事实源。
└── docs\actions\2026-09-01-codex-governance.md
    └── 本次规则落盘的可追溯行动记录。

C:\Users\YINGYI\.codex\skills\action-document\
├── SKILL.md
│   └── 行动文档工作流定义；在项目文件修改类任务中自动触发。
└── agents\openai.yaml
    └── Skill 的界面元数据与自动调用策略。
```

设计关系：`AGENTS.md` 是稳定规则的唯一事实源；`action-document` Skill 是执行流程；本文件是一次具体执行实例。三者职责不同，不复制维护同一类状态。

实施偏差：最初按官方项目级位置创建 Skill，但当前 Codex Desktop 在含中文路径的 `.agents/skills` 下刷新失败。Skill 校验通过后已迁移到本机可正常发现的用户级目录；没有改变 Skill 内容和适用范围。

## 修改后自验证方式

1. 运行 Skill Creator 的 `quick_validate.py` 校验用户级 `action-document` Skill。
2. 检查三个目标文件及 `openai.yaml` 均存在且非空。
3. 搜索 `AGENTS.md` 的关键规则，确认用户给出的约束均已覆盖。
4. 确认没有创建架构文档或业务代码。

## 自验证情况

- Skill 结构校验：通过。本机环境执行 `quick_validate.py` 返回 `Skill is valid!`。
- 环境差异：沙箱内 Python 缺少 `yaml` 包，首次迁移后校验器因 `ModuleNotFoundError` 未能启动；改用已具备依赖的本机 Python 重新运行后通过。该失败没有被记作通过。
- 文件存在性：`AGENTS.md`、`SKILL.md`、`agents/openai.yaml` 和本行动记录均存在且非空。
- 规则覆盖检查：已检出接口查证、业务确认、文档唯一事实源、200/250 行限制、每层 8 个文件、坏味道处理和验证纪律。
- 范围检查：`ARCHITECTURE.md` 数量为 0；没有创建业务代码或定稿架构。
- 刷新故障清理：迁移后的空项目 `.agents` 目录已删除，普通沙箱命令恢复正常；Skill 保留在用户级目录。
