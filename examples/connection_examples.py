"""
Examples demonstrating different connection usage patterns.
"""

from utils.connection_context import switch_connection, connection_manager
from utils.connection_manager import ConnectionManager
from utils.switch_api import SwitchAPI
from config.config_manager import ConfigManager

def example_context_manager():
    """Example using context manager (recommended approach)."""
    print("=== Context Manager Example ===")
    
    # Simple usage with automatic cleanup
    with switch_connection() as switch:
        result = switch.send_command("show version")
        print(f"Switch version: {result[:100]}...")
    
    print("Connection automatically closed!")

def example_connection_manager_direct():
    """Example using ConnectionManager directly."""
    print("\n=== Connection Manager Direct Example ===")
    
    config = ConfigManager()
    conn_mgr = ConnectionManager(config)
    
    try:
        # Send command directly through connection manager
        result = conn_mgr.send_command("show interfaces brief")
        print(f"Interfaces: {result[:100]}...")
    finally:
        conn_mgr.disconnect()
        print("Connection manually closed!")

def example_switch_api():
    """Example using SwitchAPI with ConnectionManager."""
    print("\n=== Switch API Example ===")
    
    config = ConfigManager()
    conn_mgr = ConnectionManager(config)
    switch_api = SwitchAPI(conn_mgr)
    
    try:
        # Use SwitchAPI methods
        result = switch_api.send_command("show vlan brief")
        print(f"VLANs: {result[:100]}...")
        
        # You can also use SwitchAPI's higher-level methods
        # success, message = switch_api.create_vlan("100", "TEST_VLAN")
        # print(f"VLAN creation: {success}, {message}")
        
    finally:
        switch_api.disconnect()
        print("Switch API connection closed!")

def example_connection_type_override():
    """Example showing how to override connection type."""
    print("\n=== Connection Type Override Example ===")
    
    # Override to use telnet instead of default
    with switch_connection(connection_type='telnet') as switch:
        result = switch.send_command("show version")
        print(f"Telnet connection result: {result[:100]}...")

def example_connection_manager_context():
    """Example using connection_manager context manager."""
    print("\n=== Connection Manager Context Example ===")
    
    with connection_manager() as conn_mgr:
        result = conn_mgr.send_command("show running-config")
        print(f"Running config: {result[:100]}...")

if __name__ == "__main__":
    # Run all examples
    example_context_manager()
    example_connection_manager_direct()
    example_switch_api()
    example_connection_type_override()
    example_connection_manager_context()
    
    print("\n=== All examples completed! ===") 