"""
Example test module demonstrating the use of CommandManager.
This module shows how to create and run tests using the centralized command management.
"""

import logging
# import pytest
from typing import Dict, Any
from utils.command_manager import CommandManager
from utils.switch_api import SwitchAPI
from utils.test_helpers import (
    clear_system_messages,
    setup_test_environment,
    verify_command_response
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_vlan_creation_example(switch_api: SwitchAPI, command_manager: CommandManager) -> None:
    """Example test for VLAN creation.
    
    Args:
        switch_api: Switch API instance
        command_manager: Command manager instance
    """
    # Create VLAN 10
    vlan_cmd = command_manager.format_command('vlan_commands', 'create_vlan', vlan_id=10)
    switch_api.send_command(vlan_cmd)
    
    # Set VLAN name
    name_cmd = command_manager.format_command('vlan_commands', 'create_vlan', 
                                            vlan_id=10, vlan_name='TEST_VLAN')
    switch_api.send_command(name_cmd)
    
    # Verify VLAN creation
    show_cmd = command_manager.format_command('vlan_commands', 'show_vlan')
    response = switch_api.send_command(show_cmd)
    matches = command_manager.parse_response('vlan_commands', 'show_vlan', response)
    
    assert any('10' in match for match in matches), "VLAN 10 not found in output"

def test_mac_learning_example(switch_api: SwitchAPI, command_manager: CommandManager) -> None:
    """Example test for MAC address learning.
    
    Args:
        switch_api: Switch API instance
        command_manager: Command manager instance
    """
    # Clear MAC address table
    clear_cmd = command_manager.format_command('mac_commands', 'clear_mac_address_table')
    switch_api.send_command(clear_cmd)
    
    # Verify MAC table is empty
    show_cmd = command_manager.format_command('mac_commands', 'show_mac_address_table')
    response = switch_api.send_command(show_cmd)
    matches = command_manager.parse_response('mac_commands', 'show_mac_address_table', response)
    
    assert len(matches) == 0, "MAC address table not empty after clearing"

def test_spanning_tree_example(switch_api: SwitchAPI, command_manager: CommandManager) -> None:
    """Example test for spanning tree configuration.
    
    Args:
        switch_api: Switch API instance
        command_manager: Command manager instance
    """
    # Configure spanning tree mode
    stp_cmd = command_manager.format_command('spanning_tree_commands', 
                                           'configure_spanning_tree', mode='rapid-pvst')
    switch_api.send_command(stp_cmd)
    
    # Set root bridge priority
    priority_cmd = command_manager.format_command('spanning_tree_commands', 
                                                'configure_spanning_tree', 
                                                mode='rapid-pvst', vlan=1, priority=4096)
    switch_api.send_command(priority_cmd)
    
    # Verify spanning tree configuration
    show_cmd = command_manager.format_command('spanning_tree_commands', 
                                            'show_spanning_tree', vlan=1)
    response = switch_api.send_command(show_cmd)
    assert command_manager.verify_response('spanning_tree_commands', 
                                         'show_spanning_tree', response, vlan=1)

def run_example_tests(switch_api: SwitchAPI) -> None:
    """Run all example tests.
    
    Args:
        switch_api: Switch API instance
    """
    command_manager = CommandManager()
    
    try:
        # Set up test environment
        setup_test_environment(switch_api, command_manager)
        
        # Run example tests
        test_vlan_creation_example(switch_api, command_manager)
        test_mac_learning_example(switch_api, command_manager)
        test_spanning_tree_example(switch_api, command_manager)
        
        logger.info("All example tests completed successfully")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        raise

if __name__ == "__main__":
    # Example usage
    switch_api = SwitchAPI()  # Initialize with your connection details
    run_example_tests(switch_api) 