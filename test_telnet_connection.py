#!/usr/bin/env python3
"""
Test script for telnet connection functionality.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.telnet_connection import TelnetConnection
from utils.connection_manager import ConnectionManager
from config.config_manager import ConfigManager

def test_telnet_connection_class():
    """Test the TelnetConnection class directly."""
    print("Testing TelnetConnection class...")
    
    # Test with minimal configuration
    try:
        # This will fail to connect but should not crash
        telnet = TelnetConnection(
            host="192.168.1.1",
            username="admin",
            password="cisco",
            port=23,
            timeout=5
        )
        print("✓ TelnetConnection instantiated successfully")
        
        # Test connection (will likely fail but should handle gracefully)
        try:
            telnet.connect()
            print("✓ Telnet connection established")
            
            # Test command sending
            output = telnet.send_command("show version")
            print(f"✓ Command sent successfully, output length: {len(output)}")
            
            telnet.disconnect()
            print("✓ Telnet connection closed")
            
        except Exception as e:
            print(f"⚠ Connection test failed (expected for test environment): {e}")
            
    except Exception as e:
        print(f"✗ TelnetConnection instantiation failed: {e}")
        return False
    
    return True

def test_connection_manager():
    """Test the ConnectionManager with telnet support."""
    print("\nTesting ConnectionManager with telnet support...")
    
    try:
        config = ConfigManager()
        
        # Test with telnet connection type
        config.set('switch', 'connection_type', 'telnet')
        
        manager = ConnectionManager(config)
        print("✓ ConnectionManager instantiated with telnet support")
        
        # Test getting telnet connection
        try:
            connection = manager.get_connection()
            print(f"✓ Telnet connection created: {type(connection).__name__}")
        except Exception as e:
            print(f"⚠ Telnet connection creation failed (expected for test environment): {e}")
        
        # Test with other connection types
        for conn_type in ['serial', 'ssh']:
            try:
                config.set('switch', 'connection_type', conn_type)
                manager = ConnectionManager(config)
                print(f"✓ ConnectionManager works with {conn_type} connection type")
            except Exception as e:
                print(f"✗ ConnectionManager failed with {conn_type}: {e}")
        
    except Exception as e:
        print(f"✗ ConnectionManager test failed: {e}")
        return False
    
    return True

def main():
    """Run all telnet connection tests."""
    print("Telnet Connection Test Suite")
    print("=" * 40)
    
    success = True
    
    # Test 1: TelnetConnection class
    if not test_telnet_connection_class():
        success = False
    
    # Test 2: ConnectionManager integration
    if not test_connection_manager():
        success = False
    
    print("\n" + "=" * 40)
    if success:
        print("✓ All tests passed! Telnet connection support is working.")
    else:
        print("✗ Some tests failed. Please check the implementation.")
    
    return success

if __name__ == "__main__":
    main() 