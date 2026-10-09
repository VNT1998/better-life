import json
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.api.deps import auth_service, get_current_user
from app.main import app

client = TestClient(app)


def test_chat_streaming_endpoint():
    # Setup test user session
    _, session = auth_service.create_session("test_user_id")
    session_id = session["id"]

    # Mock stream response from AI service
    async def mock_stream_chunks(*args, **kwargs):
        yield {"token": "Hello ", "done": False, "model": "medgemma:4b"}
        yield {"token": "Doctor!", "done": True, "model": "medgemma:4b"}

    # Override get_current_user dependency
    app.dependency_overrides[get_current_user] = lambda: {
        "id": "test_user_id",
        "email": "test@betterlife.ai",
    }

    try:
        with patch(
            "app.api.chat.ai_service.stream_chat_response_async", side_effect=mock_stream_chunks
        ):
            response = client.post(
                "/api/v1/chat/stream",
                json={"session_id": session_id, "query": "Hello!"},
            )
            assert response.status_code == 200
            assert "text/event-stream" in response.headers["content-type"]

            lines = [line for line in response.text.split("\n") if line.startswith("data: ")]
            assert len(lines) == 2

            first_event = json.loads(lines[0].replace("data: ", ""))
            assert first_event["token"] == "Hello "
            assert first_event["done"] is False

            second_event = json.loads(lines[1].replace("data: ", ""))
            assert second_event["token"] == "Doctor!"
            assert second_event["done"] is True
    finally:
        app.dependency_overrides.pop(get_current_user, None)
