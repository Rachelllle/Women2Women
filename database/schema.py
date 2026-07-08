"""Database schema setup — creates the users table and applies light migrations."""
from database.db import db_query


def init_db():
    db_query("""
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            email         TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            name          TEXT,
            last_period   TEXT,
            cycle_len     INTEGER DEFAULT 28,
            period_len    INTEGER DEFAULT 5,
            avatar        TEXT,
            notif_prefs   TEXT,
            created_at    TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """, write=True)
    # add columns if an older database was missing them
    existing = {r["name"] for r in db_query("PRAGMA table_info(users)")}
    for col, defn in [
        ("name",        "TEXT"),
        ("last_period", "TEXT"),
        ("cycle_len",   "INTEGER DEFAULT 28"),
        ("period_len",  "INTEGER DEFAULT 5"),
        ("avatar",      "TEXT"),
        ("notif_prefs", "TEXT"),
    ]:
        if col not in existing:
            try:
                db_query(f"ALTER TABLE users ADD COLUMN {col} {defn}", write=True)
            except Exception:
                pass

    # Cycle history (Katia's feature) — one archived row per completed cycle
    db_query("""
        CREATE TABLE IF NOT EXISTS cycle_history (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER NOT NULL,
            start_date TEXT NOT NULL,
            end_date   TEXT,
            cycle_len  INTEGER,
            period_len INTEGER,
            notes      TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """, write=True)
    # migration: add period_len to an existing cycle_history table
    hcols = {r["name"] for r in db_query("PRAGMA table_info(cycle_history)")}
    if "period_len" not in hcols:
        try:
            db_query("ALTER TABLE cycle_history ADD COLUMN period_len INTEGER", write=True)
        except Exception:
            pass

    _init_alerting_tables()


def _init_alerting_tables():
    """Alerting module (Nadia's feature) — MySQL schema ported to SQLite:
    ENUM/BOOLEAN -> TEXT/INTEGER, AUTO_INCREMENT -> AUTOINCREMENT, JSON -> TEXT.
    """
    db_query("""
        CREATE TABLE IF NOT EXISTS alerting_profile (
            user_id          INTEGER PRIMARY KEY,
            birth_date       TEXT,
            phone_number     TEXT,
            whatsapp_consent INTEGER DEFAULT 0,
            created_at       TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """, write=True)

    db_query("""
        CREATE TABLE IF NOT EXISTS cycles (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            start_date  TEXT NOT NULL,
            period_len  INTEGER,
            cycle_len   INTEGER,
            logged_late INTEGER DEFAULT 0,
            source      TEXT DEFAULT 'real_user',
            created_at  TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """, write=True)
    db_query("CREATE INDEX IF NOT EXISTS idx_cycles_user_date ON cycles(user_id, start_date)", write=True)

    db_query("""
        CREATE TABLE IF NOT EXISTS symptom_logs (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER NOT NULL,
            log_date   TEXT NOT NULL,
            cycle_day  INTEGER,
            phase      TEXT,
            pain_score INTEGER,
            symptoms   TEXT,
            source     TEXT DEFAULT 'real_user',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """, write=True)
    db_query("CREATE INDEX IF NOT EXISTS idx_symptom_user_date ON symptom_logs(user_id, log_date)", write=True)

    db_query("""
        CREATE TABLE IF NOT EXISTS symptom_catalog_stats (
            id                   INTEGER PRIMARY KEY AUTOINCREMENT,
            phase                TEXT,
            age_bracket          TEXT,
            symptom_tag          TEXT,
            occurrence_count     INTEGER DEFAULT 0,
            total_logs_in_bucket INTEGER DEFAULT 0,
            last_updated         TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (phase, age_bracket, symptom_tag)
        )
    """, write=True)

    db_query("""
        CREATE TABLE IF NOT EXISTS alerts_log (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id       INTEGER NOT NULL,
            type          TEXT,
            level         TEXT,
            score         REAL,
            message_sent  TEXT,
            sent_at       TEXT DEFAULT CURRENT_TIMESTAMP,
            whatsapp_sent INTEGER DEFAULT 0,
            user_feedback TEXT DEFAULT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """, write=True)
    # migration: add whatsapp_sent to an existing alerts_log table
    cols = {r["name"] for r in db_query("PRAGMA table_info(alerts_log)")}
    if "whatsapp_sent" not in cols:
        try:
            db_query("ALTER TABLE alerts_log ADD COLUMN whatsapp_sent INTEGER DEFAULT 0", write=True)
        except Exception:
            pass

    db_query("""
        CREATE TABLE IF NOT EXISTS model_registry (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            model_type          TEXT,
            trained_at          TEXT DEFAULT CURRENT_TIMESTAMP,
            n_users_in_training INTEGER,
            storage_path        TEXT,
            is_active           INTEGER DEFAULT 1
        )
    """, write=True)
