import json
import re
from openai import OpenAI


class DeepSeekClient:
    def __init__(self, api_key: str, base_url: str = "https://api.deepseek.com", model: str = "deepseek-chat"):
        self.base_url = base_url
        self.model = model
        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def chat_json(self, messages: list[dict], temperature: float = 0.3, max_tokens: int = 8192) -> dict:
        # DeepSeek requires "json" in the prompt for json_object response_format
        msgs = [dict(m) for m in messages]
        if msgs and msgs[0]["role"] == "system":
            msgs[0] = {**msgs[0], "content": msgs[0]["content"] + "\n请以JSON格式输出。"}
        response = self.client.chat.completions.create(
            model=self.model,
            messages=msgs,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content.strip()

        if raw.startswith("```"):
            raw = re.sub(r"^```(?:json)?\s*\n", "", raw)
            raw = re.sub(r"\n```\s*$", "", raw)

        return json.loads(raw)
