from .vdi_daq import VDAQ
from .vdi_fcounter import FC
from .vdi_synth import Synth

from .synth_view import SmarterSynthView

class SmarterSynth:
	#manage power correction for cable
	#control vdidaq > vva to toggle power
	#control frequency counter to measure exact frequency

	def __init__(self, synth_sn, fc_sn, vdaq_sn):
		print(synth_sn)
		print(fc_sn)
		print(vdaq_sn)

		self.synth_sn = synth_sn
		self.fc_sn = fc_sn
		self.vdaq_sn = vdaq_sn

	def connect_and_test(self):

		self.synth = Synth(self.synth_sn)
		self.fc = FC(self.fc_sn)
		self.daq = VDAQ(self.vdaq_sn)

		self.synth.set_frequency(10)

		print( self.fc.read_frequency() )
		print( self.daq.get_data(0,1) )

class SynthHelper:
	#open GUI interface for user to select instruments

	def __init__(self):
		view = SmarterSynthView(controller=self)
		view.Show()

	def set_serial_numbers(self, synth_sn, fc_sn, vdaq_sn):

		self.synth_sn = synth_sn
		self.fc_sn = fc_sn
		self.vdaq_sn = vdaq_sn

	def get_synth_obj(self):
		return SmarterSynth(self.synth_sn, self.fc_sn, self.vdaq_sn)