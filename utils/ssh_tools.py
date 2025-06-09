"""
SSH connection tools for L2 switch testing framework.
"""

import paramiko
import time
from typing import Optional, Union, Dict, Any
from config.config_manager import ConfigManager
from .connection import SwitchConnectionBase

class ConnectionError(Exception):
    """Base exception for connection errors."""
    pass

class SSHConnectionError(ConnectionError):
    """Exception raised for SSH connection issues."""
    pass

class CommandError(Exception):
    """Exception raised for command execution issues."""
    pass

class SSHConnection(SwitchConnectionBase):
    def __init__(self, host: str, username: str, password: str, port: int = 22, timeout: int = 10):
        """
        Initialize SSH connection to the switch.
        
        Args:
            host: Switch IP address or hostname
            username: SSH username
            password: SSH password
            port: SSH port (default: 22)
            timeout: Connection timeout in seconds (default: 10)
            
        Raises:
            ValueError: If any required parameter is missing or invalid
        """
        if not host:
            raise ValueError("Host cannot be empty")
        if not username:
            raise ValueError("Username cannot be empty")
        if not password:
            raise ValueError("Password cannot be empty")
        if not isinstance(port, int) or port <= 0:
            raise ValueError("Port must be a positive integer")
        if not isinstance(timeout, (int, float)) or timeout <= 0:
            raise ValueError("Timeout must be a positive number")
            
        self.host = host
        self.username = username
        self.password = password
        self.port = port
        self.timeout = timeout
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.shell = None
    
    def connect(self) -> None:
        """
        Establish SSH connection and open shell.
        
        Raises:
            SSHConnectionError: If connection fails
        """
        try:
            self.client.connect(
                hostname=self.host,
                username=self.username,
                password=self.password,
                port=self.port,
                timeout=self.timeout
            )
            self.shell = self.client.invoke_shell()
            # Wait for initial prompt
            time.sleep(2)
            self.shell.recv(10000)
        except paramiko.AuthenticationException:
            raise SSHConnectionError(f"Authentication failed for {self.username}@{self.host}")
        except paramiko.SSHException as e:
            raise SSHConnectionError(f"SSH protocol error: {str(e)}")
        except Exception as e:
            raise SSHConnectionError(f"Failed to connect to switch {self.host}: {str(e)}")
    
    def send_command(self, command: str, wait_time: float = 1) -> str:
        """
        Send command to switch and return output.
        
        Args:
            command: Command to send
            wait_time: Time to wait for output in seconds
            
        Returns:
            str: Command output
            
        Raises:
            CommandError: If command execution fails
            SSHConnectionError: If not connected to switch
        """
        if not self.is_connected():
            raise SSHConnectionError("Not connected to switch")
        
        try:
            self.shell.send(command + '\n')
            time.sleep(wait_time)
            output = self.shell.recv(10000).decode('utf-8')
            return output
        except UnicodeDecodeError:
            raise CommandError(f"Failed to decode command output for '{command}'")
        except Exception as e:
            raise CommandError(f"Failed to execute command '{command}': {str(e)}")
    
    def disconnect(self) -> None:
        """
        Close SSH connection.
        
        This method will not raise exceptions, it will attempt to close
        both shell and client connections gracefully.
        """
        try:
            if self.shell:
                self.shell.close()
        except Exception:
            pass
        
        try:
            if self.client:
                self.client.close()
        except Exception:
            pass
        
        self.shell = None
    
    def is_connected(self) -> bool:
        """
        Check if SSH connection is active.
        
        Returns:
            bool: True if connected, False otherwise
        """
        try:
            transport = self.client.get_transport() if self.client else None
            return self.shell is not None and transport is not None and transport.is_active()
        except Exception:
            return False

def get_connection() -> SwitchConnectionBase:
    """
    Create and return a configured switch connection.
    
    Returns:
        SwitchConnectionBase: Connected switch instance
        
    Raises:
        ConnectionError: If connection creation fails
        ValueError: If configuration is invalid
    """
    try:
        config = ConfigManager()
        conn_type = config.get('switch', 'connection_type', default='ssh')
        
        if conn_type == 'ssh':
            creds = config.get('switch', 'ssh')
            if not isinstance(creds, dict):
                raise ValueError("SSH configuration must be a dictionary")
            
            required_fields = ['host', 'username', 'password']
            missing_fields = [field for field in required_fields if field not in creds]
            if missing_fields:
                raise ValueError(f"Missing required SSH configuration fields: {', '.join(missing_fields)}")
            
            timeout = creds.get('timeout', 10)
            conn = SSHConnection(
                host=creds['host'],
                username=creds['username'],
                password=creds['password'],
                port=creds.get('port', 22),
                timeout=timeout
            )
        else:  # serial
            from .serial_connection import SerialConnection
            serial_config = config.get('switch', 'serial')
            if not isinstance(serial_config, dict):
                raise ValueError("Serial configuration must be a dictionary")
            
            if 'port' not in serial_config:
                raise ValueError("Missing required serial configuration field: port")
            
            conn = SerialConnection(
                port=serial_config['port'],
                baudrate=serial_config.get('baudrate', 9600),
                timeout=serial_config.get('timeout', 10),
                parity=serial_config.get('parity', 'N'),
                stopbits=serial_config.get('stopbits', 1),
                bytesize=serial_config.get('bytesize', 8),
                xonxoff=serial_config.get('xonxoff', False),
                rtscts=serial_config.get('rtscts', False)
            )
        
        conn.connect()
        return conn
        
    except (ValueError, ConnectionError):
        raise
    except Exception as e:
        raise ConnectionError(f"Failed to create connection: {str(e)}")
