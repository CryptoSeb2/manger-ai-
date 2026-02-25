-- Add CRM integration columns to businesses table.
-- Run this if you have an existing database created before CRM was added.
-- SQLite: ALTER TABLE ADD COLUMN (no IF NOT EXISTS for columns in older SQLite)

ALTER TABLE businesses ADD COLUMN crm_provider VARCHAR(50);
ALTER TABLE businesses ADD COLUMN crm_access_token TEXT;
