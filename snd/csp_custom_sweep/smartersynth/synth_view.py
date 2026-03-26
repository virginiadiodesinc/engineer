from .synth_gui import SmarterSynthGUI


class SmarterSynthView(SmarterSynthGUI):

    def __init__(self, controller, **kwargs):
        SmarterSynthGUI.__init__(self, parent=None, **kwargs)

        self.controller = controller
    
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
        synth_sn = self.m_textCtrl31.GetValue()
        fc_sn = self.m_textCtrl32.GetValue()
        vdaq_sn = self.m_textCtrl33.GetValue()
        self.controller.set_serial_numbers(synth_sn, fc_sn, vdaq_sn)
        self.Close()

    def cancel_pressed( self, event ):
        event.Skip()
        self.Close()

    def populate_choicebox( self, choices ):
        self.m_listBox1.Set( choices )

    def get_current_selection( self ):
        choice_index = self.m_listBox1.GetSelection()
        choice = self.m_listBox1.GetString(choice_index)
        return choice