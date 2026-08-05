from vdi_synth import Synth
from vdi_daq import VDAQ
from vdi_fcounter import FC
from agilent_signal_generator import PSG

import wx

from synth_view import SmarterSynthView


#subclass the PSG since that is the main function
class GenericSynthesizer():

    def __new__(self, address, **kwargs):
        #address can be "SAX", "SGX", a full GPIB string, or an int
        #for vdi synth it will be a serial number
        #either way, try to connect and see what happens
        #if we have an instrument just double check that we connected to a PSG
        #and print out the *IDN? response

        try:
            return PSG(add=address,**kwargs)
        except:
            return VDISynth(**kwargs)

class VDISynth():
    def __init__(self):
        with SmarterSynthView() as dialog:
            if dialog.ShowModal() == wx.ID_OK:
                #if this succeeds, then we are a synthesizer class
                print('ok')                    
                print(f'synth: {dialog.synth_sn}')
                print(f'freq counter: {dialog.fc_sn}')
                print(f'daq: {dialog.vdaq_sn}')
                print(f'channel: {dialog.channel}')

                self.synth_sn = dialog.synth_sn
                self.fc_sn = dialog.fc_sn
                self.vdaq_sn = dialog.vdaq_sn
                self.vdaq_channel = int(dialog.channel)

                self.power_off()
                
            else:
                print('canceld')
                self.synth = None
                self.fc = None
                self.vdaq = None
                self.vdaq_channel = None

    def query_idn(self):
        with Synth(self.synth_sn) as synth:
            synth_id = synth.dev.getDeviceInfo()
        with FC(self.fc_sn) as fc:
            fc_id = fc.dev.getDeviceInfo()
        with VDAQ(self.vdaq_sn) as vdaq:
            vdaq_id = vdaq.dev.getDeviceInfo()
        return f'{synth_id}\n{fc_id}\n{vdaq_id}\nvdaq_channel:{self.vdaq_channel}'

    def get_frequency(self):
        with FC(self.fc_sn) as fc:
            return fc.read_frequency()

    def set_frequency(self, freq):
        #frequency in ghz
        with Synth(self.synth_sn) as synth:
            synth.set_frequency(freq)

    def power_on(self):
        #set vva to 0
        with VDAQ(self.vdaq_sn) as vdaq:
            vdaq.write_voltage(self.vdaq_channel,0)

    def power_off(self):
        #set vva to 5
        with VDAQ(self.vdaq_sn) as vdaq:
            vdaq.write_voltage(self.vdaq_channel,5)


if __name__ == '__main__':
    app = wx.App(False)
    app.MainLoop()
    a = GenericSynthesizer(16)