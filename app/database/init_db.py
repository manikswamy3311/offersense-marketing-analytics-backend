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
        conversions INTEGER
    )
    """)

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

    # Create indexes for users
    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)
    """)
    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)
    """)

    conn.commit()
    conn.close()
    print("Database and tables created successfully!")

if __name__ == "__main__":
    initialize_database()
