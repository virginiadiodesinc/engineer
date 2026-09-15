
import pandas as pd
import numpy as np
import os
from taper_correction_gui import TaperCorrectPanel
import wx

def apply_taper_correction(trx_path, taper1_loss_db=0.28, taper2_loss_db=0.11, thot=293):
	#taper loss a positive int

	combined_loss_db = taper1_loss_db + taper2_loss_db
	combined_loss_lin = np.power(10, combined_loss_db/10)

	combined_temperature = (combined_loss_lin - 1)* thot

	df = pd.read_csv(trx_path, index_col=0)

	trec = df['T(K)']

	trec_prime = (trec-combined_temperature) / combined_loss_lin

	return trec_prime

def calculate_enr(trx_path, ns_unk_path, taper1_loss_db, taper2_loss_db, thot=293):

	trx_prime = apply_taper_correction(trx_path, taper1_loss_db, taper2_loss_db, thot)
	df = pd.read_csv(ns_unk_path,index_col=0)

	trx_interpolated = np.interp(df.index, trx_prime.index, trx_prime)

	df['Trx_prime'] = trx_interpolated
	df['Tns(K)'] = trx_interpolated*(df['Y']-1)+df['Y']*df['rt(K)']
	df['ENR'] = (df['Tns(K)']-df['rt(K)'])/df['rt(K)']
	df['ENR(dB)']=10*np.log10(df['ENR'])

	return df

class Main():

	def __init__(self):
		app = wx.App(False)
		frame = wx.Frame(parent=None, size=wx.Size(500,500))

		panel = GUIPanel(parent=frame)

		frame.Show()
		app.MainLoop()

class GUIPanel(TaperCorrectPanel):

	def calculate_function(self, event):
		event.Skip()
		mixer_path = self.m_filePicker1.GetPath()
		ns_selections = self.m_listBox1.GetSelections()
		
		taper1_db = float( self.m_textCtrl1.GetValue() )
		taper2_db = float( self.m_textCtrl2.GetValue() )

		for j in ns_selections:
			ns_filename = self.m_listBox1.GetString(j)
			ns_dir = self.m_dirPicker1.GetPath()
			ns_path = os.path.join(ns_dir,ns_filename)
			enr = calculate_enr(mixer_path,ns_path,taper1_db,taper2_db)

			underscore_location = ns_filename.rfind('_')
			name = ns_filename[:underscore_location]
			enr.to_csv(f"{name}_corrected.csv")

	def dir_changed_function(self, event):
		event.Skip()
		new_dir = self.m_dirPicker1.GetPath()
		self.m_listBox1.Set(os.listdir(new_dir))


if __name__ == '__main__':

	Main()
	# files_to_correct = os.listdir('to_calculate')
	# mixer_temp_file = 'mixer 2-06 with iso 101pts.csv'
	
	# out = pd.DataFrame()

	# for f in files_to_correct:
	# 	ns_file = os.path.join('to_calculate',f)
	# 	df = calculate_enr(mixer_temp_file, ns_file, 0.28, 0.11, 293)
		
	# 	underscore_index = f.rfind('_')
	# 	name = f[:underscore_index]
	# 	out[name] = df['ENR(dB)']