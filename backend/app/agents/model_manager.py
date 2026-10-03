import logging
import time
from typing import Dict, Any, List, Optional
import httpx
from app.config import (
    OLLAMA_BASE_URL,
    OLLAMA_PRIMARY_MODEL,
    OLLAMA_FALLBACK_MODELS,
)

logger = logging.getLogger(__name__)


class ModelManager:
    """
    Manages AI model inference, fallback, and discovery via self-hosted Ollama.
    Target endpoint: https://ollama.calmalpha.in/
    """

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = (base_url or OLLAMA_BASE_URL).rstrip("/")
        self.primary_model = OLLAMA_PRIMARY_MODEL
        self.fallback_models = OLLAMA_FALLBACK_MODELS
        self.model_hierarchy = [self.primary_model] + [
            m for m in self.fallback_models if m != self.primary_model
        ]

    def get_available_models(self) -> List[Dict[str, Any]]:
        """Fetch list of available models from Ollama."""
        try:
            with httpx.Client(timeout=15.0) as client:
                res = client.get(f"{self.base_url}/api/tags")
                if res.status_code == 200:
                    return res.json().get("models", [])
        except Exception as e:
            logger.error(f"Failed to fetch Ollama models: {e}")
        return []

    async def get_available_models_async(self) -> List[Dict[str, Any]]:
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
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2500,
        retry_index: int = 0,
    ) -> Dict[str, Any]:
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
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2500,
        retry_index: int = 0,
    ) -> Dict[str, Any]:
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
                    logger.warning(f"Ollama async HTTP {res.status_code} for {current_model}: {res.text}")
        except Exception as e:
            logger.warning(f"Ollama async generation failed for {current_model}: {e}")

        return await self.generate_chat_completion_async(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            retry_index=retry_index + 1,
        )
