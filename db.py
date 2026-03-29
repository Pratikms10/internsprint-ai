import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    return pymysql.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", 3306)),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "internsprint"),
        cursorclass=pymysql.cursors.DictCursor
    )

def get_all_internships():
    """Fetch all open internships from MySQL"""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT i.id, i.title, i.domain, i.location,
                       i.skills_required, i.stipend, i.duration,
                       i.deadline, c.company_name,
                       CAST(c.is_verified AS UNSIGNED) as is_verified
                FROM internships i
                JOIN companies c ON i.company_id = c.id
                WHERE i.status = 'open'
            """)
            rows = cursor.fetchall()
            # Convert any remaining bytes/date objects to serializable types
            for row in rows:
                for key, val in row.items():
                    if isinstance(val, bytes):
                        row[key] = bool(val[0]) if val else False
                    elif hasattr(val, 'isoformat'):
                        row[key] = val.isoformat()
            return rows
    finally:
        conn.close()

def get_student_skills(user_id):
    """Fetch a student's skills from their profile"""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT skills FROM student_profiles WHERE user_id = %s",
                (user_id,)
            )
            row = cursor.fetchone()
            return row['skills'] if row and row['skills'] else ""
    finally:
        conn.close()