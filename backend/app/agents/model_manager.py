import logging
import time
from typing import Any

import httpx

from app.config import (
    OLLAMA_BASE_URL,
    OLLAMA_FALLBACK_MODELS,
    OLLAMA_PRIMARY_MODEL,
)

logger = logging.getLogger(__name__)


class ModelManager:
    """
    Manages AI model inference, fallback, and discovery via self-hosted Ollama.
    Target endpoint: https://ollama.calmalpha.in/
    """

    def __init__(self, base_url: str | None = None):
        self.base_url = (base_url or OLLAMA_BASE_URL).rstrip("/")
        self.primary_model = OLLAMA_PRIMARY_MODEL
        self.fallback_models = OLLAMA_FALLBACK_MODELS
        self.model_hierarchy = [self.primary_model] + [
            m for m in self.fallback_models if m != self.primary_model
        ]

    def get_available_models(self) -> list[dict[str, Any]]:
        """Fetch list of available models from Ollama."""
        try:
            with httpx.Client(timeout=15.0) as client:
                res = client.get(f"{self.base_url}/api/tags")
                if res.status_code == 200:
                    return res.json().get("models", [])
        except Exception as e:
            logger.error(f"Failed to fetch Ollama models: {e}")
        return []

    async def get_available_models_async(self) -> list[dict[str, Any]]:
        """Asynchronously fetch list of available models from Ollama."""
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.get(f"{self.base_url}/api/tags")
                if res.status_code == 200:
                    return res.json().get("models", [])
        except Exception as e:
            logger.error(f"Failed to fetch Ollama models: {e}")
        return []

    def generate_chat_completion(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2500,
        retry_index: int = 0,
    ) -> dict[str, Any]:
        """Generate response with automatic model fallback."""
        if model and retry_index == 0:
            target_models = [model] + [m for m in self.model_hierarchy if m != model]
        else:
            target_models = self.model_hierarchy

        if retry_index >= len(target_models):
            return {
                "success": False,
                "error": "All Ollama models failed to generate response. Please check Ollama server status.",
            }

        current_model = target_models[retry_index]
        payload = {
            "model": current_model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        try:
            with httpx.Client(timeout=120.0) as client:
                res = client.post(f"{self.base_url}/api/chat", json=payload)
                if res.status_code == 200:
                    data = res.json()
                    return {
                        "success": True,
                        "content": data.get("message", {}).get("content", ""),
                        "model_used": current_model,
                    }
                else:
                    logger.warning(f"Ollama HTTP {res.status_code} for {current_model}: {res.text}")
        except Exception as e:
            logger.warning(f"Ollama generation failed for {current_model}: {e}")

        time.sleep(1)
        return self.generate_chat_completion(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            retry_index=retry_index + 1,
        )

    async def generate_chat_completion_async(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2500,
        retry_index: int = 0,
    ) -> dict[str, Any]:
        """Asynchronously generate response with automatic model fallback."""
        if model and retry_index == 0:
            target_models = [model] + [m for m in self.model_hierarchy if m != model]
        else:
            target_models = self.model_hierarchy

        if retry_index >= len(target_models):
            return {
                "success": False,
                "error": "All Ollama models failed to generate response. Please check Ollama server status.",
            }

        current_model = target_models[retry_index]
        payload = {
            "model": current_model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                res = await client.post(f"{self.base_url}/api/chat", json=payload)
                if res.status_code == 200:
                    data = res.json()
                    return {
                        "success": True,
                        "content": data.get("message", {}).get("content", ""),
                        "model_used": current_model,
                    }
                else:
                    logger.warning(
                        f"Ollama async HTTP {res.status_code} for {current_model}: {res.text}"
                    )
        except Exception as e:
            logger.warning(f"Ollama async generation failed for {current_model}: {e}")

        return await self.generate_chat_completion_async(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            retry_index=retry_index + 1,
        )

    async def stream_chat_completion_async(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2500,
    ):
        """Asynchronously stream tokens from Ollama chat completion."""
        target_model = model or self.primary_model
        payload = {
            "model": target_model,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        try:
            async with (
                httpx.AsyncClient(timeout=120.0) as client,
                client.stream("POST", f"{self.base_url}/api/chat", json=payload) as response,
            ):
                if response.status_code != 200:
                    logger.warning(
                        f"Streaming error HTTP {response.status_code} on {target_model}, falling back to non-streaming"
                    )
                    fallback_res = await self.generate_chat_completion_async(
                        messages=messages,
                        model=model,
                        temperature=temperature,
                        max_tokens=max_tokens,
                    )
                    if fallback_res.get("success"):
                        yield {
                            "token": fallback_res.get("content", ""),
                            "done": True,
                            "model": fallback_res.get("model_used"),
                        }
                    else:
                        yield {
                            "error": fallback_res.get("error", "Failed to stream response"),
                            "done": True,
                        }
                    return

                async for line in response.aiter_lines():
                    if not line:
                        continue
                    try:
                        import json

                        data = json.loads(line)
                        token = data.get("message", {}).get("content", "")
                        is_done = data.get("done", False)
                        yield {"token": token, "done": is_done, "model": target_model}
                        if is_done:
                            break
                    except Exception:
                        continue
        except Exception as e:
            logger.error(f"Error during Ollama stream: {e}")
            fallback_res = await self.generate_chat_completion_async(
                messages=messages, model=model, temperature=temperature, max_tokens=max_tokens
            )
            if fallback_res.get("success"):
                yield {
                    "token": fallback_res.get("content", ""),
                    "done": True,
                    "model": fallback_res.get("model_used"),
                }
            else:
                yield {"error": str(e), "done": True}
