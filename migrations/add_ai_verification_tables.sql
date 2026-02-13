-- CivicFix AI Verification and Enhanced Timeline Schema
-- Migration: Add AI verification, timeline events, and escalation tables

-- ================================
-- Timeline Events (Immutable Log)
-- ================================
CREATE TABLE IF NOT EXISTS timeline_events (
    id SERIAL PRIMARY KEY,
    issue_id INTEGER NOT NULL REFERENCES issues(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL,
    actor_type VARCHAR(20) NOT NULL CHECK (actor_type IN ('CITIZEN', 'AI', 'GOVERNMENT', 'SYSTEM')),
    actor_id INTEGER,
    description TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    image_urls TEXT[],
    created_at TIMESTAMP DEFAULT NOW(),
    
    -- Indexes for performance
    CONSTRAINT timeline_events_issue_id_idx FOREIGN KEY (issue_id) REFERENCES issues(id)
);

CREATE INDEX IF NOT EXISTS idx_timeline_events_issue_id ON timeline_events(issue_id);
CREATE INDEX IF NOT EXISTS idx_timeline_events_created_at ON timeline_events(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_timeline_events_event_type ON timeline_events(event_type);

-- ================================
-- AI Verification Results
-- ================================
CREATE TABLE IF NOT EXISTS ai_verifications (
    id SERIAL PRIMARY KEY,
    issue_id INTEGER NOT NULL REFERENCES issues(id) ON DELETE CASCADE,
    verification_type VARCHAR(50) NOT NULL CHECK (verification_type IN ('INITIAL', 'CROSS_VERIFICATION', 'REVALIDATION')),
    status VARCHAR(20) NOT NULL CHECK (status IN ('APPROVED', 'REJECTED', 'NEEDS_REVIEW', 'PENDING')),
    confidence_score FLOAT CHECK (confidence_score >= 0 AND confidence_score <= 1),
    rejection_reasons TEXT[],
    checks_performed JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT ai_verifications_issue_id_idx FOREIGN KEY (issue_id) REFERENCES issues(id)
);

CREATE INDEX IF NOT EXISTS idx_ai_verifications_issue_id ON ai_verifications(issue_id);
CREATE INDEX IF NOT EXISTS idx_ai_verifications_status ON ai_verifications(status);
CREATE INDEX IF NOT EXISTS idx_ai_verifications_created_at ON ai_verifications(created_at DESC);

-- ================================
-- Citizen Verifications
-- ================================
CREATE TABLE IF NOT EXISTS citizen_verifications (
    id SERIAL PRIMARY KEY,
    issue_id INTEGER NOT NULL REFERENCES issues(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    verification_type VARCHAR(50) NOT NULL CHECK (verification_type IN ('FINAL_VERIFICATION', 'PROGRESS_CHECK', 'DISPUTE')),
    status VARCHAR(20) NOT NULL CHECK (status IN ('VERIFIED', 'NOT_VERIFIED', 'DISPUTED')),
    image_urls TEXT[],
    notes TEXT,
    location_verified BOOLEAN DEFAULT FALSE,
    latitude FLOAT,
    longitude FLOAT,
    created_at TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT citizen_verifications_issue_id_idx FOREIGN KEY (issue_id) REFERENCES issues(id),
    CONSTRAINT citizen_verifications_user_id_idx FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_citizen_verifications_issue_id ON citizen_verifications(issue_id);
CREATE INDEX IF NOT EXISTS idx_citizen_verifications_user_id ON citizen_verifications(user_id);
CREATE INDEX IF NOT EXISTS idx_citizen_verifications_status ON citizen_verifications(status);

-- ================================
-- Escalations
-- ================================
CREATE TABLE IF NOT EXISTS escalations (
    id SERIAL PRIMARY KEY,
    issue_id INTEGER NOT NULL REFERENCES issues(id) ON DELETE CASCADE,
    trigger_reason VARCHAR(100) NOT NULL,
    evidence_bundle JSONB DEFAULT '{}',
    nearest_police_station JSONB DEFAULT '{}',
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'APPROVED', 'FILED', 'REJECTED', 'RESOLVED')),
    admin_notes TEXT,
    admin_id INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT escalations_issue_id_idx FOREIGN KEY (issue_id) REFERENCES issues(id)
);

CREATE INDEX IF NOT EXISTS idx_escalations_issue_id ON escalations(issue_id);
CREATE INDEX IF NOT EXISTS idx_escalations_status ON escalations(status);
CREATE INDEX IF NOT EXISTS idx_escalations_created_at ON escalations(created_at DESC);

-- ================================
-- AI Assistant Conversations
-- ================================
CREATE TABLE IF NOT EXISTS ai_conversations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    issue_id INTEGER REFERENCES issues(id) ON DELETE SET NULL,
    messages JSONB DEFAULT '[]',
    context JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT ai_conversations_user_id_idx FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_ai_conversations_user_id ON ai_conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_ai_conversations_issue_id ON ai_conversations(issue_id);
CREATE INDEX IF NOT EXISTS idx_ai_conversations_updated_at ON ai_conversations(updated_at DESC);

-- ================================
-- Modify Issues Table
-- ================================

-- Add new columns to issues table
ALTER TABLE issues 
    ADD COLUMN IF NOT EXISTS ai_verification_status VARCHAR(20) DEFAULT 'PENDING' CHECK (ai_verification_status IN ('PENDING', 'REVIEWING', 'APPROVED', 'REJECTED', 'NEEDS_REVIEW')),
    ADD COLUMN IF NOT EXISTS government_images TEXT[],
    ADD COLUMN IF NOT EXISTS government_notes TEXT,
    ADD COLUMN IF NOT EXISTS citizen_verification_status VARCHAR(20) CHECK (citizen_verification_status IN ('PENDING', 'VERIFIED', 'NOT_VERIFIED', 'DISPUTED')),
    ADD COLUMN IF NOT EXISTS escalation_status VARCHAR(20) CHECK (escalation_status IN ('NONE', 'PENDING', 'ESCALATED', 'RESOLVED')),
    ADD COLUMN IF NOT EXISTS escalation_date TIMESTAMP,
    ADD COLUMN IF NOT EXISTS resolution_date TIMESTAMP,
    ADD COLUMN IF NOT EXISTS trust_score FLOAT DEFAULT 0.0 CHECK (trust_score >= 0 AND trust_score <= 1);

-- Create indexes for new columns
CREATE INDEX IF NOT EXISTS idx_issues_ai_verification_status ON issues(ai_verification_status);
CREATE INDEX IF NOT EXISTS idx_issues_citizen_verification_status ON issues(citizen_verification_status);
CREATE INDEX IF NOT EXISTS idx_issues_escalation_status ON issues(escalation_status);

-- ================================
-- Government Actions Log
-- ================================
CREATE TABLE IF NOT EXISTS government_actions (
    id SERIAL PRIMARY KEY,
    issue_id INTEGER NOT NULL REFERENCES issues(id) ON DELETE CASCADE,
    action_type VARCHAR(50) NOT NULL CHECK (action_type IN ('ASSIGNED', 'STARTED', 'UPDATED', 'COMPLETED', 'REJECTED')),
    department VARCHAR(100),
    assigned_to VARCHAR(255),
    notes TEXT,
    image_urls TEXT[],
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT government_actions_issue_id_idx FOREIGN KEY (issue_id) REFERENCES issues(id)
);

CREATE INDEX IF NOT EXISTS idx_government_actions_issue_id ON government_actions(issue_id);
CREATE INDEX IF NOT EXISTS idx_government_actions_action_type ON government_actions(action_type);
CREATE INDEX IF NOT EXISTS idx_government_actions_created_at ON government_actions(created_at DESC);

-- ================================
-- Notification Queue
-- ================================
CREATE TABLE IF NOT EXISTS notification_queue (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    issue_id INTEGER REFERENCES issues(id) ON DELETE CASCADE,
    notification_type VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    data JSONB DEFAULT '{}',
    status VARCHAR(20) DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'SENT', 'FAILED', 'READ')),
    sent_at TIMESTAMP,
    read_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT notification_queue_user_id_idx FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_notification_queue_user_id ON notification_queue(user_id);
CREATE INDEX IF NOT EXISTS idx_notification_queue_status ON notification_queue(status);
CREATE INDEX IF NOT EXISTS idx_notification_queue_created_at ON notification_queue(created_at DESC);

-- ================================
-- Comments
-- Update comments table to use 'content' instead of 'text'
-- ================================
DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'comments' AND column_name = 'text') THEN
        ALTER TABLE comments RENAME COLUMN text TO content;
    END IF;
