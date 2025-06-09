# Memory Bank

## Project Structure
```
l2_switch_tester/
├── config/
│   ├── config.yaml           # Main configuration file
│   ├── switch_commands.json  # Switch commands and responses
│   └── config_manager.py     # Configuration management
├── utils/
│   ├── command_manager.py    # Command management and formatting
│   ├── switch_api.py         # Switch API interface
│   └── test_helpers.py       # Common test helper functions
├── tests/
│   ├── test_vlan.py          # VLAN tests
│   ├── test_mac_learning.py  # MAC learning tests
│   ├── test_spanning_tree.py # Spanning tree tests
│   └── test_runner.py        # Test execution runner
└── main.py                   # Main entry point
```

## Test Architecture

### Command Management
- Commands are stored in `switch_commands.json`
- Organized by categories (vlan_commands, mac_commands, etc.)
- Each command has:
  - command: The actual command string with parameters
  - expected_response: Expected response pattern
  - parse_pattern: Regex pattern for parsing output
  - subcommands: Nested commands if applicable

### Test Structure
Each test module follows this pattern:
```python
def verify_feature(switch_api: SwitchAPI, command_manager: CommandManager, **params) -> bool:
    """Verify a specific feature.
    
    Args:
        switch_api: Switch API instance
        command_manager: Command manager instance
        **params: Feature-specific parameters
        
    Returns:
        bool: True if verification successful
    """
    # Implementation

def test_feature(switch_api: SwitchAPI, command_manager: CommandManager) -> None:
    """Test a specific feature."""
    # Test implementation
    assert verify_feature(...), "Error message"

def run(switch_api: SwitchAPI, logger: logging.Logger) -> bool:
    """Run all tests in the module."""
    command_manager = CommandManager()
    try:
        setup_test_environment(switch_api, command_manager)
        # Run tests
        return True
    except Exception as e:
        logger.error(f"Test failed: {e}")
        return False
```

### Test Runner
- Centralized test execution
- Consistent environment setup
- Proper error handling and logging
- Test suite organization

## Adding New Tests

1. Add commands to `switch_commands.json`:
```json
{
    "new_feature_commands": {
        "command_name": {
            "command": "command {param}",
            "expected_response": "Expected response",
            "parse_pattern": "pattern"
        }
    }
}
```

2. Create test module following the structure:
```python
"""New feature test module."""

import logging
from utils.command_manager import CommandManager
from utils.switch_api import SwitchAPI
from utils.test_helpers import (
    clear_system_messages,
    setup_test_environment,
    verify_command_response
)

# Test functions
def verify_feature(...):
    pass

def test_feature(...):
    pass

def run(switch_api: SwitchAPI, logger: logging.Logger) -> bool:
    pass
```

3. Add to test runner:
```python
from tests.new_feature import run as run_new_feature_tests

test_suites = [
    # ... existing suites ...
    ("New Feature Tests", run_new_feature_tests)
]
```

## Best Practices
1. Use command manager for all switch commands
2. Follow consistent naming conventions
3. Include proper error handling
4. Add comprehensive logging
5. Use type hints and docstrings
6. Keep test functions focused and atomic
7. Use helper functions for common operations 