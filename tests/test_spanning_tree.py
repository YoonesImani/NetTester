"""
Test module for Spanning Tree Protocol (STP) functionality on L2 switches.
Tests STP configuration, verification, and behavior.
"""

import logging
import time
import json
from typing import List, Tuple, Dict, Any
from utils.switch_api import SwitchAPI, SwitchAPIError
from config.config_manager import ConfigManager
from utils.command_manager import CommandManager
from utils.test_helpers import (
    clear_system_messages,
    setup_test_environment,
    verify_command_response
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class STPError(SwitchAPIError):
    """Exception raised for STP operation failures."""
    pass

class SwitchPatternConfig:
    """Configuration for different switch types and their command patterns."""
    
    def __init__(self, switch_type: str):
        """
        Initialize switch pattern configuration.
        
        Args:
            switch_type: Type of switch (e.g., 'cisco', 'hpe', 'juniper')
        """
        self.switch_type = switch_type
        self.patterns = self._load_patterns()
    
    def _load_patterns(self) -> Dict[str, Any]:
        """Load patterns from configuration file."""
        try:
            with open(f'config/switch_patterns/{self.switch_type}.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            # Return default patterns if specific switch type not found
            return {
                'stp_mode': {
                    'command': 'show spanning-tree mode',
                    'patterns': ['Spanning tree mode', 'STP mode']
                },
                'root_bridge': {
                    'command': 'show spanning-tree vlan {vlan}',
                    'priority_keyword': 'Priority',
                    'value_position': 'next'
                },
                'port_cost': {
                    'command': 'show spanning-tree vlan {vlan}',
                    'port_format': '{port}',
                    'cost_position': 3
                },
                'port_priority': {
                    'command': 'show spanning-tree vlan {vlan}',
                    'port_format': '{port}',
                    'priority_format': '{priority}.{port_number}'
                },
                'stp_guard': {
                    'command': 'show spanning-tree guard {port}',
                    'patterns': {
                        'root': 'Root',
                        'bpdu': 'BPDU',
                        'loop': 'Loop'
                    }
                },
                'stp_state': {
                    'command': 'show spanning-tree vlan {vlan} state',
                    'patterns': ['Forwarding', 'Blocking']
                },
                'stp_convergence': {
                    'command': 'show spanning-tree vlan {vlan} state',
                    'patterns': ['Forwarding', 'Blocking']
                }
            }
    
    def get_command(self, command_type: str, **kwargs) -> str:
        """Get command string for the specified type."""
        cmd_template = self.patterns[command_type]['command']
        return cmd_template.format(**kwargs)
    
    def get_priority_keyword(self) -> str:
        """Get priority keyword for the switch type."""
        return self.patterns['root_bridge']['priority_keyword']
    
    def get_port_format(self) -> str:
        """Get port format for the switch type."""
        return self.patterns['port_cost']['port_format']
    
    def get_priority_format(self) -> str:
        """Get priority format for the switch type."""
        return self.patterns['port_priority']['priority_format']

def verify_stp_mode(switch_api: SwitchAPI, command_manager: CommandManager,
                   mode: str) -> bool:
    """Verify spanning tree mode.
    
    Args:
        switch_api: Switch API instance
        command_manager: Command manager instance
        mode: Expected STP mode
        
    Returns:
        True if mode matches, False otherwise
    """
    show_cmd = command_manager.format_command('spanning_tree_commands', 'show_spanning_tree', vlan=1)
    response = switch_api.send_command(show_cmd)
    return mode.lower() in response.lower()

def verify_root_bridge_priority(switch_api: SwitchAPI, command_manager: CommandManager,
                              vlan_id: int, priority: int) -> bool:
    """Verify root bridge priority.
    
    Args:
        switch_api: Switch API instance
        command_manager: Command manager instance
        vlan_id: VLAN ID to check
        priority: Expected priority value
        
    Returns:
        True if priority matches, False otherwise
    """
    show_cmd = command_manager.format_command('spanning_tree_commands', 'show_spanning_tree', vlan=vlan_id)
    response = switch_api.send_command(show_cmd)
    return str(priority) in response

def test_stp_mode(switch_api: SwitchAPI, command_manager: CommandManager, logger: logging.Logger) -> None:
    """Test spanning tree mode configuration."""
    logger.info("Starting STP mode test")
    try:
        # Configure STP mode
        stp_cmd = command_manager.format_command('spanning_tree_commands', 
                                               'configure_spanning_tree', mode='rapid-pvst')
        logger.debug(f"Sending command: {stp_cmd}")
        switch_api.send_command(stp_cmd)
        
        # Verify STP mode
        logger.debug("Verifying STP mode configuration")
        assert verify_stp_mode(switch_api, command_manager, 'rapid-pvst'), \
            "Failed to configure STP mode"
        logger.info("[PASS] STP mode test completed successfully")
        
    except Exception as e:
        logger.error(f"[FAIL] STP mode test failed: {str(e)}")
        raise

def test_root_bridge_priority(switch_api: SwitchAPI, command_manager: CommandManager, logger: logging.Logger) -> None:
    """Test root bridge priority configuration."""
    logger.info("Starting root bridge priority test")
    try:
        # Set root bridge priority
        priority_cmd = command_manager.format_command('spanning_tree_commands', 
                                                    'configure_spanning_tree', 
                                                    mode='rapid-pvst', vlan=1, priority=4096)
        logger.debug(f"Sending command: {priority_cmd}")
        switch_api.send_command(priority_cmd)
        
        # Verify root bridge priority
        logger.debug("Verifying root bridge priority")
        assert verify_root_bridge_priority(switch_api, command_manager, 1, 4096), \
            "Failed to set root bridge priority"
        logger.info("[PASS] Root bridge priority test completed successfully")
        
    except Exception as e:
        logger.error(f"[FAIL] Root bridge priority test failed: {str(e)}")
        raise

def test_port_cost(switch_api: SwitchAPI, command_manager: CommandManager, logger: logging.Logger) -> None:
    """Test port cost configuration."""
    logger.info("Starting port cost test")
    try:
        # Configure interface
        interface_cmd = command_manager.format_command('interface_commands', 'configure_interface',
                                                     interface_name='FastEthernet0/1',
                                                     subcommand='switchport_mode_access')
        switch_api.send_command(interface_cmd)
        
        # Exit interface configuration
        switch_api.send_command("exit")
        time.sleep(1)
        
        # Exit configuration mode
        switch_api.send_command("end")
        time.sleep(1)
        
        # Set port cost
        cost_cmd = command_manager.format_command('interface_commands', 'configure_interface',
                                                interface_name='FastEthernet0/1',
                                                subcommand='spanning_tree_cost',
                                                cost=100)
        logger.debug(f"Sending command: {cost_cmd}")
        switch_api.send_command(cost_cmd)
        
        # Verify port cost
        show_cmd = command_manager.format_command('spanning_tree_commands', 
                                                'show_spanning_tree', vlan=1)
        logger.debug(f"Sending command: {show_cmd}")
        response = switch_api.send_command(show_cmd)
        assert '100' in response, "Failed to set port cost"
        logger.info("[PASS] Port cost test completed successfully")
        
    except Exception as e:
        logger.error(f"[FAIL] Port cost test failed: {str(e)}")
        raise

def test_port_priority(switch_api: SwitchAPI, command_manager: CommandManager, logger: logging.Logger) -> None:
    """Test port priority configuration."""
    logger.info("Starting port priority test")
    try:
        # Configure interface
        interface_cmd = command_manager.format_command('interface_commands', 'configure_interface',
                                                     interface_name='FastEthernet0/1')
        logger.debug(f"Sending command: {interface_cmd}")
        switch_api.send_command(interface_cmd)
        
        # Set port priority
        priority_cmd = command_manager.format_command('interface_commands', 'configure_interface',
                                                    interface_name='FastEthernet0/1',
                                                    subcommand='spanning_tree_priority',
                                                    priority=64)
        logger.debug(f"Sending command: {priority_cmd}")
        switch_api.send_command(priority_cmd)
        
        # Verify port priority
        show_cmd = command_manager.format_command('spanning_tree_commands', 
                                                'show_spanning_tree', vlan=1)
        logger.debug(f"Sending command: {show_cmd}")
        response = switch_api.send_command(show_cmd)
        assert '64' in response, "Failed to set port priority"
        logger.info("[PASS] Port priority test completed successfully")
        
    except Exception as e:
        logger.error(f"[FAIL] Port priority test failed: {str(e)}")
        raise

def test_stp_root_bridge(switch: SwitchAPI, logger: logging.Logger, vlan: str, priority: str) -> Tuple[bool, str]:
    """
    Test STP root bridge configuration.
    
    Args:
        switch: Switch API instance
        logger: Logger object for test output
        vlan: VLAN ID
        priority: Bridge priority value
        
    Returns:
        Tuple[bool, str]: (success status, error message if any)
    """
    try:
        logger.info(f"Configuring root bridge for VLAN {vlan} with priority {priority}")
        success, error = switch.configure_root_bridge(vlan, priority)
        if not success:
            return False, f"Failed to configure root bridge: {error}"
        
        # Clear system messages after config change
        clear_system_messages(switch, logger)
            
        # Verify root bridge configuration with sys-id-ext
        success, error = verify_root_bridge_priority(switch, logger, int(vlan), int(priority))
        if not success:
            return False, f"Root bridge verification failed: {error}"
            
        logger.info(f"[PASS] Root bridge configured successfully for VLAN {vlan}")
        return True, ""
        
    except Exception as e:
        return False, f"Unexpected error in root bridge test: {str(e)}"

def test_stp_port_cost(switch: SwitchAPI, logger: logging.Logger, port: str, vlan: str, cost: str) -> Tuple[bool, str]:
    """
    Test STP port cost configuration.
    
    Args:
        switch: Switch API instance
        logger: Logger object for test output
        port: Port identifier
        vlan: VLAN ID
        cost: Port cost value
        
    Returns:
        Tuple[bool, str]: (success status, error message if any)
    """
    try:
        logger.info(f"Configuring port cost for {port} in VLAN {vlan}")
        success, error = switch.configure_port_cost(port, vlan, cost)
        if not success:
            return False, f"Failed to configure port cost: {error}"
        
        # Clear system messages after config change
        clear_system_messages(switch, logger)
            
        # Verify port cost configuration
        success, error = switch.verify_port_cost(port, vlan, cost)
        if not success:
            return False, f"Port cost verification failed: {error}"
            
        logger.info(f"[PASS] Port cost configured successfully for {port}")
        return True, ""
        
    except Exception as e:
        return False, f"Unexpected error in port cost test: {str(e)}"

def test_stp_port_priority(switch: SwitchAPI, logger: logging.Logger, port: str, vlan: str, priority: str) -> Tuple[bool, str]:
    """
    Test STP port priority configuration.
    
    Args:
        switch: Switch API instance
        logger: Logger object for test output
        port: Port identifier
        vlan: VLAN ID
        priority: Port priority value
        
    Returns:
        Tuple[bool, str]: (success status, error message if any)
    """
    try:
        logger.info(f"Configuring port priority for {port} in VLAN {vlan}")
        success, error = switch.configure_port_priority(port, vlan, priority)
        if not success:
            return False, f"Failed to configure port priority: {error}"
        
        # Clear system messages after config change
        clear_system_messages(switch, logger)
            
        # Verify port priority configuration
        success, error = switch.verify_port_priority(port, vlan, priority)
        if not success:
            return False, f"Port priority verification failed: {error}"
            
        logger.info(f"[PASS] Port priority configured successfully for {port}")
        return True, ""
        
    except Exception as e:
        return False, f"Unexpected error in port priority test: {str(e)}"

def test_stp_guard(switch: SwitchAPI, logger: logging.Logger, port: str, guard_type: str, switch_config: SwitchPatternConfig) -> Tuple[bool, str]:
    """
    Test STP guard features.
    
    Args:
        switch: Switch API instance
        logger: Logger object for test output
        port: Port identifier
        guard_type: Type of guard (root, bpdu, loop)
        switch_config: Switch pattern configuration
        
    Returns:
        Tuple[bool, str]: (success status, error message if any)
    """
    try:
        logger.info(f"Configuring {guard_type} guard on {port}")
        success, error = switch.configure_stp_guard(port, guard_type)
        if not success:
            return False, f"Failed to configure STP guard: {error}"
        
        # Clear system messages after config change
        clear_system_messages(switch, logger)
            
        # Verify guard configuration using switch-specific command
        command = switch_config.get_command('stp_guard', port=port)
        output = switch.send_command(command)
        clear_system_messages(switch, logger)
        
        # Format port according to switch type
        port_format = switch_config.get_port_format()
        formatted_port = port_format.format(port=port)
        
        # Get guard patterns for the switch type
        guard_patterns = switch_config.patterns['stp_guard']['patterns']
        guard_keyword = guard_patterns.get(guard_type, guard_type)
        
        # Look for the port and guard configuration
        for line in output.splitlines():
            if formatted_port in line and guard_keyword in line:
                logger.info(f"[PASS] {guard_type} guard configured successfully")
                return True, ""
        
        return False, f"{guard_type} guard configuration not found for port {port}"
        
    except Exception as e:
        return False, f"Unexpected error in STP guard test: {str(e)}"

def test_stp_convergence(switch: SwitchAPI, logger: logging.Logger, vlan: str, switch_config: SwitchPatternConfig) -> Tuple[bool, str]:
    """
    Test STP convergence behavior.
    
    Args:
        switch: Switch API instance
        logger: Logger object for test output
        vlan: VLAN ID
        switch_config: Switch pattern configuration
        
    Returns:
        Tuple[bool, str]: (success status, error message if any)
    """
    try:
        logger.info(f"Testing STP convergence for VLAN {vlan}")
        
        # Get initial STP state
        command = switch_config.get_command('stp_state', vlan=vlan)
        initial_state = switch.send_command(command)
        clear_system_messages(switch, logger)
        
        # Test convergence
        success, error = switch.test_stp_convergence(vlan)
        if not success:
            return False, f"STP convergence test failed: {error}"
        
        # Clear system messages after test
        clear_system_messages(switch, logger)
        
        # Get final STP state
        final_state = switch.send_command(command)
        clear_system_messages(switch, logger)
        
        # Verify convergence using switch-specific patterns
        convergence_patterns = switch_config.patterns['stp_convergence']['patterns']
        if not any(pattern in final_state for pattern in convergence_patterns):
            return False, f"STP convergence verification failed. Expected patterns: {convergence_patterns}, output: {final_state}"
            
        logger.info(f"[PASS] STP convergence test completed successfully")
        return True, ""
        
    except Exception as e:
        return False, f"Unexpected error in STP convergence test: {str(e)}"

def verify_port_cost_pattern(switch: SwitchAPI, logger: logging.Logger, port: str, vlan: str, cost: str, switch_config: SwitchPatternConfig) -> Tuple[bool, str]:
    """
    Verify port cost using the interface output pattern.
    
    Args:
        switch: Switch API instance
        logger: Logger object for test output
        port: Port identifier
        vlan: VLAN ID
        cost: Expected port cost value
        switch_config: Switch pattern configuration
        
    Returns:
        Tuple[bool, str]: (success status, error message if any)
    """
    try:
        logger.info(f"Verifying port cost for {port} in VLAN {vlan}")
        
        # Get spanning tree information using switch-specific command
        command = switch_config.get_command('port_cost', vlan=vlan)
        output = switch.send_command(command)
        clear_system_messages(switch, logger)
        
        # Format port according to switch type
        port_format = switch_config.get_port_format()
        formatted_port = port_format.format(port=port)
        
        # Look for the port in the output
        for line in output.splitlines():
            if formatted_port in line:
                # Parse the cost from the line
                parts = [p for p in line.split() if p]
                if len(parts) >= 4:
                    actual_cost = parts[switch_config.patterns['port_cost']['cost_position']]
                    if actual_cost == cost:
                        logger.info(f"[PASS] Port cost verified: {cost}")
                        return True, ""
                    else:
                        return False, f"Port cost mismatch. Expected {cost}, found {actual_cost} in line: {line}"
        
        return False, f"Port {port} not found in spanning tree output"
        
    except Exception as e:
        return False, f"Error verifying port cost: {str(e)}"

def verify_port_priority_pattern(switch: SwitchAPI, logger: logging.Logger, port: str, vlan: str, priority: str, switch_config: SwitchPatternConfig) -> Tuple[bool, str]:
    """
    Verify port priority using the interface output pattern.
    
    Args:
        switch: Switch API instance
        logger: Logger object for test output
        port: Port identifier
        vlan: VLAN ID
        priority: Expected port priority value
        switch_config: Switch pattern configuration
        
    Returns:
        Tuple[bool, str]: (success status, error message if any)
    """
    try:
        logger.info(f"Verifying port priority for {port} in VLAN {vlan}")
        
        # Get spanning tree information using switch-specific command
        command = switch_config.get_command('port_priority', vlan=vlan)
        output = switch.send_command(command)
        clear_system_messages(switch, logger)
        
        # Format port according to switch type
        port_format = switch_config.get_port_format()
        formatted_port = port_format.format(port=port)
        
        # Look for the port in the output
        for line in output.splitlines():
            if formatted_port in line:
                # Parse the priority from the line
                parts = [p for p in line.split() if p]
                if len(parts) >= 5:
                    # Get priority format from switch config
                    priority_format = switch_config.get_priority_format()
                    # Extract port number from port string (e.g., "Fa0/1" -> "1")
                    port_number = port.split('/')[-1]
                    expected_priority_format = priority_format.format(priority=priority, port_number=port_number)
                    
                    actual_priority = parts[4]
                    if actual_priority == expected_priority_format:
                        logger.info(f"[PASS] Port priority verified: {priority}")
                        return True, ""
                    else:
                        return False, f"Port priority mismatch. Expected {expected_priority_format}, found {actual_priority} in line: {line}"
        
        return False, f"Port {port} not found in spanning tree output"
        
    except Exception as e:
        return False, f"Error verifying port priority: {str(e)}"

def run(switch_api: SwitchAPI, command_manager: CommandManager, logger: logging.Logger) -> bool:
    """Run all spanning tree tests.
    
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
        logger.info("Starting Spanning Tree test suite")
        
        # Test STP mode
        try:
            test_stp_mode(switch_api, command_manager, logger)
            test_results.append(("STP Mode", True))
        except Exception as e:
            test_results.append(("STP Mode", False, str(e)))
        
        # Test root bridge priority
        try:
            test_root_bridge_priority(switch_api, command_manager, logger)
            test_results.append(("Root Bridge Priority", True))
        except Exception as e:
            test_results.append(("Root Bridge Priority", False, str(e)))
        
        # Test port cost
        try:
            test_port_cost(switch_api, command_manager, logger)
            test_results.append(("Port Cost", True))
        except Exception as e:
            test_results.append(("Port Cost", False, str(e)))
        
        # Test port priority
        try:
            test_port_priority(switch_api, command_manager, logger)
            test_results.append(("Port Priority", True))
        except Exception as e:
            test_results.append(("Port Priority", False, str(e)))
        
        # Log test results
        logger.info("\nSpanning Tree Test Suite Results:")
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
        logger.error(f"Spanning Tree test suite failed: {e}")
        return False

if __name__ == "__main__":
    # Example usage
    switch_api = SwitchAPI()  # Initialize with your connection details
    run(switch_api, CommandManager(), logger) 