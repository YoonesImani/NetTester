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

def _parse_vlan_output(vlan_info: str) -> List[Dict[str, str]]:
    """Parse VLAN output into a list of dictionaries.
    
    Args:
        vlan_info: Output from show vlan brief command
        
    Returns:
        List of dictionaries containing VLAN information:
        [
            {
                'vlan_id': '1',
                'name': 'default',
                'status': 'active',
                'ports': 'Fa0/1, Fa0/2, ...'
            },
            ...
        ]
    """
    # Split output into lines and skip header lines
    lines = vlan_info.splitlines()
    vlan_lines = [line for line in lines if line.strip() and not line.startswith('VLAN') and not line.startswith('----')]
    
    vlan_list = []
    for line in vlan_lines:
        # Split line into fields, handling multiple spaces
        fields = line.split()
        if len(fields) >= 2:
            vlan_info = {
                'vlan_id': fields[0],
                'name': fields[1],
                'status': fields[2] if len(fields) > 2 else '',
                'ports': fields[3] if len(fields) > 3 else ''
            }
            vlan_list.append(vlan_info)
    
    return vlan_list

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
    show_cmd = command_manager.format_command('show_commands', 'show_vlan_brief')
    vlan_info = switch_api.send_command(show_cmd)
    
    vlan_list = _parse_vlan_output(vlan_info)
    for vlan in vlan_list:
        if vlan['vlan_id'] == str(vlan_id):
            return vlan['name'] == vlan_name
    
    return False

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
    show_cmd = command_manager.format_command('show_commands', 'show_vlan_brief')
    vlan_info = switch_api.send_command(show_cmd)
    
    vlan_list = _parse_vlan_output(vlan_info)
    for vlan in vlan_list:
        if vlan['vlan_id'] == str(vlan_id):
            return False
    
    return True

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
    show_cmd = command_manager.format_command('show_commands', 'show_vlan_brief')
    vlan_info = switch_api.send_command(show_cmd)
    
    vlan_list = _parse_vlan_output(vlan_info)
    for vlan in vlan_list:
        if vlan['vlan_id'] == str(vlan_id):
            # Split ports by comma and check if our interface is in the list
            port_list = [p.strip() for p in vlan['ports'].split(',')]
            return interface in port_list
    
    return False

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
        show_cmd = command_manager.format_command('vlan_commands', 'show_vlan_brief')
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
        show_cmd = command_manager.format_command('vlan_commands', 'show_vlan_brief')
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
        interface = "FastEthernet0/1"
        
        logger.debug(f"Creating VLAN {vlan_id} for port assignment")
        success, error = switch_api.create_vlan(str(vlan_id), vlan_name)
        assert success, f"Failed to create VLAN {vlan_id}: {error}"
        
        # Configure interface
        logger.debug(f"Configuring interface {interface}")
        interface_cmd = command_manager.format_command('interface_commands', 'configure_interface', interface=interface)
        success, error = switch_api.configure_interface(interface)
        assert success, f"Failed to configure interface {interface}: {error}"
        
        # Set port mode and assign VLAN
        logger.debug(f"Setting port mode and assigning VLAN {vlan_id} to {interface}")
        mode_cmd = command_manager.format_command('interface_commands', 'switchport_mode', mode='access')
        response = switch_api.send_command(mode_cmd)
        assert "Invalid input" not in response, f"Failed to set port mode: {response}"
        
        vlan_cmd = command_manager.format_command('interface_commands', 'switchport_access_vlan', vlan_id=vlan_id)
        response = switch_api.send_command(vlan_cmd)
        assert "Invalid input" not in response, f"Failed to assign VLAN {vlan_id} to port: {response}"
        
        # Exit configuration mode
        end_cmd = command_manager.format_command('system_commands', 'end')
        switch_api.send_command(end_cmd)
        
        # Verify port assignment
        logger.debug("Verifying port assignment")
        show_cmd = command_manager.format_command('vlan_commands', 'show_interface_switchport', interface=interface)
        port_info = switch_api.send_command(show_cmd)
        assert str(vlan_id) in port_info, f"VLAN {vlan_id} not found in port configuration"
        logger.info("[PASS] VLAN port assignment test completed successfully")
        
    except Exception as e:
        logger.error(f"[FAIL] VLAN port assignment test failed: {str(e)}")
        raise

def test_vlan_trunk_configuration(switch_api: SwitchAPI, command_manager: CommandManager , logger: logging.Logger) -> None:
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

def test_vlan_interface(switch_api: SwitchAPI, command_manager: CommandManager , logger: logging.Logger) -> None:
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

def test_voice_vlan(switch_api: SwitchAPI, command_manager: CommandManager , logger: logging.Logger) -> None:
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

def test_private_vlan(switch_api: SwitchAPI, command_manager: CommandManager , logger: logging.Logger) -> None:
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

def test_vlan_acl(switch_api: SwitchAPI, command_manager: CommandManager ,logger: logging.Logger) -> None:
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
    logger.info("Starting VLAN test suite")
    
    test_functions = [
        test_vlan_creation,
        test_vlan_deletion,
        test_vlan_port_assignment,
        test_vlan_trunk_configuration,
        test_vlan_interface,
        test_voice_vlan,
        test_vlan_acl,
        test_private_vlan
    ]
    
    passed_tests = 0
    total_tests = len(test_functions)
    
    # Set up test environment
    logger.info("Setting up test environment")
    setup_test_environment(switch_api, command_manager)
    
    for test_func in test_functions:
        try:
            test_func(switch_api, command_manager, logger)
            passed_tests += 1
        except Exception as e:
            logger.error(f"Test {test_func.__name__} failed: {str(e)}")
            continue
    
    logger.info(f"VLAN test suite completed: {passed_tests}/{total_tests} tests passed")
    return passed_tests == total_tests

if __name__ == "__main__":
    # Example usage
    switch_api = SwitchAPI()  # Initialize with your connection details
    run(switch_api, CommandManager(), logger)
