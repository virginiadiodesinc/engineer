import power_control_functions as pcf
import usb_communicator

class VDIModuleController:
    """
    wrapper for the PNA Triggered USB Module.
    Handles the USB connection and simplifies memory and voltage commands.
    """
    def __init__(self):
        """Initializes the controller and the underlying USB communicator."""
        self.connection = usb_communicator.usb_communicator()
        self.is_connected = False

    def connect(self):
        """Establishes the USB connection."""
        try:
            self.connection.connect()
            self.is_connected = True
            print("Connected to VDI USB Module.")
        except Exception as e:
            print(f"Failed to connect to the VDI USB Module: {e}")
            self.is_connected = False

    def set_immediate_voltage(self, voltage):
        """
        Immediately sets the output voltage (0-10V) and disables trigger response.
        Wraps the Set Voltage (0x56) command.
        """
        if not self.is_connected:
            raise ConnectionError("Module is not connected. Call connect() first.")
            
        command_bytes = pcf.set_voltage(voltage)
        self.connection.write(command_bytes)

    def load_memory_sequence(self, start_address, voltages_list):
        """
        Loads an array or list of voltages into memory starting at the given address.
        Wraps the Load Memory (0x57) command.
        """
        if not self.is_connected:
            raise ConnectionError("Module is not connected. Call connect() first.")
            
        command_bytes = pcf.load_memory(start_address, voltages_list)
        self.connection.write(command_bytes)

    def load_single_memory_voltage(self, address, voltage):
        """
        Loads a single voltage into a specific memory address.
        """
        self.load_memory_sequence(address, [voltage])

    def set_sweep_start_address(self, address):
        """
        Sets the starting address for the hardware sweep trigger.
        Wraps the Set Start Address (0x53) command.
        
        When the module receives the sweep trigger, the address will be 
        reset to this starting address, and subsequent step triggers will advance it.
        """
        if not self.is_connected:
            raise ConnectionError("Module is not connected. Call connect() first.")
            
        command_bytes = pcf.set_start_address(address)
        self.connection.write(command_bytes)

    def output_memory_sequence(self, start_address, num_addresses):
        """
        Outputs a series of memory locations internally without requiring triggers.
        Wraps the Output Memory (0x40) command.
        
        Note: This disables the hardware trigger response. You must call 
        set_sweep_start_address() again to re-enable hardware sweeps.
        """
        if not self.is_connected:
            raise ConnectionError("Module is not connected. Call connect() first.")
            
        command_bytes = pcf.output_memory(start_address, num_addresses)
        self.connection.write(command_bytes)