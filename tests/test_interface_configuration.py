import time

# Configure interface
interface_cmd = command_manager.format_command('interface_commands', 'configure_interface',
                                             interface_name='FastEthernet0/1',
                                             subcommand='switchport_mode_access')
switch_api.send_command(interface_cmd)

# Exit interface configuration
switch_api.send_command("exit")
time.sleep(1)

# Exit configuration mode
switch_api.send_command("end")
time.sleep(1)

# Verify interface configuration 