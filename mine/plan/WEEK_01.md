# 第 1 周：理解控制流，写出最小执行循环

- 状态：进行中；任务 A、B 已通过；任务 C 的可复现验证已完成，设计取舍仍待提交。
- 预计投入：6–8 小时，可按实际节奏拆分。
- 前置基础：熟悉 Python 和 tool calling。
- 推进规则：[学习大纲](OUTLINE.md)；本周评估通过后再制定第 2 周详细计划。

## 1. 本周目标与源码入口

**架构问题：** 模型与程序各自决定什么？什么时候继续调用模型，什么时候结束？

阅读顺序：

1. [Agent loop 文档](../../hermes-agent/website/docs/developer-guide/agent-loop.md)：建立概念，不追完全部分支。
2. [AIAgent 入口](../../hermes-agent/run_agent.py)、[Turn 入口](../../hermes-agent/agent/turn_facade.py)：只看接口与转发关系。
3. [主循环](../../hermes-agent/agent/conversation_loop.py)：定位入口、循环条件、阶段分派。
4. [响应解析](../../hermes-agent/agent/turn_response_intake.py)、[工具轮次](../../hermes-agent/agent/turn_tool_round.py)、[最终回答](../../hermes-agent/agent/turn_final_response.py)：沿一条成功路径追踪。

自己实现：一个最小 CLI、模型调用适配函数、内存消息列表，以及一个无副作用的小工具。循环必须保存 assistant 的 tool_calls 和对应的 tool 结果；设置最大模型调用次数，日志记录每轮输入类型、工具名和结束原因。

验收：

- 普通问题直接回答；需要工具的问题完成“模型 → 工具 → 模型 → 回答”。
- 用脚本化的假模型连续返回工具调用，程序到达上限后停止。
- 能手画一次完整请求的消息序列，解释每条消息由谁产生。

产物：可运行的最小闭环，一份请求轨迹，一页控制流笔记。

## 2. 阅读时建立的架构地图

按这条主线理解系统：

```text
CLI 收到用户输入
  → 加载 Session，开始一个 Turn
  → Context Builder 组装本次请求
  → Model Client 调用模型
  → 有工具调用：记录调用 → 校验和执行 → 记录结果 → 再次调用模型
  → 无工具调用：输出最终回答，保存状态，结束 Turn
```

从第一天开始区分四个概念：

- **Session**：跨多次用户输入保存的会话。
- **Turn**：处理一次用户输入的完整过程，可能调用模型很多次。
- **Iteration**：循环中的一次模型调用及其后续处理。
- **Tool call**：模型提出的一次工具调用请求，由程序决定是否执行。

再区分三类数据：**完整会话记录**用来恢复与追踪；**模型上下文**是本次实际发送给模型的内容；**长期记忆**保存跨会话仍有用的事实。它们不能简单等同于一个不断增长的 messages 列表。

本地源码的主循环已拆分。先看 `run_agent.py` 的公共接口和组合关系，再定位 `agent/conversation_loop.py::run_conversation` 及其调用的阶段函数；不要从大型文件第一行逐行读到末尾。

以上是完整 Agent 的概念地图。本周只实现内存中的会话与循环；持久化、长期记忆、上下文压缩属于后续阶段。

## 3. 建议执行顺序

### 任务 A：追踪与解释（约 1.5 小时）

沿上述源码入口追踪一条普通回答路径和一条工具调用路径。写出 Session、Turn、Iteration、Tool call 的区别，标明每条消息由谁创建、在哪里进入历史。记录关键函数及它们的职责，不必追完兼容与恢复分支。

### 任务 B：独立实现（约 3 小时）

在 `mine/src/` 中实现最小 CLI、模型适配函数和循环，接入一个确定性、无副作用的小工具，例如两个数字相加。消息保存在内存；至少能接收两次连续用户输入并传递已有历史。

先接入可脚本化的假模型，稳定观察消息流和停止条件，再接入你选定的一个真实模型。真实模型接入保留一个适配入口即可，不需要设计多供应商框架。若账户或网络暂不可用，可以先提交假模型验证的成果，但真实接入验收项保持待验证。

使用简单函数与数据结构即可。模型返回一批多个工具调用时可以串行执行；再次调用模型前，每个调用都应有匹配的结果。本周只要求明确基本失败行为，例如报告错误并停止；完整的参数校验与错误恢复留到工具阶段。

