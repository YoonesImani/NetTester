"""
Test module for MAC address learning functionality on L2 switches.
Tests MAC table operations and dynamic MAC learning.
"""

import logging
import time
import json
from typing import List, Tuple, Dict, Any
from utils.switch_api import SwitchAPI, MACTableError, SwitchAPIError
from config.config_manager import ConfigManager
from utils.switch_feature_checker import check_feature_support
from utils.command_manager import CommandManager
from tests.test_spanning_tree import SwitchPatternConfig
from utils.test_helpers import (
    clear_system_messages,
    setup_test_environment,
    verify_command_response
)
from tests.test_runner import run_all_tests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_mac_address(switch_api: SwitchAPI, command_manager: CommandManager,
                      mac_address: str, vlan_id: int) -> bool:
    """Verify MAC address in the table.
    
    Args:
        switch_api: Switch API instance
        command_manager: Command manager instance
        mac_address: MAC address to verify
        vlan_id: VLAN ID to check
        
    Returns:
        True if MAC address is found, False otherwise
    """
    show_cmd = command_manager.format_command('mac_commands', 'show_mac_address_table')
    response = switch_api.send_command(show_cmd)
    matches = command_manager.parse_response('mac_commands', 'show_mac_address_table', response)
    
    return any(mac_address in match and f"{vlan_id}" in match for match in matches)

def test_mac_table_clear(switch_api: SwitchAPI, command_manager: CommandManager, logger: logging.Logger) -> None:
    """Test clearing MAC address table."""
    logger.info("Starting MAC table clear test")
    try:
        # Clear MAC address table
        clear_cmd = command_manager.format_command('mac_commands', 'clear_mac_address_table')
        switch_api.send_command(clear_cmd)
        
        # Verify MAC table is empty
        show_cmd = command_manager.format_command('mac_commands', 'show_mac_address_table')
        response = switch_api.send_command(show_cmd)
        matches = command_manager.parse_response('mac_commands', 'show_mac_address_table', response)
        
        assert len(matches) == 0, "MAC address table not empty after clearing"
        logger.info("[PASS] MAC table clear test completed successfully")
        
    except Exception as e:
        logger.error(f"[FAIL] MAC table clear test failed: {str(e)}")
        raise

def test_mac_learning(switch_api: SwitchAPI, command_manager: CommandManager, logger: logging.Logger) -> None:
    """Test MAC address learning."""
    logger.info("Starting MAC learning test")
    try:
        # Configure interface for MAC learning
        interface_cmd = command_manager.format_command('interface_commands', 'configure_interface',
                                                     interface_name='FastEthernet0/1')
        switch_api.send_command(interface_cmd)
        
        # Set port mode
        mode_cmd = command_manager.format_command('interface_commands', 'configure_interface',
                                                interface_name='FastEthernet0/1',
                                                subcommand='switchport_mode_access')
        switch_api.send_command(mode_cmd)
        
        # Assign VLAN
        vlan_cmd = command_manager.format_command('interface_commands', 'configure_interface',
                                                interface_name='FastEthernet0/1',
                                                subcommand='switchport_access_vlan',
                                                vlan_id=10)
        switch_api.send_command(vlan_cmd)
        
        # Verify MAC learning
        test_mac = "00:11:22:33:44:55"
        assert verify_mac_address(switch_api, command_manager, test_mac, 10), \
            f"Failed to learn MAC address {test_mac}"
        logger.info("[PASS] MAC learning test completed successfully")
        
    except Exception as e:
        logger.error(f"[FAIL] MAC learning test failed: {str(e)}")
        raise

def test_mac_aging(switch_api: SwitchAPI, command_manager: CommandManager, logger: logging.Logger) -> None:
    """Test MAC address aging."""
    logger.info("Starting MAC aging test")
    try:
        # Configure interface
        interface_cmd = command_manager.format_command('interface_commands', 'configure_interface',
                                                     interface_name='FastEthernet0/1')
        switch_api.send_command(interface_cmd)
        
        # Set port mode
        mode_cmd = command_manager.format_command('interface_commands', 'configure_interface',
                                                interface_name='FastEthernet0/1',
                                                subcommand='switchport_mode_access')
        switch_api.send_command(mode_cmd)
        
        # Assign VLAN
        vlan_cmd = command_manager.format_command('interface_commands', 'configure_interface',
                                                interface_name='FastEthernet0/1',
                                                subcommand='switchport_access_vlan',
                                                vlan_id=10)
        switch_api.send_command(vlan_cmd)
        
        # Add test MAC address
        test_mac = "00:11:22:33:44:55"
        assert verify_mac_address(switch_api, command_manager, test_mac, 10), \
            f"Failed to learn MAC address {test_mac}"
        
        # Wait for aging
        logger.info("Waiting for MAC address to age out")
        time.sleep(300)  # 5 minutes default aging time
        
        # Verify MAC address is aged out
        show_cmd = command_manager.format_command('mac_commands', 'show_mac_address_table')
        response = switch_api.send_command(show_cmd)
        matches = command_manager.parse_response('mac_commands', 'show_mac_address_table', response)
        
        assert not any(test_mac in match for match in matches), \
            f"MAC address {test_mac} not aged out"
        logger.info("[PASS] MAC aging test completed successfully")
        
    except Exception as e:
        logger.error(f"[FAIL] MAC aging test failed: {str(e)}")
        raise

