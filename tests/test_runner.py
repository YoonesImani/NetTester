"""Test runner module for executing all switch tests."""

import logging
from typing import Dict, Any, List
from utils.switch_api import SwitchAPI
from utils.command_manager import CommandManager
from utils.test_helpers import setup_test_environment

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_all_tests(switch_api: SwitchAPI) -> bool:
    """Run all switch tests.
    
    Args:
        switch_api: Switch API instance
        
    Returns:
        bool: True if all tests passed, False otherwise
    """
    try:
        # Import test modules here to avoid circular imports
        from tests.test_vlan import run as run_vlan_tests
        from tests.test_mac_learning import run as run_mac_tests
        from tests.test_spanning_tree import run as run_stp_tests
        
        # Initialize command manager
        command_manager = CommandManager()
        
        # Set up test environment
        setup_test_environment(switch_api, command_manager)
        
        # Run all test suites
        test_suites = [
            ("VLAN Tests", run_vlan_tests),
            ("MAC Learning Tests", run_mac_tests),
            ("Spanning Tree Tests", run_stp_tests)
        ]
        
        for suite_name, test_func in test_suites:
            logger.info(f"Running {suite_name}")
            try:
                test_func(switch_api, logger)
                logger.info(f"{suite_name} completed successfully")
            except Exception as e:
                logger.error(f"{suite_name} failed: {e}")
                return False
        
        logger.info("All test suites completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Unexpected error during test execution: {e}")
        return False

if __name__ == "__main__":
    # Example usage
    switch_api = SwitchAPI()  # Initialize with your connection details
    success = run_all_tests(switch_api)
    exit(0 if success else 1) 