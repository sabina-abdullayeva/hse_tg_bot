import json
import sqlite3
from pathlib import Path
from typing import Optional


ROOT_DIR = Path(__file__).resolve().parent
DB_PATH = ROOT_DIR / "hse.db"
DATA_PATH = ROOT_DIR / "data" / "hse_bachelor_courses_2025.json"


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def _rows_to_dicts(rows: list[sqlite3.Row]) -> list[dict]:
    return [dict(row) for row in rows]


def run_select(sql: str) -> list[dict]:
    with connect() as conn:
        rows = conn.execute(sql).fetchall()
    return _rows_to_dicts(rows)


def search_courses(query: str, limit: int = 5) -> list[dict]:
    query = query.strip()
    if not query:
        return []

    pattern = f"%{query}%"
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT
                c.id,
                c.title,
                c.status,
                c.languages,
                p.id AS program_id,
                p.title AS program_title,
                p.url AS program_url,
                p.courses_url,
                REPLACE(GROUP_CONCAT(DISTINCT t.name), ',', ', ') AS teachers
            FROM courses c
            JOIN programs p ON p.id = c.program_id
            LEFT JOIN teachers t ON t.course_id = c.id
            WHERE c.title LIKE ?
               OR p.title LIKE ?
               OR t.name LIKE ?
            GROUP BY c.id
            ORDER BY p.title, c.title
            LIMIT ?
            """,
            (pattern, pattern, pattern, limit),
        ).fetchall()
    return _rows_to_dicts(rows)


def search_teachers(query: str, limit: int = 8) -> list[dict]:
    query = query.strip()
    if not query:
        return []

    pattern = f"%{query}%"
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT
                t.name,
                c.id AS course_id,
                c.title AS course_title,
                c.status,
                c.languages,
                p.id AS program_id,
                p.title AS program_title,
                p.url AS program_url
            FROM teachers t
            JOIN courses c ON c.id = t.course_id
            JOIN programs p ON p.id = c.program_id
            WHERE t.name LIKE ?
            ORDER BY
                CASE WHEN t.name LIKE ? THEN 0 ELSE 1 END,
                t.name,
                c.title
            LIMIT ?
            """,
            (pattern, f"{query}%", limit),
        ).fetchall()
    return _rows_to_dicts(rows)


def get_programs(page: int = 0, per_page: int = 10) -> list[dict]:
    offset = max(page, 0) * per_page
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT id, title, url, courses_url, courses_count
            FROM programs
            ORDER BY title
            LIMIT ? OFFSET ?
            """,
            (per_page, offset),
        ).fetchall()
    return _rows_to_dicts(rows)


def get_program_courses(program_id: int) -> list[dict]:
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT id, title, status, languages
            FROM courses
            WHERE program_id = ?
            ORDER BY title
            """,
            (program_id,),
        ).fetchall()
    return _rows_to_dicts(rows)


def search_programs(query: str = "", limit: int = 10) -> list[dict]:
    query = query.strip()
    pattern = f"%{query}%"
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT id, title, url, courses_url, courses_count
            FROM programs
            WHERE title LIKE ?
            ORDER BY
                CASE
                    WHEN title = ? THEN 0
                    WHEN title LIKE ? THEN 1
                    ELSE 2
                END,
                title
            LIMIT ?
            """,
            (pattern, query, f"{query}%", limit),
        ).fetchall()
    return _rows_to_dicts(rows)


def search_programs_by_words(words: list[str], limit: int = 10) -> list[dict]:
    if not words:
        return []

    variants = sorted({word for word in words} | {word.capitalize() for word in words} | {word.upper() for word in words})
    where = " OR ".join("title LIKE ?" for _ in variants)
    params = [f"%{word}%" for word in variants]
    with connect() as conn:
        rows = conn.execute(
            f"""
            SELECT id, title, url, courses_url, courses_count
            FROM programs
            WHERE {where}
            ORDER BY title
            LIMIT ?
            """,
            (*params, limit),
        ).fetchall()
    return _rows_to_dicts(rows)


def get_biggest_program() -> Optional[dict]:
    with connect() as conn:
        row = conn.execute(
            """
            SELECT id, title, url, courses_count
            FROM programs
            ORDER BY courses_count DESC
            LIMIT 1
            """
        ).fetchone()
    return dict(row) if row else None


def get_courses_for_program(
    program_query: str,
    status: Optional[str] = None,
    limit: int = 20,
) -> list[dict]:
    program_query = program_query.strip()
    program_pattern = f"%{program_query}%"
    params: list[object] = [program_pattern, program_query, f"{program_query}%"]
    status_filter = ""
    if status:
        status_filter = "AND c.status = ?"
        params.append(status)
    params.append(limit)

    with connect() as conn:
        rows = conn.execute(
            f"""
            SELECT
                c.id,
                c.title,
                c.status,
                c.languages,
                p.title AS program_title
            FROM courses c
            JOIN programs p ON p.id = c.program_id
            WHERE p.id = (
                SELECT id
                FROM programs
                WHERE title LIKE ?
                ORDER BY
                    CASE
                        WHEN title = ? THEN 0
                        WHEN title LIKE ? THEN 1
                        ELSE 2
                    END,
                    title
                LIMIT 1
            )
              {status_filter}
            ORDER BY c.title
            LIMIT ?
            """,
            params,
        ).fetchall()
    return _rows_to_dicts(rows)


def search_courses_by_status(status: str, limit: int = 20) -> list[dict]:
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT
                c.id,
                c.title,
                c.status,
                c.languages,
                p.title AS program_title
            FROM courses c
            JOIN programs p ON p.id = c.program_id
            WHERE c.status = ?
            ORDER BY c.title
            LIMIT ?
            """,
            (status, limit),
        ).fetchall()
    return _rows_to_dicts(rows)


