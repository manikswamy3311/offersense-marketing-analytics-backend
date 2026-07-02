from pydantic import BaseModel, Field, EmailStr, field_validator
from typing import Optional, Literal, List
from datetime import datetime
import re

# =================== Campaign Models ===================

class CampaignBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Campaign name")
    impressions: int = Field(..., ge=0, description="Number of impressions")
    clicks: int = Field(..., ge=0, description="Number of clicks")
    conversions: int = Field(..., ge=0, description="Number of conversions")

class CampaignCreate(CampaignBase):
    pass

class CampaignUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    impressions: Optional[int] = Field(None, ge=0)
    clicks: Optional[int] = Field(None, ge=0)
    conversions: Optional[int] = Field(None, ge=0)

class CampaignResponse(CampaignBase):
    id: int
    ctr: Optional[float] = None
    conversion_rate: Optional[float] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class KPIResponse(BaseModel):
    impressions: int
    clicks: int
    conversions: int
    ctr: float
    conversion_rate: float

class CampaignPerformanceResponse(BaseModel):
    name: str
    impressions: int
    clicks: int
    conversions: int
    ctr: float
    conversion_rate: float

class SegmentResponse(BaseModel):
    name: str
    impressions: int
    clicks: int
    conversions: int
    ctr: float
    conversion_rate: float
    segment: str

class OfferEffectivenessResponse(BaseModel):
    name: str
    impressions: int
    clicks: int
    conversions: int
    ctr: float
    conversion_rate: float
    drop_off_rate: float

class PaginatedCampaignResponse(BaseModel):
    campaigns: List[CampaignResponse]
    total: int
    page: int
    limit: int
    pages: int
    has_next: bool
    has_prev: bool

# =================== User & Authentication Models ===================

class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    email: EmailStr = Field(..., description="User email address")
    full_name: Optional[str] = Field(None, max_length=255, description="Full name")

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, description="Password (min 8 characters)")
    role: Literal["admin", "analyst", "viewer"] = Field("viewer", description="User role")

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if not re.search(r'[A-Z]', v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r'\d', v):
            raise ValueError("Password must contain at least one digit")
        if not re.search(r'[@$!%*?&#]', v):
            raise ValueError("Password must contain at least one special character (@$!%*?&#)")
        return v

class UserLogin(BaseModel):
    username: str = Field(..., description="Username")
    password: str = Field(..., description="Password")

class UserResponse(UserBase):
    id: int
    is_active: bool
    role: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int

class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., description="Refresh token")

class ChangePasswordRequest(BaseModel):
    old_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password (min 8 characters)")

    @field_validator("new_password")
    @classmethod
    def validate_new_password_strength(cls, v: str) -> str:
        if not re.search(r'[A-Z]', v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r'\d', v):
            raise ValueError("Password must contain at least one digit")
        if not re.search(r'[@$!%*?&#]', v):
            raise ValueError("Password must contain at least one special character (@$!%*?&#)")
        return v

class TokenPayload(BaseModel):
    user_id: int
    username: str
    role: str
    exp: int
    type: str  # "access" or "refresh"

# =================== OAuth Models ===================

class OAuthUserInfo(BaseModel):
    """Normalised user info returned by any OAuth provider."""
    provider: str          # "google" or "github"
    oauth_id: str          # provider's unique user id
    email: str
    full_name: Optional[str] = None
    username: Optional[str] = None
