import logging
from typing import List, Dict, Any, Optional
from langchain_text_splitters import RecursiveCharacterTextSplitter
from agents.model_manager import ModelManager

logger = logging.getLogger(__name__)


class ChatAgent:
    """
    RAG-powered chat agent for follow-up questions on blood reports using Ollama.
    """

    def __init__(self, model_manager: Optional[ModelManager] = None):
        self.model_manager = model_manager or ModelManager()
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=200
        )

    def extract_relevant_context(self, query: str, text_content: str) -> str:
        """
        Extract relevant context from text content.
        Since reports are typically 1,000-5,000 words and modern Ollama models
        support 128k context, we provide the full report if under 15,000 characters,
        or the top relevant chunks for very large reports.
        """
        if not text_content or text_content.strip() == "":
            return ""

        text_content = text_content.strip()
        if len(text_content) <= 15000:
            return text_content

        # For very long documents, chunk and score by term frequency
        chunks = self.text_splitter.split_text(text_content)
        query_words = set(query.lower().split())

        def score_chunk(chunk: str) -> int:
            chunk_lower = chunk.lower()
            return sum(1 for w in query_words if len(w) > 2 and w in chunk_lower)

        ranked = sorted(chunks, key=score_chunk, reverse=True)
        top_chunks = ranked[:4]
        return "\n\n---\n\n".join(top_chunks)

    def _format_chat_history(self, chat_history: List[Dict[str, str]]) -> List[Dict[str, str]]:
        messages = []
        for msg in chat_history:
            if msg.get("role") in ["user", "assistant"]:
                messages.append({"role": msg["role"], "content": msg["content"]})
        return messages

    def get_response(
        self,
        query: str,
        context_text: str,
        chat_history: Optional[List[Dict[str, str]]] = None,
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get response to follow-up question.
        """
        if chat_history is None:
            chat_history = []

        context = self.extract_relevant_context(query, context_text)

        qa_system_prompt = (
            "You are an expert medical AI assistant specialized in laboratory and blood report analysis. "
            "Use the provided report context to accurately, clearly, and concisely answer the user's questions. "
            "Always explain medical terminology in an understandable way. "
            "If the report does not contain the answer, state that it's not mentioned in the report. "
            "Always include a brief reminder that this information is for educational purposes."
        )

        messages = [{"role": "system", "content": qa_system_prompt}]

        # Add recent chat history (up to last 6 messages)
        if chat_history:
            recent_history = self._format_chat_history(chat_history[-6:])
            messages.extend(recent_history)

        # Build current user message with context
        if context:
            user_message = f"### Blood Report Context:\n{context}\n\n### User Question:\n{query}"
        else:
            user_message = f"### User Question:\n{query}\n\n(Note: No specific report context provided. Answer generally and state that.)"

        messages.append({"role": "user", "content": user_message})

        result = self.model_manager.generate_chat_completion(
            messages=messages, model=model, temperature=0.7, max_tokens=1500
        )
        return result

    async def get_response_async(
        self,
        query: str,
        context_text: str,
        chat_history: Optional[List[Dict[str, str]]] = None,
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Asynchronously get response to follow-up question.
        """
        if chat_history is None:
            chat_history = []

        context = self.extract_relevant_context(query, context_text)

        qa_system_prompt = (
            "You are an expert medical AI assistant specialized in laboratory and blood report analysis. "
            "Use the provided report context to accurately, clearly, and concisely answer the user's questions. "
            "Always explain medical terminology in an understandable way. "
            "If the report does not contain the answer, state that it's not mentioned in the report. "
            "Always include a brief reminder that this information is for educational purposes."
        )

        messages = [{"role": "system", "content": qa_system_prompt}]

        if chat_history:
            recent_history = self._format_chat_history(chat_history[-6:])
            messages.extend(recent_history)

        if context:
            user_message = f"### Blood Report Context:\n{context}\n\n### User Question:\n{query}"
        else:
            user_message = f"### User Question:\n{query}\n\n(Note: No specific report context provided. Answer generally and state that.)"

        messages.append({"role": "user", "content": user_message})

        result = await self.model_manager.generate_chat_completion_async(
            messages=messages, model=model, temperature=0.7, max_tokens=1500
        )
        return result
