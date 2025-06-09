"""
VLAN testing module for L2 switch testing framework.
"""

import logging
import time
import json
from typing import List, Tuple, Dict, Any
from utils.switch_api import SwitchAPI, VLANOperationError, SwitchAPIError
from utils.switch_feature_checker import check_feature_support
from utils.command_manager import CommandManager
from tests.test_spanning_tree import SwitchPatternConfig
from utils.test_helpers import (
    clear_system_messages,
    setup_test_environment,
    verify_command_response
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_vlan_creation(switch_api: SwitchAPI, command_manager: CommandManager,
                        vlan_id: int, vlan_name: str) -> bool:
    """Verify VLAN creation.
    
    Args:
        switch_api: Switch API instance
        command_manager: Command manager instance
        vlan_id: VLAN ID to verify
        vlan_name: Expected VLAN name
        
    Returns:
        True if VLAN exists with correct name, False otherwise
    """
    show_cmd = command_manager.format_command('vlan_commands', 'show_vlan')
    response = switch_api.send_command(show_cmd)
    matches = command_manager.parse_response('vlan_commands', 'show_vlan', response)
    
    return any(f"{vlan_id}" in match and vlan_name in match for match in matches)

def verify_vlan_deletion(switch_api: SwitchAPI, command_manager: CommandManager,
                        vlan_id: int) -> bool:
    """Verify VLAN deletion.
    
    Args:
        switch_api: Switch API instance
        command_manager: Command manager instance
        vlan_id: VLAN ID to verify
        
    Returns:
        True if VLAN does not exist, False otherwise
    """
    show_cmd = command_manager.format_command('vlan_commands', 'show_vlan')
    response = switch_api.send_command(show_cmd)
    matches = command_manager.parse_response('vlan_commands', 'show_vlan', response)
    
    return not any(f"{vlan_id}" in match for match in matches)

def verify_port_vlan_assignment(switch_api: SwitchAPI, command_manager: CommandManager,
                              interface: str, vlan_id: int) -> bool:
    """Verify port VLAN assignment.
    
    Args:
        switch_api: Switch API instance
        command_manager: Command manager instance
        interface: Interface to verify
        vlan_id: Expected VLAN ID
        
    Returns:
        True if port is assigned to correct VLAN, False otherwise
    """
    show_cmd = command_manager.format_command('vlan_commands', 'show_vlan')
    response = switch_api.send_command(show_cmd)
    matches = command_manager.parse_response('vlan_commands', 'show_vlan', response)
    
    return any(f"{vlan_id}" in match and interface in match for match in matches)

def test_vlan_creation(switch_api: SwitchAPI, command_manager: CommandManager, logger: logging.Logger) -> None:
    """Test VLAN creation functionality"""
    logger.info("Starting VLAN creation test")
    try:
        # Create a new VLAN
        vlan_id = 100
        vlan_name = "test_vlan"
        
        logger.debug(f"Creating VLAN {vlan_id} with name {vlan_name}")
        success, error = switch_api.create_vlan(str(vlan_id), vlan_name)
        assert success, f"Failed to create VLAN {vlan_id}: {error}"
        logger.debug(f"Successfully created VLAN {vlan_id}")
        
        # Verify VLAN creation
        logger.debug("Verifying VLAN creation")
        show_cmd = command_manager.format_command('vlan_commands', 'show_vlan')
        vlan_info = switch_api.send_command(show_cmd)
        assert str(vlan_id) in vlan_info, f"VLAN {vlan_id} not found in show vlan output"
        assert vlan_name in vlan_info, f"VLAN name {vlan_name} not found in show vlan output"
        logger.info("[PASS] VLAN creation test completed successfully")
        
    except Exception as e:
        logger.error(f"[FAIL] VLAN creation test failed: {str(e)}")
        raise

def test_vlan_deletion(switch_api: SwitchAPI, command_manager: CommandManager, logger: logging.Logger) -> None:
    """Test VLAN deletion functionality"""
    logger.info("Starting VLAN deletion test")
    try:
        # Create a VLAN first
        vlan_id = 200
        vlan_name = "temp_vlan"
        
        logger.debug(f"Creating temporary VLAN {vlan_id}")
        success, error = switch_api.create_vlan(str(vlan_id), vlan_name)
        assert success, f"Failed to create temporary VLAN {vlan_id}: {error}"
        
        # Delete the VLAN
        logger.debug(f"Deleting VLAN {vlan_id}")
        success, error = switch_api.delete_vlan(str(vlan_id))
        assert success, f"Failed to delete VLAN {vlan_id}: {error}"
        
        # Verify deletion
        logger.debug("Verifying VLAN deletion")
        show_cmd = command_manager.format_command('vlan_commands', 'show_vlan')
        vlan_info = switch_api.send_command(show_cmd)
        assert str(vlan_id) not in vlan_info, f"VLAN {vlan_id} still exists after deletion"
        logger.info("[PASS] VLAN deletion test completed successfully")
        
    except Exception as e:
        logger.error(f"[FAIL] VLAN deletion test failed: {str(e)}")
        raise

def test_vlan_port_assignment(switch_api: SwitchAPI, command_manager: CommandManager, logger: logging.Logger) -> None:
    """Test VLAN port assignment functionality"""
    logger.info("Starting VLAN port assignment test")
    try:
        # Create a VLAN
        vlan_id = 300
        vlan_name = "port_vlan"
        interface = "GigabitEthernet1/0/1"
        
        logger.debug(f"Creating VLAN {vlan_id} for port assignment")
        success, error = switch_api.create_vlan(str(vlan_id), vlan_name)
        assert success, f"Failed to create VLAN {vlan_id}: {error}"
        
        # Configure interface
        logger.debug(f"Configuring interface {interface}")
        interface_cmd = command_manager.format_command('vlan_commands', 'configure_interface', interface=interface)
        success, error = switch_api.configure_interface(interface)
        assert success, f"Failed to configure interface {interface}: {error}"
        
        # Set port mode and assign VLAN
        logger.debug(f"Setting port mode and assigning VLAN {vlan_id} to {interface}")
        mode_cmd = command_manager.format_command('vlan_commands', 'configure_interface', 
                                                interface=interface,
                                                subcommand='switchport_mode',
                                                mode='access')
        response = switch_api.send_command(mode_cmd)
        assert "Invalid input" not in response, f"Failed to set port mode: {response}"
        
        vlan_cmd = command_manager.format_command('vlan_commands', 'configure_interface',
                                                interface=interface,
                                                subcommand='switchport_access_vlan',
                                                vlan_id=vlan_id)
        response = switch_api.send_command(vlan_cmd)
        assert "Invalid input" not in response, f"Failed to assign VLAN {vlan_id} to port: {response}"
        
        # Verify port assignment
        logger.debug("Verifying port assignment")
        show_cmd = command_manager.format_command('vlan_commands', 'show_interface_switchport', interface=interface)
        port_info = switch_api.send_command(show_cmd)
        assert str(vlan_id) in port_info, f"VLAN {vlan_id} not found in port configuration"
        logger.info("[PASS] VLAN port assignment test completed successfully")
        
    except Exception as e:
        logger.error(f"[FAIL] VLAN port assignment test failed: {str(e)}")
        raise

def test_vlan_trunk_configuration(switch_api: SwitchAPI, command_manager: CommandManager) -> None:
    """Test VLAN trunk configuration."""
    logger.info("Starting VLAN trunk configuration test")
    try:
        # Configure trunk port
        success, error = switch_api.configure_trunk_port(
            port="FastEthernet0/24",
            native_vlan="1",
            allowed_vlans="1,10,20,30"
        )
        if not success:
            raise VLANOperationError(f"Failed to configure trunk port: {error}")
        
        # Verify trunk configuration
        success, error = switch_api.verify_trunk_configuration(
            port="FastEthernet0/24",
            native_vlan="1",
            allowed_vlans="1,10,20,30"
        )
        if not success:
            raise VLANOperationError(f"Failed to verify trunk configuration: {error}")
        logger.info("[PASS] VLAN trunk configuration test completed successfully")
        
    except Exception as e:
        logger.error(f"[FAIL] VLAN trunk configuration test failed: {str(e)}")
        raise

def test_vlan_interface(switch_api: SwitchAPI, command_manager: CommandManager) -> None:
    """Test VLAN interface configuration."""
    logger.info("Starting VLAN interface test")
    try:
        # Create VLAN
        success, error = switch_api.create_vlan("40", "SVI_TEST")
        if not success:
            raise VLANOperationError(f"Failed to create VLAN for SVI test: {error}")
        
        # Configure SVI
        success, error = switch_api.configure_svi(
            vlan_id="40",
            ip_address="192.168.40.1",
            subnet_mask="255.255.255.0",
            description="Test SVI"
        )
        if not success:
            raise VLANOperationError(f"Failed to configure SVI: {error}")
        
        # Verify SVI configuration
        success, error = switch_api.verify_svi_configuration(
            vlan_id="40",
            ip_address="192.168.40.1",
            subnet_mask="255.255.255.0"
        )
        if not success:
            raise VLANOperationError(f"Failed to verify SVI configuration: {error}")
        logger.info("[PASS] VLAN interface test completed successfully")
        
    except Exception as e:
        logger.error(f"[FAIL] VLAN interface test failed: {str(e)}")
        raise

def test_voice_vlan(switch_api: SwitchAPI, command_manager: CommandManager) -> None:
    """Test voice VLAN configuration."""
    logger.info("Starting voice VLAN test")
    try:
        # Create VLANs
        success, error = switch_api.create_vlan("50", "VOICE_VLAN")
        if not success:
            raise VLANOperationError(f"Failed to create voice VLAN: {error}")
        
        success, error = switch_api.create_vlan("60", "DATA_VLAN")
        if not success:
            raise VLANOperationError(f"Failed to create data VLAN: {error}")
        
        # Configure voice VLAN
        success, error = switch_api.configure_voice_vlan(
            port="FastEthernet0/1",
            voice_vlan="50",
            data_vlan="60"
        )
        if not success:
            raise VLANOperationError(f"Failed to configure voice VLAN: {error}")
        
        # Verify voice VLAN configuration
        success, error = switch_api.verify_voice_vlan_configuration(
            port="FastEthernet0/1",
            voice_vlan="50",
            data_vlan="60"
        )
        if not success:
            raise VLANOperationError(f"Failed to verify voice VLAN configuration: {error}")
        logger.info("[PASS] Voice VLAN test completed successfully")
        
    except Exception as e:
        logger.error(f"[FAIL] Voice VLAN test failed: {str(e)}")
        raise

def test_private_vlan(switch_api: SwitchAPI, command_manager: CommandManager) -> None:
    """Test private VLAN configuration."""
    logger.info("Starting private VLAN test")
    try:
        # Configure private VLANs
        success, error = switch_api.configure_private_vlan(
            primary_vlan="100",
            isolated_vlan="101",
            community_vlan="102"
        )
        if not success:
            raise VLANOperationError(f"Failed to configure private VLANs: {error}")
        
        # Verify private VLAN configuration
        success, error = switch_api.verify_private_vlan_configuration(
            primary_vlan="100",
            isolated_vlan="101",
            community_vlan="102"
        )
        if not success:
            raise VLANOperationError(f"Failed to verify private VLAN configuration: {error}")
        logger.info("[PASS] Private VLAN test completed successfully")
        
    except Exception as e:
        logger.error(f"[FAIL] Private VLAN test failed: {str(e)}")
        raise

def test_vlan_acl(switch_api: SwitchAPI, command_manager: CommandManager) -> None:
    """Test VLAN ACL configuration."""
    logger.info("Starting VLAN ACL test")
    try:
    # Create VLAN
        success, error = switch_api.create_vlan("70", "ACL_TEST")
        if not success:
            raise VLANOperationError(f"Failed to create VLAN for ACL test: {error}")
        
        # Configure VLAN access-map
        success, error = switch_api.configure_vlan_access_map(
            map_name="VLAN_ACL",
            sequence="10",
            action="permit",
            acl_name="VLAN_ACL_LIST"
        )
        if not success:
            raise VLANOperationError(f"Failed to configure VLAN access-map: {error}")
        
        # Apply VLAN access-map
        success, error = switch_api.apply_vlan_access_map(
            vlan_id="70",
            map_name="VLAN_ACL"
        )
        if not success:
            raise VLANOperationError(f"Failed to apply VLAN access-map: {error}")
        logger.info("[PASS] VLAN ACL test completed successfully")
        
    except Exception as e:
        logger.error(f"[FAIL] VLAN ACL test failed: {str(e)}")
        raise

def run(switch_api: SwitchAPI, command_manager: CommandManager, logger: logging.Logger) -> bool:
    """Run all VLAN tests.
    
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
        logger.info("Starting VLAN test suite")
        
        # Test VLAN creation
        try:
            test_vlan_creation(switch_api, command_manager, logger)
            test_results.append(("VLAN Creation", True))
        except Exception as e:
            test_results.append(("VLAN Creation", False, str(e)))
        
        # Test VLAN deletion
        try:
            test_vlan_deletion(switch_api, command_manager, logger)
            test_results.append(("VLAN Deletion", True))
        except Exception as e:
            test_results.append(("VLAN Deletion", False, str(e)))
        
        # Test VLAN port assignment
        try:
            test_vlan_port_assignment(switch_api, command_manager, logger)
            test_results.append(("VLAN Port Assignment", True))
        except Exception as e:
            test_results.append(("VLAN Port Assignment", False, str(e)))
        
        # Log test results
        logger.info("\nVLAN Test Suite Results:")
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
        logger.error(f"VLAN test suite failed: {e}")
        return False

if __name__ == "__main__":
    # Example usage
    switch_api = SwitchAPI()  # Initialize with your connection details
    run(switch_api, CommandManager(), logger)