END $$;

-- ================================
-- Functions and Triggers
-- ================================

-- Function to automatically create timeline event
CREATE OR REPLACE FUNCTION create_timeline_event()
RETURNS TRIGGER AS $$
BEGIN
    -- This function can be called by triggers to auto-create timeline events
    -- Implementation depends on specific trigger needs
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Function to update issue updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply updated_at trigger to escalations
DROP TRIGGER IF EXISTS update_escalations_updated_at ON escalations;
CREATE TRIGGER update_escalations_updated_at
    BEFORE UPDATE ON escalations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Apply updated_at trigger to ai_conversations
DROP TRIGGER IF EXISTS update_ai_conversations_updated_at ON ai_conversations;
CREATE TRIGGER update_ai_conversations_updated_at
    BEFORE UPDATE ON ai_conversations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ================================
-- Initial Data / Seed
-- ================================

-- Add system user for automated actions
INSERT INTO users (firebase_uid, email, name, display_name)
VALUES ('SYSTEM', 'system@civicfix.internal', 'CivicFix System', 'System')
ON CONFLICT (firebase_uid) DO NOTHING;

-- ================================
-- Grants (if needed for specific roles)
-- ================================

-- Grant permissions as needed for your application user
-- GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO your_app_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO your_app_user;

-- ================================
-- Migration Complete
-- ================================

COMMENT ON TABLE timeline_events IS 'Immutable log of all events in an issue lifecycle';
COMMENT ON TABLE ai_verifications IS 'AI verification results for issues';
COMMENT ON TABLE citizen_verifications IS 'Citizen verification of government work';
COMMENT ON TABLE escalations IS 'Escalated issues requiring higher authority intervention';
COMMENT ON TABLE ai_conversations IS 'AI assistant conversation history';
COMMENT ON TABLE government_actions IS 'Government department actions on issues';
COMMENT ON TABLE notification_queue IS 'Push notification queue for users';
