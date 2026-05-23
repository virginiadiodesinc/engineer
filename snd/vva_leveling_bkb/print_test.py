import power_control_functions as pcf
import numpy as np

def main():

	set_voltage_test = pcf.set_voltage(5.5).hex(' ')
	print(set_voltage_test)

	load_memory_voltages = np.linspace(0, 10, 11)
	print(load_memory_voltages)
	load_memory_test = pcf.load_memory(0, load_memory_voltages).hex(' ')
	print(load_memory_test)

	set_start_address_test = pcf.set_start_address(8).hex(' ')
	print(set_start_address_test)

	output_memory_test = pcf.output_memory(1, 11).hex(' ')
	print(output_memory_test)

if __name__ == "__main__":
	main()