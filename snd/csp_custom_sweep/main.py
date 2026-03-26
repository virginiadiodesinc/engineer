import wx
from smartersynth.synth import SynthHelper
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
		a = SynthHelper()
		a.Show()

		print( a.get_synth_obj() )

if __name__ == '__main__':
	a = Main()