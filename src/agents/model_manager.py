import logging
import time
from typing import Dict, Any, List, Optional
import httpx
from config.app_config import (
    OLLAMA_BASE_URL,
    OLLAMA_PRIMARY_MODEL,
    OLLAMA_FALLBACK_MODELS,
)

logger = logging.getLogger(__name__)


class ModelManager:
    """
    Manages AI model selection, fallback, and inference via self-hosted Ollama.
    Endpoint: https://ollama.calmalpha.in/
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
                response = client.get(f"{self.base_url}/api/tags")
                if response.status_code == 200:
                    data = response.json()
                    return data.get("models", [])
        except Exception as e:
            logger.error(f"Failed to fetch Ollama models: {e}")
        return []

    async def get_available_models_async(self) -> List[Dict[str, Any]]:
        """Asynchronously fetch list of available models from Ollama."""
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                if response.status_code == 200:
                    data = response.json()
                    return data.get("models", [])
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
        """
        Generate chat response using Ollama with automatic fallback across models.
        """
        if model and retry_index == 0:
            target_models = [model] + [m for m in self.model_hierarchy if m != model]
        else:
            target_models = self.model_hierarchy

        if retry_index >= len(target_models):
            return {
                "success": False,
                "error": "All Ollama models failed to generate response. Please check server status.",
            }

        current_model = target_models[retry_index]
        logger.info(f"Attempting generation with Ollama model: {current_model} (attempt {retry_index + 1})")

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
            # Model switching or cold starts can take up to 90-120 seconds
            with httpx.Client(timeout=120.0) as client:
                res = client.post(f"{self.base_url}/api/chat", json=payload)
                if res.status_code == 200:
                    data = res.json()
                    msg_content = data.get("message", {}).get("content", "")
                    return {
                        "success": True,
                        "content": msg_content,
                        "model_used": current_model,
                        "total_duration": data.get("total_duration"),
                    }
                else:
                    logger.warning(
                        f"Ollama returned HTTP {res.status_code} for {current_model}: {res.text}"
                    )
        except Exception as e:
            logger.warning(f"Ollama generation failed for {current_model}: {e}")

        # Sleep briefly before fallback retry
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
        """
        Asynchronously generate chat response with fallback.
        """
        if model and retry_index == 0:
            target_models = [model] + [m for m in self.model_hierarchy if m != model]
        else:
            target_models = self.model_hierarchy

        if retry_index >= len(target_models):
            return {
                "success": False,
                "error": "All Ollama models failed to generate response. Please check server status.",
            }

        current_model = target_models[retry_index]
        logger.info(f"Async generation with Ollama model: {current_model} (attempt {retry_index + 1})")

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
                    msg_content = data.get("message", {}).get("content", "")
                    return {
                        "success": True,
                        "content": msg_content,
                        "model_used": current_model,
                        "total_duration": data.get("total_duration"),
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

    def generate_analysis(
        self, data: Any, system_prompt: str, model: Optional[str] = None, retry_count: int = 0
    ) -> Dict[str, Any]:
        """
        Generate blood report analysis using Ollama.
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": str(data)},
        ]
        return self.generate_chat_completion(
            messages=messages, model=model, retry_index=retry_count
        )

    async def generate_analysis_async(
        self, data: Any, system_prompt: str, model: Optional[str] = None, retry_count: int = 0
    ) -> Dict[str, Any]:
        """
        Generate blood report analysis asynchronously using Ollama.
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": str(data)},
        ]
        return await self.generate_chat_completion_async(
            messages=messages, model=model, retry_index=retry_count
        )