def search_courses_by_language(language: str, limit: int = 20) -> list[dict]:
    pattern = f"%{language.strip()}%"
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT
                c.id,
                c.title,
                c.status,
                c.languages,
                p.title AS program_title
            FROM courses c
            JOIN programs p ON p.id = c.program_id
            WHERE c.languages LIKE ?
            ORDER BY c.title
            LIMIT ?
            """,
            (pattern, limit),
        ).fetchall()
    return _rows_to_dicts(rows)


def search_programs_by_language(language: str, limit: int = 10) -> list[dict]:
    pattern = f"%{language.strip()}%"
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT
                p.id,
                p.title,
                p.url,
                COUNT(c.id) AS courses_count
            FROM programs p
            JOIN courses c ON c.program_id = p.id
            WHERE c.languages LIKE ?
            GROUP BY p.id
            ORDER BY courses_count DESC, p.title
            LIMIT ?
            """,
            (pattern, limit),
        ).fetchall()
    return _rows_to_dicts(rows)


def search_course_programs(course_query: str, limit: int = 20) -> list[dict]:
    pattern = f"%{course_query.strip()}%"
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT
                c.id,
                c.title,
                c.status,
                c.languages,
                p.title AS program_title,
                p.url AS program_url
            FROM courses c
            JOIN programs p ON p.id = c.program_id
            WHERE c.title LIKE ?
            ORDER BY c.title, p.title
            LIMIT ?
            """,
            (pattern, limit),
        ).fetchall()
    return _rows_to_dicts(rows)


def search_course_teachers(course_query: str, limit: int = 20) -> list[dict]:
    pattern = f"%{course_query.strip()}%"
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT DISTINCT
                t.name,
                c.title AS course_title,
                p.title AS program_title
            FROM teachers t
            JOIN courses c ON c.id = t.course_id
            JOIN programs p ON p.id = c.program_id
            WHERE c.title LIKE ?
            ORDER BY t.name, c.title
            LIMIT ?
            """,
            (pattern, limit),
        ).fetchall()
    return _rows_to_dicts(rows)


def get_teacher_stats(query: str, limit: int = 10) -> list[dict]:
    pattern = f"%{query.strip()}%"
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT
                t.name,
                COUNT(DISTINCT c.id) AS courses_count,
                COUNT(DISTINCT p.id) AS programs_count
            FROM teachers t
            JOIN courses c ON c.id = t.course_id
            JOIN programs p ON p.id = c.program_id
            WHERE t.name LIKE ?
            GROUP BY t.name
            ORDER BY
                CASE WHEN t.name LIKE ? THEN 0 ELSE 1 END,
                courses_count DESC,
                t.name
            LIMIT ?
            """,
            (pattern, f"{query}%", limit),
        ).fetchall()
    return _rows_to_dicts(rows)


def get_top_teachers(limit: int = 10) -> list[dict]:
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT
                t.name,
                COUNT(DISTINCT c.id) AS courses_count
            FROM teachers t
            JOIN courses c ON c.id = t.course_id
            GROUP BY t.name
            ORDER BY courses_count DESC, t.name
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return _rows_to_dicts(rows)

