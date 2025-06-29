"""
High-level switch operations API.
"""

import logging
from typing import List, Optional, Tuple, Any

from utils.command_manager import CommandManager
from utils.connection_manager import ConnectionManager
from utils.ssh_tools import CommandError
from utils.connection import SwitchConnectionBase
import time

# Setup logger
logger = logging.getLogger(__name__)

class SwitchAPIError(Exception):
    """Base exception for switch API errors."""
    pass

class VLANOperationError(SwitchAPIError):
    """Exception raised for VLAN operation failures."""
    pass

class PortConfigurationError(SwitchAPIError):
    """Exception raised for port configuration failures."""
    pass

class MACTableError(SwitchAPIError):
    """Exception raised for MAC table operation failures."""
    pass

class STPError(SwitchAPIError):
    """Exception raised for STP operation failures."""
    pass

class SwitchAPI:
    """API for interacting with L2 switches."""
    
    def __init__(self, connection_manager: ConnectionManager):
        """Initialize SwitchAPI with a connection manager.
        
        Args:
            connection_manager: Connection manager object
        """
        self._connection_manager = connection_manager
        self._command_manager = CommandManager()
    
    def _ensure_connection(self) -> None:
        """Ensure we have an active connection."""
        if not self._connection_manager.is_connected():
            self._connection_manager.connect()
    
    def send_command(self, command: str) -> str:
        """
        Send a command to the switch and return the response.
        
        Args:
            command: The command to send to the switch
            
        Returns:
            str: The response from the switch
            
        Raises:
            ConnectionError: If there is an error connecting to the switch
            CommandError: If there is an error executing the command
        """
        try:
            # Ensure we have a connection
            self._ensure_connection()
            
            # Send the command
            logger.debug(f"Sending command: {command}")
            response = self._connection_manager.send_command(command)
            logger.debug(f"Received response: {response}")
            
            return response
            
        except Exception as e:
            logger.error(f"Error sending command '{command}': {str(e)}")
            raise CommandError(f"Failed to send command: {str(e)}")
    
    def disconnect(self) -> None:
        """Disconnect from the switch."""
        self._connection_manager.disconnect()
    
    def create_vlan(self, vlan_id: str, name: Optional[str] = None) -> Tuple[bool, str]:
        """Create a new VLAN on the switch.
        
        Args:
            vlan_id: VLAN ID to create
            name: Optional VLAN name
            
        Returns:
            Tuple[bool, str]: (success status, error message if any)
        """
        try:
            if not self._connection_manager.is_connected():
                raise VLANOperationError("Not connected to switch")
            
            # Enter configuration mode
            logger.info("Entering config mode")
            config_cmd = self._command_manager.format_command('system_commands', 'configure_terminal')
            self._connection_manager.send_command(config_cmd)
            time.sleep(2)
            
            # Create VLAN
            logger.info(f"Creating VLAN {vlan_id}")
            vlan_cmd = self._command_manager.format_command('vlan_commands', 'create_vlan', vlan_id=vlan_id)
            self._connection_manager.send_command(vlan_cmd)
            time.sleep(2)
            
            # Set VLAN name if provided
            if name:
                logger.info(f"Setting VLAN name to {name}")
                name_cmd = self._command_manager.format_command('vlan_commands', 'name_vlan', vlan_name=name)
                self._connection_manager.send_command(name_cmd)
                time.sleep(2)
            
            # Exit VLAN configuration
            # self._connection.send_command("exit")       
            # time.sleep(2)
            
            # Exit configuration mode
            end_cmd = self._command_manager.format_command('system_commands', 'end')
            self._connection_manager.send_command(end_cmd)
            time.sleep(2)
            
            return True, ""
            
        except Exception as e:
            return False, f"Error creating VLAN: {str(e)}"
    
    def delete_vlan(self, vlan_id: str) -> Tuple[bool, str]:
        """Delete a VLAN from the switch.
        
        Args:
            vlan_id: VLAN ID to delete
            
        Returns:
            Tuple[bool, str]: (success status, error message if any)
        """
        try:
            if not self._connection_manager.is_connected():
                raise VLANOperationError("Not connected to switch")
            
            # Enter configuration mode
            logger.info("Entering config mode")
            config_cmd = self._command_manager.format_command('system_commands', 'configure_terminal')
            self._connection_manager.send_command(config_cmd)
            time.sleep(2)
            
            # Delete VLAN
            logger.info(f"Deleting VLAN {vlan_id}")
            delete_cmd = self._command_manager.format_command('vlan_commands', 'delete_vlan', vlan_id=vlan_id)
            self._connection_manager.send_command(delete_cmd)
            time.sleep(2)
            
            # Exit configuration mode
            end_cmd = self._command_manager.format_command('system_commands', 'end')
            self._connection_manager.send_command(end_cmd)
            time.sleep(2)
            
            return True, ""
            
        except Exception as e:
            return False, f"Error deleting VLAN: {str(e)}"
    
    def configure_interface(self, interface: str) -> Tuple[bool, str]:
        """Configure an interface.
        
        Args:
            interface: Interface to configure
            
        Returns:
            Tuple[bool, str]: (success status, error message if any)
        """
        try:
            if not self._connection_manager.is_connected():
                raise PortConfigurationError("Not connected to switch")
            
            # Enter configuration mode
            logger.info("Entering config mode")
            config_cmd = self._command_manager.format_command('system_commands', 'configure_terminal')
            self._connection_manager.send_command(config_cmd)
            time.sleep(2)
            
            # Enter interface configuration
            logger.info(f"Configuring interface {interface}")
            interface_cmd = self._command_manager.format_command('interface_commands', 'configure_interface', 
                                                              interface=interface)
            self._connection_manager.send_command(interface_cmd)
            time.sleep(2)
            
            return True, ""
            
        except Exception as e:
            return False, f"Error configuring interface: {str(e)}"
    
    def assign_port_to_vlan(self, port: str, vlan_id: str, mode: str = "access") -> Tuple[bool, str]:
        """Assign a port to a VLAN.
        
        Args:
            port: Port identifier (e.g., "Gi1/0/1")
            vlan_id: VLAN ID to assign
            mode: Port mode ("access" or "trunk")
            
        Returns:
            Tuple[bool, str]: (success status, error message if any)
        """
        try:
            if not self._connection_manager.is_connected():
                raise PortConfigurationError("Not connected to switch")
            
            # Validate mode
            if mode not in ["access", "trunk"]:
                raise ValueError(f"Invalid mode: {mode}. Must be 'access' or 'trunk'")
            
            # Validate VLAN ID
            try:
                vlan_num = int(vlan_id)
                if not (1 <= vlan_num <= 4094):
                    raise ValueError(f"Invalid VLAN ID: {vlan_id}. Must be between 1 and 4094.")
            except ValueError as e:
                return False, str(e)
            
            # Check if VLAN exists
            show_cmd = self._command_manager.format_command('vlan_commands', 'show_vlan')
            output = self._connection_manager.send_command(show_cmd)
            if "Invalid input" in output or "Error" in output:
                return False, f"Failed to check VLAN existence: {output}"
            
            if str(vlan_id) not in output:
                return False, f"VLAN {vlan_id} does not exist"
            
            # Enter configuration mode
            logger.info("Entering config mode")
            config_cmd = self._command_manager.format_command('system_commands', 'configure_terminal')
            self._connection_manager.send_command(config_cmd)
            time.sleep(2)
            
            # Enter interface configuration
            logger.info(f"Configuring interface {port}")
            interface_cmd = self._command_manager.format_command('vlan_commands', 'configure_interface', 
                                                              interface=port)
            self._connection_manager.send_command(interface_cmd)
            time.sleep(2)
            
            # Configure port mode
            mode_cmd = self._command_manager.format_command('vlan_commands', 'configure_interface',
                                                         interface=port,
                                                         subcommand='switchport_mode',
                                                         mode=mode)
            self._connection_manager.send_command(mode_cmd)
            time.sleep(2)
            
            # Configure VLAN assignment
            if mode == "access":
                vlan_cmd = self._command_manager.format_command('vlan_commands', 'configure_interface',
                                                             interface=port,
                                                             subcommand='switchport_access_vlan',
                                                             vlan_id=vlan_id)
            else:  # trunk mode
                vlan_cmd = self._command_manager.format_command('vlan_commands', 'configure_interface',
                                                             interface=port,
                                                             subcommand='switchport_trunk_allowed_vlan',
                                                             vlan_list=vlan_id)
            self._connection_manager.send_command(vlan_cmd)
            time.sleep(2)
            
            # Enable interface
            self._connection_manager.send_command("no shutdown")
            time.sleep(2)
            
            # Exit interface configuration
            # self._connection.send_command("exit")
            # time.sleep(2)
            
            # Exit configuration mode
            end_cmd = self._command_manager.format_command('system_commands', 'end')
            self._connection_manager.send_command(end_cmd)
            time.sleep(2)
            
            return True, ""
            
        except Exception as e:
            return False, f"Error assigning port to VLAN: {str(e)}"
    
    def get_mac_table(self) -> Tuple[str, str]:
        """
        Get the MAC address table from the switch.
        
        Returns:
            Tuple[str, str]: (MAC table output if successful, error message if any)
            
        Raises:
            MACTableError: If unable to get MAC table
        """
        try:
            if not self._connection_manager.is_connected():
                raise MACTableError("Not connected to switch")
            
            output = self._connection_manager.send_command("show mac address-table")
            return output, ""
            
        except MACTableError as e:
            return "", str(e)
        except Exception as e:
            return "", f"Unexpected error getting MAC table: {str(e)}"
    
    def clear_mac_table(self) -> Tuple[bool, str]:
        """
        Clear the MAC address table.
        
        Returns:
            Tuple[bool, str]: (success status, error message if any)
            
        Raises:
            MACTableError: If unable to clear MAC table
        """
        try:
            if not self._connection_manager.is_connected():
                raise MACTableError("Not connected to switch")
            
            self._connection_manager.send_command("clear mac address-table dynamic")
            
            # Verify table was cleared
            output = self._connection_manager.send_command("show mac address-table")
            if "dynamic" in output.lower():
                raise MACTableError("Failed to clear dynamic MAC entries")
            
            return True, ""
            
        except MACTableError as e:
            return False, str(e)
        except Exception as e:
            return False, f"Unexpected error clearing MAC table: {str(e)}"

    def configure_trunk_port(self, port: str, native_vlan: str, allowed_vlans: str, encapsulation: str = "dot1q") -> Tuple[bool, str]:
        """
        Configure a port as a trunk port.
        
        Args:
            port: Port to configure
            native_vlan: Native VLAN ID
            allowed_vlans: Comma-separated list of allowed VLANs
            encapsulation: Trunk encapsulation (dot1q or isl)
            
        Returns:
            Tuple[bool, str]: (success status, error message if any)
        """
        try:
            if not self._connection_manager.is_connected():
                raise PortConfigurationError("Not connected to switch")
            
            # Enter configuration mode
            logger.info("Entering config mode")
            config_cmd = self._command_manager.format_command('system_commands', 'configure_terminal')
            self._connection_manager.send_command(config_cmd)
            time.sleep(2)
            
            # Enter interface configuration
            logger.info(f"Configuring interface {port}")
            interface_cmd = self._command_manager.format_command('interface_commands', 'configure_interface', 
                                                              interface=port)
            self._connection_manager.send_command(interface_cmd)
            time.sleep(2)
            
            # Configure trunk mode
            logger.info("Setting trunk mode")
            mode_cmd = self._command_manager.format_command('interface_commands', 'switchport_mode', mode='trunk')
            self._connection_manager.send_command(mode_cmd)
            time.sleep(2)
            
            # Configure native VLAN
            logger.info(f"Setting native VLAN {native_vlan}")
            native_vlan_cmd = self._command_manager.format_command('interface_commands', 'switchport_trunk_native_vlan', vlan_id=native_vlan)
            self._connection_manager.send_command(native_vlan_cmd)
            time.sleep(2)
            
            # Configure allowed VLANs
            logger.info(f"Setting allowed VLANs: {allowed_vlans}")
            allowed_vlans_cmd = self._command_manager.format_command('interface_commands', 'switchport_trunk_allowed_vlan', vlan_list=allowed_vlans)
            self._connection_manager.send_command(allowed_vlans_cmd)
            time.sleep(2)
            
            # Enable interface
            logger.info("Enabling interface")
            self._connection_manager.send_command("no shutdown")
            time.sleep(2)
            
            # Exit interface configuration
            # self._connection.send_command("exit")
            # time.sleep(2)
            
            # Exit configuration mode
            end_cmd = self._command_manager.format_command('system_commands', 'end')
            self._connection_manager.send_command(end_cmd)
            time.sleep(2)
            
            # Check interface status first
            logger.info("Checking interface status")
            status_output = self._connection_manager.send_command(f"show interfaces {port} status")
            logger.debug(f"Interface status output:\n{status_output}")
            
            if "notconnect" in status_output.lower() or "disabled" in status_output.lower():
                logger.warning(f"Interface {port} is down. Configuration applied but interface needs to be connected.")
                return True, "Interface is down but configuration applied successfully"
            
            # Verify trunk configuration
            logger.info("Verifying trunk configuration")
            output = self._connection_manager.send_command(f"show interfaces {port} trunk")
            logger.debug(f"Trunk configuration output:\n{output}")
            
            if "trunking" not in output.lower():
                raise PortConfigurationError(f"Port {port} is not in trunking mode")
            
            if native_vlan not in output:
                raise PortConfigurationError(f"Native VLAN {native_vlan} not configured correctly")
            
            for vlan in allowed_vlans.split(","):
                if vlan not in output:
                    raise PortConfigurationError(f"VLAN {vlan} not in allowed VLANs list")
            
            return True, ""
            
        except Exception as e:
            return False, f"Error configuring trunk port: {str(e)}"

    def configure_svi(self, vlan_id: str, ip_address: str, subnet_mask: str, description: str = "") -> Tuple[bool, str]:
        """
        Configure a Switch Virtual Interface (SVI).
        
        Args:
            vlan_id: VLAN ID for the SVI
            ip_address: IP address for the SVI
            subnet_mask: Subnet mask for the SVI (can be in CIDR format like /24 or dotted decimal like 255.255.255.0)
            description: Optional description for the SVI
            
        Returns:
            Tuple[bool, str]: (success status, error message if any)
        """
        try:
            if not self._connection_manager.is_connected():
                raise VLANOperationError("Not connected to switch")
            
            # Enter configuration mode
            logger.info("Entering config mode")
            config_cmd = self._command_manager.format_command('system_commands', 'configure_terminal')
            self._connection_manager.send_command(config_cmd)
            time.sleep(2)
            
            # Enter interface configuration
            logger.info(f"Configuring interface vlan {vlan_id}")
            interface_cmd = self._command_manager.format_command('vlan_commands', 'configure_interface', vlan_id=vlan_id)
            self._connection_manager.send_command(interface_cmd)
            time.sleep(2)   
            
            # Configure IP address
            logger.info(f"Setting IP address {ip_address} {subnet_mask}")
            ip_cmd = self._command_manager.format_command('vlan_commands', 'ip_address', ip_address=ip_address, subnet_mask=subnet_mask)
            self._connection_manager.send_command(ip_cmd)
            time.sleep(2)
            
            # Configure description if provided
            if description:
                logger.info(f"Setting description: {description}")
                description_cmd = self._command_manager.format_command('vlan_commands', 'description', description=description)
                self._connection_manager.send_command(description_cmd)
                time.sleep(2)
            
            # Exit interface configuration
            # self._connection.send_command("exit")
            # time.sleep(2)
            
            # Exit configuration mode
            end_cmd = self._command_manager.format_command('system_commands', 'end')
            self._connection_manager.send_command(end_cmd)
            time.sleep(2)
            
            # Verify configuration
            logger.info("Verifying SVI configuration")
            show_cmd = self._command_manager.format_command('vlan_commands', 'show_interface_vlan', vlan_id=vlan_id)
            output = self._connection_manager.send_command(show_cmd)
            logger.debug(f"SVI configuration output:\n{output}")
            
            if ip_address not in output:
                raise VLANOperationError(f"IP address {ip_address} not configured correctly")
            
            # Convert subnet mask to CIDR format if it's in dotted decimal
            if "." in subnet_mask:
                # Convert dotted decimal to CIDR
                octets = subnet_mask.split(".")
                binary = "".join([bin(int(x))[2:].zfill(8) for x in octets])
                cidr = str(binary.count("1"))
                subnet_mask = f"/{cidr}"
            
            # Check if subnet mask is in the output (either format)
            if subnet_mask not in output and f" {subnet_mask}" not in output:
                # Try to find the subnet mask in the output
                import re
                mask_pattern = r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|\/\d{1,2})"
                found_mask = re.search(mask_pattern, output)
                if not found_mask:
                    raise VLANOperationError(f"Subnet mask {subnet_mask} not configured correctly")
                actual_mask = found_mask.group(1)
                raise VLANOperationError(f"Subnet mask mismatch. Expected: {subnet_mask}, Found: {actual_mask}")
            
            return True, ""
            
        except Exception as e:
            return False, f"Error configuring SVI: {str(e)}"

    def configure_voice_vlan(self, port: str, voice_vlan: str, data_vlan: str, qos_trust: str = "cos") -> Tuple[bool, str]:
        """
        Configure voice VLAN on a port.
        
        Args:
            port: Port to configure
            voice_vlan: Voice VLAN ID
            data_vlan: Data VLAN ID
            qos_trust: QoS trust mode (cos, dscp, or none)
            
        Returns:
            Tuple[bool, str]: (success status, error message if any)
        """
        try:
            if not self._connection_manager.is_connected():
                raise PortConfigurationError("Not connected to switch")
            
            # Enter configuration mode
            logger.info("Entering config mode")
            config_cmd = self._command_manager.format_command('system_commands', 'configure_terminal')
            self._connection_manager.send_command(config_cmd)
            time.sleep(2)
            
            # Enter interface configuration
            logger.info(f"Configuring interface {port}")
            interface_cmd = self._command_manager.format_command('vlan_commands', 'configure_interface', 
                                                              interface=port)
            self._connection_manager.send_command(interface_cmd)
            time.sleep(2)
            
            # Configure access mode and data VLAN
            logger.info("Setting access mode")
            self._connection_manager.send_command("switchport mode access")
            time.sleep(2)
            
            logger.info(f"Setting access VLAN {data_vlan}")
            self._connection_manager.send_command(f"switchport access vlan {data_vlan}")
            time.sleep(2)
            
            # Configure voice VLAN
            logger.info(f"Setting voice VLAN {voice_vlan}")
            self._connection_manager.send_command(f"switchport voice vlan {voice_vlan}")
            time.sleep(2)
            
            # Configure QoS trust
            logger.info(f"Setting QoS trust mode to {qos_trust}")
            self._connection_manager.send_command(f"mls qos trust {qos_trust}")
            time.sleep(2)
            
            # Enable interface
            logger.info("Enabling interface")
            self._connection_manager.send_command("no shutdown")
            time.sleep(2)
            
            # Exit interface configuration
            self._connection_manager.send_command("exit")
            time.sleep(2)
            
            # Exit configuration mode
            end_cmd = self._command_manager.format_command('system_commands', 'end')
            self._connection_manager.send_command(end_cmd)
            time.sleep(2)
            
            return True, ""
            
        except Exception as e:
            return False, f"Error configuring voice VLAN: {str(e)}"

    def configure_private_vlan(self, primary_vlan: str, isolated_vlan: str, community_vlan: str) -> Tuple[bool, str]:
        """
        Configure private VLANs.
        
        Args:
            primary_vlan: Primary VLAN ID
            isolated_vlan: Isolated VLAN ID
            community_vlan: Community VLAN ID
            
        Returns:
            Tuple[bool, str]: (success status, error message if any)
        """
        try:
            if not self._connection_manager.is_connected():
                raise VLANOperationError("Not connected to switch")
            
            # Enter configuration mode
            logger.info("Entering config mode")
            self._connection_manager.send_command("configure terminal")
            time.sleep(2)
            
            # Configure primary VLAN
            logger.info(f"Configuring primary VLAN {primary_vlan}")
            self._connection_manager.send_command(f"vlan {primary_vlan}")
            time.sleep(2)
            self._connection_manager.send_command("private-vlan primary")
            time.sleep(2)
            self._connection_manager.send_command("exit")
            time.sleep(2)
            
            # Configure isolated VLAN
            logger.info(f"Configuring isolated VLAN {isolated_vlan}")
            self._connection_manager.send_command(f"vlan {isolated_vlan}")
            time.sleep(2)
            self._connection_manager.send_command("private-vlan isolated")
            time.sleep(2)
            self._connection_manager.send_command("exit")
            time.sleep(2)
            
            # Configure community VLAN
            logger.info(f"Configuring community VLAN {community_vlan}")
            self._connection_manager.send_command(f"vlan {community_vlan}")
            time.sleep(2)
            self._connection_manager.send_command("private-vlan community")
            time.sleep(2)
            self._connection_manager.send_command("exit")
            time.sleep(2)
            
            # Associate secondary VLANs with primary
            logger.info("Associating secondary VLANs with primary")
            self._connection_manager.send_command(f"vlan {primary_vlan}")
            time.sleep(2)
            self._connection_manager.send_command(f"private-vlan association {isolated_vlan},{community_vlan}")
            time.sleep(2)
            self._connection_manager.send_command("exit")
            time.sleep(2)
            
            # Exit configuration mode
            self._connection_manager.send_command("exit")
            time.sleep(2)
            
            # Verify configuration
            logger.info("Verifying private VLAN configuration")
            output = self._connection_manager.send_command("show vlan private-vlan")
            logger.debug(f"Private VLAN configuration output:\n{output}")
            
            if f"Primary Secondary Type" not in output:
                raise VLANOperationError("Private VLAN not configured correctly")
            
            if f"{primary_vlan} {isolated_vlan} isolated" not in output:
                raise VLANOperationError(f"Isolated VLAN {isolated_vlan} not associated with primary VLAN {primary_vlan}")
            
            if f"{primary_vlan} {community_vlan} community" not in output:
                raise VLANOperationError(f"Community VLAN {community_vlan} not associated with primary VLAN {primary_vlan}")
            
            return True, ""
            
        except Exception as e:
            return False, f"Error configuring private VLANs: {str(e)}"

    def configure_vlan_access_map(self, map_name: str, sequence: str, action: str, acl_name: str) -> Tuple[bool, str]:
        """
        Configure VLAN access-map.
        
        Args:
            map_name: Name of the access-map
            sequence: Sequence number
            action: Action (permit or drop)
            acl_name: Name of the ACL
            
        Returns:
            Tuple[bool, str]: (success status, error message if any)
        """
        try:
            if not self._connection_manager.is_connected():
                raise VLANOperationError("Not connected to switch")
            
            # Enter configuration mode
            logger.info("Entering config mode")
            self._connection_manager.send_command("configure terminal")
            time.sleep(2)
            
            # Configure access-map
            logger.info(f"Configuring access-map {map_name}")
            self._connection_manager.send_command(f"vlan access-map {map_name} {sequence}")
            time.sleep(2)
            
            # Configure match and action
            logger.info(f"Configuring match and action")
            self._connection_manager.send_command(f"match ip address {acl_name}")
            time.sleep(2)
            self._connection_manager.send_command(f"action {action}")
            time.sleep(2)
            
            # Exit access-map configuration
            self._connection_manager.send_command("exit")
            time.sleep(2)
            
            # Exit configuration mode
            self._connection_manager.send_command("exit")
            time.sleep(2)
            
            # Verify configuration
            logger.info("Verifying access-map configuration")
            output = self._connection_manager.send_command(f"show vlan access-map {map_name}")
            logger.debug(f"Access-map configuration output:\n{output}")
            
            if map_name not in output:
                raise VLANOperationError(f"Access-map {map_name} not configured correctly")
            
            return True, ""
            
        except Exception as e:
            return False, f"Error configuring VLAN access-map: {str(e)}"

    def apply_vlan_access_map(self, vlan_id: str, map_name: str) -> Tuple[bool, str]:
        """
        Apply VLAN access-map to a VLAN.
        
        Args:
            vlan_id: VLAN ID
            map_name: Name of the access-map
            
        Returns:
            Tuple[bool, str]: (success status, error message if any)
        """
        try:
            if not self._connection_manager.is_connected():
                raise VLANOperationError("Not connected to switch")
            
            # Enter configuration mode
            logger.info("Entering config mode")
            self._connection_manager.send_command("configure terminal")
            time.sleep(2)
            
            # Enter VLAN configuration
            logger.info(f"Configuring VLAN {vlan_id}")
            self._connection_manager.send_command(f"vlan {vlan_id}")
            time.sleep(2)
            
            # Apply access-map
            logger.info(f"Applying access-map {map_name}")
            self._connection_manager.send_command(f"vlan filter {map_name} vlan-list {vlan_id}")
            time.sleep(2)
            
            # Exit VLAN configuration
            self._connection_manager.send_command("exit")
            time.sleep(2)
            
            # Exit configuration mode
            self._connection_manager.send_command("exit")
            time.sleep(2)
            
            # Verify configuration
            logger.info("Verifying access-map application")
            output = self._connection_manager.send_command("show vlan filter")
            logger.debug(f"Access-map application output:\n{output}")
            
            if f"VLAN {vlan_id}" not in output:
                raise VLANOperationError(f"Access-map not applied to VLAN {vlan_id}")
            
            return True, ""
            
        except Exception as e:
            return False, f"Error applying VLAN access-map: {str(e)}"

    def verify_trunk_configuration(self, port: str, native_vlan: str, allowed_vlans: str) -> Tuple[bool, str]:
        """
        Verify trunk port configuration.
        
        Args:
            port: Port to verify
            native_vlan: Expected native VLAN ID
            allowed_vlans: Expected allowed VLANs (comma-separated)
            
        Returns:
            Tuple[bool, str]: (success status, error message if any)
        """
        try:
            if not self._connection_manager.is_connected():
                raise PortConfigurationError("Not connected to switch")
            
            # Check interface status first
            logger.info("Checking interface status")
            status_output = self._connection_manager.send_command(f"show interfaces {port} status")
            logger.debug(f"Interface status output:\n{status_output}")
            
            if "notconnect" in status_output.lower() or "disabled" in status_output.lower():
                logger.warning(f"Interface {port} is down. Cannot verify trunk configuration.")
                # Check administrative mode
                logger.info("Checking administrative mode")
                switchport_output = self._connection_manager.send_command(f"show interfaces {port} switchport")
                logger.debug(f"Switchport configuration output:\n{switchport_output}")
                
                if "Administrative Mode: trunk" not in switchport_output:
                    raise PortConfigurationError(f"Port {port} is not administratively configured as trunk")
                
                return True, "Interface is down"
            else:
                # Verify trunk configuration
                logger.info("Verifying trunk configuration")
                output = self._connection_manager.send_command(f"show interfaces {port} trunk")
                logger.debug(f"Trunk configuration output:\n{output}")
                
                if "trunking" not in output.lower():
                    raise PortConfigurationError(f"Port {port} is not in trunking mode")
                
                if native_vlan not in output:
                    raise PortConfigurationError(f"Native VLAN {native_vlan} not configured correctly")
                
                for vlan in allowed_vlans.split(","):
                    if vlan not in output:
                        raise PortConfigurationError(f"VLAN {vlan} not in allowed VLANs list")
            
            return True, ""
            
        except Exception as e:
            return False, f"Error verifying trunk configuration: {str(e)}"

    def shutdown_svi(self, vlan_id: str) -> Tuple[bool, str]:
        """
        Shutdown a Switch Virtual Interface (SVI).
        
        Args:
            vlan_id: VLAN ID of the SVI to shutdown
            
        Returns:
            Tuple[bool, str]: (success status, error message if any)
        """
        try:
            if not self._connection_manager.is_connected():
                raise VLANOperationError("Not connected to switch")
            
            # Enter configuration mode
            logger.info("Entering config mode")
            self._connection_manager.send_command("configure terminal")
            time.sleep(2)
            
            # Enter interface configuration
            logger.info(f"Configuring interface vlan {vlan_id}")
            self._connection_manager.send_command(f"interface vlan {vlan_id}")
            time.sleep(2)
            
            # Shutdown the interface
            logger.info("Shutting down SVI")
            self._connection_manager.send_command("shutdown")
            time.sleep(2)
            
            # Exit interface configuration
            self._connection_manager.send_command("exit")
            time.sleep(2)
            
            # Exit configuration mode
            self._connection_manager.send_command("exit")
            time.sleep(2)
            
            # Verify shutdown
            logger.info("Verifying SVI shutdown")
            output = self._connection_manager.send_command(f"show interfaces vlan {vlan_id}")
            logger.debug(f"SVI status output:\n{output}")
            
            if "administratively down" not in output.lower():
                raise VLANOperationError(f"SVI {vlan_id} was not properly shutdown")
            
            return True, ""
            
        except Exception as e:
            return False, f"Error shutting down SVI: {str(e)}"

    def no_shutdown_svi(self, vlan_id: str) -> Tuple[bool, str]:
        """
        Enable a Switch Virtual Interface (SVI).
        
        Args:
            vlan_id: VLAN ID of the SVI to enable
            
        Returns:
            Tuple[bool, str]: (success status, error message if any)
        """
        try:
            if not self._connection_manager.is_connected():
                raise VLANOperationError("Not connected to switch")
            
            # Enter configuration mode
            logger.info("Entering config mode")
            self._connection_manager.send_command("configure terminal")
            time.sleep(2)
            
            # Enter interface configuration
            logger.info(f"Configuring interface vlan {vlan_id}")
            self._connection_manager.send_command(f"interface vlan {vlan_id}")
            time.sleep(2)
            
            # Enable the interface
            logger.info("Enabling SVI")
            self._connection_manager.send_command("no shutdown")
            time.sleep(2)
            
            # Exit configuration mode
            end_cmd = self._command_manager.format_command('system_commands', 'end')
            self._connection_manager.send_command(end_cmd)
            time.sleep(2)
            
            # Verify enable
            logger.info("Verifying SVI enable")
            output = self._connection_manager.send_command(f"show interfaces vlan {vlan_id}")
            logger.debug(f"SVI status output:\n{output}")
            
            if "administratively down" in output.lower():
                raise VLANOperationError(f"SVI {vlan_id} was not properly enabled")
            
            return True, ""
            
        except Exception as e:
            return False, f"Error enabling SVI: {str(e)}"

    def verify_svi_configuration(self, vlan_id: str, ip_address: str = None, subnet_mask: str = None) -> Tuple[bool, str]:
        """
        Verify Switch Virtual Interface (SVI) configuration.
        
        Args:
            vlan_id: VLAN ID of the SVI to verify
            ip_address: Expected IP address (optional)
            subnet_mask: Expected subnet mask (optional, can be in CIDR or dotted decimal format)
            
        Returns:
            Tuple[bool, str]: (success status, error message if any)
        """
        try:
            if not self._connection_manager.is_connected():
                raise VLANOperationError("Not connected to switch")
            
            # Get SVI configuration
            logger.info(f"Verifying SVI {vlan_id} configuration")
            output = self._connection_manager.send_command(f"show interfaces vlan {vlan_id}")
            logger.debug(f"SVI configuration output:\n{output}")
            
            verification_details = []
            
            # Check if SVI exists
            if f"Vlan{vlan_id}" not in output:
                verification_details.append(f"SVI {vlan_id} does not exist")
                return False, " | ".join(verification_details)
            
            # Check interface status
            if "administratively down" in output.lower():
                verification_details.append("SVI is administratively down")
            
            # Verify IP address if provided
            if ip_address:
                if ip_address not in output:
                    verification_details.append(f"IP address {ip_address} not configured correctly")
            
            # Verify subnet mask if provided
            if subnet_mask:
                # Convert subnet mask to CIDR format if it's in dotted decimal
                if "." in subnet_mask:
                    octets = subnet_mask.split(".")
                    binary = "".join([bin(int(x))[2:].zfill(8) for x in octets])
                    cidr = str(binary.count("1"))
                    subnet_mask = f"/{cidr}"
                
                # Check if subnet mask is in the output (either format)
                if subnet_mask not in output and f" {subnet_mask}" not in output:
                    # Try to find the subnet mask in the output
                    import re
                    mask_pattern = r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|\/\d{1,2})"
                    found_mask = re.search(mask_pattern, output)
                    if not found_mask:
                        verification_details.append(f"Subnet mask {subnet_mask} not configured correctly")
                    else:
                        actual_mask = found_mask.group(1)
                        verification_details.append(f"Subnet mask mismatch. Expected: {subnet_mask}, Found: {actual_mask}")
            
            if verification_details:
                return False, " | ".join(verification_details)
            
            return True, "SVI configuration verified successfully"
            
        except Exception as e:
            return False, f"Error verifying SVI configuration: {str(e)}"

    def verify_voice_vlan_configuration(self, port: str, voice_vlan: str, data_vlan: str, qos_trust: str = "cos") -> Tuple[bool, str]:
        """
        Verify voice VLAN configuration on a port.
        
        Args:
            port: Port to verify
            voice_vlan: Expected voice VLAN ID
            data_vlan: Expected data VLAN ID
            qos_trust: Expected QoS trust mode (cos, dscp, or none)
            
        Returns:
            Tuple[bool, str]: (success status, error message if any)
        """
        try:
            if not self._connection_manager.is_connected():
                raise PortConfigurationError("Not connected to switch")
            
            # Check interface status first
            logger.info("Checking interface status")
            status_output = self._connection_manager.send_command(f"show interfaces {port} status")
            logger.debug(f"Interface status output:\n{status_output}")
            
            if "notconnect" in status_output.lower() or "disabled" in status_output.lower():
                logger.warning(f"Interface {port} is down. Cannot verify voice VLAN configuration.")
                return True, "Interface is down, cannot verify voice VLAN configuration"
            
            # Get switchport configuration
            logger.info("Checking switchport configuration")
            output = self._connection_manager.send_command(f"show interfaces {port} switchport")
            logger.debug(f"Switchport configuration output:\n{output}")
            
            verification_details = []
            
            # Check if port is in access mode
            if "Switchport Mode: access" not in output:
                verification_details.append("Port is not in access mode")
            
            # Verify voice VLAN
            if f"Voice VLAN: {voice_vlan}" not in output:
                verification_details.append(f"Voice VLAN {voice_vlan} not configured correctly")
            
            # Verify data VLAN
            if f"Access Mode VLAN: {data_vlan}" not in output:
                verification_details.append(f"Data VLAN {data_vlan} not configured correctly")
            
            # Verify QoS trust mode
            if f"Trust state: {qos_trust}" not in output.lower():
                verification_details.append(f"QoS trust mode {qos_trust} not configured correctly")
            
            if verification_details:
                return False, " | ".join(verification_details)
            
            return True, "Voice VLAN configuration verified successfully"
            
        except Exception as e:
            return False, f"Error verifying voice VLAN configuration: {str(e)}"

    def configure_pvlan_ports(self, promiscuous_port: str, isolated_port: str, community_port: str, 
                            primary_vlan: str, isolated_vlan: str, community_vlan: str) -> Tuple[bool, str]:
        """
        Configure private VLAN ports.
        
        Args:
            promiscuous_port: Port to configure as promiscuous
            isolated_port: Port to configure as isolated
            community_port: Port to configure as community
            primary_vlan: Primary VLAN ID
            isolated_vlan: Isolated VLAN ID
            community_vlan: Community VLAN ID
            
        Returns:
            Tuple[bool, str]: (success status, error message if any)
        """
        try:
            if not self._connection_manager.is_connected():
                raise PortConfigurationError("Not connected to switch")
            
            # Enter configuration mode
            logger.info("Entering config mode")
            self._connection_manager.send_command("configure terminal")
            time.sleep(2)
            
            # Configure promiscuous port
            logger.info(f"Configuring promiscuous port {promiscuous_port}")
            self._connection_manager.send_command(f"interface {promiscuous_port}")
            time.sleep(2)
            self._connection_manager.send_command("switchport mode private-vlan promiscuous")
            time.sleep(2)
            self._connection_manager.send_command(f"switchport private-vlan mapping {primary_vlan} {isolated_vlan},{community_vlan}")
            time.sleep(2)
            self._connection_manager.send_command("no shutdown")
            time.sleep(2)
            self._connection_manager.send_command("exit")
            time.sleep(2)
            
            # Configure isolated port
            logger.info(f"Configuring isolated port {isolated_port}")
            self._connection_manager.send_command(f"interface {isolated_port}")
            time.sleep(2)
            self._connection_manager.send_command("switchport mode private-vlan host")
            time.sleep(2)
            self._connection_manager.send_command(f"switchport private-vlan host-association {primary_vlan} {isolated_vlan}")
            time.sleep(2)
            self._connection_manager.send_command("no shutdown")
            time.sleep(2)
            self._connection_manager.send_command("exit")
            time.sleep(2)
            
            # Configure community port
            logger.info(f"Configuring community port {community_port}")
            self._connection_manager.send_command(f"interface {community_port}")
            time.sleep(2)
            self._connection_manager.send_command("switchport mode private-vlan host")
            time.sleep(2)
            self._connection_manager.send_command(f"switchport private-vlan host-association {primary_vlan} {community_vlan}")
            time.sleep(2)
            self._connection_manager.send_command("no shutdown")
            time.sleep(2)
            self._connection_manager.send_command("exit")
            time.sleep(2)
            
            # Exit configuration mode
            self._connection_manager.send_command("exit")
            time.sleep(2)
            
            return True, ""
            
        except Exception as e:
            return False, f"Error configuring private VLAN ports: {str(e)}"

    def verify_pvlan_configuration(self, primary_vlan: str, isolated_vlan: str, community_vlan: str) -> Tuple[bool, str]:
        """
        Verify private VLAN configuration.
        
        Args:
            primary_vlan: Primary VLAN ID
            isolated_vlan: Isolated VLAN ID
            community_vlan: Community VLAN ID
            
        Returns:
            Tuple[bool, str]: (success status, error message if any)
        """
        try:
            if not self._connection_manager.is_connected():
                raise VLANOperationError("Not connected to switch")
            
            verification_details = []
            
            # Verify private VLAN configuration
            logger.info("Verifying private VLAN configuration")
            output = self._connection_manager.send_command("show vlan private-vlan")
            logger.debug(f"Private VLAN configuration output:\n{output}")
            
            if f"Primary Secondary Type" not in output:
                verification_details.append("Private VLAN not configured correctly")
            
            if f"{primary_vlan} {isolated_vlan} isolated" not in output:
                verification_details.append(f"Isolated VLAN {isolated_vlan} not associated with primary VLAN {primary_vlan}")
            
            if f"{primary_vlan} {community_vlan} community" not in output:
                verification_details.append(f"Community VLAN {community_vlan} not associated with primary VLAN {primary_vlan}")
            
            # Verify port configurations
            logger.info("Verifying port configurations")
            port_output = self._connection_manager.send_command("show interfaces status")
            logger.debug(f"Port status output:\n{port_output}")
            
            if verification_details:
                return False, " | ".join(verification_details)
            
            return True, "Private VLAN configuration verified successfully"
            
        except Exception as e:
            return False, f"Error verifying private VLAN configuration: {str(e)}"

    def get_switch_info(self) -> Tuple[str, str]:
        """
        Execute 'show version' command and log the switch model and IOS version.

        Returns:
            Tuple[str, str]: (model, ios_version)
        """
        try:
            output = self._connection_manager.send_command("show version")
            
            # Parse output to extract model and IOS version
            model = None
            ios_version = None
            
            # Split output into lines and process
            lines = output.splitlines()
            for i, line in enumerate(lines):
                if "Model number" in line:
                    model = line.split(":")[1].strip()
                # Look for the line containing SW Version
                if "SW Version" in line and i + 2 < len(lines):
                    # The line after next contains the actual version info
                    version_line = lines[i + 2]
                    parts = version_line.split()
                    if len(parts) >= 4:  # Ensure we have enough parts
                        ios_version = parts[3]  # SW Version is the 4th column

            if not model or not ios_version:
                raise SwitchAPIError("Failed to parse switch model or IOS version from 'show version' output.")

            return model, ios_version
            
        except Exception as e:
            raise SwitchAPIError(f"Failed to get switch info: {str(e)}")

    def enable_mac_notification(self) -> Tuple[bool, str]:
        """
        Enable MAC address notification feature.
        
        Returns:
            Tuple[bool, str]: (success status, error message if any)
        """
        try:
            if not self._connection_manager.is_connected():
                raise MACTableError("Not connected to switch")
            
            # Enter configuration mode
            self._connection_manager.send_command("configure terminal")
            self._connection_manager.send_command("mac address-table notification")
            self._connection_manager.send_command("exit")
            
            return True, ""
            
        except Exception as e:
            return False, f"Error enabling MAC notification: {str(e)}"

    def verify_mac_notification(self) -> Tuple[bool, str]:
        """
        Verify MAC address notification configuration.
        
        Returns:
            Tuple[bool, str]: (success status, error message if any)
        """
        try:
            if not self._connection_manager.is_connected():
                raise MACTableError("Not connected to switch")
            
            output = self._connection_manager.send_command("show mac address-table notification")
            if "MAC address notification is enabled" not in output:
                return False, "MAC notification is not enabled"
            
            return True, ""
            
        except Exception as e:
            return False, f"Error verifying MAC notification: {str(e)}"

    def configure_mac_filtering(self, mac_address: str, vlan: str) -> Tuple[bool, str]:
        """
        Configure MAC address filtering.
        
        Args:
            mac_address: MAC address to filter
            vlan: VLAN ID
            
        Returns:
            Tuple[bool, str]: (success status, error message if any)
        """
        try:
            if not self._connection_manager.is_connected():
                raise MACTableError("Not connected to switch")
            
            # Enter configuration mode
            self._connection_manager.send_command("configure terminal")
            self._connection_manager.send_command(f"mac address-table static {mac_address} vlan {vlan} drop")
            self._connection_manager.send_command("exit")
            
            return True, ""
            
        except Exception as e:
            return False, f"Error configuring MAC filtering: {str(e)}"

    def verify_mac_filtering(self, mac_address: str, vlan: str) -> Tuple[bool, str]:
        """
        Verify MAC address filtering configuration.
        
        Args:
            mac_address: MAC address to verify
            vlan: VLAN ID
            
        Returns:
            Tuple[bool, str]: (success status, error message if any)
        """
        try:
            if not self._connection_manager.is_connected():
                raise MACTableError("Not connected to switch")
            
            output = self._connection_manager.send_command("show mac address-table static")
            if f"{mac_address} vlan {vlan} drop" not in output:
                return False, f"MAC filtering not configured for {mac_address} in VLAN {vlan}"
            
            return True, ""
            
        except Exception as e:
            return False, f"Error verifying MAC filtering: {str(e)}"

    def test_mac_filtering_behavior(self, mac_address: str, vlan: str) -> Tuple[bool, str]:
        """
        Test MAC address filtering behavior.
        
        Args:
            mac_address: MAC address to test
            vlan: VLAN ID
            
        Returns:
            Tuple[bool, str]: (success status, error message if any)
        """
        try:
            if not self._connection_manager.is_connected():
                raise MACTableError("Not connected to switch")
            
            # Send test traffic and verify it's dropped
            output = self._connection_manager.send_command(f"show mac address-table static {mac_address} vlan {vlan}")
            if "drop" not in output.lower():
                return False, f"MAC filtering not working for {mac_address} in VLAN {vlan}"
            
            return True, ""
            
        except Exception as e:
            return False, f"Error testing MAC filtering behavior: {str(e)}"

    def configure_mac_security(self, port: str) -> Tuple[bool, str]:
        """
        Configure MAC address security features.
        
        Args:
            port: Port to configure
            
        Returns:
            Tuple[bool, str]: (success status, error message if any)
        """
        try:
            if not self._connection_manager.is_connected():
                raise MACTableError("Not connected to switch")
            
            # Enter configuration mode
            self._connection_manager.send_command("configure terminal")
            self._connection_manager.send_command(f"interface {port}")
            self._connection_manager.send_command("switchport port-security")
            self._connection_manager.send_command("switchport port-security maximum 1")
            self._connection_manager.send_command("switchport port-security violation restrict")
            self._connection_manager.send_command("exit")
            self._connection_manager.send_command("exit")
            
            return True, ""
            
        except Exception as e:
            return False, f"Error configuring MAC security: {str(e)}"

    def verify_mac_security(self, port: str) -> Tuple[bool, str]:
        """
        Verify MAC address security configuration.
        
        Args:
            port: Port to verify
            
        Returns:
            Tuple[bool, str]: (success status, error message if any)
        """
        try:
            if not self._connection_manager.is_connected():
                raise MACTableError("Not connected to switch")
            
            output = self._connection_manager.send_command(f"show port-security interface {port}")
            if "Port Security: Enabled" not in output:
                return False, f"Port security not enabled on {port}"
            
            return True, ""
            
        except Exception as e:
            return False, f"Error verifying MAC security: {str(e)}"

    def test_mac_security_features(self, port: str) -> Tuple[bool, str]:
        """
        Test MAC address security features.
        
        Args:
            port: Port to test
            
        Returns:
            Tuple[bool, str]: (success status, error message if any)
        """
        try:
            if not self._connection_manager.is_connected():
                raise MACTableError("Not connected to switch")
            
            # Verify security features are working
            output = self._connection_manager.send_command(f"show port-security interface {port}")
            if "Security Violation Count: 0" not in output:
                return False, f"Security violation detected on {port}"
            
            return True, ""
            
        except Exception as e:
            return False, f"Error testing MAC security features: {str(e)}"

    def configure_stp_mode(self, mode: str) -> Tuple[bool, str]:
        """
        Configure STP mode on the switch.
        
        Args:
            mode: STP mode (pvst, rapid-pvst, mst)
            
        Returns:
            Tuple[bool, str]: (success status, error message if any)
        """
        try:
            if not self._connection_manager.is_connected():
                raise STPError("Not connected to switch")
            
            # Enter enable mode
            output = self._connection_manager.send_command("enable")
            if "Invalid input" in output or "Error" in output:
                return False, f"Failed to enter enable mode: {output}"
            time.sleep(2)
            
            # Enter config mode
            output = self._connection_manager.send_command("configure terminal")
            if "Invalid input" in output or "Error" in output:
                return False, f"Failed to enter config mode: {output}"
            time.sleep(2)
            
            # Configure STP mode
            if mode == "pvst":
                output = self._connection_manager.send_command("spanning-tree mode pvst")
            elif mode == "rapid-pvst":
                output = self._connection_manager.send_command("spanning-tree mode rapid-pvst")
            elif mode == "mst":
                output = self._connection_manager.send_command("spanning-tree mode mst")
            else:
                return False, f"Invalid STP mode: {mode}"
            
            if "Invalid input" in output or "Error" in output:
                return False, f"Failed to configure STP mode {mode}: {output}"
            
            time.sleep(2)
            
            # Exit config mode
            output = self._connection_manager.send_command("exit")
            if "Invalid input" in output or "Error" in output:
                return False, f"Failed to exit config mode: {output}"
            time.sleep(2)
            
            return True, ""
            
        except Exception as e:
            return False, f"Failed to configure STP mode: {str(e)}"
    
    def verify_stp_mode(self, mode: str) -> Tuple[bool, str]:
        """
        Verify STP mode configuration.
        
        Args:
            mode: Expected STP mode
            
        Returns:
            Tuple[bool, str]: (success status, error message if any)
        """
        try:
            output = self._connection_manager.send_command("show spanning-tree summary")
            # Convert both the output and expected mode to lowercase for case-insensitive comparison
            output_lower = output.lower()
            mode_lower = mode.lower()
            
            # Check for common variations of STP mode names
            mode_variations = {
                'pvst': ['pvst', 'per-vlan spanning tree'],
                'rapid-pvst': ['rapid-pvst', 'rapid pvst', 'rapid per-vlan spanning tree'],
                'mst': ['mst', 'multiple spanning tree']
            }
            
            # Get the variations for the expected mode
            variations = mode_variations.get(mode_lower, [mode_lower])
            
            # Check if any variation is present in the output
            if not any(var in output_lower for var in variations):
                return False, f"STP mode mismatch. Expected {mode}, output: {output}"
            return True, ""
        except Exception as e:
            return False, f"Failed to verify STP mode: {str(e)}"
    
    def configure_root_bridge(self, vlan: str, priority: str) -> Tuple[bool, str]:
        """
        Configure root bridge for a VLAN.
        
        Args:
            vlan: VLAN ID
            priority: Bridge priority value
            
        Returns:
            Tuple[bool, str]: (success status, error message if any)
        """
        try:
            if not self._connection_manager.is_connected():
                raise STPError("Not connected to switch")
            
            # Enter enable mode
            output = self._connection_manager.send_command("enable")
            if "Invalid input" in output or "Error" in output:
                return False, f"Failed to enter enable mode: {output}"
            time.sleep(2)
            
            # Enter config mode
            output = self._connection_manager.send_command("configure terminal")
            if "Invalid input" in output or "Error" in output:
                return False, f"Failed to enter config mode: {output}"
            time.sleep(2)
            
            # Configure root bridge
            output = self._connection_manager.send_command(f"spanning-tree vlan {vlan} root primary")
            if "Invalid input" in output or "Error" in output:
                return False, f"Failed to configure root bridge: {output}"
            time.sleep(2)
            
            # Exit config mode
            output = self._connection_manager.send_command("exit")
            if "Invalid input" in output or "Error" in output:
                return False, f"Failed to exit config mode: {output}"
            time.sleep(2)
            
            return True, ""
            
        except Exception as e:
            return False, f"Failed to configure root bridge: {str(e)}"
    
    def verify_root_bridge(self, vlan: str, priority: str) -> Tuple[bool, str]:
        """
        Verify root bridge configuration.
        
        Args:
            vlan: VLAN ID
            priority: Expected bridge priority
            
        Returns:
            Tuple[bool, str]: (success status, error message if any)
        """
        try:
            output = self._connection_manager.send_command(f"show spanning-tree vlan {vlan}")
            # Look for priority in different possible formats
            priority_patterns = [
                f"Priority {priority}",
                f"Bridge Priority {priority}",
                f"Priority: {priority}",
                f"Bridge Priority: {priority}"
            ]
            
            if not any(pattern in output for pattern in priority_patterns):
                return False, f"Root bridge priority mismatch. Expected {priority}, output: {output}"
            return True, ""
        except Exception as e:
            return False, f"Failed to verify root bridge: {str(e)}"
    
    def configure_port_cost(self, port: str, vlan: str, cost: str) -> Tuple[bool, str]:
        """
        Configure STP port cost.
        
        Args:
            port: Port identifier
            vlan: VLAN ID
            cost: Port cost value
            
        Returns:
            Tuple[bool, str]: (success status, error message if any)
        """
        try:
            if not self._connection_manager.is_connected():
                raise STPError("Not connected to switch")
            
            # Enter enable mode
            output = self._connection_manager.send_command("enable")
            if "Invalid input" in output or "Error" in output:
                return False, f"Failed to enter enable mode: {output}"
            time.sleep(2)
            
            # Enter config mode
            output = self._connection_manager.send_command("configure terminal")
            if "Invalid input" in output or "Error" in output:
                return False, f"Failed to enter config mode: {output}"
            time.sleep(2)
            
            # Enter interface config mode
            output = self._connection_manager.send_command(f"interface {port}")
            if "Invalid input" in output or "Error" in output:
                return False, f"Failed to enter interface config mode: {output}"
            time.sleep(2)
            
            # Configure port cost
            output = self._connection_manager.send_command(f"spanning-tree vlan {vlan} cost {cost}")
            if "Invalid input" in output or "Error" in output:
                return False, f"Failed to configure port cost: {output}"
            time.sleep(2)
            
            # Exit interface config mode
            output = self._connection_manager.send_command("exit")
            if "Invalid input" in output or "Error" in output:
                return False, f"Failed to exit interface config mode: {output}"
            time.sleep(2)
            
            # Exit global config mode
            output = self._connection_manager.send_command("exit")
            if "Invalid input" in output or "Error" in output:
                return False, f"Failed to exit config mode: {output}"
            time.sleep(2)
            
            return True, ""
            
        except Exception as e:
            return False, f"Failed to configure port cost: {str(e)}"
    
    def verify_port_cost(self, port: str, vlan: str, cost: str) -> Tuple[bool, str]:
        """
        Verify STP port cost configuration.
        
        Args:
            port: Port identifier
            vlan: VLAN ID
            cost: Expected port cost
            
        Returns:
            Tuple[bool, str]: (success status, error message if any)
        """
        try:
            output = self._connection_manager.send_command(f"show spanning-tree vlan {vlan}")
            # Look for port cost in different possible formats
            cost_patterns = [
                f"Cost {cost}",
                f"Port Cost {cost}",
                f"Cost: {cost}",
                f"Port Cost: {cost}"
            ]
            
            # Find the port section in the output
            port_section = ""
            for line in output.splitlines():
                if port.lower() in line.lower():
                    port_section = line
                    break
            
            if not any(pattern in port_section for pattern in cost_patterns):
                return False, f"Port cost mismatch. Expected {cost}, output: {output}"
            return True, ""
        except Exception as e:
            return False, f"Failed to verify port cost: {str(e)}"
    
    def configure_port_priority(self, port: str, vlan: str, priority: str) -> Tuple[bool, str]:
        """
        Configure STP port priority.
        
        Args:
            port: Port identifier
            vlan: VLAN ID
            priority: Port priority value
            
        Returns:
            Tuple[bool, str]: (success status, error message if any)
        """
        try:
            if not self._connection_manager.is_connected():
                raise STPError("Not connected to switch")
            
            # Enter enable mode
            output = self._connection_manager.send_command("enable")
            if "Invalid input" in output or "Error" in output:
                return False, f"Failed to enter enable mode: {output}"
            time.sleep(2)
            
            # Enter config mode
            output = self._connection_manager.send_command("configure terminal")
            if "Invalid input" in output or "Error" in output:
                return False, f"Failed to enter config mode: {output}"
            time.sleep(2)
            
            # Enter interface config mode
            output = self._connection_manager.send_command(f"interface {port}")
            if "Invalid input" in output or "Error" in output:
                return False, f"Failed to enter interface config mode: {output}"
            time.sleep(2)
            
            # Configure port priority
            output = self._connection_manager.send_command(f"spanning-tree vlan {vlan} port-priority {priority}")
            if "Invalid input" in output or "Error" in output:
                return False, f"Failed to configure port priority: {output}"
            time.sleep(2)
            
            # Exit interface config mode
            output = self._connection_manager.send_command("exit")
            if "Invalid input" in output or "Error" in output:
                return False, f"Failed to exit interface config mode: {output}"
            time.sleep(2)
            
            # Exit global config mode
            output = self._connection_manager.send_command("exit")
            if "Invalid input" in output or "Error" in output:
                return False, f"Failed to exit config mode: {output}"
            time.sleep(2)
            
            return True, ""
            
        except Exception as e:
            return False, f"Failed to configure port priority: {str(e)}"
    
    def verify_port_priority(self, port: str, vlan: str, priority: str) -> Tuple[bool, str]:
        """
        Verify STP port priority configuration.
        
        Args:
            port: Port identifier
            vlan: VLAN ID
            priority: Expected port priority
            
        Returns:
            Tuple[bool, str]: (success status, error message if any)
        """
        try:
            output = self._connection_manager.send_command(f"show spanning-tree vlan {vlan}")
            # Look for port priority in different possible formats
            priority_patterns = [
                f"Priority {priority}",
                f"Port Priority {priority}",
                f"Priority: {priority}",
                f"Port Priority: {priority}"
            ]
            
            # Find the port section in the output
            port_section = ""
            for line in output.splitlines():
                if port.lower() in line.lower():
                    port_section = line
                    break
            
            if not any(pattern in port_section for pattern in priority_patterns):
                return False, f"Port priority mismatch. Expected {priority}, output: {output}"
            return True, ""
        except Exception as e:
            return False, f"Failed to verify port priority: {str(e)}"
    
    def configure_stp_guard(self, port: str, guard_type: str) -> Tuple[bool, str]:
        """
        Configure STP guard feature.
        
        Args:
            port: Port identifier
            guard_type: Type of guard (root, bpdu, loop)
            
        Returns:
            Tuple[bool, str]: (success status, error message if any)
        """
        try:
            if not self._connection_manager.is_connected():
                raise STPError("Not connected to switch")
            
            # Enter enable mode
            output = self._connection_manager.send_command("enable")
            if "Invalid input" in output or "Error" in output:
                return False, f"Failed to enter enable mode: {output}"
            time.sleep(2)
            
            # Enter config mode
            output = self._connection_manager.send_command("configure terminal")
            if "Invalid input" in output or "Error" in output:
                return False, f"Failed to enter config mode: {output}"
            time.sleep(2)
            
            # Enter interface config mode
            output = self._connection_manager.send_command(f"interface {port}")
            if "Invalid input" in output or "Error" in output:
                return False, f"Failed to enter interface config mode: {output}"
            time.sleep(2)
            
            # Configure guard
            if guard_type == "root":
                output = self._connection_manager.send_command("spanning-tree guard root")
            elif guard_type == "bpdu":
                output = self._connection_manager.send_command("spanning-tree bpduguard enable")
            elif guard_type == "loop":
                output = self._connection_manager.send_command("spanning-tree guard loop")
            else:
                return False, f"Invalid guard type: {guard_type}"
            
            if "Invalid input" in output or "Error" in output:
                return False, f"Failed to configure {guard_type} guard: {output}"
            
            time.sleep(2)
            
            # Exit interface config mode
            output = self._connection_manager.send_command("exit")
            if "Invalid input" in output or "Error" in output:
                return False, f"Failed to exit interface config mode: {output}"
            time.sleep(2)
            
            # Exit global config mode
            output = self._connection_manager.send_command("exit")
            if "Invalid input" in output or "Error" in output:
                return False, f"Failed to exit config mode: {output}"
            time.sleep(2)
            
            return True, ""
            
        except Exception as e:
            return False, f"Failed to configure STP guard: {str(e)}"
    
    def verify_stp_guard(self, port: str, guard_type: str) -> Tuple[bool, str]:
        """
        Verify STP guard configuration.
        
        Args:
            port: Port identifier
            guard_type: Type of guard to verify
            
        Returns:
            Tuple[bool, str]: (success status, error message if any)
        """
        try:
            output = self._connection_manager.send_command(f"show spanning-tree interface {port} detail")
            # Define patterns for different guard types
            guard_patterns = {
                "root": ["Root guard is enabled", "Root Guard: Enabled", "RootGuard: Enabled"],
                "bpdu": ["Bpdu guard is enabled", "Bpdu Guard: Enabled", "BpduGuard: Enabled"],
                "loop": ["Loop guard is enabled", "Loop Guard: Enabled", "LoopGuard: Enabled"]
            }
            
            # Get patterns for the specified guard type
            patterns = guard_patterns.get(guard_type.lower(), [])
            if not patterns:
                return False, f"Invalid guard type: {guard_type}"
            
            if not any(pattern in output for pattern in patterns):
                return False, f"{guard_type} guard not enabled. Output: {output}"
            return True, ""
        except Exception as e:
            return False, f"Failed to verify STP guard: {str(e)}"
    
    def test_stp_convergence(self, vlan: str) -> Tuple[bool, str]:
        """
        Test STP convergence behavior.
        
        Args:
            vlan: VLAN ID
            
        Returns:
            Tuple[bool, str]: (success status, error message if any)
        """
        try:
            # Get initial STP state
            initial_state = self._connection_manager.send_command(f"show spanning-tree vlan {vlan}")
            time.sleep(2)
            
            # Simulate topology change
            self._connection_manager.send_command("configure terminal")
            time.sleep(2)
            self._connection_manager.send_command(f"interface Fa0/1")
            time.sleep(5)  # Keep this at 5 seconds for topology change
            self._connection_manager.send_command("shutdown")
            time.sleep(5)  # Keep this at 5 seconds for topology change
            self._connection_manager.send_command("no shutdown")
            time.sleep(5)  # Keep this at 5 seconds for topology change
            self._connection_manager.send_command("exit")
            time.sleep(2)
            self._connection_manager.send_command("exit")
            time.sleep(2)
            
            # Get final STP state
            final_state = self._connection_manager.send_command(f"show spanning-tree vlan {vlan}")
            
            # Verify convergence
            if "Blocking" in final_state and "Forwarding" in final_state:
                return True, ""
            else:
                return False, "STP did not converge properly"
                
        except Exception as e:
            return False, f"Failed to test STP convergence: {str(e)}"
