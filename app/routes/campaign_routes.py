from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import StreamingResponse
from app.services.campaign_analysis import load_sample_data, get_campaign_performance, get_offer_effectiveness
from app.database.db import get_connection
from app.services.kpi_service import get_kpis
from app.services.segmentation_service import get_customer_segments
from app.services.crud_service import (
    create_campaign, get_campaign_by_id, get_all_campaigns,
    update_campaign, delete_campaign
)
from app.models.models import CampaignCreate, CampaignUpdate
from app.dependencies import get_current_user, require_role
from app.services.analytics_service import (
    get_summary_stats, get_benchmark, get_performance_scores, get_top_performers
)
import logging
import csv
import io

logger = logging.getLogger(__name__)
router = APIRouter()

# =================== PUBLIC ENDPOINTS ===================

@router.get("/test")
def test_route():
    """Public health check endpoint"""
    return {"message": "Campaign route working", "status": "healthy"}


@router.get("/load-data")
def load_data():
    """Load sample campaign data (for testing/demo only)"""
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
    """View all raw campaign data (public for demo)"""
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

# =================== PROTECTED ANALYTICS ENDPOINTS ===================
# These require JWT authentication

@router.get("/kpis")
def fetch_kpis(current_user: dict = Depends(require_role("admin", "analyst"))):
    """
    Get overall KPI metrics (requires authentication).
    
    Returns: impressions, clicks, conversions, CTR, conversion rate
    """
    try:
        logger.info(f"KPI fetch by user: {current_user['username']}")
        return get_kpis()
    except Exception as e:
        logger.error(f"Error fetching KPIs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate KPIs: {str(e)}"
        )

@router.get("/campaign-performance")
def fetch_campaign_performance(current_user: dict = Depends(require_role("admin", "analyst"))):
    """
    Get campaign performance metrics (requires authentication).
    
    Returns: All campaigns with CTR, conversion rate, and best performer
    """
    try:
        logger.info(f"Campaign performance fetch by user: {current_user['username']}")
        return get_campaign_performance()
    except Exception as e:
        logger.error(f"Error fetching campaign performance: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get campaign performance: {str(e)}"
        )

@router.get("/segments")
def customer_segments(current_user: dict = Depends(require_role("admin", "analyst"))):
    """
    Get customer segmentation (requires authentication).
    
    Returns: Campaigns segmented into High/Medium/Low performers
    """
    try:
        logger.info(f"Segmentation fetch by user: {current_user['username']}")
        return get_customer_segments()
    except Exception as e:
        logger.error(f"Error fetching segments: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get customer segments: {str(e)}"
        )

@router.get("/offer-effectiveness")
def offer_effectiveness(current_user: dict = Depends(require_role("admin", "analyst"))):
    """
    Get offer effectiveness analysis (requires authentication).
    
    Returns: Campaigns with drop-off rates and best/worst offers
    """
    try:
        logger.info(f"Offer effectiveness fetch by user: {current_user['username']}")
        return get_offer_effectiveness()
    except Exception as e:
        logger.error(f"Error fetching offer effectiveness: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get offer effectiveness: {str(e)}"
        )

# ========== PROTECTED CRUD ENDPOINTS ==========
# All require JWT authentication

@router.post("/campaigns", status_code=status.HTTP_201_CREATED)
def create_new_campaign(
    campaign: CampaignCreate,
    current_user: dict = Depends(require_role("admin"))
):
    """Create a new campaign (requires authentication)"""
    try:
        logger.info(f"Campaign created by user: {current_user['username']}")
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
def get_campaigns(current_user: dict = Depends(get_current_user)):
    """Get all campaigns (requires authentication)"""
    try:
        logger.info(f"All campaigns fetched by user: {current_user['username']}")
        campaigns = get_all_campaigns()
        return {"campaigns": campaigns, "count": len(campaigns)}
    except Exception as e:
        logger.error(f"Error fetching campaigns: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch campaigns: {str(e)}"
        )

