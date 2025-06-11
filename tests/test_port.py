#!/usr/bin/env python3
"""
Port Testing Module for L2 Switch Testing Framework

This module implements comprehensive port testing functionality including:
- Port status verification
- Port configuration testing
- Port feature testing
- Port monitoring and statistics
"""

import logging
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import time

from utils.switch_api import SwitchAPI, SwitchAPIError
from utils.switch_feature_checker import check_feature_support
from utils.command_manager import CommandManager
from utils.test_helpers import (
    clear_system_messages,
    setup_test_environment,
    verify_command_response,
    TestStatus,
    TestResult
)

logger = logging.getLogger(__name__)

@dataclass
class PortConfig:
    """Port configuration data class"""
    interface: str
    speed: Optional[str] = None
    duplex: Optional[str] = None
    description: Optional[str] = None
    vlan: Optional[int] = None
    shutdown: bool = False

class PortTester:
    """Port testing implementation class"""
    
    def __init__(self, switch_api: SwitchAPI, command_manager: CommandManager):
        self.switch_api = switch_api
        self.cmd_mgr = command_manager
        self.results: List[TestResult] = []

    def verify_port_status(self, interface: str) -> TestResult:
        """Verify port operational status"""
        try:
            cmd = self.cmd_mgr.format_command('show_commands', 'show_interface_status', interface=interface)
            output = self.switch_api.send_command(cmd)
            
            if 'up' in output.lower():
                return TestResult(
                    name=f"Port {interface} Status Check",
                    status=TestStatus.PASS,
                    message=f"Port {interface} is operational"
                )
            return TestResult(
                name=f"Port {interface} Status Check",
                status=TestStatus.FAIL,
                message=f"Port {interface} is not operational"
            )
        except Exception as e:
            return TestResult(
                name=f"Port {interface} Status Check",
                status=TestStatus.ERROR,
                message=f"Error checking port status: {str(e)}"
            )

    def configure_port(self, config: PortConfig) -> TestResult:
        """Configure port with specified settings"""
        try:
            commands = []
            if config.speed:
                commands.append(self.cmd_mgr.format_command('interface_commands', 'set_speed', speed=config.speed))
            if config.duplex:
                commands.append(self.cmd_mgr.format_command('interface_commands', 'set_duplex', duplex=config.duplex))
            if config.description:
                commands.append(self.cmd_mgr.format_command('interface_commands', 'set_description', description=config.description))
            if config.vlan:
                commands.append(self.cmd_mgr.format_command('interface_commands', 'set_port_vlan', interface=config.interface, vlan=config.vlan))
            
            for cmd in commands:
                self.switch_api.send_command(cmd)
            
            return TestResult(
                name=f"Port {config.interface} Configuration",
                status=TestStatus.PASS,
                message=f"Successfully configured port {config.interface}"
            )
        except Exception as e:
            return TestResult(
                name=f"Port {config.interface} Configuration",
                status=TestStatus.ERROR,
                message=f"Error configuring port: {str(e)}"
            )

    def test_port_security(self, interface: str) -> TestResult:
        """Test port security features"""
        try:
            # Enable port security
            cmd = self.cmd_mgr.format_command('interface_commands', 'configure_port_security')
            self.switch_api.send_command(cmd)
            
            # Verify port security status
            cmd = self.cmd_mgr.format_command('show_commands', 'show_port_security', interface=interface)
            output = self.switch_api.send_command(cmd)
            
            if 'enabled' in output.lower():
                return TestResult(
                    name=f"Port {interface} Security Test",
                    status=TestStatus.PASS,
                    message=f"Port security successfully enabled on {interface}"
                )
            return TestResult(
                name=f"Port {interface} Security Test",
                status=TestStatus.FAIL,
                message=f"Port security not properly enabled on {interface}"
            )
        except Exception as e:
            return TestResult(
                name=f"Port {interface} Security Test",
                status=TestStatus.ERROR,
                message=f"Error testing port security: {str(e)}"
            )

    def test_port_channel(self, interface: str, channel_group: int) -> TestResult:
        """Test port channel/LAG configuration"""
        try:
            # Configure port channel
            cmd = self.cmd_mgr.format_command('interface_commands', 'configure_port_channel',
                interface=interface, channel_group=channel_group)
            self.switch_api.send_command(cmd)
            
            # Verify port channel status
            cmd = self.cmd_mgr.format_command('show_commands', 'show_port_channel', interface=interface)
            output = self.switch_api.send_command(cmd)
            
            if str(channel_group) in output:
                return TestResult(
                    name=f"Port {interface} Channel Test",
                    status=TestStatus.PASS,
                    message=f"Port channel {channel_group} successfully configured"
                )
            return TestResult(
                name=f"Port {interface} Channel Test",
                status=TestStatus.FAIL,
                message=f"Port channel configuration failed"
            )
        except Exception as e:
            return TestResult(
                name=f"Port {interface} Channel Test",
                status=TestStatus.ERROR,
                message=f"Error testing port channel: {str(e)}"
            )

    def monitor_port_statistics(self, interface: str, duration: int = 60) -> TestResult:
        """Monitor port statistics for specified duration"""
        try:
            # Get initial statistics
            cmd = self.cmd_mgr.format_command('show_commands', 'show_interface_status', interface=interface)
            initial_stats = self.switch_api.send_command(cmd)
            
            # Wait for specified duration
            time.sleep(duration)
            
            # Get final statistics
            final_stats = self.switch_api.send_command(cmd)
            
            # Compare statistics
            if self._compare_statistics(initial_stats, final_stats):
                return TestResult(
                    name=f"Port {interface} Statistics Monitoring",
                    status=TestStatus.PASS,
                    message=f"Port statistics collected successfully"
                )
            return TestResult(
                name=f"Port {interface} Statistics Monitoring",
                status=TestStatus.FAIL,
                message=f"Port statistics show unexpected changes"
            )
        except Exception as e:
            return TestResult(
                name=f"Port {interface} Statistics Monitoring",
                status=TestStatus.ERROR,
                message=f"Error monitoring port statistics: {str(e)}"
            )

    def _compare_statistics(self, initial: str, final: str) -> bool:
        """Compare initial and final statistics"""
        # Implement statistics comparison logic here
        # This is a placeholder implementation
        return True

    def run_all_tests(self, interface: str) -> List[TestResult]:
        """Run all port tests for specified interface"""
        self.results = []
        
        # Run basic port tests
        self.results.append(self.verify_port_status(interface))
        
        # Run configuration tests
        config = PortConfig(
            interface=interface,
            speed='1000',
            duplex='full',
            description='Test Port',
            vlan=1
        )
        self.results.append(self.configure_port(config))
        
        # Run feature tests
        self.results.append(self.test_port_security(interface))
        self.results.append(self.test_port_channel(interface, 1))
        
        # Run monitoring tests
        self.results.append(self.monitor_port_statistics(interface))
        
        return self.results

