# 第 1 周验证记录

记录日期：2026-09-28。验证对象：`mine/src/agent/` 的内存会话和工具循环。

## 可重复运行的离线验证

在仓库根目录运行：

```bash
mine/src/.venv/bin/python mine/tests/verify_week01.py
```

脚本使用固定响应的假客户端，不读取 API 密钥，也不发起网络请求。每个场景都会断言消息顺序、工具调用与结果的 ID 关系、模型调用次数和结束行为；全部通过时退出码为 0，并打印三条 JSON 轨迹。

| 场景 | 实际模型调用次数 | 消息角色顺序 | 工具名与调用 ID | 结束原因 |
| --- | ---: | --- | --- | --- |
| 正常工具任务 | 2 | `system → user → assistant → tool → assistant` | `add`，`call_ok`；结果 ID 相同，结果为 18 | `final_response` |
| 持续请求工具 | 3/3 | `system → user → (assistant → tool) × 3` | `add`，`call_1`、`call_2`、`call_3`；结果逐一匹配 | `iteration_budget_exhausted`，未发起第 4 次请求 |
| 工具参数格式错误 | 2 | `system → user → assistant → tool → assistant` | `add`，`call_bad`；同 ID 的 tool 结果说明 JSON 参数错误 | `tool_error_then_final_response` |

正常任务的第二次模型请求包含 assistant 工具调用、匹配的 tool 结果及 `reasoning_content`。格式错误时，程序将异常写为 tool 结果，模型随后返回解释。以上轨迹由助手在本地实际运行并核对，完整去敏字段由脚本逐次输出。

## 真实模型工具任务

此命令会调用计费 API。项目虚拟环境需安装 `mine/src/requirements.txt` 中的依赖，并在 `mine/src/.env` 中配置 `DEEPSEEK_API_KEY`：

```bash
mine/src/.venv/bin/python mine/tests/verify_week01_live.py
```

脚本按 CLI 一样使用 `load_dotenv(override=True)`，将模型调用上限设为 5，请求 DeepSeek 调用 `add` 计算 7+11。它只输出消息角色、工具名与 ID、工具结果、模型调用次数、最终回答、结束原因以及是否存在推理字段；不输出 API 密钥或推理正文。

2026-09-28 助手真实运行结果：**2/5 次模型调用**，消息顺序为 `system → user → assistant(tool_calls) → tool → assistant`，`add` 返回 18，最终回答为“7 + 11 = 18”，结束原因为 `final_response`。assistant 工具调用与 tool 结果使用同一个 ID（文档中记为 `call_live_1`）；两条 assistant 消息均带有 `reasoning_content`。该次命令退出码为 0。

## 范围与限制

- 预算停止和工具参数错误使用可控假客户端验证，避免随机响应影响结果。
- 真实运行验证了一次成功的工具闭环；网络错误、认证失败和 CLI 的 EOF 处理不属于这三条验收轨迹。
- 真实模型每次输出和调用 ID 可能不同；判断条件是调用与结果 ID 相等、结果为 18、最终回答包含 18，且调用次数不超过 5。
