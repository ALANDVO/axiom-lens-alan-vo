"""
Axiom Lens - Pydantic schemas for request/response validation.
"""
from datetime import datetime
from typing import Optional, Any
from uuid import UUID

from pydantic import BaseModel, Field, EmailStr, ConfigDict


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "healthy"
    version: str
    environment: str
    timestamp: datetime


class VersionResponse(BaseModel):
    """Version info response."""
    name: str
    version: str
    description: str


# Auth schemas
class LoginRequest(BaseModel):
    """Login request (not used for OIDC, but for demo mode)."""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Token response."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    """User response."""
    id: str
    email: str
    name: Optional[str] = None
    roles: list[str] = []
    created_at: datetime


class CurrentUserResponse(BaseModel):
    """Current user response."""
    id: str
    email: str
    name: Optional[str] = None
    roles: list[str] = []


# Analysis schemas
class AnalysisBase(BaseModel):
    """Base analysis schema."""
    type: str = Field(..., pattern="^(binary|javascript|process)$")
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    target_path: Optional[str] = None


class AnalysisCreate(AnalysisBase):
    """Create analysis request."""
    pass


class AnalysisUpdate(BaseModel):
    """Update analysis request."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(pending|running|completed|failed)$")
    result: Optional[dict] = None
    error: Optional[str] = None


class AnalysisResponse(AnalysisBase):
    """Analysis response."""
    id: str
    user_id: str
    status: str
    target_hash: Optional[str] = None
    result: Optional[dict] = None
    error: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class AnalysisListResponse(BaseModel):
    """Paginated analysis list response."""
    items: list[AnalysisResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# Pagination
class PaginationParams(BaseModel):
    """Pagination parameters."""
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class PaginatedResponse(BaseModel):
    """Generic paginated response."""
    items: list[Any]
    total: int
    page: int
    page_size: int
    total_pages: int


# Audit schemas
class AuditLogResponse(BaseModel):
    """Audit log response."""
    id: str
    user_id: Optional[str] = None
    event_type: str
    event_data: Optional[dict] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    success: bool
    error_message: Optional[str] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# Error schemas
class ErrorResponse(BaseModel):
    """Error response."""
    detail: str
    error_code: Optional[str] = None


class ValidationErrorResponse(BaseModel):
    """Validation error response."""
    detail: list[dict]
    error_code: str = "validation_error"