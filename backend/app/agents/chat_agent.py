import logging
from typing import List, Dict, Any, Optional
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.agents.model_manager import ModelManager

logger = logging.getLogger(__name__)


class ChatAgent:
    """
    RAG-powered chat agent for follow-up clinical questions using Ollama.
    """

    def __init__(self, model_manager: Optional[ModelManager] = None):
        self.model_manager = model_manager or ModelManager()
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=200
        )

    def extract_relevant_context(self, query: str, text_content: str) -> str:
        """Extract focused context from blood report."""
        if not text_content or not text_content.strip():
            return ""

        text_content = text_content.strip()
        # For standard reports (under 15,000 characters), modern 128k context models
        # benefit from receiving the entire report to avoid missing subtle cross-panel interactions.
        if len(text_content) <= 15000:
            return text_content

        chunks = self.text_splitter.split_text(text_content)
        query_terms = set(w for w in query.lower().split() if len(w) > 2)

        def score_chunk(c: str) -> int:
            c_low = c.lower()
            return sum(1 for term in query_terms if term in c_low)

        ranked = sorted(chunks, key=score_chunk, reverse=True)
        return "\n\n---\n\n".join(ranked[:4])

    def _build_messages(
        self,
        query: str,
        context_text: str,
        chat_history: Optional[List[Dict[str, str]]] = None,
    ) -> List[Dict[str, str]]:
        qa_system_prompt = (
            "You are a medical AI assistant specializing in clinical laboratory analysis. "
            "Your objective is to provide precise, medically accurate, and easy-to-understand answers "
            "to follow-up questions regarding the patient's blood report. "
            "Explain lab values, reference intervals, potential implications, and practical guidance. "
            "If a parameter isn't mentioned in the report, explicitly note that. "
            "Conclude with a brief reminder to discuss findings with a qualified physician."
        )

        messages = [{"role": "system", "content": qa_system_prompt}]

        if chat_history:
            for msg in chat_history[-6:]:
                if msg.get("role") in ["user", "assistant"]:
                    messages.append({"role": msg["role"], "content": msg["content"]})

        context = self.extract_relevant_context(query, context_text)
        if context:
            user_content = f"### Relevant Blood Report Data:\n{context}\n\n### Follow-Up Question:\n{query}"
        else:
            user_content = f"### Follow-Up Question:\n{query}\n\n(Note: No specific report context provided.)"

        messages.append({"role": "user", "content": user_content})
        return messages

    def get_response(
        self,
        query: str,
        context_text: str,
        chat_history: Optional[List[Dict[str, str]]] = None,
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        messages = self._build_messages(query, context_text, chat_history)
        return self.model_manager.generate_chat_completion(
            messages=messages, model=model, temperature=0.7, max_tokens=1500
        )

    async def get_response_async(
        self,
        query: str,
        context_text: str,
        chat_history: Optional[List[Dict[str, str]]] = None,
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        messages = self._build_messages(query, context_text, chat_history)
        return await self.model_manager.generate_chat_completion_async(
            messages=messages, model=model, temperature=0.7, max_tokens=1500
        )
