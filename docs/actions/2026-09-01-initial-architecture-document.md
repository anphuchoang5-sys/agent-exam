# 初版架构文档落盘行动记录

## 状态和情况说明

- 状态：已完成
- 来源请求：用户确认物理环境只能单机运行，并要求现在创建带 Mermaid 图的架构文档，后续随讨论持续更新，防止上下文丢失。
- 当前阶段：架构讨论设计；允许创建和更新文档，不编写业务代码。
- 已确认事实：
  - 项目直接使用 SWE-Gym 及配套 SWE-Bench-Fork 作为任务与确定性评测核心。
  - 部署和执行只考虑单台物理计算机，不规划多机调度实现。
  - 题目要求统一 Runner、Docker 隔离与治理、LLM-as-Judge、人工抽检、Next.js 15 + React 19、PostgreSQL + MinIO。
  - 团队名义 5 人，实际有效开发力量约 2.5 人，周期约一个月。
- 未确认内容：后端框架、Worker 部署方式、自定义 Agent 提交形式、排行榜比较对象、Judge 与过程指标是否参与总分等。
- 明确排除：本次不安装依赖、不运行 Docker、不创建业务源代码、不把待确认方案伪装为定稿。

## 实施措施

1. 已创建术语唯一事实源 `CONTEXT.md`，只记录已经明确的领域词义。
2. 已创建 `docs/architecture/ARCHITECTURE.md`，分别标注已确认、候选和待确认内容。
3. 已在架构文档中加入系统关系图、评测时序图和运行状态图的 Mermaid 源码。
4. 已写入带职责、依赖关系和设计模式角色说明的候选文件树。
5. 已在既有研究记录中增加当前架构文档指针，避免历史研究建议被误认成当前决定。
6. 已检查 Markdown 结构、Mermaid 代码块、文件树职责、决策状态和文档交叉引用。

完成标准：架构文档能够独立说明当前已知架构、候选方案、关键数据流、设计模式、风险和待讨论问题；所有未确认项都有显式标记。

## 实际修改的文件树

```text
E:\9.1实训\
├─ CONTEXT.md
│  # 项目领域术语的唯一事实源；不记录实现细节
└─ docs\
   ├─ actions\
   │  └─ 2026-09-01-initial-architecture-document.md
   │     # 本次架构文档创建过程、范围和验证证据
   ├─ architecture\
   │  └─ ARCHITECTURE.md
   │     # 当前架构唯一事实源；保存已确认、候选和待确认设计
   └─ research\
      └─ 2026-09-01-agent-evaluation-platforms.md
         # 外部项目研究记录；增加指向当前架构的状态提示
```

文档间职责：`CONTEXT.md` 只定义“词是什么意思”；`ARCHITECTURE.md` 定义“系统怎样组成和协作”；研究记录保存“外部事实如何得出”；本行动记录保存“这次文档如何创建和验证”。

## 修改后自验证方式

1. 用 `rg` 检查架构文档是否包含“已确认”“候选”“待确认”三种状态。
2. 检查至少包含 3 个 `mermaid` 代码块，且每个代码块闭合。
3. 检查文件树中的每个规划路径都带职责说明，设计模式参与文件和角色有明确说明。
4. 检查单机、SWE-Gym、SWE-Bench-Fork、Runner、Docker、Judge、人工抽检、Next.js、PostgreSQL、MinIO 均被覆盖。
5. 检查 `CONTEXT.md` 不含框架选型和部署等实现细节。
6. 检查研究记录能够指向架构唯一事实源。
7. 若本机没有 Mermaid 渲染器，如实记录“仅完成源码结构检查，未完成图形渲染”。

## 自验证情况

- 文件存在性：`CONTEXT.md` 与 `docs/architecture/ARCHITECTURE.md` 均存在；研究记录的当前决定提示能正确指向架构文档。
- 决策状态检查：`rg` 检出“已确认”“候选”“待确认”，未把候选模块描述为已经实现。
- 范围覆盖检查：已检出 SWE-Gym、SWE-Bench-Fork、单台物理计算机、统一 Agent Runner、Docker、LLM Judge、人工抽检、Next.js 15、React 19、PostgreSQL 和 MinIO。
- Mermaid 源码检查：架构文档包含 3 个 `mermaid` 代码块，分别为单机系统关系图、评测时序图和运行状态图；文档共有 4 个 fenced code block，起止 fence 数为 8，结构闭合。
- Mermaid 渲染限制：本机未发现 `mmdc` Mermaid CLI，因此没有执行图形渲染；只完成了代码块结构与源码人工检查，不能把它描述为渲染通过。
- 文件树检查：规划树中每个列出的文件或目录都带有同行或紧随其后的职责说明；Adapter、Factory/Registry、Repository、State 模式均列出参与文件、角色和关系。
- 术语表检查：`CONTEXT.md` 包含评测任务、被测 Agent、Agent 配置、评测运行、补丁、轨迹、确定性验证、Judge 分析、人工复核和制品；没有写入 FastAPI、Docker、Next.js、PostgreSQL、MinIO 或 Adapter 等实现选择。
- 文档唯一事实源检查：研究记录保留外部事实并新增架构指针；架构决定由 `ARCHITECTURE.md` 维护；词义由 `CONTEXT.md` 维护；没有重复创建第二份架构文档。
- 范围检查：本次只创建或更新 Markdown 文档，没有创建业务源代码、安装依赖、下载数据集或运行 Docker。
