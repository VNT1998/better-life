from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any
from api.deps import auth_service, get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


class SignUpRequest(BaseModel):
    name: str
    email: str
    password: str


class SignInRequest(BaseModel):
    email: str
    password: str


@router.post("/signup")
def sign_up(req: SignUpRequest):
    success, result = auth_service.sign_up(
        email=req.email.strip(),
        password=req.password,
        name=req.name.strip(),
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result,
        )
    return result


@router.post("/signin")
def sign_in(req: SignInRequest):
    success, result = auth_service.sign_in(
        email=req.email.strip(),
        password=req.password,
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=result,
        )
    return result


@router.get("/me")
def get_me(user: Dict[str, Any] = Depends(get_current_user)):
    return {"user": user}


@router.post("/signout")
def sign_out():
    return {"message": "Signed out successfully"}
