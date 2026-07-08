-- ============================================================
-- Module Alerting — Women2Women
-- Nouvelles tables uniquement. Aucune modification des tables
-- existantes (users, etc.). Toutes reliées via FOREIGN KEY.
-- ============================================================

CREATE TABLE IF NOT EXISTS alerting_profile (
    user_id           INT PRIMARY KEY,
    birth_date        DATE,
    phone_number      VARCHAR(20),
    whatsapp_consent  BOOLEAN DEFAULT FALSE,
    created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS cycles (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    user_id       INT NOT NULL,
    start_date    DATE NOT NULL,
    period_len    INT,
    cycle_len     INT,
    logged_late   BOOLEAN DEFAULT FALSE,
    source        ENUM('real_user','seed_dataset') DEFAULT 'real_user',
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    INDEX idx_user_date (user_id, start_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS symptom_logs (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    user_id       INT NOT NULL,
    log_date      DATE NOT NULL,
    cycle_day     INT,
    phase         ENUM('menstrual','follicular','ovulation','luteal'),
    pain_score    INT,
    symptoms      JSON,
    source        ENUM('real_user','seed_dataset') DEFAULT 'real_user',
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    INDEX idx_user_date (user_id, log_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS symptom_catalog_stats (
    id                     INT AUTO_INCREMENT PRIMARY KEY,
    phase                  ENUM('menstrual','follicular','ovulation','luteal'),
    age_bracket            ENUM('18-25','26-35','36-45','46+'),
    symptom_tag            VARCHAR(50),
    occurrence_count       INT DEFAULT 0,
    total_logs_in_bucket   INT DEFAULT 0,
    last_updated           TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_bucket_symptom (phase, age_bracket, symptom_tag)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS alerts_log (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    user_id        INT NOT NULL,
    type           ENUM('missed_log','late_period','irregularity','abnormal_pain'),
    level          ENUM('info','attention','recommandation'),
    score          FLOAT,
    message_sent   TEXT,
    sent_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_feedback  ENUM('utile','pas_pertinent') DEFAULT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS model_registry (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    model_type          VARCHAR(50),
    trained_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    n_users_in_training INT,
    storage_path        VARCHAR(255),
    is_active           BOOLEAN DEFAULT TRUE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;