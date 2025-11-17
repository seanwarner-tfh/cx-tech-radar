import sqlite3
import json
from typing import Dict, Optional
import pandas as pd
import hashlib

class TechRadarDB:
    def __init__(self, db_path: str = "data/radar.db"):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """Initialize the database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tools (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                category TEXT,
                radar_position TEXT,
                cx_relevance_score INTEGER,
                integration_score INTEGER,
                overall_score REAL,
                cost_rating TEXT,
                pricing_model TEXT,
                key_features TEXT,
                use_cases TEXT,
                integrations TEXT,
                source_url TEXT,
                reasoning TEXT,
                status TEXT DEFAULT 'active',
                added_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                plot_angle_offset INTEGER,
                plot_radius_offset REAL
            )
        """)
        
        # Add new columns if they don't exist (for existing databases)
        try:
            cursor.execute("ALTER TABLE tools ADD COLUMN plot_angle_offset INTEGER")
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        try:
            cursor.execute("ALTER TABLE tools ADD COLUMN plot_radius_offset REAL")
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        # Create FTS5 table for full-text search (external content table)
        # Check if FTS5 is available
        try:
            cursor.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS tools_fts USING fts5(
                    name,
                    description,
                    category,
                    content='tools',
                    content_rowid='id'
                )
            """)
            
            # Create triggers to keep FTS5 in sync
            # Insert trigger
            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS tools_fts_insert AFTER INSERT ON tools BEGIN
                    INSERT INTO tools_fts(rowid, name, description, category)
                    VALUES (new.id, new.name, new.description, new.category);
                END
            """)
            
            # Update trigger
            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS tools_fts_update AFTER UPDATE ON tools BEGIN
                    UPDATE tools_fts SET
                        name = new.name,
                        description = new.description,
                        category = new.category
                    WHERE rowid = new.id;
                END
            """)
            
            # Delete trigger
            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS tools_fts_delete AFTER DELETE ON tools BEGIN
                    DELETE FROM tools_fts WHERE rowid = old.id;
                END
            """)
            
            # Populate FTS5 table with existing data if empty
            cursor.execute("SELECT COUNT(*) FROM tools_fts")
            if cursor.fetchone()[0] == 0:
                cursor.execute("""
                    INSERT INTO tools_fts(rowid, name, description, category)
                    SELECT id, name, description, category FROM tools
                """)
            
            self.fts5_available = True
        except sqlite3.OperationalError as e:
            # FTS5 not available, fall back to LIKE search
            self.fts5_available = False
        
        conn.commit()
        conn.close()
    
    def _compute_stable_offsets(self, name: str) -> tuple:
        """Compute stable angle and radius offsets from tool name hash
        Uses MD5 for deterministic hashing across Python versions"""
        # Use MD5 for deterministic hash (stable across Python versions)
        name_hash = int(hashlib.md5(name.encode('utf-8')).hexdigest(), 16)
        # Angle offset: -20 to 20 degrees
        angle_offset = (name_hash % 41) - 20
        # Radius offset: 0.00 to 0.29
        radius_offset = (name_hash % 30) / 100.0
        return angle_offset, radius_offset
    
    def add_tool(self, tool_data: Dict) -> int:
        """Add a new tool to the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Compute stable offsets if not provided
        if 'plot_angle_offset' not in tool_data or tool_data.get('plot_angle_offset') is None:
            angle_offset, radius_offset = self._compute_stable_offsets(tool_data['name'])
            tool_data['plot_angle_offset'] = angle_offset
            tool_data['plot_radius_offset'] = radius_offset
        
        try:
            cursor.execute("""
                INSERT INTO tools (
                    name, description, category, radar_position,
                    cx_relevance_score, integration_score, overall_score,
                    cost_rating, pricing_model, key_features, use_cases,
                    integrations, source_url, reasoning,
                    plot_angle_offset, plot_radius_offset
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                tool_data['name'],
                tool_data.get('description', ''),
                tool_data.get('category', ''),
                tool_data.get('radar_position', 'Assess'),
                tool_data.get('cx_relevance_score', 5),
                tool_data.get('integration_score', 5),
                tool_data.get('overall_score', 5.0),
                tool_data.get('cost_rating', '$$'),
                tool_data.get('pricing_model', ''),
                json.dumps(tool_data.get('key_features', [])),
                json.dumps(tool_data.get('use_cases', [])),
                json.dumps(tool_data.get('integrations', [])),
                tool_data.get('source_url', ''),
                tool_data.get('reasoning', ''),
                tool_data.get('plot_angle_offset'),
                tool_data.get('plot_radius_offset')
            ))
            
            tool_id = cursor.lastrowid
            conn.commit()
            return tool_id
            
        except sqlite3.IntegrityError:
            return -1
        finally:
            conn.close()
    
    def get_all_tools(self, filters: Optional[Dict] = None) -> pd.DataFrame:
        """Get all tools as a pandas DataFrame, optionally filtered"""
        conn = sqlite3.connect(self.db_path)
        
        query = "SELECT * FROM tools WHERE status = 'active'"
        params = []
        
        if filters:
            conditions = []
            if filters.get('category'):
                conditions.append("category = ?")
                params.append(filters['category'])
            if filters.get('position'):
                conditions.append("radar_position = ?")
                params.append(filters['position'])
            if filters.get('min_cx_score') is not None:
                conditions.append("cx_relevance_score >= ?")
                params.append(filters['min_cx_score'])
            if filters.get('max_cx_score') is not None:
                conditions.append("cx_relevance_score <= ?")
                params.append(filters['max_cx_score'])
            if filters.get('min_integration_score') is not None:
                conditions.append("integration_score >= ?")
                params.append(filters['min_integration_score'])
            if filters.get('max_integration_score') is not None:
                conditions.append("integration_score <= ?")
                params.append(filters['max_integration_score'])
            
            if conditions:
                query += " AND " + " AND ".join(conditions)
        
        df = pd.read_sql_query(query, conn, params=params if params else None)
        conn.close()
        
        # Backfill missing offsets for existing tools
        if not df.empty:
            missing_offsets = df['plot_angle_offset'].isna() | df['plot_radius_offset'].isna()
            if missing_offsets.any():
                for idx, row in df[missing_offsets].iterrows():
                    angle_offset, radius_offset = self._compute_stable_offsets(row['name'])
                    df.at[idx, 'plot_angle_offset'] = angle_offset
                    df.at[idx, 'plot_radius_offset'] = radius_offset
                    # Optionally update DB (but don't block on it)
                    try:
                        conn = sqlite3.connect(self.db_path)
                        cursor = conn.cursor()
                        cursor.execute("""
                            UPDATE tools 
                            SET plot_angle_offset = ?, plot_radius_offset = ?
                            WHERE id = ?
                        """, (angle_offset, radius_offset, row['id']))
                        conn.commit()
                        conn.close()
                    except (sqlite3.Error, Exception) as e:
                        # Non-critical, continue - offsets are computed on-the-fly anyway
                        pass
        
        if not df.empty:
            df['key_features'] = df['key_features'].apply(
                lambda x: json.loads(x) if x else []
            )
            df['use_cases'] = df['use_cases'].apply(
                lambda x: json.loads(x) if x else []
            )
        
        return df
    
    def search_tools(self, query: str) -> pd.DataFrame:
        """Search tools using FTS5 if available, otherwise fallback to LIKE"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if FTS5 is available (re-check in case it wasn't initialized)
        try:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tools_fts'")
            fts5_available = cursor.fetchone() is not None
        except sqlite3.Error:
            fts5_available = False
        
        if fts5_available:
            # Use FTS5 with ranking
            # Escape special FTS5 characters and build query
            # FTS5 special chars: ", ', \, and operators like AND, OR, NOT
            fts_query = query.replace('"', '""').replace("'", "''")
            # Wrap in quotes for phrase search, or use simple token search
            fts_query = f'"{fts_query}"' if ' ' in fts_query else fts_query
            try:
                df = pd.read_sql_query("""
                    SELECT t.*, 
                           bm25(tools_fts) AS rank
                    FROM tools t
                    JOIN tools_fts ON tools_fts.rowid = t.id
                    WHERE t.status = 'active'
                    AND tools_fts MATCH ?
                    ORDER BY rank
                """, conn, params=(fts_query,))
            except sqlite3.OperationalError:
                # If FTS5 query fails, fall back to LIKE
                fts5_available = False
        
        if not fts5_available:
            # Fallback to LIKE search
            like_pattern = f'%{query}%'
            df = pd.read_sql_query("""
                SELECT * FROM tools 
                WHERE status = 'active' 
                AND (name LIKE ? OR description LIKE ? OR category LIKE ?)
                ORDER BY name
            """, conn, params=(like_pattern, like_pattern, like_pattern))
        
        conn.close()
        
        return df
    
    def get_stats(self) -> Dict:
        """Get database statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM tools WHERE status = 'active'")
        total_tools = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT radar_position, COUNT(*) 
            FROM tools 
            WHERE status = 'active' 
            GROUP BY radar_position
        """)
        by_position = dict(cursor.fetchall())
        
        cursor.execute("""
            SELECT category, COUNT(*) 
            FROM tools 
            WHERE status = 'active' 
            GROUP BY category
        """)
        by_category = dict(cursor.fetchall())
        
        conn.close()
        
        return {
            'total_tools': total_tools,
            'by_position': by_position,
            'by_category': by_category
        }