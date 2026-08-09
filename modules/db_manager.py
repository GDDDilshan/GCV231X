import sqlite3
import os
import xml.etree.ElementTree as ET
from modules.config import DB_PATH

class DatabaseManager:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        """Initialize database tables if they do not exist."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Students Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS students (
                student_index TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                title TEXT,
                batch TEXT DEFAULT '2016.1'
            )
        """)

        # Sessions Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_date TEXT NOT NULL,
                time_range TEXT,
                lecturer_name TEXT,
                image_source TEXT UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Attendance Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS attendance (
                attendance_id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                student_index TEXT NOT NULL,
                status TEXT NOT NULL, -- 'PRESENT' or 'ABSENT'
                ink_density REAL,
                cropped_signature_path TEXT,
                FOREIGN KEY (session_id) REFERENCES sessions (session_id),
                FOREIGN KEY (student_index) REFERENCES students (student_index)
            )
        """)

        # Signatures Reference Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS signature_templates (
                template_id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_index TEXT NOT NULL,
                template_path TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_index) REFERENCES students (student_index)
            )
        """)

        conn.commit()
        conn.close()

    def sync_students_from_xml(self, xml_path):
        """Parse student info from XML and sync with database."""
        if not os.path.exists(xml_path):
            raise FileNotFoundError(f"XML file not found at: {xml_path}")

        tree = ET.parse(xml_path)
        root = tree.getroot()

        conn = self._get_connection()
        cursor = conn.cursor()

        synced_count = 0
        # Search for student nodes recursively
        for student_elem in root.iter('student'):
            index = student_elem.findtext('index')
            name = student_elem.findtext('name')
            title = student_elem.findtext('title') or ''

            if index and name:
                cursor.execute("""
                    INSERT INTO students (student_index, name, title)
                    VALUES (?, ?, ?)
                    ON CONFLICT(student_index) DO UPDATE SET
                        name=excluded.name,
                        title=excluded.title
                """, (index.strip(), name.strip(), title.strip()))
                synced_count += 1

        conn.commit()
        conn.close()
        return synced_count