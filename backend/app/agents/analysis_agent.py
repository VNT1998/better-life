import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from app.agents.model_manager import ModelManager
from app.config import ANALYSIS_DAILY_LIMIT

logger = logging.getLogger(__name__)


class AnalysisAgent:
    """
    Clinical report analysis agent.
    Manages structured medical evaluation, rate-limiting, and context synthesis.
    """

    def __init__(self, model_manager: Optional[ModelManager] = None):
        self.model_manager = model_manager or ModelManager()
        self._user_analytics: Dict[str, Dict[str, Any]] = {}

    def _get_user_state(self, user_id: str) -> Dict[str, Any]:
        if user_id not in self._user_analytics:
            self._user_analytics[user_id] = {
                "analysis_count": 0,
                "last_analysis": datetime.now(),
                "daily_limit": ANALYSIS_DAILY_LIMIT,
            }
        return self._user_analytics[user_id]

    def get_remaining_limit(self, user_id: str = "default") -> int:
        state = self._get_user_state(user_id)
        if datetime.now() - state["last_analysis"] > timedelta(days=1):
            state["analysis_count"] = 0
            state["last_analysis"] = datetime.now()
        return max(0, state["daily_limit"] - state["analysis_count"])

    def check_rate_limit(self, user_id: str = "default") -> Tuple[bool, Optional[str]]:
        state = self._get_user_state(user_id)
        time_since = datetime.now() - state["last_analysis"]

        if time_since > timedelta(days=1):
            state["analysis_count"] = 0
            state["last_analysis"] = datetime.now()
            return True, None

        if state["analysis_count"] >= state["daily_limit"]:
            time_until_reset = timedelta(days=1) - time_since
            hours, remainder = divmod(max(0, int(time_until_reset.total_seconds())), 3600)
            minutes, _ = divmod(remainder, 60)
            return False, f"Daily limit reached ({state['daily_limit']}/day). Reset in {hours}h {minutes}m"

        return True, None

    def _format_patient_context(self, data: Dict[str, Any]) -> str:
        name = data.get("patient_name", "Patient")
        age = data.get("age", "Unknown")
        gender = data.get("gender", "Unknown")
        report = data.get("report", "")

        return (
            f"### Patient Demographics:\n"
            f"- Name: {name}\n"
            f"- Age: {age} years old\n"
            f"- Biological Sex: {gender}\n\n"
            f"### Laboratory Blood Report Data:\n"
            f"```\n{report}\n```"
        )

    def analyze_report(
        self,
        data: Dict[str, Any],
        system_prompt: str,
        user_id: str = "default",
        model: Optional[str] = None,
        check_only: bool = False,
    ) -> Dict[str, Any]:
        can_analyze, error_msg = self.check_rate_limit(user_id)
        if not can_analyze:
            return {"success": False, "error": error_msg}

        if check_only:
            return {"success": True, "error": None}

        patient_content = self._format_patient_context(data)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": patient_content},
        ]

        result = self.model_manager.generate_chat_completion(
            messages=messages, model=model
        )

        if result.get("success"):
            state = self._get_user_state(user_id)
            state["analysis_count"] += 1
            state["last_analysis"] = datetime.now()

        return result

    async def analyze_report_async(
        self,
        data: Dict[str, Any],
        system_prompt: str,
        user_id: str = "default",
        model: Optional[str] = None,
        check_only: bool = False,
    ) -> Dict[str, Any]:
        can_analyze, error_msg = self.check_rate_limit(user_id)
        if not can_analyze:
            return {"success": False, "error": error_msg}

        if check_only:
            return {"success": True, "error": None}

        patient_content = self._format_patient_context(data)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": patient_content},
        ]

        result = await self.model_manager.generate_chat_completion_async(
            messages=messages, model=model
        )

        if result.get("success"):
            state = self._get_user_state(user_id)
            state["analysis_count"] += 1
            state["last_analysis"] = datetime.now()

        return result
