"""
Context manager for switch connections.
"""

from contextlib import contextmanager
from typing import Generator
from utils.connection_manager import ConnectionManager
from utils.switch_api import SwitchAPI
from config.config_manager import ConfigManager

@contextmanager
def switch_connection(connection_type: str = None) -> Generator[SwitchAPI, None, None]:
    """
    Context manager for switch connections.
    
    Args:
        connection_type: Optional connection type override
        
    Yields:
        SwitchAPI: Configured switch API instance
        
    Example:
        with switch_connection() as switch:
            switch.send_command("show version")
    """
    config = ConfigManager()
    
    # Override connection type if specified
    if connection_type:
        config.set('switch', 'connection_type', connection_type)
    
    conn_manager = ConnectionManager(config)
    switch_api = SwitchAPI(conn_manager)
    
    try:
        yield switch_api
    finally:
        switch_api.disconnect()

@contextmanager
def connection_manager(connection_type: str = None) -> Generator[ConnectionManager, None, None]:
    """
    Context manager for connection manager.
    
    Args:
        connection_type: Optional connection type override
        
    Yields:
        ConnectionManager: Configured connection manager instance
        
    Example:
        with connection_manager() as conn_mgr:
            conn_mgr.send_command("show version")
    """
    config = ConfigManager()
    
    # Override connection type if specified
    if connection_type:
        config.set('switch', 'connection_type', connection_type)
    
    conn_manager = ConnectionManager(config)
    
    try:
        yield conn_manager
    finally:
        conn_manager.disconnect() 