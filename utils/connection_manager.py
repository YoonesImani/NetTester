"""
Connection manager for L2 switch testing framework.
"""

from typing import Optional
from utils.connection import SwitchConnectionBase
from utils.connection_factory import ConnectionFactory
from config.config_manager import ConfigManager

class ConnectionManager:
    """Manages switch connections with support for multiple connection types."""
    
    def __init__(self, config: ConfigManager):
        """
        Initialize ConnectionManager with configuration.
        
        Args:
            config: Configuration manager instance
        """
        self.config = config
        self.connection_type = config.get('switch', 'connection_type', default='ssh')
        self._connection: Optional[SwitchConnectionBase] = None
    
    def get_connection(self, auto_connect: bool = True) -> SwitchConnectionBase:
        """
        Get appropriate connection based on configuration.
        
        Args:
            auto_connect: Whether to automatically connect the instance
            
        Returns:
            SwitchConnectionBase: Connection instance
            
        Raises:
            ValueError: If connection type is unsupported
        """
        if self._connection and self._connection.is_connected():
            return self._connection
        
        # Get configuration for the connection type
        config_section = self.config.get('switch', self.connection_type)
        if not isinstance(config_section, dict):
            raise ValueError(f"{self.connection_type.capitalize()} configuration must be a dictionary")
        
        # Create connection using factory
        self._connection = ConnectionFactory.create_connection(self.connection_type, config_section)
        
        if auto_connect:
            self._connection.connect()
            
        return self._connection
    
    def connect(self) -> None:
        """Connect to the switch if not already connected."""
        if not self._connection or not self._connection.is_connected():
            self.get_connection(auto_connect=True)
    
    def disconnect(self) -> None:
        """Disconnect from the switch."""
        if self._connection:
            self._connection.disconnect()
            self._connection = None
    
    def is_connected(self) -> bool:
        """Check if currently connected to switch."""
        return self._connection is not None and self._connection.is_connected()
    
    def send_command(self, command: str, wait_time: float = 1) -> str:
        """
        Send command to switch.
        
        Args:
            command: Command to send
            wait_time: Time to wait for output
            
        Returns:
            str: Command output
        """
        if not self.is_connected():
            self.connect()
        return self._connection.send_command(command, wait_time) 