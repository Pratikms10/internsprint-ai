import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "bvruysje8hnyddzrnmgo-mysql.services.clever-cloud.com"),
    "port": int(os.getenv("DB_PORT", 3306)),
    "user": os.getenv("DB_USER", "usvqkhlcpxivmogv"),
    "password": os.getenv("DB_PASSWORD", "o1g58IKOhrNTkmSf4P7t"),
    "database": os.getenv("DB_NAME", "bvruysje8hnyddzrnmgo"),
    "cursorclass": pymysql.cursors.DictCursor,
    "connect_timeout": 10,
    "autocommit": True,
}

def get_connection():
    return pymysql.connect(**DB_CONFIG)

def get_all_internships():
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