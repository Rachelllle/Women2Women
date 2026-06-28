-- schema.sql
-- Run this file to set up the database schema

-- Add missing columns to users table
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS name VARCHAR(100),
ADD COLUMN IF NOT EXISTS last_period DATE,
ADD COLUMN IF NOT EXISTS cycle_len INT DEFAULT 28,
ADD COLUMN IF NOT EXISTS period_len INT DEFAULT 5;

-- Create cycle history table
CREATE TABLE IF NOT EXISTS cycle_history (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    user_id     INT NOT NULL,
    start_date  DATE NOT NULL,
    end_date    DATE,
    cycle_len   INT,
    notes       TEXT,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);