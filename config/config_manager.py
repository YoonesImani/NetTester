"""
Configuration manager for L2 switch testing framework.
"""

import os
import yaml
from typing import Any, Dict

class ConfigManager:
    _instance = None
    _config = None
    
    def __new__(cls):
        """Singleton pattern to ensure only one config instance exists."""
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize config manager if not already initialized."""
        if self._config is None:
            self.load_config()
    
    def load_config(self, config_path: str = None) -> None:
        """
        Load configuration from YAML file.
        
        Args:
            config_path: Optional path to config file. If None, uses default.
        """
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')
        
        try:
            with open(config_path, 'r') as f:
                self._config = yaml.safe_load(f)
        except Exception as e:
            raise Exception(f"Failed to load config from {config_path}: {str(e)}")
    
    def get(self, *keys: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation.
        
        Args:
            *keys: Configuration keys (e.g., 'switch', 'host')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        current = self._config
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        return current
    
    def get_switch_credentials(self) -> Dict[str, Any]:
        """
        Get switch connection credentials.
        
        Returns:
            Dict with host, username, password, and port
        """
        return {
            'host': self.get('switch', 'host'),
            'username': self.get('switch', 'username'),
            'password': self.get('switch', 'password'),
            'port': self.get('switch', 'port', default=22)
        }
    
    def get_test_config(self, test_name: str) -> Dict[str, Any]:
        """
        Get configuration for specific test.
        
        Args:
            test_name: Name of test (e.g., 'vlan', 'mac_learning')
            
        Returns:
            Test configuration dictionary
        """
        return self.get('test', test_name, default={}) 