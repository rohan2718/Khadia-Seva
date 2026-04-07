import sqlite3
from datetime import datetime

KHADIA_PINCODES = {'380001', '380002', '380008', '380016'}


def get_connection(db_path='khadia_seva.db'):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path='khadia_seva.db'):
    conn = get_connection(db_path)
    cursor = conn.cursor()

    cursor.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            mobile TEXT UNIQUE NOT NULL,
            ward TEXT NOT NULL,
            pincode TEXT,
            role TEXT NOT NULL DEFAULT 'user',
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            category TEXT NOT NULL,
            suggested_category TEXT,
            priority TEXT NOT NULL DEFAULT 'Normal',
            status TEXT NOT NULL DEFAULT 'Pending',
            location_text TEXT,
            latitude TEXT,
            longitude TEXT,
            image_filename TEXT,
            assigned_to TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            complaint_id INTEGER,
            message TEXT NOT NULL,
            is_read INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (complaint_id) REFERENCES complaints(id)
        );

        CREATE TABLE IF NOT EXISTS complaint_updates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            complaint_id INTEGER NOT NULL,
            note TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (complaint_id) REFERENCES complaints(id)
        );
        """
    )

    now = datetime.utcnow().isoformat()
    cursor.execute(
        """
        INSERT OR IGNORE INTO users (name, mobile, ward, pincode, role, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        ('Admin User', '9999999999', 'Khadia', '380001', 'admin', now),
    )

    conn.commit()
    conn.close()


def is_allowed_ward(ward, pincode):
    return (ward or '').strip().lower() == 'khadia' or (pincode or '').strip() in KHADIA_PINCODES


def suggest_category(text):
    text = (text or '').lower()
    mapping = {
        'Garbage': ['garbage', 'waste', 'trash', 'dump'],
        'Road': ['road', 'pothole', 'street damage', 'crack'],
        'Water': ['water', 'leakage', 'supply', 'pipeline'],
        'Drainage': ['drain', 'sewage', 'drainage', 'overflow'],
        'Street Light': ['light', 'streetlight', 'lamp', 'dark'],
    }
    for category, keywords in mapping.items():
        if any(word in text for word in keywords):
            return category
    return 'Other'


def detect_priority(text):
    text = (text or '').lower()
    urgent_keywords = ['danger', 'accident', 'fire', 'water leakage', 'electrocution', 'collapse', 'emergency']
    return 'High' if any(keyword in text for keyword in urgent_keywords) else 'Normal'