### 任务 C：验证与对照（约 1.5–2.5 小时）

用假模型稳定覆盖普通回答、工具调用、连续工具调用达到预算上限三条路径。预算明确按模型调用次数计数，最后一次允许调用后不再发起额外模型请求。

补充至少一次真实模型完成工具任务的运行记录，观察后续请求中是否包含完整调用与结果。日志保留消息角色、工具名、调用 ID、实际调用次数和停止原因；去除密钥及个人敏感内容。

最后写下你的实现与 Hermes 的三点取舍，例如同步串行、内存历史、简单上限分别省去了什么，又带来什么限制。

## 4. 产出位置建议

- `mine/docs/week-01/agent-loop.md`：概念、调用链、消息序列和设计取舍。
- `mine/docs/week-01/verification.md`：运行命令、环境前提、验证结果和代表性轨迹。
- `mine/src/`：最小实现；具体文件名与拆分由你决定。

这些路径是建议，不要求为满足命名机械搬动文件。提交时指出实际位置即可；本计划不会预先替你填写学习笔记或实现源码。

## 5. 本周必需验收项

以下由助手评估后更新。全部通过才判定本周完成；备注可写证据路径或待补事项。

| 编号 | 验收标准 | 状态 | 证据或备注 |
| --- | --- | --- | --- |
| W1-01 | 能区分 Session、Turn、Iteration、Tool call，解释模型与程序各自的职责 | 通过 | 四个概念和调用链已说明；模型提出工具调用、程序执行的职责可由现有描述和路径看出，无需再写重复说明；见下方最新评估 |
| W1-02 | 能结合源码解释普通回答和工具调用两条路径，并展示完整消息序列 | 通过 | 两条路径、`tool_call_id` 角色和消息进入 `messages` 的主要位置已展示；无需另造具体 ID 示例；见下方最新评估 |
| W1-03 | 最小 CLI 可以普通回答，并在连续两次输入间保留内存历史 | 通过 | 可控响应验证 CLI 两轮输入及 `system, user, assistant, user, assistant` 内存历史；模型适配仍未消费完整历史，属任务 B 待补 |
| W1-04 | 至少一次真实模型运行完成工具闭环；后续请求保留 assistant 调用和匹配的 tool 结果 | 通过 | 真实 DeepSeek 请求完成 `add(7, 11) → 18`，共 2 次模型调用；assistant 调用和 tool 结果 ID 匹配，后续请求成功得到最终回答；见下方真实运行记录 |
| W1-05 | 假模型持续请求工具时，到达调用预算后明确停止，实际模型调用次数不超限 | 通过 | 可控假模型持续请求工具时恰好调用 60/60 次后停止；第 60 次返回最终回答也能正常结束 |
| W1-06 | 有可复现的验证方法和运行轨迹，能区分正常完成、预算停止与基本失败 | 通过 | `mine/tests/verify_week01.py` 离线覆盖三条路径并打印去敏轨迹；`mine/tests/verify_week01_live.py` 真实工具运行通过；见 `mine/docs/week-01/verification.md` |
| W1-07 | 能说明自己的最小实现与 Hermes 的至少三点取舍及适用边界 | 待评估 | 尚未提交 |

本周不要求工具注册框架、文件工具、持久化、记忆、异步并发或 UI。额外实现这些能力不抵消上表中的缺项。

## 6. 第一次学习：90 分钟起步

- **0–20 分钟：** 阅读 Agent loop 文档，写下 Session、Turn、Iteration、Tool call 的定义。
- **20–45 分钟：** 定位 `run_conversation`、主循环和 `run_tool_round`，追踪 assistant 消息及 tool 结果如何进入历史。
- **45–65 分钟：** 手写“用户提问 → 模型要求工具 → 程序执行 → 模型回答”的消息序列，标出 tool_call_id。
- **65–90 分钟：** 设计自己的最小循环伪代码，明确输入、状态、继续条件、停止原因和工具错误去向。

本次结束时应该能回答：为什么工具结果需要再次交给模型？为什么要保存 assistant 的工具调用？循环在哪里可能失控？哪些决定由模型做，哪些必须由程序保证？

## 7. 评估记录

之后每次提交由助手追加：

