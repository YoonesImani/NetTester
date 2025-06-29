# l2_switch_test_framework/main.py

import logging
from utils.connection_manager import ConnectionManager
from utils.connection_context import switch_connection, connection_manager
from utils.logger import setup_logger
from utils.switch_api import SwitchAPI
from utils.command_manager import CommandManager
from tests import test_vlan, test_mac_learning, test_spanning_tree, test_port
from config.config_manager import ConfigManager


def main_traditional():
    """
    Main function using traditional OOP approach.
    """
    # Setup logging
    logger = setup_logger()
    logger.debug("Starting L2 switch testing framework (Traditional OOP)")
    
    try:
        # Initialize configuration and connection manager
        logger.debug("Initializing configuration")
        config = ConfigManager()
        
        logger.debug("Initializing connection manager")
        conn_manager = ConnectionManager(config)
        
        # Initialize command manager
        logger.debug("Initializing command manager")
        command_manager = CommandManager()
        
        # Create SwitchAPI instance with the connection manager
        switch_api = SwitchAPI(conn_manager)
        
        # Run tests
        logger.info("Starting test execution")
        try:
            # Connect to the switch
            switch_api._ensure_connection()
            
            logger.debug("Running VLAN tests")
            test_vlan.run(switch_api, command_manager, logger)
            logger.debug("Running MAC Learning tests")
            test_mac_learning.run(switch_api, command_manager, logger)
            logger.debug("Running Spanning Tree tests")
            test_spanning_tree.run(switch_api, command_manager, logger)
            logger.debug("Running Port tests")
            test_port.run(switch_api, command_manager, logger)
            
            logger.info("[PASS] All tests completed successfully")
            
        finally:
            # Ensure we disconnect properly
            switch_api.disconnect()
        
    except ConnectionError as e:
        logger.error(f"[FAIL] Test suite failed due to switch operation error: {str(e)}")
        return 1
    except Exception as e:
        logger.error(f"[FAIL] Unexpected error during test execution: {str(e)}")
        return 1
        
    return 0

def main_context_manager():
    """
    Main function using context manager approach (cleaner).
    """
    logger = setup_logger()
    logger.debug("Starting L2 switch testing framework (Context Manager)")
    
    try:
        # Use context manager for automatic cleanup
        with switch_connection() as switch_api:
            logger.info("Starting test execution with context manager")
            
            # Initialize command manager
            command_manager = CommandManager()
            
            # Run all tests - no need to manually connect/disconnect
            logger.debug("Running VLAN tests")
            test_vlan.run(switch_api, command_manager, logger)
            
            logger.debug("Running MAC Learning tests")
            test_mac_learning.run(switch_api, command_manager, logger)
            
            logger.debug("Running Spanning Tree tests")
            test_spanning_tree.run(switch_api, command_manager, logger)
            
            logger.debug("Running Port tests")
            test_port.run(switch_api, command_manager, logger)
            
            logger.info("[PASS] All tests completed successfully")
            
    except Exception as e:
        logger.error(f"[FAIL] Unexpected error during test execution: {str(e)}")
        return 1
        
    return 0

def main():
    """
    Main entry point - choose your preferred approach.
    """
    # You can choose either approach:
    # return main_traditional()  # Traditional OOP
    return main_context_manager()  # Context manager (recommended)

if __name__ == "__main__":
    exit(main())
