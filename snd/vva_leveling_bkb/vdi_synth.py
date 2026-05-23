from util.vi.vdi_daq import VDAQ

try:
	import ftd2xx as d2xx
except:
	print('pip install ftd2xx to control vdi synth')

# Table of synth limits
SYNTH_LIMITS = {'VDIS':{'power':[14.5,19.0],'freq':[8,20]},'VEY':{'power':[0,0],'freq':[0,0]},'FTE11':{'power':[18.7,22.6],'freq':[2,20]}}

class Synth():
	'''
	Synth class to control VDI synthesizer.
	For use with Arduino microcontroller.
	'''
	def __init__(self, sn):
		#self.sn = sn
		
		if sn is not None and sn != '':	sns = [sn]
		else:				sns = list(SYNTH_LIMITS.keys())
		
		device_list = d2xx.listDevices()
		device_id = -1

		for k in device_list:
			string = k.decode('utf-8')
			for sn_check in sns:
				if sn_check in string:
					print(f'Found synth {string}')
					device_id = device_list.index(k)
					break
			if device_id != -1:	break

		self.dev = d2xx.open(device_id)
		self.dev_id = device_id
		
	def close(self):
		self.dev.close()
		print('VDI synth disconnected')
	
	def __del__(self):
		try:	self.close()
		except:	pass

	def set_frequency(self, frequency):	
		if 0 <= frequency <= 22:
			cw = ['0x06', '0x46'] # [number of bytes to follow, CW freq. command]
			cw_2 = int(frequency)

			frac = (frequency - int(frequency)) * 2**32
			frac = int(frac)
			cw_3 = ((frac & 0xff000000) >> 24)
			cw_4 = ((frac & 0xff0000) >> 16)
			cw_5 = ((frac & 0xff00) >> 8)
			cw_6 = (frac & 0xff)
			cw_7 = hex(0x06 ^ 0x46 ^ cw_2 ^ (cw_3) ^ (cw_4) ^ (cw_5) ^ (cw_6))
			cw.append(hex(cw_2))
			cw.append(hex(cw_3))
			cw.append(hex(cw_4))
			cw.append(hex(cw_5))
			cw.append(hex(cw_6))
			cw.append(cw_7)

			#print (f'raw hex bytes: {cw}')
			synth_output_freq = [int(k,16) for k in cw]
			#print (f'writing int bytes: {synth_output_freq}')
			self.dev.write(bytes(synth_output_freq))
		else:
			print ("Bad input frequency.")

class VDISynth(Synth):
	'''
	Child class of Synth, creating the same synth connection and also looking for a DAQ to turn the synth on and off
	Functions will have names that mimic the functions of our agilent_signal_generator class to be easily used in place
	Will fail to initialize if a daq connection cannot be made
	
	@param	sn	The sn of the synth to connect to
	'''
	def __init__(self, sn='VDIS'):
		super().__init__(sn)
		
		self.daq = self.initDAQ()
		
		if not self.daq:	return None
		
		self.power_warning = False
		
		# Placeholder frequency until I learn how to read freq. Might need frequency counter for this
		self.freq = 0
	
	def initDAQ(self):
		try:	return VDAQ(sn='VDAQ')
		except:
			print("Could not connect to the DAQ for synth control")
			return	False
	
	def close(self):
		try:	self.daq.cleanup()
		except:	pass
		super().close()
	
	#Property functions used to easily set and read frequency in GHz
	# self.set_frequency is already defined and formatted correctly
	def set_frequency(self,frequency):
		super().set_frequency(frequency)
		self.freq = frequency
	def get_frequency(self):
		return self.freq

	#Filler functions to allow this to act as a signal generator
	def set_power(self,power):
		if not self.power_warning:
			print("One time Warning: Cannot set power on VDI synth")
			self.power_warning = True
	def get_power(self):
		return "Base power out of synth is 16dBm?"

	#Creating properties so that settings can be treated like variables
	frequency=property(get_frequency,set_frequency)
	power = property(get_power,set_power)

	def power_on(self):
		self.daq.write_voltage(0,0)

	def power_off(self):
		self.daq.write_voltage(0,5)

#Overloading Synth class to deal with AM noise behavior, opening / closing within each function
class VDISynth_AMnoise(Synth):
	def __init__(self, sn='VDIS'):
		super().__init__(sn)
		try:
			super().close()
		except:
			print('Failed to close synth')

	def set_frequency(self,frequency):
		self.dev = d2xx.open(self.dev_id)
		super().set_frequency(frequency)
		self.freq = frequency
		try:
			super().close()
		except:
			print('Failed to close synth')