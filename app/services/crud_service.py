from app.database.db import get_connection
from app.models.models import CampaignCreate, CampaignUpdate
import logging

logger = logging.getLogger(__name__)

def create_campaign(campaign: CampaignCreate):
    """Create a new campaign"""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO campaigns (name, impressions, clicks, conversions) VALUES (?, ?, ?, ?)",
            (campaign.name, campaign.impressions, campaign.clicks, campaign.conversions)
        )
        conn.commit()
        campaign_id = cursor.lastrowid
        
        # Fetch the created campaign
        cursor.execute("SELECT * FROM campaigns WHERE id = ?", (campaign_id,))
        result = cursor.fetchone()
        
        return dict(result) if result else None
    except Exception as e:
        logger.error(f"Error creating campaign: {str(e)}")
        if conn:
            conn.rollback()
        raise Exception(f"Failed to create campaign: {str(e)}")
    finally:
        if conn:
            conn.close()

def get_campaign_by_id(campaign_id: int):
    """Get a single campaign by ID (excludes soft-deleted)"""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM campaigns WHERE id = ? AND is_deleted = 0", (campaign_id,))
        result = cursor.fetchone()
        
        if not result:
            return None
            
        campaign = dict(result)
        
        # Calculate metrics
        impressions = campaign['impressions']
        clicks = campaign['clicks']
        conversions = campaign['conversions']
        
        campaign['ctr'] = round((clicks / impressions) * 100, 2) if impressions > 0 else 0.00
        campaign['conversion_rate'] = round((conversions / clicks) * 100, 2) if clicks > 0 else 0.00
        
        return campaign
    except Exception as e:
        logger.error(f"Error fetching campaign {campaign_id}: {str(e)}")
        raise Exception(f"Failed to fetch campaign: {str(e)}")
    finally:
        if conn:
            conn.close()

def get_all_campaigns():
    """Get all campaigns (excludes soft-deleted)"""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM campaigns WHERE is_deleted = 0")
        results = cursor.fetchall()
        
        campaigns = []
        for row in results:
            campaign = dict(row)
            impressions = campaign['impressions']
            clicks = campaign['clicks']
            conversions = campaign['conversions']
            
            campaign['ctr'] = round((clicks / impressions) * 100, 2) if impressions > 0 else 0.00
            campaign['conversion_rate'] = round((conversions / clicks) * 100, 2) if clicks > 0 else 0.00
            campaigns.append(campaign)
        
        return campaigns
    except Exception as e:
        logger.error(f"Error fetching all campaigns: {str(e)}")
        raise Exception(f"Failed to fetch campaigns: {str(e)}")
    finally:
        if conn:
            conn.close()

ALLOWED_SORT_COLUMNS = {'id', 'name', 'impressions', 'clicks', 'conversions'}

def get_campaigns_paginated(
    page: int = 1,
    limit: int = 20,
    name: str = None,
    sort_by: str = 'id',
    order: str = 'asc',
):
    """Get campaigns with pagination, optional name filter, and sorting."""
    # Allowlist sort column and direction to prevent SQL injection
    sort_col = sort_by if sort_by in ALLOWED_SORT_COLUMNS else 'id'
    sort_dir = 'ASC' if order.lower() != 'desc' else 'DESC'

    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Build WHERE clause (always exclude soft-deleted)
        conditions = ["is_deleted = 0"]
        params = []
        if name:
            conditions.append("name LIKE ?")
            params.append(f"%{name}%")
        where_clause = "WHERE " + " AND ".join(conditions)

        cursor.execute(f"SELECT COUNT(*) FROM campaigns {where_clause}", params)
        total = cursor.fetchone()[0]

        offset = (page - 1) * limit
        query = f"SELECT * FROM campaigns {where_clause} ORDER BY {sort_col} {sort_dir} LIMIT ? OFFSET ?"
        cursor.execute(query, params + [limit, offset])
        results = cursor.fetchall()

        campaigns = []
        for row in results:
            campaign = dict(row)
            impressions = campaign['impressions']
            clicks = campaign['clicks']
            conversions = campaign['conversions']
            campaign['ctr'] = round((clicks / impressions) * 100, 2) if impressions > 0 else 0.00
            campaign['conversion_rate'] = round((conversions / clicks) * 100, 2) if clicks > 0 else 0.00
            campaigns.append(campaign)

        import math
        pages = math.ceil(total / limit) if total > 0 else 1

        return {
            "campaigns": campaigns,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": pages,
            "has_next": page < pages,
            "has_prev": page > 1,
        }
    except Exception as e:
        logger.error(f"Error fetching paginated campaigns: {str(e)}")
        raise Exception(f"Failed to fetch campaigns: {str(e)}")
    finally:
        if conn:
            conn.close()

def update_campaign(campaign_id: int, campaign_update: CampaignUpdate):
    """Update an existing campaign"""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # First check if campaign exists
        cursor.execute("SELECT * FROM campaigns WHERE id = ?", (campaign_id,))
        if not cursor.fetchone():
            return None
        
        # Build update query dynamically based on provided fields
        update_fields = []
        values = []
        
        if campaign_update.name is not None:
            update_fields.append("name = ?")
            values.append(campaign_update.name)
        if campaign_update.impressions is not None:
            update_fields.append("impressions = ?")
            values.append(campaign_update.impressions)
        if campaign_update.clicks is not None:
            update_fields.append("clicks = ?")
            values.append(campaign_update.clicks)
        if campaign_update.conversions is not None:
            update_fields.append("conversions = ?")
            values.append(campaign_update.conversions)
        
        if not update_fields:
            # No fields to update, return current campaign
            return get_campaign_by_id(campaign_id)

        # Always bump updated_at
        update_fields.append("updated_at = CURRENT_TIMESTAMP")
        values.append(campaign_id)
        query = f"UPDATE campaigns SET {', '.join(update_fields)} WHERE id = ?"
        
        cursor.execute(query, values)
        conn.commit()
        
        # Return updated campaign
        return get_campaign_by_id(campaign_id)
    except Exception as e:
        logger.error(f"Error updating campaign {campaign_id}: {str(e)}")
        if conn:
            conn.rollback()
        raise Exception(f"Failed to update campaign: {str(e)}")
    finally:
        if conn:
            conn.close()

def delete_campaign(campaign_id: int):
    """Soft-delete a campaign (sets is_deleted=1, data is preserved)"""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Check if campaign exists and is not already deleted
        cursor.execute("SELECT id FROM campaigns WHERE id = ? AND is_deleted = 0", (campaign_id,))
        if not cursor.fetchone():
            return False

        cursor.execute(
            "UPDATE campaigns SET is_deleted = 1, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (campaign_id,)
        )
        conn.commit()

        return True
    except Exception as e:
        logger.error(f"Error deleting campaign {campaign_id}: {str(e)}")
        if conn:
            conn.rollback()
        raise Exception(f"Failed to delete campaign: {str(e)}")
    finally:
        if conn:
            conn.close()

def restore_campaign(campaign_id: int):
    """Restore a soft-deleted campaign (sets is_deleted=0)."""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Only restore if it actually exists AND is deleted
        cursor.execute("SELECT id FROM campaigns WHERE id = ? AND is_deleted = 1", (campaign_id,))
        if not cursor.fetchone():
            return False

        cursor.execute(
            "UPDATE campaigns SET is_deleted = 0, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (campaign_id,)
        )
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error restoring campaign {campaign_id}: {str(e)}")
        if conn:
            conn.rollback()
        raise Exception(f"Failed to restore campaign: {str(e)}")
    finally:
        if conn:
            conn.close()
