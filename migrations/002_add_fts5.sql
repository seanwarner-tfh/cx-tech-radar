-- Migration 002: Add FTS5 full-text search table
-- Creates FTS5 virtual table and triggers for search functionality

-- Create FTS5 table (external content table)
CREATE VIRTUAL TABLE IF NOT EXISTS tools_fts USING fts5(
    name,
    description,
    category,
    content='tools',
    content_rowid='id'
);

-- Populate FTS5 with existing data
INSERT INTO tools_fts(rowid, name, description, category)
SELECT id, name, description, category FROM tools;

-- Create triggers to keep FTS5 in sync
CREATE TRIGGER IF NOT EXISTS tools_fts_insert AFTER INSERT ON tools BEGIN
    INSERT INTO tools_fts(rowid, name, description, category)
    VALUES (new.id, new.name, new.description, new.category);
END;

CREATE TRIGGER IF NOT EXISTS tools_fts_update AFTER UPDATE ON tools BEGIN
    UPDATE tools_fts SET
        name = new.name,
        description = new.description,
        category = new.category
    WHERE rowid = new.id;
END;

CREATE TRIGGER IF NOT EXISTS tools_fts_delete AFTER DELETE ON tools BEGIN
    DELETE FROM tools_fts WHERE rowid = old.id;
END;