def _parse_port_output(port_info: str) -> List[Dict[str, str]]:
    """Parse port output into a list of dictionaries.
    
    Args:
        port_info: Output from show interfaces status command
        
    Returns:
        List of dictionaries containing port information:
        [
            {
                'port': 'Fa0/1',
                'name': 'Server1',
                'status': 'connected',
                'vlan': '1',
                'duplex': 'full',
                'speed': '1000'
            },
            ...
        ]
    """
    # Split output into lines and skip header lines
    port_lines = re.findall(r'^(?:Fa|Gi)\S+.*', port_info, re.MULTILINE)
    
    port_list = []
    for line in port_lines:
        # Split line into fields, handling multiple spaces
        fields = line.split()
        if len(fields) >= 2:
            port_info = {
            'port': line[0:10].strip(),
            'name': line[10:29].strip(),
            'status': line[29:42].strip(),
            'vlan': line[42:53].strip(),
            'duplex': line[53:61].strip(),
            'speed': line[61:67].strip(),
            'type': line[67:].strip()
            }
            port_list.append(port_info)
    
    return port_list

def verify_port_status(switch_api: SwitchAPI, command_manager: CommandManager,
                      interface: str) -> bool:
    """Verify port operational status.
    
    Args:
        switch_api: Switch API instance
        command_manager: Command manager instance
        interface: Interface to verify (short or full name)
        
    Returns:
        True if port is operational, False otherwise
    """
    show_cmd = command_manager.format_command('show_commands', 'show_interface_status', interface=interface)
    port_info = switch_api.send_command(show_cmd)
    
    port_list = _parse_port_output(port_info)
    for port in port_list:
        # Check if this is the port we're looking for
        if port['port'] == interface:
            logger.debug(f"Found port {interface} with status: {port['status']}")
            return port['status'].lower() == 'connected'
    
    logger.warning(f"Port {interface} not found in output")
    return False

