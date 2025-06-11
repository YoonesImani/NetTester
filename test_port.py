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
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import time

from switch_connection import SwitchConnection
from test_utils import TestResult, TestStatus
from command_manager import CommandManager

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
    
    def __init__(self, connection: SwitchConnection, command_manager: CommandManager):
        self.conn = connection
        self.cmd_mgr = command_manager
        self.results: List[TestResult] = []

    def verify_port_status(self, interface: str) -> TestResult:
        """Verify port operational status"""
        try:
            cmd = self.cmd_mgr.get_command('show_interface_status', interface=interface)
            output = self.conn.execute_command(cmd)
            
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
                commands.append(self.cmd_mgr.get_command('set_port_speed', 
                    interface=config.interface, speed=config.speed))
            if config.duplex:
                commands.append(self.cmd_mgr.get_command('set_port_duplex',
                    interface=config.interface, duplex=config.duplex))
            if config.description:
                commands.append(self.cmd_mgr.get_command('set_port_description',
                    interface=config.interface, description=config.description))
            if config.vlan:
                commands.append(self.cmd_mgr.get_command('set_port_vlan',
                    interface=config.interface, vlan=config.vlan))
            
            for cmd in commands:
                self.conn.execute_command(cmd)
            
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
            cmd = self.cmd_mgr.get_command('enable_port_security', interface=interface)
            self.conn.execute_command(cmd)
            
            # Verify port security status
            cmd = self.cmd_mgr.get_command('show_port_security', interface=interface)
            output = self.conn.execute_command(cmd)
            
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
            cmd = self.cmd_mgr.get_command('configure_port_channel',
                interface=interface, channel_group=channel_group)
            self.conn.execute_command(cmd)
            
            # Verify port channel status
            cmd = self.cmd_mgr.get_command('show_port_channel', interface=interface)
            output = self.conn.execute_command(cmd)
            
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
            cmd = self.cmd_mgr.get_command('show_interface_statistics', interface=interface)
            initial_stats = self.conn.execute_command(cmd)
            
            # Wait for specified duration
            time.sleep(duration)
            
            # Get final statistics
            final_stats = self.conn.execute_command(cmd)
            
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

def main():
    """Main function for running port tests"""
    # Initialize connection and command manager
    connection = SwitchConnection()
    command_manager = CommandManager()
    
    # Create port tester instance
    tester = PortTester(connection, command_manager)
    
    # Run tests for specified interface
    interface = "GigabitEthernet1/0/1"
    results = tester.run_all_tests(interface)
    
    # Print results
    for result in results:
        print(f"{result.name}: {result.status} - {result.message}")

if __name__ == "__main__":
    main() 