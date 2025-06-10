# l2_switch_test_framework/main.py

import logging
from utils.connection_manager import ConnectionManager
from utils.logger import setup_logger
from utils.switch_api import SwitchAPI
from utils.command_manager import CommandManager
from tests import test_vlan, test_mac_learning, test_spanning_tree
from config.config_manager import ConfigManager

def main():
    """
    Main function to run switch tests.
    """
    # Setup logging
    logger = setup_logger()
    logger.debug("Starting L2 switch testing framework")
    
    try:
        # Initialize connection and configuration
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
            # logger.debug("Running MAC Learning tests")
            # test_mac_learning.run(switch_api, command_manager, logger)
            # logger.debug("Running Spanning Tree tests")
            # test_spanning_tree.run(switch_api, command_manager, logger)
            
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

if __name__ == "__main__":
    exit(main())
