"""
Connection factory for creating different types of switch connections.
"""

from typing import Dict, Any
from utils.connection import SwitchConnectionBase
from utils.ssh_tools import SSHConnection
from utils.telnet_connection import TelnetConnection
from utils.serial_connection import SerialConnection

class ConnectionFactory:
    """Factory for creating switch connections."""
    
    @staticmethod
    def create_connection(connection_type: str, config: Dict[str, Any]) -> SwitchConnectionBase:
        """
        Create a connection instance based on type and configuration.
        
        Args:
            connection_type: Type of connection ('ssh', 'telnet', 'serial')
            config: Configuration dictionary for the connection
            
        Returns:
            SwitchConnectionBase: Connection instance
            
        Raises:
            ValueError: If connection type is unsupported or config is invalid
        """
        if connection_type == 'ssh':
            return ConnectionFactory._create_ssh_connection(config)
        elif connection_type == 'telnet':
            return ConnectionFactory._create_telnet_connection(config)
        elif connection_type == 'serial':
            return ConnectionFactory._create_serial_connection(config)
        else:
            raise ValueError(f"Unsupported connection type: {connection_type}")
    
    @staticmethod
    def _create_ssh_connection(config: Dict[str, Any]) -> SSHConnection:
        """Create SSH connection with validation."""
        if not isinstance(config, dict):
            raise ValueError("SSH configuration must be a dictionary")
        
        required_fields = ['host', 'username', 'password']
        missing_fields = [field for field in required_fields if field not in config]
        if missing_fields:
            raise ValueError(f"Missing required SSH configuration fields: {', '.join(missing_fields)}")
        
        return SSHConnection(
            host=config['host'],
            username=config['username'],
            password=config['password'],
            port=config.get('port', 22),
            timeout=config.get('timeout', 10)
        )
    
    @staticmethod
    def _create_telnet_connection(config: Dict[str, Any]) -> TelnetConnection:
        """Create Telnet connection with validation."""
        if not isinstance(config, dict):
            raise ValueError("Telnet configuration must be a dictionary")
        
        if 'host' not in config:
            raise ValueError("Missing required telnet configuration field: host")
        
        return TelnetConnection(
            host=config['host'],
            username=config.get('username'),
            password=config.get('password'),
            port=config.get('port', 23),
            timeout=config.get('timeout', 10)
        )
    
    @staticmethod
    def _create_serial_connection(config: Dict[str, Any]) -> SerialConnection:
        """Create Serial connection with validation."""
        if not isinstance(config, dict):
            raise ValueError("Serial configuration must be a dictionary")
        
        if 'port' not in config:
            raise ValueError("Missing required serial configuration field: port")
        
        return SerialConnection(
            port=config['port'],
            baudrate=config.get('baudrate', 9600),
            timeout=config.get('timeout', 10),
            parity=config.get('parity', 'N'),
            stopbits=config.get('stopbits', 1),
            bytesize=config.get('bytesize', 8),
            xonxoff=config.get('xonxoff', False),
            rtscts=config.get('rtscts', False)
        ) 