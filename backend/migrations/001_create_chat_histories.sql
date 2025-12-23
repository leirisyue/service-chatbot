-- Create chat_histories table for storing chat logs
CREATE TABLE IF NOT EXISTS chat_histories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    email TEXT NOT NULL,
    session_id TEXT NOT NULL,
    
    chat_date DATE NOT NULL,          -- ngày chat (YYYY-MM-DD)
    time_block SMALLINT NOT NULL,     -- 1 = 0-12h, 2 = 12-24h
    
    history JSONB NOT NULL,           -- toàn bộ Q&A
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE (email, session_id, chat_date, time_block)
);

-- Create index for faster retrieval by email and session_id
CREATE INDEX IF NOT EXISTS idx_chat_histories_email_session 
    ON chat_histories(email, session_id, chat_date DESC, time_block DESC);

-- Create index for date-based queries
CREATE INDEX IF NOT EXISTS idx_chat_histories_date 
    ON chat_histories(chat_date DESC);

-- Add comment to table
COMMENT ON TABLE chat_histories IS 'Stores chat conversation history grouped by date and time blocks';
COMMENT ON COLUMN chat_histories.time_block IS '1 = 0-12h, 2 = 12-24h';
COMMENT ON COLUMN chat_histories.history IS 'JSONB array of Q&A pairs: [{question: string, answer: string, timestamp: string, ocr_text: string}]';
