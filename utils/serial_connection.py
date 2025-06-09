"""
Serial connection implementation for L2 switch testing framework.
"""

import serial
import time
import re
import logging
from typing import Optional, Tuple, Any
from .connection import SwitchConnectionBase
from .ssh_tools import ConnectionError, CommandError
from config.config_manager import ConfigManager

# Setup logger
logger = logging.getLogger(__name__)

class SerialConnectionError(ConnectionError):
    """Exception raised for serial connection issues."""
    pass

class SerialConnection(SwitchConnectionBase):
    # Cisco IOS command prompts and patterns
    USER_PROMPT = r'[a-zA-Z0-9\-_]+>\s*$'
    ENABLE_PROMPT = r'[a-zA-Z0-9\-_]+#\s*$'
    CONFIG_PROMPT = r'[a-zA-Z0-9\-_]+\(config\)#\s*$'
    INTERFACE_PROMPT = r'[a-zA-Z0-9\-_]+\(config-if\)#\s*$'
    VLAN_PROMPT = r'[a-zA-Z0-9\-_]+\(config-vlan\)#\s*$'
    PASSWORD_PROMPT = r'Password:\s*$'
    INITIAL_PROMPTS = [
        r'Press RETURN to get started',
        r'Initial configuration dialog\? \[yes/no\]:',
        USER_PROMPT,
        ENABLE_PROMPT
    ]
    
    def __init__(self, port: str, baudrate: int = 9600, timeout: int = 10,
                 parity: str = 'N', stopbits: int = 1, bytesize: int = 8,
                 xonxoff: bool = False, rtscts: bool = False):
        """Initialize serial connection to the switch.
        
        Args:
            port: Serial port (e.g., 'COM1' on Windows, '/dev/ttyUSB0' on Linux)
            baudrate: Baud rate (default: 9600)
            timeout: Read timeout in seconds (default: 10)
            parity: Parity (default: 'N' for None)
            stopbits: Number of stop bits (default: 1)
            bytesize: Number of data bits (default: 8)
            xonxoff: Software flow control (default: False)
            rtscts: Hardware flow control (default: False)
            
        Raises:
            ValueError: If any parameter is invalid
        """
        if not port:
            raise ValueError("Port cannot be empty")
        if not isinstance(baudrate, int) or baudrate <= 0:
            raise ValueError("Baudrate must be a positive integer")
        if not isinstance(timeout, (int, float)) or timeout <= 0:
            raise ValueError("Timeout must be a positive number")
        if parity not in ['N', 'E', 'O', 'M', 'S']:
            raise ValueError("Invalid parity value")
        if not isinstance(stopbits, (int, float)) or stopbits not in [1, 1.5, 2]:
            raise ValueError("Invalid stopbits value")
        if not isinstance(bytesize, int) or bytesize not in [5, 6, 7, 8]:
            raise ValueError("Invalid bytesize value")
        
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.parity = parity
        self.stopbits = stopbits
        self.bytesize = bytesize
        self.xonxoff = xonxoff
        self.rtscts = rtscts
        self.serial = None
        self.in_enable_mode = False
        self.in_config_mode = False
        
        # Update prompt patterns to be more flexible
        self.USER_PROMPT = r'[a-zA-Z0-9\-_]+>\s*$'
        self.ENABLE_PROMPT = r'[a-zA-Z0-9\-_]+#\s*$'
        self.CONFIG_PROMPT = r'[a-zA-Z0-9\-_]+\(config\)#\s*$'
        self.INTERFACE_PROMPT = r'[a-zA-Z0-9\-_]+\(config-if\)#\s*$'
        self.VLAN_PROMPT = r'[a-zA-Z0-9\-_]+\(config-vlan\)#\s*$'
        self.PASSWORD_PROMPT = r'Password:\s*$'
        self.INITIAL_PROMPTS = [
            r'Press RETURN to get started',
            r'Initial configuration dialog\? \[yes/no\]:',
            self.USER_PROMPT,
            self.ENABLE_PROMPT
        ]
    
    def _read_until(self, expected_patterns: list, timeout: int = None) -> Tuple[str, str]:
        """
        Read from serial port until one of the expected patterns is found.
        
        Args:
            expected_patterns: List of regex patterns to match
            timeout: Read timeout in seconds (overrides default timeout)
            
        Returns:
            Tuple[str, str]: (complete output, matched pattern)
            
        Raises:
            SerialConnectionError: If timeout occurs before pattern match
        """
        if timeout is None:
            timeout = self.timeout
            
        start_time = time.time()
        output = ""
        
        while time.time() - start_time < timeout:
            if self.serial.in_waiting:
                try:
                    char = self.serial.read().decode('utf-8', errors='ignore')
                    output += char
                    
                    # Check for pattern matches
                    for pattern in expected_patterns:
                        if re.search(pattern, output, re.MULTILINE):
                            # Log the matched pattern for debugging
                            logger.debug(f"Matched pattern: {pattern}")
                            logger.debug(f"Output: {output}")
                            return output, pattern
                except UnicodeDecodeError:
                    continue
            time.sleep(0.1)
            
        # If we timeout, try to read any remaining data
        try:
            if self.serial.in_waiting:
                remaining = self.serial.read_all().decode('utf-8', errors='ignore')
                output += remaining
        except:
            pass
            
        # Log the full output for debugging
        logger.debug(f"Timeout waiting for patterns: {expected_patterns}")
        logger.debug(f"Got output: {output}")
            
        raise SerialConnectionError(f"Timeout waiting for patterns: {expected_patterns}. Got: {output}")
    
    def _handle_initial_connection(self) -> None:
        """
        Handle initial connection scenarios like auto-installation prompts.
        
        Raises:
            SerialConnectionError: If unable to get to a usable prompt
        """
        try:
            # Send break sequence and newlines to interrupt boot or get prompt
            self.serial.send_break()
            self.serial.write(b'\r\n\r\n')
            time.sleep(1)
            
            output, pattern = self._read_until(self.INITIAL_PROMPTS)
            
            if "Press RETURN to get started" in output:
                self.serial.write(b'\r\n')
                time.sleep(1)
                output, pattern = self._read_until(self.INITIAL_PROMPTS)
            
            if "Initial configuration dialog" in output:
                self.serial.write(b'no\r\n')  # Skip initial config
                time.sleep(1)
                output, pattern = self._read_until([self.USER_PROMPT, self.ENABLE_PROMPT])
            
        except Exception as e:
            raise SerialConnectionError(f"Failed to handle initial connection: {str(e)}")
    
    def _enter_enable_mode(self) -> None:
        """
        Enter enable mode if not already in it.
        
        Raises:
            SerialConnectionError: If unable to enter enable mode
        """
        if self.in_enable_mode:
            return
            
        try:
            # Send enable command
            self.serial.write(b'enable\n')
            output, pattern = self._read_until([self.ENABLE_PROMPT, self.PASSWORD_PROMPT])
            
            # If we get a password prompt, we don't need to enter a password
            # since we're using a non-secure connection
            if pattern == self.PASSWORD_PROMPT:
                # Just press enter to continue
                self.serial.write(b'\n')
                output, pattern = self._read_until([self.ENABLE_PROMPT])
            
            if pattern != self.ENABLE_PROMPT:
                raise SerialConnectionError("Failed to enter enable mode")
            
            self.in_enable_mode = True
            
        except SerialConnectionError:
            raise
        except Exception as e:
            raise SerialConnectionError(f"Failed to enter enable mode: {str(e)}")
    
    def connect(self) -> None:
        """
        Establish serial connection to the switch.
        
        Raises:
            SerialConnectionError: If connection fails
        """
        try:
            if self.serial and self.serial.is_open:
                return
                
            self.serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout,
                parity=self.parity,
                stopbits=self.stopbits,
                bytesize=self.bytesize,
                xonxoff=self.xonxoff,
                rtscts=self.rtscts
            )
            
            if not self.serial.is_open:
                self.serial.open()
            
            # Clear any buffered data
            self.serial.reset_input_buffer()
            self.serial.reset_output_buffer()
            
            # Handle initial connection and prompts
            self._handle_initial_connection()
            
            # Enter enable mode if needed
            if not self.in_enable_mode:
                self._enter_enable_mode()
            
            # Disable console logging to prevent output interference
            self.send_command("terminal length 0")
            self.send_command("terminal width 0")
            
        except serial.SerialException as e:
            raise SerialConnectionError(f"Failed to open serial port {self.port}: {str(e)}")
        except Exception as e:
            raise SerialConnectionError(f"Unexpected error connecting to serial port {self.port}: {str(e)}")
    
    def disconnect(self) -> None:
        """
        Close the serial connection.
        
        This method will not raise exceptions, it will attempt to close
        the connection gracefully.
        """
        try:
            if self.serial and self.serial.is_open:
                if self.in_config_mode:
                    try:
                        self.send_command("end")
                    except:
                        pass
                try:
                    self.send_command("terminal length 24")  # Restore default terminal settings
                except:
                    pass
                self.serial.close()
        except Exception:
            pass
        finally:
            self.serial = None
            self.in_enable_mode = False
            self.in_config_mode = False
    
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
            SerialConnectionError: If not connected
        """
        if not self.is_connected():
            raise SerialConnectionError("Serial port not connected")
        
        try:
            # Log the command being sent
            logger.debug(f"Sending command: {command}")
            
            # Ensure in enable mode for privileged commands
            if not self.in_enable_mode and command.strip() not in ['quit', 'exit']:
                logger.debug("Not in enable mode, attempting to enter enable mode")
                self._enter_enable_mode()
                if not self.in_enable_mode:
                    raise CommandError("Failed to enter enable mode")
                logger.debug("Successfully entered enable mode")
            
            # Handle config mode
            if command.strip() == "configure terminal":
                # Clear buffers before entering config mode
                self.serial.reset_input_buffer()
                self.serial.reset_output_buffer()
                time.sleep(0.5)  # Give time for buffers to clear
                
                # Send command and wait for config prompt
                self.serial.write(f"{command}\r\n".encode())
                output, pattern = self._read_until([self.CONFIG_PROMPT])
                
                # Only set config mode if we got the expected prompt
                if pattern == self.CONFIG_PROMPT:
                    self.in_config_mode = True
                    logger.debug("Entering config mode")
                else:
                    raise CommandError("Failed to enter config mode")
                
                # Return the output without the prompt
                lines = output.splitlines()
                if lines and lines[0].strip() == command.strip():
                    lines = lines[1:]
                if lines and re.match(self.CONFIG_PROMPT, lines[-1]):
                    lines = lines[:-1]
                return '\n'.join(lines).strip()
                
            elif command.strip() in ["end", "exit"] and self.in_config_mode:
                self.in_config_mode = False
                logger.debug("Exiting config mode")
            
            # Send command
            self.serial.write(f"{command}\r\n".encode())
            
            # Determine expected prompt
            if self.in_config_mode:
                expected_prompt = self.CONFIG_PROMPT
            elif self.in_enable_mode:
                expected_prompt = self.ENABLE_PROMPT
            else:
                expected_prompt = self.USER_PROMPT
            
            # Wait for command output
            output, _ = self._read_until([expected_prompt])
            
            # Remove command echo and trailing prompt
            lines = output.splitlines()
            if lines and lines[0].strip() == command.strip():
                lines = lines[1:]
            if lines and (re.match(expected_prompt, lines[-1]) or 
                        re.match(self.USER_PROMPT, lines[-1]) or 
                        re.match(self.ENABLE_PROMPT, lines[-1]) or
                        re.match(self.CONFIG_PROMPT, lines[-1])):
                lines = lines[:-1]
            
            result = '\n'.join(lines).strip()
            
            # Log the command output
            logger.debug(f"Command output:\n{result}")
            
            return result
            
        except serial.SerialException as e:
            error_msg = f"Serial communication error: {str(e)}"
            logger.error(error_msg)
            raise CommandError(error_msg)
        except UnicodeDecodeError:
            error_msg = f"Failed to decode command output for '{command}'"
            logger.error(error_msg)
            raise CommandError(error_msg)
        except Exception as e:
            error_msg = f"Failed to execute command '{command}': {str(e)}"
            logger.error(error_msg)
            raise CommandError(error_msg)
    
    def is_connected(self) -> bool:
        """
        Check if serial connection is active.
        
        Returns:
            bool: True if connected, False otherwise
        """
        try:
            return self.serial is not None and self.serial.is_open
        except Exception:
            return False

    def __enter__(self) -> 'SerialConnection':
        """Enter the runtime context for using the connection."""
        self.connect()
        return self

    def __exit__(self, exc_type: Optional[type], exc_val: Optional[Exception], 
                 exc_tb: Optional[Any]) -> None:
        """Exit the runtime context and ensure connection is closed."""
        self.disconnect() 