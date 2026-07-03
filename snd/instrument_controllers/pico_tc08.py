import ctypes
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
		'''
		Returns:
		> 0, The handle of a unit.
		0, No more units were found.
		-1, Unit failed to open. Call usb_tc08_get_last_error with a handle of 0 to
		obtain the error code.
		'''
		self.dev = tc08.usb_tc08_open_unit()
		if self.dev > 0:
			return self.dev
		elif self.dev == 0:
			print('TC08 failed to open. No more units were found')
		elif self.dev == -1:
			error = tc08.usb_tc08_get_last_error(0)
			print(f'TC08 failed to open.\nError: {error}')
			return None
		else:
			return None

	def close(self):
		tc08.usb_tc08_close_unit(self.dev)

	def __exit__(self):
		'''
		this might force close on CTRL+C
		'''
		tc08.usb_tc08_close_unit(self.dev)