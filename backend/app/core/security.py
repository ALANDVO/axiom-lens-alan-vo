"""
Axiom Lens - Security utilities for authentication and authorization.
"""
from datetime import datetime, timedelta, UTC
from typing import Optional
from uuid import uuid4

from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from app.core.config import settings


# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TokenData(BaseModel):
    """Decoded token data."""
    sub: str  # subject (user ID)
    email: Optional[str] = None
    name: Optional[str] = None
    roles: list[str] = []
    exp: int
    iat: int
    jti: str


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def create_access_token(
    subject: str,
    email: Optional[str] = None,
    name: Optional[str] = None,
    roles: Optional[list[str]] = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a JWT access token."""
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
    
    iat = datetime.now(UTC)
    jti = str(uuid4())
    
    to_encode = {
        "sub": subject,
        "email": email,
        "name": name,
        "roles": roles or [],
        "exp": int(expire.timestamp()),
        "iat": int(iat.timestamp()),
        "jti": jti,
    }
    
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


def decode_token(token: str) -> Optional[TokenData]:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )
        return TokenData(**payload)
    except JWTError:
        return None


def create_csrf_token() -> str:
    """Create a CSRF token."""
    return str(uuid4())


def verify_csrf_token(token: str, stored_token: str) -> bool:
    """Verify a CSRF token."""
    return token == stored_token