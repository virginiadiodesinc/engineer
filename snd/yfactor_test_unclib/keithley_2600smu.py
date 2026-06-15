import pyvisa

class SMU_K2611B():
	#GPIB address 18 by default
	def __init__(self, address, **kwargs):

		address_string = f'GPIB0::{address}::INSTR'

		rm = pyvisa.ResourceManager()
		self.inst = rm.open_resource(address_string)

		self.inst.write('display.screen = display.SMUA')
		self.inst.write('format.data = format.ASCII')
		self.inst.write('smua.nvbuffer1.clear()')
		self.inst.write('smua.nvbuffer1.appendmode = 1')
		self.inst.write('smua.nvbuffer1.collectsourcevalues = 1')
		self.inst.write('smua.measure.count = 1')
	
	def reset(self):
		self.inst.write('smua.reset()')
		
	def setsourceOn(self):
		self.inst.write('smua.source.output = smua.OUTPUT_ON')
		
	def setsourceOff(self):
		self.inst.write('smua.source.output = smua.OUTPUT_OFF')

	def set_voltage_limit(self, Vmax):
		#voltage in volts
		self.inst.write(f'smua.source.limitv = {Vmax}')

	def set_current_limit(self, Imax):
		#current in amps
		self.inst.write(f'smua.source.limiti = {Imax}')

	def set_voltage_level(self, Vlevel):
		self.inst.write(f'smua.source.levelv = {Vlevel}')

	def set_current_level(self, Ilevel):
		self.inst.write(f'smua.source.leveli = {Ilevel}')

	def set_mode_current_source(self):
		self.inst.write('smua.source.func = smua.OUTPUT_DCAMPS')
		self.inst.write('display.smua.measure.func = display.MEASURE_DCVOLTS')

	def set_mode_voltage_source(self):
		self.inst.write('smua.source.func = smua.OUTPUT_DCVOLTS')
		self.inst.write('display.smua.measure.func = display.MEASURE_DCAMPS')

	def add_current_reading_to_buffer(self):
		self.inst.write('smua.measure.i(smua.nvbuffer1)')

	def add_voltage_reading_to_buffer(self):
		self.inst.write('smua.measure.v(smua.nvbuffer1)')

	def read_value_buffer(self):
		vals = self.inst.query_ascii_values('printbuffer(1, smua.nvbuffer1.n, smua.nvbuffer1.readings)')
		return vals

	def clear_value_buffer(self):
		self.inst.write('smua.nvbuffer1.clear()')

	def get_voltage(self):
		self.add_voltage_reading_to_buffer()
		val = self.read_value_buffer()[0]
		self.clear_value_buffer()
		return val

	def get_current(self):
		self.add_current_reading_to_buffer()
		val = self.read_value_buffer()[0]
		self.clear_value_buffer()
		return val

	# def takeIV(self, Imin=1e-9, Imax=1e-3, Vmax=1, numpts = 101, dtime=0.01):
	#     self.reset()
		
	#     self.inst.write('display.screen = display.SMUA')
	#     self.inst.write('display.smua.measure.func = display.MEASURE_DCVOLTS')
	#     self.inst.write('smua.measure.autorangei = smua.AUTORANGE_ON')
	#     self.inst.write('format.data = format.ASCII')
	#     self.inst.write('smua.nvbuffer1.clear()')
	#     self.inst.write('smua.nvbuffer1.appendmode = 1')
	#     self.inst.write('smua.nvbuffer1.collectsourcevalues = 1')
	#     self.inst.write('smua.measure.count = 1')
	#     self.inst.write('smua.source.func = smua.OUTPUT_DCAMPS')
	#     self.inst.write(f'smua.source.limitv = {Vmax}')
	
	#     self.inst.write(f'smua.source.leveli = {Imin}')
		
	#     self.setsourceOn()
	
	#     irange = np.logspace(np.log10(Imin),np.log10(Imax),numpts)
	#     for ii in irange:
	#         self.inst.write(f'smua.source.leveli = {ii}')
	#         time.sleep(dtime)
	#         self.inst.write('smua.measure.v(smua.nvbuffer1)')
		
	#     # And back down
	#     for ii in reversed(irange):
	#         self.inst.write(f'smua.source.leveli = {ii}')
	#         time.sleep(dtime)
	#         self.inst.write('smua.measure.v(smua.nvbuffer1)')        
	
	#     self.setsourceOff()

	#     # pull data from internal buffer
	#     redvals = self.inst.query_ascii_values('printbuffer(1, smua.nvbuffer1.n, smua.nvbuffer1.readings)')
	#     srcvals = self.inst.query_ascii_values('printbuffer(1, smua.nvbuffer1.n, smua.nvbuffer1.sourcevalues)')
	
	#     df = pd.DataFrame({'Current (A)':srcvals[:numpts], 'Voltage Up (V)': redvals[:numpts], 
	#                        'Voltage Down (V)':[x for x in reversed(redvals[numpts:])]})
		
	#     df['Voltage avg (V)'] = (df['Voltage Up (V)']+df['Voltage Down (V)'])/2
		
	#     return(df)