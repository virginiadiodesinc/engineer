import wx
from test_panel_gui import MyFrame1
from synthesizer_controller import GenericSynthesizer
from agilent_signal_generator import PSG

class TestPanel(MyFrame1):
    def __init__(self, **kwargs):
        MyFrame1.__init__(self, **kwargs)

    def connect_pressed(self, event):
        event.Skip()
        address = self.m_textCtrl1.GetValue()
        try:
            address = int(address)
        except:
            pass
        self.gs = GenericSynthesizer(address)

    def idn_pressed(self, event):
        event.Skip()
        idn = self.gs.query_idn()
        self.m_textCtrl2.SetValue(idn)

    def psg_connect_pressed(self, event):
        event.Skip()
        address = self.m_textCtrl1.GetValue()
        try:
            address = int(address)
        except:
            pass
        self.psg = PSG(add=address)

    def power_on_pressed( self, event ):
        event.Skip()
        self.gs.power_on()

    def power_off_pressed( self, event ):
        event.Skip()
        self.gs.power_off()

    def set_freq_pressed( self, event ):
        event.Skip()
        self.gs.set_frequency(float(self.m_textCtrl3.GetValue()))

    def get_freq_pressed( self, event ):
        event.Skip()
        val = self.gs.get_frequency()
        self.m_textCtrl4.SetValue(val)

if __name__ == '__main__':
    app = wx.App(False)
    frame = TestPanel(parent=None)
    frame.Show()

    app.MainLoop()