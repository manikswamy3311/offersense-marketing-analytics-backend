# IMPORTANT:
# Use sqlite3 only
# Do NOT use pandas
# Do NOT use ML libraries
# Do NOT change project structure

# Create a function get_customer_segments()
# Requirements:
# - Fetch all campaigns from campaigns table
# - For each campaign calculate:
#     ctr = (clicks / impressions) * 100
#     conversion_rate = (conversions / clicks) * 100
# - Handle division by zero
# - Based on conversion_rate assign segment:
#     if conversion_rate >= 12 → "High Performer"
#     if conversion_rate between 10 and 12 → "Medium Performer"
#     else → "Low Performer"
# - Return list of campaigns with:
#     id, name, impressions, clicks, conversions, ctr, conversion_rate, segment
# - Use get_connection() from app.database.db
# - Close connection
# - Keep code clean and minimal
import sqlite3
from app.database.db import get_connection      

def get_customer_segments():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name, impressions, clicks, conversions FROM campaigns")
    campaigns = cursor.fetchall()
    
    result = []
    
    for campaign in campaigns:
        name, impressions, clicks, conversions = campaign
        
        ctr = (clicks / impressions) * 100 if impressions > 0 else 0
        conversion_rate = round((conversions / clicks) * 100, 2) if clicks > 0 else 0
        ctr = round((clicks / impressions) * 100, 2) if impressions > 0 else 0
        
        if conversion_rate >= 12:
            segment = "High Performer"
        elif 10 <= conversion_rate < 12:
            segment = "Medium Performer"
        else:
            segment = "Low Performer"
        
        result.append({
            "name": name,
            "impressions": impressions,
            "clicks": clicks,
            "conversions": conversions,
            "ctr": ctr,
            "conversion_rate": conversion_rate,
            "segment": segment
        })
    
    conn.close()
    return result
