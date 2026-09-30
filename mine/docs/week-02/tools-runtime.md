# week-02

## 工具运行时

自注册函数、分组管理（`registry.register()`）；中心化注册分发（`model_tools.py`）

工具可用性检查、缓存调用（check_fn）

工具过滤（按显式启用、显式禁用、可用性检查失败）

调度流程：agent -> (relay_tools) -> 模型工具入口 -> 调度中心分发 -> 同步/异步处理器 -> 具体函数

错误包装：1. 工具入口处 try-catch （针对调度） 2. 分发处 try-catch （针对handler）

agent 级工具在 dispatch 前被拦截并直接在 agent-loop 中处理，如果意外到达 handler 则直接报错。

* todo_list - plan/task 追踪
* memory - 写持久化记忆
* session_search - 跨会话 recall
* delegate_task - 分派子 agent task

命令行工具执行前需要通过危险性检查（regex 匹配），然后通过放行策略

hermes 加了一个 NaMo Relay 层包装 tool 执行管线，用来追踪 tool 执行情况。实际的管线从 `model_tools.handle_function_call()` 开始

## QA

Q：工具是怎么传给模型的

A：agent 初始决定 `enabled_toolsets` 和 `disabled_toolsets，通过` `model_tools.get_tool_definitions()` 获得 `tools_schema` 并记录，之后模型调用时作为参数使用。

Q：程序怎么将工具名映射到具体的工具，并怎么解析和传递参数，怎么判定工具名或参数有效

A：程序会将模型返回的 tool_call 中的方法名与本地持有的方法名进行比较，如果没找到会尝试修复方法名（模型幻觉），如果仍没有记为无效方法。

有效方法与无效方法混合：告知无效方法，调用有效方法

仅无效方法：告知无效方法，让模型尝试修复幻觉，连续重复三次后终止 turn

对于方法参数，程序会尝试将格式统一为 dict。

参数截断：终止 turn

JSON 格式错误：重试请求，如果重试3次仍出现，则将错误告知模型。

Q：为什么结果 id 需要与调用 id 对应

A：模型侧无状态，但能看到携带的历史。因此能够通过 id 将工具调用与工具结果联系起来。

Q：什么情况下工具错误应该停止 turn

A：参照上述，当无效方法连续重复三次时、当方法参数被截断时
