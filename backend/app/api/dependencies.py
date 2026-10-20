"""
Axiom Lens - API dependencies for authentication and database.
"""
from typing import Optional

from fastapi import Depends, Header, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db_session
from app.core.oidc import oidc_service, get_demo_user, get_demo_token, TokenData
from app.core.security import decode_token
from app.services.user_service import UserService


async def get_db() -> AsyncSession:
    """Get database session."""
    async for session in get_db_session():
        yield session


async def get_current_user_oidc(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> TokenData:
    """Get current user from OIDC session or demo mode."""
    # Demo mode for development
    if settings.demo_mode_effective:
        return get_demo_user()
    
    # Production: require OIDC authentication
    user = oidc_service.get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


async def get_current_user_token(
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
) -> TokenData:
    """Get current user from Bearer token (for API clients)."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid authentication scheme")
    
    token_data = decode_token(token)
    if not token_data:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    return token_data


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> TokenData:
    """Get current user from either session (web) or Bearer token (API)."""
    # Demo mode for development
    if settings.demo_mode_effective:
        return get_demo_user()
    
    # Try session first (web UI)
    user = oidc_service.get_current_user(request)
    if user:
        return user
    
    # Try Bearer token (API)
    auth_header = request.headers.get("Authorization")
    if auth_header:
        return await get_current_user_token(authorization=auth_header, db=db)
    
    raise HTTPException(status_code=401, detail="Not authenticated")


async def get_current_user_id(
    current_user: TokenData = Depends(get_current_user),
) -> str:
    """Get current user ID."""
    return current_user.sub


async def require_operator_role(
    current_user: TokenData = Depends(get_current_user),
) -> TokenData:
    """Require operator or admin role."""
    if "operator" not in current_user.roles and "admin" not in current_user.roles:
        raise HTTPException(status_code=403, detail="Operator role required")
    return current_user


async def require_admin_role(
    current_user: TokenData = Depends(get_current_user),
) -> TokenData:
    """Require admin role."""
    if "admin" not in current_user.roles:
        raise HTTPException(status_code=403, detail="Admin role required")
    return current_user


def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    """Get user service instance."""
    return UserService(db)