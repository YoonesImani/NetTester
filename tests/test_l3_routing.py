"""
L3 Routing testing module for Cisco c7200 routers in GNS3.
"""

import logging
import time
import json
import re
from typing import List, Tuple, Dict, Any, Optional
from utils.switch_api import SwitchAPI, SwitchAPIError
from utils.command_manager import CommandManager
from utils.test_helpers import (
    clear_system_messages,
    setup_test_environment,
    verify_command_response
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class L3RoutingError(SwitchAPIError):
    """Exception raised for L3 routing operation errors."""
    pass

def _parse_routing_table(routing_output: str) -> List[Dict[str, str]]:
    """Parse routing table output into structured data."""
    routes = []
    lines = routing_output.splitlines()
    
    for line in lines:
        if re.match(r'^[A-Z]', line):  # Route codes like C, O, E, etc.
            parts = line.split()
            if len(parts) >= 4:
                route_info = {
                    'code': parts[0],
                    'network': parts[1],
                    'via': parts[2] if len(parts) > 2 else '',
                    'interface': parts[3] if len(parts) > 3 else '',
                    'metric': parts[4] if len(parts) > 4 else '',
                    'next_hop': parts[2] if len(parts) > 2 else ''
                }
                routes.append(route_info)
    
    return routes

def test_interface_ip_configuration(switch_api: SwitchAPI, command_manager: CommandManager, logger: logging.Logger) -> None:
    """Test IP address configuration on interfaces."""
    logger.info("Starting interface IP configuration test")
    try:
        interface = "FastEthernet0/0"
        ip_address = "192.168.1.1"
        subnet_mask = "255.255.255.0"
        
        # Configure interface IP address
        logger.debug(f"Configuring IP address {ip_address}/{subnet_mask} on {interface}")
        success, error = switch_api.configure_interface_ip(interface, ip_address, subnet_mask)
        assert success, f"Failed to configure IP on {interface}: {error}"
        
        # Verify configuration
        logger.debug("Verifying IP configuration")
        show_cmd = command_manager.format_command('show_commands', 'show_ip_interface_brief')
        output = switch_api.send_command(show_cmd)
        assert ip_address in output, f"IP address {ip_address} not found in interface output"
        
        logger.info("[PASS] Interface IP configuration test completed successfully")
        
    except Exception as e:
        logger.error(f"[FAIL] Interface IP configuration test failed: {str(e)}")
        raise

def test_static_routing(switch_api: SwitchAPI, command_manager: CommandManager, logger: logging.Logger) -> None:
    """Test static route configuration."""
    logger.info("Starting static routing test")
    try:
        network = "10.0.0.0"
        mask = "255.255.255.0"
        next_hop = "192.168.1.2"
        
        # Add static route
        logger.debug(f"Adding static route {network}/{mask} via {next_hop}")
        success, error = switch_api.add_static_route(network, mask, next_hop)
        assert success, f"Failed to add static route: {error}"
        
        # Verify route in routing table
        logger.debug("Verifying static route in routing table")
        show_cmd = command_manager.format_command('show_commands', 'show_ip_route')
        output = switch_api.send_command(show_cmd)
        assert network in output, f"Static route {network} not found in routing table"
        
        logger.info("[PASS] Static routing test completed successfully")
        
    except Exception as e:
        logger.error(f"[FAIL] Static routing test failed: {str(e)}")
        raise

def test_ospf_configuration(switch_api: SwitchAPI, command_manager: CommandManager, logger: logging.Logger) -> None:
    """Test OSPF routing protocol configuration."""
    logger.info("Starting OSPF configuration test")
    try:
        process_id = "1"
        network = "192.168.1.0"
        wildcard_mask = "0.0.0.255"
        area = "0"
        
        # Configure OSPF
        logger.debug(f"Configuring OSPF process {process_id}")
        success, error = switch_api.configure_ospf(process_id, network, wildcard_mask, area)
        assert success, f"Failed to configure OSPF: {error}"
        
        # Verify OSPF configuration
        logger.debug("Verifying OSPF configuration")
        show_cmd = command_manager.format_command('show_commands', 'show_ip_ospf')
        output = switch_api.send_command(show_cmd)
        assert f"Process {process_id}" in output, f"OSPF process {process_id} not found"
        
        logger.info("[PASS] OSPF configuration test completed successfully")
        
    except Exception as e:
        logger.error(f"[FAIL] OSPF configuration test failed: {str(e)}")
        raise

def test_acl_configuration(switch_api: SwitchAPI, command_manager: CommandManager, logger: logging.Logger) -> None:
    """Test Access Control List configuration."""
    logger.info("Starting ACL configuration test")
    try:
        acl_name = "TEST_ACL"
        sequence = "10"
        action = "permit"
        protocol = "ip"
        source = "192.168.1.0"
        source_wildcard = "0.0.0.255"
        destination = "any"
        
        # Create ACL
        logger.debug(f"Creating ACL {acl_name}")
        success, error = switch_api.create_acl(acl_name, sequence, action, protocol, source, source_wildcard, destination)
        assert success, f"Failed to create ACL: {error}"
        
        # Verify ACL configuration
        logger.debug("Verifying ACL configuration")
        show_cmd = command_manager.format_command('show_commands', 'show_ip_access_list')
        output = switch_api.send_command(show_cmd)
        assert acl_name in output, f"ACL {acl_name} not found"
        
        logger.info("[PASS] ACL configuration test completed successfully")
        
    except Exception as e:
        logger.error(f"[FAIL] ACL configuration test failed: {str(e)}")
        raise

def run(switch_api: SwitchAPI, command_manager: CommandManager, logger: logging.Logger) -> bool:
    """Run all L3 routing tests."""
    logger.info("Starting L3 routing test suite")
    
    test_functions = [
        test_interface_ip_configuration,
        test_static_routing,
        test_ospf_configuration,
        test_acl_configuration
    ]
    
    passed_tests = 0
    total_tests = len(test_functions)
    
    for test_func in test_functions:
        try:
            test_func(switch_api, command_manager, logger)
            passed_tests += 1
        except Exception as e:
            logger.error(f"Test {test_func.__name__} failed: {str(e)}")
            continue
    
    logger.info(f"L3 routing test suite completed: {passed_tests}/{total_tests} tests passed")
    return passed_tests == total_tests
