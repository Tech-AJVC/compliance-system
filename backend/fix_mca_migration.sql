-- Fix Alembic version table
DELETE FROM alembic_version WHERE version_num = '5f52e1d7d8a3';
UPDATE alembic_version SET version_num = 'cdfa556e8bc1' WHERE version_num = '224814d90ff6';

-- Add MCA to the task category constraint
ALTER TABLE compliance_tasks DROP CONSTRAINT IF EXISTS valid_category;
ALTER TABLE compliance_tasks ADD CONSTRAINT valid_category CHECK (category IN ('SEBI', 'RBI', 'IT/GST', 'LP', 'OTHER', 'MCA'));
