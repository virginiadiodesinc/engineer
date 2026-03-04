# -*- coding: utf-8 -*-

###########################################################################
## Python code generated with wxFormBuilder (version 3.10.1-0-g8feb16b3)
## http://www.wxformbuilder.org/
##
## PLEASE DO *NOT* EDIT THIS FILE!
###########################################################################

import wx
import wx.xrc

###########################################################################
## Class VirtualENRPanel
###########################################################################

class VirtualENRPanel ( wx.Panel ):

	def __init__( self, parent, id = wx.ID_ANY, pos = wx.DefaultPosition, size = wx.Size( 500,650 ), style = wx.TAB_TRAVERSAL, name = wx.EmptyString ):
		wx.Panel.__init__ ( self, parent, id = id, pos = pos, size = size, style = style, name = name )

		bSizer7 = wx.BoxSizer( wx.VERTICAL )

		self.m_panel5 = wx.Panel( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		gSizer1 = wx.GridSizer( 0, 2, 0, 0 )

		self.m_staticText27 = wx.StaticText( self.m_panel5, wx.ID_ANY, u"VBW (Hz)", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText27.Wrap( -1 )

		gSizer1.Add( self.m_staticText27, 0, wx.ALL, 5 )

		self.vbw_hz = wx.TextCtrl( self.m_panel5, wx.ID_ANY, u"1", wx.DefaultPosition, wx.DefaultSize, 0 )
		gSizer1.Add( self.vbw_hz, 0, wx.ALL, 5 )

		self.m_staticText28 = wx.StaticText( self.m_panel5, wx.ID_ANY, u"RBW (Hz)", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText28.Wrap( -1 )

		gSizer1.Add( self.m_staticText28, 0, wx.ALL, 5 )

		self.rbw_hz = wx.TextCtrl( self.m_panel5, wx.ID_ANY, u"8000000", wx.DefaultPosition, wx.DefaultSize, 0 )
		gSizer1.Add( self.rbw_hz, 0, wx.ALL, 5 )

		self.m_staticText4 = wx.StaticText( self.m_panel5, wx.ID_ANY, u"IF Center Freq (MHz)", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText4.Wrap( -1 )

		gSizer1.Add( self.m_staticText4, 0, wx.ALL, 5 )

		self.ifcenter_mhz = wx.TextCtrl( self.m_panel5, wx.ID_ANY, u"70", wx.DefaultPosition, wx.DefaultSize, 0 )
		gSizer1.Add( self.ifcenter_mhz, 0, wx.ALL, 5 )

		self.m_staticText5 = wx.StaticText( self.m_panel5, wx.ID_ANY, u"IF Bandwidth (MHz)", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText5.Wrap( -1 )

		gSizer1.Add( self.m_staticText5, 0, wx.ALL, 5 )

		self.ifbw_mhz = wx.TextCtrl( self.m_panel5, wx.ID_ANY, u"5", wx.DefaultPosition, wx.DefaultSize, 0 )
		gSizer1.Add( self.ifbw_mhz, 0, wx.ALL, 5 )

		self.m_staticText6 = wx.StaticText( self.m_panel5, wx.ID_ANY, u"Start Frequency (GHz)", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText6.Wrap( -1 )

		gSizer1.Add( self.m_staticText6, 0, wx.ALL, 5 )

		self.fstart_ghz = wx.TextCtrl( self.m_panel5, wx.ID_ANY, u"110", wx.DefaultPosition, wx.DefaultSize, 0 )
		gSizer1.Add( self.fstart_ghz, 0, wx.ALL, 5 )

		self.m_staticText7 = wx.StaticText( self.m_panel5, wx.ID_ANY, u"Stop Frequency (GHz)", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText7.Wrap( -1 )

		gSizer1.Add( self.m_staticText7, 0, wx.ALL, 5 )

		self.fstop_ghz = wx.TextCtrl( self.m_panel5, wx.ID_ANY, u"170", wx.DefaultPosition, wx.DefaultSize, 0 )
		gSizer1.Add( self.fstop_ghz, 0, wx.ALL, 5 )

		self.m_staticText25 = wx.StaticText( self.m_panel5, wx.ID_ANY, u"Multiplier", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText25.Wrap( -1 )

		gSizer1.Add( self.m_staticText25, 0, wx.ALL, 5 )

		self.mult = wx.TextCtrl( self.m_panel5, wx.ID_ANY, u"12", wx.DefaultPosition, wx.DefaultSize, 0 )
		gSizer1.Add( self.mult, 0, wx.ALL, 5 )

		self.m_staticText8 = wx.StaticText( self.m_panel5, wx.ID_ANY, u"LO Power (dBm)", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText8.Wrap( -1 )

		gSizer1.Add( self.m_staticText8, 0, wx.ALL, 5 )

		self.lopower_dbm = wx.TextCtrl( self.m_panel5, wx.ID_ANY, u"0", wx.DefaultPosition, wx.DefaultSize, 0 )
		gSizer1.Add( self.lopower_dbm, 0, wx.ALL, 5 )

		self.m_staticText16 = wx.StaticText( self.m_panel5, wx.ID_ANY, u"Number of Points", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText16.Wrap( -1 )

		gSizer1.Add( self.m_staticText16, 0, wx.ALL, 5 )

		self.num_points = wx.TextCtrl( self.m_panel5, wx.ID_ANY, u"101", wx.DefaultPosition, wx.DefaultSize, 0 )
		gSizer1.Add( self.num_points, 0, wx.ALL, 5 )

		self.m_staticText26 = wx.StaticText( self.m_panel5, wx.ID_ANY, u"Meas. Delay (s)", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText26.Wrap( -1 )

		gSizer1.Add( self.m_staticText26, 0, wx.ALL, 5 )

		self.measdelay = wx.TextCtrl( self.m_panel5, wx.ID_ANY, u"1", wx.DefaultPosition, wx.DefaultSize, 0 )
		gSizer1.Add( self.measdelay, 0, wx.ALL, 5 )

		self.m_button5 = wx.Button( self.m_panel5, wx.ID_ANY, u"Check Setup at Midband", wx.DefaultPosition, wx.DefaultSize, 0 )
		gSizer1.Add( self.m_button5, 0, wx.ALL, 5 )

		self.verify_textbox = wx.StaticText( self.m_panel5, wx.ID_ANY, u"[measured power]", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.verify_textbox.Wrap( -1 )

		gSizer1.Add( self.verify_textbox, 0, wx.ALL, 5 )


		self.m_panel5.SetSizer( gSizer1 )
		self.m_panel5.Layout()
		gSizer1.Fit( self.m_panel5 )
		bSizer7.Add( self.m_panel5, 0, wx.EXPAND |wx.ALL, 5 )

		bSizer13 = wx.BoxSizer( wx.HORIZONTAL )

		self.m_staticText3 = wx.StaticText( self, wx.ID_ANY, u"Save Directory: ", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText3.Wrap( -1 )

		bSizer13.Add( self.m_staticText3, 0, wx.ALL, 5 )

		self.output_dir_picker = wx.DirPickerCtrl( self, wx.ID_ANY, wx.EmptyString, u"Select a folder", wx.DefaultPosition, wx.DefaultSize, wx.DIRP_DEFAULT_STYLE )
		bSizer13.Add( self.output_dir_picker, 1, wx.ALL, 5 )


		bSizer7.Add( bSizer13, 0, wx.EXPAND, 5 )

		bSizer15 = wx.BoxSizer( wx.HORIZONTAL )

		self.m_staticText19 = wx.StaticText( self, wx.ID_ANY, u"Filename:", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText19.Wrap( -1 )

		bSizer15.Add( self.m_staticText19, 0, wx.ALL, 5 )

		self.output_filename = wx.TextCtrl( self, wx.ID_ANY, u"Tsys", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer15.Add( self.output_filename, 1, wx.ALL, 5 )


		bSizer7.Add( bSizer15, 0, wx.EXPAND, 5 )

		self.m_notebook4 = wx.Notebook( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_panel3 = wx.Panel( self.m_notebook4, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		gSizer3 = wx.GridSizer( 0, 2, 0, 0 )

		self.m_staticText17 = wx.StaticText( self.m_panel3, wx.ID_ANY, u"NS Calibration File (T Hot)", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText17.Wrap( -1 )

		gSizer3.Add( self.m_staticText17, 0, wx.ALL, 5 )

		self.ns_file_in = wx.FilePickerCtrl( self.m_panel3, wx.ID_ANY, wx.EmptyString, u"Select a file", u"*.*", wx.DefaultPosition, wx.DefaultSize, wx.FLP_DEFAULT_STYLE )
		gSizer3.Add( self.ns_file_in, 0, wx.ALL, 5 )

		self.m_staticText18 = wx.StaticText( self.m_panel3, wx.ID_ANY, u"Room Temp (K)", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText18.Wrap( -1 )

		gSizer3.Add( self.m_staticText18, 0, wx.ALL, 5 )

		self.roomtemp_k = wx.TextCtrl( self.m_panel3, wx.ID_ANY, u"293", wx.DefaultPosition, wx.DefaultSize, 0 )
		gSizer3.Add( self.roomtemp_k, 0, wx.ALL, 5 )

		self.m_button8 = wx.Button( self.m_panel3, wx.ID_ANY, u"Save NS Off", wx.DefaultPosition, wx.DefaultSize, 0 )
		gSizer3.Add( self.m_button8, 0, wx.ALL, 5 )

		self.m_button9 = wx.Button( self.m_panel3, wx.ID_ANY, u"Save NS On", wx.DefaultPosition, wx.DefaultSize, 0 )
		gSizer3.Add( self.m_button9, 0, wx.ALL, 5 )

		self.m_button11 = wx.Button( self.m_panel3, wx.ID_ANY, u"Calculate and Save File", wx.DefaultPosition, wx.DefaultSize, 0 )
		gSizer3.Add( self.m_button11, 0, wx.ALL, 5 )


		self.m_panel3.SetSizer( gSizer3 )
		self.m_panel3.Layout()
		gSizer3.Fit( self.m_panel3 )
		self.m_notebook4.AddPage( self.m_panel3, u"NS Measurement", True )
		self.m_panel2 = wx.Panel( self.m_notebook4, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		gSizer2 = wx.GridSizer( 0, 2, 0, 0 )

		self.m_staticText11 = wx.StaticText( self.m_panel2, wx.ID_ANY, u"T Hot (K)", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText11.Wrap( -1 )

		gSizer2.Add( self.m_staticText11, 0, wx.ALL, 5 )

		self.ln2_thot = wx.TextCtrl( self.m_panel2, wx.ID_ANY, u"293", wx.DefaultPosition, wx.DefaultSize, 0 )
		gSizer2.Add( self.ln2_thot, 0, wx.ALL, 5 )

		self.m_staticText12 = wx.StaticText( self.m_panel2, wx.ID_ANY, u"T Cold (K)", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText12.Wrap( -1 )

		gSizer2.Add( self.m_staticText12, 0, wx.ALL, 5 )

		self.ln2_tcold = wx.TextCtrl( self.m_panel2, wx.ID_ANY, u"80", wx.DefaultPosition, wx.DefaultSize, 0 )
		gSizer2.Add( self.ln2_tcold, 0, wx.ALL, 5 )

		self.m_button6 = wx.Button( self.m_panel2, wx.ID_ANY, u"Meas. Chopped", wx.DefaultPosition, wx.DefaultSize, 0 )
		gSizer2.Add( self.m_button6, 0, wx.ALL, 5 )

		self.m_button7 = wx.Button( self.m_panel2, wx.ID_ANY, u"Meas. No Motor", wx.DefaultPosition, wx.DefaultSize, 0 )
		gSizer2.Add( self.m_button7, 0, wx.ALL, 5 )

		self.m_button10 = wx.Button( self.m_panel2, wx.ID_ANY, u"Calculate and Save File", wx.DefaultPosition, wx.DefaultSize, 0 )
		gSizer2.Add( self.m_button10, 0, wx.ALL, 5 )


		self.m_panel2.SetSizer( gSizer2 )
		self.m_panel2.Layout()
		gSizer2.Fit( self.m_panel2 )
		self.m_notebook4.AddPage( self.m_panel2, u"LN2 Measurement", False )
		self.m_panel7 = wx.Panel( self.m_notebook4, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		gSizer4 = wx.GridSizer( 0, 2, 0, 0 )

		self.m_staticText22 = wx.StaticText( self.m_panel7, wx.ID_ANY, u"RX Tsys File", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText22.Wrap( -1 )

		gSizer4.Add( self.m_staticText22, 0, wx.ALL, 5 )

		self.rx_tsys_in = wx.FilePickerCtrl( self.m_panel7, wx.ID_ANY, wx.EmptyString, u"Select a file", u"*.*", wx.DefaultPosition, wx.DefaultSize, wx.FLP_DEFAULT_STYLE )
		gSizer4.Add( self.rx_tsys_in, 0, wx.ALL, 5 )

		self.m_staticText23 = wx.StaticText( self.m_panel7, wx.ID_ANY, u"NS with unknown T Hot", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText23.Wrap( -1 )

		gSizer4.Add( self.m_staticText23, 0, wx.ALL, 5 )

		self.ns_unknown_in = wx.FilePickerCtrl( self.m_panel7, wx.ID_ANY, wx.EmptyString, u"Select a file", u"*.*", wx.DefaultPosition, wx.DefaultSize, wx.FLP_DEFAULT_STYLE )
		gSizer4.Add( self.ns_unknown_in, 0, wx.ALL, 5 )

		self.m_staticText24 = wx.StaticText( self.m_panel7, wx.ID_ANY, u"Filename", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText24.Wrap( -1 )

		gSizer4.Add( self.m_staticText24, 0, wx.ALL, 5 )

		self.ns_cal_filename = wx.TextCtrl( self.m_panel7, wx.ID_ANY, u"NS XX Cal File", wx.DefaultPosition, wx.DefaultSize, 0 )
		gSizer4.Add( self.ns_cal_filename, 0, wx.ALL, 5 )

		self.m_button12 = wx.Button( self.m_panel7, wx.ID_ANY, u"Calculate and Save File", wx.DefaultPosition, wx.DefaultSize, 0 )
		gSizer4.Add( self.m_button12, 0, wx.ALL, 5 )


		self.m_panel7.SetSizer( gSizer4 )
		self.m_panel7.Layout()
		gSizer4.Fit( self.m_panel7 )
		self.m_notebook4.AddPage( self.m_panel7, u"Create NS Cal File", False )

		bSizer7.Add( self.m_notebook4, 1, wx.EXPAND |wx.ALL, 5 )

		bSizer4 = wx.BoxSizer( wx.HORIZONTAL )

		self.m_button91 = wx.Button( self, wx.ID_ANY, u"MotorCW", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer4.Add( self.m_button91, 0, wx.ALL, 5 )

		self.m_button101 = wx.Button( self, wx.ID_ANY, u"MotorCCW", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer4.Add( self.m_button101, 0, wx.ALL, 5 )


		bSizer7.Add( bSizer4, 1, wx.EXPAND, 5 )


		self.SetSizer( bSizer7 )
		self.Layout()

		# Connect Events
		self.m_button5.Bind( wx.EVT_BUTTON, self.VerifySetup )
		self.m_button8.Bind( wx.EVT_BUTTON, self.Save_NS_Off )
		self.m_button9.Bind( wx.EVT_BUTTON, self.Save_NS_On )
		self.m_button11.Bind( wx.EVT_BUTTON, self.Calculate_NS )
		self.m_button6.Bind( wx.EVT_BUTTON, self.Save_LN2_Cold )
		self.m_button7.Bind( wx.EVT_BUTTON, self.Save_LN2_Hot )
		self.m_button10.Bind( wx.EVT_BUTTON, self.Calculate_LN2 )
		self.m_button12.Bind( wx.EVT_BUTTON, self.Create_Calfile )
		self.m_button91.Bind( wx.EVT_BUTTON, self.MotorCW )
		self.m_button101.Bind( wx.EVT_BUTTON, self.MotorCCW )

	def __del__( self ):
		pass


	# Virtual event handlers, override them in your derived class
	def VerifySetup( self, event ):
		event.Skip()

	def Save_NS_Off( self, event ):
		event.Skip()

	def Save_NS_On( self, event ):
		event.Skip()

	def Calculate_NS( self, event ):
		event.Skip()

	def Save_LN2_Cold( self, event ):
		event.Skip()

	def Save_LN2_Hot( self, event ):
		event.Skip()

	def Calculate_LN2( self, event ):
		event.Skip()

	def Create_Calfile( self, event ):
		event.Skip()

	def MotorCW( self, event ):
		event.Skip()

	def MotorCCW( self, event ):
		event.Skip()


