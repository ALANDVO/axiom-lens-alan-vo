"""
Axiom Lens - Authentication API routes.
"""
from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db_session
from app.core.oidc import oidc_service, get_demo_token, TokenData
from app.core.security import create_access_token
from app.schemas import TokenResponse, CurrentUserResponse, ErrorResponse
from app.api.dependencies import get_current_user, get_db
from app.services.user_service import UserService


router = APIRouter(prefix="/auth", tags=["authentication"])


@router.get("/login")
async def login(request: Request):
    """Initiate OIDC login flow."""
    if settings.demo_mode_effective:
        # Demo mode: create token directly and redirect to frontend
        token = get_demo_token()
        frontend_url = "http://localhost:5173"
        response = RedirectResponse(url=f"{frontend_url}/?demo_token={token}")
        return response
    
    # Production: redirect to Keycloak
    auth_url = oidc_service.get_authorization_url(request)
    return RedirectResponse(url=auth_url)


@router.get("/callback")
async def auth_callback(
    request: Request,
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    error_description: Optional[str] = None,
    db: AsyncSession = Depends(get_db_session),
):
    """Handle OIDC callback from Keycloak."""
    if error:
        raise HTTPException(
            status_code=400,
            detail=f"OIDC error: {error} - {error_description}",
        )
    
    if not code or not state:
        raise HTTPException(status_code=400, detail="Missing code or state parameter")
    
    # Exchange code for tokens
    access_token, token_data = await oidc_service.exchange_code_for_tokens(
        request, code, state
    )
    
    # Sync user to local database
    user_service = UserService(db)
    await user_service.get_or_create_user(token_data)
    
    # Redirect to frontend with token
    frontend_url = "http://localhost:5173"
    response = RedirectResponse(url=f"{frontend_url}/?token={access_token}")
    return response


@router.post("/logout")
async def logout(request: Request, response: Response):
    """Logout user."""
    if settings.demo_mode_effective:
        # Demo mode: just clear session
        request.session.clear()
        return {"message": "Logged out"}
    
    # Production: redirect to Keycloak logout
    logout_url = await oidc_service.logout(request, response)
    return RedirectResponse(url=logout_url)


@router.get("/me", response_model=CurrentUserResponse)
async def get_current_user_info(
    current_user: TokenData = Depends(get_current_user),
):
    """Get current authenticated user info."""
    return CurrentUserResponse(
        id=current_user.sub,
        email=current_user.email or "",
        name=current_user.name,
        roles=current_user.roles,
    )


@router.post("/demo-token", response_model=TokenResponse)
async def get_demo_token_endpoint():
    """Get a demo token for development (only in demo mode)."""
    if not settings.demo_mode_effective:
        raise HTTPException(status_code=403, detail="Demo mode not enabled")
    
    token = get_demo_token()
    return TokenResponse(
        access_token=token,
        expires_in=24 * 60 * 60,  # 24 hours
    )