def verify_port_configuration(switch_api: SwitchAPI, command_manager: CommandManager,
                            interface: str, speed: str, duplex: str) -> bool:
    """Verify port configuration.
    
    Args:
        switch_api: Switch API instance
        command_manager: Command manager instance
        interface: Interface to verify (short or full name)
        speed: Expected speed
        duplex: Expected duplex
        
    Returns:
        True if port is configured correctly, False otherwise
    """
    show_cmd = command_manager.format_command('show_commands', 'show_interface_status', interface=interface)
    port_info = switch_api.send_command(show_cmd)
    
    port_list = _parse_port_output(port_info)
    for port in port_list:
        # Check if this is the port we're looking for
        if port['port'] == interface:
            logger.debug(f"Found port {interface} with speed: {port['speed']}, duplex: {port['duplex']}")
            return (port['speed'] == speed and 
                   port['duplex'] == duplex)
    
    logger.warning(f"Port {interface} not found in output")
    return False

def test_port_status(switch_api: SwitchAPI, command_manager: CommandManager, logger: logging.Logger) -> None:
    """Test port operational status."""
    logger.info("Starting port status test")
    try:
        interface = "Fa0/1"
        
        # Enter configuration mode
        logger.info("Entering config mode")
        config_cmd = command_manager.format_command('system_commands', 'configure_terminal')
        switch_api.send_command(config_cmd)
        time.sleep(2)
        
        # Configure interface
        logger.debug(f"Configuring {interface}")
        config_cmd = command_manager.format_command('interface_commands', 'configure_interface', interface=interface)
        switch_api.send_command(config_cmd)
        
        # Enable interface
        no_shutdown_cmd = command_manager.format_command('interface_commands', 'no_shutdown')
        switch_api.send_command(no_shutdown_cmd)
        
        # Exit configuration mode
        end_cmd = command_manager.format_command('system_commands', 'end')
        switch_api.send_command(end_cmd)
        
        # Verify port status
        logger.debug(f"Verifying status of {interface}")
        assert verify_port_status(switch_api, command_manager, interface), \
            f"Port {interface} is not operational"
        
        logger.info("[PASS] Port status test completed successfully")
        
    except Exception as e:
        logger.error(f"[FAIL] Port status test failed: {str(e)}")
        raise

def test_port_configuration(switch_api: SwitchAPI, command_manager: CommandManager, logger: logging.Logger) -> None:
    """Test port configuration."""
    logger.info("Starting port configuration test")
    try:
        interface = "Fa0/1"
        speed = "10"
        duplex = "full"
        description = "Test Port"
        
        # Enter configuration mode
        logger.info("Entering config mode")
        config_cmd = command_manager.format_command('system_commands', 'configure_terminal')
        switch_api.send_command(config_cmd)
        time.sleep(2)
        
        # Configure interface
        logger.debug(f"Configuring {interface}")
        config_cmd = command_manager.format_command('interface_commands', 'configure_interface', interface=interface)
        switch_api.send_command(config_cmd)
        
        # Set speed
        speed_cmd = command_manager.format_command('interface_commands', 'set_speed', speed=speed)
        switch_api.send_command(speed_cmd)
        
        # Set duplex
        duplex_cmd = command_manager.format_command('interface_commands', 'set_duplex', duplex=duplex)
        switch_api.send_command(duplex_cmd)
        
        # Set description
        desc_cmd = command_manager.format_command('interface_commands', 'set_description', description=description)
        switch_api.send_command(desc_cmd)
        
        # Exit configuration mode
        end_cmd = command_manager.format_command('system_commands', 'end')
        switch_api.send_command(end_cmd)
        
        # Verify configuration
        logger.debug("Verifying port configuration")
        assert verify_port_configuration(switch_api, command_manager, interface, speed, duplex), \
            f"Port {interface} not configured correctly"
        
        logger.info("[PASS] Port configuration test completed successfully")
        
    except Exception as e:
        logger.error(f"[FAIL] Port configuration test failed: {str(e)}")
        raise

