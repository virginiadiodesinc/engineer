from .vdi_daq import VDAQ
from .vdi_fcounter import FC
from .vdi_synth import Synth

from .synth_view import SmarterSynthView


class SmarterSynth:
	#manage power correction for cable
	#control vdidaq > vva to toggle power
	#control frequency counter to measure exact frequency

	def __init__(self):
		self.synth = SmarterSynthView(controller=self)
		self.synth.Show()

	def initialize_synth(self, synth_sn, fc_sn, vdaq_sn):
		print(synth_sn)
		print(fc_sn)
		print(vdaq_sn)

	def connect_and_test(self):

		synth_sn = 'VEY14'
		synth2_sn = 'VDIS195'
		fc_sn = 'VDIF0036'
		fc2_sn = 'VDIF0069'
		vdaq_sn = 'RFVDAQ30'

		self.synth = Synth(synth_sn)
		self.synth2 = Synth(synth2_sn)

		self.fc = FC(fc_sn)
		self.fc2 = FC(fc2_sn)

		self.daq = VDAQ(vdaq_sn)

		self.synth.set_frequency(10)
		self.synth2.set_frequency(11)


		print( self.fc.read_frequency() )
		print( self.fc2.read_frequency() )
		print( self.daq.get_data(0,1) )