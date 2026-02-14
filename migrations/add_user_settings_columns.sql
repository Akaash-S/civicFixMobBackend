-- Add missing settings columns to users table
-- Run this on Render/Neon database if you get "column does not exist" errors

-- Appearance settings
ALTER TABLE users ADD COLUMN IF NOT EXISTS theme_color VARCHAR(20) DEFAULT 'blue';
ALTER TABLE users ADD COLUMN IF NOT EXISTS font_size VARCHAR(20) DEFAULT 'medium';

-- Notification settings
ALTER TABLE users ADD COLUMN IF NOT EXISTS issue_updates_notifications BOOLEAN DEFAULT TRUE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS community_activity_notifications BOOLEAN DEFAULT TRUE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS system_alerts_notifications BOOLEAN DEFAULT TRUE;

-- Media settings
ALTER TABLE users ADD COLUMN IF NOT EXISTS photo_quality VARCHAR(20) DEFAULT 'high';
ALTER TABLE users ADD COLUMN IF NOT EXISTS video_quality VARCHAR(20) DEFAULT 'high';
ALTER TABLE users ADD COLUMN IF NOT EXISTS auto_upload BOOLEAN DEFAULT FALSE;

-- Storage settings
ALTER TABLE users ADD COLUMN IF NOT EXISTS cache_auto_clear BOOLEAN DEFAULT TRUE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS backup_sync BOOLEAN DEFAULT FALSE;

-- Privacy settings
ALTER TABLE users ADD COLUMN IF NOT EXISTS location_services BOOLEAN DEFAULT TRUE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS data_collection BOOLEAN DEFAULT TRUE;

-- Accessibility settings
ALTER TABLE users ADD COLUMN IF NOT EXISTS high_contrast BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS large_text BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS voice_over BOOLEAN DEFAULT FALSE;
