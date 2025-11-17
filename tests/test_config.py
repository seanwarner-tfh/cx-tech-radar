"""Unit tests for configuration and scoring"""
import unittest
import os
import tempfile
import yaml
from src.config import load_config, compute_weighted_score, get_config


class TestConfig(unittest.TestCase):
    """Test cases for configuration and scoring"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, 'test_settings.yaml')
    
    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_load_config_defaults(self):
        """Test loading config with defaults when file doesn't exist"""
        config = load_config('nonexistent.yaml')
        
        self.assertIn('scoring', config)
        self.assertEqual(config['scoring']['cx_weight'], 0.6)
        self.assertEqual(config['scoring']['integration_weight'], 0.4)
        self.assertIn('categories', config)
        self.assertIn('positions', config)
    
    def test_load_config_from_file(self):
        """Test loading config from YAML file"""
        test_config = {
            'scoring': {
                'cx_weight': 0.7,
                'integration_weight': 0.3
            },
            'categories': ['CRM', 'Analytics'],
            'positions': ['Adopt', 'Trial']
        }
        
        with open(self.config_path, 'w') as f:
            yaml.dump(test_config, f)
        
        config = load_config(self.config_path)
        
        self.assertEqual(config['scoring']['cx_weight'], 0.7)
        self.assertEqual(config['scoring']['integration_weight'], 0.3)
        self.assertEqual(config['categories'], ['CRM', 'Analytics'])
    
    def test_load_config_normalizes_weights(self):
        """Test that weights are normalized to sum to 1.0"""
        test_config = {
            'scoring': {
                'cx_weight': 0.8,
                'integration_weight': 0.4  # Sums to 1.2, should normalize
            }
        }
        
        with open(self.config_path, 'w') as f:
            yaml.dump(test_config, f)
        
        config = load_config(self.config_path)
        
        total = config['scoring']['cx_weight'] + config['scoring']['integration_weight']
        self.assertAlmostEqual(total, 1.0, places=5)
    
    def test_compute_weighted_score_default_weights(self):
        """Test weighted score calculation with default weights"""
        cx_score = 8.0
        integration_score = 6.0
        
        # Default: 0.6 * CX + 0.4 * Integration
        expected = (0.6 * 8.0) + (0.4 * 6.0)
        result = compute_weighted_score(cx_score, integration_score)
        
        self.assertAlmostEqual(result, expected, places=2)
    
    def test_compute_weighted_score_custom_weights(self):
        """Test weighted score calculation with custom weights"""
        cx_score = 10.0
        integration_score = 5.0
        
        custom_config = {
            'scoring': {
                'cx_weight': 0.8,
                'integration_weight': 0.2
            }
        }
        
        expected = (0.8 * 10.0) + (0.2 * 5.0)
        result = compute_weighted_score(cx_score, integration_score, custom_config)
        
        self.assertAlmostEqual(result, expected, places=2)
    
    def test_compute_weighted_score_edge_cases(self):
        """Test weighted score with edge case values"""
        # Minimum scores
        result = compute_weighted_score(1.0, 1.0)
        self.assertEqual(result, 1.0)
        
        # Maximum scores
        result = compute_weighted_score(10.0, 10.0)
        self.assertEqual(result, 10.0)
        
        # Zero integration weight (should still work)
        custom_config = {
            'scoring': {
                'cx_weight': 1.0,
                'integration_weight': 0.0
            }
        }
        result = compute_weighted_score(8.0, 5.0, custom_config)
        self.assertEqual(result, 8.0)
    
    def test_get_config_singleton(self):
        """Test that get_config returns a singleton"""
        config1 = get_config()
        config2 = get_config()
        
        # Should be the same instance (or at least same values)
        self.assertEqual(config1, config2)


if __name__ == '__main__':
    unittest.main()

