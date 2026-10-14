-- ============================================================
-- WineCoach PostgreSQL 建表脚本
-- 数据库：wine_coach_memory（L2 摘要记忆）
-- 执行前需先创建数据库：CREATE DATABASE wine_coach_memory;
-- ============================================================

-- 会话摘要表（(session_id, user_id) 唯一约束，供 UPSERT 使用）
CREATE TABLE IF NOT EXISTS session_summary (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(64) NOT NULL,
    user_id VARCHAR(64) NOT NULL,
    summary TEXT,
    UNIQUE (session_id, user_id)
);
