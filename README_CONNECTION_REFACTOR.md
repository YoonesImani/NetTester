# Connection Management Refactoring

## Overview

The connection management system has been refactored to be more object-oriented, cleaner, and easier to use. This document explains the changes and how to use the new system.

## What Changed

### Before (Problems)
- **Duplicate Functions**: Two different `get_connection()` functions with different purposes
- **Mixed Responsibilities**: Connection creation and management scattered across files
- **Manual Cleanup**: Required manual connection/disconnection management
- **Inconsistent Interfaces**: Different approaches for different connection types

### After (Solutions)
- **Single Responsibility**: Each class has a clear, single purpose
- **Factory Pattern**: `ConnectionFactory` handles connection creation
- **Context Managers**: Automatic cleanup with `with` statements
- **Unified Interface**: Consistent API across all connection types
- **Better OOP**: Proper inheritance, encapsulation, and abstraction

## New Architecture

```
ConnectionFactory (Factory Pattern)
    ↓ creates
ConnectionManager (Connection Management)
    ↓ manages
SwitchConnectionBase (Abstract Base)
    ↓ implemented by
SSHConnection / TelnetConnection / SerialConnection
```

## Usage Patterns

### 1. Context Manager (Recommended)

```python
from utils.connection_context import switch_connection

# Simple and clean - automatic cleanup
with switch_connection() as switch:
    result = switch.send_command("show version")
    print(result)

# With connection type override
with switch_connection(connection_type='telnet') as switch:
    result = switch.send_command("show interfaces")
    print(result)
```

### 2. Traditional OOP

```python
from utils.connection_manager import ConnectionManager
from utils.switch_api import SwitchAPI
from config.config_manager import ConfigManager

# Initialize components
config = ConfigManager()
conn_manager = ConnectionManager(config)
switch_api = SwitchAPI(conn_manager)

try:
    # Use the switch
    result = switch_api.send_command("show vlan brief")
    print(result)
finally:
    # Manual cleanup
    switch_api.disconnect()
```

### 3. Direct Connection Manager

```python
from utils.connection_manager import ConnectionManager
from config.config_manager import ConfigManager

config = ConfigManager()
conn_mgr = ConnectionManager(config)

try:
    # Send commands directly
    result = conn_mgr.send_command("show running-config")
    print(result)
finally:
    conn_mgr.disconnect()
```

## Key Classes

### ConnectionFactory
- **Purpose**: Creates connection instances based on type and configuration
- **Methods**: `create_connection(connection_type, config)`
- **Benefits**: Centralized creation logic, validation, and error handling

### ConnectionManager
- **Purpose**: Manages connection lifecycle and provides unified interface
- **Methods**: 
  - `get_connection(auto_connect=True)`
  - `connect()`
  - `disconnect()`
  - `is_connected()`
  - `send_command(command, wait_time=1)`
- **Benefits**: Connection pooling, automatic reconnection, unified API

### Context Managers
- **Purpose**: Provide automatic resource management
- **Functions**: `switch_connection()`, `connection_manager()`
- **Benefits**: Automatic cleanup, exception safety, cleaner code

## Benefits

### 1. **Cleaner Code**
- No more duplicate functions
- Consistent interfaces across connection types
- Automatic resource management

### 2. **Better Error Handling**
- Centralized validation in factory
- Proper exception hierarchy
- Graceful connection cleanup

### 3. **Easier Testing**
- Mockable interfaces
- Dependency injection
- Isolated components

### 4. **Extensibility**
- Easy to add new connection types
- Factory pattern for new implementations
- Pluggable architecture

## Migration Guide

### Old Code (Remove)
```python
from utils.ssh_tools import get_connection

conn = get_connection()
result = conn.send_command("show version")
conn.disconnect()
```

### New Code (Use)
```python
from utils.connection_context import switch_connection

with switch_connection() as switch:
    result = switch.send_command("show version")
```

## Examples

See `examples/connection_examples.py` for comprehensive usage examples.

## Configuration

The system uses the existing configuration structure:

```yaml
switch:
  connection_type: ssh  # or 'telnet', 'serial'
  ssh:
    host: 192.168.1.1
    username: admin
    password: password
    port: 22
    timeout: 10
```

## Best Practices

1. **Use Context Managers**: Prefer `with switch_connection()` for automatic cleanup
2. **Handle Exceptions**: Always wrap connection code in try/finally or use context managers
3. **Validate Configuration**: Check your config files before running
4. **Use Type Hints**: The new system has comprehensive type hints for better IDE support

## Testing

The refactored system is easier to test:

```python
# Mock the connection manager
with patch('utils.connection_manager.ConnectionManager') as mock_cm:
    mock_cm.return_value.send_command.return_value = "Mock response"
    
    with switch_connection() as switch:
        result = switch.send_command("test")
        assert result == "Mock response"
``` 