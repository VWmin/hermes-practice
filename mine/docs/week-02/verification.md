# 第 2 周离线验证记录

记录日期：2026-09-30。验证对象：`mine/src/agent/` 的工具注册、分发、错误结果和笔记目录边界。

## 运行方法

在仓库根目录执行：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 mine/tests/verify_week02.py
PYTHONDONTWRITEBYTECODE=1 python3 mine/tests/verify_week01.py
```

两个命令本次退出码均为 **0**。W2 脚本以固定响应的假客户端代替 DeepSeek，保留真实的 Agent 循环、注册表和工具函数；它会保存每次模型请求的消息快照，并在运行期间统计 handler 调用次数和成功次数。脚本不读取密钥、不联网、不输出笔记正文。目录越界场景临时创建一个指向目录外的符号链接，运行结束后自动删除。

## W2-05 三条轨迹

| 场景 | 模型调用 | 消息角色顺序 | 工具调用与结果 ID 顺序 | handler 调用 / 成功 | 结束原因 |
| --- | ---: | --- | --- | --- | --- |
| 正常双工具批次 | 2 | `system → user → assistant → tool → tool → assistant` | `add:normal_add`、`read_docs:normal_read`；结果依次为 `normal_add`、`normal_read` | `add` 1/1，`read_docs` 1/1 | `final_response` |
| 混合错误批次 | 2 | `system → user → assistant → tool → tool → tool → assistant` | 未知工具 `unknown`、无效 JSON `bad_json`、有效 `add:valid_add`；结果保持同一顺序 | `add` 1/1；前两项未调用 handler | `final_response` |
| 目录越界批次 | 2 | `system → user → assistant → tool → tool → tool → assistant` | 相对越界 `relative_escape`、绝对越界 `absolute_escape`、符号链接越界 `symlink_escape`；结果保持同一顺序 | `read_docs` 3/0；三次均拒绝读取 | `final_response` |

正常批次的 `add(7,11)` 数值结果为 18，`read_docs` 返回的正文不超过 1024 字符；第二次模型请求含两个 assistant 工具调用和两个匹配的 tool 结果。混合错误批次只有有效 `add` 调用了处理函数并得到数值 18，其余两项分别返回未知工具和无效 JSON 错误。目录越界批次的三个结果均为错误，没有返回目录外的文件内容。脚本对这些关系和实际调用次数做断言；不满足时以非零状态退出。

第 1 周回归脚本也重新通过了普通工具完成、预算耗尽及格式错误参数三条路径。原脚本对错误文案的硬编码断言已改为检查错误语义与结果 ID 配对；数字结果允许 `18` 或 `18.0`，以数值是否为 18 为准。

## 范围

以上三条是可重复的离线验证；根据本周已确定的范围，无法转换但仍被处理函数接受的语义不作为 W2-05 的阻碍，参数预处理异常和工具结果配对仍由脚本覆盖。

## W2-06 真实模型笔记工具验证

此命令会调用计费 API。项目虚拟环境需安装 `mine/src/requirements.txt` 中的依赖，并在 `mine/src/.env` 配置 `DEEPSEEK_API_KEY`：

```bash
PYTHONDONTWRITEBYTECODE=1 mine/src/.venv/bin/python mine/tests/verify_week02_live.py
```

脚本仅向模型提供 `read_docs` schema，且本次运行临时限制 handler 只可读取[合成测试笔记](live-fixture.md)；任何其他路径都返回错误。合成笔记只含测试标题与标记，没有用户笔记、凭据或私人内容。脚本将模型调用上限设为 5，只打印角色、工具名和 ID、结果长度、是否存在推理字段及结束原因，不输出文件正文或推理内容。该限制只作用于本次验证脚本，不改变日常 Agent 的工具配置。

2026-09-30 助手真实运行结果：退出码 **0**，模型调用 **2/5** 次，消息角色为 `system → user → assistant(tool_calls) → tool → assistant`。模型调用 `read_docs` 一次；调用与结果使用同一个 ID（文档中记为 `call_live_1`），工具读取成功，正文长度为 189 字符；第二次模型请求包含该 tool 结果。两条 assistant 消息均含 `reasoning_content`，最终回答识别了合成标题 `W2FIXTURE`，结束原因为 `final_response`。

最初针对现有本地学习笔记的联网请求被自动审批阻止，未发给 API；自动审批指出“允许计费”并不等于授权把私人笔记内容发往外部服务。随后改用明确的合成笔记和单文件读取限制，才完成上述真实验证。W2-06 要求的两点与 Hermes 的取舍仍需另行记录。
