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