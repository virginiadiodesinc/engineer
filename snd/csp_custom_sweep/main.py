import wx
from smartersynth import SmarterSynthView, SmarterSynth
from main_gui import MyPanel2

class Main():

	def __init__(self):

		app = wx.App(False)
		frame = wx.Frame(parent=None)

		panel = MainPanel(parent=frame)

		frame.Show()
		app.MainLoop()

class MainPanel(MyPanel2):

	def __init__(self, parent):
		MyPanel2.__init__(self, parent)

	def idk(self, event):
		event.Skip()
		a = SmarterSynthView(controller=self)
		a.Show()

	def initialize_synth(self, synth_sn, fc_sn, vdaq_sn):
		a = SmarterSynth()

if __name__ == '__main__':
	a = Main()