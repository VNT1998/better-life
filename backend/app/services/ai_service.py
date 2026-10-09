import logging
from typing import Any, Optional

from app.agents.analysis_agent import AnalysisAgent
from app.agents.chat_agent import ChatAgent
from app.agents.model_manager import ModelManager

logger = logging.getLogger(__name__)


class AIService:
    _instance: Optional["AIService"] = None

    def __init__(self):
        self.model_manager = ModelManager()
        self.analysis_agent = AnalysisAgent(model_manager=self.model_manager)
        self.chat_agent = ChatAgent(model_manager=self.model_manager)

    @classmethod
    def get_instance(cls) -> "AIService":
        if cls._instance is None:
            cls._instance = AIService()
        return cls._instance

    def check_rate_limit(self, user_id: str = "default"):
        return self.analysis_agent.check_rate_limit(user_id)

    def get_remaining_limit(self, user_id: str = "default") -> int:
        return self.analysis_agent.get_remaining_limit(user_id)

    def generate_analysis(
        self,
        data: dict[str, Any],
        system_prompt: str,
        user_id: str = "default",
        model: str | None = None,
        check_only: bool = False,
    ) -> dict[str, Any]:
        return self.analysis_agent.analyze_report(
            data=data,
            system_prompt=system_prompt,
            user_id=user_id,
            model=model,
            check_only=check_only,
        )

    async def generate_analysis_async(
        self,
        data: dict[str, Any],
        system_prompt: str,
        user_id: str = "default",
        model: str | None = None,
        check_only: bool = False,
    ) -> dict[str, Any]:
        return await self.analysis_agent.analyze_report_async(
            data=data,
            system_prompt=system_prompt,
            user_id=user_id,
            model=model,
            check_only=check_only,
        )

    def get_chat_response(
        self,
        query: str,
        context_text: str,
        chat_history: list[dict[str, str]] | None = None,
        model: str | None = None,
    ) -> dict[str, Any]:
        return self.chat_agent.get_response(
            query=query,
            context_text=context_text,
            chat_history=chat_history,
            model=model,
        )

    async def get_chat_response_async(
        self,
        query: str,
        context_text: str,
        chat_history: list[dict[str, str]] | None = None,
        model: str | None = None,
    ) -> dict[str, Any]:
        return await self.chat_agent.get_response_async(
            query=query,
            context_text=context_text,
            chat_history=chat_history,
            model=model,
        )

    async def stream_chat_response_async(
        self,
        query: str,
        context_text: str,
        chat_history: list[dict[str, str]] | None = None,
        model: str | None = None,
    ):
        async for chunk in self.chat_agent.stream_response_async(
            query=query,
            context_text=context_text,
            chat_history=chat_history,
            model=model,
        ):
            yield chunk

    async def get_available_models(self) -> list[dict[str, Any]]:
        return await self.model_manager.get_available_models_async()


def get_ai_service() -> AIService:
    return AIService.get_instance()
