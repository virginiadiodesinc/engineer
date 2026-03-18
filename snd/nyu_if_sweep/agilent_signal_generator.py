#Class used to control the Agilent PSG (and also MXG)
#CXS (5/14/2021) - Adapted from SND (1/28/2014)
#KDH (12/15/2023) - Adding functions for PXA Sweep

import pyvisa

PSG_ADDRESS_GEN = 19
PSG_ADDRESS_ANA = 20
PSG_POWER_LIMIT = 20	#dBm

#Put these limits in GHz for now
SG_FREQ_LIMITS = {
	'N5183B': [0.000009, 40],
	'E8257D': [0.00025, 50]
}

class PSG():
	#Power limit in dbm, 15 by default
	def __init__(self, powerlimit=PSG_POWER_LIMIT, add='SGX', virtual=False, **kwargs):

		self.virtual = False

		#adding logic for dealing with virtual connection, do not attempt to connect with resource manager
		if virtual:
			self.virtual = True
			self.inst = None
			return

		rm = pyvisa.ResourceManager()

		skip=False	#SND - could not think of a smarter way to do this
		if add=='SAX':	address = PSG_ADDRESS_ANA
		elif add=='SGX':address = PSG_ADDRESS_GEN
		elif type(add) == str:
			self.inst = rm.open_resource(add)	#if the add is a full resource string, connect to it verbatim
			skip=True	#then skip the line later that is hardcoded to connect to GPIB
		else:			address = add
		
		if not skip:
			self.inst = rm.open_resource("GPIB0::%s"%address)
		self._powerlim = powerlimit
		self.power_off()
		self.preset()
		self.setLimits()

	def query_idn(self):
		#Identification query to outputs an identifying string. 
		#The response will show the following information: <company name>, <model number>, <serial number>, <firmware revision>
		return self.inst.query('*IDN?')
	
	def get_model_serial_number(self):
		idn_str = self.query_idn()
		idn_split = idn_str.split(',')
		return idn_split[1].replace(' ',''), idn_split[2].replace(' ','')
	
	def setLimits(self):
		model_num, sn = self.get_model_serial_number()
		if sn == 'MY61361552':
			self.min_freq = SG_FREQ_LIMITS[model_num][0]
			self.max_freq = 67
		else:
			self.min_freq = SG_FREQ_LIMITS[model_num][0]
			self.max_freq = SG_FREQ_LIMITS[model_num][1]

	def get_max_freq(self):
		return self.max_freq
	
	def get_min_freq(self):
		return self.min_freq

	#Property functions used to easily set and read frequency in GHz
	def set_frequency(self,frequency):
		if self.virtual:
			print("Simulated setting frequency on sig gen to " + str(frequency))
		else:
			self.inst.write(":FREQ %s GHZ" %(frequency))
	def get_frequency(self):
		return self.inst.ask_for_values(":FREQ?")[0]/1e9

	#Property functions used to easily set and read power in dBm
	def set_power(self,power):
		if self.virtual:
			print("Simulated setting power on sig gen to " + str(power))
		else:
			if self._powerlim < power:
				self.inst.write(":AMPL %s DBM" %(self._powerlim))
			else:
				self.inst.write(":AMPL %s DBM" %(power))
	def get_power(self):
		return self.inst.ask_for_values(":AMPL?")[0]

	#Creating properties so that settings can be treated like variables
	frequency=property(get_frequency,set_frequency)
	power = property(get_power,set_power)

	def power_on(self):
		if self.virtual:
			print('Simulated sig gen power on')
		else:
			self.inst.write(":OUTP 1")

	def power_off(self):
		if self.virtual:
			print('Simulated sig gen power off')
		else:
			self.inst.write(":OUTP 0")

	def freq_mult(self,mult):
		if self.virtual:
			print(f'Simulated setting sig gen mult to {mult}')
		else:
			self.inst.write(":FREQ:MULT %s"%(mult))

	def preset(self):
		self.inst.write("*RST")
	
	def send_opcheck(self):
		return self.inst.query('*OPC?')
	
	def set_MXG_sweep_freq_start(self, freq_start):
		"""Command to set freq start of signal generator

		Set the frequency start of sweep on MXG.

		@param freq_start Str representation of frequency start of DUT (in MHz) (casted to an int)
		"""
		if self.virtual:
			print(f'Simulated setting sig gen sweep start to {freq_start}')
		else:
			self.inst.write(':SOUR:FREQ:STAR %s MHz' %((int)(freq_start)))

	def set_MXG_sweep_freq_stop(self, freq_stop):
		"""Command to set freq stop of signal generator

		Set the frequency stop of sweep on MXG.

		@param freq_stop Str representation of frequency stop of DUT (in MHz) (casted to an int)
		"""
		if self.virtual:
			print(f'Simulated setting sig gen sweep start to {freq_stop}')
		else:
			self.inst.write(':SOUR:FREQ:STOP %s MHz' %((int)(freq_stop)))

	def set_MXG_sweep_npoints(self, npoints_MXG):
		"""Command to set number of points of signal generator

		Set the number of points taken on sweep on MXG.

		@param npoints_MXG Int representation of number points to sweep
		"""
		if self.virtual:
			print(f'Simulated setting sig gen sweep pts to {npoints_MXG}')
		else:
			self.inst.write(':SOUR:SWE:POIN %s' %(npoints_MXG))

	def set_sweep_dwell_time(self, dwell_time):
		"""Command to set dwell time of signal generator

		Set step sweep dwell time on MXG. This is the delay taken between each point in the sweep.

		@param dwell_time Int representation of dwell time
		"""
		if self.virtual:
			print(f'Simulated setting sig gen sweep dwell time to {dwell_time}')
		else:
			self.inst.write(':SOUR:SWE:DWEL %s' %(dwell_time))

	def set_freq_sweep_on(self):
		"""Command to set freq sweep to ON

		Set the frequency sweep to be ON on MXG (p. 75 MXG programming manual).
		"""
		if self.virtual:
			print('Simulated setting sig gen sweep to ON')
		else:
			self.inst.write(':SOUR:FREQ:MODE LIST')

	def set_sweep_cont_mode(self):
		self.inst.write(':INIT:CONT')

	def set_amptd_sweep_on(self):
		"""Command to set power sweep to ON

		Set the amplitude sweep to be ON on MXG.
		"""
		self.inst.write(':SOUR:POW:MODE LIST')

	def single_sweep(self):
		"""Command to start single sweep

		Aborts current sweep and arms or starts a sweep (p. 246 MXG programming manual).
		"""
		if self.virtual:
			print('Simulated starting a sweep on sig gen')
		else:
			self.inst.write(':SOUR:TSW')

	def abort_sweep(self):
		"""Command to abort sweep

		This command causes the List or Step sweep in progress to abort (p. 242 MXG programming manual).
		"""
		self.inst.write(':ABOR')