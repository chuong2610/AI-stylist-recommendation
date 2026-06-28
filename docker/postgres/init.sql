-- ============================================================
-- PostgreSQL Init: chat/session storage only
-- Runs automatically on first "docker compose up" (empty volume)
-- ============================================================

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS chat_sessions (
    id         UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id    VARCHAR(100) NOT NULL,
    title      VARCHAR(255),
    created_at TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_chat_sessions_user_id ON chat_sessions (user_id);

CREATE TABLE IF NOT EXISTS messages (
    id         UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID         NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    role       VARCHAR(20)  NOT NULL,
    content    TEXT         NOT NULL,
    intent     VARCHAR(50),
    metadata   JSONB,
    created_at TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_messages_session_id ON messages (session_id);
