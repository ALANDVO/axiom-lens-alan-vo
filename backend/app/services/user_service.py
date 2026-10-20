"""
Axiom Lens - User service for user management.
"""
from datetime import datetime, UTC
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User
from app.core.oidc import TokenData


class UserService:
    """Service for user management."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_or_create_user(self, token_data: TokenData) -> User:
        """Get existing user or create new one from OIDC token data."""
        # Try to find by OIDC subject
        result = await self.db.execute(
            select(User).where(User.oidc_sub == token_data.sub)
        )
        user = result.scalar_one_or_none()
        
        if user:
            # Update user info
            user.email = token_data.email or user.email
            user.name = token_data.name or user.name
            user.roles = token_data.roles
            user.last_login = datetime.now(UTC)
            await self.db.commit()
            await self.db.refresh(user)
            return user
        
        # Create new user
        user = User(
            oidc_sub=token_data.sub,
            email=token_data.email or "unknown@example.com",
            name=token_data.name,
            roles=token_data.roles,
            last_login=datetime.now(UTC),
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()
    
    async def update_user_roles(self, user_id: str, roles: list[str]) -> Optional[User]:
        """Update user roles."""
        user = await self.get_user_by_id(user_id)
        if user:
            user.roles = roles
            await self.db.commit()
            await self.db.refresh(user)
        return user