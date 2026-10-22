# session sotrage

(session 与 message 的关系、怎么保存的、怎么恢复的)

session 用 sqllite 存的，建了两张表，sessions 和 messages，用 session_id 关联。多个程序只有一个 state.db，内部机制避免写入冲突。db 文件默认存在 ~/.hermes/state.db

DB 类以 session_id 处理 message 写入和查询。

session 追踪：

* 新建 session：hermes 没有 session 对象，session 相关值直接作为 agent 属性存在，例如 session_id、session_messages、session_db 等。在 `run_agent.py::init_agent()` 时新建。
* 保存 session：保存动作位于 `session_persistence.py :: _flush_messages_to_session_db() / _persist_session()`，当接下来的动作存在风险时，预先将 session 保存，例如：

  * turn 刚开始，首次 llm 调用前：崩溃后用户输入不丢
  * 工具执行后：崩溃后工具结果不丢
    * 对于并行工具执行，这样的好处是避免副作用发生了，而程序不知道。例如 tool_a 写了文件，tool_b 引发了崩溃，已记录的执行结果就可以避免再次修改文件。
  * 产生最终回复后，离开循环前：中间不涉及工具调用，assistant 最终回复不丢
  * 中断 / 错误 / 恢复路径

* 恢复 session：以 CLI 为例，从 `cli_agent_setup_mixin.py::_preload_resumed_session()` 恢复。