@router.get("/campaigns/{campaign_id}")
def get_campaign(
    campaign_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Get a single campaign by ID (requires authentication)"""
    try:
        logger.info(f"Campaign {campaign_id} fetched by user: {current_user['username']}")
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
def update_existing_campaign(
    campaign_id: int,
    campaign_update: CampaignUpdate,
    current_user: dict = Depends(require_role("admin"))
):
    """Update an existing campaign (requires authentication)"""
    try:
        logger.info(f"Campaign {campaign_id} updated by user: {current_user['username']}")
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
def delete_existing_campaign(
    campaign_id: int,
    current_user: dict = Depends(require_role("admin"))
):
    """Delete a campaign (requires authentication)"""
    try:
        logger.info(f"Campaign {campaign_id} deleted by user: {current_user['username']}")
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

# =================== CSV EXPORT ENDPOINTS ===================

def _make_csv_response(rows: list, filename: str) -> StreamingResponse:
    """Helper: convert list of dicts to a CSV StreamingResponse."""
    if not rows:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No data to export")
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/export/campaigns")
def export_campaigns(current_user: dict = Depends(require_role("admin", "analyst", "viewer"))):
    """Export all campaigns as CSV (requires authentication)."""
    try:
        logger.info(f"Campaign CSV export by user: {current_user['username']}")
        campaigns = get_all_campaigns()
        return _make_csv_response(campaigns, "campaigns.csv")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting campaigns: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Export failed")


@router.get("/export/performance")
def export_performance(current_user: dict = Depends(require_role("admin", "analyst"))):
    """Export campaign performance analysis as CSV (analyst/admin only)."""
    try:
        logger.info(f"Performance CSV export by user: {current_user['username']}")
        data = get_campaign_performance()
        rows = data.get("campaigns", data) if isinstance(data, dict) else data
        return _make_csv_response(rows, "campaign_performance.csv")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting performance: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Export failed")


@router.get("/export/segments")
def export_segments(current_user: dict = Depends(require_role("admin", "analyst"))):
    """Export customer segments as CSV (analyst/admin only)."""
    try:
        logger.info(f"Segments CSV export by user: {current_user['username']}")
        rows = get_customer_segments()
        return _make_csv_response(rows, "segments.csv")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting segments: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Export failed")

# =================== ADVANCED ANALYTICS ENDPOINTS ===================

@router.get("/analytics/summary")
def analytics_summary(current_user: dict = Depends(require_role("admin", "analyst"))):
    """Statistical summary across all campaigns (analyst/admin only)."""
    try:
        logger.info(f"Analytics summary by user: {current_user['username']}")
        return get_summary_stats()
    except Exception as e:
        logger.error(f"Error in analytics summary: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Analytics failed")


@router.get("/analytics/benchmark")
def analytics_benchmark(current_user: dict = Depends(require_role("admin", "analyst"))):
    """Compare each campaign against portfolio average (analyst/admin only)."""
    try:
        logger.info(f"Analytics benchmark by user: {current_user['username']}")
        return get_benchmark()
    except Exception as e:
        logger.error(f"Error in analytics benchmark: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Analytics failed")


@router.get("/analytics/scores")
def analytics_scores(current_user: dict = Depends(require_role("admin", "analyst"))):
    """Composite performance score (0-100) per campaign (analyst/admin only)."""
    try:
        logger.info(f"Analytics scores by user: {current_user['username']}")
        return get_performance_scores()
    except Exception as e:
        logger.error(f"Error in analytics scores: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Analytics failed")


@router.get("/analytics/top")
def analytics_top(
    metric: str = "conversion_rate",
    limit: int = 3,
    current_user: dict = Depends(require_role("admin", "analyst"))
):
    """
    Top N campaigns by a chosen metric (analyst/admin only).

    - **metric**: ctr | conversion_rate | impressions | clicks | conversions
    - **limit**: number of results (default 3)
    """
    try:
        logger.info(f"Analytics top by user: {current_user['username']}")
        return get_top_performers(metric=metric, limit=limit)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error in analytics top: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Analytics failed")
