from fastapi import APIRouter, HTTPException, status
from app.services.campaign_analysis import load_sample_data, get_campaign_performance, get_offer_effectiveness
from app.database.db import get_connection
from app.services.kpi_service import get_kpis
from app.services.segmentation_service import get_customer_segments
from app.services.crud_service import (
    create_campaign, get_campaign_by_id, get_all_campaigns,
    update_campaign, delete_campaign
)
from app.models.models import CampaignCreate, CampaignUpdate
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/test")
def test_route():
    return {"message": "Campaign route working"}


@router.get("/load-data")
def load_data():
    try:
        load_sample_data()
        return {"message": "Sample data loaded successfully"}
    except Exception as e:
        logger.error(f"Error loading data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load sample data: {str(e)}"
        )


@router.get("/check-data")
def check_data():
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM campaigns")
        data = cursor.fetchall()
        return [dict(row) for row in data]
    except Exception as e:
        logger.error(f"Error checking data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch data: {str(e)}"
        )
    finally:
        if conn:
            conn.close()

@router.get("/kpis")
def fetch_kpis():
    try:
        return get_kpis()
    except Exception as e:
        logger.error(f"Error fetching KPIs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate KPIs: {str(e)}"
        )

@router.get("/campaign-performance")
def fetch_campaign_performance():
    try:
        return get_campaign_performance()
    except Exception as e:
        logger.error(f"Error fetching campaign performance: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get campaign performance: {str(e)}"
        )

@router.get("/segments")
def customer_segments():
    try:
        return get_customer_segments()
    except Exception as e:
        logger.error(f"Error fetching segments: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get customer segments: {str(e)}"
        )

@router.get("/offer-effectiveness")
def offer_effectiveness():
    try:
        return get_offer_effectiveness()
    except Exception as e:
        logger.error(f"Error fetching offer effectiveness: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get offer effectiveness: {str(e)}"
        )

# ========== CRUD ENDPOINTS ==========

@router.post("/campaigns", status_code=status.HTTP_201_CREATED)
def create_new_campaign(campaign: CampaignCreate):
    """Create a new campaign"""
    try:
        result = create_campaign(campaign)
        if result:
            return {"message": "Campaign created successfully", "campaign": result}
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create campaign"
        )
    except Exception as e:
        logger.error(f"Error creating campaign: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create campaign: {str(e)}"
        )

@router.get("/campaigns")
def get_campaigns():
    """Get all campaigns"""
    try:
        campaigns = get_all_campaigns()
        return {"campaigns": campaigns, "count": len(campaigns)}
    except Exception as e:
        logger.error(f"Error fetching campaigns: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch campaigns: {str(e)}"
        )

@router.get("/campaigns/{campaign_id}")
def get_campaign(campaign_id: int):
    """Get a single campaign by ID"""
    try:
        campaign = get_campaign_by_id(campaign_id)
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Campaign with ID {campaign_id} not found"
            )
        return campaign
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching campaign {campaign_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch campaign: {str(e)}"
        )

@router.put("/campaigns/{campaign_id}")
def update_existing_campaign(campaign_id: int, campaign_update: CampaignUpdate):
    """Update an existing campaign"""
    try:
        updated_campaign = update_campaign(campaign_id, campaign_update)
        if not updated_campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Campaign with ID {campaign_id} not found"
            )
        return {"message": "Campaign updated successfully", "campaign": updated_campaign}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating campaign {campaign_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update campaign: {str(e)}"
        )

@router.delete("/campaigns/{campaign_id}", status_code=status.HTTP_200_OK)
def delete_existing_campaign(campaign_id: int):
    """Delete a campaign"""
    try:
        success = delete_campaign(campaign_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Campaign with ID {campaign_id} not found"
            )
        return {"message": f"Campaign {campaign_id} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting campaign {campaign_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete campaign: {str(e)}"
        )