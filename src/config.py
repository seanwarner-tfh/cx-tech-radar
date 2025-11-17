"""Configuration loader for CX Tech Radar"""
import yaml
import os
from typing import Dict, Any

def load_config(config_path: str = "settings.yaml") -> Dict[str, Any]:
    """Load configuration from YAML file"""
    if not os.path.exists(config_path):
        # Return defaults if file doesn't exist
        return {
            'scoring': {
                'cx_weight': 0.6,
                'integration_weight': 0.4
            },
            'categories': [
                "CRM", "Helpdesk/Support", "Analytics", "Knowledge Base",
                "Chat/Messaging", "Feedback/Survey", "Workforce Management",
                "AI/Automation", "Integration Platform", "Voice/Phone", "Other"
            ],
            'cost_bands': {
                'low': '$',
                'medium': '$$',
                'high': '$$$',
                'enterprise': '$$$$'
            },
            'positions': ['Adopt', 'Trial', 'Assess', 'Hold']
        }
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Normalize weights to sum to 1.0
    if 'scoring' in config:
        cx_w = config['scoring'].get('cx_weight', 0.6)
        int_w = config['scoring'].get('integration_weight', 0.4)
        total = cx_w + int_w
        if total > 0:
            config['scoring']['cx_weight'] = cx_w / total
            config['scoring']['integration_weight'] = int_w / total
    
    return config

# Global config instance (loaded at module level)
_config = None

def get_config() -> Dict[str, Any]:
    """Get the global config instance"""
    global _config
    if _config is None:
        _config = load_config()
    return _config

def compute_weighted_score(cx_score: float, integration_score: float, config: Dict[str, Any] = None) -> float:
    """Compute weighted overall score from CX and Integration scores"""
    if config is None:
        config = get_config()
    
    cx_weight = config['scoring']['cx_weight']
    int_weight = config['scoring']['integration_weight']
    
    return (cx_score * cx_weight) + (integration_score * int_weight)

