import time

# Configure interface
interface_cmd = command_manager.format_command('interface_commands', 'configure_interface',
                                             interface_name='FastEthernet0/1',
                                             subcommand='switchport_mode_access')
switch_api.send_command(interface_cmd)

# Exit configuration mode
end_cmd = command_manager.format_command('system_commands', 'end')
switch_api.send_command(end_cmd)

# Verify interface configuration 