- 评估日期与本次提交范围。
- 审阅的文件和运行证据；哪些是助手验证、哪些是你提供的结果。
- 对应验收项的结论与理由。
- 本周必须补齐的问题，以及不阻碍通过的改进建议。
- 总结论：部分完成 / 待补充或修正 / 本周完成。
- 下一步：继续本周的具体任务，或通过后创建下一周计划。

### 2026-09-24：任务 A 初稿评估

- **提交与证据：** 审阅 `mine/docs/week-01/agent-loop.md`，对照本地 Hermes 源码提交 `550d74c6` 的 `agent/conversation_loop.py`、`agent/turn_context.py`、`agent/turn_tool_round.py`、`agent/tool_executor.py`、`agent/turn_final_response.py` 和 Agent loop 文档。结论基于文件静态审阅；本次没有运行程序，用户也未提供运行记录。
- **W1-01：待补充。** 已列出四个术语和主调用链，但 Session 被限定为 Agent 创建到进程退出，与会话可持久化并恢复不符；Iteration 不宜定义成“一次 API 调用或一组工具调用”二选一，主循环的一次迭代包含模型调用后的响应处理，可能执行一轮工具；Tool call 的定义尚未写完。还需解释模型提出工具请求、程序校验执行并决定停止等职责。
- **W1-02：待补充。** `run_conversation → _run_conversation_turn → build_turn_context → normalize_model_response → run_tool_round / finish_text_response` 的主干正确。尚未分别写出普通回答和工具调用路径，也没有标出 user、assistant（含 `tool_calls`）、tool、最终 assistant 消息由谁创建、在哪个函数加入 `messages`，以及工具结果的 `tool_call_id` 如何与调用对应。尤其应注意 Hermes 先保存 assistant 工具调用再执行工具，之后追加并保存工具结果。
- **其他验收项：** W1-03 至 W1-07 本次未提交对应产出，保持待评估；任务 A 的局部评估不代表第 1 周完成。
- **最小补齐清单：** 修正四个术语；写出两条路径的消息序列及每条消息的创建者、入历史位置；补上模型与程序的职责边界，以及工具结果为何要交回模型、为何保存 assistant 工具调用。
- **不阻碍任务 A 的建议：** 继续只沿成功路径追踪，不必展开重试、兼容、恢复和持久化失败分支。
- **总结论与下一步：** 任务 A 待补充或修正；补齐笔记后可再次评估，再继续任务 B、C。本周仍在进行中。

### 2026-09-24：任务 A 修订稿复评

- **提交与证据：** 重新审阅 `mine/docs/week-01/agent-loop.md` 第 1–31 行，对照本地 Hermes 源码提交 `550d74c6`；本次仍为静态审阅，没有运行程序。保留上次评估作为历史记录。
- **W1-01：待补充，有进展。** Session 已写明可持久化，Iteration 已改为一次主循环迭代，Tool call 不再只是标题。但“通过 session 恢复进程到上次对话处”不准确：恢复的是会话状态/消息，不是原进程执行位置。工具 schema 通常作为模型请求的 `tools` 参数提供，不能笼统写成“随系统提示词告诉模型”。还缺模型提出调用、程序校验执行并控制停止等职责说明。
- **W1-02：待补充。** 第 30 行把普通回答和工具路径串成 `user → assistant 最终回复 → tool_result`，顺序错误；工具路径应先有带 `tool_calls` 的 assistant 消息，再有匹配 `tool_call_id` 的 tool 结果，之后再次调用模型得到最终 assistant 消息。`build_turn_context` 使用 `append_message`（单数）追加 user；`run_tool_round` 追加并先持久化 assistant 工具调用；工具结果由 `tool_executor` 加入 `messages` 并持久化；`finish_text_response` 追加并持久化最终 assistant 回复。第 18–20 行“消息如何进入对话历史”仍是空白，尚未逐条区分加入 `messages` 与写入 Session 数据库。
- **其他验收项：** W1-03 至 W1-07 仍无对应提交，保持待评估。
- **最小补齐清单：** 分开写普通回答和工具调用两条成功路径；逐条标注消息角色、创建者、加入 `messages` 的函数、持久化时机，并在工具调用与结果上标出相同的 `tool_call_id`；修正 Session 恢复和工具 schema 的说法，补上模型/程序职责边界。
- **总结论与下一步：** 任务 A 修订稿有实质进展，但 W1-01、W1-02 尚未达到任务 A 的验收要求；第 1 周继续进行。

