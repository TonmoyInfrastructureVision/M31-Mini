from datetime import datetime, timedelta
from typing import Dict, Optional, Union

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from config.settings import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


class TokenData(BaseModel):
    username: Optional[str] = None
    scopes: list[str] = []


class User(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: bool = False
    scopes: list[str] = []


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def authenticate_user(
    fake_db: Dict[str, Dict[str, Union[str, bool, list[str]]]],
    username: str,
    password: str
) -> Optional[User]:
    if username not in fake_db:
        return None
    user_dict = fake_db[username]
    if not verify_password(password, user_dict["hashed_password"]):
        return None
    return User(
        username=username,
        email=user_dict.get("email"),
        full_name=user_dict.get("full_name"),
        disabled=user_dict.get("disabled", False),
        scopes=user_dict.get("scopes", [])
    )


def create_access_token(
    data: dict, 
    expires_delta: Optional[timedelta] = None
) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.security.secret_key, 
        algorithm=settings.security.algorithm
    )
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(
            token, 
            settings.security.secret_key, 
            algorithms=[settings.security.algorithm]
        )
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_scopes = payload.get("scopes", [])
        token_data = TokenData(username=username, scopes=token_scopes)
    except JWTError:
        raise credentials_exception
        
    # In production, this would query a database
    user = fake_users_db.get(token_data.username)
    if user is None:
        raise credentials_exception
        
    return User(
        username=token_data.username,
        email=user.get("email"),
        full_name=user.get("full_name"),
        disabled=user.get("disabled", False),
        scopes=user.get("scopes", [])
    )


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


# Temporary in-memory user database for demonstration
# In production, this would be replaced with a real database
fake_users_db = {
    "admin": {
        "username": "admin",
        "full_name": "Admin User",
        "email": "admin@example.com",
        "hashed_password": get_password_hash("admin"),
        "disabled": False,
        "scopes": ["agents:read", "agents:write", "tasks:read", "tasks:write"]
    },
    "user": {
        "username": "user",
        "full_name": "Regular User",
        "email": "user@example.com",
        "hashed_password": get_password_hash("user"),
        "disabled": False,
        "scopes": ["agents:read", "tasks:read"]
    }
} 