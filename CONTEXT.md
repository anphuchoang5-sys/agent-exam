# AI Coding Agent 评测领域

本文件统一项目中的领域词义，避免团队成员和 Agent 用不同名称描述同一事物。实现框架、部署和代码结构不在此记录。

## Language

**评测任务（Evaluation Task）**：
一项不可随运行变化的软件修复题目，由问题描述、目标仓库、固定提交和判定测试共同确定。
_Avoid_：题目实例、Sample、Case

**被测 Agent（Evaluated Agent）**：
接受评测任务、操作代码仓库并尝试生成修复补丁的编码系统；它不等同于其使用的语言模型。
_Avoid_：模型、选手程序、机器人

**Agent 配置（Agent Configuration）**：
一次可复现的被测 Agent 身份，包含 Agent 版本、模型版本和影响行为的配置。
_Avoid_：Agent 名称、模型名称

**已登记 Agent（Registered Agent）**：
经过项目组审核、固定版本并明确允许出现在评测列表中的被测 Agent。
_Avoid_：任意 Agent 仓库、临时 Agent

**评测运行（Evaluation Run）**：
一个 Agent 配置在一个评测任务和一组固定限制下完成的一次独立评测尝试。
_Avoid_：Job、Trial、测试记录

**补丁（Patch）**：
被测 Agent 针对目标仓库生成的 Git diff，是确定性验证的主要输入。
_Avoid_：答案、代码文件、提交

**轨迹（Trajectory）**：
评测运行中按时间排列的 Agent 消息、工具调用、环境反馈和资源统计事件。
_Avoid_：日志、回答过程、思维链

**确定性验证（Deterministic Verification）**：
把补丁应用到干净任务环境并执行规定测试后得到的可重复判定。
_Avoid_：LLM 打分、Judge、人工评分

**Judge 分析（Judge Analysis）**：
LLM 根据运行证据生成的失败归因或质量分析；它与确定性验证结果分别保存。
_Avoid_：测试结果、最终事实

**人工复核（Human Review）**：
评审者检查任务证据并确认、修正或补充 Judge 分析的记录。
_Avoid_：人工测试、重新评测

**制品（Artifact）**：
评测运行产生并需要长期保存的补丁、原始日志、轨迹、测试输出或 Judge 原始响应。
_Avoid_：数据库记录、临时文件
