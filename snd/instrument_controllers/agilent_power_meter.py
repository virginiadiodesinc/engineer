#Class used to control the Agilent Power Meter
#CXS (5/17/2021) - Adapted from SND (1/28/2014)
#(Calhead data moved to util module)

import pyvisa

AGILENT_PM_ADDRESS = 13

class E4419B():
	def __init__(self, address=AGILENT_PM_ADDRESS, channel=1, **kwargs):
		rm = pyvisa.ResourceManager()
		self.inst = rm.open_resource("GPIB0::%s"%address)
		self.inst.write("SYST:PRES")
		self.channel = channel

	def test(self):
		print(self.inst.query("*IDN?"))

	#DBM or W (SND)
	def set_units(self,units):
		self.inst.write("UNIT1:POW %s" %(units))
		self.inst.write("UNIT2:POW %s" %(units))
	def get_units(self):
		return self.inst.query("UNIT1:POW?")

	units=property(get_units,set_units)

	def set_channel(self, channel):
		self.channel = channel

	def get_power(self, channel=None):
		if channel == None:	channel = self.channel
		return self.inst.query("FETC%i:POW:AC?" %(channel))

	#Tries both channels on an agilent power meter and returns the one that works
	def getAgilentChannel(self):
		channel = 0
		chans = ['ERR', 'A', 'B']
		for ch in [2,1]:
			try:
				self.get_power(channel=ch)
				channel = ch
				break
			except Exception as err:
				print("Issue with channel %s on the Agilent Power Meter:\n"%chans[ch] + str(err) + '\nTrying other channels\n')
		print('Using channel %s on the Agilent Power Meter\n' %chans[channel])
		self.set_channel(channel)
		return channel