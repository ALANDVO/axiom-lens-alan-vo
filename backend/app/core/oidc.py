"""
Axiom Lens - OIDC Keycloak authentication service.
"""
from datetime import datetime, timedelta, UTC
from typing import Optional
from urllib.parse import urlencode
from uuid import uuid4

import httpx
from authlib.integrations.starlette_client import OAuth
from fastapi import HTTPException, Request, Response
from starlette.middleware.sessions import SessionMiddleware

from app.core.config import settings
from app.core.security import create_access_token, decode_token, TokenData


class OIDCService:
    """OIDC authentication service using Keycloak."""
    
    def __init__(self):
        self.oauth = OAuth()
        self._initialized = False
    
    def initialize(self, secret_key: str) -> None:
        """Initialize OAuth with Keycloak configuration."""
        if self._initialized:
            return
        
        self.oauth.register(
            name="keycloak",
            client_id=settings.oidc_client_id,
            client_secret=settings.oidc_client_secret,
            server_metadata_url=f"{settings.oidc_issuer_url}/.well-known/openid-configuration",
            client_kwargs={
                "scope": settings.oidc_scopes,
                "code_challenge_method": "S256",
            },
        )
        self._initialized = True
    
    def get_authorization_url(self, request: Request, state: Optional[str] = None) -> str:
        """Get the Keycloak authorization URL with PKCE."""
        if not self._initialized:
            self.initialize(settings.secret_key)
        
        if state is None:
            state = str(uuid4())
        
        # Store state and PKCE verifier in session
        request.session["oidc_state"] = state
        request.session["oidc_nonce"] = str(uuid4())
        
        redirect_uri = settings.oidc_redirect_uri
        auth_url = f"{settings.oidc_issuer_url}/protocol/openid-connect/auth"
        
        params = {
            "client_id": settings.oidc_client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": settings.oidc_scopes,
            "state": state,
            "nonce": request.session["oidc_nonce"],
        }
        
        return f"{auth_url}?{urlencode(params)}"
    
    async def exchange_code_for_tokens(
        self,
        request: Request,
        code: str,
        state: str,
    ) -> tuple[str, TokenData]:
        """Exchange authorization code for tokens and create session."""
        # Verify state
        stored_state = request.session.pop("oidc_state", None)
        if not stored_state or stored_state != state:
            raise HTTPException(status_code=400, detail="Invalid state parameter")
        
        if not self._initialized:
            self.initialize(settings.secret_key)
        
        # Exchange code for tokens
        token_endpoint = f"{settings.oidc_issuer_url}/protocol/openid-connect/token"
        
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                token_endpoint,
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": settings.oidc_redirect_uri,
                    "client_id": settings.oidc_client_id,
                    "client_secret": settings.oidc_client_secret,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            
            if token_response.status_code != 200:
                raise HTTPException(
                    status_code=400,
                    detail=f"Token exchange failed: {token_response.text}",
                )
            
            tokens = token_response.json()
            
            # Get user info
            userinfo_endpoint = f"{settings.oidc_issuer_url}/protocol/openid-connect/userinfo"
            userinfo_response = await client.get(
                userinfo_endpoint,
                headers={"Authorization": f"Bearer {tokens['access_token']}"},
            )
            
            if userinfo_response.status_code != 200:
                raise HTTPException(
                    status_code=400,
                    detail=f"Userinfo request failed: {userinfo_response.text}",
                )
            
            userinfo = userinfo_response.json()
        
        # Create our own access token with user info
        user_id = userinfo.get("sub", userinfo.get("preferred_username", "unknown"))
        email = userinfo.get("email")
        name = userinfo.get("name") or userinfo.get("preferred_username")
        roles = userinfo.get("realm_access", {}).get("roles", [])
        
        access_token = create_access_token(
            subject=user_id,
            email=email,
            name=name,
            roles=roles,
        )
        
        token_data = TokenData(
            sub=user_id,
            email=email,
            name=name,
            roles=roles,
            exp=int((datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)).timestamp()),
            iat=int(datetime.now(UTC).timestamp()),
            jti=str(uuid4()),
        )
        
        # Store tokens in session
        request.session["access_token"] = access_token
        request.session["refresh_token"] = tokens.get("refresh_token")
        request.session["user_id"] = user_id
        request.session["user_email"] = email
        request.session["user_name"] = name
        request.session["user_roles"] = roles
        
        return access_token, token_data
    
    async def logout(self, request: Request, response: Response) -> str:
        """Logout user and redirect to Keycloak logout."""
        # Clear session
        request.session.clear()
        
        # Keycloak logout URL
        logout_url = f"{settings.oidc_issuer_url}/protocol/openid-connect/logout"
        params = {
            "post_logout_redirect_uri": "http://localhost:5173",
            "client_id": settings.oidc_client_id,
        }
        
        return f"{logout_url}?{urlencode(params)}"
    
    def get_current_user(self, request: Request) -> Optional[TokenData]:
        """Get current user from session."""
        access_token = request.session.get("access_token")
        if not access_token:
            return None
        
        return decode_token(access_token)
    
    def require_auth(self, request: Request) -> TokenData:
        """Require authentication, raise if not authenticated."""
        user = self.get_current_user(request)
        if not user:
            raise HTTPException(status_code=401, detail="Not authenticated")
        return user
    
    def require_role(self, request: Request, required_roles: list[str]) -> TokenData:
        """Require specific role(s)."""
        user = self.require_auth(request)
        user_roles = set(user.roles)
        if not any(role in user_roles for role in required_roles):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user


# Global OIDC service instance
oidc_service = OIDCService()


# Demo mode user (for development without Keycloak)
DEMO_USER = TokenData(
    sub="demo-user",
    email="demo@axiom-lens.local",
    name="Demo User",
    roles=["viewer", "operator"],
    exp=int((datetime.now(UTC) + timedelta(hours=24)).timestamp()),
    iat=int(datetime.now(UTC).timestamp()),
    jti="demo-jti",
)

DEMO_ACCESS_TOKEN = create_access_token(
    subject=DEMO_USER.sub,
    email=DEMO_USER.email,
    name=DEMO_USER.name,
    roles=DEMO_USER.roles,
    expires_delta=timedelta(hours=24),
)


def get_demo_user() -> TokenData:
    """Get demo user for development mode."""
    return DEMO_USER


def get_demo_token() -> str:
    """Get demo access token for development mode."""
    return DEMO_ACCESS_TOKEN