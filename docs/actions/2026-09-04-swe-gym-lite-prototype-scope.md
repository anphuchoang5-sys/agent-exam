# 行动文档：固定首个 SWE-Gym-Lite 原型范围

## 状态与情况说明

- 状态：已完成。
- 来源请求：用户接受首个真实闭环使用 `SWE-Gym/SWE-Gym-Lite` 的 1～3 道真实题，并要求继续讨论尚未确定的架构问题。
- 当前事实：此前文档只确认“首个原型使用少量 SWE-Gym 任务”，仍把精确 dataset ID、revision、split 和任务 ID 全部列为未决。
- 本次确认：原型数据集 ID 固定为 `SWE-Gym/SWE-Gym-Lite`；首个验收批次只选择 1～3 道真实任务；不是 Mock，也不代表正式排行榜最终只使用 Lite。
- 仍待技术核验：数据集不可变 revision、真实 split、实例字段、镜像可用性、单题资源与运行时间，以及最终 1～3 个 `instance_id`。
- 明确排除：本次不下载数据或镜像，不选择未经核验的 revision/split/instance，不运行 Harbor、Agent 或 SWE-Bench-Fork，不修改业务代码，不提交或推送 Git。

## 实施措施

1. 在总架构中增加已确认的 Lite 原型范围，并把未决事项缩小为 revision、split 和具体任务的技术核验。
2. 在依赖事实源中把原型 dataset ID 从“待确认”改为已确认，同时保持 revision、split、实例和校验值待核验。
3. 在 Harbor 接口和框架接口中明确首个验收使用 Lite 真实任务，不把尚未读取的数据字段写死。
4. 检查术语、链接、Markdown 围栏、尾随空白和差异格式，并回填真实结果。

完成标准：所有当前权威文档一致表达“Lite + 1～3 道真实题已确认”，且没有把 revision、split、具体实例或运行能力伪装成已确认。

## 需要修改的文件树

```text
E:\9.1实训\
└─ docs\
   ├─ actions\2026-09-04-swe-gym-lite-prototype-scope.md
   │  # 本次范围确认、措施与验证证据
   ├─ architecture\ARCHITECTURE.md
   │  # 记录 Lite 原型决定、验证门槛与后续技术核验项
   ├─ dependencies\DEPENDENCIES.md
   │  # 原型 dataset ID 的唯一依赖事实和未锁定项
   └─ interfaces\
      ├─ HARBOR_EXECUTION.md
      │  # 首个 Harbor 验收输入范围
      └─ FRAMEWORK_INTERFACES.md
         # SWE-Gym 数据接口的已确认与待核验边界
```

设计关系：不新增模块或设计模式。`Task Catalog Adapter` 仍负责把固定数据 revision 中的真实任务转换为项目 `EvaluationTask`；Harbor 只消费转换后的任务，不能自行选择漂移的数据版本。

## 修改后自验证方式

1. `git diff --check`：无补丁格式或尾随空格错误。
2. 文档检索：在权威文档中能检出 `SWE-Gym/SWE-Gym-Lite` 和 `1～3` 道真实任务。
3. 未知项检索：revision、split、`instance_id`、镜像与资源仍明确标为待核验。
4. Markdown 检查：相对链接目标存在、代码围栏成对。
5. 范围检查：没有业务源码、数据、镜像或运行产物变化。

## 自验证情况

- `git diff --check`：通过；仅出现 Git 的未来 LF→CRLF 提示，不是差异错误。
- 文件与格式：5 份目标文档均存在、无尾随空白，代码围栏数量均为偶数，相对链接目标存在。
- 已确认事实：总架构、依赖事实源、Harbor 接口和框架接口共 4 份权威文档都包含 `SWE-Gym/SWE-Gym-Lite` 与 1～3 道真实任务范围。
- 未知边界：逐文件复核确认 revision、split、具体实例/`instance_id` 仍写为待读取或待核验；没有采用 Hugging Face 漂移的 `main` 或猜测 split。
- 首次自动检索用一个过窄的正则表达式统计到 3/4 份未知边界，因此检查返回失败；展开逐行检索后确认第 4 份文档同样保留待核验表述，这是验证脚本条件问题，不是文档缺失。
- 范围：Git 状态只有上述 Markdown 文档变化；没有下载数据/镜像，没有运行 Harbor、Agent 或 Harness，也没有提交或推送。
