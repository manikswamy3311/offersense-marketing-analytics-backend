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

def get_kpis():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(impressions), SUM(clicks), SUM(conversions) FROM campaigns")
    result = cursor.fetchone()
    conn.close()

    impressions, clicks, conversions = result

    ctr = round((clicks / impressions) * 100, 2) if impressions > 0 else 0.00
    conversion_rate = round((conversions / clicks) * 100, 2) if clicks > 0 else 0.00

    return {
        "impressions": impressions,
        "clicks": clicks,
        "conversions": conversions,
        "ctr": ctr,
        "conversion_rate": conversion_rate
    }

