# database/db.py

import sqlite3

DB_PATH   = 'database/ipo_tracker.db'

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.execute('PRAGMA foreign_keys = ON')
    return conn

def execute_schema():
    conn   = get_conn()
    with open('database/schema.sql') as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()
    print('Schema created successfully')

if __name__ == '__main__':
    execute_schema()
