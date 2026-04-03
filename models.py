import sqlite3

DB_NAME = "database.db"

# ------------------- CONNECT DB -------------------
def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # Allows dict-like access
    return conn


# ------------------- INIT DB -------------------
def init_db():
    db = get_db()

    # USERS TABLE
    db.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    """)

    # HISTORY TABLE
    db.execute("""
    CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        study REAL,
        absences REAL,
        failures REAL,
        prediction REAL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    db.commit()
    db.close()