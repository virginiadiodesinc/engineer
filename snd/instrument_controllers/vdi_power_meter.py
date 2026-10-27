try:
	import ftd2xx as d2xx
except:
	print('Warning: Install ftd2xx to control PM5 and VDI synth\n')

class PM5():
	def __init__(self, serial='321V'):
		#devicelist = ftd2xx.listDevices()
		#index = devicelist.index('%s'%(serial))
		#self._handler = ftd2xx.open(0)  #Opens the first available device (no aux synth can be plugged in)


		#updated 09/26/2022 SND, now searches for the correct serial# before connecting
		#so we can connect to more than one USB device
		device_list = d2xx.listDevices()
		device_id = -1

		for k in device_list:
			string = k.decode('utf-8')
			if serial in string:
				device_id = device_list.index(k)

		#but to avoid breaking Carter's code, if the serial number isn't found, and it's 321V
		#then we'll just connect to the first device anyway
		if device_id == -1:
			if serial == '321V':
				self._handler = d2xx.open(0)
			else:
				raise ConnectionError(f'could not connect to PM5 serial# {serial}')
		elif device_id >-1:
			self._handler = d2xx.open(device_id)

	#writes array of decimals to bytes (SND)
	def _write(self,data):
		return self._handler.write(bytes(data))

	def set_zero(self):
		self._write([38,1,0,1])
		return self._handler.read(1)

	#return power in milliwatts (SND)
	def get_power(self):
		self._write([38,1,2,3])
		a = self._handler.read(14)
		num_sign = a[1]
		num_raw = a[2:10]
		exp_sign = a[11]
		exp_power = a[12:14]
		
		if chr(exp_sign) == '+':
			num = float(num_raw)*(10**int(exp_power))
		elif chr(exp_sign) == '-':
			num = float(num_raw)/(10**int(exp_power))
		else:
			num = float(num_raw)
		if chr(num_sign) == '-':
			num *= -1
		#print(chr(num_sign)+str(float(num_raw))+" * 10^"+chr(exp_sign)+str(int(exp_power)))
		#print(num)
		return num

	def close(self):
		#print('Closing PM5 connection')
		self._handler.close()