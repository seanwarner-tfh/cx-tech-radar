-- Migration 001: Add plot_angle_offset and plot_radius_offset columns
-- These columns enable stable point placement on the radar chart
-- Note: Backfilling of values is handled by the Python code in database.py

-- Add columns if they don't exist
ALTER TABLE tools ADD COLUMN plot_angle_offset INTEGER;
ALTER TABLE tools ADD COLUMN plot_radius_offset REAL;

