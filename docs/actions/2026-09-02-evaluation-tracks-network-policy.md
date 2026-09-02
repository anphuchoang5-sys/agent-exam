# 闭卷主榜与开卷实验榜决策同步行动记录

## 状态和情况说明

- 状态：已完成
- 来源请求：用户确认采用“闭卷主排行榜 + 开卷实验榜”，并提出不同 Agent 的联网与 Web 工具能力可能不同，尤其需要避免用模型国别直接推断 GitHub/外网访问能力。
- 当前阶段：架构讨论；本次只同步已经确认的高层规则和仍待讨论的公平性问题，不实现网络代理、Agent、排行榜或其他业务代码。
- 已确认：
  - 闭卷评测进入核心排行榜。
  - 开卷运行必须与闭卷成绩分开，进入实验榜。
  - 确定性判卷仍统一使用 SWE-Bench-Fork；网络模式不能改变 `resolved` 的原始测试事实。
- 已核验事实：当前固定 SWE-Bench-Fork 创建实例容器时未显式断网，使用 Docker 默认网络；断网是本项目候选治理能力，不是上游已经提供的保证。
- 未确认：
  - 开卷实验榜使用所有 Agent 共同的平台 Web 工具，还是允许各 Agent 使用自己的原生搜索工具。
  - Docker Desktop 下模型端点白名单/代理的具体实现。
  - 所谓“国产 Agent”的具体产品、版本、工具接口及其 GitHub/境外网站访问能力。
- 明确排除：不按“国产/国外”预设网络能力，不把宿主机能使用代理等同于 Docker 自动继承代理，不在本轮运行任何真实 Agent 或修改网络配置。

## 实施措施

1. 在总架构中新增已确认评测赛道决定，区分闭卷主榜与开卷实验榜。
2. 在模块契约中要求 Run Submission、Runner、Sandbox 和 Reporting 冻结并按赛道/网络/工具配置分组。
3. 在 Runner 协议中新增 `evaluation_track`、`network_policy_id` 和 `tool_profile_id` 的候选语义，明确工具权限与网络权限是两层控制。
4. 在 HTTP 契约中让创建运行和排行榜查询显式携带赛道，禁止跨赛道混分。
5. 在数据模型中持久化赛道、网络和工具配置快照，确保历史可追溯。
6. 保留“标准化开卷工具 vs Agent 原生工具”为下一项用户决策，不替用户定稿。

完成标准：所有受影响文档一致表达“同一确定性判卷、不同网络赛道、成绩不得混合”；未确认的开卷公平标准仍明确标记为待确认。

## 需要修改的文件树

```text
E:\9.1实训\docs\
├─ actions\
│  └─ 2026-09-02-evaluation-tracks-network-policy.md
│     # 本次网络赛道决策、修改范围和验证证据
├─ architecture\
│  ├─ ARCHITECTURE.md
│  │  # 新增闭卷主榜/开卷实验榜全局决定和待讨论公平性问题
│  ├─ MODULE_CONTRACTS.md
│  │  # 同步 Run、Sandbox、Reporting 的赛道输入输出与不变量
│  └─ DATA_MODEL.md
│     # 保存赛道、网络策略和工具配置快照，支持分榜统计
└─ interfaces\
   ├─ RUNNER_PROTOCOL.md
   │  # 运行输入中明确赛道、网络策略和工具配置
   └─ HTTP_API.md
      # 创建运行和排行榜查询显式选择赛道
```

设计关系：Sandbox Controller 落实 `network_policy_id`，各 Agent Adapter 落实 `tool_profile_id`，Run Orchestrator 只传递已登记配置，Reporting 按 `evaluation_track` 分组；这些都是既有 Adapter/Registry/Repository seam 的扩展，不新增微服务或新设计模式。

## 修改后自验证方式

1. 检查 5 份权威文档均出现闭卷主榜、开卷实验榜或相应稳定字段。
2. 检查 Runner 的示例和字段表包含 `evaluation_track`、`network_policy_id`、`tool_profile_id`。
3. 检查 HTTP 创建运行与排行榜查询都要求赛道，且明确禁止跨赛道混分。
4. 检查数据模型冻结赛道/网络/工具快照，并有对应排行榜验证规则。
5. 检查总架构不再把“Agent 网络策略整体待确认”写成未作任何决定，而是只保留执行细节与开卷公平标准待确认。
6. 检查 Markdown 本地链接和 fenced code block；若无 Mermaid 渲染器，如实记录限制。
7. 确认本次没有创建业务代码、运行 Agent 或修改主机/Docker 网络配置。

## 自验证情况

- 文件范围：行动记录和计划中的 5 份权威文档均已存在并完成同步；没有修改范围外项目文件。
- 赛道一致性：`ARCHITECTURE.md`、`MODULE_CONTRACTS.md`、`DATA_MODEL.md`、`RUNNER_PROTOCOL.md`、`HTTP_API.md` 均检出 `closed_book` 与 `open_book_experimental`，且说明使用相同 SWE-Bench-Fork 确定性判卷、成绩不得混合。
- Runner 字段：`RunEnvelope` 示例和字段表均包含 `evaluation_track`、`network_policy_id`、`tool_profile_id`；示例 JSON 已由 PowerShell `ConvertFrom-Json` 成功解析，值分别为 `closed_book`、`provider-only-v1`、`no-web-tools-v1`。
- HTTP 契约：创建运行请求显式包含 `evaluation_track`；排行榜查询要求赛道并按网络/工具配置分组。Runner 与 HTTP 文档共 14 个 JSON 代码块，全部解析成功，错误数为 0。
- 数据模型：`evaluation_runs` 的 Mermaid 概念实体和表级字段都加入赛道、网络策略、工具配置；排行榜索引和验证规则明确禁止跨赛道混分。
- 待确认项：5 份权威文档中仍有 4 处明确指向“平台统一 Web 工具 vs Agent 原生搜索工具”，没有把该公平标准提前定稿。
- 过期描述：未再检出“Agent 阶段精确网络策略仍待确认”或原笼统网络策略待确认句；已经替换为高层规则已确认、执行细节待实测。
- 链接检查：本轮 6 个文档的本地 Markdown 链接断链数为 0。
- Markdown 结构：本轮 6 个文档均为偶数 fenced code block，未发现未闭合围栏。
- Mermaid 限制：本机仍未发现 `mmdc`，本轮没有执行图形渲染；只做了围栏结构和修改处人工检查。
- 范围检查：`apps` 目录业务文件数为 0；没有创建业务代码、运行 Agent、修改代理、防火墙或 Docker 网络。
- 尚未核验：用户没有指定具体国产 Agent/模型产品，因此没有臆测其 GitHub、境外网站或原生搜索工具能力；需要产品名和固定版本后逐个查官方接口并实测 Docker 网络路径。
