"""SQLite data layer.

Zero-config: the whole database is a single file (women2women.db) created next
to the project. No server to start — just run app.py. `db_query` keeps the same
signature as before; it auto-translates MySQL-style %s placeholders to SQLite's
? so the rest of the app didn't need to change.
"""
import os
import sqlite3

DB_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),   # the database/ folder
    "women2women.db",
)


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row   # rows accessible by column name
    return conn


def db_query(sql, params=(), one=False, write=False):
    sql = sql.replace("%s", "?")     # accept legacy MySQL-style placeholders
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute(sql, params)
        if write:
            conn.commit()
            return cur.rowcount
        rows = cur.fetchall()
        if one:
            return dict(rows[0]) if rows else None
        return [dict(r) for r in rows]
    finally:
        conn.close()
