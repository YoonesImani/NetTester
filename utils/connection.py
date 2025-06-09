"""
Base connection classes for L2 switch testing framework.
"""

from abc import ABC, abstractmethod
from typing import Optional

class SwitchConnectionBase(ABC):
    """Abstract base class for switch connections."""
    
    @abstractmethod
    def connect(self) -> None:
        """Establish connection to the switch."""
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """Close the connection."""
        pass
    
    @abstractmethod
    def send_command(self, command: str, wait_time: float = 5) -> str:
        """
        Send command to switch and return output.
        
        Args:
            command: Command to send
            wait_time: Time to wait for output in seconds
            
        Returns:
            str: Command output
        """
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if connection is active."""
        pass 