-- Database initialization script for OIDC Platform
-- This script will be executed when the PostgreSQL container starts

-- Create extensions if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Set timezone
SET timezone = 'UTC';

-- Create indexes for better performance (will be created by SQLAlchemy, but good to have as backup)
-- These will be created automatically by the application, but listed here for reference

-- Sample data can be inserted here if needed
-- INSERT INTO oauth2_clients (client_id, client_secret_hash, name, redirect_uris, scopes, client_type)
-- VALUES ('sample-client', '$2b$12$...', 'Sample Client', '["http://localhost:3000/callback"]', '["openid", "profile", "email"]', 'confidential');

-- Grant necessary permissions
GRANT ALL PRIVILEGES ON DATABASE oidc_db TO oidc_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO oidc_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO oidc_user;

-- Set default privileges for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO oidc_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO oidc_user;
