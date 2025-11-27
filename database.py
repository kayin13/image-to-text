import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, date
from typing import Optional, List, Dict, Any

DATABASE_URL = os.environ.get("DATABASE_URL")


def get_connection():
    return psycopg2.connect(DATABASE_URL)


def init_database():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS extracted_texts (
            id SERIAL PRIMARY KEY,
            filename VARCHAR(255) NOT NULL,
            extracted_text TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    cur.close()
    conn.close()


def save_extracted_text(filename: str, extracted_text: str) -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO extracted_texts (filename, extracted_text)
        VALUES (%s, %s)
        RETURNING id
        """,
        (filename, extracted_text)
    )
    result = cur.fetchone()
    record_id = result[0] if result else 0
    conn.commit()
    cur.close()
    conn.close()
    return record_id


def get_all_records() -> List[Dict[str, Any]]:
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT id, filename, extracted_text, created_at
        FROM extracted_texts
        ORDER BY created_at DESC
    """)
    records = cur.fetchall()
    cur.close()
    conn.close()
    return list(records)


def search_records(query: str) -> List[Dict[str, Any]]:
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT id, filename, extracted_text, created_at
        FROM extracted_texts
        WHERE filename ILIKE %s OR extracted_text ILIKE %s
        ORDER BY created_at DESC
    """, (f"%{query}%", f"%{query}%"))
    records = cur.fetchall()
    cur.close()
    conn.close()
    return list(records)


def search_records_advanced(
    keyword: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> List[Dict[str, Any]]:
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    query = "SELECT id, filename, extracted_text, created_at FROM extracted_texts WHERE 1=1"
    params: List[Any] = []
    
    if keyword:
        query += " AND (filename ILIKE %s OR extracted_text ILIKE %s)"
        params.extend([f"%{keyword}%", f"%{keyword}%"])
    
    if start_date:
        query += " AND created_at >= %s"
        params.append(datetime.combine(start_date, datetime.min.time()))
    
    if end_date:
        query += " AND created_at <= %s"
        params.append(datetime.combine(end_date, datetime.max.time()))
    
    query += " ORDER BY created_at DESC"
    
    cur.execute(query, params)
    records = cur.fetchall()
    cur.close()
    conn.close()
    return list(records)


def delete_record(record_id: int) -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM extracted_texts WHERE id = %s", (record_id,))
    conn.commit()
    cur.close()
    conn.close()


def update_extracted_text(record_id: int, new_text: str) -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE extracted_texts SET extracted_text = %s WHERE id = %s",
        (new_text, record_id)
    )
    conn.commit()
    cur.close()
    conn.close()


def get_record_by_id(record_id: int) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute(
        "SELECT id, filename, extracted_text, created_at FROM extracted_texts WHERE id = %s",
        (record_id,)
    )
    record = cur.fetchone()
    cur.close()
    conn.close()
    return dict(record) if record else None