def test_port_security(switch_api: SwitchAPI, command_manager: CommandManager, logger: logging.Logger) -> None:
    """Test port security features."""
    logger.info("Starting port security test")
    try:
        interface = "Fa0/1"
        max_mac = "2"
        violation_action = "restrict"
        
        # Enter configuration mode
        logger.info("Entering config mode")
        config_cmd = command_manager.format_command('system_commands', 'configure_terminal')
        switch_api.send_command(config_cmd)
        time.sleep(2)
        
        # Configure interface
        logger.debug(f"Configuring {interface}")
        config_cmd = command_manager.format_command('interface_commands', 'configure_interface', interface=interface)
        switch_api.send_command(config_cmd)
        
        # Configure port security
        logger.debug(f"Configuring port security on {interface}")
        security_cmd = command_manager.format_command('interface_commands', 'configure_port_security')
        switch_api.send_command(security_cmd)
        
        # Set maximum MAC addresses
        max_mac_cmd = command_manager.format_command('interface_commands', 'set_port_security_max_mac', max_mac=max_mac)
        switch_api.send_command(max_mac_cmd)
        
        # Set violation action
        violation_cmd = command_manager.format_command('interface_commands', 'set_port_security_violation', action=violation_action)
        switch_api.send_command(violation_cmd)
        
        # Exit configuration mode
        end_cmd = command_manager.format_command('system_commands', 'end')
        switch_api.send_command(end_cmd)
        
        # Verify port security
        logger.debug("Verifying port security configuration")
        verify_cmd = command_manager.format_command('show_commands', 'show_port_security', interface=interface)
        output = switch_api.send_command(verify_cmd)
        assert "Port Security" in output, f"Port security not enabled on {interface}"
        assert f"Maximum MAC Addresses: {max_mac}" in output, f"Maximum MAC addresses not set correctly"
        assert f"Violation Mode: {violation_action}" in output, f"Violation action not set correctly"
        
        logger.info("[PASS] Port security test completed successfully")
        
    except Exception as e:
        logger.error(f"[FAIL] Port security test failed: {str(e)}")
        raise

def test_port_channel(switch_api: SwitchAPI, command_manager: CommandManager, logger: logging.Logger) -> None:
    """Test port channel configuration."""
    logger.info("Starting port channel test")
    try:
        interface = "Fa0/1"
        channel_group = "1"
        mode = "active"
        
        # Enter configuration mode
        logger.info("Entering config mode")
        config_cmd = command_manager.format_command('system_commands', 'configure_terminal')
        switch_api.send_command(config_cmd)
        time.sleep(2)
        
        # Configure interface
        logger.debug(f"Configuring {interface}")
        config_cmd = command_manager.format_command('interface_commands', 'configure_interface', interface=interface)
        switch_api.send_command(config_cmd)
        
        # Configure port channel
        logger.debug(f"Configuring port channel on {interface}")
        channel_cmd = command_manager.format_command('interface_commands', 'configure_port_channel',
                                                   channel_group=channel_group, mode=mode)
        switch_api.send_command(channel_cmd)
        
        # Exit configuration mode
        end_cmd = command_manager.format_command('system_commands', 'end')
        switch_api.send_command(end_cmd)
        
        # Verify port channel
        logger.debug("Verifying port channel configuration")
        verify_cmd = command_manager.format_command('show_commands', 'show_port_channel', interface=interface)
        output = switch_api.send_command(verify_cmd)
        assert f"Port-channel{channel_group}" in output, f"Port channel {channel_group} not configured correctly"
        
        logger.info("[PASS] Port channel test completed successfully")
        
    except Exception as e:
        logger.error(f"[FAIL] Port channel test failed: {str(e)}")
        raise

def run(switch_api: SwitchAPI, command_manager: CommandManager, logger: logging.Logger) -> bool:
    """Run all port tests.
    
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
        logger.info("Starting port test suite")
        
        # Test port status
        try:
            test_port_status(switch_api, command_manager, logger)
            test_results.append(("Port Status", True))
        except Exception as e:
            test_results.append(("Port Status", False, str(e)))
        
        # Test port configuration
        try:
            test_port_configuration(switch_api, command_manager, logger)
            test_results.append(("Port Configuration", True))
        except Exception as e:
            test_results.append(("Port Configuration", False, str(e)))
        
        # Test port security
        try:
            test_port_security(switch_api, command_manager, logger)
            test_results.append(("Port Security", True))
        except Exception as e:
            test_results.append(("Port Security", False, str(e)))
        
        # Test port channel
        try:
            test_port_channel(switch_api, command_manager, logger)
            test_results.append(("Port Channel", True))
        except Exception as e:
            test_results.append(("Port Channel", False, str(e)))
        
        # Log test results
        logger.info("\nPort Test Suite Results:")
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
        logger.error(f"Port test suite failed: {e}")
        return False

def main():
    """Main function for running port tests"""
    # Initialize connection and command manager
    switch_api = SwitchAPI()
    command_manager = CommandManager()
    
    # Create port tester instance
    tester = PortTester(switch_api, command_manager)
    
    # Run tests for specified interface
    interface = "GigabitEthernet1/0/1"
    results = tester.run_all_tests(interface)
    
    # Print results
    for result in results:
        print(f"{result.name}: {result.status} - {result.message}")

if __name__ == "__main__":
    main() 