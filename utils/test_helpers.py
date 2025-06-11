"""Common test helper functions for switch testing."""

import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from utils.switch_api import SwitchAPI
from utils.command_manager import CommandManager
import time

logger = logging.getLogger(__name__)

class TestStatus(Enum):
    """Test status enumeration"""
    PASS = "PASS"
    FAIL = "FAIL"
    ERROR = "ERROR"

@dataclass
class TestResult:
    """Test result data class"""
    name: str
    status: TestStatus
    message: str

def clear_system_messages(switch_api: SwitchAPI, command_manager: CommandManager) -> None:
    """Clear system messages from the switch.
    
    Args:
        switch_api: Switch API instance
        command_manager: Command manager instance
    """
    try:
        # Commenting out clear logging command as it's causing issues
        clear_cmd = command_manager.format_command('system_commands', 'clear_system_messages')
        logger.debug(f"[COMMAND] Attempting to send: {clear_cmd}")
        # switch_api.send_command(clear_cmd)
        logger.info("Skipping clear system messages")
    except Exception as e:
        logger.error(f"Failed to clear system messages: {e}")
        raise

def setup_test_environment(switch_api: SwitchAPI, command_manager: CommandManager) -> None:
    """Set up the test environment by clearing switch configuration.
    
    Args:
        switch_api: Switch API instance
        command_manager: Command manager instance
    """
    try:
        # Enter configuration mode with retry
        max_retries = 3
        for attempt in range(max_retries):
            try:
                logger.debug(f"[ATTEMPT] Entering config mode (attempt {attempt + 1}/{max_retries})")
                
                # First ensure we're in enable mode
                enable_cmd = command_manager.format_command('system_commands', 'enable')
                logger.debug(f"[COMMAND] Attempting to send: {enable_cmd}")
                switch_api.send_command(enable_cmd)
                time.sleep(2)  # Wait for enable mode
                
                # Then enter configuration mode
                config_cmd = command_manager.format_command('system_commands', 'configure_terminal')
                logger.debug(f"[COMMAND] Attempting to send: {config_cmd}")
                response = switch_api.send_command(config_cmd)
                logger.debug(f"[RESPONSE] Received: {response}")
                time.sleep(2)  # Wait for config mode
                
                # If we get here, config mode was successful
                logger.info("Successfully entered configuration mode")
                break
                
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")
                if attempt == max_retries - 1:
                    raise
                time.sleep(2)  # Increased wait time between retries
        
        # Exit configuration mode
        logger.debug("Exiting configuration mode")
        switch_api.send_command("end")
        time.sleep(1)  # Give time for the command to take effect
        
        logger.info("Test environment setup completed")
    except Exception as e:
        logger.error(f"Failed to setup test environment: {e}")
        logger.error("[DEBUG] Full error details:", exc_info=True)
        raise

def verify_command_response(switch_api: SwitchAPI, command_manager: CommandManager,
                          category: str, command_name: str, **kwargs) -> bool:
    """Verify a command's response.
    
    Args:
        switch_api: Switch API instance
        command_manager: Command manager instance
        category: Command category
        command_name: Command name
        **kwargs: Parameters for command formatting
        
    Returns:
        True if response matches expected pattern, False otherwise
    """
    try:
        cmd = command_manager.format_command(category, command_name, **kwargs)
        logger.debug(f"[COMMAND] Attempting to send: {cmd}")
        response = switch_api.send_command(cmd)
        logger.debug(f"[RESPONSE] Received: {response}")
        return command_manager.verify_response(category, command_name, response, **kwargs)
    except Exception as e:
        logger.error(f"Failed to verify command response: {e}")
        return False 