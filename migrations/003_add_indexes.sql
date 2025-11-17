-- Migration 003: Add indexes for better query performance

CREATE INDEX IF NOT EXISTS idx_tools_category ON tools(category);
CREATE INDEX IF NOT EXISTS idx_tools_position ON tools(radar_position);
CREATE INDEX IF NOT EXISTS idx_tools_status ON tools(status);
CREATE INDEX IF NOT EXISTS idx_tools_cx_score ON tools(cx_relevance_score);
CREATE INDEX IF NOT EXISTS idx_tools_integration_score ON tools(integration_score);

