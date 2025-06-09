"""
Connection manager for L2 switch testing framework.
"""

from typing import Union
from utils.serial_connection import SerialConnection
from utils.ssh_tools import SSHConnection

class ConnectionManager:
    def __init__(self, config):
        self.config = config
        self.connection_type = config.get('switch', 'connection_type', default='serial')

    def get_connection(self) -> Union[SerialConnection, SSHConnection]:
        """Get appropriate connection based on configuration."""
        if self.connection_type == 'serial':
            serial_config = self.config.get('switch', 'serial')
            return SerialConnection(**serial_config)
        elif self.connection_type == 'ssh':
            ssh_config = self.config.get('switch', 'ssh')
            return SSHConnection(**ssh_config)
        else:
            raise ValueError(f"Unsupported connection type: {self.connection_type}") 