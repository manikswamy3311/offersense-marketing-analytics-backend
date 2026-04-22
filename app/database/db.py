# Create a simple SQLite connection using sqlite3
# Database name: offersense.db
# Create a function get_connection()
# It should:
# - connect to database
# - set row_factory to sqlite3.Row
# - return connection
# Do NOT use SQLAlchemy
# Do NOT add extra code

import sqlite3

def get_connection():
    conn = sqlite3.connect('offersense.db')
    conn.row_factory = sqlite3.Row
    return conn 
