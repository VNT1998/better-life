import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from agents.model_manager import ModelManager
from config.app_config import ANALYSIS_DAILY_LIMIT

logger = logging.getLogger(__name__)


class AnalysisAgent:
    """
    Agent responsible for managing report analysis, rate limiting,
    and implementing in-context learning from previous analyses using Ollama.
    """

    def __init__(self, model_manager: Optional[ModelManager] = None):
        self.model_manager = model_manager or ModelManager()
        # In-memory stores: user_id -> state dict
        self._user_analytics: Dict[str, Dict[str, Any]] = {}
        # Knowledge base of learned indicators across analyses
        self._knowledge_base: Dict[str, Dict[str, List[str]]] = {}

    def _get_user_state(self, user_id: str) -> Dict[str, Any]:
        if user_id not in self._user_analytics:
            self._user_analytics[user_id] = {
                "analysis_count": 0,
                "last_analysis": datetime.now(),
                "daily_limit": ANALYSIS_DAILY_LIMIT,
                "models_used": {},
            }
        return self._user_analytics[user_id]

    def get_remaining_limit(self, user_id: str = "default") -> int:
        state = self._get_user_state(user_id)
        # Check if reset needed (24 hours)
        if datetime.now() - state["last_analysis"] > timedelta(days=1):
            state["analysis_count"] = 0
            state["last_analysis"] = datetime.now()
        return max(0, state["daily_limit"] - state["analysis_count"])

    def check_rate_limit(self, user_id: str = "default") -> Tuple[bool, Optional[str]]:
        """Check if user has reached their daily analysis limit."""
        state = self._get_user_state(user_id)
        time_until_reset = timedelta(days=1) - (datetime.now() - state["last_analysis"])

        # Reset counter after 24 hours
        if time_until_reset.days < 0 or datetime.now() - state["last_analysis"] > timedelta(days=1):
            state["analysis_count"] = 0
            state["last_analysis"] = datetime.now()
            return True, None

        hours, remainder = divmod(max(0, int(time_until_reset.total_seconds())), 3600)
        minutes, _ = divmod(remainder, 60)

        if state["analysis_count"] >= state["daily_limit"]:
            error_msg = f"Daily limit reached ({state['daily_limit']}/day). Reset in {hours}h {minutes}m"
            return False, error_msg

        return True, None

    def analyze_report(
        self,
        data: Dict[str, Any],
        system_prompt: str,
        user_id: str = "default",
        model: Optional[str] = None,
        check_only: bool = False,
        chat_history: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """
        Analyze report data using in-context learning from previous analyses.
        """
        can_analyze, error_msg = self.check_rate_limit(user_id)
        if not can_analyze:
            return {"success": False, "error": error_msg}

        if check_only:
            return {"success": True, "error": None}

        processed_data = self._preprocess_data(data)
        enhanced_prompt = (
            self._build_enhanced_prompt(system_prompt, processed_data, chat_history)
            if chat_history
            else system_prompt
        )

        result = self.model_manager.generate_analysis(
            processed_data, enhanced_prompt, model=model
        )

        if result.get("success"):
            self._update_analytics(user_id, result)
            self._update_knowledge_base(processed_data, result.get("content", ""))

        return result

    async def analyze_report_async(
        self,
        data: Dict[str, Any],
        system_prompt: str,
        user_id: str = "default",
        model: Optional[str] = None,
        check_only: bool = False,
        chat_history: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """
        Asynchronously analyze report data.
        """
        can_analyze, error_msg = self.check_rate_limit(user_id)
        if not can_analyze:
            return {"success": False, "error": error_msg}

        if check_only:
            return {"success": True, "error": None}

        processed_data = self._preprocess_data(data)
        enhanced_prompt = (
            self._build_enhanced_prompt(system_prompt, processed_data, chat_history)
            if chat_history
            else system_prompt
        )

        result = await self.model_manager.generate_analysis_async(
            processed_data, enhanced_prompt, model=model
        )

        if result.get("success"):
            self._update_analytics(user_id, result)
            self._update_knowledge_base(processed_data, result.get("content", ""))

        return result

    def _update_analytics(self, user_id: str, result: Dict[str, Any]):
        state = self._get_user_state(user_id)
        state["analysis_count"] += 1
        state["last_analysis"] = datetime.now()

        model_used = result.get("model_used", "unknown")
        state["models_used"][model_used] = state["models_used"].get(model_used, 0) + 1

    def _update_knowledge_base(self, data: Dict[str, Any], analysis: str):
        if not isinstance(data, dict) or "report" not in data:
            return

        report_text = data["report"].lower()
        patient_profile = f"{data.get('age', 'unknown')}-{data.get('gender', 'unknown')}"

        key_indicators = [
            "hemoglobin",
            "glucose",
            "cholesterol",
            "triglycerides",
            "hdl",
            "ldl",
            "wbc",
            "rbc",
            "platelet",
            "creatinine",
        ]

        for indicator in key_indicators:
            if indicator in report_text and indicator in analysis.lower():
                if indicator not in self._knowledge_base:
                    self._knowledge_base[indicator] = {}

                if patient_profile not in self._knowledge_base[indicator]:
                    self._knowledge_base[indicator][patient_profile] = []

                lines = analysis.split("\n")
                relevant_lines = [l.strip() for l in lines if indicator in l.lower() and len(l.strip()) > 10]
                if relevant_lines:
                    if len(self._knowledge_base[indicator][patient_profile]) >= 3:
                        self._knowledge_base[indicator][patient_profile].pop(0)
                    self._knowledge_base[indicator][patient_profile].append(relevant_lines[0])

    def _build_enhanced_prompt(
        self, system_prompt: str, data: Dict[str, Any], chat_history: Optional[List[Dict[str, str]]]
    ) -> str:
        enhanced_prompt = system_prompt
        kb_context = self._get_knowledge_base_context(data)
        if kb_context:
            enhanced_prompt += "\n\n## Relevant Insights From Previous Analyses\n" + kb_context

        if chat_history:
            session_context = self._get_session_context(chat_history)
            if session_context:
                enhanced_prompt += "\n\n## Current Session History\n" + session_context

        return enhanced_prompt

    def _get_knowledge_base_context(self, data: Dict[str, Any]) -> str:
        if not self._knowledge_base:
            return ""

        report_text = data.get("report", "").lower()
        patient_profile = f"{data.get('age', 'unknown')}-{data.get('gender', 'unknown')}"
        context_items = []

        for indicator, profiles in self._knowledge_base.items():
            if indicator in report_text:
                if patient_profile in profiles:
                    for insight in profiles[patient_profile]:
                        context_items.append(f"- {indicator} (similar patient): {insight}")
                for profile, insights in profiles.items():
                    if profile != patient_profile:
                        for insight in insights:
                            context_items.append(f"- {indicator}: {insight}")

        if len(context_items) > 5:
            context_items = context_items[:5]

        return "\n".join(context_items) if context_items else ""

    def _get_session_context(self, chat_history: List[Dict[str, str]]) -> str:
        if not chat_history or len(chat_history) < 2:
            return ""

        context_items = []
        for i in range(len(chat_history) - 1, 0, -2):
            if i >= 1 and chat_history[i - 1].get("role") == "user" and chat_history[i].get("role") == "assistant":
                user_msg = chat_history[i - 1].get("content", "")
                ai_msg = chat_history[i].get("content", "")
                if len(user_msg) > 200:
                    user_msg = user_msg[:197] + "..."
                if len(ai_msg) > 200:
                    ai_msg = ai_msg[:197] + "..."
                context_items.append(f"User: {user_msg}\nAssistant: {ai_msg}")
                if len(context_items) >= 2:
                    break

        return "\n\n".join(reversed(context_items)) if context_items else ""

    def _preprocess_data(self, data: Any) -> Any:
        if isinstance(data, dict):
            return {
                "patient_name": data.get("patient_name", ""),
                "age": data.get("age", ""),
                "gender": data.get("gender", ""),
                "report": data.get("report", ""),
            }
        return data
