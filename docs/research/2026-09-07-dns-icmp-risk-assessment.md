# DNS / ICMP 与评测凭据风险评估

> 状态：本轮风险评估完成；公网利用链仍未证实。不是安全验收通过、已确认的架构变更或用户批准的风险豁免。
>
> 资料核对日期：2026-09-07。

> 后续状态：用户已授权并完成一轮假凭据检查及日志小修；当前能力和未接线项见 [认证接口第 6.2 节](../interfaces/CODEX_AUTHENTICATION.md#62-2026-09-07-假凭据安全收尾)。下文保留评估当时的原始证据和建议，不再把“本轮未修复/尚未授权”等历史表述当最新实施状态。

结论：不建议把“全面封禁 DNS/ICMP”当作 MVP 前置条件，也不能把现状认证为安全。当前更紧迫的是凭据可读边界及日志/制品脱敏：固定上游把凭据交给 Agent 用户并关闭内层沙箱；方法级合成验证已复现文件内假 Token 不被现有脱敏方法清除。DNS/ICMP 的外传风险取决于尚未证明的外部可达性，处理优先级应低于这项已确认的覆盖不足。

## 1. 范围与权威入口

回答“保留 DNS / ICMP 到底对本项目构成什么风险”，分别判断通道存在、敏感数据可读、对外可达和后果；不以“能通信”直接替代风险结论。

既定业务范围引用[架构文档](../architecture/ARCHITECTURE.md)，闭卷规则引用 [Runner 协议](../interfaces/RUNNER_PROTOCOL.md)，认证约定引用 [Codex 认证接口](../interfaces/CODEX_AUTHENTICATION.md)。本报告不重复维护这些政策，不授权修复、真实凭据读取或模型调用。

## 2. 协议与平台外部来源

本节是协议事实与据此作出的条件推理，不是本项目网络实测。Docker / Kernel 在线文档介绍一般机制，不能代替固定版本、实际内核和运行配置的检查。

### 2.1 Docker 内置 DNS：限定解析器不等于限定查询域名

Docker 官方说明：用户自建网络使用内置 DNS，地址为 `127.0.0.11`；外部域名查询会转发到宿主配置的 DNS 服务器。同一用户自建网络也支持按容器名通信。[Docker Networking：DNS services / User-defined networks](https://docs.docker.com/engine/network/)

据此推断：仅允许向某个解析器地址发送 DNS 请求，限制的是“向谁问”，未必限制“问哪些域名”。要据此认定外传受阻，还需检查解析器是否允许外部递归/转发、是否限制查询域名，以及上游路径是否可用。内部别名成功可以由 Docker 本地回答，不能证明查询已到公网。

### 2.2 DNS 夹带信息的必要条件

DNS 查询包含域名字段 `QNAME`，解析器可能查询其他服务器，也可能用缓存作答。[RFC 1035 §2.1–2.2、§4.1.2](https://www.rfc-editor.org/rfc/rfc1035.html)

基于这个机制，查询名可被程序用来夹带编码后的信息；若讨论“经攻击者控制域名外传”这条路径，必须同时满足：程序取得待传数据、能构造查询、查询链把相关名称送达攻击者可观察的服务器。双向隧道还需要可返回并被程序读取的回复。域名最终是否解析出有效 IP，不是判断查询内容是否已经送出的充分条件。

这是条件推理，不是发现了本项目的 DNS 隧道。内部别名解析成功、一次公网查询失败，分别都不足以证明“任意公网可外泄”或“所有外部 DNS 都阻断”。

### 2.3 ICMP Echo 有数据字段，但可达范围仍需单独证明

ICMP Echo（`ping` 使用的回显消息）包含数据，Echo Reply 应返回收到的数据。[RFC 792：Echo or Echo Reply Message](https://www.rfc-editor.org/rfc/rfc792.html)

据此推断：如果发送程序能读取敏感内容、把它放入报文，而且报文能到达外部接收者，就可能形成外传通道。仅给自己的测试容器发送合成标记，证明的是该目的地的数据通信，不证明公网接收方可达、完整双向隧道可用或真实凭据已泄露。

### 2.4 Linux 的 ping socket 与原始套接字权限不是一回事

Linux 的 `ping_group_range` 决定哪些组可以创建 ICMP 数据报套接字；它有独立的权限范围控制。[Linux Kernel：IP Sysctl / ping_group_range](https://docs.kernel.org/networking/ip-sysctl.html)

Linux v6.6 的 `inet_create()` 对用户创建 `SOCK_RAW` 明确检查 `CAP_NET_RAW`。[Linux v6.6：net/ipv4/af_inet.c](https://github.com/torvalds/linux/blob/v6.6/net/ipv4/af_inet.c)

因此，撤掉 `CAP_NET_RAW` 或全部 capability（进程特权）不能单独证明 ICMP Echo 一定不可用：非原始的 ping socket 仍须结合组范围、其他系统限制及网络规则判断。以上只解释机制，不假定本机内核就是 v6.6，也不假定它采用上游默认组范围。

### 2.5 不应不分类型地封禁全部 ICMPv6

ICMPv6 不只有回显，还承担邻居发现、路由器发现与必要错误反馈；`Packet Too Big` 用于发现路径可承受的报文大小。RFC 4890 按消息类型与流向提出过滤建议，而不是全部丢弃。[RFC 4890 §4.3.1、§4.4.1、附录 A.2](https://www.rfc-editor.org/rfc/rfc4890.html)

因此，如需收紧，应先明确实际使用 IPv4 / IPv6、限制对象及必要控制消息；不能为了阻止主动携带数据的回显请求，未经验证就删除维持正常网络的所有消息。这是评估建议，不是已批准的配置更改。

## 3. 本地证据

### 3.1 固定身份和当前实际暴露

本轮只读复核 Harbor HEAD=`6af8d6e31eced13b93849cdf80feeadf24603d15`，工作树干净。项目当前入口在加载 Harbor/创建容器前拒绝非 NOP；宿主环境过滤排除认证变量。本轮重跑 [现有网络契约](../../apps/backend/tests/contract/test_execution_network.py) 为 **28 passed / 0.48 s**，包含这两项与配置防篡改。固定依赖身份引用[依赖总表](../dependencies/DEPENDENCIES.md)。

这是“尚未运行真实评测”的保护，不是将来注入凭据后的隔离保证。我们没有证据表明本项目已发生真实凭据泄露。

### 3.2 已有容器网络证据，本轮只复核未重跑

逐项网络行为唯一维护在 [执行接口追加取证](../interfaces/HARBOR_EXECUTION.md#无凭据追加边界取证2026-09-07)。本轮重新读取忽略证据目录 `runtime/prototype/m0-network-extra-20260907-03/` 的 `extra-summary.json` 与 `extra-cleanup.json`：受控 TLS 对照符合预期；DNS 解析返回本测试网络 IP；ICMP 向另一测试容器往返成功；该轮专属资源清理记录 verified=true。此记录不等于本轮重新查询 Docker 全局状态。

固定 [network-policy 源码](https://github.com/harbor-framework/harbor/blob/6af8d6e31eced13b93849cdf80feeadf24603d15/src/harbor/environments/docker/harbor-docker-egress-control-sidecar/bin/network-policy) 在 output/egress 中放行配置的 resolver、本地目的地及 ICMP；非本地 TCP 交给受控代理。它没有按 DNS 查询名称实施模型域名过滤，ICMP 规则也没有把目标限定为模型服务。但仅凭输出链规则仍不能确定宿主、VPN、路由和上游网络最终允许哪些外部目的地。

现有有效 DNS/ICMP 探针测的是 `public` 与 `no-network`；`allowlist` 使用同一组底层放行规则是源码事实，不冒充已做独立的 DNS/ICMP allowlist 容器实测。上一次公网 DNS 失败没有有效正对照，也没有权威 DNS 接收端观测，不能算外传被阻断。

### 3.3 凭据读取、输出与清理

准确认证路径维护于 [认证接口第 6.1 节](../interfaces/CODEX_AUTHENTICATION.md#61-2026-09-07-风险评估发现)。静态依据是固定 [Codex.run](https://github.com/harbor-framework/harbor/blob/6af8d6e31eced13b93849cdf80feeadf24603d15/src/harbor/agents/installed/codex.py#L1380-L1484)：上传凭据并允许 Agent 用户读取；CLI 使用 bypass 参数；输出进入 `tee` 和 session 日志；退出后复制 session，再尝试清理凭据目录，清理异常被忽略。`try/finally` 也不是所有前置 setup 失败的包围范围。

据此判断：若直接沿用该路径，不能声称同一用户的仓库进程与登录文件隔离，也不能仅靠方法结束就断言已清干净。完整 Trial 的实际读取权限、启动失败及强杀后的清理仍未验证；已通过的无凭据容器清理测试不能覆盖文件内容检查。

官方说明文件型 `auth.json` 含访问令牌，应按密码处理；官方也警示容器内关闭 Codex 沙箱时，恶意项目可能外传容器可访问内容，包括 Codex 凭据。这支持防护必要性，但不是本机已发生攻击的证据。[官方认证文档](https://learn.chatgpt.com/docs/auth#credential-storage)、[官方安全文档](https://learn.chatgpt.com/docs/agent-approvals-security#run-codex-in-dev-containers)

### 3.4 新增无模型合成验证

使用忽略的 `runtime/prototype/dns-icmp-risk-probe.py`，以固定 Harbor Python 调用真实 `Trial._scrub_jobs_dir()`；Trial 的配置容器用简单替身提供，输入完全是本次生成的非有效假值。未调用 Agent.run、登录、模型、Docker 或外部 DNS/ICMP。

结果保留在 `runtime/prototype/dns-icmp-risk-20260907/summary.json`：

| 检查 | 结果 | 解释 |
|---|---|---|
| 敏感环境变量中的假值 | 被替换 | 正对照证明真实脱敏方法已执行 |
| 环境变量中的合成认证文件路径 | 被替换 | 隐去路径不等于隐去文件内 Token |
| 合成认证文件内、同时写入测试日志的假 Token | 仍存在 | 现有方法不会自动读取文件并识别内部秘密 |
| 同一假 Token 经过项目 `write_log()` | 仍存在，日志未截断 | 有界持久化不是内容脱敏 |

5 项行为断言全部成立，程序退出 0；其中两项是**风险复现成功，不是安全通过**。依据：[固定 scrub 方法](https://github.com/harbor-framework/harbor/blob/6af8d6e31eced13b93849cdf80feeadf24603d15/src/harbor/trial/trial.py#L889-L942)、[项目日志写入](../../apps/backend/src/eval_platform/adapters/execution/harbor/process_evidence.py)。未证明真实 CLI 会主动打印 Token；但若秘密进入输出，当前这些方法不足以保证清除。即使封禁 DNS/ICMP，本地输出残留问题仍存在。

## 4. 风险与优先级

采用定性分级，不编造发生概率、CVSS 或“安全百分比”。“高影响”描述条件成立时的后果，不等于已经发生或高概率；优先级是实施建议，不是新增业务门槛。

| 风险 | 证据与成立前提 | 可能影响 | 可能性判断 / 建议优先级 |
|---|---|---|---|
| R1：仓库命令读取容器凭据 | 固定源码确认 Agent 用户可读且关闭内层沙箱；需注入真实凭据并执行恶意/被诱导的读取行为，尚未容器实测 | 高：可复用凭据暴露、账号被滥用 | 当前真实入口关闭；启用后不能排除。**首次真实凭据前优先验证/处理** |
| R2：日志/轨迹/patch 等保留秘密 | 方法级验证确认 env 脱敏不覆盖文件内部假 Token，日志写入不脱敏；实际泄露还需秘密进入输出 | 高：即使没有公网，随后共享报告也可能暴露凭据 | 覆盖不足证据强；真实发生频率未知。**首次真实凭据前优先处理并验证清理** |
| R3：经 DNS 对外传数据或获取信息 | 内部解析实测 + 上游放行规则；还需外部转发、攻击者可观察接收方和受控查询内容 | 若传凭据则高；也可能影响闭卷公平性 | 公网利用链未知，不能认证低风险。**中优先级核验范围**，不先建复杂 DNS 系统 |
| R4：经 ICMP 对外传数据或获取信息 | 容器间带标记回显实测；还需外部接收方可达、构造内容/响应能力 | 若传凭据则高；一般回显本身不等于查答案 | 公网利用链未知。**中优先级核验范围**；必要控制消息与主动 Echo 分开判断 |

固定 Agent、固定任务和所有者批准降低了任意参与者主动植入代码的机会，但批准任务不等于审计过所有仓库/依赖代码。当前不把面向任意恶意 Agent 的 P2 强对抗防护拉进 MVP；也不把“可信队友”当作文件内容安全的证明。

## 5. 最小处置建议

1. **先深化现有执行适配层的凭据与输出处理**：用假 Token 验证读取范围、敏感文件排除与内容覆盖、刷新值，以及成功/失败/超时清理。避免先为 DNS/ICMP 新增独立业务模块。单纯 `chmod 600` 不能隔离同一用户；匹配若干字符串也不能宣称抵御恶意编码外传。
2. **网络补测有界且无秘密**：分别检查当前 allowlist 的 DNS 解析器外部转发范围与 ICMP 目的地范围；所有主动实验限于自有/获授权接收方。若没有这样的外部接收端，就明确保留未知，不扫描校园网或用第三方网站作数据接收器，也不把 NXDOMAIN/超时当安全证明。
3. **处置按结果决定**：必要 DNS 和必要 ICMP 控制消息可以保留并明确许可范围；不必要的外传路径若能在既有模板中小幅收紧，再提出具体修改。若需要复杂解析服务、认证代理或改变凭据边界，应先说明代价并由用户确认。
4. **分清继续与通过**：无凭据开发/合成检查可以继续；当前仍不建议注入真实个人登录文件。网络剩余风险如需暂缓，必须由所有者明确接受其范围，并如实记录为例外，不能把授权风险接受写成技术验收通过。正式闭卷的模型端点、Web 工具和验证环境门槛仍按原权威文档执行。

本轮仅完成评估与事实纠偏；没有执行以上修复，没有改变 DNS/ICMP 放行规则，没有选择新的凭据架构。

## 6. 限制与验证记录

外部协议资料使用 6 项一手来源，另核对 2 项 OpenAI 官方安全/认证页面；每项论点均在附近引用。代码结论依据本机已核验的固定上游和项目实现，不把滚动更新的在线文档当固定 CLI 行为证明。

本轮执行：既有网络契约 28 项通过；合成方法探针 5 项行为断言成立；探针 Ruff lint/格式通过。未重跑 Docker 网络集成、完整 pytest、mypy 或真实模型；旧轮网络证据是复核而非重跑。没有启动/停止容器、重启 WSL/Docker、修改代理/防火墙、读取真实凭据或提交/push。文档链接、围栏和最终 Git 检查结果见 [M0 行动记录末节](../actions/2026-09-05-m0-codex-harbor-implementation.md#2026-09-07-dnsicmp-风险评估)。
