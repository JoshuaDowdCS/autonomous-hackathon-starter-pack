import sqlite3
import json
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'hackathon.db')

def get_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    
    # raw_data table
    c.execute('''
        CREATE TABLE IF NOT EXISTS raw_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT,
            data TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # user_profile table
    c.execute('''
        CREATE TABLE IF NOT EXISTS user_profile (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT,
            answer TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # pipeline_state table
    # status field: idle | running | eval_failed | complete
    c.execute('''
        CREATE TABLE IF NOT EXISTS pipeline_state (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE,
            status TEXT,
            value TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print("Database initialized at", DB_PATH)

def set_state(key: str, status: str, value: str = ""):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO pipeline_state (key, status, value)
        VALUES (?, ?, ?)
        ON CONFLICT(key) DO UPDATE SET status=excluded.status, value=excluded.value, timestamp=CURRENT_TIMESTAMP
    ''', (key, status, value))
    conn.commit()
    conn.close()

def get_state(key: str):
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT status, value FROM pipeline_state WHERE key = ?', (key,))
    row = c.fetchone()
    conn.close()
    if row:
        return {"status": row[0], "value": row[1]}
    return None

def append_raw_data(source: str, data: str):
    conn = get_connection()
    c = conn.cursor()
    c.execute('INSERT INTO raw_data (source, data) VALUES (?, ?)', (source, data))
    conn.commit()
    conn.close()

def append_user_profile(question: str, answer: str):
    conn = get_connection()
    c = conn.cursor()
    c.execute('INSERT INTO user_profile (question, answer) VALUES (?, ?)', (question, answer))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    
    # Test: write a dummy record and read it back
    set_state("test_step", "running", json.dumps({"test": "data"}))
    print(get_state("test_step"))
