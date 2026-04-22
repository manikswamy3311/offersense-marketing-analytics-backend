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
    conversions INTEGER
);