### 2026-09-24：任务 A 评估范围澄清

- 上一轮复评把每条消息的 Session 数据库持久化时机列为任务 A 必补项，要求超出了本周范围。任务 A 只需说明每条消息何时加入当前 `messages` 列表、工具调用与结果怎样配对，以及下一次模型调用为何能看到工具结果。Session 只需知道它跨 Turn 关联会话，Hermes 可以持久化并恢复会话；数据库写入细节留到第 3 周。
- 因此，W1-02 的剩余必补项是分开写两条成功路径，标注 user、带 `tool_calls` 的 assistant、带匹配 `tool_call_id` 的 tool、最终 assistant 消息由谁产生及在何处加入 `messages`。无需追踪 `_flush_messages_to_session_db` 或解释崩溃恢复分支。

### 2026-09-24：任务 A 第三版复评

- **提交与证据：** 审阅 `mine/docs/week-01/agent-loop.md` 第 1–35 行，对照本地 Hermes 源码提交 `550d74c6` 中的 `turn_context.py`、`conversation_loop.py`、`turn_response_intake.py`、`turn_tool_round.py`、`tool_executor.py`、`turn_final_response.py`；静态审阅，未运行程序。
- **W1-01：待补充，概念部分基本到位。** Session 改为恢复会话状态，Iteration、Turn、Tool call 的简要说明可用于本周学习；但文中没有说明模型负责提出工具调用、程序负责校验和执行、追加工具结果、决定何时继续或停止。工具的具体来源及持久化机制本阶段无需展开。
- **W1-02：待补充，路径部分接近完成。** 已分开写出 `user → assistant` 与 `user → assistant(tool_calls) → tool(tool_call_id) → assistant`，并正确定位了 user、工具调用消息、工具结果和最终回答的主要写入函数。还需在同一个示例中明确 assistant 的某个工具调用 `id` 与 tool 消息的 `tool_call_id` 相等，并说明工具结果要随下一次请求交给模型，模型才能据此作最终回答。`perform_api_call` 获得原始模型响应，`normalize_model_response` 解析出 assistant 消息；第 34 行把 assistant 消息直接说成由前者产生，是可改进的精度问题，不单独阻止任务 A 通过。
- **最小补齐清单：** 补一段模型/程序职责划分；给工具路径写一个相同 ID 的调用与结果示例，说明为什么要把两条消息留在 `messages` 并再次调用模型。无需追踪 Session 数据库写入。
- **其他验收项与下一步：** W1-03 至 W1-07 未提交，保持待评估；本周继续进行。补齐上述两点后可结束任务 A 并开始任务 B。

### 2026-09-24：任务 A 评估调整与通过

- **调整原因：** 用户指出上一轮要求补写的职责划分段落与具体 ID 示例信息增量低。复核现有笔记后，任务 A 所需的概念、两条成功路径及主要消息写入位置已经可见；这两项额外文字不再作为通过条件。上一轮待补意见保留为历史记录，以本次结论为准。
- **W1-01：通过。** 笔记区分了 Session、Turn、Iteration、Tool call，主调用链与工具调用描述足以体现模型提出请求、程序处理工具调用的基本边界。本周不要求展开校验和恢复机制。
- **W1-02：通过。** 笔记分开写了普通回答和工具调用消息序列，并定位 user、assistant、tool 消息进入 `messages` 的主要函数；`tool(tool_call_id)` 已表达结果的关联角色。本阶段不要求具体 ID 值或 Session 数据库写入细节。
- **非阻碍性精度建议：** 第 34 行的模型响应先经 `perform_api_call` 获取，再由 `normalize_model_response` 解析为 assistant 消息；可在以后改笔记时顺手调整。
- **本周状态与下一步：** 任务 A 完成；W1-03 至 W1-07 尚未评估。继续任务 B 的最小 CLI 和内存消息循环，第 1 周仍在进行中。

### 2026-09-28：任务 B 简略实现首轮 review

