import power_control_functions as pcf
import usb_communicator
import numpy as np



def main():
    connection = usb_communicator.usb_communicator()
    connection.connect()

    load_memory_voltages = np.linspace(0, 10, 21)
    connection.write(pcf.load_memory(0, load_memory_voltages))
    
    command = pcf.set_start_address(0)
    connection.write(command)

    # key = input("Please enter any text to continue: ")
    # current_memory_index = 0
    # while (key != ""):
        # print("You are at memory address ", current_memory_index)
        # connection.write(pcf.output_memory(current_memory_index, 1))

        # current_memory_index = current_memory_index + 1
        # key = input("Please enter any text to continue: ")

    # print("Test complete!")
    # connection.write(pcf.output_memory(0, 1))

if __name__ == "__main__":
    main()




    # set_voltage_test = set_voltage(5.5)
    # print(set_voltage_test)

    # load_memory_voltages = np.linspace(0, 10, 101)
    # load_memory_test = load_memory(0, load_memory_voltages)
    # print(load_memory_test)

    # set_start_address_test = set_start_address(513)
    # print(set_start_address_test)