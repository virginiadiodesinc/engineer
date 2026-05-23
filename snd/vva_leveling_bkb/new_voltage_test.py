import numpy as np
from vdi_controller import VDIModuleController

def main():
    # Initialize the controller wrapper
    module = VDIModuleController()
    
    # Connect to the USB module
    module.connect()
    
    # check connection was successful before trying to send commands
    if not module.is_connected:
        print("Exiting test due to connection failure.")
        return

    # Generate a ramp of voltages or whatever
    num_points = 1001
    ramp_voltages = np.linspace(10, 10, num_points)
    
    
    #Load the voltages into memory, starting at address 0
    print("Loading voltages into memory")
    module.load_memory_sequence(0, ramp_voltages)
    
    # Set the sweep start address
    print("Setting sweep start address to 0...")
    module.set_sweep_start_address(0)
    

if __name__ == "__main__":
    main()