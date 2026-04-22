from app.database.db import get_connection

def initialize_database():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS campaigns (
        id INTEGER PRIMARY KEY,
        name TEXT,
        impressions INTEGER,
        clicks INTEGER,
        conversions INTEGER
    )
    """)

    conn.commit()
    conn.close()
    print("Database and table created successfully!")

if __name__ == "__main__":
    initialize_database()
