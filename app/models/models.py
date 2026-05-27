from pydantic import BaseModel, Field
from typing import Optional

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
