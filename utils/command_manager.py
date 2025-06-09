import json
import logging
import os
import re
from typing import Dict, Any, Optional, List
from pathlib import Path

class CommandManager:
    """Manages switch commands and their expected responses."""
    
    def __init__(self, config_path: str = "config/switch_commands.json"):
        """Initialize the command manager with the command configuration file.
        
        Args:
            config_path: Path to the JSON configuration file containing command definitions
        """
        self.logger = logging.getLogger(__name__)
        self.config_path = config_path
        self.commands = self._load_commands()

    def _load_commands(self) -> Dict[str, Any]:
        """Load commands from the JSON configuration file."""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Command configuration file not found at {self.config_path}")
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON in command configuration file {self.config_path}")
        except Exception as e:
            self.logger.error(f"Failed to load command configuration: {e}")
            return {}

    def get_command(self, category: str, command_name: str) -> Dict[str, Any]:
        """Get a specific command configuration."""
        try:
            return self.commands[category][command_name]
        except KeyError:
            raise KeyError(f"Command {command_name} not found in category {category}")

    def format_command(self, category: str, command_name: str, **kwargs) -> str:
        """Format a command with the given parameters.
        
        Args:
            category: Command category (e.g., 'vlan_commands')
            command_name: Name of the command within the category
            **kwargs: Parameters to format the command string
            
        Returns:
            Formatted command string
            
        Raises:
            KeyError: If category or command not found
            ValueError: If required parameters are missing
        """
        try:
            command_def = self.commands[category][command_name]
            command = command_def['command']
            
            # Format the command with provided parameters
            try:
                return command.format(**kwargs)
            except KeyError as e:
                raise ValueError(f"Missing required parameter: {e}")
                
        except KeyError as e:
            raise KeyError(f"Command not found: {category}.{command_name}")

    def get_expected_response(self, category: str, command_name: str, **kwargs) -> str:
        """Get the expected response for a command.
        
        Args:
            category: Command category
            command_name: Name of the command
            **kwargs: Parameters to format the response string
            
        Returns:
            Expected response string
        """
        try:
            response = self.commands[category][command_name]['expected_response']
            return response.format(**kwargs)
        except KeyError:
            return ""

    def get_parse_pattern(self, category: str, command_name: str) -> Optional[str]:
        """Get the parse pattern for a command's response.
        
        Args:
            category: Command category
            command_name: Name of the command
            
        Returns:
            Parse pattern string or None if not defined
        """
        try:
            return self.commands[category][command_name].get('parse_pattern')
        except KeyError:
            return None

    def get_valid_modes(self, category: str, command_name: str) -> List[str]:
        """Get valid modes for a command.
        
        Args:
            category: Command category
            command_name: Name of the command
            
        Returns:
            List of valid modes
        """
        try:
            return self.commands[category][command_name].get('valid_modes', [])
        except KeyError:
            return []

    def get_subcommands(self, category: str, command_name: str) -> Dict[str, Any]:
        """Get subcommands for a command.
        
        Args:
            category: Command category
            command_name: Name of the command
            
        Returns:
            Dictionary of subcommand definitions
        """
        try:
            return self.commands[category][command_name].get('subcommands', {})
        except KeyError:
            return {}

    def verify_response(self, category: str, command_name: str, 
                       response: str, **kwargs) -> bool:
        """Verify if a response matches the expected pattern.
        
        Args:
            category: Command category
            command_name: Name of the command
            response: Response to verify
            **kwargs: Parameters for response formatting
            
        Returns:
            True if response matches expected pattern, False otherwise
        """
        expected = self.get_expected_response(category, command_name, **kwargs)
        if not expected:
            return True
            
        return expected in response

    def parse_response(self, category: str, command_name: str, response: str) -> List[str]:
        """Parse the command response using the configured pattern."""
        pattern = self.get_parse_pattern(category, command_name)
        if not pattern:
            return [response]
        
        matches = re.finditer(pattern, response)
        return [match.group(0) for match in matches]

    def update_command(self, category: str, command_name: str, 
                      command: str, expected_response: str, 
                      parse_pattern: Optional[str] = None,
                      subcommands: Optional[Dict[str, Any]] = None) -> None:
        """Update or add a new command configuration."""
        if category not in self.commands:
            self.commands[category] = {}
        
        self.commands[category][command_name] = {
            'command': command,
            'expected_response': expected_response
        }
        
        if parse_pattern:
            self.commands[category][command_name]['parse_pattern'] = parse_pattern
        if subcommands:
            self.commands[category][command_name]['subcommands'] = subcommands

    def save_commands(self) -> None:
        """Save the current command configuration to the JSON file."""
        with open(self.config_path, 'w') as f:
            json.dump(self.commands, f, indent=4)

    def add_new_category(self, category: str) -> None:
        """Add a new command category."""
        if category not in self.commands:
            self.commands[category] = {}
            self.save_commands()

    def remove_command(self, category: str, command_name: str) -> None:
        """Remove a command from the configuration."""
        if category in self.commands and command_name in self.commands[category]:
            del self.commands[category][command_name]
            self.save_commands()

# command_manager = CommandManager()
# command_manager.update_command(
#     category="vlan_commands",
#     command_name="create_vlan",
#     command="new vlan command {vlan_id}",
#     expected_response="New expected response",
#     parse_pattern="new pattern"
# )
# command_manager.save_commands()

# command_manager.add_new_category("new_feature_commands")
# command_manager.update_command(
#     category="new_feature_commands",
#     command_name="new_command",
#     command="new command {param}",
#     expected_response="Expected response",
#     parse_pattern="pattern"
# )
# command_manager.save_commands() 