from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime

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

# =================== User & Authentication Models ===================

class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    email: EmailStr = Field(..., description="User email address")
    full_name: Optional[str] = Field(None, max_length=255, description="Full name")

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, description="Password (min 8 characters)")

class UserLogin(BaseModel):
    username: str = Field(..., description="Username")
    password: str = Field(..., description="Password")

class UserResponse(UserBase):
    id: int
    is_active: bool
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

class TokenPayload(BaseModel):
    user_id: int
    username: str
    exp: int
    type: str  # "access" or "refresh"
