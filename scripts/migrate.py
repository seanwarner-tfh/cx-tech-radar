#!/usr/bin/env python3
"""Apply database migrations in order"""
import sqlite3
import os
import sys
from pathlib import Path

def get_migration_files(migrations_dir: str = "migrations") -> list:
    """Get sorted list of migration SQL files"""
    migrations_path = Path(migrations_dir)
    if not migrations_path.exists():
        print(f"Error: Migrations directory '{migrations_dir}' not found")
        return []
    
    migration_files = sorted(migrations_path.glob("*.sql"))
    return [str(f) for f in migration_files]

def get_applied_migrations(db_path: str) -> set:
    """Get set of already applied migrations"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create migrations tracking table if it doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version TEXT PRIMARY KEY,
            applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    
    # Get applied migrations
    cursor.execute("SELECT version FROM schema_migrations")
    applied = {row[0] for row in cursor.fetchall()}
    conn.close()
    
    return applied

def apply_migration(db_path: str, migration_file: str) -> bool:
    """Apply a single migration file"""
    migration_name = Path(migration_file).stem
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Read and execute migration SQL
        with open(migration_file, 'r') as f:
            sql = f.read()
        
        # Execute migration (may contain multiple statements)
        cursor.executescript(sql)
        
        # Record migration as applied
        cursor.execute("""
            INSERT OR IGNORE INTO schema_migrations (version) VALUES (?)
        """, (migration_name,))
        
        conn.commit()
        print(f"✅ Applied migration: {migration_name}")
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error applying migration {migration_name}: {e}")
        return False
    finally:
        conn.close()

def main():
    """Main migration runner"""
    db_path = os.getenv("DB_PATH", "data/radar.db")
    
    if not os.path.exists(db_path):
        print(f"Error: Database file '{db_path}' not found")
        sys.exit(1)
    
    migrations_dir = os.getenv("MIGRATIONS_DIR", "migrations")
    migration_files = get_migration_files(migrations_dir)
    
    if not migration_files:
        print("No migration files found")
        sys.exit(1)
    
    applied = get_applied_migrations(db_path)
    
    print(f"Found {len(migration_files)} migration(s)")
    print(f"Already applied: {len(applied)}")
    print()
    
    new_migrations = [f for f in migration_files if Path(f).stem not in applied]
    
    if not new_migrations:
        print("✅ All migrations already applied")
        return
    
    print(f"Applying {len(new_migrations)} new migration(s)...")
    print()
    
    for migration_file in new_migrations:
        if not apply_migration(db_path, migration_file):
            print(f"\n❌ Migration failed. Stopping.")
            sys.exit(1)
    
    print()
    print("✅ All migrations applied successfully!")

if __name__ == "__main__":
    main()