- **提交与验证：** 审阅 `mine/src/agent/agent.py`、`mine/src/agent/tools.py` 和更新的 `mine/docs/week-01/agent-loop.md`。运行 `python3 -m py_compile` 通过；使用不修改源码的可控假模型分别执行普通回答、连续两次输入、一次工具闭环和持续请求工具的场景；直接运行 `python3 mine/src/agent/agent.py` 无 CLI 交互输出。未调用付费或真实模型。
- **主要问题 1（阻碍预算验收）：** `run_conversation` 将 `cur_iteration` 初始化为 0，但循环内从未增加。持续请求工具的假模型在配置上限 60 时仍发起第 62 次调用；验证用的哨兵主动抛错才结束。需要按模型调用次数推进计数，并在上限处返回明确的停止原因。
- **主要问题 2（阻碍工具协议）：** 工具路径只把 `tool` 结果加入 `conversation_history`，没有先保存带 `tool_calls` 的 assistant 消息，也没有 `id`/`tool_call_id` 配对。一次工具任务的实际消息角色为 `system, user, tool, assistant`；后续真实模型无法据此得到完整的调用与结果链。多工具调用同样需要各自的匹配结果。
- **主要问题 3（任务 B 尚不完整）：** 现有 `api_call` 使用随机选择且不读取历史，不能稳定脚本化验证输入消息或停止条件；源码没有 CLI 输入循环、真实模型适配入口或基本失败后的明确停止行为。连续两次调用同一 `Agent` 的确保留了 `system, user, assistant, user, assistant` 历史，这是已验证的进展。
- **笔记勘误：** `mine/docs/week-01/agent-loop.md` 最后一行称工具在“下一个 Iteration”调用；参考主循环在解析出 `tool_calls` 后于**当前** Iteration 执行工具，下一次 Iteration 才把结果交给模型再次调用。
- **验收映射：** W1-03 部分完成，W1-05 未通过；W1-04 尚无真实模型证据，且当前协议阻碍该项；W1-06、W1-07 未提交相应证据，保持待评估。任务 A 已通过的结论不因本次 review 改变。
- **最小下一步：** 先用可脚本化响应固定普通回答、工具调用和持续工具调用三条路径；修正调用计数与 assistant/tool 消息配对；然后补 CLI、适配入口和运行记录。保留简洁函数结构即可，无需提前实现完整工具框架。

### 2026-09-28：任务 B 第二轮 review

- **提交与验证：** 重新审阅 `mine/src/agent/agent.py`、`mine/src/agent/tools.py`；以不修改源码的可控模型验证一次含两个工具调用的请求、两次连续用户输入、持续工具调用到默认上限 60，以及第 60 次给出最终回答。以模拟 CLI 输入验证两轮对话与退出。未运行真实模型，也未看到项目内保存的验证脚本或轨迹。
- **W1-03：通过。** CLI 已读取多次用户输入并复用同一个 Agent；可控响应下能打印两轮回答，历史角色为 `system, user, assistant, user, assistant`。收到 EOF 会抛未捕获的 `EOFError`，建议处理，但不单独阻止此项通过。
- **W1-05：通过。** `cur_iteration` 现在随工具轮次增加；持续工具调用恰好在 60 次模型调用后以明确的 `RuntimeError` 停止，没有第 61 次调用。若最后一次允许的模型调用给出文本回答，则正常结束。CLI 尚未将预算异常转换为友好提示，这是后续可改进项。
- **阻碍任务 B 工具闭环的缺陷：** 工具路径在历史中追加了普通 assistant 文本，未把 `response["tool_calls"]` 保存在该 assistant 消息里。验证得到 `system → user → assistant(无 tool_calls) → tool(call_1) → tool(call_2) → assistant`；两个 tool 结果都缺少可配对的历史请求，真实模型协议无法据此重放完整闭环。
- **模型适配仍待补：** 内置 `api_call` 随机选择分支，仅读取 `last_message()`，未消费完整 `conversation_history`；没有可脚本化假模型或真实模型接入。CLI 的历史保留已验证，但“下一次模型请求接收已有历史”尚无证据。工具调用 ID 在随机假模型中固定重复，也不适合作为多轮协议验证来源。
- **其他验收项：** W1-04 未提交真实模型运行，W1-06 未提交可复现轨迹和失败分类，W1-07 未提交取舍对照，保持待评估。任务 B 仍为部分完成；任务 A 已通过的结论不变。
- **下一步：** 先让 assistant 工具消息携带本轮全部 `tool_calls`，再以可脚本化假模型检查每个调用都有匹配结果及下一次请求包含完整历史；之后接入真实模型并记录运行证据。EOF 与 CLI 异常显示可顺手改善。

### 2026-09-28：任务 B 第三轮 review

