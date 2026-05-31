"""LLM 客户端 — 封装 OpenAI 兼容接口调用"""

import logging
import time
from dataclasses import dataclass

from openai import AsyncOpenAI

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class LLMResponse:
    content: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    latency_ms: float


class LLMClient:
    """OpenAI 兼容的 LLM 客户端，支持 DeepSeek / GPT-4o / Qwen 等"""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ):
        self.api_key = api_key or settings.llm_api_key
        self.base_url = base_url or settings.llm_base_url
        self.model = model or settings.llm_model
        self.temperature = temperature if temperature is not None else settings.llm_temperature
        self.max_tokens = max_tokens or settings.llm_max_tokens

        client_kwargs = {"api_key": self.api_key}
        if self.base_url:
            client_kwargs["base_url"] = self.base_url
        self._client = AsyncOpenAI(**client_kwargs)

    async def chat(
        self,
        prompt: str,
        system: str | None = None,
        model: str | None = None,
    ) -> LLMResponse:
        """发送聊天请求，返回 LLMResponse"""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        target_model = model or self.model
        start = time.time()

        try:
            response = await self._client.chat.completions.create(
                model=target_model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
        except Exception as e:
            logger.error("LLM call failed (model=%s): %s", target_model, e)
            raise

        latency = (time.time() - start) * 1000
        choice = response.choices[0]
        usage = response.usage

        return LLMResponse(
            content=choice.message.content or "",
            model=target_model,
            prompt_tokens=usage.prompt_tokens if usage else 0,
            completion_tokens=usage.completion_tokens if usage else 0,
            total_tokens=usage.total_tokens if usage else 0,
            latency_ms=latency,
        )

    async def chat_with_messages(
        self,
        messages: list[dict],
        model: str | None = None,
    ) -> LLMResponse:
        """使用预构造的消息列表发送请求"""
        target_model = model or self.model
        start = time.time()

        try:
            response = await self._client.chat.completions.create(
                model=target_model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
        except Exception as e:
            logger.error("LLM call failed (model=%s): %s", target_model, e)
            raise

        latency = (time.time() - start) * 1000
        choice = response.choices[0]
        usage = response.usage

        return LLMResponse(
            content=choice.message.content or "",
            model=target_model,
            prompt_tokens=usage.prompt_tokens if usage else 0,
            completion_tokens=usage.completion_tokens if usage else 0,
            total_tokens=usage.total_tokens if usage else 0,
            latency_ms=latency,
        )
