import wx
from synth_gui import MyDialog1
import ftd2xx as d2xx

class SmarterSynthView(MyDialog1):

    def __init__(self, **kwargs):
        MyDialog1.__init__(self, parent=None, **kwargs)

        try:
            device_list = d2xx.listDevices()
            device_list_ascii = [k.decode('utf-8') for k in device_list]
            self.populate_choicebox(device_list_ascii)
        except:
            print('failed to connect to d2xx, populating with dummy list')
            device_list_ascii = ['vdis001', 'vdif001', 'vdidaq001']
            self.populate_choicebox(device_list_ascii)
    
    def synth_selected( self, event ):
        event.Skip()
        choice = self.get_current_selection()
        self.m_textCtrl31.SetValue( choice )

    def fc_selected( self, event ):
        event.Skip()
        choice = self.get_current_selection()
        self.m_textCtrl32.SetValue( choice )

    def vdaq_selected( self, event ):
        event.Skip()
        choice = self.get_current_selection()
        self.m_textCtrl33.SetValue( choice )

    def ok_pressed( self, event ):
        self.synth_sn = self.m_textCtrl31.GetValue()
        self.fc_sn = self.m_textCtrl32.GetValue()
        self.vdaq_sn = self.m_textCtrl33.GetValue()
        self.channel = int( self.m_radioBox1.GetStringSelection() )
        self.EndModal(wx.ID_OK)

    def cancel_pressed( self, event ):
        event.Skip()
        self.EndModal(wx.ID_CANCEL)

    def populate_choicebox( self, choices ):
        self.m_listBox1.Set( choices )

    def get_current_selection( self ):
        choice_index = self.m_listBox1.GetSelection()
        choice = self.m_listBox1.GetString(choice_index)
        return choice