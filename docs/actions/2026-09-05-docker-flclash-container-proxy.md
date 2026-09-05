# Docker / FlClash 容器代理配置行动记录

## 状态与情况说明

- 状态：已完成通用 Docker 容器代理配置与分层验证；Harbor/Codex Trial 和闭卷防绕过保留为后续原型。
- 来源请求：用户要求由 Codex 直接帮助配置 Docker 容器通过本机 FlClash 访问外网。
- 范围：核对并配置本机 Docker Desktop、FlClash 与 Windows 防火墙之间的最小代理通路；使用无凭据请求验证容器出站；把实际环境事实同步到权威运维文档。
- 初始事实：Windows 系统代理已启用并指向 `127.0.0.1:7890`；FlClash TUN 关闭；FlClash Core 只在回环地址监听 `7890`；Docker CLI 的 `proxies` 配置为空；首次检查时 Docker Engine 未运行。
- 已确认决定：保持 FlClash TUN 关闭；容器不得把 `127.0.0.1` 当成宿主机；正式 Harbor Codex Trial 的代理变量最终由受控 `AgentConfig.env` 注入，不能由远端 Job 任意传入。
- 已查明：Docker Desktop 已是系统代理模式，并通过内部 `http.docker.internal:3128` 转发到 FlClash；运行中容器可使用该内部代理，因此无需开启 Allow LAN 或新增防火墙规则。容器还可经 `host.docker.internal:7890` 直接触达宿主代理，这是闭卷隔离必须处理的旁路。
- 仍未知：Harbor 动态 Trial 是否正确接收 `AgentConfig.env`、Codex CLI 所需完整端点、闭卷端点白名单与防直连策略，以及现有系统防火墙规则的完整筛选器详情。
- 明确排除：不读取或输出 FlClash 订阅/节点、Docker 登录凭据、Codex `auth.json` 或 Token；不打开校园网公网端口；不启用 FlClash TUN；不运行真实付费 Codex Trial；不把代理地址固化进镜像。

## 实施措施

1. 只读核对 Docker Desktop、FlClash 运行配置入口、监听地址、Docker/WSL 网络和现有防火墙规则。
2. 启动 Docker Desktop 并确认 Engine 恢复；先使用本地已有镜像完成不依赖下载的网络探针。
3. 优先选择 Docker Desktop 内部代理；实测成功后不启用 FlClash `Allow LAN`，不创建 7890 防火墙规则。
4. 保留 Docker Desktop 的系统代理模式；为 Docker CLI 新容器配置 `http.docker.internal:3128` 自动代理。未来 Harbor Trial 仍通过受控 `AgentConfig.env` 显式注入同一路径。
5. 分层验证本地代理监听、容器到宿主代理、无凭据 OpenAI HTTPS 请求和 Docker 拉取路径；如某层失败，停止扩大权限并记录真实失败。
6. 将实际配置、验证证据、限制与回退方式同步到本机 Docker/WSL 权威文档和远程接入文档。

完成标准：容器可经受控宿主代理完成 HTTPS 请求；代理端口没有向校园网形成宽泛入站暴露；Docker/FlClash/TUN 的实际状态和未完成的 Harbor/Codex E2E 在文档中与实测一致。

## 需要修改的文件树

```text
docs/
├─ actions/
│  └─ 2026-09-05-docker-flclash-container-proxy.md
│     # 本次主机配置、偏差、验证结果和回退信息的行动记录
├─ architecture/
│  └─ ARCHITECTURE.md
│     # 区分已验证的代理连通能力与尚未实现的闭卷防绕过边界
└─ operations/
   ├─ LOCAL_DOCKER_ENVIRONMENT.md
   │  # 同步本机 Docker/WSL/代理的最新动态事实与验证状态
   └─ REMOTE_TEAM_ACCESS.md
      # 只引用本机代理实测结论，并保持 FlClash/Tailscale 边界一致
HANDOFF.md
  # 同步下一窗口必须了解的代理实测状态和剩余风险

Windows host（不进入 Git）：
├─ Docker Desktop proxy settings
│  # 已确认原有系统代理模式正确，无需修改
├─ C:\Users\YINGYI\.docker\config.json
│  # 实际新增 Docker CLI 默认代理；保留原有登录、插件和上下文字段
├─ FlClash runtime settings
│  # 已确认 TUN/Allow LAN 关闭和回环监听；本次不修改
└─ Windows Defender Firewall
   # 本次不新增、不修改、不删除规则
```

设计关系：Docker Desktop 管理镜像拉取链路并提供内部代理；FlClash 是 Windows 系统出站代理；宿主回环监听避免校园网直接进入 7890。未来 `HarborExecutionAdapter` 通过 Harbor `AgentConfig.env` 为受控 Codex Trial 注入代理变量，并另行实现宿主/公网防绕过。未新增设计模式或业务接口。