- **提交与验证：** 审阅更新的 `mine/src/agent/agent.py`；使用不修改源码的可控假模型运行一次含两个工具调用的请求、两次连续用户输入及持续工具调用到上限。未调用真实模型，未修改用户实现。
- **工具消息问题已修正：** `run_conversation` 现在将整批 `tool_calls` 加入 assistant 消息，再逐个执行工具并追加结果。实测角色顺序为 `system → user → assistant(tool_calls) → tool(call_1) → tool(call_2) → assistant`；两个结果的 `tool_call_id` 均与 assistant 中的调用对应，第二次模型调用前的历史包含完整链。
- **预算与跨 Turn 历史复核：** 持续工具调用正好在 60/60 次模型调用后停止；第二次用户输入前的请求历史包含前一轮的 `system, user, assistant`。W1-03、W1-05 继续通过。
- **仍待完成：** 内置 `api_call` 仍以随机分支和 `last_message()` 生成模拟响应；注释中的 `_send(self.conversation_history)` 尚未实现，因此当前不能证明真实模型接收完整历史。项目内未保存可脚本化假模型、验证轨迹，也无真实模型适配和运行记录。W1-04、W1-06、W1-07 保持待评估；任务 B 仍为部分完成。
- **非阻碍性建议：** 当接入真实 API 时，将当前自定义 `tool_calls` 结构转换为该 API 所需格式，并为每次工具调用提供不重复的 ID；CLI 的 EOF 和预算异常可转为正常提示。本周无需扩展成完整工具框架。

### 2026-09-28：任务 B 第四轮 review（DeepSeek 客户端初稿）

