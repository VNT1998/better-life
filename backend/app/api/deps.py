from fastapi import Header, HTTPException, status
from typing import Optional, Dict, Any
from app.auth.auth_service import AuthService
from app.services.ai_service import AIService

auth_service = AuthService()
ai_service = AIService.get_instance()


def get_current_user(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    """Dependency to extract and validate the user token."""
    if not authorization:
        # Default guest identity for instant development/testing
        return {
            "id": "guest_user",
            "email": "guest@bloodanalysis.local",
            "name": "Guest User",
        }

    token = authorization
    if token.startswith("Bearer "):
        token = token[7:]

    user = auth_service.validate_token(token)
    if not user:
        if token.startswith("local_token_"):
            uid = token.replace("local_token_", "")
            user = auth_service.get_user_data(uid)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session token",
        )
    return user
