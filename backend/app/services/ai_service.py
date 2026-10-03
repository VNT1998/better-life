import logging
from typing import Dict, Any, Optional, List
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
        data: Dict[str, Any],
        system_prompt: str,
        user_id: str = "default",
        model: Optional[str] = None,
        check_only: bool = False,
    ) -> Dict[str, Any]:
        return self.analysis_agent.analyze_report(
            data=data,
            system_prompt=system_prompt,
            user_id=user_id,
            model=model,
            check_only=check_only,
        )

    async def generate_analysis_async(
        self,
        data: Dict[str, Any],
        system_prompt: str,
        user_id: str = "default",
        model: Optional[str] = None,
        check_only: bool = False,
    ) -> Dict[str, Any]:
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
        chat_history: Optional[List[Dict[str, str]]] = None,
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
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
        chat_history: Optional[List[Dict[str, str]]] = None,
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        return await self.chat_agent.get_response_async(
            query=query,
            context_text=context_text,
            chat_history=chat_history,
            model=model,
        )

    async def get_available_models(self) -> List[Dict[str, Any]]:
        return await self.model_manager.get_available_models_async()


def get_ai_service() -> AIService:
    return AIService.get_instance()
