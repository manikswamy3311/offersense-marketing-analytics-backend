# IMPORTANT:
# Use pandas and sqlite3 only.
# Do NOT change project structure.

# Create a function load_sample_data() to insert sample campaign data into SQLite database.
# Requirements:
# - Use pandas DataFrame
# - Create sample data with columns:
#     name, impressions, clicks, conversions
# - At least 3 sample campaigns
# - Use get_connection() from app.database.db
# - Insert data into "campaigns" table using pandas to_sql()
# - if_exists="replace"
# - Do NOT create tables here
# - Close the connection after inserting
# - Keep code clean and minimal
import pandas as pd
from app.database.db import get_connection

def load_sample_data():
    # Sample campaign data
    data = {
        "name": ["Campaign A", "Campaign B", "Campaign C"],
        "impressions": [1000, 1500, 2000],
        "clicks": [100, 150, 250],
        "conversions": [10, 20, 30]
    }
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    # Get database connection
    conn = get_connection()
    
    # Insert data into campaigns table
    df.to_sql("campaigns", conn, if_exists="replace", index=False)
    
    # Close the connection
    conn.close()


    # Create a function get_campaign_performance()
# Requirements:
# - Fetch all campaigns from database
# - For each campaign calculate:
#     ctr = (clicks / impressions) * 100
#     conversion_rate = (conversions / clicks) * 100
# - Handle division by zero
# - Add these metrics to each campaign
# - Find best campaign based on highest conversion_rate
# - Return:
#     {
#       "campaigns": [...],
#       "best_campaign": {...}
#     }
# - Use get_connection()
# - Close connection
# - Keep code clean
def get_campaign_performance():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name, impressions, clicks, conversions FROM campaigns")
    campaigns = cursor.fetchall()
    conn.close()

    campaign_list = []
    best_campaign = None
    highest_conversion_rate = 0

    for name, impressions, clicks, conversions in campaigns:
        ctr = round((clicks / impressions) * 100, 2) if impressions > 0 else 0.00
        conversion_rate = round((conversions / clicks) * 100, 2) if clicks > 0 else 0.00
        
        campaign_data = {
            "name": name,
            "impressions": impressions,
            "clicks": clicks,
            "conversions": conversions,
            "ctr": ctr,
            "conversion_rate": conversion_rate
        }
        
        campaign_list.append(campaign_data)

        if conversion_rate > highest_conversion_rate:
            highest_conversion_rate = conversion_rate
            best_campaign = campaign_data

    return {
        "campaigns": campaign_list,
        "best_campaign": best_campaign
    }