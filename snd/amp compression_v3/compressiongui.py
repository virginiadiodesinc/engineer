# -*- coding: utf-8 -*-

###########################################################################
## Python code generated with wxFormBuilder (version 4.2.1-0-g80c4cb6)
## http://www.wxformbuilder.org/
##
## PLEASE DO *NOT* EDIT THIS FILE!
###########################################################################

import wx
import wx.xrc

###########################################################################
## Class compressionGUI
###########################################################################

class compressionGUI ( wx.Frame ):

	def __init__( self, parent ):
		wx.Frame.__init__ ( self, parent, id = wx.ID_ANY, title = wx.EmptyString, pos = wx.DefaultPosition, size = wx.Size( 500,601 ), style = wx.DEFAULT_FRAME_STYLE|wx.TAB_TRAVERSAL )

		self.SetSizeHints( wx.DefaultSize, wx.DefaultSize )

		bSizer1 = wx.BoxSizer( wx.VERTICAL )

		self.m_notebook1 = wx.Notebook( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_panel1 = wx.Panel( self.m_notebook1, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		bSizer2 = wx.BoxSizer( wx.HORIZONTAL )

		self.m_textCtrl1 = wx.TextCtrl( self.m_panel1, wx.ID_ANY, u"-setup VNAX pair using mmwave macro\n-connect in thru with a big attenuator in between\n    -it should be more than the gain of your amp\n-run the power calibration (2nd tab)\n-after the cal. algorithm runs the pna should switch to a linear sweep with very low power (-30 to -29dbm input)\n   -verify this is the case before you proceed\n-add your amplifier (DUT)\n-note: input of DUT has to be on P1, output of DUT on attenuator\n-the attenuator should be between DUT and P2\n-run the compression test (3rd tab)\n    -the \"check setup\" button will show what power ranges you are about to sweep\n    -you can run multiple amps using the same power calibration\n    -but for safety the power cal won't save when the program closes\n-plot whatever you want on the (4th tab)\n-data exports in longform .csv, ask JJG for tips on plotting in excel\n-this program can alternatively be used just to generate plots from previous data\n-SND&TJR 05/2025", wx.DefaultPosition, wx.DefaultSize, wx.TE_MULTILINE|wx.TE_READONLY )
		bSizer2.Add( self.m_textCtrl1, 1, wx.ALL|wx.EXPAND, 5 )


		self.m_panel1.SetSizer( bSizer2 )
		self.m_panel1.Layout()
		bSizer2.Fit( self.m_panel1 )
		self.m_notebook1.AddPage( self.m_panel1, u"instructions", False )
		self.m_panel2 = wx.Panel( self.m_notebook1, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		bSizer3 = wx.BoxSizer( wx.VERTICAL )

		gSizer1 = wx.GridSizer( 0, 2, 0, 0 )

		self.f_npts = wx.TextCtrl( self.m_panel2, wx.ID_ANY, u"41", wx.DefaultPosition, wx.DefaultSize, 0 )
		gSizer1.Add( self.f_npts, 0, wx.ALL|wx.EXPAND, 5 )

		self.m_staticText13 = wx.StaticText( self.m_panel2, wx.ID_ANY, u"rf pts", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText13.Wrap( -1 )

		gSizer1.Add( self.m_staticText13, 0, wx.ALL, 5 )

		self.tpp_string = wx.FilePickerCtrl( self.m_panel2, wx.ID_ANY, wx.EmptyString, u"Select a file", u"*.*", wx.DefaultPosition, wx.DefaultSize, wx.FLP_DEFAULT_STYLE )
		gSizer1.Add( self.tpp_string, 0, wx.ALL|wx.EXPAND, 5 )

		self.m_staticText18 = wx.StaticText( self.m_panel2, wx.ID_ANY, u"VNAX TPP File (with VAR at minimum)", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText18.Wrap( -1 )

		gSizer1.Add( self.m_staticText18, 0, wx.ALL, 5 )

		self.vnax_rbw_hz = wx.TextCtrl( self.m_panel2, wx.ID_ANY, u"1000", wx.DefaultPosition, wx.DefaultSize, 0 )
		gSizer1.Add( self.vnax_rbw_hz, 0, wx.ALL|wx.EXPAND, 5 )

		self.m_staticText19 = wx.StaticText( self.m_panel2, wx.ID_ANY, u"RBW during power sweeps (hz)", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText19.Wrap( -1 )

		gSizer1.Add( self.m_staticText19, 0, wx.ALL, 5 )

		self.outputdir = wx.DirPickerCtrl( self.m_panel2, wx.ID_ANY, wx.EmptyString, u"Select a folder", wx.DefaultPosition, wx.DefaultSize, wx.DIRP_DEFAULT_STYLE )
		gSizer1.Add( self.outputdir, 0, wx.ALL|wx.EXPAND, 5 )

		self.m_staticText23 = wx.StaticText( self.m_panel2, wx.ID_ANY, u"output directory", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText23.Wrap( -1 )

		gSizer1.Add( self.m_staticText23, 0, wx.ALL, 5 )

		self.debug_fname = wx.TextCtrl( self.m_panel2, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		gSizer1.Add( self.debug_fname, 0, wx.ALL|wx.EXPAND, 5 )

		self.m_staticText24 = wx.StaticText( self.m_panel2, wx.ID_ANY, u"output filename (for the debug file)", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText24.Wrap( -1 )

		gSizer1.Add( self.m_staticText24, 0, wx.ALL, 5 )

		self.m_button41 = wx.Button( self.m_panel2, wx.ID_ANY, u"find power limits", wx.DefaultPosition, wx.DefaultSize, 0 )
		gSizer1.Add( self.m_button41, 0, wx.ALL|wx.EXPAND, 5 )

		self.m_staticText231 = wx.StaticText( self.m_panel2, wx.ID_ANY, u"(set VAR to min. attenuation first)", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText231.Wrap( -1 )

		gSizer1.Add( self.m_staticText231, 0, wx.ALL, 5 )

		self.vnax_pmin = wx.TextCtrl( self.m_panel2, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		gSizer1.Add( self.vnax_pmin, 0, wx.ALL|wx.EXPAND, 5 )

		self.m_staticText14 = wx.StaticText( self.m_panel2, wx.ID_ANY, u"vnax p1 output power min (dbm)", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText14.Wrap( -1 )

		gSizer1.Add( self.m_staticText14, 0, wx.ALL, 5 )

		self.vnax_pmax = wx.TextCtrl( self.m_panel2, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		gSizer1.Add( self.vnax_pmax, 0, wx.ALL|wx.EXPAND, 5 )

		self.m_staticText15 = wx.StaticText( self.m_panel2, wx.ID_ANY, u"vnax p1 output power max (dbm)", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText15.Wrap( -1 )

		gSizer1.Add( self.m_staticText15, 0, wx.ALL, 5 )

		self.vnax_pstep = wx.TextCtrl( self.m_panel2, wx.ID_ANY, u".05", wx.DefaultPosition, wx.DefaultSize, 0 )
		gSizer1.Add( self.vnax_pstep, 0, wx.ALL|wx.EXPAND, 5 )

		self.m_staticText22 = wx.StaticText( self.m_panel2, wx.ID_ANY, u"vnax power step (db)", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText22.Wrap( -1 )

		gSizer1.Add( self.m_staticText22, 0, wx.ALL, 5 )


		bSizer3.Add( gSizer1, 0, wx.EXPAND, 5 )

		self.m_staticline6 = wx.StaticLine( self.m_panel2, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
		bSizer3.Add( self.m_staticline6, 0, wx.EXPAND |wx.ALL, 5 )

		gSizer61 = wx.GridSizer( 0, 2, 0, 0 )

		self.m_staticText233 = wx.StaticText( self.m_panel2, wx.ID_ANY, u"Optionally turn VAR down to limit max power. Program will adjust the TPP file by the delta. New TPP = TPP File - (Max R1 from \"find power limits\") - (R1 when button is pressed)", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText233.Wrap( 450 )

		gSizer61.Add( self.m_staticText233, 0, wx.ALL, 5 )


		gSizer61.Add( ( 0, 0), 1, wx.EXPAND, 5 )

		self.m_button71 = wx.Button( self.m_panel2, wx.ID_ANY, u"Run TPP Adjust", wx.DefaultPosition, wx.DefaultSize, 0 )
		gSizer61.Add( self.m_button71, 0, wx.ALL, 5 )

		self.m_button8 = wx.Button( self.m_panel2, wx.ID_ANY, u"Plot Adjusted TPP", wx.DefaultPosition, wx.DefaultSize, 0 )
		gSizer61.Add( self.m_button8, 0, wx.ALL, 5 )


		bSizer3.Add( gSizer61, 0, wx.EXPAND, 5 )

		self.m_staticline7 = wx.StaticLine( self.m_panel2, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
		bSizer3.Add( self.m_staticline7, 0, wx.EXPAND |wx.ALL, 5 )

		gSizer5 = wx.GridSizer( 0, 2, 0, 0 )

		self.m_button7 = wx.Button( self.m_panel2, wx.ID_ANY, u"run power cal", wx.DefaultPosition, wx.DefaultSize, 0 )
		gSizer5.Add( self.m_button7, 0, wx.ALL|wx.EXPAND, 5 )

		self.m_staticText28 = wx.StaticText( self.m_panel2, wx.ID_ANY, u"dont forget the attenuator", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText28.Wrap( -1 )

		gSizer5.Add( self.m_staticText28, 0, wx.ALL, 5 )

		self.powercalexists = wx.CheckBox( self.m_panel2, wx.ID_ANY, u"power cal exists", wx.DefaultPosition, wx.DefaultSize, 0 )
		gSizer5.Add( self.powercalexists, 0, wx.ALL|wx.EXPAND, 5 )


		bSizer3.Add( gSizer5, 0, wx.EXPAND, 5 )


		self.m_panel2.SetSizer( bSizer3 )
		self.m_panel2.Layout()
		bSizer3.Fit( self.m_panel2 )
		self.m_notebook1.AddPage( self.m_panel2, u"power calibration", True )
		self.m_panel3 = wx.Panel( self.m_notebook1, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		bSizer8 = wx.BoxSizer( wx.VERTICAL )

		bSizer7 = wx.BoxSizer( wx.HORIZONTAL )

		gSizer2 = wx.GridSizer( 0, 2, 0, 0 )

		self.compression_max_rf = wx.TextCtrl( self.m_panel3, wx.ID_ANY, u"0", wx.DefaultPosition, wx.DefaultSize, 0 )
		gSizer2.Add( self.compression_max_rf, 0, wx.ALL|wx.EXPAND, 5 )

		self.m_staticText25 = wx.StaticText( self.m_panel3, wx.ID_ANY, u"amplifier damage limit (dBm)", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText25.Wrap( -1 )

		gSizer2.Add( self.m_staticText25, 0, wx.ALL, 5 )

		self.psweep_npoints = wx.TextCtrl( self.m_panel3, wx.ID_ANY, u"1001", wx.DefaultPosition, wx.DefaultSize, 0 )
		gSizer2.Add( self.psweep_npoints, 0, wx.ALL|wx.EXPAND, 5 )

		self.m_staticText221 = wx.StaticText( self.m_panel3, wx.ID_ANY, u"num. points for power sweep", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText221.Wrap( -1 )

		gSizer2.Add( self.m_staticText221, 0, wx.ALL, 5 )

		self.psweep_rbw = wx.TextCtrl( self.m_panel3, wx.ID_ANY, u"100", wx.DefaultPosition, wx.DefaultSize, 0 )
		gSizer2.Add( self.psweep_rbw, 0, wx.ALL|wx.EXPAND, 5 )

		self.m_staticText211 = wx.StaticText( self.m_panel3, wx.ID_ANY, u"rbw for power sweep", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText211.Wrap( -1 )

		gSizer2.Add( self.m_staticText211, 0, wx.ALL, 5 )

		self.comp_fname = wx.TextCtrl( self.m_panel3, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		gSizer2.Add( self.comp_fname, 0, wx.ALL|wx.EXPAND, 5 )

		self.m_staticText27 = wx.StaticText( self.m_panel3, wx.ID_ANY, u"filename (still uses the same dir. as 2nd tab)", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText27.Wrap( -1 )

		gSizer2.Add( self.m_staticText27, 0, wx.ALL, 5 )

		self.m_staticText26 = wx.StaticText( self.m_panel3, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText26.Wrap( -1 )

		gSizer2.Add( self.m_staticText26, 0, wx.ALL, 5 )


		bSizer7.Add( gSizer2, 1, 0, 5 )


		bSizer8.Add( bSizer7, 1, wx.EXPAND, 5 )

		self.m_button4 = wx.Button( self.m_panel3, wx.ID_ANY, u"check the setup", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer8.Add( self.m_button4, 1, wx.ALL|wx.EXPAND, 5 )

		self.debugwindow = wx.TextCtrl( self.m_panel3, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.TE_MULTILINE|wx.TE_READONLY )
		bSizer8.Add( self.debugwindow, 3, wx.ALL|wx.EXPAND, 5 )

		self.m_button6 = wx.Button( self.m_panel3, wx.ID_ANY, u"run the sweep", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer8.Add( self.m_button6, 1, wx.ALL|wx.EXPAND, 5 )


		self.m_panel3.SetSizer( bSizer8 )
		self.m_panel3.Layout()
		bSizer8.Fit( self.m_panel3 )
		self.m_notebook1.AddPage( self.m_panel3, u"compression sweep", False )
		self.m_panel4 = wx.Panel( self.m_notebook1, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		bSizer10 = wx.BoxSizer( wx.VERTICAL )

		bSizer7 = wx.BoxSizer( wx.VERTICAL )

		gSizer6 = wx.GridSizer( 0, 2, 0, 0 )

		self.m_staticText30 = wx.StaticText( self.m_panel4, wx.ID_ANY, u"this tab made possible by Theodore", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText30.Wrap( -1 )

		gSizer6.Add( self.m_staticText30, 0, wx.ALL, 5 )


		gSizer6.Add( ( 0, 0), 1, wx.EXPAND, 5 )

		self.m_staticText232 = wx.StaticText( self.m_panel4, wx.ID_ANY, u"input file", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText232.Wrap( -1 )

		gSizer6.Add( self.m_staticText232, 0, wx.ALL, 5 )

		self.html_inputfile = wx.FilePickerCtrl( self.m_panel4, wx.ID_ANY, wx.EmptyString, u"Select a file", u"*.*", wx.DefaultPosition, wx.DefaultSize, wx.FLP_DEFAULT_STYLE )
		gSizer6.Add( self.html_inputfile, 0, wx.ALL, 5 )

		self.m_staticText251 = wx.StaticText( self.m_panel4, wx.ID_ANY, u"html and formatted files output dir", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText251.Wrap( -1 )

		gSizer6.Add( self.m_staticText251, 0, wx.ALL, 5 )

		self.html_outputdir = wx.DirPickerCtrl( self.m_panel4, wx.ID_ANY, wx.EmptyString, u"Select a folder", wx.DefaultPosition, wx.DefaultSize, wx.DIRP_DEFAULT_STYLE )
		gSizer6.Add( self.html_outputdir, 0, wx.ALL, 5 )

		self.m_staticText261 = wx.StaticText( self.m_panel4, wx.ID_ANY, u"load output  dir from power calibration tab?", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText261.Wrap( -1 )

		gSizer6.Add( self.m_staticText261, 0, wx.ALL, 5 )

		self.m_button5 = wx.Button( self.m_panel4, wx.ID_ANY, u"Click Me", wx.DefaultPosition, wx.DefaultSize, 0 )
		gSizer6.Add( self.m_button5, 0, wx.ALL, 5 )

		self.show_html = wx.CheckBox( self.m_panel4, wx.ID_ANY, u"open html files now?", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.show_html.SetValue(True)
		gSizer6.Add( self.show_html, 0, wx.ALL, 5 )

		self.m_button61 = wx.Button( self.m_panel4, wx.ID_ANY, u"Compile Data", wx.DefaultPosition, wx.DefaultSize, 0 )
		gSizer6.Add( self.m_button61, 0, wx.ALL, 5 )


		bSizer7.Add( gSizer6, 0, wx.EXPAND, 5 )

		self.m_staticline2 = wx.StaticLine( self.m_panel4, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
		bSizer7.Add( self.m_staticline2, 0, wx.EXPAND |wx.ALL, 5 )

		gSizer4 = wx.GridSizer( 0, 2, 0, 0 )

		self.m_staticText281 = wx.StaticText( self.m_panel4, wx.ID_ANY, u"optional stuff", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText281.Wrap( -1 )

		gSizer4.Add( self.m_staticText281, 0, wx.ALL, 5 )


		gSizer4.Add( ( 0, 0), 1, wx.EXPAND, 5 )

		self.m_staticText29 = wx.StaticText( self.m_panel4, wx.ID_ANY, u"input power for psat (dbm)", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText29.Wrap( -1 )

		gSizer4.Add( self.m_staticText29, 0, wx.ALL, 5 )

		self.psat_input_power = wx.TextCtrl( self.m_panel4, wx.ID_ANY, u"3", wx.DefaultPosition, wx.DefaultSize, 0 )
		gSizer4.Add( self.psat_input_power, 0, wx.ALL, 5 )

		self.m_staticText241 = wx.StaticText( self.m_panel4, wx.ID_ANY, u"small signal backoff (db)", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText241.Wrap( -1 )

		gSizer4.Add( self.m_staticText241, 0, wx.ALL, 5 )

		self.ssbackoff = wx.TextCtrl( self.m_panel4, wx.ID_ANY, u"1", wx.DefaultPosition, wx.DefaultSize, 0 )
		gSizer4.Add( self.ssbackoff, 0, wx.ALL, 5 )


		bSizer7.Add( gSizer4, 0, wx.EXPAND, 5 )


		bSizer10.Add( bSizer7, 1, wx.EXPAND, 5 )


		self.m_panel4.SetSizer( bSizer10 )
		self.m_panel4.Layout()
		bSizer10.Fit( self.m_panel4 )
		self.m_notebook1.AddPage( self.m_panel4, u"generate html plots", False )

		bSizer1.Add( self.m_notebook1, 1, wx.EXPAND |wx.ALL, 5 )


		self.SetSizer( bSizer1 )
		self.Layout()

		self.Centre( wx.BOTH )

		# Connect Events
		self.m_button41.Bind( wx.EVT_BUTTON, self.find_appropriate_input_powers )
		self.m_button71.Bind( wx.EVT_BUTTON, self.run_tpp_adjust )
		self.m_button8.Bind( wx.EVT_BUTTON, self.plot_adjusted_tpp )
		self.m_button7.Bind( wx.EVT_BUTTON, self.runPowerSweep )
		self.m_button4.Bind( wx.EVT_BUTTON, self.checkSetup )
		self.m_button6.Bind( wx.EVT_BUTTON, self.runCompSweep )
		self.m_button5.Bind( wx.EVT_BUTTON, self.loadHtmlFilePath )
		self.m_button61.Bind( wx.EVT_BUTTON, self.compileHtml )

	def __del__( self ):
		pass


	# Virtual event handlers, override them in your derived class
	def find_appropriate_input_powers( self, event ):
		event.Skip()

	def run_tpp_adjust( self, event ):
		event.Skip()

	def plot_adjusted_tpp( self, event ):
		event.Skip()

	def runPowerSweep( self, event ):
		event.Skip()

	def checkSetup( self, event ):
		event.Skip()

	def runCompSweep( self, event ):
		event.Skip()

	def loadHtmlFilePath( self, event ):
		event.Skip()

	def compileHtml( self, event ):
		event.Skip()


