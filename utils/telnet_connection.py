"""
Telnet connection implementation for L2 switch testing framework (Python 3.13+ compatible).
"""

import socket
import time
import re
import logging
from typing import Optional, Tuple, Any, List
from .connection import SwitchConnectionBase
from .ssh_tools import ConnectionError, CommandError

# Setup logger
logger = logging.getLogger(__name__)

class TelnetConnectionError(ConnectionError):
    """Exception raised for telnet connection issues."""
    pass

class TelnetConnection(SwitchConnectionBase):
    # Cisco IOS command prompts and patterns
    USER_PROMPT = r'[a-zA-Z0-9\-_]+>\s*$'
    ENABLE_PROMPT = r'[a-zA-Z0-9\-_]+#\s*$'
    CONFIG_PROMPT = r'[a-zA-Z0-9\-_]+\(config\)#\s*$'
    INTERFACE_PROMPT = r'[a-zA-Z0-9\-_]+\(config-if\)#\s*$'
    VLAN_PROMPT = r'[a-zA-Z0-9\-_]+\(config-vlan\)#\s*$'
    PASSWORD_PROMPT = r'Password:\s*$'
    USERNAME_PROMPT = r'Username:\s*$'
    INITIAL_PROMPTS = [
        r'Press RETURN to get started',
        r'Initial configuration dialog\? \[yes/no\]:',
        USER_PROMPT,
        ENABLE_PROMPT,
        USERNAME_PROMPT
    ]
    
    def __init__(self, host: str, username: str = None, password: str = None, 
                 port: int = 23, timeout: int = 10):
        """Initialize telnet connection to the switch."""
        if not host:
            raise ValueError("Host cannot be empty")
        if not isinstance(port, int) or port <= 0:
            raise ValueError("Port must be a positive integer")
        if not isinstance(timeout, (int, float)) or timeout <= 0:
            raise ValueError("Timeout must be a positive number")
        
        self.host = host
        self.username = username
        self.password = password
        self.port = port
        self.timeout = timeout
        self.socket = None
        self._connected = False
        self.in_enable_mode = False
        self.in_config_mode = False
        self.in_interface_mode = False
        self.in_vlan_mode = False
    
    def connect(self) -> None:
        """Establish telnet connection to the switch."""
        try:
            if self._connected:
                return
                
            logger.info(f"Connecting to switch via telnet at {self.host}:{self.port}")
            
            # Create socket connection
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(self.timeout)
            self.socket.connect((self.host, self.port))
            
            # Handle initial connection
            self._handle_initial_connection()
            
            # Try to enter enable mode
            try:
                self._enter_enable_mode()
            except TelnetConnectionError:
                # It's okay if we can't enter enable mode
                pass
            
            self._connected = True
            logger.info(f"Successfully connected to switch via telnet")
            
        except socket.timeout:
            raise TelnetConnectionError(f"Connection timeout to {self.host}:{self.port}")
        except ConnectionRefusedError:
            raise TelnetConnectionError(f"Connection refused to {self.host}:{self.port}")
        except Exception as e:
            raise TelnetConnectionError(f"Failed to connect to switch {self.host}:{self.port}: {str(e)}")

    def disconnect(self) -> None:
        """Close telnet connection."""
        try:
            if self.socket:
                self.socket.close()
        except Exception:
            pass
        
        self.socket = None
        self._connected = False
        self.in_enable_mode = False
        self.in_config_mode = False
        self.in_interface_mode = False
        self.in_vlan_mode = False
        logger.info("Telnet connection closed")

    def send_command(self, command: str, wait_time: float = 1) -> str:
        """Send command to switch and return output."""
        if not self.is_connected():
            raise TelnetConnectionError("Not connected to switch")
        
        try:
            logger.debug(f"Sending command: {command}")
            
            # Send command
            self.socket.send((command + '\r\n').encode('ascii'))
            
            # Wait for output
            time.sleep(wait_time)
            
            # Read response
            output = self._read_until_prompt()
            
            logger.debug(f"Command output: {output}")
            return output
            
        except Exception as e:
            raise CommandError(f"Failed to execute command '{command}': {str(e)}")

    def is_connected(self) -> bool:
        """Check if telnet connection is active."""
        return self._connected and self.socket is not None

    def _read_until_prompt(self, timeout: float = 10) -> str:
        """Read until a prompt is found."""
        output = ''
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                # Read available data
                data = self.socket.recv(1024).decode('utf-8', errors='ignore')
                if data:
                    output += data
                    
                    # Check for any prompt patterns
                    for pattern in [self.USER_PROMPT, self.ENABLE_PROMPT, self.CONFIG_PROMPT, 
                                   self.INTERFACE_PROMPT, self.VLAN_PROMPT]:
                        if re.search(pattern, output, re.MULTILINE):
                            return output
                            
            except socket.timeout:
                # No data available, continue reading
                continue
            except Exception:
                # Connection might be closed
                break
        
        return output

    def _handle_initial_connection(self):
        """Handle initial connection scenarios."""
        time.sleep(2)
        output = self._read_until_prompt()
        
        # Handle username prompt
        if re.search(self.USERNAME_PROMPT, output):
            if self.username:
                self.socket.send((self.username + '\r\n').encode('ascii'))
                time.sleep(1)
                output = self._read_until_prompt()
            else:
                raise TelnetConnectionError("Username required but not provided")
        
        # Handle password prompt
        if re.search(self.PASSWORD_PROMPT, output):
            if self.password:
                self.socket.send((self.password + '\r\n').encode('ascii'))
                time.sleep(1)
                output = self._read_until_prompt()
            else:
                # Try pressing enter if no password provided
                self.socket.send(b'\r\n')
                time.sleep(1)
                output = self._read_until_prompt()
        
        # Handle initial setup prompts
        if "Press RETURN to get started" in output:
            self.socket.send(b'\r\n')
            time.sleep(1)
            output = self._read_until_prompt()
        
        if "Initial configuration dialog" in output:
            self.socket.send(b'no\r\n')
            time.sleep(1)
            output = self._read_until_prompt()

    def _enter_enable_mode(self):
        """Enter enable mode if not already in it."""
        if self.in_enable_mode:
            return
        
        try:
            # Send enable command
            self.socket.send(b'enable\r\n')
            output = self._read_until_prompt()
            
            # If we get a password prompt, just press enter
            if re.search(self.PASSWORD_PROMPT, output):
                self.socket.send(b'\r\n')
                output = self._read_until_prompt()
            
            if not re.search(self.ENABLE_PROMPT, output):
                raise TelnetConnectionError("Failed to enter enable mode")
            
            self.in_enable_mode = True
            
        except Exception as e:
            raise TelnetConnectionError(f"Failed to enter enable mode: {str(e)}")

    def __enter__(self) -> 'TelnetConnection':
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type: Optional[type], exc_val: Optional[Exception], 
                 exc_tb: Optional[Any]) -> None:
        """Context manager exit."""
        self.disconnect() 