-- Create table campaigns
-- Columns:
-- id INTEGER PRIMARY KEY
-- name TEXT
-- impressions INTEGER
-- clicks INTEGER
-- conversions INTEGER
-- Use CREATE TABLE IF NOT EXISTS
-- Do NOT add extra columns
CREATE TABLE IF NOT EXISTS campaigns (
    id INTEGER PRIMARY KEY,
    name TEXT,
    impressions INTEGER,
    clicks INTEGER,
    conversions INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN DEFAULT 0
);

-- Create table users for authentication
-- Columns:
-- id INTEGER PRIMARY KEY
-- username TEXT UNIQUE
-- email TEXT UNIQUE
-- full_name TEXT
-- hashed_password TEXT
-- is_active BOOLEAN
-- created_at TIMESTAMP
-- updated_at TIMESTAMP
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    full_name TEXT,
    hashed_password TEXT NOT NULL,
    is_active BOOLEAN DEFAULT 1,
    role TEXT DEFAULT 'viewer' CHECK(role IN ('admin', 'analyst', 'viewer')),
    oauth_provider TEXT DEFAULT NULL,
    oauth_id TEXT DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index on username and email for faster lookups
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);