回退方式：若该 Docker CLI 自动代理影响其他本机容器，只删除 `C:\Users\YINGYI\.docker\config.json` 中本次新增的顶层 `proxies` 字段并重新创建受影响容器；不要删除整个文件，因为其中还保留 Docker 登录、插件和 context 配置。Docker Desktop 与 FlClash 本次未改变，无需回退。

## 修改后自验证方式

1. `docker version`、`docker info`：Engine 可响应，并记录 Desktop/Engine 与代理相关事实。
2. `netstat -ano`、`Get-NetTCPConnection`：确认 TCP 7890 的真实监听地址和所属 FlClash Core 进程。
3. `Get-NetFirewallRule` / `Get-NetFirewallAddressFilter`：确认不存在面向任意远端地址的项目新增允许规则。
4. 使用本地已有镜像从容器连接 `host.docker.internal:7890`；成功标准为 TCP 建连成功。
5. 在容器中显式设置 `HTTP_PROXY`/`HTTPS_PROXY`，向 OpenAI HTTPS API 发无凭据请求；成功标准为收到 HTTP `401` 等应用层响应，而不是 DNS、连接或 TLS 错误。
6. 检查 Docker Desktop 代理日志或执行受控镜像拉取，区分镜像拉取代理和运行中容器代理。
7. `git diff --check`、相关文档关键词/链接检查、`git status --short`：文档格式通过且变化范围与本行动记录一致。

## 自验证情况

- 通过：`docker desktop start` 后 `docker desktop status` 为 `running`，`docker version` 的 Client/Server 均为 `27.5.1`。
- 通过：Docker Desktop 设置为 `ProxyHTTPMode=system`，Engine 报告 `HTTPProxy`/`HTTPSProxy` 为 `http.docker.internal:3128`；Docker 代理日志明确显示 OpenAI 与 Docker Registry 的 CONNECT 经 Windows 系统代理 `127.0.0.1:7890`。
- 通过：本地 BusyBox 对 `http.docker.internal:3128` 的 TCP 探针成功。
- 通过：更新后的 Docker CLI 配置重新解析为合法 JSON，原有 `auths`、`credsStore`、`currentContext`、`features`、`plugins` 均保留，并新增 `proxies`。新 BusyBox 在没有命令行 `-e` 的情况下自动获得大小写两套 HTTP(S)/NO_PROXY 变量。
- 通过：新 BusyBox 自动代理请求 `https://api.openai.com/v1/models`，收到 `HTTP/2.0 401 Unauthorized`。这证明 DNS、TCP、代理和 TLS 可达，不表示已完成 Codex 认证。
- 通过：按本机已有 `busybox@sha256:32015ee641bfecc97161986c9d24957068175444f66fbcbe08a664b6cf5c1c2e` 固定摘要执行 `docker pull`，返回 `Image is up to date`，没有移动 `latest` 标签。
- 通过：FlClash 运行配置仍为 `mixed-port: 7890`、`allow-lan: false`、`tun.enable: false`；宿主只监听 `127.0.0.1:7890`。对当前 WLAN 地址 `10.62.158.77:7890` 的 TCP 探针失败，未形成校园网入口。本次没有执行任何防火墙写命令。
- 发现风险：BusyBox 对 `host.docker.internal:7890` 的 TCP 探针意外成功。Docker Desktop 的宿主转发可使容器触达回环代理，因此代理环境变量不是闭卷防绕过边界；已同步总架构、Docker 环境和远程接入文档。
- 限制：读取现有 7890 防火墙筛选器时 `Get-NetFirewallPortFilter` 返回“拒绝访问”，所以没有宣称完整审计了既有防火墙规则。
- 失败后恢复：第一次配置写入使用带空备份参数的 `.NET File.Replace`，调用被拒绝；随后确认原文件 SHA-256 未变、JSON 可解析、代理字段不存在且临时文件数为 0。第二次用同目录覆盖移动成功，并再次验证 JSON 和字段。
- 通过：`git diff --check` 无空白错误；只出现 Git 预期的 LF/CRLF 提示。相关本地链接全部存在，关键词一致性检查覆盖内部代理、宿主旁路、Allow LAN 和 `AgentConfig.env`。
- 变更范围：仓库内实际修改 `HANDOFF.md`、`docs/architecture/ARCHITECTURE.md`、`docs/operations/LOCAL_DOCKER_ENVIRONMENT.md`、`docs/operations/REMOTE_TEAM_ACCESS.md`，并新增本行动文档；仓库外只修改 `C:\Users\YINGYI\.docker\config.json` 的代理字段和启动 Docker Desktop。
