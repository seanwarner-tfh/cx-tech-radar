-- Migration 004: Add trigger to auto-update updated_date on row changes

CREATE TRIGGER IF NOT EXISTS tools_update_timestamp 
AFTER UPDATE ON tools
BEGIN
    UPDATE tools 
    SET updated_date = CURRENT_TIMESTAMP 
    WHERE id = new.id;
END;

