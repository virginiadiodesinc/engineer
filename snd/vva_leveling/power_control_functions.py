import math
import numpy as np

def convert_voltage_to_proportional_voltage_in_hex(voltage):
	if voltage < 0:
		voltage = 0.0

	if voltage > 10.0:
		voltage = 10.0
	
	voltage_over_10 = voltage / 10.0
	proportional_voltage = math.floor(voltage_over_10 * 65536)
	if proportional_voltage >= 65536:
		proportional_voltage = 65535

	hex_proportional_voltage = hex(proportional_voltage)

	return hex_proportional_voltage


def convert_hex_number_to_bytes(hex_number, size_in_bytes):
	hex_number_as_string = str(hex_number).replace('0x', '')
	
	while (len(hex_number_as_string) < size_in_bytes):
		hex_number_as_string = "0" + hex_number_as_string
	
	starting_index = 0
	ending_index = 2

	bytes = []
	while (ending_index <= len(hex_number_as_string)):
		byte = hex(int(hex_number_as_string[starting_index:ending_index], 16))
		bytes.append(byte)

		starting_index = ending_index
		ending_index = ending_index + 2
	
	return bytes


def set_voltage(voltage_as_float):

	set_voltage_command = hex(0x56)
	
	hex_voltage = convert_voltage_to_proportional_voltage_in_hex(voltage_as_float)
	[msb, lsb] = convert_hex_number_to_bytes(hex_voltage, 4)

	full_command_list = [set_voltage_command, msb, lsb]

	full_command_bytes = [(int(byte, 16)) for byte in full_command_list]
	full_command_bytes = bytes(full_command_bytes)
	
	return full_command_bytes

def load_memory(starting_address_as_integer, voltages_as_integers):
	load_memory_command = hex(0x57)

	if starting_address_as_integer > 524287:
		starting_address_as_integer = 524287

	if starting_address_as_integer < 0:
		starting_address_as_integer = 0

	if len(voltages_as_integers) + starting_address_as_integer > 524287:
		voltages_as_integers = voltages_as_integers[0:524287 - starting_address_as_integer]


	number_of_voltages_as_hex = hex(len(voltages_as_integers))
	starting_address_as_hex = hex(starting_address_as_integer)

	voltages_msb_and_lsb_list = []

	for voltage in voltages_as_integers:
		hex_voltage = convert_voltage_to_proportional_voltage_in_hex(voltage)
		[msb, lsb] = convert_hex_number_to_bytes(hex_voltage, 4)
		voltages_msb_and_lsb_list.append([msb, lsb])

	bytes_of_number_of_voltages = convert_hex_number_to_bytes(number_of_voltages_as_hex, 8)
	bytes_of_starting_addresss = convert_hex_number_to_bytes(starting_address_as_hex, 8)

	full_command_list= [load_memory_command]

	for byte in bytes_of_number_of_voltages:
		full_command_list.append(byte)

	for byte in bytes_of_starting_addresss:
		full_command_list.append(byte)

	for msb_and_lsb in voltages_msb_and_lsb_list:
		full_command_list.append(msb_and_lsb[0])
		full_command_list.append(msb_and_lsb[1])

	full_command_bytes = [(int(byte, 16)) for byte in full_command_list]
	full_command_bytes = bytes(full_command_bytes)

	return full_command_bytes


def set_start_address(starting_address_as_integer):
	set_start_address_command = hex(0x53)

	if starting_address_as_integer > 524287:
		starting_address_as_integer = 524287

	if starting_address_as_integer < 0:
		starting_address_as_integer = 0

	starting_address_as_hex = hex(starting_address_as_integer)
	bytes_of_starting_address = convert_hex_number_to_bytes(starting_address_as_hex, 8)

	full_command_list = [set_start_address_command]

	for byte in bytes_of_starting_address:
		full_command_list.append(byte)

	full_command_bytes = [(int(byte, 16)) for byte in full_command_list]
	full_command_bytes = bytes(full_command_bytes)

	return full_command_bytes

def output_memory(starting_address_as_integer, number_of_addresses_as_integer):
	output_memory_command = hex(0x40)

	if starting_address_as_integer > 524287:
		starting_address_as_integer = 524287

	if starting_address_as_integer < 0:
		starting_address_as_integer = 0

	if number_of_addresses_as_integer + starting_address_as_integer > 524287:
		starting_address_as_integer = 524287 - starting_address_as_integer

	starting_address_as_hex = hex(starting_address_as_integer)
	bytes_of_starting_address = convert_hex_number_to_bytes(starting_address_as_hex, 8)

	number_of_addresses_as_hex = hex(number_of_addresses_as_integer)
	bytes_of_number_of_addresses = convert_hex_number_to_bytes(number_of_addresses_as_hex, 8) 

	full_command_list = [output_memory_command]

	for byte in bytes_of_number_of_addresses:
		full_command_list.append(byte)

	for byte in bytes_of_starting_address:
		full_command_list.append(byte)

	full_command_bytes = [(int(byte, 16)) for byte in full_command_list]
	full_command_bytes = bytes(full_command_bytes)
	
	return full_command_bytes