import pytest

from app.auth.auth_service import AuthService, hash_password, verify_password


@pytest.fixture
def auth_service():
    service = AuthService()
    return service


def test_password_hashing():
    raw_password = "supersecretpassword123"
    hashed = hash_password(raw_password)
    assert hashed != raw_password
    assert hashed.startswith("$2b$")
    assert verify_password(raw_password, hashed) is True
    assert verify_password("wrongpassword", hashed) is False


def test_user_signup_and_login(auth_service):
    email = f"testdoctor_{id(auth_service)}@betterlife.ai"
    password = "SafePassword99!"
    name = "Dr. Test User"

    # Sign up
    success, result = auth_service.sign_up(email=email, password=password, name=name)
    assert success is True
    user = result["user"]
    assert user["email"] == email
    assert user["name"] == name
    assert "password" not in user
    assert "_password_hash" not in user

    # Log in
    login_success, login_result = auth_service.sign_in(email=email, password=password)
    assert login_success is True
    token = login_result.get("access_token")
    assert token is not None

    # Verify token
    user_data_validated = auth_service.validate_token(token)
    assert user_data_validated is not None
    assert user_data_validated["id"] == user["id"]


def test_session_lifecycle_and_messages(auth_service):
    # Create session
    success, session = auth_service.create_session(user_id="user_test_123")
    assert success is True
    session_id = session["id"]

    # Save messages
    auth_service.save_chat_message(session_id=session_id, content="What is HbA1c?", role="user")
    auth_service.save_chat_message(
        session_id=session_id, content="HbA1c measures average blood sugar.", role="assistant"
    )

    # Retrieve messages
    success_msg, messages = auth_service.get_session_messages(session_id=session_id)
    assert success_msg is True
    assert len(messages) >= 2
    assert messages[0]["content"] == "What is HbA1c?"
    assert messages[1]["role"] == "assistant"
