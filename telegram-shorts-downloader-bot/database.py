import sqlite3
import datetime
from config import DB_PATH

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        full_name TEXT,
        join_date TEXT,
        downloads_count INTEGER DEFAULT 0,
        is_vip INTEGER DEFAULT 0,
        referrer_id INTEGER DEFAULT 0
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS downloads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        video_title TEXT,
        video_url TEXT,
        format TEXT,
        downloaded_at TEXT
    )
    """)
    
    conn.commit()
    conn.close()

def register_user(user_id: int, username: str, full_name: str, referrer_id: int = 0):
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    cursor.execute("""
    INSERT OR IGNORE INTO users (user_id, username, full_name, join_date, referrer_id)
    VALUES (?, ?, ?, ?, ?)
    """, (user_id, username or "", full_name or "", now, referrer_id))
    
    # Update username or name if changed
    cursor.execute("""
    UPDATE users SET username = ?, full_name = ? WHERE user_id = ?
    """, (username or "", full_name or "", user_id))
    
    conn.commit()
    conn.close()

def get_user(user_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def record_download(user_id: int, title: str, url: str, format_type: str):
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    cursor.execute("""
    INSERT INTO downloads (user_id, video_title, video_url, format, downloaded_at)
    VALUES (?, ?, ?, ?, ?)
    """, (user_id, title, url, format_type, now))
    
    cursor.execute("""
    UPDATE users SET downloads_count = downloads_count + 1 WHERE user_id = ?
    """, (user_id,))
    
    conn.commit()
    conn.close()

def get_stats():
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) as total_users FROM users")
    total_users = cursor.fetchone()['total_users']
    
    cursor.execute("SELECT COUNT(*) as total_downloads FROM downloads")
    total_downloads = cursor.fetchone()['total_downloads']
    
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    cursor.execute("SELECT COUNT(*) as today_downloads FROM downloads WHERE downloaded_at LIKE ?", (f"{today}%",))
    today_downloads = cursor.fetchone()['today_downloads']
    
    conn.close()
    return {
        'total_users': total_users,
        'total_downloads': total_downloads,
        'today_downloads': today_downloads
    }

def get_all_user_ids():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users")
    rows = cursor.fetchall()
    conn.close()
    return [row['user_id'] for row in rows]
