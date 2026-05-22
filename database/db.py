import pymysql, pymysql.cursors

DB_CONFIG = {
    "host":        "127.0.0.1",
    "user":        "root",
    "password":    "",
    "db":          "women2women",
    "charset":     "utf8mb4",
    "cursorclass": pymysql.cursors.DictCursor,
}

def get_db():
    return pymysql.connect(**DB_CONFIG)

def db_query(sql, params=(), one=False, write=False):
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            if write:
                conn.commit()
                return cur.rowcount
            return cur.fetchone() if one else cur.fetchall()
    finally:
        conn.close()
