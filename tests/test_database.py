"""Unit tests for database operations"""
import unittest
import os
import tempfile
import sqlite3
from src.database import TechRadarDB
import json


class TestTechRadarDB(unittest.TestCase):
    """Test cases for TechRadarDB class"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create a temporary database for testing
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db_path = self.temp_db.name
        self.db = TechRadarDB(db_path=self.db_path)
    
    def tearDown(self):
        """Clean up test fixtures"""
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)
    
    def test_init_db_creates_tables(self):
        """Test that database initialization creates required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check that tools table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='tools'
        """)
        self.assertIsNotNone(cursor.fetchone())
        
        # Check that required columns exist
        cursor.execute("PRAGMA table_info(tools)")
        columns = [row[1] for row in cursor.fetchall()]
        self.assertIn('name', columns)
        self.assertIn('category', columns)
        self.assertIn('cx_relevance_score', columns)
        self.assertIn('plot_angle_offset', columns)
        self.assertIn('plot_radius_offset', columns)
        
        conn.close()
    
    def test_add_tool_success(self):
        """Test adding a tool successfully"""
        tool_data = {
            'name': 'Test Tool',
            'description': 'A test tool',
            'category': 'CRM',
            'radar_position': 'Trial',
            'cx_relevance_score': 8,
            'integration_score': 7,
            'overall_score': 7.5,
            'cost_rating': '$$',
            'pricing_model': 'Per seat',
            'key_features': ['Feature 1', 'Feature 2'],
            'use_cases': ['Use case 1'],
            'integrations': ['Integration 1'],
            'source_url': 'https://example.com',
            'reasoning': 'Test reasoning'
        }
        
        result = self.db.add_tool(tool_data)
        self.assertGreater(result, 0)
        
        # Verify tool was added
        tools = self.db.get_all_tools()
        self.assertEqual(len(tools), 1)
        self.assertEqual(tools.iloc[0]['name'], 'Test Tool')
        self.assertIsNotNone(tools.iloc[0]['plot_angle_offset'])
        self.assertIsNotNone(tools.iloc[0]['plot_radius_offset'])
    
    def test_add_tool_duplicate(self):
        """Test that adding duplicate tool returns -1"""
        tool_data = {
            'name': 'Duplicate Tool',
            'description': 'Test',
            'category': 'CRM'
        }
        
        result1 = self.db.add_tool(tool_data)
        self.assertGreater(result1, 0)
        
        result2 = self.db.add_tool(tool_data)
        self.assertEqual(result2, -1)
    
    def test_add_tool_computes_offsets(self):
        """Test that offsets are computed when not provided"""
        tool_data = {
            'name': 'Offset Test Tool',
            'description': 'Test',
            'category': 'CRM'
        }
        
        result = self.db.add_tool(tool_data)
        self.assertGreater(result, 0)
        
        tools = self.db.get_all_tools()
        tool = tools.iloc[0]
        
        # Check offsets are in valid ranges
        self.assertGreaterEqual(tool['plot_angle_offset'], -20)
        self.assertLessEqual(tool['plot_angle_offset'], 20)
        self.assertGreaterEqual(tool['plot_radius_offset'], 0.0)
        self.assertLessEqual(tool['plot_radius_offset'], 0.29)
    
    def test_get_all_tools_empty(self):
        """Test getting all tools when database is empty"""
        tools = self.db.get_all_tools()
        self.assertTrue(tools.empty)
    
    def test_get_all_tools_with_filters(self):
        """Test filtering tools"""
        # Add multiple tools
        tools_data = [
            {
                'name': 'Tool 1',
                'category': 'CRM',
                'radar_position': 'Adopt',
                'cx_relevance_score': 9,
                'integration_score': 8
            },
            {
                'name': 'Tool 2',
                'category': 'Analytics',
                'radar_position': 'Trial',
                'cx_relevance_score': 6,
                'integration_score': 7
            },
            {
                'name': 'Tool 3',
                'category': 'CRM',
                'radar_position': 'Assess',
                'cx_relevance_score': 5,
                'integration_score': 4
            }
        ]
        
        for tool_data in tools_data:
            self.db.add_tool(tool_data)
        
        # Test category filter
        filtered = self.db.get_all_tools(filters={'category': 'CRM'})
        self.assertEqual(len(filtered), 2)
        
        # Test position filter
        filtered = self.db.get_all_tools(filters={'position': 'Adopt'})
        self.assertEqual(len(filtered), 1)
        
        # Test score filters
        filtered = self.db.get_all_tools(filters={'min_cx_score': 7})
        self.assertEqual(len(filtered), 1)
        
        filtered = self.db.get_all_tools(filters={'max_cx_score': 6})
        self.assertEqual(len(filtered), 2)
    
    def test_search_tools_like_fallback(self):
        """Test search functionality with LIKE fallback"""
        tool_data = {
            'name': 'Searchable Tool',
            'description': 'This is a searchable description',
            'category': 'CRM'
        }
        self.db.add_tool(tool_data)
        
        # Test search by name
        results = self.db.search_tools('Searchable')
        self.assertEqual(len(results), 1)
        
        # Test search by description
        results = self.db.search_tools('searchable description')
        self.assertEqual(len(results), 1)
        
        # Test search by category
        results = self.db.search_tools('CRM')
        self.assertEqual(len(results), 1)
        
        # Test no results
        results = self.db.search_tools('Nonexistent')
        self.assertTrue(results.empty)
    
    def test_get_stats(self):
        """Test statistics retrieval"""
        # Add tools with different positions
        tools_data = [
            {'name': 'Tool 1', 'radar_position': 'Adopt', 'category': 'CRM'},
            {'name': 'Tool 2', 'radar_position': 'Trial', 'category': 'Analytics'},
            {'name': 'Tool 3', 'radar_position': 'Adopt', 'category': 'CRM'}
        ]
        
        for tool_data in tools_data:
            self.db.add_tool(tool_data)
        
        stats = self.db.get_stats()
        
        self.assertEqual(stats['total_tools'], 3)
        self.assertEqual(stats['by_position']['Adopt'], 2)
        self.assertEqual(stats['by_position']['Trial'], 1)
        self.assertEqual(stats['by_category']['CRM'], 2)
        self.assertEqual(stats['by_category']['Analytics'], 1)
    
    def test_stable_offsets_deterministic(self):
        """Test that offsets are deterministic for the same name"""
        tool_name = 'Deterministic Test Tool'
        
        offset1 = self.db._compute_stable_offsets(tool_name)
        offset2 = self.db._compute_stable_offsets(tool_name)
        
        self.assertEqual(offset1, offset2)
        
        # Test offsets are in valid ranges
        angle_offset, radius_offset = offset1
        self.assertGreaterEqual(angle_offset, -20)
        self.assertLessEqual(angle_offset, 20)
        self.assertGreaterEqual(radius_offset, 0.0)
        self.assertLessEqual(radius_offset, 0.29)


if __name__ == '__main__':
    unittest.main()