- **提交与验证：** 审阅 `mine/src/agent/client.py`、`mine/src/agent/agent.py`、`mine/src/agent/tools.py`、`mine/src/main.py` 和依赖声明。核对 [DeepSeek 官方 thinking mode 文档](https://api-docs.deepseek.com/guides/thinking_mode/) 与 Chat Completions 接口文档；当前执行环境的 `python3` 缺少 `openai`、`python-dotenv`，所以使用本地 OpenAI 替身检查请求消息，未发起付费 API 调用。未看到用户提交的真实模型运行轨迹。
- **已有进展：** `DeepseekClient.chat` 现在将完整的 `conversation_history` 传给 `chat.completions.create`，模型名 `deepseek-flash`、thinking 参数与工具 schema 符合当前官方文档。替身场景中，一次工具调用后的第二次请求包含 `system → user → assistant(tool_calls) → tool`，工具 ID 能匹配；连续两轮输入的历史也传入客户端。
- **阻碍真实 thinking 模式闭环：** 客户端启用了 thinking，并在每次请求都提供 `tools`。官方文档要求后续请求完整回传每条 assistant 消息的 `reasoning_content`，否则 API 返回 400。`run_conversation` 只将 `content`、`tool_calls` 写入历史；本地替身确认第二次模型请求和下一用户 Turn 均缺失 `reasoning_content`。需保留模型响应的这个字段，再进行真实运行验收。
- **基本失败行为缺口：** `json.loads(tool_call["function"]["arguments"])` 在工具执行的异常处理之前运行；用格式错误的参数复现 `JSONDecodeError`，历史停在 assistant 工具调用消息，没有匹配的 tool 结果，也没有明确的 CLI 停止提示。至少需要把此类失败明确报告并停止；若选择继续调用模型，则必须补匹配的错误 tool 结果。
- **验收映射：** W1-03 已有 CLI 与跨 Turn 历史证据、W1-05 已有预算证据，结论不变。W1-04 因无真实模型记录且存在上述 thinking 协议缺项继续待评估；W1-06、W1-07 仍未提交相应产出。任务 B 部分完成，第 1 周继续进行。
- **下一步：** 优先回传 `reasoning_content` 并处理格式错误的工具参数；然后在已安装依赖和已配置密钥的环境中完成一次真实工具闭环，保存去敏轨迹。无需增加多供应商框架。

### 2026-09-28：任务 B 第五轮 review

- **提交与验证：** 审阅更新的 `mine/src/agent/agent.py`，对 `agent.py`、`client.py`、`tools.py`、`main.py` 做 Python 语法解析；使用不触网的 OpenAI 客户端替身验证工具闭环、跨 Turn 历史、格式错误的工具参数和持续工具调用上限。当前执行环境未安装 `openai`、`python-dotenv`，没有发起真实 API 调用。
- **thinking 历史修正已验证：** `run_conversation` 现在直接保存客户端返回的完整 assistant 消息。替身返回 `reasoning_content` 后，工具结果之后的第二次请求包含该字段；下一用户 Turn 的请求也保留前两条 assistant 的 `reasoning_content`，符合 [DeepSeek 官方 thinking mode 文档](https://api-docs.deepseek.com/guides/thinking_mode/) 所要求的回传形式。
- **工具错误修正已验证：** 格式错误的 `function.arguments` 现在被 `run_tool` 捕获，追加具有匹配 `tool_call_id` 的错误 tool 消息，再交给下一次模型调用；未留下孤立的 assistant 工具调用。
- **预算复核：** 替身持续返回工具调用时，实际模型调用次数为 60/60，随后以预算异常停止，没有发起第 61 次请求。W1-03、W1-05 原通过结论保持。
- **验收边界：** W1-04 仍需一次真实模型工具运行记录；W1-06 仍需项目内可复现的验证方法和代表性轨迹；W1-07 仍需三点设计取舍。任务 B 的控制流和 DeepSeek 请求结构已在本地替身中验证，但本周尚未完成。CLI 的 EOF/异常提示属于非阻碍性改进。

### 2026-09-28：真实 DeepSeek 工具闭环验证

- **授权与环境：** 用户明确授权真实请求，并将 `MAX_ITERATIONS` 设为 5。使用 `mine/src/.venv/bin/python`、项目 `mine/src/.env` 和 `deepseek-flash`，仅运行合成算术问题，未输出密钥或推理正文。首次联网尝试因进程环境中的同名密钥与 `.env` 不同而返回 401；随后按 `mine/src/main.py` 的 `load_dotenv(override=True)` 行为重试成功。沙箱内的连接失败未到达 API。
- **助手实测结果：** 用户问题要求调用 `add` 计算 7+11；模型第 1 次请求返回一个 `add` 工具调用，assistant 消息含 `reasoning_content`；程序执行得 18，加入带相同 `tool_call_id` 的 tool 结果；模型第 2 次请求返回“7 加 11 的结果是 18”。最终消息角色为 `system → user → assistant(tool_calls) → tool → assistant`，实际模型调用次数 2/5。
- **W1-04：通过。** 真实模型完成工具闭环；后续请求成功处理了 assistant 调用及匹配 tool 结果，未发生此前的 thinking 协议 400 错误。该结论基于助手真实运行的去敏轨迹与已审阅的 `Agent.api_call` 历史传递路径。
- **其余状态：** W1-03、W1-05 继续通过；W1-06 仍需在项目中保存可复现的普通完成、预算停止与基本失败的验证方法和轨迹，W1-07 仍需至少三点取舍说明。第 1 周继续进行，不提前开启第 2 周。

### 2026-09-28：W1-06 可复现验证完成

- **提交范围：** 助手根据用户授权创建 `mine/tests/verify_week01.py`、`mine/tests/verify_week01_live.py` 和 `mine/docs/week-01/verification.md`；未改动用户的 Agent 实现。离线脚本使用固定响应假客户端，不需要密钥或网络；真实脚本限定最多 5 次模型调用，只输出去敏轨迹。
- **助手复核：** 执行 `mine/src/.venv/bin/python mine/tests/verify_week01.py`，退出码 0。正常工具完成：2 次调用，`add` 结果 18，`final_response`；持续工具调用：3/3 次后 `iteration_budget_exhausted`，没有第 4 次调用；格式错误参数：2 次调用，匹配 ID 的错误 tool 结果后得到最终回答，`tool_error_then_final_response`。每条轨迹含角色序列、工具名、调用 ID、结果、调用次数和结束原因。
- **真实运行：** 用户明确允许计费调用。执行 `mine/src/.venv/bin/python mine/tests/verify_week01_live.py`，退出码 0，真实 DeepSeek 使用 2/5 次模型调用完成 `add(7, 11) → 18`；调用与结果 ID 相同，两条 assistant 消息均含 `reasoning_content`。未输出密钥或推理正文；详细去敏记录在验证文档。
- **验收结论：** W1-06 通过；W1-01 至 W1-06 现均通过。W1-07 的三点实现取舍及适用边界尚未提交，第 1 周继续进行，不创建第 2 周详细计划。
