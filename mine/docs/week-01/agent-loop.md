# week-01

## 基本概念、最简会话流程

``` plantext
# 一次普通问答 / 带工具执行
turn_facade.py::agent.run_conversation() ->
    conversation_loop.py::run_conversation() ->
        _run_conversation_turn() ->
            _ctx = build_turn_context() # 构建会话上下文
            while (未达到循环上限) # 一轮会话的主循环
                _run_api_retry_loop() # 带重试地执行 api call
                normalize_model_response() # 解析模型结果
                run_tool_round() / finish_text_response() # 如果有工具调用则执行，否则准备文本结果
            return result
```

``` plaintext
# 消息如何进入对话历史
```

Session：随 agent 创建时初始化，用于将跨越多个对话轮次的内容关联在一起。可以被持久化，以及通过 session 恢复状态到上次对话处。

Turn：一次处理用户输入到模型回复消息的过程。

Iteration：是主循环的一次迭代。一次迭代中包含模型调用以及可能的一组工具调用。

Tool call：工具通常是本地定义的方法，模型回复可能认为需要调用工具获取结果以进行进一步思考，并返回决定要调用的工具名和参数。

普通回答：user -> assistant
工具调用：user -> assistant(tool_calls) -> tool(tool_call_id) -> assistant

用户输入：由用户提供，在 build_turn_context() 中追加到 messages
模型回复：1. 无 tool_calls：由 perform_api_call() 产生，在 finish_text_response() 中追加 2. 有 tool_calls：由 perform_api_call() 产生，在 run_tool_round() 中在调用工具之前追加
工具结果：由 agent._execute_tool_calls() 产生，在 _commit_tool_result() 中追加

模型 & anget 程序：模型提出工具调用；程序校验、执行、追加结果，并控制继续或停止
