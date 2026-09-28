from typing import Any
import abc
import os



class Client(abc.ABC):
    @abc.abstractmethod
    def chat(self, messages: list[dict[str, str]], **kwargs) -> dict[str, Any]:
        pass

class DeepseekClient(Client):
    def __init__(self, api_key: str = "", base_url: str = "https://api.deepseek.com", tools: list = None):
        self.api_key = api_key or os.environ.get("DEEPSEEK_API_KEY")
        self.base_url = base_url
        self.tools = tools or []
        from openai import OpenAI
        self.openai_client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    def chat(self, messages: list[dict[str, str]], **kwargs) -> dict[str, Any]:
        # For now, we'll just return a mock response
        response = self.openai_client.chat.completions.create(
            model="deepseek-flash",
            messages=messages,
            stream=False,
            reasoning_effort="high",
            extra_body={"thinking": {"type": "enabled"}},
            tools=self.tools,
            **kwargs
        )
        return response.choices[0].message.to_dict()
