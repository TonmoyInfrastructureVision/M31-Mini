from datetime import timedelta
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from config.settings import settings
from api.auth import (
    User, authenticate_user, create_access_token, 
    get_current_active_user, fake_users_db
)

router = APIRouter(tags=["authentication"])


class Token(Dict):
    access_token: str
    token_type: str


@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> Dict[str, str]:
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(
        minutes=settings.security.access_token_expire_minutes
    )
    access_token = create_access_token(
        data={
            "sub": user.username,
            "scopes": user.scopes,
        },
        expires_delta=access_token_expires,
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/users/me", response_model=User)
async def read_users_me(
    current_user: User = Depends(get_current_active_user),
) -> User:
    return current_user


@router.get("/status")
async def get_auth_status(
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, bool]:
    return {"authenticated": True} 