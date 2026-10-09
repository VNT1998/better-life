from typing import Any

from fastapi import Header, HTTPException, status

from app.auth.auth_service import GUEST_UUID, AuthService
from app.services.ai_service import AIService

auth_service = AuthService()
ai_service = AIService.get_instance()


def get_current_user(authorization: str | None = Header(None)) -> dict[str, Any]:
    """Dependency to extract and validate the user token."""
    if not authorization:
        # Default guest identity with valid UUID for instant development/testing
        return {
            "id": GUEST_UUID,
            "email": "guest@betterlife.local",
            "name": "Guest User",
        }

    token = authorization.strip()
    if token.startswith("Bearer "):
        token = token[7:].strip()

    user = auth_service.validate_token(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session token",
        )
    return user
