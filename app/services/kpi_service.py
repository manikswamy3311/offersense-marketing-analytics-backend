# IMPORTANT:
# Use sqlite3 only
# Do NOT use pandas
# Do NOT use ORM
# Do NOT change project structure

# Create a function get_kpis() to calculate KPIs from campaigns table
# Requirements:
# - Use get_connection() from app.database.db
# - Query:
#     SELECT SUM(impressions), SUM(clicks), SUM(conversions) FROM campaigns
# - Extract values
# - Calculate:
#     ctr = clicks / impressions
#     conversion_rate = conversions / clicks
# - Handle division by zero
# - Round values to 2 decimal places
# - Return dictionary:
#     {
#       "impressions": value,
#       "clicks": value,
#       "conversions": value,
#       "ctr": value,
#       "conversion_rate": value
#     }
# - Close DB connection
# - Keep code minimal and clean
from app.database.db import get_connection
import logging

logger = logging.getLogger(__name__)

def get_kpis():
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT SUM(impressions), SUM(clicks), SUM(conversions) FROM campaigns")
        result = cursor.fetchone()
        
        impressions, clicks, conversions = result
        
        # Handle None values
        impressions = impressions or 0
        clicks = clicks or 0
        conversions = conversions or 0

        ctr = round((clicks / impressions) * 100, 2) if impressions > 0 else 0.00
        conversion_rate = round((conversions / clicks) * 100, 2) if clicks > 0 else 0.00

        return {
            "impressions": impressions,
            "clicks": clicks,
            "conversions": conversions,
            "ctr": ctr,
            "conversion_rate": conversion_rate
        }
    except Exception as e:
        logger.error(f"Error calculating KPIs: {str(e)}")
        raise Exception(f"Failed to calculate KPIs: {str(e)}")
    finally:
        if conn:
            conn.close()

