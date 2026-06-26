from app.database.db import get_connection

def initialize_database():
    conn = get_connection()
    cursor = conn.cursor()

    # Create campaigns table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS campaigns (
        id INTEGER PRIMARY KEY,
        name TEXT,
        impressions INTEGER,
        clicks INTEGER,
        conversions INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        is_deleted BOOLEAN DEFAULT 0
    )
    """)

    # Migrate existing databases: add timestamp columns if missing
    for col_sql in [
        "ALTER TABLE campaigns ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
        "ALTER TABLE campaigns ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
        "ALTER TABLE campaigns ADD COLUMN is_deleted BOOLEAN DEFAULT 0",
    ]:
        try:
            cursor.execute(col_sql)
            conn.commit()
        except Exception:
            pass  # Column already exists

    # Create users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        full_name TEXT,
        hashed_password TEXT NOT NULL,
        is_active BOOLEAN DEFAULT 1,
        role TEXT DEFAULT 'viewer' CHECK(role IN ('admin', 'analyst', 'viewer')),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Migrate existing databases: add role column if missing
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'viewer' CHECK(role IN ('admin', 'analyst', 'viewer'))")
        conn.commit()
    except Exception:
        pass  # Column already exists

    # Migrate: add oauth columns if missing
    for col_sql in [
        "ALTER TABLE users ADD COLUMN oauth_provider TEXT DEFAULT NULL",
        "ALTER TABLE users ADD COLUMN oauth_id TEXT DEFAULT NULL",
    ]:
        try:
            cursor.execute(col_sql)
            conn.commit()
        except Exception:
            pass  # Column already exists

    # Create indexes for users
    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)
    """)
    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)
    """)

    # Create audit_logs table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        username TEXT NOT NULL,
        action TEXT NOT NULL,
        campaign_id INTEGER,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()
    print("Database and tables created successfully!")

if __name__ == "__main__":
    initialize_database()
