

import ctypes
import sys

from picosdk.usbtc08 import usbtc08 as tc08





class TC08:

	def __init__(self):
		self.open()
		# self.activate_channel(1,'k')
		# print( self.get_data() )

	def activate_channel(self,num,therm_type='K'):
		tt_lookup = {
		"B": 66,
		"E": 69,
		"J": 74,
		"K": 75,
		"N": 78,
		"R": 82,
		"S": 83,
		"T": 84,
		' ': 32,
		"X": 88,
		}

		try:
			ttype = ctypes.c_int8(tt_lookup[therm_type.upper()])
		except:
			print('thermocouple type not exist')
			return

		tc08.usb_tc08_set_channel(self.dev,num,ttype)

	def get_data(self, units='C'):
		units_lookup = {
		"C": 0,
		"F": 1,
		"K": 2,
		"R": 3,
		}

		temp = (ctypes.c_float * 9)()
		overflow = ctypes.c_int16(0)

		try:
			utype = units_lookup[units.upper()]
		except:
			print('unit type not exist')
			return

		tc08.usb_tc08_get_single(self.dev, ctypes.byref(temp), ctypes.byref(overflow), utype)

		return temp

	def get_meas_time(self):
		return tc08.usb_tc08_get_minimum_interval_ms(self.dev)

	def set_mains(self):
		'''
		according to the documentation this sets mains rejection to 50Hz
		'''
		tc08.usb_tc08_set_mains(self.dev,0)

	def open(self):
		self.dev = tc08.usb_tc08_open_unit()

	def close(self):
		tc08.usb_tc08_close_unit(self.dev)