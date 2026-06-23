
from keithley_2600smu import SMU_K2611B

'''
smu needs to be set up for constant I and limit V
then safely toggle off => take an IV
=> go back into constant I bias

eventually handle both types of keithley
but for now only 2611B
'''

class KeithleyManager:
	def __init__(self, address):
		try:
			self.smu = SMU_K2611B(address)
			self.smu.setsourceOff()
		except:
			self.smu = None
		self.power_status = False


	def setup_current_source(self, ibias_ma, vlimit_v):
		if self.smu:
			self.smu.reset()
			self.smu.initialize()
			self.smu.set_mode_current_source()

			self.smu.set_voltage_limit(vlimit_v)
			self.smu.set_current_level(ibias_ma/1e3)
		else:
			pass

	def get_connected_status(self):
		if self.smu:
			return True
		return False

	def get_power_status(self):
		return self.power_status

	def toggle_on(self):
		if self.smu:
			self.smu.setsourceOn()
			self.power_status = True
			return True
		else:
			self.power_status = False
			return False

	def toggle_off(self):
		if self.smu:
			self.smu.setsourceOff()
			self.power_status = False
		return False

	def take_iv(self, compliance_v, start_i, end_i, numpoints):
		self.smu.reset()
		self.smu.initialize()
		self.smu.initialize_iv()
		#self.toggle_on()

		#source_values,measure_values = self.smu.run_iv(compliance_v, start_i, end_i, numpoints)
		self.smu.run_iv_tjr(1.2,100e-9,1e-3,30,0.001)
		source_values, measure_values = self.smu.get_iv_data()

		self.toggle_off()

		return source_values, measure_values