def test_mac_notification(switch: SwitchAPI, logger: logging.Logger) -> Tuple[bool, str]:
    """
    Test MAC address notification feature.
    
    Args:
        switch: Switch API instance
        logger: Logger object for test output
        
    Returns:
        Tuple[bool, str]: (success status, error message if any)
    """
    try:
        # Enable MAC notification
        logger.info("Enabling MAC notification")
        success, error = switch.enable_mac_notification()
        if not success:
            return False, f"Failed to enable MAC notification: {error}"
        
        # Wait for notifications
        logger.info("Waiting for MAC notifications...")
        time.sleep(10)  # Wait for potential notifications
        
        # Verify MAC notification status
        success, error = switch.verify_mac_notification()
        if not success:
            return False, f"MAC notification verification failed: {error}"
        
        logger.info("[PASS] MAC notification test completed successfully")
        return True, ""
        
    except Exception as e:
        return False, f"Unexpected error in MAC notification test: {str(e)}"

def test_mac_filtering(switch: SwitchAPI, logger: logging.Logger) -> Tuple[bool, str]:
    """
    Test MAC address filtering feature.
    
    Args:
        switch: Switch API instance
        logger: Logger object for test output
        
    Returns:
        Tuple[bool, str]: (success status, error message if any)
    """
    try:
        # Configure MAC filtering
        test_mac = "0000.0000.0001"
        test_vlan = "1"
        logger.info(f"Configuring MAC filtering for {test_mac} in VLAN {test_vlan}")
        success, error = switch.configure_mac_filtering(test_mac, test_vlan)
        if not success:
            return False, f"Failed to configure MAC filtering: {error}"
        
        # Verify MAC filtering configuration
        success, error = switch.verify_mac_filtering(test_mac, test_vlan)
        if not success:
            return False, f"MAC filtering verification failed: {error}"
        
        # Test filtering behavior
        logger.info("Testing MAC filtering behavior")
        success, error = switch.test_mac_filtering_behavior(test_mac, test_vlan)
        if not success:
            return False, f"MAC filtering behavior test failed: {error}"
        
        logger.info("[PASS] MAC filtering test completed successfully")
        return True, ""
        
    except Exception as e:
        return False, f"Unexpected error in MAC filtering test: {str(e)}"

def test_mac_security(switch: SwitchAPI, logger: logging.Logger) -> Tuple[bool, str]:
    """
    Test MAC address security features.
    
    Args:
        switch: Switch API instance
        logger: Logger object for test output
        
    Returns:
        Tuple[bool, str]: (success status, error message if any)
    """
    try:
        # Configure MAC security
        test_port = "Fa0/1"
        logger.info(f"Configuring MAC security on port {test_port}")
        success, error = switch.configure_mac_security(test_port)
        if not success:
            return False, f"Failed to configure MAC security: {error}"
        
        # Verify MAC security configuration
        success, error = switch.verify_mac_security(test_port)
        if not success:
            return False, f"MAC security verification failed: {error}"
        
        # Test security features
        logger.info("Testing MAC security features")
        success, error = switch.test_mac_security_features(test_port)
        if not success:
            return False, f"MAC security features test failed: {error}"
        
        logger.info("[PASS] MAC security test completed successfully")
        return True, ""
        
    except Exception as e:
        return False, f"Unexpected error in MAC security test: {str(e)}"

def run(switch_api: SwitchAPI, command_manager: CommandManager, logger: logging.Logger) -> bool:
    """Run all MAC learning tests.
    
    Args:
        switch_api: Switch API instance
        command_manager: Command manager instance
        logger: Logger instance
        
    Returns:
        bool: True if all tests passed, False otherwise
    """
    test_results = []
    
    try:
        # Set up test environment
        logger.info("Setting up test environment")
        setup_test_environment(switch_api, command_manager)
        
        # Run tests
        logger.info("Starting MAC Learning test suite")
        
        # Test MAC table clear
        try:
            test_mac_table_clear(switch_api, command_manager, logger)
            test_results.append(("MAC Table Clear", True))
        except Exception as e:
            test_results.append(("MAC Table Clear", False, str(e)))
        
        # Test MAC learning
        try:
            test_mac_learning(switch_api, command_manager, logger)
            test_results.append(("MAC Learning", True))
        except Exception as e:
            test_results.append(("MAC Learning", False, str(e)))
        
        # Test MAC aging
        try:
            test_mac_aging(switch_api, command_manager, logger)
            test_results.append(("MAC Aging", True))
        except Exception as e:
            test_results.append(("MAC Aging", False, str(e)))
        
        # Log test results
        logger.info("\nMAC Learning Test Suite Results:")
        logger.info("-" * 50)
        all_passed = True
        for test_name, *result in test_results:
            if len(result) == 1 and result[0]:  # Test passed
                logger.info(f"[PASS] {test_name}")
            else:  # Test failed
                all_passed = False
                error_msg = result[1] if len(result) > 1 else "Unknown error"
                logger.error(f"[FAIL] {test_name}: {error_msg}")
        logger.info("-" * 50)
        
        return all_passed
    
    except Exception as e:
        logger.error(f"MAC learning test suite failed: {e}")
        return False

if __name__ == "__main__":
    # Example usage
    switch_api = SwitchAPI()  # Initialize with your connection details
    run(switch_api, CommandManager(), logger) 