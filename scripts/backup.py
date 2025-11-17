#!/usr/bin/env python3
"""Create timestamped backup of the database"""
import sqlite3
import shutil
import os
import sys
from datetime import datetime
from pathlib import Path

def create_backup(db_path: str, backups_dir: str = "data/backups") -> str:
    """Create a timestamped backup of the database"""
    if not os.path.exists(db_path):
        print(f"Error: Database file '{db_path}' not found")
        sys.exit(1)
    
    # Ensure backups directory exists
    Path(backups_dir).mkdir(parents=True, exist_ok=True)
    
    # Generate backup filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"radar_backup_{timestamp}.db"
    backup_path = os.path.join(backups_dir, backup_filename)
    
    try:
        # Use SQLite backup API for safe copying
        source = sqlite3.connect(db_path)
        backup = sqlite3.connect(backup_path)
        source.backup(backup)
        backup.close()
        source.close()
        
        # Get file size
        size_mb = os.path.getsize(backup_path) / (1024 * 1024)
        
        print(f"✅ Backup created: {backup_path}")
        print(f"   Size: {size_mb:.2f} MB")
        return backup_path
        
    except Exception as e:
        print(f"❌ Error creating backup: {e}")
        sys.exit(1)

def main():
    """Main backup function"""
    db_path = os.getenv("DB_PATH", "data/radar.db")
    backups_dir = os.getenv("BACKUPS_DIR", "data/backups")
    
    create_backup(db_path, backups_dir)

if __name__ == "__main__":
    main()

