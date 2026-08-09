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

    def save_session_attendance(self, session_date, time_range, lecturer_name, image_source, attendance_results):
        """
        Save or update attendance for a session.
        attendance_results: list of dicts: [{'student_index': '10000409', 'status': 'PRESENT', 'ink_density': 0.045, 'crop_path': '...'}, ...]
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Insert or get session
        cursor.execute("""
            INSERT INTO sessions (session_date, time_range, lecturer_name, image_source)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(image_source) DO UPDATE SET
                session_date=excluded.session_date,
                time_range=excluded.time_range,
                lecturer_name=excluded.lecturer_name
        """, (session_date, time_range, lecturer_name, os.path.basename(image_source)))

        cursor.execute("SELECT session_id FROM sessions WHERE image_source = ?", (os.path.basename(image_source),))
        session_id = cursor.fetchone()[0]

        # Clear previous attendance records for this session if re-running
        cursor.execute("DELETE FROM attendance WHERE session_id = ?", (session_id,))

        # Insert attendance rows
        for item in attendance_results:
            cursor.execute("""
                INSERT INTO attendance (session_id, student_index, status, ink_density, cropped_signature_path)
                VALUES (?, ?, ?, ?, ?)
            """, (session_id, item['student_index'], item['status'], item.get('ink_density', 0.0), item.get('crop_path', '')))

        conn.commit()
        conn.close()
        return session_id

    def get_student_info(self, student_index):
        """Fetch student details."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT student_index, name, title, batch FROM students WHERE student_index = ?", (student_index,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return {"student_index": row[0], "name": row[1], "title": row[2], "batch": row[3]}
        return None

    def get_student_attendance_history(self, student_index):
        """Fetch attendance history across all sessions for a given student."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT s.session_date, s.time_range, s.lecturer_name, a.status, a.ink_density, a.cropped_signature_path
            FROM attendance a
            JOIN sessions s ON a.session_id = s.session_id
            WHERE a.student_index = ?
            ORDER BY s.session_date ASC
        """, (student_index,))
        rows = cursor.fetchall()
        conn.close()

        history = []
        for row in rows:
            history.append({
                "date": row[0],
                "time": row[1],
                "lecturer": row[2],
                "status": row[3],
                "ink_density": row[4],
                "signature_path": row[5]
            })
        return history

    def get_all_student_indices(self):
        """Get list of all student indices."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT student_index FROM students")
        rows = cursor.fetchall()
        conn.close()
        return [r[0] for r in rows]

    def register_signature_template(self, student_index, template_path):
        """Register a reference signature template for verification."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO signature_templates (student_index, template_path)
            VALUES (?, ?)
        """, (student_index, template_path))
        conn.commit()
        conn.close()

    def get_signature_templates(self, student_index):
        """Get baseline signature template paths for a student."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT template_path FROM signature_templates WHERE student_index = ?", (student_index,))
        rows = cursor.fetchall()
        conn.close()
        return [r[0] for r in rows]
